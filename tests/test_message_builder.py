"""Тесты сборки текста SMS и подсчёта метрик."""

from core.message_builder import (
    ENCODING_GSM7,
    ENCODING_UCS2,
    GSM7_MULTIPART_LIMIT,
    GSM7_SINGLE_LIMIT,
    PLACEHOLDER,
    UCS2_MULTIPART_LIMIT,
    UCS2_SINGLE_LIMIT,
    build_message,
    count_sms,
)


class TestBuildMessage:
    def test_build_message_inserts_variable_correctly(self):
        result = build_message(f"Привет, {PLACEHOLDER}!", "Иван")
        assert result == "Привет, Иван!"

    def test_build_message_replaces_all_occurrences(self):
        template = f"{PLACEHOLDER} и ещё раз {PLACEHOLDER}"
        assert build_message(template, "Анна") == "Анна и ещё раз Анна"

    def test_build_message_returns_template_unchanged_without_placeholder(self):
        template = "Текст без плейсхолдера"
        assert build_message(template, "Иван") == template

    def test_build_message_handles_empty_variable(self):
        assert build_message(f"Здравствуйте, {PLACEHOLDER}", "") == "Здравствуйте, "

    def test_build_message_keeps_unrelated_braces(self):
        template = f"Скидка {{до 50%}} для {PLACEHOLDER}"
        assert build_message(template, "Пётр") == "Скидка {до 50%} для Пётр"

    def test_build_message_handles_empty_template(self):
        assert build_message("", "Иван") == ""


class TestCountSmsAscii:
    def test_count_sms_ascii_short_returns_single_segment_gsm7(self):
        stats = count_sms("Hello world")
        assert stats.encoding == ENCODING_GSM7
        assert stats.length == 11
        assert stats.segments == 1
        assert stats.per_segment_limit == GSM7_SINGLE_LIMIT

    def test_count_sms_ascii_at_single_limit_is_one_segment(self):
        text = "a" * GSM7_SINGLE_LIMIT
        stats = count_sms(text)
        assert stats.segments == 1
        assert stats.per_segment_limit == GSM7_SINGLE_LIMIT

    def test_count_sms_ascii_above_single_limit_switches_to_multipart(self):
        text = "a" * (GSM7_SINGLE_LIMIT + 1)
        stats = count_sms(text)
        assert stats.encoding == ENCODING_GSM7
        assert stats.segments == 2
        assert stats.per_segment_limit == GSM7_MULTIPART_LIMIT

    def test_count_sms_ascii_three_segments(self):
        text = "a" * (GSM7_MULTIPART_LIMIT * 2 + 1)
        stats = count_sms(text)
        assert stats.segments == 3


class TestCountSmsCyrillic:
    def test_count_sms_cyrillic_short_returns_single_segment_ucs2(self):
        stats = count_sms("Привет")
        assert stats.encoding == ENCODING_UCS2
        assert stats.length == 6
        assert stats.segments == 1
        assert stats.per_segment_limit == UCS2_SINGLE_LIMIT

    def test_count_sms_cyrillic_at_single_limit_is_one_segment(self):
        text = "я" * UCS2_SINGLE_LIMIT
        stats = count_sms(text)
        assert stats.segments == 1
        assert stats.per_segment_limit == UCS2_SINGLE_LIMIT

    def test_count_sms_cyrillic_above_single_limit_switches_to_multipart(self):
        text = "я" * (UCS2_SINGLE_LIMIT + 1)
        stats = count_sms(text)
        assert stats.encoding == ENCODING_UCS2
        assert stats.segments == 2
        assert stats.per_segment_limit == UCS2_MULTIPART_LIMIT

    def test_count_sms_cyrillic_three_segments(self):
        text = "я" * (UCS2_MULTIPART_LIMIT * 2 + 1)
        stats = count_sms(text)
        assert stats.segments == 3


class TestCountSmsEdgeCases:
    def test_count_sms_empty_string_is_single_segment_gsm7(self):
        stats = count_sms("")
        assert stats.length == 0
        assert stats.encoding == ENCODING_GSM7
        assert stats.segments == 1
        assert stats.per_segment_limit == GSM7_SINGLE_LIMIT

    def test_count_sms_mixed_ascii_with_one_cyrillic_is_ucs2(self):
        stats = count_sms("Hello, мир")
        assert stats.encoding == ENCODING_UCS2
        assert stats.per_segment_limit == UCS2_SINGLE_LIMIT

    def test_count_sms_emoji_is_ucs2(self):
        stats = count_sms("Hi 👋")
        assert stats.encoding == ENCODING_UCS2
