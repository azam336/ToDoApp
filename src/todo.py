"""Main entry-point: python -m src.todo <command> [args]."""

import sys

from src.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
