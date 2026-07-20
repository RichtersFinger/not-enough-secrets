"""Encode and decode the common metadata header of encrypted files.

The layout is a fixed magic prefix followed by length-prefixed strings. Each
string is stored as a two byte big-endian length followed by its utf-8 bytes.
The module payload (IV, tag, ciphertext) is appended by the module itself and
is returned untouched by `decode`.
"""

from dataclasses import dataclass

from . import exceptions
from .constants import MAGIC


_LENGTH_BYTES = 2
_BYTE_ORDER = "big"
_FIELD_COUNT = 3


@dataclass
class Header:
    """Common metadata stored ahead of the module payload."""

    app_version: str
    module_id: str
    module_options: str


def encode(header: Header) -> bytes:
    """Serialize `header` into the metadata prefix bytes.

    :param header: the header to serialize
    """
    parts = [MAGIC]
    for field in (header.app_version, header.module_id, header.module_options):
        parts.append(_encode_string(field))
    return b"".join(parts)


def decode(data: bytes) -> tuple[Header, bytes]:
    """Parse the metadata prefix and return the header and module payload.

    :param data: the full file content
    """
    if not data.startswith(MAGIC):
        raise exceptions.DetectionError(
            "input is not a not-enough-secrets file"
        )
    offset = len(MAGIC)
    fields = []
    for _ in range(_FIELD_COUNT):
        value, offset = _decode_string(data, offset)
        fields.append(value)
    header = Header(
        app_version=fields[0], module_id=fields[1], module_options=fields[2]
    )
    return header, data[offset:]


def _encode_string(value: str) -> bytes:
    raw = value.encode("utf-8")
    if len(raw) >= 1 << (8 * _LENGTH_BYTES):
        raise exceptions.DecodeError("header field is too long to encode")
    return len(raw).to_bytes(_LENGTH_BYTES, _BYTE_ORDER) + raw


def _decode_string(data: bytes, offset: int) -> tuple[str, int]:
    end = offset + _LENGTH_BYTES
    if end > len(data):
        raise exceptions.DecodeError("truncated header")
    length = int.from_bytes(data[offset:end], _BYTE_ORDER)
    start = end
    end = start + length
    if end > len(data):
        raise exceptions.DecodeError("truncated header")
    try:
        value = data[start:end].decode("utf-8")
    except UnicodeDecodeError as err:
        raise exceptions.DecodeError(
            "header field is not valid utf-8"
        ) from err
    return value, end
