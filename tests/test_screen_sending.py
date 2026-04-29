"""Тесты helper-функций экрана рассылки."""

from pathlib import Path

from core.models import Contact
from core.report_exporter import STATUS_FAILED, STATUS_PENDING, STATUS_SENT
from core.send_queue import QueueState, SendEvent, SendEventType
from ui.screen_sending import (
    SendingStats,
    build_default_report_filename,
    build_initial_statuses,
    build_status_summary,
    calculate_progress,
    update_status_from_event,
)


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


def test_build_initial_statuses_marks_contacts_as_pending():
    contacts = [
        Contact(row=2, phone="+79990000001", variable="Анна"),
        Contact(row=4, phone="+79990000002", variable="Иван"),
    ]

    assert build_initial_statuses(contacts) == {
        2: STATUS_PENDING,
        4: STATUS_PENDING,
    }


def test_update_status_from_event_updates_contact_row():
    statuses_by_row = {2: STATUS_PENDING}
    event = SendEvent(
        type=SendEventType.SENT,
        state=QueueState.RUNNING,
        contact=Contact(row=2, phone="+79990000001", variable="Анна"),
    )

    update_status_from_event(statuses_by_row, event, STATUS_SENT)

    assert statuses_by_row == {2: STATUS_SENT}


def test_update_status_from_event_ignores_event_without_contact():
    statuses_by_row = {2: STATUS_PENDING}
    event = SendEvent(type=SendEventType.FAILED, state=QueueState.RUNNING)

    update_status_from_event(statuses_by_row, event, STATUS_FAILED)

    assert statuses_by_row == {2: STATUS_PENDING}


def test_build_default_report_filename_uses_source_stem():
    assert build_default_report_filename(Path("contacts.xlsx")) == "contacts_report.xlsx"
