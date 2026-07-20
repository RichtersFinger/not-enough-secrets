"""Detect not-enough-secrets files and identify their module."""

from dataclasses import dataclass

from . import codec, registry


@dataclass
class Detection:
    """Result of inspecting a file header.

    :param identifier: module identifier stored in the header
    :param options: module options stored in the header
    :param known: whether the identifier is registered on this system
    """

    identifier: str
    options: str
    known: bool


def detect(data: bytes) -> Detection:
    """Inspect `data` and report the module it was encrypted with.

    :param data: the full file content
    """
    header, _ = codec.decode(data)
    return Detection(
        identifier=header.module_id,
        options=header.module_options,
        known=registry.has_module(header.module_id),
    )
