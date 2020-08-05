import asyncio
import logging

from pyppeteer.page import Page

from dnbad.common.azure_auth import *
from dnbad.common.azure_auth_handler import AzureAuthHandler, AuthState
from dnbad.common.password_manager import PasswordManager

LOG = logging.getLogger(__name__)


class GProxyAdLogin(AzureAuthHandler):
    URL = "https://microsoft.com/devicelogin"
    STATE_GPROXY = AuthState("GitProxy")
    END_STATES = (STATE_GPROXY,)

    def __init__(self, code: str, password_manager: PasswordManager, config: AuthConfig):
        super().__init__(password_manager)
        self.config = config
        self.code = code
        self.code_submitted = False

    def login_sync(self) -> bool:
        return asyncio.get_event_loop().run_until_complete(self.login())

    async def login(self):
        async with single_auth_page(self, self.config) as auth_page:
            await auth_page.page.goto(self.URL)
            await auth_page.await_auth()

    async def _on_state_changed(self, page: Page, s: AuthState):
        """ The first OTC is the GProxy code"""
        if s != self.STATE_OTC_CODE or self.code_submitted:
            await super()._on_state_changed(page, s)
        else:
            await self._submit_value(page, "input[name=otc]", self.code)
            self.code_submitted = True
            LOG.info("GProxy code submitted")
