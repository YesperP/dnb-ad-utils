import os
from os.path import expanduser, exists

__all__ = ["VERSION", "DATA_ROOT", "create_data_root"]

VERSION = "0.1.0"
DATA_ROOT = expanduser("~/.dnb-ad-utils")


def create_data_root():
    if not exists(DATA_ROOT):
        os.mkdir(DATA_ROOT)
