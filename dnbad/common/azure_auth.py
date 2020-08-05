import asyncio
import logging
from asyncio import Task, create_task, wait
from typing import *

from pyppeteer.page import Page, Request

from .azure_auth_config import AuthConfig
from .azure_auth_handler import *
from .pyppeteer import PypBrowser

__all__ = ["AuthPage", "AuthConfig", "AuthBrowser"]

LOG = logging.getLogger(__name__)


class AuthPage:
    def __init__(self, page: Page, auth_handler: AzureAuthHandler, config: AuthConfig):
        self.page: Page = page
        self._auth_handler = auth_handler
        self._config = config
        self._auth_task: Optional[Task] = None

    async def await_auth(self):
        return await self._auth_task

    async def await_request_after_auth(self, url: str) -> Request:
        main_task = create_task(self.page.waitForRequest(url))
        done, pending = await wait((main_task, self._auth_task), return_when=asyncio.FIRST_COMPLETED)
        if self._auth_task in done:
            # May be an exception. Make sure that its raised.
            await self._auth_task
        return await main_task

    async def __aenter__(self):
        if self._config.use_cookies:
            await self._auth_handler.load_cookies(self.page)
        self._auth_task = create_task(self._auth_handler.handle_auth(self.page))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self._auth_handler.save_cookies(self.page)
            self._auth_task.cancel()
        return False


class AuthBrowser(PypBrowser):
    def __init__(self, auth_handler: AzureAuthHandler, config: AuthConfig):
        super().__init__(config.headless, config.dump_io)
        self.auth_handler = auth_handler
        self.config = config

    async def new_auth_page(self) -> AuthPage:
        return AuthPage(await self.browser.newPage(), self.auth_handler, self.config)
