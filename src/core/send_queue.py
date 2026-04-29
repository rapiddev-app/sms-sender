"""Очередь отправки SMS с группами, задержками, паузой и остановкой."""

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from threading import Event, Lock

from adb.sms_sender import SmsCommandResult
from core.message_builder import build_message
from core.models import Contact


class QueueState(Enum):
    """Состояние очереди отправки."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    FINISHED = "finished"


class SendEventType(Enum):
    """Тип события, которое очередь отдаёт GUI-слою."""

    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    PAUSED = "paused"
    STOPPED = "stopped"
    FINISHED = "finished"


@dataclass(frozen=True)
class SendQueueSettings:
    """Настройки пакетной отправки."""

    group_size: int
    sms_delay_sec: float
    group_delay_sec: float

    def __post_init__(self) -> None:
        if self.group_size <= 0:
            raise ValueError("group_size должен быть больше 0")
        if self.sms_delay_sec < 0:
            raise ValueError("sms_delay_sec не может быть отрицательным")
        if self.group_delay_sec < 0:
            raise ValueError("group_delay_sec не может быть отрицательным")


@dataclass(frozen=True)
class SendEvent:
    """Событие прогресса отправки для GUI и отчёта."""

    type: SendEventType
    state: QueueState
    contact: Contact | None = None
    request_id: str | None = None
    message: str = ""
    error: str = ""


SendFunc = Callable[[str, str], SmsCommandResult]
SleepFunc = Callable[[float], None]
EventCallback = Callable[[SendEvent], None]


class SendQueue:
    """Синхронная очередь отправки SMS.

    `run()` блокирует текущий поток. GUI должен запускать очередь в отдельном
    `threading.Thread`, чтобы интерфейс оставался отзывчивым.
    """

    def __init__(
        self,
        contacts: list[Contact],
        template: str,
        settings: SendQueueSettings,
        send_func: SendFunc,
        sleep_func: SleepFunc = time.sleep,
        on_event: EventCallback | None = None,
    ) -> None:
        self._contacts = list(contacts)
        self._template = template
        self._settings = settings
        self._send_func = send_func
        self._sleep_func = sleep_func
        self._on_event = on_event
        self._pause_event = Event()
        self._stop_event = Event()
        self._lock = Lock()
        self._state = QueueState.IDLE
        self._pause_event.set()

    @property
    def state(self) -> QueueState:
        """Возвращает текущее состояние очереди."""
        with self._lock:
            return self._state

    def run(self) -> None:
        """Запускает отправку всех контактов в текущем потоке."""
        if self.state in {QueueState.RUNNING, QueueState.PAUSED}:
            raise RuntimeError("Очередь уже запущена")
        if self.state == QueueState.STOPPED:
            return

        self._stop_event.clear()
        self._pause_event.set()
        self._set_state(QueueState.RUNNING)

        for contact in self._contacts:
            message = build_message(self._template, contact.variable)
            self._emit(SendEventType.QUEUED, contact=contact, message=message)

        for index, contact in enumerate(self._contacts):
            if self._wait_if_paused_or_stopped():
                return

            message = build_message(self._template, contact.variable)
            self._emit(SendEventType.SENDING, contact=contact, message=message)

            try:
                result = self._send_func(contact.phone, message)
            except Exception as exc:  # noqa: BLE001 - ошибка должна попасть в событие, не роняя очередь.
                self._emit(
                    SendEventType.FAILED,
                    contact=contact,
                    message=message,
                    error=str(exc),
                )
            else:
                self._emit(
                    SendEventType.SENT,
                    contact=contact,
                    request_id=result.request_id,
                    message=message,
                )

            if self._delay_after_contact(index):
                return

        self._set_state(QueueState.FINISHED)
        self._emit(SendEventType.FINISHED)

    def pause(self) -> None:
        """Ставит очередь на паузу перед следующей отправкой или задержкой."""
        if self.state != QueueState.RUNNING:
            return
        self._pause_event.clear()
        self._set_state(QueueState.PAUSED)
        self._emit(SendEventType.PAUSED)

    def resume(self) -> None:
        """Возобновляет очередь после паузы."""
        if self.state != QueueState.PAUSED:
            return
        self._set_state(QueueState.RUNNING)
        self._pause_event.set()

    def stop(self) -> None:
        """Останавливает очередь перед следующей отправкой или задержкой."""
        if self.state in {QueueState.STOPPED, QueueState.FINISHED}:
            return
        self._stop_event.set()
        self._pause_event.set()
        self._set_state(QueueState.STOPPED)
        self._emit(SendEventType.STOPPED)

    def _delay_after_contact(self, index: int) -> bool:
        next_index = index + 1
        if next_index >= len(self._contacts):
            return False

        if next_index % self._settings.group_size == 0:
            delay = self._settings.group_delay_sec
        else:
            delay = self._settings.sms_delay_sec

        if delay > 0:
            return self._interruptible_sleep(delay)
        return self._wait_if_paused_or_stopped()

    def _interruptible_sleep(self, delay_sec: float) -> bool:
        if self._wait_if_paused_or_stopped():
            return True

        self._sleep_func(delay_sec)
        return self._wait_if_paused_or_stopped()

    def _wait_if_paused_or_stopped(self) -> bool:
        while not self._pause_event.is_set():
            if self._stop_event.is_set():
                self._set_state(QueueState.STOPPED)
                return True
            self._pause_event.wait(timeout=0.1)

        if self._stop_event.is_set():
            self._set_state(QueueState.STOPPED)
            return True
        return False

    def _set_state(self, state: QueueState) -> None:
        with self._lock:
            self._state = state

    def _emit(
        self,
        event_type: SendEventType,
        *,
        contact: Contact | None = None,
        request_id: str | None = None,
        message: str = "",
        error: str = "",
    ) -> None:
        if self._on_event is None:
            return
        self._on_event(
            SendEvent(
                type=event_type,
                state=self.state,
                contact=contact,
                request_id=request_id,
                message=message,
                error=error,
            )
        )
