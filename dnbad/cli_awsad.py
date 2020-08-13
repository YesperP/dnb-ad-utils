from typing import *

from dnbad.awsad.awsad import AwsAd, AuthConfig
from dnbad.awsad.configure import AWSAdConfigure
from dnbad.common.cli_base import CliBase, Namespace


def main() -> int:
    return AwsAdCli().handle()


class AwsAdCli(CliBase):
    def __init__(self):
        super().__init__("awsad", "AWS Login with Azure AD")
        p_login = self.add_cmd("login", "Login and store credentials")
        AuthConfig.add_arguments_to_parser(p_login)
        p_login.add_argument("-p", "--profile", help="AWS Profile")

        p_configure = self.add_cmd("configure", "Configure a profile")
        AuthConfig.add_arguments_to_parser(p_configure)

        self.add_cmd("list", "List all AWS profiles")

        p_status = self.add_cmd("status", "Get status of credentials")
        p_status.add_argument("-p", "--profile", help="AWS Profile")

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
