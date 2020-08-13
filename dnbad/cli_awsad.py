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

        p_configure = self.add_cmd("configure", "Configure a profile")
        AuthConfig.add_arguments_to_parser(p_configure)

        self.add_cmd("list", "List all AWS profiles")

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


if __name__ == '__main__':
    main()
