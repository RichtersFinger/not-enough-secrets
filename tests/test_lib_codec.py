"""Tests for the metadata encoder and decoder."""

import unittest

from not_enough_secrets.lib import codec, exceptions


class CodecRoundTripTest(unittest.TestCase):
    """Test codec round-trip."""

    def test_roundtrip_preserves_header_and_payload(self):
        """Validate header+payload are preserved."""
        header = codec.Header(
            app_version="0.1.0", module_id="base64", module_options=""
        )
        payload = b"cipher-bytes"

        encoded = codec.encode(header) + payload
        decoded_header, decoded_payload = codec.decode(encoded)

        self.assertEqual(decoded_header, header)
        self.assertEqual(decoded_payload, payload)


class CodecErrorTest(unittest.TestCase):
    """Test codec error behavior."""

    def test_missing_magic_raises_detection_error(self):
        """Missing magic bytes."""
        with self.assertRaises(exceptions.DetectionError):
            codec.decode(b"not a valid file")

    def test_truncated_header_raises_decode_error(self):
        """Truncated header."""
        header = codec.Header(
            app_version="0.1.0", module_id="base64", module_options=""
        )
        encoded = codec.encode(header)

        with self.assertRaises(exceptions.DecodeError):
            codec.decode(encoded[:-1])
