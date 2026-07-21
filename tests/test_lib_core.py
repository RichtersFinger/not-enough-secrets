"""Tests for the encrypt and decrypt orchestration."""

import unittest

from not_enough_secrets.lib import core, codec, modules, exceptions


class CoreTest(unittest.TestCase):
    """Test library core."""

    def test_default_roundtrip(self):
        """Test round-trip."""
        blob = core.encrypt(b"secret data", b"pw", None)
        self.assertEqual(core.decrypt(blob, b"pw", None), b"secret data")

    def test_explicit_module_roundtrip(self):
        """Test round-trip with specific module."""
        blob = core.encrypt(b"secret data", b"pw", "base64")
        self.assertEqual(core.decrypt(blob, b"pw", None), b"secret data")

    def test_wrong_key_raises(self):
        """Test round-trip failed: wrong key."""
        blob = core.encrypt(b"secret data", b"pw", None)
        with self.assertRaises(exceptions.DecryptError):
            core.decrypt(blob, b"wrong", None)

    def test_unknown_module_on_encrypt_raises(self):
        """Test unknown module."""
        with self.assertRaises(exceptions.UnknownModuleError):
            core.encrypt(b"data", b"pw", "ghost-9")

    def test_parse_module_spec(self):
        """Test parsing of module spec."""
        self.assertEqual(core.parse_module_spec("base64"), ("base64", ""))
        self.assertEqual(
            core.parse_module_spec("aesgcm-1:mode=x"), ("aesgcm-1", "mode=x")
        )

    @unittest.skipUnless(
        modules.aes_gcm.AesGcmModule.is_available(),
        "cryptography is not installed",
    )
    def test_header_stores_resolved_default_options(self):
        """Test generation and parsing of module options."""
        blob = core.encrypt(b"data", b"pw", "aes-gcm-0")
        header, _ = codec.decode(blob)
        self.assertEqual(header.module_options, "256")
