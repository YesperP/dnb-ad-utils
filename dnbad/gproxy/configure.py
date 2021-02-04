import os
from os import path

from sshconf import read_ssh_config, empty_ssh_config_file

from dnbad.common.configure import *
from dnbad.common.utils import *
from .constants import *

HOST = BIND_HOST
DEFAULT_HOSTNAME = "localhost"
DEFAULT_PORT = "9000"
ENTRY_DEFAULT = {
    "Hostname": DEFAULT_HOSTNAME,
    "Port": DEFAULT_PORT,
    "StrictHostKeyChecking": "no"
}
ENTRY_REQUIRED = {
    "Hostname": DEFAULT_HOSTNAME,
    "Port": DEFAULT_PORT
}


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

        # Check and create a compliant config:
        changed = False
        host_config = ssh_config.host(HOST)
        if len(host_config) == 0:
            changed = True
            ssh_config.add(HOST, **ENTRY_DEFAULT)
        else:
            for key, default in ENTRY_REQUIRED.items():
                if key.lower() not in host_config:
                    changed = True
                    ssh_config.set(HOST, **{key: default})

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
        ssh_config.add(HOST, **ENTRY_DEFAULT)
        print(f"No ssh config found at {SSH_CONFIG_PATH}. We need to create this file:")
        show_file(ssh_config.config().split("\n"))
        if yes_no("Do you want us to create the file?", default=True):
            _create_dir(SSH_CONFIG_PATH)
            ssh_config.write(SSH_CONFIG_PATH)


def _create_dir(file_path: str):
    directory = path.dirname(path.expanduser(file_path))
    exists = path.exists(directory)
    if not exists:
        os.mkdir(directory)
    return exists
