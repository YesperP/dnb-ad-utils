import os
from os import path

from sshconf import read_ssh_config, empty_ssh_config_file

from dnbad.common.configure import *
from . import *
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
    with open(path.join(path.dirname(__file__), "prerequisites.txt")) as f:
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
    host_name = BIND_ADDRESS

    if os.path.exists(SSH_CONFIG_PATH):

        # Create a compliant config:
        new_config = read_ssh_config(SSH_CONFIG_PATH)
        for key, val in DEFAULT_BIT_BUCKET_HOST.items():
            new_config.set(host_name, **{key: val})
        new_config_str = new_config.config()

        # Old config:
        old_config_str = read_ssh_config(SSH_CONFIG_PATH).config()

        if new_config_str != old_config_str:
            print(f"Some changes are needed for your ssh config file ({SSH_CONFIG_PATH}).")
            if yes_no("Do you want to look at the changes?", default=True):
                show_line_diff(
                    old=old_config_str.split("\n"),
                    new=new_config_str.split("\n")
                )
            if yes_no("Do you want us to make these changes?", default=True):
                new_config.save(SSH_CONFIG_PATH)
        else:
            print("Your SSH config file is already configured correctly. No changes needed.")
    else:
        ssh_config = empty_ssh_config_file()
        for key, val in DEFAULT_BIT_BUCKET_HOST.items():
            ssh_config.set(host_name, **{key: val})
        print(f"No ssh config found at {SSH_CONFIG_PATH}")
        if yes_no("Do you want us to create the file?", default=True):
            ssh_config.write(SSH_CONFIG_PATH)


def _create_control_socket_dir(control_path):
    control_dir = path.dirname(path.expanduser(control_path))
    if not path.exists(control_dir):
        print(f"Creating '{control_dir}' for control-socket...")
        os.mkdir(control_dir)
