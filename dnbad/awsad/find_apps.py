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
    app_id: str


class AzureAppsFinder:
    APPS_URL = "https://myapplications.microsoft.com/"
    APP_ITEM_SELECTOR = "div[class=ms-List-cell]"

    def __init__(
            self,
            config: AuthConfig,
            password_manager: PasswordManager,
            timeout=10
    ):
        self.config = config
        self.password_manager = password_manager
        self.timeout = timeout

    def find_apps_sync(self) -> List[AdApp]:
        return asyncio.get_event_loop().run_until_complete(self.find_apps())

    async def find_apps(self) -> List[AdApp]:
        async with single_auth_page(AzureAuthHandler(self.password_manager), self.config) as auth_page:
            await auth_page.page.goto(self.APPS_URL)
            await auth_page.page.waitForSelector(self.APP_ITEM_SELECTOR, visible=True, timeout=self.timeout * 1000)

            # Examine app results:
            ad_apps = await self.query_apps(auth_page.page)
            aws_apps = [app for app in ad_apps if app.title.startswith("AWS")]
            return aws_apps

    @classmethod
    async def query_apps(cls, page: Page) -> List[AdApp]:
        def get_prop(s, key):
            """ Designed to find a value based on key for a url. """
            m = re.search(f"(?<={key}=)[^&']+", s)
            return m.group(0) if m else None

        apps = []
        for element in await page.querySelectorAll(cls.APP_ITEM_SELECTOR):
            link = await element.querySelector("a")
            img = await link.querySelector("img")
            div = await link.querySelector("div")

            img_src = await page.evaluate('(e) => e.getAttribute("src")', img)
            title = await page.evaluate('(e) => e.getAttribute("title")', div)

            apps.append(AdApp(
                title=title,
                tenant_id=get_prop(img_src, 'tenantId'),
                app_id=get_prop(img_src, 'appId')
            ))
        return apps
