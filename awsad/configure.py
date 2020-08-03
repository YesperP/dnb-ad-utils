from typing import *

from botocore.session import Session

from awsad.find_apps import *
from common.configure import *
from common.local_config import LocalConfig
from .aws_config import AwsConfig, MissingAwsConfigException
from pprint import pformat

__all__ = ["AWSAdConfigure"]


class AWSAdConfigure:
    @classmethod
    def _format_list(cls, iterable: Iterable[str]):
        return '\n'.join(f"• {e}" for e in sorted(iterable))

    @classmethod
    def list_profiles(cls) -> str:
        all_profiles: List[Optional[str]] = [None] + sorted(name for name in Session().full_config["profiles"].keys())
        config_status = []
        for profile_name in all_profiles:
            try:
                AwsConfig.load(Session(profile=profile_name))
                config_status.append(True)
            except MissingAwsConfigException:
                config_status.append(False)
        profile_display = [f"{p if p else 'default':<20}{'' if status else '(not configured)'}"
                           for p, status in zip(all_profiles, config_status)]
        return cls._format_list(profile_display)

    def _get_profile(self) -> str:
        print(f"We found the existing AWS profiles:\n{self.list_profiles()}")
        print(f"You can choose an existing profile or create a new one.")
        profile = get_input("AWS Profile")
        return None if profile == "default" else profile

    def configure(
            self,
            profile: Optional[str] = None
    ):
        # Do general configuration:
        general_config()

        header(f"AwsAd Config")

        session = Session(profile=profile or self._get_profile())

        # Load the current config for the profile:
        try:
            config = AwsConfig.load(session)
        except MissingAwsConfigException:
            # noinspection PyTypeChecker
            config = AwsConfig(
                azure_tenant_id=None,
                azure_app_id=None,
                azure_app_title=None,
                aws_session_duration=None,
                aws_default_role_arn=None,

                aws_role_arn=None,
                aws_access_key_id=None,
                aws_secret_access_key=None,
                aws_session_token=None
            )

        # App:
        if config.azure_tenant_id and config.azure_app_id and config.azure_app_title:
            if yes_no(f"Do you want to change aws account from '{config.azure_app_title}'?", default=False):
                self._choose_app(config)
        else:
            self._choose_app(config)

        config.aws_default_role_arn = get_input(
            "Default Role Arn",
            hint="optional",
            default=config.aws_default_role_arn
        )
        config.save(session)

        header("AwsAd Configuration Completed")
        print("You may run the configuration again at any time.")

    def _choose_app(self, config: AwsConfig):
        print("Finding aws accounts...")
        apps = AzureAppsFinder(
            password_manager=PasswordManager(LocalConfig.load().username),
            azure_config=AzureAdConfig(
                headless=True,
                use_cookies=True,
                dump_io=False
            )
        ).find_apps_sync()

        app_titles = [app.title for app in apps]
        print(f"We have found the following aws accounts:\n{self._format_list(app_titles)}")
        app_title = get_input("Pick aws account", hint="", allowed_values=app_titles)
        app = max(apps, key=lambda a: a.title == app_title)
        config.azure_app_title = app.title
        config.azure_app_id = app.app_id
        config.azure_tenant_id = app.tenant_id
