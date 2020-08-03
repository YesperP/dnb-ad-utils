import re
from dataclasses import dataclass
from typing import *

from dnbad.common import PasswordManager
from pyppeteer.page import Page

__all__ = ["AzureAppsFinder", "AuthConfig", "PasswordManager"]


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
        auth_page = AuthPage(
            auth_handler=AzureAuthHandler(self.password_manager, self.config),
            config=self.config
        )

        async with auth_page as page:
            await page.goto(self.APPS_URL)
            await page.waitForSelector(self.APPS_SELECTOR, visible=True)

            # Examine app results:
            ad_apps = await self.query_apps(page)
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
