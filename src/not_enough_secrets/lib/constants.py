"""Global constants shared across components."""

import logging
from importlib.metadata import version, PackageNotFoundError


log = logging.getLogger(__name__)


# Magic prefix that marks a not-enough-secrets file.
MAGIC = b"NES\x00"


# Separator between the module identifier and its options in a `-m` string.
OPTION_SEPARATOR = ":"


# Name used for the cli program and user facing output.
PACKAGE_NAME = "not-enough-secrets"


# Version of the not-enough-secrets package.
try:
    APP_VERSION = version(PACKAGE_NAME)
except PackageNotFoundError:
    APP_VERSION = "0.0.0"
    log.warning(
        "Cannot load package version, it looks like '%s' is not "
        + "installed correctly. Falling back to version '%s'.",
        PACKAGE_NAME,
        APP_VERSION,
    )
