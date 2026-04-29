"""Экран выполнения SMS-рассылки."""

from collections.abc import Callable
from dataclasses import dataclass
from threading import Thread
from tkinter import TclError

import customtkinter as ctk

from adb.sms_sender import SmsCommandResult, send_sms
from core.models import Contact
from core.send_queue import QueueState, SendEvent, SendEventType, SendQueue, SendQueueSettings


@dataclass
class SendingStats:
    """Счётчики экрана рассылки."""

    total: int
    sent: int = 0
    failed: int = 0

    @property
    def processed(self) -> int:
        """Количество контактов с финальным результатом на уровне очереди."""
        return self.sent + self.failed


class SendingScreen(ctk.CTkFrame):
    """Экран прогресса, лога и управления очередью отправки."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        contacts: list[Contact],
        template: str,
        settings: SendQueueSettings,
        send_func: Callable[[str, str], SmsCommandResult] = send_sms,
        on_paused: Callable[[], None] | None = None,
        on_resumed: Callable[[], None] | None = None,
        on_stopped: Callable[[], None] | None = None,
        on_finished: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._stats = SendingStats(total=len(contacts))
        self._destroyed = False
        self._on_paused = on_paused
        self._on_resumed = on_resumed
        self._on_stopped = on_stopped
        self._on_finished = on_finished
        self._queue = SendQueue(
            contacts=contacts,
            template=template,
            settings=settings,
            send_func=send_func,
            on_event=self._schedule_event,
        )
        self._thread: Thread | None = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_summary()
        self._build_controls()
        self._build_log()
        self._refresh_stats()
        self._start_queue()

    def destroy(self) -> None:
        """Останавливает очередь при уничтожении экрана."""
        self._destroyed = True
        self._queue.stop()
        super().destroy()

    def update_template(self, template: str) -> None:
        """Обновляет шаблон для ещё не отправленных контактов."""
        self._queue.update_template(template)

    def _build_summary(self) -> None:
        summary = ctk.CTkFrame(self)
        summary.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        summary.grid_columnconfigure(0, weight=1)

        self._status_label = ctk.CTkLabel(
            summary,
            text="Подготовка рассылки",
            anchor="w",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self._status_label.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="ew")

        self._progress = ctk.CTkProgressBar(summary)
        self._progress.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="ew")
        self._progress.set(0)

        self._stats_label = ctk.CTkLabel(summary, text="", anchor="w")
        self._stats_label.grid(row=2, column=0, padx=16, pady=(0, 14), sticky="ew")

    def _build_controls(self) -> None:
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        controls.grid_columnconfigure(0, weight=1)

        self._pause_button = ctk.CTkButton(
            controls,
            text="Пауза",
            command=self._toggle_pause,
            width=140,
        )
        self._pause_button.grid(row=0, column=1, padx=(0, 8))

        self._stop_button = ctk.CTkButton(
            controls,
            text="Стоп",
            command=self._stop_queue,
            width=140,
            fg_color="#8a1f1f",
            hover_color="#6f1919",
        )
        self._stop_button.grid(row=0, column=2)

    def _build_log(self) -> None:
        log_panel = ctk.CTkFrame(self)
        log_panel.grid(row=2, column=0, sticky="nsew")
        log_panel.grid_columnconfigure(0, weight=1)
        log_panel.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(
            log_panel,
            text="Лог отправки",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        title.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")

        self._log_frame = ctk.CTkScrollableFrame(log_panel)
        self._log_frame.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self._log_frame.grid_columnconfigure(0, weight=1)

    def _start_queue(self) -> None:
        self._thread = Thread(target=self._queue.run, daemon=True)
        self._thread.start()

    def _toggle_pause(self) -> None:
        if self._queue.state == QueueState.PAUSED:
            self._queue.resume()
            self._pause_button.configure(text="Пауза")
            self._status_label.configure(text="Рассылка продолжается")
            if self._on_resumed is not None:
                self._on_resumed()
        elif self._queue.state == QueueState.RUNNING:
            self._queue.pause()

    def _stop_queue(self) -> None:
        self._queue.stop()

    def _schedule_event(self, event: SendEvent) -> None:
        if self._destroyed:
            return
        try:
            self.after(0, lambda event=event: self._handle_event(event))
        except TclError:
            self._destroyed = True

    def _handle_event(self, event: SendEvent) -> None:
        if self._destroyed:
            return

        if event.type == SendEventType.QUEUED:
            return
        if event.type == SendEventType.SENDING:
            phone = event.contact.phone if event.contact is not None else ""
            self._status_label.configure(text=f"Отправка: {phone}")
            self._append_log("⏳", event, "отправляется")
            return
        if event.type == SendEventType.SENT:
            self._stats.sent += 1
            self._append_log("✅", event, f"команда принята, request_id={event.request_id}")
            self._refresh_stats()
            return
        if event.type == SendEventType.FAILED:
            self._stats.failed += 1
            self._append_log("❌", event, event.error or "ошибка отправки")
            self._refresh_stats()
            return
        if event.type == SendEventType.PAUSED:
            self._pause_button.configure(text="Продолжить")
            self._stop_button.configure(state="normal")
            self._status_label.configure(text="Пауза: можно изменить шаблон и продолжить")
            if self._on_paused is not None:
                self._on_paused()
            return
        if event.type == SendEventType.STOPPED:
            self._status_label.configure(text="Остановлено. Результат готов к выгрузке")
            self._disable_controls()
            self._refresh_stats()
            if self._on_stopped is not None:
                self._on_stopped()
            return
        if event.type == SendEventType.FINISHED:
            self._status_label.configure(text="Рассылка завершена")
            self._disable_controls()
            self._refresh_stats()
            if self._on_finished is not None:
                self._on_finished()

    def _append_log(self, icon: str, event: SendEvent, details: str) -> None:
        contact_text = ""
        if event.contact is not None:
            contact_text = f"{event.contact.phone} | строка {event.contact.row}"

        row = len(self._log_frame.winfo_children())
        label = ctk.CTkLabel(
            self._log_frame,
            text=f"{icon} {contact_text} | {details}",
            anchor="w",
            justify="left",
            wraplength=760,
        )
        label.grid(row=row, column=0, sticky="ew", padx=6, pady=3)

    def _refresh_stats(self) -> None:
        self._progress.set(calculate_progress(self._stats))
        self._stats_label.configure(text=build_status_summary(self._stats))

    def _disable_controls(self) -> None:
        self._pause_button.configure(state="disabled")
        self._stop_button.configure(state="disabled")


def calculate_progress(stats: SendingStats) -> float:
    """Возвращает прогресс от 0 до 1."""
    if stats.total <= 0:
        return 0
    return stats.processed / stats.total


def build_status_summary(stats: SendingStats) -> str:
    """Форматирует статистику рассылки для UI."""
    return (
        f"Всего: {stats.total} | Обработано: {stats.processed} | "
        f"Успешно: {stats.sent} | Ошибок: {stats.failed}"
    )
