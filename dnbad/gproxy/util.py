import socket
from typing import List


def show_line_diff(old: List[str], new: List[str]):
    line_max_old = max(len(l) for l in old)
    line_max_new = max(len(l) for l in new)
    f_str = f"{{}} |{{:<{line_max_old}}}|{{:<{line_max_new}}}"

    old.append("".join(["-"] * line_max_old))
    new.append("".join(["-"] * line_max_new))

    longest = old if len(old) > len(new) else new
    shortest = new if len(old) > len(new) else old
    shortest.extend([" "] * (len(longest) - len(shortest)))

    sep = "".join(["-"] * 4)
    print(f_str.format(" ", f"{sep} OLD {sep}", f"{sep} NEW {sep}"))
    for left_line, right_line in zip(old, new):
        print(f_str.format("X" if left_line != right_line else " ", left_line, right_line))


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
