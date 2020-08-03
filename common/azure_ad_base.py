import asyncio
import inspect
import json
import logging
import os
from dataclasses import dataclass
from typing import *

from pyppeteer.errors import TimeoutError as PypTimeoutError
from pyppeteer.page import Page

from common import DATA_ROOT
from common.password_manager import PasswordManager
from common.pyppeteer import PypBrowser
from common.exceptions import DnbException

__all__ = ["MfaExpiredException", "State", "AzureAdConfig", "AzureAdBase"]

LOG = logging.getLogger(__name__)


class MfaExpiredException(DnbException):
    pass


class PasswordError(DnbException):
    pass


@dataclass(init=False)
class State:
    matches: Tuple[str]
    timeout: Optional[int]

    def __init__(self, *matches: str, timeout=None):
        self.matches = matches
        self.timeout = timeout

    @staticmethod
    def find(s: str, states: List["State"], default=None):
        matching = [state for state in states if s in state.matches]
        if len(matching) > 1:
            raise Exception("More than one state matching heading.")
        elif len(matching) == 1:
            return matching[0]
        else:
            return default


@dataclass(frozen=True)
class AzureAdConfig:
    headless: bool
    use_cookies: bool
    dump_io: bool
    default_timeout: Optional[int] = 20


class AzureAdBase:
    TIMEOUT_MFA = 120
    AZURE_BASE_URL = "https://login.microsoftonline.com"
    # For some reason this cookie creates an error when used, but it is not needed for restoring session.
    IGNORE_COOKIE_NAMES = ["esctx"]

    STATE_PICK_ACC = State("Pick an account")
    STATE_SIGN_IN = State("Sign in")
    STATE_PWD = State("Enter password")
    STATE_PWD_UPDATE = State("Update your password")
    STATE_TRYING_TO_SIGN_YOU_IN = State("Trying to sign you in")

    # App and phone call.
    STATE_MFA = State("Approve sign-in request", "Approve sign in request", timeout=TIMEOUT_MFA)
    STATE_MFA_EXPIRED = State("We didn't hear from you")

    # Text to phone and code in app
    STATE_OTC_CODE = State("Enter code", timeout=TIMEOUT_MFA)

    DEFAULT_END_STATES = (STATE_MFA, STATE_OTC_CODE)

    def __init__(self, password_manager: PasswordManager, azure_config: AzureAdConfig):
        self.password_manager = password_manager
        self.config = azure_config
        self.cookie_path = os.path.join(DATA_ROOT, f"cookies_{password_manager.username}.json")

    @classmethod
    def _states(cls):
        return [s for key, s in inspect.getmembers(cls) if key.startswith("STATE") and isinstance(s, State)]

    def _on_timeout(self, state: State, state_str: str):
        if state is self.STATE_PWD:
            raise PasswordError(
                f"Failed when submitting password. "
                f"Check the password for '{self.password_manager.username}'."
            ) from None
        raise TimeoutError(f"Timed out in heading '{state_str}'") from None

    def _browser(self) -> PypBrowser:
        return PypBrowser(headless=self.config.headless, dump_io=self.config.dump_io)

    @staticmethod
    async def _wait_for_login_screen(page: Page):
        return await page.waitForXPath("//div[@role='heading']", visible=True)

    async def _wait_for_after_auth(self, page: Page, future):
        wait_main = asyncio.ensure_future(coro_or_future=future)
        wait_login = asyncio.ensure_future(coro_or_future=self._wait_for_login_screen(page))
        done, pending = await asyncio.wait([wait_main, wait_login], return_when=asyncio.FIRST_COMPLETED)

        if wait_main in done:
            LOG.info("Already authenticated.")
            wait_login.cancel()
            return await wait_main
        else:
            LOG.info("Authentication needed")
            await self.authenticate(page, end_states=self.DEFAULT_END_STATES)
            return await wait_main

    async def authenticate(self, page: Page, end_states: Sequence[State]):
        states = self._states()

        heading = "**Init**"
        state = State(heading)

        while True:
            try:
                timeout = state.timeout or self.config.default_timeout
                evt = await page.waitForXPath(
                    f"//div[@role='heading' and text() != '{heading}']",
                    visible=True,
                    timeout=timeout * 1000 if timeout else None
                )
                heading = await page.evaluate('(e) => e.textContent', evt)

                state = State.find(heading, states)
                LOG.info(f"## Header: {heading}")
                if state is None:
                    state = State(heading)
                else:
                    await self._on_state_changed(page, state, heading)
                    if state in end_states:
                        return
            except PypTimeoutError:
                self._on_timeout(state, heading)

    async def _on_state_changed(self, page: Page, s: State, state_str: str):
        if s is self.STATE_PICK_ACC:
            # There is always just one account (because of cookies).
            await page.keyboard.press("Enter")
            LOG.info("Account selected")
        if s is self.STATE_MFA_EXPIRED:
            raise MfaExpiredException("MFA Expired!")
        elif s is self.STATE_SIGN_IN:
            await self._submit_value(page, "input[name=loginfmt]", self.password_manager.username)
            LOG.info("Username submitted")
        elif s is self.STATE_PWD:
            await self._submit_value(page, "input[name=passwd]", self.password_manager.get_password())
            LOG.info("Password submitted")
        elif s is self.STATE_MFA:
            print("Approve the sign-in request on your phone...")
        elif s is self.STATE_PWD_UPDATE:
            print(f"Your password needs to be updated. Login to {self.password_manager.username} in your browser.")
        elif s is self.STATE_OTC_CODE:
            await self._submit_value(page, "input[name=otc]", self.password_manager.ask_for_otc())
            print("One-time-code submitted")

    @classmethod
    async def _enter_value(cls, page: Page, xpath: str, value: str):
        await page.waitFor(xpath, visible=True)
        await page.type(xpath, value)

    @classmethod
    async def _submit_value(cls, page: Page, xpath: str, value: str):
        await cls._enter_value(page, xpath, value)
        await page.keyboard.press("Enter")

    async def _load_cookies(self, page: Page):
        if not self.config.use_cookies:
            return
        elif os.path.exists(self.cookie_path):
            with open(self.cookie_path, mode="r") as f:
                cookies = json.load(f)
            tasks = [asyncio.create_task(page.setCookie(c))
                     for c in cookies if c["name"] not in self.IGNORE_COOKIE_NAMES]
            if len(tasks) > 0:
                await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
            LOG.info(f"Cookies for {self.password_manager.username} loaded.")
        else:
            LOG.info(f"Cookies for {self.password_manager.username} not yet existing.")

    async def _save_cookies(self, page: Page):
        with open(self.cookie_path, mode="w") as f:
            json.dump(await page.cookies(), f)
        LOG.info(f"Cookies for {self.password_manager.username} saved.")
