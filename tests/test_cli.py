"""Integration tests that drive the cli for the most important paths."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from not_enough_secrets import cli


class CliIntegrationTest(unittest.TestCase):
    """Use CLI for integration tests."""

    def test_encrypt_then_decrypt_via_files(self):
        """Round trip through CLI."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "plain.txt"
            encrypted = Path(directory) / "cipher.nes"
            decrypted = Path(directory) / "plain.out"
            source.write_bytes(b"hello world")

            with mock.patch(
                "not_enough_secrets.cli.getpass.getpass", return_value="pw"
            ):
                self.assertEqual(
                    cli.main(["encrypt", str(source), "-o", str(encrypted)]), 0
                )
                self.assertEqual(
                    cli.main(
                        ["decrypt", str(encrypted), "-o", str(decrypted)]
                    ),
                    0,
                )

            self.assertEqual(decrypted.read_bytes(), b"hello world")

    def test_output_exists_without_force_fails(self):
        """Test status code with and without force."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "plain.txt"
            target = Path(directory) / "cipher.nes"
            source.write_bytes(b"data")
            target.write_bytes(b"existing")

            with mock.patch(
                "not_enough_secrets.cli.getpass.getpass", return_value="pw"
            ):
                self.assertEqual(
                    cli.main(["encrypt", str(source), "-o", str(target)]), 1
                )
                self.assertEqual(
                    cli.main(
                        ["encrypt", str(source), "-o", str(target), "-f"]
                    ),
                    0,
                )

    def test_mismatched_key_confirmation_fails(self):
        """Test abort when key input mismatch."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "plain.txt"
            source.write_bytes(b"data")

            with mock.patch(
                "not_enough_secrets.cli.getpass.getpass",
                side_effect=["a", "b"],
            ):
                self.assertEqual(
                    cli.main(
                        [
                            "encrypt",
                            str(source),
                            "-o",
                            str(Path(directory) / "x"),
                        ]
                    ),
                    1,
                )

    def test_modules_lists_base64(self):
        """Test basic modules command."""
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            self.assertEqual(cli.main(["modules"]), 0)
        self.assertIn("base64", buffer.getvalue())

    def test_version(self):
        """Test basic version command."""
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            self.assertEqual(cli.main(["version"]), 0)
        self.assertIn("not-enough-secrets", buffer.getvalue())
