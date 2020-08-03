import os
from os import path

from common import PROJECT_ROOT
from common.configure import *
from . import *
from .ssh_config import SSHConfig
from .util import show_line_diff


def configure():
    # Do general configuration:
    local_config = general_config()

    # Setting defaults:
    if local_config.gproxy_hostname is None:
        local_config.gproxy_hostname = DEFAULT_PROXY_HOSTNAME
    if local_config.gproxy_port is None:
        local_config.gproxy_port = DEFAULT_PROXY_PORT

    header("GProxy Prerequisites")
    with open(path.join(PROJECT_ROOT, "prerequisites.txt")) as f:
        print(f.read())

    header("GProxy Connection")
    local_config.gproxy_hostname = get_input("GProxy Hostname", default=local_config.gproxy_hostname)
    local_config.gproxy_port = get_input("GProxy Port", default=local_config.gproxy_port)
    local_config.save()

    _configure_openssh()

    # Create control sockets directory
    _create_control_socket_dir(CONTROL_SOCKETS_PATH)

    header("GProxy Configuration Completed")
    print("You may run the configuration again at any time.")


def _configure_openssh():
    header("GProxy OpenSSH config")
    new_ssh_config = SSHConfig.load_from_file()
    for key, val in DEFAULT_BIT_BUCKET_HOST.items():
        if new_ssh_config.get_line(BIND_ADDRESS, key) is None:
            new_ssh_config.set_value(BIND_ADDRESS, key, val)

    ssh_config = SSHConfig.load_from_file()
    if ssh_config != new_ssh_config:
        print(f"Some changes are needed for your ssh config file ({SSH_CONFIG_PATH}).")
        if yes_no("Do you want to look at the changes?", default=True):
            show_line_diff([line.to_line() for line in ssh_config.lines()],
                           [line.to_line() for line in new_ssh_config.lines()])
        if yes_no("Do you want to make these changes?"):
            new_ssh_config.write()
            ssh_config = new_ssh_config
    else:
        print("Your SSH config file is already configured correctly. No changes needed.")

    return ssh_config.get_config()


def _create_control_socket_dir(control_path):
    control_dir = path.dirname(path.expanduser(control_path))
    if not path.exists(control_dir):
        print(f"Creating '{control_dir}' for control-socket...")
        os.mkdir(control_dir)
