from os.path import expanduser, join

SSH_FOLDER = expanduser("~/.ssh")
SSH_CONFIG_PATH = join(SSH_FOLDER, "config")
SSH_KEY_FOLDER = join(SSH_FOLDER, "key")

SSH_USER = "git"
CONTROL_SOCKETS_PATH = "~/.ssh/sockets/%r@%h:%p"
FORWARD_PORT = 22
BIND_ADDRESS = "git.tech-01.net"

PERSIST_POLL_TIME = 10
PERSIST_RETRY_TIME = 30

DEFAULT_PROXY_HOSTNAME = "gitproxy.ccoe.cloud"
DEFAULT_PROXY_PORT = "443"

DEFAULT_BIT_BUCKET_HOST = {
    "Hostname": "localhost",
    "StrictHostKeyChecking": "no",
    "Port": "9000",
}
