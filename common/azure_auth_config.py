from dataclasses import dataclass


@dataclass(frozen=True)
class AuthConfig:
    headless: bool
    use_cookies: bool
    dump_io: bool
    keep_open: bool

    @staticmethod
    def add_arguments_to_parser(parser):
        parser.add_argument("-n", "--no-headless", help="Login to Azure AD in non-headless mode", action="store_true")
        parser.add_argument("-d", "--debug", help="Debug mode", action="store_true")
        parser.add_argument("-c", "--no-cookies", help="Login without using cookies", action="store_true")
        parser.add_argument("-p", "--profile", help="AWS Profile")

    @classmethod
    def from_args(cls, args) -> "AuthConfig":
        return AuthConfig(
            headless=not args.no_headless,
            use_cookies=not args.no_cookies,
            dump_io=args.debug,
            keep_open=args.debug and not args.no_headless
        )
