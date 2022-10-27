import asyncio
import logging

from pyppeteer.page import Page

from dnbad.common.azure_auth import *
from dnbad.common.azure_auth_handler import AzureAuthHandler, AuthState
from dnbad.common.password_manager import PasswordManager

LOG = logging.getLogger(__name__)


class GProxyAdLogin:
    URL = "https://microsoft.com/devicelogin"

    def __init__(self, code: str, password_manager: PasswordManager, config: AuthConfig):
        self.auth_handler = GProxyAzureAuthHandler(code, password_manager)
        self.config = config

    def login_sync(self) -> bool:
        return asyncio.get_event_loop().run_until_complete(self.login())

    async def login(self):
        async with single_auth_page(self.auth_handler, self.config) as auth_page:
            LOG.info(f"Navigating to: {self.URL}")
            await auth_page.page.goto(self.URL)
            await auth_page.await_auth()


class GProxyAzureAuthHandler(AzureAuthHandler):
    """ Specialized auth handler for the GProxy auth flow. """

    STATE_GPROXY = AuthState("GitProxy")
    END_STATES = (STATE_GPROXY,)

    def __init__(self, code, password_manager: PasswordManager):
        super().__init__(password_manager)
        self.code = code
        self.code_submitted = False

    async def _on_state_changed(self, page: Page, s: AuthState):
        """ The first OTC is the GProxy code """
        if s == self.STATE_OTC_CODE and not self.code_submitted:
            await self._submit_value(page, "input[name=otc]", self.code)
            self.code_submitted = True
            LOG.info("GProxy code submitted")
        elif s == self.STATE_TRYING_TO_SIGN_GIT_PROXY:
            await page.keyboard.press("Enter")
        else:
            await super()._on_state_changed(page, s)
