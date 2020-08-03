import argparse
import time

from common import VERSION
from . import PERSIST_POLL_TIME, PERSIST_RETRY_TIME, BIND_ADDRESS
from common.password_manager import PasswordManager
from common.local_config import LocalConfig
from .configure import configure
from .gproxy import GProxy, GProxyError, AuthConfig


class NoConfigError(Exception):
    msg = "GProxy is not configured. Please run 'gproxy configure' first."


def main() -> [int, None]:
    success = _main()
    return 0 if success else 1


def _main() -> [int, None]:
    parser = argparse.ArgumentParser(
        prog="gproxy",
        description="GitProxy SSH login with Azure AD"
    )
    parser.add_argument("-v", "--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="cmd")

    p_login = subparsers.add_parser("connect")
    p_login.add_argument("-n", "--no-headless", help="Login to Azure AD in non-headless mode", action="store_true")
    p_login.add_argument("-d", "--debug", help="Debug mode", action="store_true")
    p_login.add_argument("-c", "--clean", help="Login without using cookies", action="store_true")

    subparsers.add_parser("off")
    subparsers.add_parser("configure")
    subparsers.add_parser("status")
    subparsers.add_parser("on")

    args = parser.parse_args()

    if args.cmd is None:
        parser.print_help()
    elif args.cmd == "connect":
        return connect(args)
    elif args.cmd == "status":
        return status()
    elif args.cmd == "off":
        return disconnect()
    elif args.cmd == "configure":
        configure()
    elif args.cmd == "on":
        on()


def get_config() -> LocalConfig:
    config = LocalConfig.load()
    if config is None or config.gproxy_hostname is None or config.gproxy_port is None:
        raise NoConfigError()
    return config


def connect(args):
    config = get_config()
    g_proxy = GProxy(config)
    connected = g_proxy.is_connected()
    if connected:
        print("Already connected.")
    else:
        azure_ad_config = AuthConfig(
            headless=not args.no_headless,
            use_cookies=not args.clean,
            dump_io=args.debug
        )

        g_proxy.connect(PasswordManager(config.username), azure_ad_config)
        connected = g_proxy.is_connected()
        if connected:
            print(f"You can now connect to {BIND_ADDRESS} through the proxy.")
        else:
            print("Something went wrong and the connection could not be established.")


def status() -> bool:
    g_proxy = GProxy(get_config())
    conn_ctl = g_proxy.is_connected_ctl()
    conn_conn = g_proxy.is_connected_connection()
    connected = conn_ctl and conn_conn
    print(f"Connected: {connected} (CTL-Socket: {conn_ctl}, Connection: {conn_conn})")
    return connected


def disconnect() -> bool:
    g_proxy = GProxy(get_config())
    g_proxy.disconnect()
    print(f"Connected: {g_proxy.is_connected()}")
    return not g_proxy.is_connected()


def on():
    config = get_config()
    g_proxy = GProxy(config)
    ad_config = AuthConfig(
        headless=False,
        use_cookies=True,
        dump_io=False
    )
    password_manager = PasswordManager(config.username)
    password_manager.get_password()

    while True:
        conn_ctl = g_proxy.is_connected_ctl()
        conn_conn = g_proxy.is_connected_connection()
        connected = conn_ctl and conn_conn
        if not connected:
            print(f"Connected: {connected} (CTL-Socket: {conn_ctl}, Connection: {conn_conn})")
            try:
                g_proxy.connect(password_manager, ad_config)
            except GProxyError as e:
                print(f"An error occurred when connecting:\n {str(e)}")

        time.sleep(PERSIST_POLL_TIME if connected else PERSIST_RETRY_TIME)
