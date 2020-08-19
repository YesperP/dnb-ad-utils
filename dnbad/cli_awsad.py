from typing import *

from dnbad.awsad import *
from dnbad.common.azure_auth import AuthConfig
from dnbad.common.cli_base import CliBase, Namespace


def main() -> int:
    return AwsAdCli().handle()


class AwsAdCli(CliBase):
    def __init__(self):
        super().__init__("awsad", "AWS Login with Azure AD")
        p_login = self.add_cmd("login", "Login and store credentials in .aws/credentials")
        AuthConfig.add_arguments_to_parser(p_login)
        self._add_profile(p_login)

        p_configure = self.add_cmd("configure", "Configure a profile")
        AuthConfig.add_arguments_to_parser(p_configure)
        self._add_profile(p_configure)

        self.add_cmd("list", "List all AWS profiles")

        p_status = self.add_cmd("status", "Get status of credentials")
        self._add_profile(p_status)

    @staticmethod
    def _add_profile(parser):
        parser.add_argument("-p", "--profile", help="AWS Profile")

    def _handle_cmd(self, cmd: str, args: Namespace) -> Optional[bool]:
        if cmd == "login":
            return AwsAd(
                profile=args.profile
            ).login(
                auth_config=AuthConfig.from_args(args)
            )
        elif args.cmd == "configure":
            return AWSAdConfigure().configure(
                profile=args.profile,
                auth_config=AuthConfig.from_args(args)
            )
        elif args.cmd == "list":
            print(f"AWS Profiles:\n{AWSAdConfigure.list_profiles()}")
            return True
        elif args.cmd == "status":
            status = AwsAd(profile=args.profile).has_valid_credentials()
            print(f"Credentials: {'Valid' if status else 'Invalid'}")
            return status


if __name__ == '__main__':
    main()
