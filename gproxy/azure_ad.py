import asyncio

from pyppeteer.page import Page

from common.azure_ad_base import *
from common.password_manager import PasswordManager


class AzureGProxyLogin(AzureAdBase):
    URL = "https://microsoft.com/devicelogin"
    STATE_GPROXY = State("GitProxy")

    def __init__(self, code: str, password_manager: PasswordManager, azure_config: AzureAdConfig):
        super().__init__(password_manager, azure_config)
        self.code = code
        self.code_submitted = False

    def login_sync(self) -> bool:
        return asyncio.get_event_loop().run_until_complete(self.login())

    async def login(self):
        async with self._browser() as browser:
            page = await browser.newPage()
            await self._load_cookies(page)
            await page.goto(self.URL, waitUntil='domcontentloaded')
            await self.authenticate(page, end_states=(self.STATE_GPROXY,))
            await self._save_cookies(page)

    async def _on_state_changed(self, page: Page, s: State, state_str: str):
        """ The first OTC is the GProxy code"""
        if s != self.STATE_OTC_CODE or self.code_submitted:
            await super()._on_state_changed(page, s, state_str)
        else:
            await self._submit_value(page, "input[name=otc]", self.code)
            self.code_submitted = True
            print("GProxy code submitted")
