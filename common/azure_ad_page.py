import asyncio
import logging

from pyppeteer.browser import Browser, Page

from .azure_ad_base import AzureAdBase
from .azure_ad_base import AzureAdConfig
from .password_manager import PasswordManager
from .pyppeteer import PypBrowser

LOG = logging.getLogger(__name__)


class AdPage(PypBrowser):
    def __init__(self, headless: bool, dump_io: bool, password_manager: PasswordManager):
        super().__init__(headless, dump_io)
        self.password_manager = password_manager
        self.browser: Browser = None
        self.page: Page = None
        self.auth_task = None

    def __aenter__(self) -> "AdPage":
        self.browser = await super().__aenter__()
        self.page = await self.browser.newPage()
        self.auth_task = asyncio.create_task(AzureAdBase(self.password_manager, azure_config=AzureAdConfig(
            headless=True,
            use_cookies=True,
            dump_io=False
        )).authenticate(self.page, end_states=AzureAdBase.DEFAULT_END_STATES))
        return self
