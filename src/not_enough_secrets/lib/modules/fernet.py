"""Fernet encryption module backed by the cryptography package.

The key is derived from the supplied password with PBKDF2-HMAC-SHA256 and a
random salt, then encoded as the urlsafe base64 key that Fernet expects. Each
payload stores its own salt so every encryption is independent. The payload
layout is `salt || fernet_token`, where the token already carries its version,
timestamp, IV, ciphertext and HMAC.
"""

import base64
import os

from .. import exceptions
from .base import Module, ModuleInfo

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    _CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    _CRYPTOGRAPHY_AVAILABLE = False

_SALT_BYTES = 16
_KEY_BYTES = 32
_PBKDF2_ITERATIONS = 600_000


class FernetModule(Module):
    """Fernet authenticated encryption with a PBKDF2 derived key."""

    def __init__(self, options: str) -> None:
        if options.strip():
            raise exceptions.OptionError(
                "the fernet module does not accept options"
            )

    @classmethod
    def info(cls) -> ModuleInfo:
        return ModuleInfo(
            identifier="fernet-0",
            base_name="fernet",
            version="0",
            priority=50,
            description=(
                "Fernet authenticated encryption with a PBKDF2-HMAC-SHA256 "
                + "derived key"
            ),
            options_help="none",
            requirements="the cryptography package",
            supports_streaming=False,
        )

    @classmethod
    def is_available(cls) -> bool:
        return _CRYPTOGRAPHY_AVAILABLE

    def options_string(self) -> str:
        return ""

    def encrypt(self, plaintext: bytes, key: bytes) -> bytes:
        salt = os.urandom(_SALT_BYTES)
        token = Fernet(self._derive_key(key, salt)).encrypt(plaintext)
        return salt + token

    def decrypt(self, payload: bytes, key: bytes) -> bytes:
        if len(payload) < _SALT_BYTES:
            raise exceptions.DecodeError("payload is too short")
        salt = payload[:_SALT_BYTES]
        token = payload[_SALT_BYTES:]
        try:
            return Fernet(self._derive_key(key, salt)).decrypt(token)
        except InvalidToken as err:
            raise exceptions.DecryptError(
                "wrong key or corrupted data"
            ) from err

    def _derive_key(self, key: bytes, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=_KEY_BYTES,
            salt=salt,
            iterations=_PBKDF2_ITERATIONS,
        )
        return base64.urlsafe_b64encode(kdf.derive(key))
