"""Tests for the base64 obfuscation module."""

import base64
import unittest
from pathlib import Path

from not_enough_secrets.lib import exceptions, core
from not_enough_secrets.lib.modules.base64mod import Base64Module


class Base64ModuleTest(unittest.TestCase):
    """Test Base64-module."""

    def setUp(self):
        self.module = Base64Module("")

    def test_roundtrip(self):
        """Test round-trip."""
        payload = self.module.encrypt(b"hello", b"key")
        self.assertEqual(self.module.decrypt(payload, b"key"), b"hello")

    def test_wrong_key_raises_decrypt_error(self):
        """Test bad key."""
        payload = self.module.encrypt(b"hello", b"key")
        with self.assertRaises(exceptions.DecryptError):
            self.module.decrypt(payload, b"other")

    def test_invalid_base64_raises_decode_error(self):
        """Test behavior for bad base64."""
        with self.assertRaises(exceptions.DecodeError):
            self.module.decrypt(b"not base64!", b"key")

    def test_truncated_payload_raises_decode_error(self):
        """Test behavior for truncated payload."""
        with self.assertRaises(exceptions.DecodeError):
            self.module.decrypt(base64.b64encode(b"\x00"), b"key")

    def test_options_are_rejected(self):
        """Test behavior for unknown option."""
        with self.assertRaises(exceptions.OptionError):
            Base64Module("mode=x")

    def test_backwards_compatibility(self):
        """Test decrypting existing file."""
        unencrypted = Path("tests/fixtures/base64.txt")
        encrypted = unencrypted.with_suffix(".txt.nes")

        self.assertEqual(
            core.decrypt(encrypted.read_bytes(), b"test", None),
            unencrypted.read_bytes(),
        )
