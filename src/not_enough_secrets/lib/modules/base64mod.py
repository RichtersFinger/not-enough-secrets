"""Base64 obfuscation module.

WARNING: this module provides no security. It only obfuscates data
with base64 encoding and a plain key prefix. It exists for tests
and debugging and must not be used to protect real data. The key is
stored in clear in the payload.
"""

import base64
import binascii

from .. import exceptions
from .base import Module, ModuleInfo

_KEY_LENGTH_BYTES = 4
_BYTE_ORDER = "big"


class Base64Module(Module):
    """Reversible base64 obfuscation, not a real cipher."""

    def __init__(self, options: str) -> None:
        if options.strip():
            raise exceptions.OptionError(
                "the base64 module does not accept options"
            )

    @classmethod
    def info(cls) -> ModuleInfo:
        return ModuleInfo(
            identifier="base64",
            base_name="base64",
            version="1",
            priority=0,
            description=(
                "UNSAFE base64 obfuscation for tests and debugging only"
            ),
            options_help="none",
            requirements="none, uses the standard library only",
            supports_streaming=False,
        )

    @classmethod
    def is_available(cls) -> bool:
        return True

    def encrypt(self, plaintext: bytes, key: bytes) -> bytes:
        body = _encode_key(key) + key + plaintext
        return base64.b64encode(body)

    def decrypt(self, payload: bytes, key: bytes) -> bytes:
        try:
            raw = base64.b64decode(payload, validate=True)
        except (binascii.Error, ValueError) as err:
            raise exceptions.DecodeError(
                "payload is not valid base64"
            ) from err
        if len(raw) < _KEY_LENGTH_BYTES:
            raise exceptions.DecodeError("payload is too short")
        key_length = int.from_bytes(raw[:_KEY_LENGTH_BYTES], _BYTE_ORDER)
        key_end = _KEY_LENGTH_BYTES + key_length
        if key_end > len(raw):
            raise exceptions.DecodeError("payload is truncated")
        if raw[_KEY_LENGTH_BYTES:key_end] != key:
            raise exceptions.DecryptError("wrong key")
        return raw[key_end:]


def _encode_key(key: bytes) -> bytes:
    if len(key) >= 1 << (8 * _KEY_LENGTH_BYTES):
        raise exceptions.OptionError("key is too long for the base64 module")
    return len(key).to_bytes(_KEY_LENGTH_BYTES, _BYTE_ORDER)
