import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr
)

if __name__ == "__main__":
    from awsad import cli
    sys.exit(cli.main())
