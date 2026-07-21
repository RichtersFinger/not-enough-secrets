"""Global index of known modules and helpers to select them.

Selection is deliberately simple. Maintainers manage relative priorities
to have the preferred version of a scheme win as default despite the index
not understanding that two identifiers belong to the same base scheme.
"""

from .exceptions import NoModulesAvailableError, UnknownModuleError
from .modules.base import Module
from .modules.base64mod import Base64Module
from .modules.aes_gcm import AesGcmModule
from .modules.fernet import FernetModule


# Every registered module class. Extend this list to add modules.
_MODULES: list[type[Module]] = [
    Base64Module,
    AesGcmModule,
    FernetModule,
]


def all_modules() -> list[type[Module]]:
    """Return all registered modules sorted by priority then identifier."""
    return sorted(_MODULES, key=_sort_key)


def available_modules() -> list[type[Module]]:
    """Return registered modules that can run on the current system."""
    return [module for module in all_modules() if module.is_available()]


def has_module(identifier: str) -> bool:
    """Return whether a module with `identifier` is registered.

    :param identifier: module identifier to look up
    """
    return any(module.info().identifier == identifier for module in _MODULES)


def get_module(identifier: str) -> type[Module]:
    """Return the module class for `identifier`.

    :param identifier: module identifier to look up
    """
    for module in _MODULES:
        if module.info().identifier == identifier:
            return module
    raise UnknownModuleError(f"unknown module '{identifier}'")


def default_module() -> type[Module]:
    """Return the highest ranked available module."""
    available = available_modules()
    if not available:
        raise NoModulesAvailableError("no encryption module is available")
    return available[0]


def _sort_key(module: type[Module]) -> tuple[int, str]:
    info = module.info()
    return (-info.priority, info.identifier)
