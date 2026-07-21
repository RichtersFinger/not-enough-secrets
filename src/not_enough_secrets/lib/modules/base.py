"""Common interface and data carrier for encryption modules."""

import abc
from dataclasses import dataclass
from typing import BinaryIO

from .. import exceptions


@dataclass(frozen=True)
class ModuleInfo:
    """Human and machine readable description of a module.

    :param identifier: unique identifier stored in file metadata, for example
        `aesgcm-1`; combines `base_name` and `version`; a base-/default module
        for a specific algorithm can be named without a specific version in its
        identifier
    :param base_name: name of the scheme without a version
    :param version: version of the scheme, part of the identifier
    :param priority: higher values win when picking a default module
    :param description: short description of the scheme
    :param options_help: brief explanation of the accepted options
    :param requirements: human readable system requirements
    :param supports_streaming: whether the module can process data streams
    """

    identifier: str
    base_name: str
    version: str
    priority: int
    description: str
    options_help: str
    requirements: str
    supports_streaming: bool = False


class Module(abc.ABC):
    """Base class every encryption module implements.

    The module receives its options string on construction and parses it there.
    The encryption key is never stored on the instance, it is passed to
    `encrypt` and `decrypt` so instances stay reusable and easy to test.
    """

    def __init__(self, options: str) -> None:
        """Parse the module specific `options` string.

        :param options: options portion of a `-m` string
        """

    @classmethod
    @abc.abstractmethod
    def info(cls) -> ModuleInfo:
        """Return static information about the module."""

    @abc.abstractmethod
    def options_string(self) -> str:
        """Return the canonical options for this instance.

        Reflects the settings actually in use, including any defaults, so the
        header stores what is needed to reconstruct the module on decrypt.
        """

    @classmethod
    @abc.abstractmethod
    def is_available(cls) -> bool:
        """Return whether the module can run on the current system."""

    @abc.abstractmethod
    def encrypt(self, plaintext: bytes, key: bytes) -> bytes:
        """Return the payload for `plaintext` using `key`.

        :param plaintext: data to encrypt
        :param key: raw key material
        """

    @abc.abstractmethod
    def decrypt(self, payload: bytes, key: bytes) -> bytes:
        """Return the plaintext for a module `payload` using `key`.

        :param payload: module payload produced by `encrypt`
        :param key: raw key material
        """

    def encrypt_stream(
        self, reader: BinaryIO, writer: BinaryIO, key: bytes
    ) -> None:
        """Encrypt from `reader` to `writer`. Optional streaming capability.

        :param reader: source stream
        :param writer: target stream
        :param key: raw key material
        """
        raise exceptions.UnsupportedError(
            f"module '{self.info().identifier}' does not support streaming"
        )

    def decrypt_stream(
        self, reader: BinaryIO, writer: BinaryIO, key: bytes
    ) -> None:
        """Decrypt from `reader` to `writer`. Optional streaming capability.

        :param reader: source stream
        :param writer: target stream
        :param key: raw key material
        """
        raise exceptions.UnsupportedError(
            f"module '{self.info().identifier}' does not support streaming"
        )
