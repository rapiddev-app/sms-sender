"""Тесты helper-функций экрана рассылки."""

from ui.screen_sending import SendingStats, build_status_summary, calculate_progress


def test_sending_stats_processed_returns_sent_plus_failed():
    stats = SendingStats(total=5, sent=2, failed=1)

    assert stats.processed == 3


def test_calculate_progress_returns_processed_fraction():
    stats = SendingStats(total=5, sent=2, failed=1)

    assert calculate_progress(stats) == 0.6


def test_calculate_progress_returns_zero_for_empty_queue():
    assert calculate_progress(SendingStats(total=0)) == 0


def test_build_status_summary_formats_stats():
    stats = SendingStats(total=5, sent=2, failed=1)

    assert build_status_summary(stats) == (
        "Всего: 5 | Обработано: 3 | Успешно: 2 | Ошибок: 1"
    )
