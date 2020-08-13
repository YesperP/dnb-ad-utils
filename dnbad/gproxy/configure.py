import os
from os import path

from sshconf import read_ssh_config, empty_ssh_config_file

from dnbad.common.configure import *
from . import *
from .util import show_line_diff, show_file


def configure(advanced_mode=False):
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

    # TODO: Add advanced option which asks for this
    if advanced_mode:
        header("GProxy Connection (Advanced)")
        local_config.gproxy_hostname = get_input("GProxy Server Hostname", default=local_config.gproxy_hostname)
        local_config.gproxy_port = get_input("GProxy Server Port", default=local_config.gproxy_port)
    local_config.save()

    _configure_openssh()

    # Create control sockets directory
    _create_control_socket_dir(CONTROL_SOCKETS_PATH)

    header("GProxy Configuration Completed")
    print("You may run the configuration again at any time.")


def _configure_openssh():
    header("GProxy OpenSSH config")
    host_name = BIND_HOST

    if os.path.exists(SSH_CONFIG_PATH):
        ssh_config = read_ssh_config(SSH_CONFIG_PATH)

        # Check and create a compliant config:
        changed = False
        host_config = ssh_config.host(host_name)
        if len(host_config) == 0:
            changed = True
            ssh_config.add(host_name, **DEFAULT_BIT_BUCKET_HOST)
        else:
            for key, val in DEFAULT_BIT_BUCKET_HOST.items():
                if host_config.get(key.lower(), "").lower() != val.lower():
                    changed = True
                    ssh_config.set(host_name, **{key: val})

        # Old config:
        if changed:
            new_config_str = ssh_config.config()
            old_config_str = read_ssh_config(SSH_CONFIG_PATH).config()

            print(f"Some changes are needed for your ssh config file ({SSH_CONFIG_PATH}):")
            show_line_diff(
                old=old_config_str.split("\n"),
                new=new_config_str.split("\n")
            )
            if yes_no("Do you want us to make these changes?", default=True):
                ssh_config.save()
        else:
            print("Your SSH config file is already configured correctly. No changes needed.")
    else:
        ssh_config = empty_ssh_config_file()
        ssh_config.add(host_name, **DEFAULT_BIT_BUCKET_HOST)
        print(f"No ssh config found at {SSH_CONFIG_PATH}. We need to create this file:")
        show_file(ssh_config.config().split("\n"))
        if yes_no("Do you want us to create the file?", default=True):
            ssh_config.write(SSH_CONFIG_PATH)


def _create_control_socket_dir(control_path):
    control_dir = path.dirname(path.expanduser(control_path))
    if not path.exists(control_dir):
        print(f"Creating '{control_dir}' for control-socket...")
        os.mkdir(control_dir)
