"""
Module entry point so the tool can run via `python -m not_enough_secrets`.
"""

import sys

from .cli import main


if __name__ == "__main__":
    sys.exit(main())
