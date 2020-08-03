import dataclasses
import json
from dataclasses import dataclass
from os import path
from typing import *

from dnbad.common.exceptions import DnbException
from . import DATA_ROOT, create_data_root


class MissingLocalConfigException(DnbException):
    def __init__(self):
        super().__init__("Missing config. You must configure either awsad or gproxy.")


@dataclass
class LocalConfig:
    username: str
    gproxy_hostname: Optional[str]
    gproxy_port: Optional[str]

    FILE_PATH = path.join(DATA_ROOT, "gproxy_config.json")

    def save(self):
        create_data_root()
        with open(self.FILE_PATH, "w") as f:
            json.dump(dataclasses.asdict(self), f)

    @classmethod
    def load(cls) -> "LocalConfig":
        if not path.exists(cls.FILE_PATH):
            raise MissingLocalConfigException()
        with open(cls.FILE_PATH, "r") as f:
            d = json.load(f)
        return cls(d["username"], d.get("gproxy_hostname"), d.get("gproxy_port"))
