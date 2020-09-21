import datetime
import logging
from dataclasses import dataclass
from typing import *
from xml.etree import ElementTree

import boto3
from dateutil import tz

from dnbad.common.configure import *
from dnbad.common.local_config import LocalConfig
from dnbad.common.password_manager import PasswordManager
from .aws_config import AwsConfig
from .saml import Saml
from .saml_login import SamlLogin, AuthConfig

LOG = logging.getLogger(__name__)


@dataclass
class AwsSAMLRole:
    arn: str
    principal_arn: str

    def account(self):
        return self.arn.split(":")[4]

    def role_name(self):
        return self.arn.split("/")[1]


class AwsAd:
    AWS_MIN_SESSION_DURATION = 900

    def __init__(self, profile: str):
        self.profile = profile
        self._local_config = LocalConfig.load()
        self._aws_config: AwsConfig = AwsConfig.load(profile)

    def has_valid_credentials(self) -> bool:
        return self._aws_config.aws_expiration_time is not None and \
               self._aws_config.aws_expiration_time > datetime.datetime.now(tz.UTC)

    def session(self) -> boto3.Session:
        return boto3.Session(profile_name=self.profile)

    @classmethod
    def _get_aws_saml_roles(cls, saml_xml: ElementTree) -> List[AwsSAMLRole]:
        roles = []
        for value in Saml.get_saml_response_values(saml_xml, "Role"):
            s = value.split(",")
            if "saml-provider" in s[0]:
                roles.append(AwsSAMLRole(arn=s[1], principal_arn=s[0]))
            else:
                roles.append(AwsSAMLRole(arn=s[0], principal_arn=s[1]))
        return roles

    def _put_credentials_in_config(self, credentials: dict, role_arn: str):
        self._aws_config.aws_role_arn = role_arn
        self._aws_config.aws_access_key_id = credentials["AccessKeyId"]
        self._aws_config.aws_secret_access_key = credentials["SecretAccessKey"]
        self._aws_config.aws_session_token = credentials["SessionToken"]
        self._aws_config.aws_expiration_time = credentials["Expiration"].replace(tzinfo=tz.UTC)

    def _choose_role(self, roles: List[AwsSAMLRole]) -> AwsSAMLRole:
        if len(roles) == 0:
            raise Exception("No roles found for your account.")
        elif len(roles) == 1:
            return roles[0]

        matching_roles = [r for r in roles if r.arn == self._aws_config.aws_default_role_arn]
        if len(matching_roles) == 1:
            return matching_roles[0]

        role_name = get_input("Choose the role you want to assume", allowed_values=[role.role_name() for role in roles])
        role = max(roles, key=lambda r: r.role_name() == role_name)
        make_default = yes_no("Do you want this to be the default role for the profile?", default=False)
        if make_default:
            self._aws_config.aws_default_role_arn = role
        return role

    @classmethod
    def _get_max_session_duration(cls, saml_response: str, role: AwsSAMLRole) -> int:
        min_credentials = boto3.client('sts').assume_role_with_saml(
            RoleArn=role.arn,
            PrincipalArn=role.principal_arn,
            SAMLAssertion=saml_response,
            DurationSeconds=cls.AWS_MIN_SESSION_DURATION
        )["Credentials"]
        return boto3.Session(
            aws_access_key_id=min_credentials["AccessKeyId"],
            aws_secret_access_key=min_credentials["SecretAccessKey"],
            aws_session_token=min_credentials["SessionToken"]
        ).resource("iam").Role(role.role_name()).max_session_duration

    @classmethod
    def _assume_role(cls, saml_response: str, role: AwsSAMLRole, session_duration: Optional[int]) -> dict:
        return boto3.client('sts').assume_role_with_saml(
            RoleArn=role.arn,
            PrincipalArn=role.principal_arn,
            SAMLAssertion=saml_response,
            DurationSeconds=session_duration
        )["Credentials"]

    def login_if_invalid_credentials(self, auth_config: Optional[AuthConfig] = None) -> "AwsAd":
        if not self.has_valid_credentials():
            self.login(auth_config)
        return self

    def setup_default_boto3_session(self, region_name: Optional[str] = None) -> "AwsAd":
        boto3.setup_default_session(profile_name=self.profile, region_name=region_name)
        return self

    def login(self, auth_config: Optional[AuthConfig] = None):
        auth_config = auth_config or AuthConfig()
        saml_response = SamlLogin(
            auth_config=auth_config,
            password_manager=PasswordManager(self._local_config.username),
            tenant_id=self._aws_config.azure_tenant_id,
            app_id=self._aws_config.azure_app_id
        ).login()
        LOG.info("SAML Response retrieved")

        saml_xml = Saml.response_to_xml(saml_response)
        aws_roles = self._get_aws_saml_roles(saml_xml)
        aws_role = self._choose_role(aws_roles)

        if self._aws_config.aws_session_duration is None:
            max_session_duration = self._get_max_session_duration(saml_response, aws_role)
            self._aws_config.aws_session_duration = max_session_duration

        credentials = self._assume_role(
            saml_response=saml_response,
            role=aws_role,
            session_duration=self._aws_config.aws_session_duration
        )
        self._put_credentials_in_config(credentials, aws_role.arn)
        self._aws_config.save()

        delimiter = ''.join(['-'] * 60)
        expiration_time = self._aws_config.aws_expiration_time.astimezone(tz.tzlocal())
        print(
            f"\n{delimiter}\n"
            f"Access credentials stored in AWS credentials file.\n"
            f"Account: '{self._aws_config.azure_app_title}'\n"
            f"Profile: '{self._aws_config.profile or 'default'}'.\n"
            f"Associated role: '{aws_role.role_name()}'.\n"
            f"Credentials expire at {expiration_time:%Y-%m-%d %H:%M:%S %Z}.\n"
            f"{delimiter}"
        )
