from typing import *

from botocore.session import Session

from dnbad.common.azure_auth import AuthConfig
from dnbad.common.configure import *
from dnbad.common.local_config import LocalConfig
from dnbad.common.password_manager import PasswordManager
from dnbad.common.utils import format_list
from .aws_config import AwsConfig, MissingAwsConfigException
from .find_apps import AzureAppsFinder

__all__ = ["AWSAdConfigure"]


class AWSAdConfigure:

    @classmethod
    def list_profiles(cls) -> str:
        all_profiles: List[Optional[str]] = [None] + sorted(name for name in Session().full_config["profiles"].keys())
        config_status = []
        for profile_name in all_profiles:
            try:
                AwsConfig.load(profile_name)
                config_status.append(True)
            except MissingAwsConfigException:
                config_status.append(False)
        profile_display = [f"{p if p else 'default':<20}{'' if status else '(not configured)'}"
                           for p, status in zip(all_profiles, config_status)]
        return format_list(profile_display)

    def _get_profile(self) -> str:
        print(f"We found the existing AWS profiles:\n{self.list_profiles()}")
        print(f"You can choose an existing profile or create a new one.")
        profile = get_input("AWS Profile")
        return None if profile == "default" else profile

    def configure(
            self,
            auth_config: AuthConfig,
            profile: Optional[str]
    ):
        # Do general configuration:
        general_config()

        header(f"AwsAd Config")
        profile = profile or self._get_profile()

        # Load the current config for the profile:
        try:
            config = AwsConfig.load(profile)
        except MissingAwsConfigException:
            # noinspection PyTypeChecker
            config = AwsConfig(
                profile=profile,

                azure_tenant_id=None,
                azure_app_id=None,
                azure_app_title=None,
                aws_session_duration=None,
                aws_default_role_arn=None,

                aws_access_key_id=None,
                aws_secret_access_key=None,
                aws_session_token=None,
                aws_expiration_time=None
            )

        # App:
        if config.azure_tenant_id and config.azure_app_id and config.azure_app_title:
            if yes_no(f"Do you want to change aws account from '{config.azure_app_title}'?", default=False):
                self._choose_app(config, auth_config)
        else:
            self._choose_app(config, auth_config)

        config.aws_default_role_arn = get_input(
            "Default Role Arn",
            hint="optional",
            default=config.aws_default_role_arn
        )
        config.save()

        header("AwsAd Configuration Completed")
        print("You may run the configuration again at any time.")

    @classmethod
    def _choose_app(cls, aws_config: AwsConfig, auth_config: AuthConfig):
        try:
            cls._choose_app_auto(aws_config, auth_config)
        except Exception:
            print("Something went wrong with finding your apps... Please enter manually")
            cls._choose_app_manual(aws_config)

    @classmethod
    def _choose_app_auto(cls, aws_config: AwsConfig, auth_config: AuthConfig):
        print("Finding aws accounts...")
        apps = AzureAppsFinder(
            password_manager=PasswordManager(LocalConfig.load().username),
            config=auth_config
        ).find_aws_apps_sync()

        app_titles = [app.title for app in apps]
        print(f"We have found the following aws accounts:\n{format_list(app_titles)}")
        app_title = get_input("Pick aws account", hint="", allowed_values=app_titles)
        app = max(apps, key=lambda a: a.title == app_title)
        aws_config.azure_app_title = app.title
        aws_config.azure_app_id = app.app_id
        aws_config.azure_tenant_id = app.tenant_id

    @classmethod
    def _choose_app_manual(cls, aws_config: AwsConfig):
        aws_config.azure_app_id = get_input("Azure app id")
        aws_config.azure_tenant_id = get_input("Azure tenant id")
        aws_config.azure_app_title = get_input("App Title", hint="AWS-something")
