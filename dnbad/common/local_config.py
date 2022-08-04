import dataclasses
import json
from dataclasses import dataclass
from os import path
from typing import *

from dnbad.common.exceptions import AdUtilException
from . import get_data_file_path


class MissingLocalConfigException(AdUtilException):
    def __init__(self):
        super().__init__("Missing config. You must configure either awsad or gproxy.")


@dataclass
class LocalConfig:
    username: str

    @staticmethod
    def default_file_path():
        return get_data_file_path("config.json")

    def save(self, file_path: Optional[str] = None):
        file_path = file_path or self.default_file_path()
        with open(file_path, "w") as f:
            json.dump(dataclasses.asdict(self), f)

    @classmethod
    def load(cls, file_path: Optional[str] = None) -> "LocalConfig":
        file_path = file_path or cls.default_file_path()
        if not path.exists(file_path):
            raise MissingLocalConfigException()
        with open(file_path, "r") as f:
            d = json.load(f)
        return cls(d["username"])

    @classmethod
    def empty(cls):
        # noinspection PyTypeChecker
        return LocalConfig(None)
