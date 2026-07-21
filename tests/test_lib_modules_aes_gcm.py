"""Tests for the AES-GCM module.

The whole suite is skipped when the cryptography package is not installed.
"""

import unittest
from pathlib import Path

from not_enough_secrets.lib import exceptions, core
from not_enough_secrets.lib.modules.aes_gcm import AesGcmModule


@unittest.skipUnless(
    AesGcmModule.is_available(), "cryptography is not installed"
)
class AesGcmModuleTest(unittest.TestCase):
    """Test AES-GCM-module."""

    def test_roundtrip_default(self):
        """Test round-trip."""
        module = AesGcmModule("")
        payload = module.encrypt(b"hello", b"pw")
        self.assertEqual(module.decrypt(payload, b"pw"), b"hello")

    def test_roundtrip_all_key_sizes(self):
        """Test round-trip for possible key sizes."""
        for bits in ("128", "192", "256"):
            module = AesGcmModule(bits)
            payload = module.encrypt(b"data", b"pw")
            self.assertEqual(module.decrypt(payload, b"pw"), b"data")

    def test_default_key_size_is_256(self):
        """Test default key size."""
        self.assertEqual(AesGcmModule("").key_bits, 256)

    def test_nonce_makes_each_encryption_unique(self):
        """Test encryption uniqueness."""
        module = AesGcmModule("")
        first = module.encrypt(b"hello", b"pw")
        second = module.encrypt(b"hello", b"pw")
        self.assertNotEqual(first, second)

    def test_wrong_key_raises_decrypt_error(self):
        """Test keysize validation failure."""
        module = AesGcmModule("")
        payload = module.encrypt(b"hello", b"pw")
        with self.assertRaises(exceptions.DecryptError):
            module.decrypt(payload, b"other")

    def test_tampered_payload_raises_decrypt_error(self):
        """Test behavior for manipulated payload."""
        module = AesGcmModule("")
        payload = bytearray(module.encrypt(b"hello", b"pw"))
        payload[-1] ^= 0x01
        with self.assertRaises(exceptions.DecryptError):
            module.decrypt(bytes(payload), b"pw")

    def test_short_payload_raises_decode_error(self):
        """Test behavior for truncated payload."""
        module = AesGcmModule("")
        with self.assertRaises(exceptions.DecodeError):
            module.decrypt(b"short", b"pw")

    def test_invalid_key_size_raises_option_error(self):
        """Test behavior for invalid key size."""
        with self.assertRaises(exceptions.OptionError):
            AesGcmModule("64")

    def test_non_numeric_option_raises_option_error(self):
        """Test behavior for invalid key size value."""
        with self.assertRaises(exceptions.OptionError):
            AesGcmModule("big")

    def test_backwards_compatibility(self):
        """Test decrypting existing file."""
        unencrypted = Path("tests/fixtures/aes-gcm-0.txt")
        encrypted = unencrypted.with_suffix(".txt.nes")

        self.assertEqual(
            core.decrypt(encrypted.read_bytes(), b"test", None),
            unencrypted.read_bytes(),
        )
