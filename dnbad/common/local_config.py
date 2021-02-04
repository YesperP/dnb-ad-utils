import dataclasses
import json
from dataclasses import dataclass
from os import path

from dnbad.common.exceptions import AdUtilException
from . import get_data_file_path


class MissingLocalConfigException(AdUtilException):
    def __init__(self):
        super().__init__("Missing config. You must configure either awsad or gproxy.")


@dataclass
class LocalConfig:
    username: str

    @staticmethod
    def _file_path():
        return get_data_file_path("config.json")

    def save(self):
        with open(self._file_path(), "w") as f:
            json.dump(dataclasses.asdict(self), f)

    @classmethod
    def load(cls) -> "LocalConfig":
        if not path.exists(cls._file_path()):
            raise MissingLocalConfigException()
        with open(cls._file_path(), "r") as f:
            d = json.load(f)
        return cls(d["username"])
