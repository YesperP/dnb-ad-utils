import unittest
from dnbad.common.local_config import LocalConfig
from dnbad.awsad.find_apps import AzureAppsFinder, AuthConfig, PasswordManager


class TestFindApps(unittest.TestCase):
    def test_find_apps(self):
        aws_apps = AzureAppsFinder(
            config=AuthConfig(
                headless=False,
                use_cookies=True,
                dump_io=False,
                keep_open=False
            ),
            password_manager=PasswordManager(
                username=LocalConfig.load().username
            )
        ).find_aws_apps_sync()
        print(aws_apps)
