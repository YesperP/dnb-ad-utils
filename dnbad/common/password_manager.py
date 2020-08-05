import getpass

try:
    import keyring
    import keyring.errors

    KEYRING = True
except ImportError:
    keyring = None
    KEYRING = False


class PasswordManager:
    SERVICE_NAME = "dnb-ad-utils"

    def __init__(self, username: str, use_keyring=True):
        self.username = username
        self.use_keyring = use_keyring
        self._password = None

    @classmethod
    def is_keyring_available(cls) -> bool:
        return KEYRING

    def is_keyring_set(self):
        return keyring.get_password(self.SERVICE_NAME, self.username) is not None

    def ask_for_password(self):
        return getpass.getpass(f"Password for {self.username} (hidden input): ")

    def ask_for_otc(self) -> str:
        return input(f"OTC for {self.username}: ")

    def delete_keyring(self):
        keyring.delete_password(self.SERVICE_NAME, self.username)

    def fetch_password(self):
        if self.is_keyring_available():
            self._password = keyring.get_password(self.SERVICE_NAME, self.username) or self.ask_for_password()
        else:
            self._password = self.ask_for_password()

    def get_password(self) -> str:
        if not self._password:
            self.fetch_password()
        return self._password

    def set_keyring(self, password):
        keyring.set_password(self.SERVICE_NAME, self.username, password)
