"""Tests for the file detector."""

import unittest

from not_enough_secrets.lib import codec, detector, exceptions


class DetectorTest(unittest.TestCase):
    """Test detector."""

    def test_detect_known_module(self):
        """Test behavior for known module."""
        header = codec.Header(
            app_version="0.1.0", module_id="base64", module_options=""
        )
        data = codec.encode(header)

        result = detector.detect(data)

        self.assertEqual(result.identifier, "base64")
        self.assertTrue(result.known)

    def test_detect_unknown_module(self):
        """Test behavior for unknown module."""
        header = codec.Header(
            app_version="0.1.0", module_id="ghost-9", module_options=""
        )
        data = codec.encode(header)

        result = detector.detect(data)

        self.assertFalse(result.known)

    def test_detect_non_nes_file_raises(self):
        """Test behavior unknown byte layout."""
        with self.assertRaises(exceptions.DetectionError):
            detector.detect(b"plain text")
