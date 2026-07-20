"""Tests for the module registry."""

import unittest

from not_enough_secrets.lib import exceptions, registry
from not_enough_secrets.lib.modules.base64mod import Base64Module


class RegistryTest(unittest.TestCase):
    """Test module registry."""

    def test_get_module_returns_class(self):
        """Test `get_module`."""
        self.assertIs(registry.get_module("base64"), Base64Module)

    def test_get_unknown_module_raises(self):
        """Test behavior of `get_module` for unknown identifier."""
        with self.assertRaises(exceptions.UnknownModuleError):
            registry.get_module("does-not-exist")

    def test_has_module(self):
        """Test `has_module`."""
        self.assertTrue(registry.has_module("base64"))
        self.assertFalse(registry.has_module("nope"))

    def test_default_module_is_available(self):
        """Test `default_module`."""
        self.assertIn(registry.default_module(), registry.available_modules())
