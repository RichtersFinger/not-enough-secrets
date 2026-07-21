"""Tests for the Fernet module.

The whole suite is skipped when the cryptography package is not installed.
"""

import unittest

from not_enough_secrets.lib import exceptions
from not_enough_secrets.lib.modules.fernet import FernetModule


@unittest.skipUnless(
    FernetModule.is_available(), "cryptography is not installed"
)
class FernetModuleTest(unittest.TestCase):
    """Test Fernet-module."""

    def setUp(self):
        self.module = FernetModule("")

    def test_roundtrip(self):
        """Test round-trip."""
        payload = self.module.encrypt(b"hello", b"pw")
        self.assertEqual(self.module.decrypt(payload, b"pw"), b"hello")

    def test_salt_makes_each_encryption_unique(self):
        """Test encryption uniqueness."""
        first = self.module.encrypt(b"hello", b"pw")
        second = self.module.encrypt(b"hello", b"pw")
        self.assertNotEqual(first, second)

    def test_wrong_key_raises_decrypt_error(self):
        """Test keysize validation failure."""
        payload = self.module.encrypt(b"hello", b"pw")
        with self.assertRaises(exceptions.DecryptError):
            self.module.decrypt(payload, b"other")

    def test_tampered_payload_raises_decrypt_error(self):
        """Test behavior for manipulated payload."""
        payload = bytearray(self.module.encrypt(b"hello", b"pw"))
        payload[-1] ^= 0x01
        with self.assertRaises(exceptions.DecryptError):
            self.module.decrypt(bytes(payload), b"pw")

    def test_short_payload_raises_decode_error(self):
        """Test behavior for truncated payload."""
        with self.assertRaises(exceptions.DecodeError):
            self.module.decrypt(b"short", b"pw")

    def test_options_are_rejected(self):
        """Test behavior for unexpected options."""
        with self.assertRaises(exceptions.OptionError):
            FernetModule("mode=x")
