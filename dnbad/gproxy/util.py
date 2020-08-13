import itertools
import socket
from typing import List

_MIN_HEADER_OLD = "--OLD--"
_MIN_HEADER_NEW = "--NEW--"


def show_line_diff(old: List[str], new: List[str]):
    width_max_old = max((len(line) for line in old), default=0)
    width_max_new = max((len(line) for line in new), default=0)

    width_max_old = max(len(_MIN_HEADER_OLD), width_max_old)
    width_max_new = max(len(_MIN_HEADER_NEW), width_max_new)

    old.append("".center(width_max_old, "-"))
    new.append("".center(width_max_new, "-"))

    f_str = "{}|{}|{}|"

    print(f_str.format("--", _MIN_HEADER_OLD.center(width_max_old, "-"), _MIN_HEADER_NEW.center(width_max_new, "-")))
    for i, (left_line, right_line) in enumerate(itertools.zip_longest(old, new, fillvalue=None)):
        if i + 1 == max(len(old), len(new)):
            marker = "--"
        elif left_line == right_line:
            marker = "  "
        else:
            marker = "X "
        print(f_str.format(marker, (left_line or "").ljust(width_max_old), (right_line or "").ljust(width_max_new)))


def show_file(lines: List[str]):
    line_max = max((len(line) for line in lines), default=0)
    line_max = max(line_max, len(_MIN_HEADER_NEW))
    f_str = "|{}|"
    print(f_str.format(_MIN_HEADER_NEW.center(line_max, "-")))
    for line in lines:
        print(f_str.format(line.ljust(line_max)))
    print(f_str.format("".center(line_max, "-")))


# noinspection PyBroadException
def check_host(hostname: str, port: int):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(1)
        s.connect((hostname, port))
        s.shutdown(socket.SHUT_RDWR)
        return True
    except Exception:
        return False
    finally:
        s.close()
