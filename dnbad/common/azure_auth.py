import asyncio
import logging
from asyncio import Task, create_task, wait
from dataclasses import dataclass
from typing import *

from pyppeteer.page import Page, Request

from .azure_auth_handler import *
from .pyppeteer import PypBrowser

__all__ = ["AuthPage", "AuthConfig", "AuthBrowser"]

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuthConfig:
    headless: bool
    use_cookies: bool
    dump_io: bool
    keep_open: bool

    @staticmethod
    def add_arguments_to_parser(parser):
        parser.add_argument("-n", "--no-headless", help="Login to Azure AD in non-headless mode", action="store_true")
        parser.add_argument("-d", "--debug", help="Debug mode", action="store_true")
        parser.add_argument("-c", "--no-cookies", help="Login without using cookies", action="store_true")
        parser.add_argument("-p", "--profile", help="AWS Profile")

    @classmethod
    def from_args(cls, args) -> "AuthConfig":
        return AuthConfig(
            headless=not args.no_headless,
            use_cookies=not args.no_cookies,
            dump_io=args.debug,
            keep_open=args.debug and not args.no_headless
        )


class AuthPage:
    """
    When entering AuthPage context, the authentication handler is started.
    Upon completion the auth task is cancelled.
    """

    def __init__(self, page: Page, auth_handler: AzureAuthHandler, config: AuthConfig):
        self.page: Page = page
        self.auth_config = config
        self._auth_handler = auth_handler
        self._auth_task: Optional[Task] = None

    async def await_auth(self):
        return await self._auth_task

    async def await_after_auth(self, coroutine: Coroutine):
        main_task = create_task(coroutine)
        done, pending = await wait((main_task, self._auth_task), return_when=asyncio.FIRST_COMPLETED)
        if self._auth_task in done:
            # If auth task completes first, there may be an exception. Make sure that its raised.
            await self._auth_task
        return await main_task

    async def await_request_after_auth(self, url: str) -> Request:
        return await self.await_after_auth(self.page.waitForRequest(url))

    async def __aenter__(self):
        if self.auth_config.use_cookies:
            await self._auth_handler.load_cookies(self.page)
        self._auth_task = create_task(self._auth_handler.handle_auth(self.page))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self._auth_handler.save_cookies(self.page)
            self._auth_task.cancel()
        return False


class AuthBrowser(PypBrowser):
    def __init__(self, auth_handler: AzureAuthHandler, auth_config: AuthConfig):
        super().__init__(auth_config.headless, auth_config.dump_io)
        self.auth_handler = auth_handler
        self.auth_config = auth_config

    async def new_auth_page(self) -> AuthPage:
        return AuthPage(await self.browser.newPage(), self.auth_handler, self.auth_config)
