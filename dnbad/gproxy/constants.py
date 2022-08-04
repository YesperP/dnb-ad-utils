import dataclasses
from os.path import expanduser, join
from typing import List

SSH_FOLDER = expanduser("~/.ssh")
SSH_CONFIG_PATH = join(SSH_FOLDER, "config")
SSH_KEY_FOLDER = join(SSH_FOLDER, "key")

SSH_USER = "git"
CONTROL_SOCKETS_PATH = "~/.ssh/sockets/%r@%h:%p"
GPROXY_HOSTNAME = "gitproxy.ccoe.cloud"
GPROXY_PORT = "443"
GPROXY_FINGERPRINT = "SHA256:PSGDmbx+ZSyXXZh2PM83FjAaVs1riuG3hyYhwsbh55A"

TIMEOUT_CHECK_CONNECTION = 2
PERSIST_POLL_TIME = 10
PERSIST_RETRY_TIME = 30


@dataclasses.dataclass
class Host:
    hostname: str
    port: int


@dataclasses.dataclass
class SshHost(Host):
    default_local_port: int


SSH_HOSTS = [
    SshHost("git.tech-01.net", 22, 9000),
    SshHost("gitlab.tech.dnb.no", 2222, 2222)
]
STATUS_TEST_HOST = SSH_HOSTS[0].hostname

HOSTS: List[Host] = [
    Host("nexus.tech.dnb.no", 443),
    Host("nexus.tech.dnb.no", 18443)
] + SSH_HOSTS
