import base64
import datetime
import urllib.parse
import uuid
import zlib

from xml.etree import ElementTree
from typing import *


class Saml:
    _SAML_REQUEST = \
        '<samlp:AuthnRequest xmlns="urn:oasis:names:tc:SAML:2.0:metadata" xml' \
        'ns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" ID="id_{id}" Version' \
        '="2.0" IsPassive="false" IssueInstant="{date}" AssertionConsumerServ' \
        'iceURL="https://signin.aws.amazon.com/saml"><Issuer xmlns="urn:oasis' \
        ':names:tc:SAML:2.0:assertion">{app_id}</Issuer><samlp:NameIDPolicy F' \
        'ormat="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"/></sa' \
        'mlp:AuthnRequest>'
    _SAML_URL = 'https://login.microsoftonline.com/{tenant_id}/saml2?SAMLRequest={saml_request}'
    SAML_COMPLETE_URL = 'https://signin.aws.amazon.com/saml'
    _SAML_ATTR_NS = "{urn:oasis:names:tc:SAML:2.0:assertion}"

    @staticmethod
    def response_to_xml(saml_response: str):
        decoded = base64.b64decode(saml_response)
        return ElementTree.XML(decoded)

    @classmethod
    def get_saml_response_values(cls, saml_xml: ElementTree, attr_name: str) -> List[str]:
        values = []
        for attribute in saml_xml.iter(f"{cls._SAML_ATTR_NS}Attribute"):
            if attribute.get("Name") != f"https://aws.amazon.com/SAML/Attributes/{attr_name}":
                continue
            for value in attribute.iter(f"{cls._SAML_ATTR_NS}AttributeValue"):
                values.append(value.text)
        return values

    @classmethod
    def build_url(cls, tenant_id: str, app_id: str):
        saml_request = base64.b64encode(
            zlib.compress(
                cls._SAML_REQUEST.strip().format(
                    date=datetime.datetime.now().strftime("%Y-%m-%dT%H:%m:%SZ"),
                    tenant_id=tenant_id,
                    id=uuid.uuid4(),
                    app_id=app_id
                ).encode('ascii')
            )[2:-4]
        ).decode()
        return cls._SAML_URL.format(
            tenant_id=tenant_id,
            saml_request=urllib.parse.quote(saml_request)
        )
