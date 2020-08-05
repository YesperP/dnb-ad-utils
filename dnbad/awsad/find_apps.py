import asyncio
import re
from dataclasses import dataclass
from typing import *

from pyppeteer.page import Page

from dnbad.common.azure_auth import *
from dnbad.common.password_manager import PasswordManager


@dataclass(frozen=True)
class AdApp:
    title: str
    tenant_id: str
    app_type: Optional[str]
    app_id: str


class AzureAppsFinder:
    APPS_URL = "https://account.activedirectory.windowsazure.com/r#/applications"
    APPS_SELECTOR = "div[ng-model=app]"

    def __init__(
            self,
            config: AuthConfig,
            password_manager: PasswordManager
    ):
        self.config = config
        self.password_manager = password_manager

    def find_apps_sync(self) -> List[AdApp]:
        return asyncio.get_event_loop().run_until_complete(self.find_apps())

    async def find_apps(self) -> List[AdApp]:
        async with single_auth_page(AzureAuthHandler(self.password_manager), self.config) as auth_page:
            await auth_page.page.goto(self.APPS_URL)
            await auth_page.page.waitForSelector(self.APPS_SELECTOR, visible=True)

            # Examine app results:
            ad_apps = await self.query_apps(auth_page.page)
            aws_apps = [app for app in ad_apps if app.app_type == "aws"]
            return aws_apps

    @classmethod
    async def query_apps(cls, page: Page) -> List[AdApp]:
        def get_prop(s, key):
            m = re.search(f"(?<={key}=)[^&']+", s)
            return m.group(0) if m else None

        apps = []
        for element in await page.querySelectorAll("div[ng-model=app]"):
            title_att = await page.evaluate('(e) => e.getAttribute("title")', element)
            tile_click_att = await page.evaluate('(e) => e.getAttribute("tile-click")', element)
            apps.append(AdApp(
                title=title_att,
                tenant_id=get_prop(tile_click_att, 'tenantId'),
                app_type=get_prop(tile_click_att, 'ApplicationConstName'),
                app_id=get_prop(tile_click_att, 'applicationId')
            ))
        return apps
