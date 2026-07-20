"""Exception hierarchy used across the tool.

All errors derive from `NesError` so the cli can catch and
pretty-print them instead of letting a traceback reach the
interpreter.
"""


class NesError(Exception):
    """Base class for all not-enough-secrets errors."""


class DetectionError(NesError):
    """Raised when input is not a not-enough-secrets file."""


class DecodeError(NesError):
    """Raised when stored data cannot be parsed."""


class OptionError(NesError):
    """Raised when a module options string cannot be parsed."""


class ModuleError(NesError):
    """Base class for module related errors."""


class UnknownModuleError(ModuleError):
    """Raised when a module identifier is not registered."""


class ModuleUnavailableError(ModuleError):
    """Raised when a known module cannot run on the current system."""

    def __init__(self, identifier: str, requirements: str) -> None:
        super().__init__(
            f"module '{identifier}' is not available on this system"
        )
        self.identifier = identifier
        self.requirements = requirements


class NoModulesAvailableError(ModuleError):
    """Raised when no module is available for the default selection."""


class DecryptError(NesError):
    """Raised when decryption fails, for example on a wrong key."""


class OutputError(NesError):
    """Raised when an output file cannot be written."""


class UnsupportedError(NesError):
    """Raised when an operation is not supported by a module."""
