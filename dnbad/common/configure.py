from typing import *

from .local_config import LocalConfig, MissingLocalConfigException
from .password_manager import PasswordManager


__all__ = ["INPUT_NO_DEFAULT", "yes_no", "get_input", "header", "general_config"]


INPUT_NO_DEFAULT = "//*NO_DEFAULT*//"


def yes_no(prompt: str, default: Optional[bool] = None) -> bool:
    default = "y" if default else "n"
    return "y" == get_input(prompt, default=default, allowed_values=["y", "n"])


def get_input(
        prompt: str,
        hint: Optional[str] = None,
        default: Optional[str] = INPUT_NO_DEFAULT,
        allowed_values: Optional[Sequence[str]] = None
) -> Optional[str]:
    if hint is None and allowed_values:
        hint = "/".join(allowed_values)
        if default != INPUT_NO_DEFAULT and default not in allowed_values:
            raise Exception("The default must be in the allowed values.")

    s = prompt
    if hint:
        s = f"{s} ({hint})"
    if default != INPUT_NO_DEFAULT:
        s = f"{s} [{default}]"
    s = f"{s}: "
    ans = input(s).strip()
    ans = default if len(ans) == 0 else ans

    if allowed_values:
        if ans in allowed_values:
            return ans
        else:
            print(f"Error: The values must be one of {allowed_values}. Please try again.")
            return get_input(prompt, hint, default, allowed_values)
    elif ans == INPUT_NO_DEFAULT:
        print("Error: The field can't be empty! Please try again.")
        return get_input(prompt, hint, default, allowed_values)
    else:
        return ans


def header(s: str):
    print(f"\n==== {s} ====")


def general_config() -> LocalConfig:
    header("Welcome to the configuration!")
    print("Input will be requested in the following format: '<prompt> (<hint>) [<default>]:' \n"
          "You may select the default by using 'Enter'.")

    # Load or create default config:
    try:
        local_config = LocalConfig.load()
    except MissingLocalConfigException:
        # noinspection PyTypeChecker
        local_config = LocalConfig(None, None, None)

    # Configure username
    header("Configuring Azure Information")
    local_config.username = get_input(
        prompt="Tech-01 Email",
        hint="first.last@tech-01.net",
        default=local_config.username or INPUT_NO_DEFAULT
    )
    local_config.save()

    # Configure password with keyring
    pw_manager = PasswordManager(local_config.username)
    if not pw_manager.is_keyring_available():
        print("Keyring package not installed. Skipping storing password.")
        set_keyring = False
    elif pw_manager.is_keyring_set():
        use_keyring = yes_no("Continue to use the system keyring to store your password?", True)
        if use_keyring:
            set_keyring = yes_no("Change the password in the keyring?", False)
        else:
            pw_manager.delete_keyring()
            print("Password is removed from keyring.")
            set_keyring = False
    else:
        set_keyring = yes_no("The system keyring may store your password. Do you want to use this service?", True)

    if set_keyring:
        password = pw_manager.ask_for_password()
        pw_manager.set_keyring(password)
        print("Password stored in keyring")

    return local_config
