from __future__ import annotations

import os
import tempfile
from pathlib import Path

from nlp.versions import normalize_version, is_valid_version, _build_number


class TestNormalizeVersion:
    def test_with_b_prefix(self):
        assert normalize_version("b9145") == "b9145"

    def test_without_b_prefix(self):
        assert normalize_version("9145") == "b9145"

    def test_latest_unchanged(self):
        assert normalize_version("latest") == "latest"

    def test_already_prefixed(self):
        assert normalize_version("b1") == "b1"

    def test_zero(self):
        assert normalize_version("0") == "b0"

    def test_multi_digit(self):
        assert normalize_version("12345") == "b12345"


class TestIsValidVersion:
    def test_valid_with_prefix(self):
        assert is_valid_version("b9145") is True

    def test_valid_without_prefix(self):
        assert is_valid_version("9145") is True

    def test_invalid_letters(self):
        assert is_valid_version("babc") is False

    def test_invalid_latest(self):
        assert is_valid_version("latest") is False

    def test_invalid_empty(self):
        assert is_valid_version("") is False

    def test_valid_single_digit(self):
        assert is_valid_version("b1") is True

    def test_valid_zero(self):
        assert is_valid_version("0") is True


class TestBuildNumber:
    def test_extracts_number(self):
        assert _build_number("b9145") == 9145

    def test_single_digit(self):
        assert _build_number("b1") == 1

    def test_zero(self):
        assert _build_number("b0") == 0

    def test_no_match_returns_zero(self):
        assert _build_number("abc") == 0