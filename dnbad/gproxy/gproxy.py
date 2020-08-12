import logging
import re
import subprocess

import pexpect
from sshconf import read_ssh_config

from dnbad.common.azure_auth import AuthConfig
from dnbad.common.local_config import LocalConfig
from dnbad.common.password_manager import PasswordManager
from . import *
from .gproxy_ad_login import GProxyAdLogin

LOG = logging.getLogger(__name__)


class GProxyError(Exception):
    pass


class GProxy:
    TIMEOUT_CHECK_CONNECTION = 2

    def __init__(self, config: LocalConfig):
        self.config: LocalConfig = config

        ssh_config = read_ssh_config(SSH_CONFIG_PATH)
        self.bind_hostname = ssh_config.host(BIND_HOST)["hostname"]
        self.bind_port = ssh_config.host(BIND_HOST)["port"]

    def _host(self):
        return f"ssh://{SSH_USER}@{self.config.gproxy_hostname}:{self.config.gproxy_port}"

    def _connect_args(self):
        return [
            "-fNT",
            "-L", f"{self.bind_hostname}:{self.bind_port}:{FORWARD_HOST}:{FORWARD_PORT}",
            "-S", CONTROL_SOCKETS_PATH,
            "-o", "ControlMaster auto",
            "-o", "ControlPersist yes",
            self._host()
        ]

    def connect(self, password_manager: PasswordManager, azure_ad_config: AuthConfig):
        args = self._connect_args()
        LOG.debug(f"SSH connection args: {args}")
        p = pexpect.spawn("ssh", args, encoding="utf-8")
        i = p.expect([pexpect.EOF, "authenticate."])

        if i == 0:
            raise GProxyError(f"Error when initializing SSH: {p.before}")

        p.send("\r")

        code = self._extract_code(p.before)
        url = self._extract_url(p.before)
        LOG.info(f"GProxy OTC Code: {code}, Url: {url}")

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

    @classmethod
    def is_connected(cls):
        try:
            completed_process = subprocess.run(
                ["ssh", f"git@{BIND_HOST}", "whoami"],
                capture_output=True,
                timeout=cls.TIMEOUT_CHECK_CONNECTION
            )
        except subprocess.TimeoutExpired:
            LOG.debug("Connection timeout.")
            return False

        output = completed_process.stderr.decode("utf-8")
        LOG.debug(f"Connection status output: {repr(output)}")
        if completed_process.returncode == 0:
            return True
        elif "Permission denied" in output:
            raise GProxyError(f"Connection established, but BitBucket permission denied: {repr(output)}")
        return False

    def _ctl_cmd(self, cmd):
        return subprocess.run(["ssh", "-S", CONTROL_SOCKETS_PATH, "-O", cmd, self._host()], capture_output=True)
