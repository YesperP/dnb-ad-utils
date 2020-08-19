import asyncio
from typing import *

import pyppeteer
from pyppeteer.browser import Browser
from pyppeteer.errors import NetworkError


class PypBrowser:
    def __init__(self, headless: bool, dump_io: bool, keep_open: bool = False):
        self.headless = headless
        self.dump_io = dump_io
        self.keep_open = keep_open
        self.browser: Optional[Browser] = None

    def ignore_pyppeteer_exception_handler(self, loop, context):
        if self.browser and isinstance(context["exception"], NetworkError):
            return
        loop.default_exception_handler(context)

    async def __aenter__(self):
        self.browser = await pyppeteer.launch(headless=self.headless, dump_io=self.dump_io, autoClose=False)
        asyncio.get_running_loop().set_exception_handler(self.ignore_pyppeteer_exception_handler)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if not self.keep_open:
            await self.browser.close()
            self.browser = None
        return False
