"""Command line entry point.

Each command lives in its own module under paperboy_pipeline.commands and exposes
register(subparsers), which adds one subparser and sets its `run` default to a
function taking the parsed args and returning an exit code. Adding a command means
adding a module; this file does not change.
"""
import argparse
import importlib
import pkgutil
import sys

from . import commands


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="paperboy-pipeline", description=__doc__.split("\n")[0])
    subparsers = parser.add_subparsers(dest="command", required=True)
    for module_info in sorted(pkgutil.iter_modules(commands.__path__), key=lambda m: m.name):
        module = importlib.import_module(f"{commands.__name__}.{module_info.name}")
        module.register(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.run(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
