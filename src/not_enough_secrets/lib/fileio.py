"""Safe file output, including atomic in-place replacement."""

import logging
import os
from pathlib import Path

from .exceptions import OutputError

log = logging.getLogger(__name__)

_TEMP_SUFFIX = ".nes-tmp"


def atomic_write(target: Path, data: bytes) -> None:
    """Write `data` to `target` atomically.

    A temporary file is written in the same directory and then moved onto the
    target with `os.replace`. On any failure the target is left untouched and
    the temporary file is removed.

    :param target: destination path
    :param data: bytes to write
    """
    directory = target.parent
    if not directory.is_dir():
        raise OutputError(f"output directory does not exist: {directory}")
    temp = _unique_temp(directory, target.name)
    try:
        with open(temp, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, target)
    except OSError as err:
        _cleanup(temp)
        raise OutputError(f"could not write output: {err}") from err
    except BaseException:
        _cleanup(temp)
        raise


def _unique_temp(directory: Path, name: str) -> Path:
    candidate = directory / f".{name}{_TEMP_SUFFIX}"
    index = 0
    while candidate.exists():
        index += 1
        candidate = directory / f".{name}{_TEMP_SUFFIX}.{index}"
    return candidate


def _cleanup(temp: Path) -> None:
    try:
        temp.unlink(missing_ok=True)
    except OSError:
        log.warning("could not remove temporary file %s", temp)
