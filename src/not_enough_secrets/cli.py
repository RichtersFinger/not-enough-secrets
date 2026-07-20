"""Command line frontend: argument parsing, input and output, command routing.

All input, output and key prompting live here. The library never touches stdin
or stdout, which keeps it easy to test.
"""

import argparse
import getpass
import logging
import sys
import traceback
from pathlib import Path

from .lib import core, exceptions, fileio, registry
from .lib.constants import APP_VERSION, PACKAGE_NAME
from .lib.modules.base import ModuleInfo

log = logging.getLogger(__name__)

_STDIN_MARKER = "-"


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the whole tool."""
    parser = argparse.ArgumentParser(
        prog=PACKAGE_NAME, description="basic cli tool for file encryption"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="enable info logging"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="enable debug logging and tracebacks",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("version", help="show the package version")

    modules_parser = sub.add_parser("modules", help="list available modules")
    modules_parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="also list modules that are not available",
    )

    for name, help_text in (
        ("encrypt", "encrypt a file"),
        ("decrypt", "decrypt a file"),
    ):
        command = sub.add_parser(name, help=help_text)
        command.add_argument(
            "file", help="input file, or - to read from stdin"
        )
        command.add_argument(
            "-m",
            "--module",
            help="module identifier and options, for example base64",
        )
        command.add_argument(
            "--stdout",
            action="store_true",
            help="also write the result to stdout",
        )
        command.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="overwrite an existing output file",
        )
        target = command.add_mutually_exclusive_group()
        target.add_argument(
            "--in-place", action="store_true", help="replace the input file"
        )
        target.add_argument(
            "-o", "--output", help="write the result to this path"
        )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entry point.

    :param argv: optional argument list, defaults to `sys.argv`
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args)
    try:
        return _dispatch(args)
    except exceptions.NesError as err:
        _report_error(str(err), args.debug)
        return 1
    # pylint: disable=broad-exception-caught
    # (defensive catch all)
    except Exception as err:
        _report_error(f"unexpected error: {err}", args.debug)
        return 1


def _configure_logging(args: argparse.Namespace) -> None:
    if args.debug:
        level = logging.DEBUG
    elif args.verbose:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(
        level=level,
        stream=sys.stderr,
        format="%(levelname)s %(name)s: %(message)s",
    )


def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "version":
        return _cmd_version()
    if args.command == "modules":
        return _cmd_modules(args)
    if args.command == "encrypt":
        return _cmd_encrypt(args)
    if args.command == "decrypt":
        return _cmd_decrypt(args)
    raise exceptions.NesError(f"unknown command: {args.command}")


def _cmd_version() -> int:
    print(f"{PACKAGE_NAME} {APP_VERSION}")
    return 0


def _cmd_modules(args: argparse.Namespace) -> int:
    shown = 0
    for module_cls in registry.all_modules():
        available = module_cls.is_available()
        if not available and not args.all:
            continue
        print(_format_module(module_cls.info(), available))
        shown += 1
    if shown == 0:
        print("no modules are available")
    return 0


def _cmd_encrypt(args: argparse.Namespace) -> int:
    _validate_targets(args)
    data = _read_input(args.file)
    key = _prompt_key(confirm=True)
    try:
        result = core.encrypt(data, key, args.module)
    except exceptions.ModuleUnavailableError as err:
        _report_error(str(err), args.debug)
        print(f"requires: {err.requirements}", file=sys.stderr)
        return 1
    except exceptions.NoModulesAvailableError as err:
        _report_error(str(err), args.debug)
        _print_overview()
        return 1
    _handle_output(result, args)
    return 0


def _cmd_decrypt(args: argparse.Namespace) -> int:
    _validate_targets(args)
    data = _read_input(args.file)
    key = _prompt_key(confirm=False)
    try:
        result = core.decrypt(data, key, args.module)
    except exceptions.ModuleUnavailableError as err:
        _report_error(str(err), args.debug)
        print(f"requires: {err.requirements}", file=sys.stderr)
        return 1
    except exceptions.UnknownModuleError as err:
        _report_error(str(err), args.debug)
        print(
            "use -m to override the module if you know which one applies",
            file=sys.stderr,
        )
        return 1
    _handle_output(result, args)
    return 0


def _validate_targets(args: argparse.Namespace) -> None:
    if args.in_place and args.file == _STDIN_MARKER:
        raise exceptions.NesError("cannot use --in-place with stdin input")


def _read_input(path_value: str) -> bytes:
    if path_value == _STDIN_MARKER:
        return sys.stdin.buffer.read()
    path = Path(path_value)
    if not path.is_file():
        raise exceptions.NesError(f"input file not found: {path}")
    return path.read_bytes()


def _prompt_key(confirm: bool) -> bytes:
    key = getpass.getpass("Key: ")
    if confirm:
        again = getpass.getpass("Confirm key: ")
        if key != again:
            raise exceptions.NesError("keys do not match")
    return key.encode("utf-8")


def _handle_output(result: bytes, args: argparse.Namespace) -> None:
    wrote_file = False
    if args.in_place:
        fileio.atomic_write(Path(args.file), result)
        wrote_file = True
    elif args.output:
        target = Path(args.output)
        if target.exists() and not args.force:
            raise exceptions.OutputError(
                f"output file exists: {target} (use --force to overwrite)"
            )
        fileio.atomic_write(target, result)
        wrote_file = True
    if args.stdout or not wrote_file:
        sys.stdout.buffer.write(result)
        sys.stdout.buffer.flush()


def _format_module(info: ModuleInfo, available: bool) -> str:
    lines = [
        info.identifier if available else f"{info.identifier}  [unavailable]"
    ]
    lines.append(f"    {info.description}")
    if available:
        if info.options_help:
            lines.append(f"    options: {info.options_help}")
    else:
        lines.append(f"    requires: {info.requirements}")
    return "\n".join(lines)


def _print_overview() -> None:
    print("defined modules:", file=sys.stderr)
    for module_cls in registry.all_modules():
        print(
            _format_module(module_cls.info(), module_cls.is_available()),
            file=sys.stderr,
        )


def _report_error(message: str, debug: bool) -> None:
    print(f"error: {message}", file=sys.stderr)
    if debug:
        traceback.print_exc()
