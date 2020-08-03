import asyncio
from dataclasses import dataclass
from urllib.parse import parse_qs

from pyppeteer.network_manager import Request

from common.azure_auth_page import *
from common.password_manager import PasswordManager
from .saml import Saml
from common.azure_auth_handler import AzureAuthHandler


@dataclass
class SamlLogin:
    auth_config: AuthConfig
    password_manager: PasswordManager
    tenant_id: str
    app_id: str

    def login_sync(self) -> str:
        return asyncio.get_event_loop().run_until_complete(self.login())

    async def login(self) -> str:
        auth_page = AuthPage(
            auth_handler=AzureAuthHandler(self.password_manager),
            config=self.auth_config
        )
        async with auth_page as page:
            url = Saml.build_url(tenant_id=self.tenant_id, app_id=self.app_id)
            await page.goto(url)
            request = await page.waitForRequest(Saml.SAML_COMPLETE_URL)
            saml_response = self._get_saml_response_from_request(request)
            return saml_response

    @classmethod
    def _get_saml_response_from_request(cls, request: Request) -> str:
        return parse_qs(request.postData)['SAMLResponse'][0]
