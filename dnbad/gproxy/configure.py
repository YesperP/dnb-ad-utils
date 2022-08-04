import os
from os import path

from sshconf import read_ssh_config, empty_ssh_config_file

from dnbad.common.configure import *
from dnbad.common.utils import *
from .constants import *


def configure():
    # Do general configuration:
    local_config = general_config()
    local_config.save()

    header("GProxy Prerequisites")
    with open(path.join(path.dirname(__file__), "prerequisites.txt")) as f:
        print(f.read())

    _configure_openssh()

    # Create control sockets directory
    _create_dir(CONTROL_SOCKETS_PATH)

    header("GProxy Configuration Completed")
    print("You may run the configuration again at any time.")


def _configure_openssh():
    header("GProxy OpenSSH config")

    if os.path.exists(SSH_CONFIG_PATH):
        ssh_config = read_ssh_config(SSH_CONFIG_PATH)
        changed = _make_compliant(ssh_config)

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
        _configure_empty()


def _configure_empty():
    ssh_config = empty_ssh_config_file()
    _make_compliant(ssh_config)
    print(f"No ssh config found at {SSH_CONFIG_PATH}. We need to create this file:")
    show_file(ssh_config.config().split("\n"))
    if yes_no("Do you want us to create the file?", default=True):
        _create_dir(SSH_CONFIG_PATH)
        ssh_config.write(SSH_CONFIG_PATH)


# Create a compliant config:
def _make_compliant(ssh_config):
    changed = False
    for host in SSH_HOSTS:
        host_config = ssh_config.host(host.hostname)
        print(host_config)
        if "hostname" not in host_config:
            ssh_config.set(host.hostname, Hostname="localhost")
            changed = True
        if "port" not in host_config:
            ssh_config.set(host.hostname, Port=str(host.default_local_port))
            changed = True

        # If there was no entry, we set this optional option:
        if len(host_config) == 0:
            ssh_config.set(host.hostname, StrictHostKeyChecking="no")

    return changed


def _create_dir(file_path: str):
    directory = path.dirname(path.expanduser(file_path))
    exists = path.exists(directory)
    if not exists:
        os.mkdir(directory)
    return exists
