from urllib.parse import parse_qs

from pyppeteer.network_manager import Request

from common.azure_ad_base import *
from common.password_manager import PasswordManager
from .saml import Saml
import asyncio


class AzureAwsLogin(AzureAdBase):
    def __init__(
            self,
            password_manager: PasswordManager,
            config: AzureAdConfig
    ):
        super().__init__(password_manager, config)
        self.saml_response = None
        self.tenant_id = None

    def login_sync(self, tenant_id: str, app_id: str) -> str:
        return asyncio.get_event_loop().run_until_complete(self.login(tenant_id, app_id))

    async def login(self, tenant_id: str, app_id: str) -> str:
        async with self._browser() as browser:
            page = await browser.newPage()
            await self._load_cookies(page)

            # We make the SAML request
            url = Saml.build_url(tenant_id=tenant_id, app_id=app_id)
            await page.goto(url)

            request = await self._wait_for_after_auth(
                page=page,
                future=page.waitForRequest(Saml.SAML_COMPLETE_URL)
            )
            saml_response = self._get_saml_response_from_request(request)

            await self._save_cookies(page)
            return saml_response

    @classmethod
    def _get_saml_response_from_request(cls, request: Request) -> str:
        return parse_qs(request.postData)['SAMLResponse'][0]
