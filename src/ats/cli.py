from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ATS research toolkit")
    parser.add_argument("--version", action="store_true", help="show package version")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        from ats import __version__

        print(__version__)
        return

    parser.print_help()
