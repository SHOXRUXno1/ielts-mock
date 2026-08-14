"""Unit tests for format_test_label."""

from app.utils.labels import format_test_label


class TestFormatTestLabel:
    def test_always_appends_number(self):
        assert format_test_label("Ielts 18", 1) == "Ielts 18 — Test 1"
        assert format_test_label("Ielts 18", 2) == "Ielts 18 — Test 2"

    def test_none_defaults_to_one(self):
        assert format_test_label("Ielts 11", None) == "Ielts 11 — Test 1"

    def test_zero_defaults_to_one(self):
        assert format_test_label("Ielts 11", 0) == "Ielts 11 — Test 1"

    def test_skips_when_title_already_has_test_suffix(self):
        assert (
            format_test_label("Cambridge IELTS 9 – Test 4", 4)
            == "Cambridge IELTS 9 – Test 4"
        )
        assert (
            format_test_label("Cambridge IELTS 9 — Test 4", 4)
            == "Cambridge IELTS 9 — Test 4"
        )
        assert format_test_label("IELTS 11 - Test 2", 2) == "IELTS 11 - Test 2"
