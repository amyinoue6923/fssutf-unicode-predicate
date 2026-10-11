"""FSS-UTF (UTF-8) byte-string validation.

FSS-UTF is the file-system-safe UTF transform defined in the original
Unicode 1.0 specification. It is functionally identical to what RFC 3629
later standardised as UTF-8. This module implements a strict validator for
raw byte strings (``bytes`` and ``bytearray``) that enforces:

* Every byte forms part of a well-formed UTF-8 sequence.
* No overlong encodings (e.g. U+0000 must be 0x00, not 0xC0 0x80).
* No encoding of a surrogate code point (U+D800..U+DFFF).
* No encoding of a code point above U+10FFFF.
* No trailing leading byte that lacks the continuation bytes it requires.

Design decisions:
  - Operate on ``bytes`` / ``bytearray`` only. Decoding ``str`` to bytes
    would require choosing a codec, and the whole point of FSS-UTF is to be
    that codec. Passing ``str`` raises ``TypeError`` so callers learn they
    are using the wrong type, not a silent success.
  - Iterate index-by-index with local state instead of calling
    ``bytes.decode('utf-8')``. Decoding would accept some inputs the FSS-UTF
    spec rejects (Python's ``utf-8`` codec is lenient with lone surrogates
    via the ``surrogatepass`` error handler, and we want a hard rejection).
    A hand-rolled state machine also makes the rejection reasons explicit.
  - Return ``bool`` rather than raising an exception on invalid input;
    callers who want the reason can extend this, but a predicate is the
    minimal useful contract.
"""

from __future__ import annotations

__all__ = ["is_valid_fssutf", "is_valid_fssutf_ascii"]


def is_valid_fssutf(data: bytes | bytearray) -> bool:
    """Return ``True`` if *data* is a well-formed FSS-UTF (UTF-8) byte string.

    ``data`` must be ``bytes`` or ``bytearray``. Any other type raises
    ``TypeError``. The validator rejects empty input as valid (an empty
    byte string is a valid UTF-8 string).

    The validator is strict: it rejects overlong encodings, lone surrogates,
    code points above U+10FFFF, truncated sequences, and stray continuation
    bytes.
    """
    # Accept bytearray by duck-typing; reject str explicitly so that a
    # caller passing text gets a clear error rather than a confusing
    # iteration over code points.
    if isinstance(data, (str,)):
        raise TypeError(
            "is_valid_fssutf expects bytes or bytearray, not str; "
            "FSS-UTF is itself the text-to-bytes transform"
        )
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError(
            "is_valid_fssutf expects bytes or bytearray, got "
            + type(data).__name__
        )

    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        if b < 0x80:
            # Single-byte ASCII.
            i += 1
            continue

        if b < 0xC2:
            # 0x80..0xBF are stray continuation bytes.
            # 0xC0 and 0xC1 can only start overlong 2-byte sequences
            # (U+0000..U+007F), which the spec forbids.
            return False

        if b < 0xE0:
            # 2-byte sequence for U+0080..U+07FF.
            if i + 1 >= n:
                return False
            if (data[i + 1] & 0xC0) != 0x80:
                return False
            i += 2
            continue

        if b < 0xF0:
            # 3-byte sequence for U+0800..U+FFFF (excluding surrogates).
            if i + 2 >= n:
                return False
            c1 = data[i + 1]
            c2 = data[i + 2]
            if (c1 & 0xC0) != 0x80 or (c2 & 0xC0) != 0x80:
                return False
            # Overlong guard: the lowest 3-byte form is 0xE0 0xA0 0x80.
            if b == 0xE0 and c1 < 0xA0:
                return False
            # Surrogate guard: U+D800..U+DFFF maps to 0xED 0xA0..0xBF...
            if b == 0xED and c1 >= 0xA0:
                return False
            i += 3
            continue

        if b < 0xF5:
            # 4-byte sequence for U+10000..U+10FFFF.
            if i + 3 >= n:
                return False
            c1 = data[i + 1]
            c2 = data[i + 2]
            c3 = data[i + 3]
            if (c1 & 0xC0) != 0x80 or (c2 & 0xC0) != 0x80 or (c3 & 0xC0) != 0x80:
                return False
            # Overlong guard: the lowest 4-byte form is 0xF0 0x90 0x80 0x80.
            if b == 0xF0 and c1 < 0x90:
                return False
            # Out-of-range guard: U+110000+ maps to 0xF4 0x90+.
            if b == 0xF4 and c1 >= 0x90:
                return False
            i += 4
            continue

        # 0xF5..0xFF cannot start a valid UTF-8 sequence.
        return False

    return True


def is_valid_fssutf_ascii(data: bytes | bytearray) -> bool:
    """Return ``True`` if *data* is pure 7-bit ASCII (every byte < 0x80).

    This is a convenience predicate; pure ASCII is a strict subset of FSS-UTF,
    so this is a cheap shortcut for callers who only care about ASCII and want
    to avoid the multi-byte state machine.
    """
    if isinstance(data, (str,)):
        raise TypeError(
            "is_valid_fssutf_ascii expects bytes or bytearray, not str"
        )
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError(
            "is_valid_fssutf_ascii expects bytes or bytearray, got "
            + type(data).__name__
        )
    return all(b < 0x80 for b in data)
