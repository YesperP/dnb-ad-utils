import os
from dataclasses import dataclass
from typing import List, Dict

from . import SSH_CONFIG_PATH

HOST_KEY = "Host"


@dataclass(frozen=True)
class SSHLine:
    def to_line(self):
        raise NotImplementedError()


class EmptyLine(SSHLine):
    def to_line(self):
        return ""


@dataclass(frozen=True)
class CommentLine(SSHLine):
    line: str

    def to_line(self):
        return self.line


@dataclass(frozen=True)
class KeyValueLine(SSHLine):
    indent: int
    key: str
    val: str

    def is_host(self):
        return self.key.lower() == HOST_KEY.lower()

    def to_line(self):
        return "".join([" "] * self.indent) + self.key + " " + self.val


@dataclass
class Section:
    lines: List[SSHLine]

    def get_host(self) -> [None, str]:
        first_line = self.lines[0]
        return first_line.val if isinstance(first_line, KeyValueLine) else None

    def set_line(self, line: KeyValueLine):
        line_i = -1
        for i, s_line in enumerate(self.lines):
            if isinstance(s_line, KeyValueLine) and s_line.key.lower() == line.key.lower():
                line_i = i
                break
        if line_i >= 0:
            self.lines[line_i] = line
        else:
            self.lines.append(line)

    @classmethod
    def from_lines(cls, lines: List[SSHLine]) -> List["Section"]:
        # Separate lines into sections, where a section either is:
        # - only containing comments or empty lines.
        # - starting with 'Host' argument, containing no other 'Host' argument and ending with an argument.
        sections = []
        host_builder = []
        empty_builder = []

        def flush(builder):
            if len(builder) > 0:
                sections.append(cls(builder))
            return []

        for line in lines:
            if isinstance(line, KeyValueLine):
                if line.is_host():
                    host_builder = flush(host_builder)
                    empty_builder = flush(empty_builder)
                else:
                    host_builder.extend(empty_builder)
                    empty_builder = []
                host_builder.append(line)
            else:
                empty_builder.append(line)
        flush(host_builder)
        flush(empty_builder)
        return sections


class SSHConfig:

    def __init__(self, ssh_lines: List[SSHLine]):
        # self.ssh_lines: List[SSHLine] = ssh_lines
        self._sections: List[Section] = Section.from_lines(ssh_lines)

    def get_section(self, host: str) -> Section:
        return {section.get_host(): section for section in self._sections if section.get_host()}.get(host)

    def get_line(self, host: str, key: str) -> [None, KeyValueLine]:
        for line in self.get_section(host).lines:
            if isinstance(line, KeyValueLine) and line.key.lower() == key.lower():
                return line
        return None

    def get_styling(self, lines: List[SSHLine]):
        argument_lines = self._argument_lines(lines)
        n_low = len([line for line in argument_lines if line.key.islower()])
        lower_case = (n_low > len(argument_lines) - n_low)
        host_indent = self._most_frequent([line.indent for line in argument_lines if line.is_host()], default=0)
        non_host_indent = self._most_frequent([line.indent for line in argument_lines if not line.is_host()], default=2)
        return lower_case, host_indent, non_host_indent

    def set_value(self, host: str, key: str, value: str):
        lower_case, host_indent, non_host_indent = self.get_styling(self.lines())
        indent = host_indent if key == HOST_KEY else non_host_indent
        key = key.lower() if lower_case else key
        self.set_line(host, KeyValueLine(indent, key, value))

    def set_line(self, host: str, line: KeyValueLine):
        section = self.get_section(host)
        if section is None:
            section = Section([])
            self._sections.append(section)
        section.set_line(line)

    @classmethod
    def has_file(cls) -> bool:
        return os.path.exists(SSH_CONFIG_PATH)

    @classmethod
    def load_from_file(cls) -> "SSHConfig":
        if cls.has_file():
            with open(SSH_CONFIG_PATH, mode="r") as f:
                return cls([cls._parse_line(line) for line in f.readlines()])
        else:
            return cls([])

    @staticmethod
    def _parse_line(raw_line: str) -> SSHLine:
        line = raw_line.strip("\n")

        stripped_line = line.lstrip(" ").rstrip(" ")
        if len(stripped_line) == 0:
            return EmptyLine()
        elif stripped_line.startswith("#"):
            return CommentLine(line)
        else:
            key, arg = stripped_line.split(" ", maxsplit=1)
            return KeyValueLine(len(line) - len(line.lstrip(" ")), key, arg)

    def lines(self):
        return [l for s in self._sections for l in s.lines]

    def __eq__(self, other):
        if not isinstance(other, SSHConfig):
            return False
        lines, other_lines = self.lines(), other.lines()
        if len(lines) != len(other_lines):
            return False
        return all(left.to_line() == right.to_line() for left, right in zip(lines, other_lines))

    def get_config(self) -> Dict[str, Dict[str, str]]:
        host_configs = {}
        for section in self._sections:
            arg_lines = self._argument_lines(section.lines)
            if len(arg_lines) == 0:
                continue
            host_configs[arg_lines[0].val] = {line.key.lower(): line.val for line in arg_lines[1:]}
        return host_configs

    @staticmethod
    def _argument_lines(lines: List[SSHLine]) -> List[KeyValueLine]:
        return [line for line in lines if isinstance(line, KeyValueLine)]

    @staticmethod
    def _most_frequent(l, default=None):
        return max(set(l), key=l.count, default=default)

    def write(self):
        with open(SSH_CONFIG_PATH, mode="w") as f:
            for line in self.lines():
                f.write(line.to_line() + "\n")

    def __str__(self):
        return "\n".join(line.to_line() for line in self.lines())
