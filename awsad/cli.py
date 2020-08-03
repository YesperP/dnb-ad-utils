import argparse
import sys
import traceback

from botocore.session import Session

from awsad.awsad import AwsAdLogin, AzureAdConfig
from awsad.configure import AWSAdConfigure
from common import VERSION
from common.exceptions import DnbException


# noinspection PyBroadException
def main() -> [int, None]:
    try:
        success = _main()
    except Exception:
        raise
    except DnbException as e:
        print(f"\n{str(e)}", file=sys.stderr)
        return 1
    except Exception:
        traceback.print_exc()
        return 1
    return 0 if success else 1


def _main() -> [int, None]:
    parser = argparse.ArgumentParser(
        prog="awsad",
        description="AWS Login with Azure AD"
    )
    parser.add_argument("-v", "--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="cmd")

    p_login = subparsers.add_parser("login")
    p_login.add_argument("-n", "--no-headless", help="Login to Azure AD in non-headless mode", action="store_true")
    p_login.add_argument("-d", "--debug", help="Debug mode", action="store_true")
    p_login.add_argument("-c", "--no-cookies", help="Login without using cookies", action="store_true")
    p_login.add_argument("-p", "--profile", help="AWS Profile")

    p_configure = subparsers.add_parser("configure")
    p_configure.add_argument("-p", "--profile", help="AWS Profile")

    subparsers.add_parser("list")

    args = parser.parse_args()

    if args.cmd is None:
        parser.print_help()
    elif args.cmd == "login":
        session = Session(profile=args.profile)
        ad_config = AzureAdConfig(
            headless=not args.no_headless,
            use_cookies=not args.no_cookies,
            dump_io=args.debug
        )
        AwsAdLogin(session).login(ad_config)
    elif args.cmd == "configure":
        AWSAdConfigure().configure(args.profile)
    elif args.cmd == "list":
        print(f"AWS Profiles:\n{AWSAdConfigure.list_profiles()}")
    return True
