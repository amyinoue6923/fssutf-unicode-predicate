"""Tests for fssutf_unicode_predicate.core.

Every test here exercises behaviour the implementation actually claims to
support. No invented edge cases.
"""

import unittest

from fssutf_unicode_predicate.core import (
    is_valid_fssutf,
    is_valid_fssutf_ascii,
)


class TestValidFssutf(unittest.TestCase):
    def test_empty_bytes_is_valid(self):
        self.assertTrue(is_valid_fssutf(b""))

    def test_empty_bytearray_is_valid(self):
        self.assertTrue(is_valid_fssutf(bytearray()))

    def test_pure_ascii_is_valid(self):
        self.assertTrue(is_valid_fssutf(b"Hello, world!"))

    def test_single_two_byte_sequence(self):
        # U+00E9 (é) encoded as 0xC3 0xA9.
        self.assertTrue(is_valid_fssutf(b"\xc3\xa9"))

    def test_single_three_byte_sequence(self):
        # U+20AC (€) encoded as 0xE2 0x82 0xAC.
        self.assertTrue(is_valid_fssutf(b"\xe2\x82\xac"))

    def test_single_four_byte_sequence(self):
        # U+1F600 encoded as 0xF0 0x9F 0x98 0x80.
        self.assertTrue(is_valid_fssutf(b"\xf0\x9f\x98\x80"))

    def test_mixed_valid_string(self):
        self.assertTrue(is_valid_fssutf(b"caf\xc3\xa9 \xe2\x82\xac \xf0\x9f\x98\x80"))

    def test_max_valid_code_point(self):
        # U+10FFFF encoded as 0xF4 0x8F 0xBF 0xBF.
        self.assertTrue(is_valid_fssutf(b"\xf4\x8f\xbf\xbf"))


class TestInvalidFssutf(unittest.TestCase):
    def test_stray_continuation_byte(self):
        self.assertFalse(is_valid_fssutf(b"\x80"))

    def test_lone_high_continuation_in_text(self):
        self.assertFalse(is_valid_fssutf(b"abc\x80def"))

    def test_overlong_two_byte_null(self):
        # U+0000 must not be encoded as 0xC0 0x80.
        self.assertFalse(is_valid_fssutf(b"\xc0\x80"))

    def test_overlong_two_byte_low(self):
        # 0xC1 0xBF decodes to U+007F, which must be ASCII.
        self.assertFalse(is_valid_fssutf(b"\xc1\xbf"))

    def test_overlong_three_byte_null(self):
        # 0xE0 0x80 0x80 decodes to U+0000.
        self.assertFalse(is_valid_fssutf(b"\xe0\x80\x80"))

    def test_overlong_three_byte_just_below_minimum(self):
        # 0xE0 0x9F 0xBF decodes to U+07FF, which should be a 2-byte form.
        self.assertFalse(is_valid_fssutf(b"\xe0\x9f\xbf"))

    def test_surrogate_high(self):
        # U+D800 encoded as 0xED 0xA0 0x80.
        self.assertFalse(is_valid_fssutf(b"\xed\xa0\x80"))

    def test_surrogate_low(self):
        # U+DFFF encoded as 0xED 0xBF 0xBF.
        self.assertFalse(is_valid_fssutf(b"\xed\xbf\xbf"))

    def test_code_point_above_max(self):
        # U+110000 encoded as 0xF4 0x90 0x80 0x80.
        self.assertFalse(is_valid_fssutf(b"\xf4\x90\x80\x80"))

    def test_overlong_four_byte(self):
        # 0xF0 0x80 0x80 0x80 decodes to U+0000.
        self.assertFalse(is_valid_fssutf(b"\xf0\x80\x80\x80"))

    def test_truncated_two_byte(self):
        self.assertFalse(is_valid_fssutf(b"\xc3"))

    def test_truncated_three_byte_at_end(self):
        self.assertFalse(is_valid_fssutf(b"\xe2\x82"))

    def test_truncated_four_byte_at_end(self):
        self.assertFalse(is_valid_fssutf(b"\xf0\x9f\x98"))

    def test_invalid_continuation_in_two_byte(self):
        self.assertFalse(is_valid_fssutf(b"\xc3\x00"))

    def test_invalid_continuation_in_three_byte(self):
        self.assertFalse(is_valid_fssutf(b"\xe2\x82\x00"))

    def test_invalid_continuation_in_four_byte(self):
        self.assertFalse(is_valid_fssutf(b"\xf0\x9f\x98\x00"))

    def test_trailing_leading_byte_in_four_byte(self):
        # Only one continuation byte where two are required.
        self.assertFalse(is_valid_fssutf(b"\xf0\x9f\x98"))

    def test_stray_ff_byte(self):
        self.assertFalse(is_valid_fssutf(b"\xff"))

    def test_stray_f5_byte(self):
        self.assertFalse(is_valid_fssutf(b"\xf5"))


class TestTypeErrors(unittest.TestCase):
    def test_str_raises_type_error(self):
        with self.assertRaises(TypeError):
            is_valid_fssutf("hello")

    def test_int_raises_type_error(self):
        with self.assertRaises(TypeError):
            is_valid_fssutf(42)

    def test_str_raises_type_error_ascii(self):
        with self.assertRaises(TypeError):
            is_valid_fssutf_ascii("hello")

    def test_int_raises_type_error_ascii(self):
        with self.assertRaises(TypeError):
            is_valid_fssutf_ascii(42)


class TestAsciiPredicate(unittest.TestCase):
    def test_empty_ascii(self):
        self.assertTrue(is_valid_fssutf_ascii(b""))

    def test_pure_ascii(self):
        self.assertTrue(is_valid_fssutf_ascii(b"abcdefg1234567!@#$"))

    def test_byte_with_high_bit(self):
        self.assertFalse(is_valid_fssutf_ascii(b"\x80"))

    def test_bytearray_ascii(self):
        self.assertTrue(is_valid_fssutf_ascii(bytearray(b"hello")))

    def test_mixed_with_two_byte(self):
        self.assertFalse(is_valid_fssutf_ascii(b"caf\xc3\xa9"))


if __name__ == "__main__":
    unittest.main()
