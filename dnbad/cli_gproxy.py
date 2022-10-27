import time

import pexpect.exceptions

from dnbad.common.azure_auth import AuthConfig
from dnbad.common.cli_base import *
from dnbad.common.local_config import LocalConfig
from dnbad.common.password_manager import PasswordManager
from dnbad.gproxy.constants import *
from dnbad.gproxy.configure import configure
from dnbad.gproxy.gproxy import GProxy, GProxyError

LOG = logging.getLogger(__name__)


def main() -> int:
    return GProxyCli().handle()


class GProxyCli(CliBase):
    def __init__(self):
        super().__init__(
            "gproxy",
            "GitProxy SSH login with Azure AD"
        )
        p_login = self.add_cmd("on", help="Establish connection")
        AuthConfig.add_arguments_to_parser(p_login)

        self.add_cmd("off", help="Tear down connection")
        self.add_cmd("configure", help="Configure")
        self.add_cmd("status", help="Check connection status")
        self.add_cmd("persist", help="Polls status and reconnects if connection drops.")

    def _handle_cmd(self, cmd: str, args: Namespace) -> Optional[bool]:
        if cmd == "on":
            return connect(args)
        elif cmd == "status":
            return status()
        elif cmd == "off":
            return disconnect()
        elif cmd == "configure":
            configure()
        elif cmd == "persist":
            persist()


class NoConfigError(Exception):
    msg = "GProxy is not configured. Please run 'gproxy configure' first."


def connect(args):
    config = LocalConfig.load()
    g_proxy = GProxy(config)
    connected = g_proxy.is_connected()
    if connected:
        print("Already connected.")
    else:
        g_proxy.connect(PasswordManager(config.username), AuthConfig.from_args(args))
        connected = g_proxy.is_connected()
        if connected:
            host_list = "\n ".join(
                f'{h.local_hostname}:{h.local_port} => {h.hostname}:{h.port}'
                for h in g_proxy.get_forward_hosts()
            )
            print(f"Tunnels setup for\n {host_list}\nthrough the proxy.")
        else:
            print("Something went wrong and the connection could not be established.")


def status() -> bool:
    connected = GProxy.is_connected()
    print(f"Connected: {connected}")
    return connected


def disconnect() -> bool:
    g_proxy = GProxy(LocalConfig.load())
    g_proxy.disconnect()
    connected = g_proxy.is_connected()
    print(f"Could not disconnect." if connected else "Successfully disconnected.")
    return not connected


def persist():
    config = LocalConfig.load()
    g_proxy = GProxy(config)
    ad_config = AuthConfig(
        headless=True,
        use_cookies=True,
        dump_io=False,
        keep_open=False
    )
    password_manager = PasswordManager(config.username)
    password_manager.fetch_password()

    connected = g_proxy.is_connected()
    if connected:
        LOG.info(f"Connected: {g_proxy.is_connected()}")

    while True:
        connected = g_proxy.is_connected()
        if not connected:
            LOG.info(f"Reconnecting...")
            try:
                g_proxy.connect(password_manager, ad_config)
                LOG.info(f"Connected: {g_proxy.is_connected()}")
            except (GProxyError, pexpect.exceptions.TIMEOUT) as e:
                LOG.warning(f"An error occurred when connecting:\n {str(e)}")

        time.sleep(PERSIST_POLL_TIME if connected else PERSIST_RETRY_TIME)


if __name__ == '__main__':
    main()
