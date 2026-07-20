"""Orchestration of encryption and decryption over the codec and modules."""

import logging

from . import codec, exceptions, registry
from .constants import APP_VERSION, OPTION_SEPARATOR
from .modules.base import Module

log = logging.getLogger(__name__)


def parse_module_spec(spec: str) -> tuple[str, str]:
    """Split a `-m` string into an identifier and its options.

    :param spec:
        value passed to `-m`, for example `base64` or `aesgcm-1:mode=x`
    """
    identifier, separator, options = spec.partition(OPTION_SEPARATOR)
    return identifier, options if separator else ""


def encrypt(plaintext: bytes, key: bytes, module_spec: str | None) -> bytes:
    """Encrypt `plaintext` and return a complete not-enough-secrets file.

    :param plaintext: data to encrypt
    :param key: raw key material
    :param module_spec:
        optional `-m` string; the default module is used if None
    """
    if module_spec:
        identifier, options = parse_module_spec(module_spec)
        module_cls = _require_available(registry.get_module(identifier))
    else:
        module_cls = registry.default_module()
        identifier = module_cls.info().identifier
        options = ""
    log.info("encrypting with module %s", identifier)
    module = module_cls(options)
    payload = module.encrypt(plaintext, key)
    header = codec.Header(
        app_version=APP_VERSION, module_id=identifier, module_options=options
    )
    return codec.encode(header) + payload


def decrypt(data: bytes, key: bytes, override_spec: str | None) -> bytes:
    """Decrypt a not-enough-secrets file and return its plaintext.

    :param data: the full file content
    :param key: raw key material
    :param override_spec: optional `-m` string to force a module and options
    """
    header, payload = codec.decode(data)
    if override_spec:
        identifier, options = parse_module_spec(override_spec)
    else:
        identifier, options = header.module_id, header.module_options
    log.info("decrypting with module %s", identifier)
    module_cls = _require_available(registry.get_module(identifier))
    module = module_cls(options)
    return module.decrypt(payload, key)


def _require_available(module_cls: type[Module]) -> type[Module]:
    if not module_cls.is_available():
        info = module_cls.info()
        raise exceptions.ModuleUnavailableError(
            info.identifier, info.requirements
        )
    return module_cls
