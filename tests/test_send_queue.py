"""Тесты очереди отправки SMS."""

from dataclasses import dataclass

import pytest

from core.models import Contact
from core.send_queue import QueueState, SendEvent, SendEventType, SendQueue, SendQueueSettings


@dataclass(frozen=True)
class _FakeSmsCommandResult:
    request_id: str


def _contacts(count: int) -> list[Contact]:
    return [
        Contact(row=index + 2, phone=f"+7999000000{index}", variable=f"Имя{index}")
        for index in range(count)
    ]


def test_run_sends_messages_and_emits_progress_events():
    sent: list[tuple[str, str]] = []
    events: list[SendEvent] = []
    sleeps: list[float] = []

    def send_func(phone: str, message: str):
        sent.append((phone, message))
        return _FakeSmsCommandResult(request_id=f"req-{len(sent)}")

    queue = SendQueue(
        contacts=_contacts(2),
        template="Привет, {переменная}",
        settings=SendQueueSettings(group_size=10, sms_delay_sec=1, group_delay_sec=5),
        send_func=send_func,
        sleep_func=sleeps.append,
        on_event=events.append,
    )

    queue.run()

    assert sent == [
        ("+79990000000", "Привет, Имя0"),
        ("+79990000001", "Привет, Имя1"),
    ]
    assert sleeps == [1]
    assert queue.state == QueueState.FINISHED
    assert [event.type for event in events] == [
        SendEventType.QUEUED,
        SendEventType.QUEUED,
        SendEventType.SENDING,
        SendEventType.SENT,
        SendEventType.SENDING,
        SendEventType.SENT,
        SendEventType.FINISHED,
    ]
    assert events[3].request_id == "req-1"


def test_run_uses_group_delay_between_groups():
    sleeps: list[float] = []

    queue = SendQueue(
        contacts=_contacts(3),
        template="Hi {переменная}",
        settings=SendQueueSettings(group_size=2, sms_delay_sec=1, group_delay_sec=10),
        send_func=lambda phone, message: _FakeSmsCommandResult(request_id=phone),
        sleep_func=sleeps.append,
    )

    queue.run()

    assert sleeps == [1, 10]


def test_run_emits_failed_event_and_continues_queue():
    calls: list[str] = []
    events: list[SendEvent] = []

    def send_func(phone: str, message: str):
        calls.append(phone)
        if len(calls) == 1:
            raise RuntimeError("adb failed")
        return _FakeSmsCommandResult(request_id="req-ok")

    queue = SendQueue(
        contacts=_contacts(2),
        template="Text",
        settings=SendQueueSettings(group_size=10, sms_delay_sec=0, group_delay_sec=0),
        send_func=send_func,
        on_event=events.append,
    )

    queue.run()

    assert calls == ["+79990000000", "+79990000001"]
    failed_events = [event for event in events if event.type == SendEventType.FAILED]
    sent_events = [event for event in events if event.type == SendEventType.SENT]
    assert failed_events[0].error == "adb failed"
    assert sent_events[0].request_id == "req-ok"
    assert queue.state == QueueState.FINISHED


def test_stop_inside_sleep_prevents_next_send():
    sent: list[str] = []

    def send_func(phone: str, message: str):
        sent.append(phone)
        return _FakeSmsCommandResult(request_id=phone)

    queue = SendQueue(
        contacts=_contacts(2),
        template="Text",
        settings=SendQueueSettings(group_size=10, sms_delay_sec=1, group_delay_sec=0),
        send_func=send_func,
        sleep_func=lambda delay: queue.stop(),
    )

    queue.run()

    assert sent == ["+79990000000"]
    assert queue.state == QueueState.STOPPED


def test_stop_before_run_stops_before_first_send():
    sent: list[str] = []
    queue = SendQueue(
        contacts=_contacts(1),
        template="Text",
        settings=SendQueueSettings(group_size=1, sms_delay_sec=0, group_delay_sec=0),
        send_func=lambda phone, message: sent.append(phone) or _FakeSmsCommandResult("req"),
    )

    queue.stop()
    queue.run()

    assert sent == []
    assert queue.state == QueueState.STOPPED


def test_settings_reject_invalid_group_size():
    with pytest.raises(ValueError, match="group_size"):
        SendQueueSettings(group_size=0, sms_delay_sec=0, group_delay_sec=0)


def test_settings_reject_negative_sms_delay():
    with pytest.raises(ValueError, match="sms_delay_sec"):
        SendQueueSettings(group_size=1, sms_delay_sec=-1, group_delay_sec=0)


def test_settings_reject_negative_group_delay():
    with pytest.raises(ValueError, match="group_delay_sec"):
        SendQueueSettings(group_size=1, sms_delay_sec=0, group_delay_sec=-1)
