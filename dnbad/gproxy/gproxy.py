import re
import subprocess

import pexpect
from sshconf import read_ssh_config

from dnbad.common.azure_auth_page import AuthConfig
from dnbad.common.local_config import LocalConfig
from dnbad.common.password_manager import PasswordManager
from . import *
from .gproxy_ad_login import GProxyAdLogin
from .util import check_host


class GProxyError(Exception):
    pass


class GProxy:

    def __init__(self, config: LocalConfig):
        self.config: LocalConfig = config
        ssh_config = read_ssh_config(SSH_CONFIG_PATH)
        self.forward_hostname = ssh_config.host(BIND_ADDRESS)["hostname"]
        self.forward_port = ssh_config.host(BIND_ADDRESS)["port"]

    def _host(self):
        return f"ssh://{SSH_USER}@{self.config.gproxy_hostname}:{self.config.gproxy_port}"

    def _connect_args(self):
        return [
            "-fNT",
            "-L", f"{self.forward_hostname}:{self.forward_port}:{BIND_ADDRESS}:{FORWARD_PORT}",
            "-S", CONTROL_SOCKETS_PATH,
            "-o", "ControlMaster auto",
            "-o", "ControlPersist yes",
            self._host()
        ]

    def connect(self, password_manager: PasswordManager, azure_ad_config: AuthConfig):

        if self.is_connected():
            return

        p = pexpect.spawn("ssh", self._connect_args(), encoding="utf-8")
        i = p.expect([pexpect.EOF, "authenticate."])

        if i == 0:
            raise GProxyError(f"Error when initializing SSH: {p.before}")

        p.send("\r")

        code = self._extract_code(p.before)
        url = self._extract_url(p.before)
        print(f"Code: {code}, Url: {url}")

        if url != GProxyAdLogin.URL:
            raise GProxyError(f"Url does not match expected login-url. !={GProxyAdLogin.URL}")

        GProxyAdLogin(
            code=code,
            password_manager=password_manager,
            config=azure_ad_config
        ).login_sync()

        p.expect(pexpect.EOF, timeout=30)

    @staticmethod
    def _extract_code(s):
        return re.search(r"[A-Z0-9]{3,}", s).group(0)

    @staticmethod
    def _extract_url(s):
        return re.search(r"http[^\s]+", s).group(0)

    def disconnect(self):
        self._ctl_cmd("exit")

    def is_connected(self):
        return self.is_connected_ctl() and self.is_connected_connection()

    def is_connected_ctl(self):
        return self._ctl_cmd("check").returncode == 0

    @staticmethod
    def is_connected_connection():
        return check_host("localhost", 9000)

    def _ctl_cmd(self, cmd):
        return subprocess.run(["ssh", "-S", CONTROL_SOCKETS_PATH, "-O", cmd, self._host()], capture_output=True)
