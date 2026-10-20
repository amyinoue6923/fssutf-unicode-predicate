# fssutf-unicode-predicate

A strict validator for byte strings encoded in the Unicode FSS-UTF (UTF-8) scheme. It rejects overlong encodings, lone surrogates, code points above U+10FFFF, and truncated sequences.

```python
from fssutf_unicode_predicate import is_valid_fssutf, is_valid_fssutf_ascii

is_valid_fssutf(b"hello")                  # True
is_valid_fssutf(b"\xc3\xa9")               # True  (U+00E9)
is_valid_fssutf(b"\xc0\x80")               # False (overlong null)
is_valid_fssutf(b"\xed\xa0\x80")           # False (lone surrogate U+D800)
is_valid_fssutf(bytearray(b"\xf0\x9f\x98\x80"))  # True  (U+1F600)
is_valid_fssutf_ascii(b"plain text")       # True
is_valid_fssutf_ascii(b"\x80")             # False
```

## Why this exists

Python's built-in ``bytes.decode('utf-8')`` is lenient by default and can be made more lenient still with error handlers like ``surrogatepass``. Code that must enforce the original FSS-UTF contract — no overlong forms, no surrogate code points, no out-of-range values — needs a dedicated predicate rather than relying on decode-and-catch. This library provides that predicate with no third-party dependencies.

The trade-off: this is a predicate, not a decoder. It returns ``True`` or ``False``; it does not yield the decoded string or report which byte failed. Callers who need the rejection reason can extend the state machine in ``core.py``, but the public contract stays minimal.

## Awkward edge

The validator operates on ``bytes`` and ``bytearray`` only. Passing ``str`` raises ``TypeError``. This is deliberate: FSS-UTF is itself the text-to-bytes transform, so accepting ``str`` would force an implicit choice of some other encoding to produce bytes — exactly the ambiguity the library exists to remove. If you have text and want bytes, encode them yourself first; then validate.

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

