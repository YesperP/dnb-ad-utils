import os
from os.path import dirname, expanduser, exists

__all__ = ["VERSION", "PROJECT_ROOT", "DATA_ROOT", "create_data_root"]

VERSION = "0.1.0"
PROJECT_ROOT = dirname(dirname(dirname(__name__)))
DATA_ROOT = expanduser("~/.dnb-ad-utils")


def create_data_root():
    if not exists(DATA_ROOT):
        os.mkdir(DATA_ROOT)
