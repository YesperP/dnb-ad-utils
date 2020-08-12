import os
from os.path import expanduser, exists, join

__all__ = ["VERSION", "get_data_file_path"]

VERSION = "0.1.0"
_DATA_ROOT = expanduser("~/.dnb-ad-utils")


def get_data_file_path(file_name, create_missing_folder=True) -> str:
    if create_missing_folder and not exists(_DATA_ROOT):
        os.mkdir(_DATA_ROOT)

    return join(_DATA_ROOT, file_name)
