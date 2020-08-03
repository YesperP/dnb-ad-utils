import asyncio
import logging
from asyncio import Task
from dataclasses import dataclass
from typing import *
from .azure_auth_config import AuthConfig
from pyppeteer.browser import Page

from .azure_auth_handler import *
from .pyppeteer import PypBrowser

__all__ = ["AuthPage", "AuthConfig"]

LOG = logging.getLogger(__name__)


class AuthPage(PypBrowser):
    def __init__(self, auth_handler: AzureAuthHandler, config: AuthConfig):
        super().__init__(config.headless, config.dump_io, config.keep_open)
        self.auth_handler = auth_handler
        self.config = config
        self._auth_task: Optional[Task] = None

    async def __aenter__(self) -> Page:
        browser = await super().__aenter__()
        self.page = await browser.newPage()
        if self.config.use_cookies:
            await self.auth_handler.load_cookies(self.page)
        self._auth_task = asyncio.create_task(self.auth_handler.handle_auth(self.page))
        return self.page

    async def await_auth(self):
        return await self._auth_task

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.auth_handler.save_cookies(self.page)
            self._auth_task.cancel()
        return await super().__aexit__(exc_type, exc_val, exc_tb)
