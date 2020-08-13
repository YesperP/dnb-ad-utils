from dataclasses import dataclass, asdict
from os import path
from typing import *

from awscli.customizations.configure.writer import ConfigFileWriter
from botocore.exceptions import ProfileNotFound
from botocore.session import Session

from dnbad.common.exceptions import DnbException

__all__ = ["MissingAwsConfigException", "AwsConfig"]


class MissingAwsConfigException(DnbException):
    def __init__(self, profile: Optional[str]):
        super().__init__(f"Missing Aws Config for '{profile or 'default'}'. You must configure awsad.")


@dataclass
class AwsConfig:
    profile: str

    azure_tenant_id: str
    azure_app_id: str
    azure_app_title: str
    aws_default_role_arn: Optional[str]
    aws_session_duration: Optional[str]

    aws_access_key_id: Optional[str]
    aws_secret_access_key: Optional[str]
    aws_session_token: Optional[str]

    @staticmethod
    def config_file_path(session: Session, expand_user: bool = False):
        config_path = session.get_config_variable("config_file")
        return path.expanduser(config_path) if expand_user else config_path

    @staticmethod
    def credentials_file_path(session: Session, expand_user: bool = False):
        cred_path = session.get_config_variable("credentials_file")
        return path.expanduser(cred_path) if expand_user else cred_path

    def values(self) -> dict:
        return asdict(self)

    @classmethod
    def load(cls, profile: str) -> Optional["AwsConfig"]:
        session = Session(profile=profile)
        try:
            c = session.get_scoped_config()
        except ProfileNotFound:
            raise MissingAwsConfigException(session.profile)

        def get(key: str, func: Callable = None):
            val = c.get(key)
            if val is None or val == "None":
                return None
            else:
                return func(val) if func else val

        try:
            return cls(
                profile=profile,

                azure_tenant_id=c["awsad-azure_tenant_id"],
                azure_app_id=c["awsad-azure_app_id"],
                azure_app_title=c["awsad-azure_app_title"],
                aws_default_role_arn=get("awsad-aws_default_role_arn"),
                aws_session_duration=get("awsad-aws_session_duration", int),

                aws_access_key_id=get("aws_access_key_id"),
                aws_secret_access_key=get("aws_secret_access_key"),
                aws_session_token=get("aws_session_token")
            )
        except KeyError:
            raise MissingAwsConfigException(session.profile)

    def save(self):
        session = Session(profile=self.profile)
        writer = ConfigFileWriter()
        values = {
            "awsad-azure_tenant_id": self.azure_tenant_id,
            "awsad-azure_app_id": self.azure_app_id,
            "awsad-azure_app_title": self.azure_app_title,
            "awsad-aws_default_role_arn": self.aws_default_role_arn,
            "awsad-aws_session_duration": self.aws_session_duration
        }
        if session.profile is not None:
            values["__section__"] = f"profile {session.profile}"
        writer.update_config(values, self.config_file_path(session, expand_user=True))

        writer = ConfigFileWriter()
        values = {
            "aws_access_key_id": self.aws_access_key_id,
            "aws_secret_access_key": self.aws_secret_access_key,
            "aws_session_token": self.aws_session_token
        }
        if session.profile is not None:
            values["__section__"] = session.profile
        writer.update_config(values, self.credentials_file_path(session, expand_user=True))
