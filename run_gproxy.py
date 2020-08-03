import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout
)

if __name__ == "__main__":
    from gproxy import cli
    sys.exit(cli.main())
