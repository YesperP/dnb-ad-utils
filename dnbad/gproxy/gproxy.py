import logging
import re
import subprocess

import pexpect
from sshconf import read_ssh_config

from dnbad.common.azure_auth import AuthConfig
from dnbad.common.local_config import LocalConfig
from dnbad.common.password_manager import PasswordManager
from .constants import *
from .gproxy_ad_login import GProxyAdLogin

__all__ = ["GProxy", "GProxyError", "AuthConfig", "PasswordManager"]

LOG = logging.getLogger(__name__)


class GProxyError(Exception):
    pass


class GProxy:
    def __init__(self, config: LocalConfig):
        self.config: LocalConfig = config
        # TODO: Handle missing config/not configured.
        self.ssh_config = read_ssh_config(SSH_CONFIG_PATH)

    @staticmethod
    def _host():
        return f"ssh://{SSH_USER}@{GPROXY_HOSTNAME}:{GPROXY_PORT}"

    def _connect_args(self):
        options = [
            "-fNT",
            "-S", CONTROL_SOCKETS_PATH,
            "-o", "ControlMaster auto",
            "-o", "ControlPersist yes",
        ]
        for host in HOSTS:
            config = self.ssh_config.host(host.hostname)
            options.extend(["-L", f"{config['hostname']}:{config['port']}:{host.hostname}:{host.port}"])

        return options + [self._host()]

    def connect(self, password_manager: PasswordManager, azure_ad_config: AuthConfig):
        args = self._connect_args()
        LOG.debug(f"SSH connection args: {args}")
        p: pexpect.spawn = pexpect.spawn("ssh", args, encoding="utf-8")
        self._wait_connect(p, password_manager, azure_ad_config)

    def _wait_connect(self, p: pexpect.spawn, password_manager: PasswordManager, azure_ad_config: AuthConfig):
        i = p.expect([
            pexpect.EOF,
            re.compile(r"continue connecting \(yes/no(/\[fingerprint])?\)\? "),
            re.compile(r"authenticate\.")
        ])

        if i == 0:
            if self.is_connected():
                return
            else:
                raise GProxyError(f"Error when initializing SSH: {p.before}")
        elif i == 1:
            host_key_fingerprint = self._extract_host_key_fingerprint(p.before)
            if host_key_fingerprint != GPROXY_FINGERPRINT:
                raise GProxyError(
                    f"!!!SEVERE!!! Host fingerprint is not matching expected!!! Report to CCOE!:"
                    f"Actual:{host_key_fingerprint} != Expected:{GPROXY_FINGERPRINT}"
                )
            LOG.info("Confirming host! Fingerprint is matching expected.")
            p.send("yes\r")
            self._wait_connect(p, password_manager, azure_ad_config)
            return

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
        return re.search(r"[A-Z0-9]{9,}", s).group(0)

    @staticmethod
    def _extract_url(s):
        return re.search(r"http[^\s]+", s).group(0)

    @staticmethod
    def _extract_host_key_fingerprint(s):
        return re.search(r"SHA256:[a-zA-Z+0-9]*", s).group(0)

    def disconnect(self):
        self._ctl_cmd("exit")

    @classmethod
    def is_connected(cls):
        try:
            completed_process = subprocess.run(
                ["ssh", f"git@{STATUS_TEST_HOST}", "whoami"],
                capture_output=True,
                timeout=TIMEOUT_CHECK_CONNECTION
            )
        except subprocess.TimeoutExpired:
            LOG.debug("Connection timeout.")
            return False

        output = repr(completed_process.stderr.decode("utf-8"))
        LOG.debug(f"Connection status output: {output}")
        if completed_process.returncode == 0:
            return True
        elif "Permission denied" in output:
            raise GProxyError(f"Connection established, but BitBucket permission denied. "
                              f"Check your private/public keys. ({output})")
        return False

    def _ctl_cmd(self, cmd):
        return subprocess.run(["ssh", "-S", CONTROL_SOCKETS_PATH, "-O", cmd, self._host()], capture_output=True)
