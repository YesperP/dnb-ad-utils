import argparse
import sys
import traceback

from botocore.session import Session

from dnbad.awsad.awsad import AwsAdLogin, AuthConfig
from dnbad.awsad.configure import AWSAdConfigure
from dnbad.common import VERSION
from dnbad.common.exceptions import DnbException


# noinspection PyBroadException
def main() -> [int, None]:
    parser = argparse.ArgumentParser(
        prog="awsad",
        description="AWS Login with Azure AD"
    )
    parser.add_argument("-v", "--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="cmd")

    p_login = subparsers.add_parser("login")
    AuthConfig.add_arguments_to_parser(p_login)

    p_configure = subparsers.add_parser("configure")
    AuthConfig.add_arguments_to_parser(p_configure)

    subparsers.add_parser("list")

    args = parser.parse_args()

    if args.cmd is None:
        parser.print_help()
        return 1

    try:
        _main(args)
        return 0
    except DnbException as e:
        if args.debug:
            traceback.print_exc()
        else:
            print(f"\n{str(e)}", file=sys.stderr)
    except Exception:
        traceback.print_exc()
    return 1


def _main(args):
    if args.cmd == "login":
        session = Session(profile=args.profile)
        AwsAdLogin(
            session=session
        ).login(
            auth_config=AuthConfig.from_args(args)
        )
    elif args.cmd == "configure":
        AWSAdConfigure().configure(
            profile=args.profile,
            auth_config=AuthConfig.from_args(args)
        )
    elif args.cmd == "list":
        print(f"AWS Profiles:\n{AWSAdConfigure.list_profiles()}")


if __name__ == '__main__':
    main()
