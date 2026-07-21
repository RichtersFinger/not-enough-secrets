"""AES-GCM encryption module backed by the cryptography package.

The key is derived from the supplied password with PBKDF2-HMAC-SHA256. Each
payload stores its own random salt and nonce so every encryption is
independent. The payload layout is `salt || nonce || ciphertext_with_tag`,
where the 16 byte GCM tag is appended to the ciphertext by the cryptography
API.
"""

import os

from .. import exceptions
from .base import Module, ModuleInfo

try:
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    _CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    _CRYPTOGRAPHY_AVAILABLE = False

_SALT_BYTES = 16
_NONCE_BYTES = 12
_PBKDF2_ITERATIONS = 600_000
_DEFAULT_KEY_BITS = 256
_VALID_KEY_BITS = (128, 192, 256)
_BITS_PER_BYTE = 8


class AesGcmModule(Module):
    """AES-GCM with a PBKDF2 derived key."""

    def __init__(self, options: str) -> None:
        self.key_bits = _parse_options(options)
        self.key_bytes = self.key_bits // _BITS_PER_BYTE

    @classmethod
    def info(cls) -> ModuleInfo:
        return ModuleInfo(
            identifier="aes-gcm-0",
            base_name="aes-gcm",
            version="0",
            priority=100,
            description="AES-GCM with a PBKDF2-HMAC-SHA256 derived key",
            options_help=(
                "optional key size in bits, one of 128, 192 or 256 "
                + "(default 256)"
            ),
            requirements="the cryptography package",
            supports_streaming=False,
        )

    def options_string(self) -> str:
        return str(self.key_bits)

    @classmethod
    def is_available(cls) -> bool:
        return _CRYPTOGRAPHY_AVAILABLE

    def encrypt(self, plaintext: bytes, key: bytes) -> bytes:
        salt = os.urandom(_SALT_BYTES)
        nonce = os.urandom(_NONCE_BYTES)
        derived = self._derive_key(key, salt)
        ciphertext = AESGCM(derived).encrypt(nonce, plaintext, None)
        return salt + nonce + ciphertext

    def decrypt(self, payload: bytes, key: bytes) -> bytes:
        header_length = _SALT_BYTES + _NONCE_BYTES
        if len(payload) < header_length:
            raise exceptions.DecodeError("payload is too short")
        salt = payload[:_SALT_BYTES]
        nonce = payload[_SALT_BYTES:header_length]
        ciphertext = payload[header_length:]
        derived = self._derive_key(key, salt)
        try:
            return AESGCM(derived).decrypt(nonce, ciphertext, None)
        except InvalidTag as err:
            raise exceptions.DecryptError(
                "wrong key or corrupted data"
            ) from err

    def _derive_key(self, key: bytes, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.key_bytes,
            salt=salt,
            iterations=_PBKDF2_ITERATIONS,
        )
        return kdf.derive(key)


def _parse_options(options: str) -> int:
    text = options.strip()
    if not text:
        return _DEFAULT_KEY_BITS
    if not text.isdigit():
        raise exceptions.OptionError(
            f"key size must be a number, got '{text}'"
        )
    key_bits = int(text)
    if key_bits not in _VALID_KEY_BITS:
        allowed = ", ".join(str(bits) for bits in _VALID_KEY_BITS)
        raise exceptions.OptionError(
            f"key size must be one of {allowed}, got {key_bits}"
        )
    return key_bits
