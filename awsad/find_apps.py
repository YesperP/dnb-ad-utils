import re
from dataclasses import dataclass
from typing import *

from pyppeteer.page import Page

from common.azure_ad_base import *
import asyncio
from common.password_manager import PasswordManager

__all__ = ["AzureAppsFinder", "AzureAdConfig", "PasswordManager"]


@dataclass(frozen=True)
class AdApp:
    title: str
    tenant_id: str
    app_type: Optional[str]
    app_id: str


class AzureAppsFinder(AzureAdBase):
    APPS_URL = "https://account.activedirectory.windowsazure.com/r#/applications"
    APPS_SELECTOR = "div[ng-model=app]"

    def find_apps_sync(self) -> List[AdApp]:
        return asyncio.get_event_loop().run_until_complete(self.find_apps())

    async def find_apps(self) -> List[AdApp]:
        async with self._browser() as browser:
            page = await browser.newPage()
            await self._load_cookies(page)
            await page.goto(self.APPS_URL)
            await self._wait_for_after_auth(
                page=page,
                future=page.waitForSelector(self.APPS_SELECTOR, visible=True)
            )

            # Examine app results:
            ad_apps = await self.query_apps(page)
            aws_apps = [app for app in ad_apps if app.app_type == "aws"]
            await self._save_cookies(page)
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
