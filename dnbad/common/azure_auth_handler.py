import asyncio
import inspect
import json
import logging
import os
from dataclasses import dataclass
from typing import *

from pyppeteer.errors import TimeoutError as PypTimeoutError
from pyppeteer.page import Page

from dnbad.common import DATA_ROOT
from dnbad.common.exceptions import DnbException
from dnbad.common.password_manager import PasswordManager

__all__ = ["MfaExpiredException", "AuthState", "AzureAuthHandler"]

LOG = logging.getLogger(__name__)


class MfaExpiredException(DnbException):
    pass


class PasswordError(DnbException):
    pass


@dataclass(init=False)
class AuthState:
    matches: Tuple[str]
    timeout: Optional[int]

    def __init__(self, *matches: str, timeout=None):
        self.matches = matches
        self.timeout = timeout

    @staticmethod
    def find(s: str, states: List["AuthState"], default=None):
        matching = [state for state in states if s in state.matches]
        if len(matching) > 1:
            raise Exception("More than one state matching heading.")
        elif len(matching) == 1:
            return matching[0]
        else:
            return default


class AzureAuthHandler:
    DEFAULT_TIMEOUT = 20
    TIMEOUT_MFA = 120
    AZURE_BASE_URL = "https://login.microsoftonline.com"
    # For some reason this cookie creates an error when used, but it is not needed for restoring session.
    IGNORE_COOKIE_NAMES = ["esctx"]

    STATE_PICK_ACC = AuthState("Pick an account")
    STATE_SIGN_IN = AuthState("Sign in")
    STATE_PWD = AuthState("Enter password")
    STATE_PWD_UPDATE = AuthState("Update your password")
    STATE_TRYING_TO_SIGN_YOU_IN = AuthState("Trying to sign you in")

    # App and phone call.
    STATE_MFA = AuthState("Approve sign-in request", "Approve sign in request", timeout=TIMEOUT_MFA)
    STATE_MFA_EXPIRED = AuthState("We didn't hear from you")

    # Text to phone and code in app
    STATE_OTC_CODE = AuthState("Enter code", timeout=TIMEOUT_MFA)

    END_STATES = (STATE_MFA, STATE_OTC_CODE)

    def __init__(self, password_manager: PasswordManager):
        self.password_manager = password_manager
        self.cookie_path = os.path.join(DATA_ROOT, f"cookies_{password_manager.username}.json")

    @classmethod
    def _states(cls):
        return [s for key, s in inspect.getmembers(cls) if key.startswith("STATE") and isinstance(s, AuthState)]

    async def handle_auth(self, page: Page):
        states = self._states()
        heading = "**Init**"
        state = AuthState(heading)

        while True:
            try:
                timeout = state.timeout or self.DEFAULT_TIMEOUT
                evt = await page.waitForXPath(
                    f"//div[@role='heading' and text() != '{heading}']",
                    visible=True,
                    timeout=timeout * 1000 if timeout else None
                )
                heading = await page.evaluate('(e) => e.textContent', evt)
                LOG.info(f"## AuthHeader: {heading}")

                state = AuthState.find(heading, states)
                if state is None:
                    state = AuthState(heading)
                else:
                    await self._on_state_changed(page, state)
                    if state in self.END_STATES:
                        return
            except PypTimeoutError:
                self._on_timeout(state, heading)

    async def _on_state_changed(self, page: Page, s: AuthState):
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
            LOG.info("Approve the sign-in request on your phone...")
        elif s is self.STATE_PWD_UPDATE:
            LOG.warning(f"Your password needs to be updated. "
                        f"Login to {self.password_manager.username} in your browser.")
        elif s is self.STATE_OTC_CODE:
            await self._submit_value(page, "input[name=otc]", self.password_manager.ask_for_otc())
            LOG.info("One-time-code submitted")

    def _on_timeout(self, state: AuthState, heading: str):
        if state is self.STATE_PWD:
            raise PasswordError(
                f"Failed when submitting password. "
                f"Check the password for '{self.password_manager.username}'."
            ) from None
        raise TimeoutError(f"Timed out in heading '{heading}'") from None

    @classmethod
    async def _enter_value(cls, page: Page, xpath: str, value: str):
        await page.waitFor(xpath, visible=True)
        await page.type(xpath, value)

    @classmethod
    async def _submit_value(cls, page: Page, xpath: str, value: str):
        await cls._enter_value(page, xpath, value)
        await page.keyboard.press("Enter")

    async def load_cookies(self, page: Page):
        if os.path.exists(self.cookie_path):
            with open(self.cookie_path, mode="r") as f:
                cookies = json.load(f)
            tasks = [asyncio.create_task(page.setCookie(c))
                     for c in cookies if c["name"] not in self.IGNORE_COOKIE_NAMES]
            if len(tasks) > 0:
                await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
            LOG.debug(f"Cookies for {self.password_manager.username} loaded.")
        else:
            LOG.info(f"Cookies for {self.password_manager.username} not yet existing.")

    async def save_cookies(self, page: Page):
        with open(self.cookie_path, mode="w") as f:
            json.dump(await page.cookies(), f)
        LOG.debug(f"Cookies for {self.password_manager.username} saved.")
