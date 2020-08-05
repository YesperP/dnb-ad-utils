import asyncio
from dataclasses import dataclass
from urllib.parse import parse_qs

from pyppeteer.network_manager import Request

from dnbad.common.azure_auth import *
from dnbad.common.azure_auth_handler import AzureAuthHandler
from dnbad.common.password_manager import PasswordManager
from .saml import Saml


@dataclass
class SamlLogin:
    auth_config: AuthConfig
    password_manager: PasswordManager
    tenant_id: str
    app_id: str

    def login(self) -> str:
        return asyncio.get_event_loop().run_until_complete(self._login())

    async def _login(self) -> str:
        async with single_auth_page(AzureAuthHandler(self.password_manager), self.auth_config) as auth_page:
            url = Saml.build_url(tenant_id=self.tenant_id, app_id=self.app_id)
            await auth_page.page.goto(url)
            request = await auth_page.await_request_after_auth(Saml.SAML_COMPLETE_URL)
            return self._get_saml_response_from_request(request)

    @classmethod
    def _get_saml_response_from_request(cls, request: Request) -> str:
        return parse_qs(request.postData)['SAMLResponse'][0]
