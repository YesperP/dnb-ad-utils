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
    APP_ITEM_SELECTOR = "img[alt*=AWS]"

    def __init__(
            self,
            config: AuthConfig,
            password_manager: PasswordManager,
            timeout=10
    ):
        self.config = config
        self.password_manager = password_manager
        self.timeout = timeout

    def find_aws_apps_sync(self) -> List[AdApp]:
        return asyncio.get_event_loop().run_until_complete(self.find_aws_apps())

    async def find_aws_apps(self) -> List[AdApp]:
        async with single_auth_page(AzureAuthHandler(self.password_manager), self.config) as auth_page:
            await auth_page.page.goto(self.APPS_URL)
            await auth_page.await_after_auth(auth_page.page.waitForSelector(self.APP_ITEM_SELECTOR, visible=True))

            # Examine app results:
            return await self.query_apps(auth_page.page)

    @classmethod
    async def query_apps(cls, page: Page) -> List[AdApp]:
        def get_url_attr(s, key):
            """ Designed to find a value based on key for a url. """
            m = re.search(f"(?<={key}=)[^&']+", s)
            return m.group(0) if m else None

        async def get_attr(handle, attribute):
            return await page.evaluate(f'(e) => e.getAttribute("{attribute}")', handle)

        apps = []
        aws_items = await page.querySelectorAll(cls.APP_ITEM_SELECTOR)
        for item in aws_items:

            title = await get_attr(item, "alt")
            img_src = await get_attr(item, "src")

            apps.append(AdApp(
                title=title,
                tenant_id=get_url_attr(img_src, 'tenantId'),
                app_id=get_url_attr(img_src, 'appId')
            ))
        return apps
