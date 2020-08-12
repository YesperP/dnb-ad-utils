import logging
import random
import string
import sys
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from typing import *

from . import VERSION, get_data_file_path


@dataclass
class CliBase:
    LOG = logging.getLogger("dnbad")

    def __init__(self, prog: str, description: str):
        self.prog = prog
        self.parser = ArgumentParser(prog, description=description)
        self.parser.add_argument("-v", "--version", action="version", version=VERSION)
        self.parser.add_argument("-l", "--log-console", help="log to console", action="store_true")
        self.subparsers = self.parser.add_subparsers(dest="cmd")

    def add_cmd(self, name: str, help: str):
        return self.subparsers.add_parser(name, help=help)

    def handle(self):
        success = self._handle()
        return 0 if success is None or success else 1

    def _setup_logging(self, args):
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(fmt='%(levelname)-8s %(message)s'))
        stream_handler.setLevel(logging.INFO)

        file_handler = RotatingFileHandler(
            filename=get_data_file_path(f"{self.prog}.log"),
            maxBytes=1 * 1024 * 1024,
            backupCount=0
        )
        file_handler.setFormatter(logging.Formatter(fmt="%(asctime)s %(name)-35s %(levelname)-8s %(message)s"))
        file_handler.setLevel(logging.DEBUG)

        # Add both handlers to our logger:
        self.LOG.setLevel(logging.DEBUG)
        self.LOG.addHandler(stream_handler)
        self.LOG.addHandler(file_handler)
        self.LOG.propagate = False

        # Add only the file handler to the root, and with INFO to debug.
        logging.root.setLevel(logging.INFO)
        logging.root.addHandler(file_handler)

        # Disable pyppeteer logger
        pyp = logging.getLogger("pyppeteer")
        pyp.handlers = []
        pyp.propagate = True

    def _handle(self) -> Optional[bool]:
        args = self.parser.parse_args()
        log_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))

        try:
            self._setup_logging(args)
            self.LOG.debug(f"======START(cmd={args.cmd},id={log_id})======")
            if args.cmd is None:
                self.parser.print_help()
                return True
            else:
                return self._handle_cmd(args.cmd, args)
        finally:
            self.LOG.debug(f"======END(cmd={args.cmd},id={log_id})======")

    def _handle_cmd(self, cmd: str, args: Namespace) -> Optional[bool]:
        pass
