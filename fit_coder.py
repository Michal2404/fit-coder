#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass

try:
    import tkinter as tk
    from tkinter import font as tkfont
    from tkinter import ttk
except Exception:
    tk = None
    tkfont = None
    ttk = None

LINUX_OGA_SOUNDS = (
    "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga",
    "/usr/share/sounds/freedesktop/stereo/complete.oga",
    "/usr/share/sounds/freedesktop/stereo/bell.oga",
)
LINUX_WAV_SOUNDS = (
    "/usr/share/sounds/alsa/Front_Center.wav",
    "/usr/share/sounds/alsa/Noise.wav",
)


@dataclass
class ExerciseStats:
    name: str
    total_reps: int = 0
    rounds_completed: int = 0


def format_duration(total_seconds: int) -> str:
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def _run_alarm_command(command: list[str]) -> bool:
    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
            check=False,
        )
        return completed.returncode == 0
    except Exception:
        return False


def _play_windows_alarm_once() -> bool:
    try:
        import winsound
    except Exception:
        return False

    try:
        winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        return True
    except RuntimeError:
        pass

    try:
        winsound.Beep(1300, 350)
        return True
    except RuntimeError:
        return False


def _play_linux_alarm_once() -> bool:
    if _run_alarm_command(["canberra-gtk-play", "-i", "alarm-clock-elapsed", "-d", "fitcoder"]):
        return True
    if _run_alarm_command(["canberra-gtk-play", "-i", "bell", "-d", "fitcoder"]):
        return True

    paplay_path = shutil.which("paplay")
    if paplay_path:
        for sound_path in LINUX_OGA_SOUNDS:
            if os.path.exists(sound_path) and _run_alarm_command([paplay_path, sound_path]):
                return True

    aplay_path = shutil.which("aplay")
    if aplay_path:
        for sound_path in LINUX_WAV_SOUNDS:
            if os.path.exists(sound_path) and _run_alarm_command([aplay_path, sound_path]):
                return True

    return False


def _play_system_alarm_once() -> bool:
    if sys.platform.startswith("win"):
        return _play_windows_alarm_once()
    return _play_linux_alarm_once()


def ring_alarm(
    repeats: int | None = 2, stop_event: threading.Event | None = None
) -> None:
    played = 0
    while True:
        if stop_event is not None and stop_event.is_set():
            return
        if repeats is not None and played >= repeats:
            return

        if not _play_system_alarm_once():
            print("\a", end="", flush=True)
        played += 1

        if stop_event is not None:
            if stop_event.wait(0.35):
                return
        else:
            time.sleep(0.35)


def ask_positive_int(prompt: str) -> int:
    while True:
        raw_value = input(prompt).strip()
        try:
            value = int(raw_value)
            if value <= 0:
                print("Please enter a number greater than 0.")
                continue
            return value
        except ValueError:
            print("Please enter a valid whole number.")


def ask_non_negative_int(prompt: str) -> int:
    while True:
        raw_value = input(prompt).strip()
        try:
            value = int(raw_value)
            if value < 0:
                print("Please enter 0 or a positive number.")
                continue
            return value
        except ValueError:
            print("Please enter a valid whole number.")


def ask_exercise_name(index: int) -> str:
    while True:
        name = input(f"Give the name of exercise {index}: ").strip()
        if not name:
            print("Exercise name cannot be empty.")
            continue
        return name


def print_stats(exercises: list[ExerciseStats]) -> None:
    total_reps = sum(ex.total_reps for ex in exercises)
    total_rounds = sum(ex.rounds_completed for ex in exercises)
    print("\nSession stats")
    print(f"- Total reps: {total_reps}")
    print(f"- Total completed rounds: {total_rounds}")
    print("- Per exercise:")
    for ex in exercises:
        print(f"  {ex.name}: {ex.total_reps} reps across {ex.rounds_completed} rounds")
    print()


def run_cli_fallback() -> None:
    print("Could not open widget. Running CLI fallback mode.")
    exercise_count = ask_positive_int(
        "How many exercises do you want to include into the routine? "
    )
    break_minutes = ask_positive_int(
        "How long should the break be between exercises? (mins) "
    )
    exercises = [ExerciseStats(name=ask_exercise_name(i + 1)) for i in range(exercise_count)]

    break_seconds = break_minutes * 60
    current_index = 0
    print("Timer started. Press Ctrl+C to stop.\n")

    try:
        while True:
            exercise = exercises[current_index]
            for remaining in range(break_seconds, 0, -1):
                timer = format_duration(remaining)
                print(
                    f"\rBreak time. Next: {exercise.name} in {timer}. Press Ctrl+C to stop.",
                    end="",
                    flush=True,
                )
                time.sleep(1)

            print("\rBreak over. " + " " * 70)
            ring_alarm(repeats=2)
            print(f"\nTime to do: {exercise.name}")
            reps = ask_non_negative_int("How many reps did you do? ")
            exercise.total_reps += reps
            exercise.rounds_completed += 1
            print_stats(exercises)
            current_index = (current_index + 1) % len(exercises)
    except KeyboardInterrupt:
        print("\n\nStopping fit coder...")
        print_stats(exercises)
        print("Goodbye.")


class FitCoderWidgetApp:
    def __init__(self, root: "tk.Tk") -> None:
        if tk is None or ttk is None or tkfont is None:
            raise RuntimeError("tkinter is not available")

        self.root = root
        self.palette = {
            "bg": "#f2f5fa",
            "panel": "#ffffff",
            "text": "#1f2937",
            "subtle": "#5b667a",
            "accent": "#0f766e",
            "alarm": "#dc2626",
            "track": "#dce3ef",
            "error": "#b91c1c",
        }

        self.exercise_count_var = tk.StringVar(value="3")
        self.break_minutes_var = tk.StringVar(value="15")
        self.status_var = tk.StringVar(value="Configure routine and click Start session.")
        self.timer_var = tk.StringVar(value="00:00")
        self.next_exercise_var = tk.StringVar(value="-")
        self.reps_input_var = tk.StringVar(value="")
        self.total_reps_var = tk.StringVar(value="0")
        self.total_rounds_var = tk.StringVar(value="0")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.pin_var = tk.BooleanVar(value=True)

        self.exercise_name_vars: list["tk.StringVar"] = []
        self.exercise_entry_widgets: list["tk.Entry"] = []
        self.setup_widgets: list["tk.Widget"] = []

        self.exercises: list[ExerciseStats] = []
        self.break_seconds = 0
        self.remaining_seconds = 0
        self.current_index = 0
        self.session_active = False
        self.timer_running = False
        self.waiting_for_reps = False
        self.timer_job: str | None = None

        self.compact_mode = False
        self.compact_waiting_state = False
        self.expanded_size = (430, 650)
        self.compact_size = (280, 145)

        self.timer_label: "tk.Label" | None = None
        self.timer_font: "tkfont.Font" | None = None
        self.status_label: "tk.Label" | None = None
        self.stats_text: "tk.Text" | None = None
        self.start_pause_button: "tk.Button" | None = None
        self.skip_button: "tk.Button" | None = None
        self.log_reps_button: "tk.Button" | None = None
        self.reps_entry: "tk.Entry" | None = None
        self.exercise_fields_frame: "tk.Frame" | None = None
        self.header_frame: "tk.Frame" | None = None
        self.setup_card: "tk.Frame" | None = None
        self.live_card: "tk.Frame" | None = None
        self.stats_card: "tk.Frame" | None = None
        self.next_row: "tk.Frame" | None = None
        self.reps_row: "tk.Frame" | None = None
        self.control_row: "tk.Frame" | None = None
        self.view_stats_button: "tk.Button" | None = None
        self.quick_pause_button: "tk.Button" | None = None
        self.stats_popup: "tk.Toplevel | None" = None
        self.stats_popup_text: "tk.Text | None" = None
        self.alarm_active = False
        self.alarm_stop_event = threading.Event()
        self.alarm_thread: threading.Thread | None = None

        self._build_ui()
        self._rebuild_exercise_fields()
        self._refresh_stats_view()
        self._apply_layout_mode(force=True)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        assert ttk is not None
        assert tkfont is not None
        assert tk is not None

        style = ttk.Style(self.root)
        for theme_name in ("clam", "alt", "default"):
            if theme_name in style.theme_names():
                style.theme_use(theme_name)
                break
        style.configure(
            "Fit.Horizontal.TProgressbar",
            troughcolor=self.palette["track"],
            background=self.palette["accent"],
            bordercolor=self.palette["track"],
            lightcolor=self.palette["accent"],
            darkcolor=self.palette["accent"],
            thickness=11,
        )

        self.root.title("FitCoder")
        self.root.geometry("430x650+60+50")
        self.root.minsize(340, 500)
        self.root.configure(bg=self.palette["bg"])
        self.root.attributes("-topmost", True)

        container = tk.Frame(self.root, bg=self.palette["bg"], padx=12, pady=12)
        container.pack(fill="both", expand=True)

        self.header_frame = tk.Frame(container, bg=self.palette["bg"])
        self.header_frame.pack(fill="x")

        title = tk.Label(
            self.header_frame,
            text="FITCODER",
            font=("Helvetica", 11, "bold"),
            fg=self.palette["subtle"],
            bg=self.palette["bg"],
        )
        title.pack(side="left")

        controls = tk.Frame(self.header_frame, bg=self.palette["bg"])
        controls.pack(side="right")

        pin_button = tk.Checkbutton(
            controls,
            text="Pin",
            variable=self.pin_var,
            command=self._toggle_pin,
            font=("Helvetica", 9),
            bg=self.palette["bg"],
            fg=self.palette["subtle"],
            activebackground=self.palette["bg"],
            activeforeground=self.palette["text"],
            selectcolor=self.palette["bg"],
            highlightthickness=0,
            bd=0,
        )
        pin_button.pack(side="left", padx=(0, 6))

        self.setup_card = tk.Frame(
            container,
            bg=self.palette["panel"],
            highlightbackground="#d8dfec",
            highlightthickness=1,
            padx=10,
            pady=10,
        )
        self.setup_card.pack(fill="x", pady=(10, 8))

        setup_title = tk.Label(
            self.setup_card,
            text="ROUTINE SETUP",
            font=("Helvetica", 9, "bold"),
            fg=self.palette["subtle"],
            bg=self.palette["panel"],
        )
        setup_title.pack(anchor="w")

        setup_top_row = tk.Frame(self.setup_card, bg=self.palette["panel"])
        setup_top_row.pack(fill="x", pady=(6, 6))

        tk.Label(
            setup_top_row,
            text="Exercises",
            bg=self.palette["panel"],
            fg=self.palette["text"],
            font=("Helvetica", 10),
        ).grid(row=0, column=0, sticky="w")
        count_spin = tk.Spinbox(
            setup_top_row,
            from_=1,
            to=20,
            textvariable=self.exercise_count_var,
            width=4,
            font=("Helvetica", 10),
            command=self._rebuild_exercise_fields,
        )
        count_spin.grid(row=0, column=1, padx=(8, 16), sticky="w")

        tk.Label(
            setup_top_row,
            text="Break (min)",
            bg=self.palette["panel"],
            fg=self.palette["text"],
            font=("Helvetica", 10),
        ).grid(row=0, column=2, sticky="w")
        break_spin = tk.Spinbox(
            setup_top_row,
            from_=1,
            to=180,
            textvariable=self.break_minutes_var,
            width=5,
            font=("Helvetica", 10),
        )
        break_spin.grid(row=0, column=3, padx=(8, 10), sticky="w")

        build_fields_button = tk.Button(
            setup_top_row,
            text="Build",
            command=self._rebuild_exercise_fields,
            font=("Helvetica", 9, "bold"),
            bg="#e8eef9",
            fg=self.palette["subtle"],
            relief="flat",
            bd=0,
            padx=8,
        )
        build_fields_button.grid(row=0, column=4, sticky="e")

        self.exercise_fields_frame = tk.Frame(self.setup_card, bg=self.palette["panel"])
        self.exercise_fields_frame.pack(fill="x")

        self.start_session_button = tk.Button(
            self.setup_card,
            text="Start Session",
            command=self._start_session,
            font=("Helvetica", 10, "bold"),
            bg=self.palette["accent"],
            fg="#ffffff",
            activebackground="#0c625c",
            activeforeground="#ffffff",
            relief="flat",
            padx=10,
            pady=4,
            bd=0,
        )
        self.start_session_button.pack(anchor="e", pady=(8, 0))

        self.setup_widgets = [count_spin, break_spin, build_fields_button, self.start_session_button]

        self.live_card = tk.Frame(
            container,
            bg=self.palette["panel"],
            highlightbackground="#d8dfec",
            highlightthickness=1,
            padx=10,
            pady=10,
        )
        self.live_card.pack(fill="x", pady=(0, 8))

        self.timer_font = tkfont.Font(family="Helvetica", size=44, weight="bold")
        self.timer_label = tk.Label(
            self.live_card,
            textvariable=self.timer_var,
            font=self.timer_font,
            fg=self.palette["accent"],
            bg=self.palette["panel"],
        )
        self.timer_label.pack(anchor="w")

        self.status_label = tk.Label(
            self.live_card,
            textvariable=self.status_var,
            font=("Helvetica", 10),
            fg=self.palette["subtle"],
            bg=self.palette["panel"],
            justify="left",
            anchor="w",
            wraplength=390,
        )
        self.status_label.pack(fill="x", pady=(0, 6))

        progress = ttk.Progressbar(
            self.live_card,
            style="Fit.Horizontal.TProgressbar",
            orient="horizontal",
            mode="determinate",
            maximum=100,
            variable=self.progress_var,
        )
        progress.pack(fill="x", pady=(0, 8))

        self.next_row = tk.Frame(self.live_card, bg=self.palette["panel"])
        self.next_row.pack(fill="x")
        tk.Label(
            self.next_row,
            text="Next:",
            font=("Helvetica", 10, "bold"),
            fg=self.palette["subtle"],
            bg=self.palette["panel"],
        ).pack(side="left")
        tk.Label(
            self.next_row,
            textvariable=self.next_exercise_var,
            font=("Helvetica", 10),
            fg=self.palette["text"],
            bg=self.palette["panel"],
        ).pack(side="left", padx=(6, 0))
        self.quick_pause_button = tk.Button(
            self.next_row,
            text="Pause",
            command=self._toggle_pause,
            font=("Helvetica", 8, "bold"),
            bg="#f3f4f6",
            fg=self.palette["text"],
            activebackground="#e5e7eb",
            relief="flat",
            bd=0,
            padx=6,
            pady=1,
            state="disabled",
        )
        self.quick_pause_button.pack(side="right", padx=(0, 4))
        self.view_stats_button = tk.Button(
            self.next_row,
            text="View stats",
            command=self._open_stats_popup,
            font=("Helvetica", 8, "bold"),
            bg="#e8eef9",
            fg=self.palette["subtle"],
            activebackground="#dbe8ff",
            relief="flat",
            bd=0,
            padx=6,
            pady=1,
        )
        self.view_stats_button.pack(side="right")

        self.reps_row = tk.Frame(self.live_card, bg=self.palette["panel"])
        self.reps_row.pack(fill="x", pady=(9, 4))
        tk.Label(
            self.reps_row,
            text="Reps done",
            font=("Helvetica", 10),
            fg=self.palette["text"],
            bg=self.palette["panel"],
        ).pack(side="left")
        self.reps_entry = tk.Entry(
            self.reps_row,
            textvariable=self.reps_input_var,
            width=8,
            font=("Helvetica", 10),
            state="disabled",
        )
        self.reps_entry.pack(side="left", padx=(8, 8))
        self.log_reps_button = tk.Button(
            self.reps_row,
            text="Log reps",
            command=self._log_reps,
            font=("Helvetica", 9, "bold"),
            bg="#ecfeff",
            fg=self.palette["subtle"],
            activebackground="#d7fbff",
            relief="flat",
            bd=0,
            padx=9,
            state="disabled",
        )
        self.log_reps_button.pack(side="left")

        self.control_row = tk.Frame(self.live_card, bg=self.palette["panel"])
        self.control_row.pack(fill="x", pady=(5, 0))
        self.start_pause_button = tk.Button(
            self.control_row,
            text="Pause",
            command=self._toggle_pause,
            font=("Helvetica", 9, "bold"),
            bg="#f3f4f6",
            fg=self.palette["text"],
            relief="flat",
            bd=0,
            padx=9,
            state="disabled",
        )
        self.start_pause_button.pack(side="left")
        self.skip_button = tk.Button(
            self.control_row,
            text="Skip break",
            command=self._skip_break,
            font=("Helvetica", 9, "bold"),
            bg="#fef3c7",
            fg="#7c2d12",
            relief="flat",
            bd=0,
            padx=9,
            state="disabled",
        )
        self.skip_button.pack(side="left", padx=(8, 0))
        new_session_button = tk.Button(
            self.control_row,
            text="New session",
            command=self._new_session,
            font=("Helvetica", 9, "bold"),
            bg="#fee2e2",
            fg="#7f1d1d",
            relief="flat",
            bd=0,
            padx=9,
        )
        new_session_button.pack(side="right")

        self.stats_card = tk.Frame(
            container,
            bg=self.palette["panel"],
            highlightbackground="#d8dfec",
            highlightthickness=1,
            padx=10,
            pady=10,
        )
        self.stats_card.pack(fill="both", expand=True)

        stats_title = tk.Label(
            self.stats_card,
            text="SESSION STATS",
            font=("Helvetica", 9, "bold"),
            fg=self.palette["subtle"],
            bg=self.palette["panel"],
        )
        stats_title.pack(anchor="w")

        self.stats_text = tk.Text(
            self.stats_card,
            height=9,
            font=("Helvetica", 10),
            bg=self.palette["panel"],
            fg=self.palette["text"],
            relief="flat",
            highlightthickness=0,
            padx=1,
            pady=2,
        )
        self.stats_text.pack(fill="both", expand=True, pady=(4, 0))
        self.stats_text.config(state="disabled")

        self.root.bind("<Configure>", self._on_resize)
        self.root.bind("<Return>", self._on_enter_pressed)
        self.root.bind_all("<Button-1>", self._on_any_click, add="+")

    def _on_resize(self, event: "tk.Event") -> None:
        if self.status_label is None:
            return
        if event.widget is self.root:
            min_wrap = 210 if self.compact_mode else 250
            self.status_label.config(wraplength=max(min_wrap, event.width - 48))
            if self.timer_font is not None:
                if self.compact_mode:
                    size = max(22, min(34, event.width // 9))
                else:
                    size = max(36, min(60, event.width // 8))
                self.timer_font.configure(size=size)
            if not self.compact_mode and event.width > 0 and event.height > 0:
                self.expanded_size = (event.width, event.height)

    def _on_enter_pressed(self, _: "tk.Event") -> None:
        if self.waiting_for_reps:
            self._log_reps()

    def _on_any_click(self, _: "tk.Event") -> None:
        if self.alarm_active:
            self._stop_alarm_loop(muted_by_user=True)

    def _start_alarm_loop(self) -> None:
        self._stop_alarm_loop(muted_by_user=False)
        self.alarm_stop_event = threading.Event()
        self.alarm_active = True

        def worker() -> None:
            ring_alarm(repeats=None, stop_event=self.alarm_stop_event)
            self.alarm_active = False

        self.alarm_thread = threading.Thread(target=worker, daemon=True)
        self.alarm_thread.start()

    def _stop_alarm_loop(self, muted_by_user: bool) -> None:
        if not self.alarm_active:
            return

        self.alarm_stop_event.set()
        self.alarm_active = False
        if muted_by_user and self.waiting_for_reps:
            self._set_status(
                f"Alarm muted. Time to do: {self._current_exercise_name()}. "
                "Enter reps and click Log reps."
            )

    def _toggle_pin(self) -> None:
        should_pin = self.pin_var.get()
        self.root.attributes("-topmost", should_pin)
        if self.stats_popup is not None:
            try:
                self.stats_popup.attributes("-topmost", should_pin)
            except tk.TclError:
                pass

    def _sync_pause_buttons(self) -> None:
        if not self.session_active:
            text = "Pause"
            state = "disabled"
        elif self.waiting_for_reps:
            text = "Pause"
            state = "disabled"
        elif self.timer_running:
            text = "Pause"
            state = "normal"
        else:
            text = "Resume"
            state = "normal"

        if self.start_pause_button is not None:
            self.start_pause_button.config(text=text, state=state)
        if self.quick_pause_button is not None:
            self.quick_pause_button.config(text=text, state=state)

    def _current_window_position(self) -> tuple[int, int]:
        geometry = self.root.geometry()
        parts = geometry.split("+")
        if len(parts) >= 3:
            try:
                return int(parts[1]), int(parts[2])
            except ValueError:
                pass
        return self.root.winfo_x(), self.root.winfo_y()

    def _set_window_size(self, width: int, height: int) -> None:
        x, y = self._current_window_position()
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _show_row(self, widget: "tk.Widget | None", **pack_kwargs: object) -> None:
        if widget is None:
            return
        if not widget.winfo_ismapped():
            widget.pack(**pack_kwargs)

    def _hide_row(self, widget: "tk.Widget | None") -> None:
        if widget is None:
            return
        if widget.winfo_ismapped():
            widget.pack_forget()

    def _apply_layout_mode(self, force: bool = False) -> None:
        should_compact = self.session_active
        waiting_state_changed = should_compact and (
            self.compact_waiting_state != self.waiting_for_reps
        )
        if not force and should_compact == self.compact_mode and not waiting_state_changed:
            return

        if should_compact and not self.compact_mode:
            current_width = self.root.winfo_width()
            current_height = self.root.winfo_height()
            if current_width >= 340 and current_height >= 500:
                self.expanded_size = (current_width, current_height)

        self.compact_mode = should_compact
        self.compact_waiting_state = self.waiting_for_reps

        if self.header_frame is not None:
            if self.compact_mode:
                self.header_frame.pack_forget()
            elif not self.header_frame.winfo_ismapped():
                if self.setup_card is not None and self.setup_card.winfo_ismapped():
                    self.header_frame.pack(fill="x", before=self.setup_card)
                elif self.live_card is not None and self.live_card.winfo_ismapped():
                    self.header_frame.pack(fill="x", before=self.live_card)
                else:
                    self.header_frame.pack(fill="x")

        if self.setup_card is not None:
            if not self.session_active:
                if not self.setup_card.winfo_ismapped():
                    self.setup_card.pack(fill="x", pady=(10, 8))
            else:
                self.setup_card.pack_forget()

        if self.live_card is not None and not self.live_card.winfo_ismapped():
            self.live_card.pack(fill="x", pady=(0, 8))

        if self.stats_card is not None:
            if self.compact_mode:
                self.stats_card.pack_forget()
            elif not self.stats_card.winfo_ismapped():
                self.stats_card.pack(fill="both", expand=True)

        if self.compact_mode:
            self._hide_row(self.status_label)
            self._show_row(self.next_row, fill="x")
            if self.waiting_for_reps:
                self._show_row(self.reps_row, fill="x", pady=(9, 4))
            else:
                self._hide_row(self.reps_row)
            self._hide_row(self.control_row)
            if self.waiting_for_reps:
                compact_height = 190
                self.root.minsize(260, 170)
            else:
                compact_height = self.compact_size[1]
                self.root.minsize(260, 130)
            self._set_window_size(self.compact_size[0], compact_height)
        else:
            self._show_row(self.status_label, fill="x", pady=(0, 6))
            self._show_row(self.next_row, fill="x")
            self._show_row(self.reps_row, fill="x", pady=(9, 4))
            self._show_row(self.control_row, fill="x", pady=(5, 0))
            self.root.minsize(340, 500)
            width = max(self.expanded_size[0], 340)
            height = max(self.expanded_size[1], 500)
            self._set_window_size(width, height)

            if self.waiting_for_reps:
                self.root.lift()
                try:
                    self.root.focus_force()
                except tk.TclError:
                    pass

    def _set_status(self, message: str, *, is_error: bool = False) -> None:
        self.status_var.set(message)
        if self.status_label is not None:
            self.status_label.config(
                fg=self.palette["error"] if is_error else self.palette["subtle"]
            )

    def _set_setup_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for widget in self.setup_widgets:
            try:
                widget.configure(state=state)
            except tk.TclError:
                pass
        for entry in self.exercise_entry_widgets:
            try:
                entry.configure(state=state)
            except tk.TclError:
                pass

    def _safe_positive_int(self, value: str) -> int | None:
        try:
            parsed = int(value)
            if parsed <= 0:
                return None
            return parsed
        except ValueError:
            return None

    def _safe_non_negative_int(self, value: str) -> int | None:
        try:
            parsed = int(value)
            if parsed < 0:
                return None
            return parsed
        except ValueError:
            return None

    def _rebuild_exercise_fields(self) -> None:
        if self.exercise_fields_frame is None:
            return

        count = self._safe_positive_int(self.exercise_count_var.get())
        if count is None:
            self._set_status("Exercise count must be a positive number.", is_error=True)
            return
        count = min(max(count, 1), 20)
        self.exercise_count_var.set(str(count))

        previous_names = [var.get().strip() for var in self.exercise_name_vars]
        for child in self.exercise_fields_frame.winfo_children():
            child.destroy()

        self.exercise_name_vars = []
        self.exercise_entry_widgets = []

        for index in range(count):
            row = tk.Frame(self.exercise_fields_frame, bg=self.palette["panel"])
            row.pack(fill="x", pady=2)

            tk.Label(
                row,
                text=f"Exercise {index + 1}",
                width=11,
                anchor="w",
                font=("Helvetica", 10),
                fg=self.palette["text"],
                bg=self.palette["panel"],
            ).pack(side="left")

            default_name = (
                previous_names[index]
                if index < len(previous_names) and previous_names[index]
                else f"Exercise {index + 1}"
            )
            name_var = tk.StringVar(value=default_name)
            self.exercise_name_vars.append(name_var)
            entry = tk.Entry(row, textvariable=name_var, font=("Helvetica", 10))
            entry.pack(side="left", fill="x", expand=True, padx=(6, 0))
            self.exercise_entry_widgets.append(entry)

        if self.session_active:
            self._set_setup_enabled(False)

    def _current_exercise_name(self) -> str:
        if not self.exercises:
            return "-"
        return self.exercises[self.current_index].name

    def _stats_summary_text(self) -> str:
        if not self.exercises:
            self.total_reps_var.set("0")
            self.total_rounds_var.set("0")
            return "No session started yet."

        total_reps = sum(ex.total_reps for ex in self.exercises)
        total_rounds = sum(ex.rounds_completed for ex in self.exercises)
        self.total_reps_var.set(str(total_reps))
        self.total_rounds_var.set(str(total_rounds))
        lines = [f"Total reps: {total_reps}", f"Total rounds: {total_rounds}", "", "Exercises:"]
        for ex in self.exercises:
            lines.append(
                f"- {ex.name}: {ex.total_reps} reps across {ex.rounds_completed} rounds"
            )
        return "\n".join(lines)

    def _refresh_stats_popup(self) -> None:
        if self.stats_popup_text is None:
            return
        summary = self._stats_summary_text()
        self.stats_popup_text.config(state="normal")
        self.stats_popup_text.delete("1.0", "end")
        self.stats_popup_text.insert("1.0", summary)
        self.stats_popup_text.config(state="disabled")

    def _close_stats_popup(self) -> None:
        if self.stats_popup is not None:
            try:
                self.stats_popup.destroy()
            except tk.TclError:
                pass
        self.stats_popup = None
        self.stats_popup_text = None

    def _open_stats_popup(self) -> None:
        if self.stats_popup is not None:
            try:
                self.stats_popup.lift()
                self.stats_popup.focus_force()
                self._refresh_stats_popup()
                return
            except tk.TclError:
                self.stats_popup = None
                self.stats_popup_text = None

        popup = tk.Toplevel(self.root)
        popup.title("FitCoder Stats")
        popup.geometry("360x320")
        popup.minsize(300, 220)
        popup.configure(bg=self.palette["panel"])
        popup.attributes("-topmost", self.pin_var.get())

        title = tk.Label(
            popup,
            text="SESSION STATS",
            font=("Helvetica", 10, "bold"),
            fg=self.palette["subtle"],
            bg=self.palette["panel"],
        )
        title.pack(anchor="w", padx=10, pady=(10, 4))

        text = tk.Text(
            popup,
            font=("Helvetica", 10),
            bg=self.palette["panel"],
            fg=self.palette["text"],
            relief="flat",
            highlightthickness=0,
            padx=2,
            pady=2,
        )
        text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        text.config(state="disabled")

        self.stats_popup = popup
        self.stats_popup_text = text
        popup.protocol("WM_DELETE_WINDOW", self._close_stats_popup)
        self._refresh_stats_popup()

    def _refresh_stats_view(self) -> None:
        if self.stats_text is None:
            return
        text = self._stats_summary_text()
        self.stats_text.config(state="normal")
        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("1.0", text)
        self.stats_text.config(state="disabled")
        self._refresh_stats_popup()

    def _update_live_panel(self) -> None:
        if not self.session_active:
            self.timer_var.set("00:00")
            self.next_exercise_var.set("-")
            self.progress_var.set(0.0)
            return

        self.timer_var.set(format_duration(self.remaining_seconds))
        self.next_exercise_var.set(self._current_exercise_name())
        if self.waiting_for_reps:
            self.progress_var.set(100.0)
        elif self.break_seconds > 0:
            progress = ((self.break_seconds - self.remaining_seconds) / self.break_seconds) * 100
            self.progress_var.set(max(0.0, min(100.0, progress)))
        else:
            self.progress_var.set(0.0)

    def _cancel_timer(self) -> None:
        if self.timer_job is not None:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None

    def _schedule_tick(self) -> None:
        self._cancel_timer()
        self.timer_job = self.root.after(1000, self._tick)

    def _start_timer(self) -> None:
        if not self.session_active or self.waiting_for_reps:
            return
        if self.timer_running:
            return
        self.timer_running = True
        self._sync_pause_buttons()
        self._schedule_tick()

    def _pause_timer(self) -> None:
        self.timer_running = False
        self._cancel_timer()
        self._sync_pause_buttons()
        self._set_status(f"Paused. Next: {self._current_exercise_name()}")

    def _toggle_pause(self) -> None:
        if not self.session_active or self.waiting_for_reps:
            return
        if self.timer_running:
            self._pause_timer()
        else:
            self._set_status(f"Break running. Next: {self._current_exercise_name()}")
            self._start_timer()

    def _tick(self) -> None:
        if not self.session_active or not self.timer_running:
            return
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self._update_live_panel()

        if self.remaining_seconds <= 0:
            self._finish_break()
            return

        self._schedule_tick()

    def _finish_break(self) -> None:
        self._cancel_timer()
        self.timer_running = False
        self.waiting_for_reps = True
        self.remaining_seconds = 0
        self._update_live_panel()
        self._apply_layout_mode()
        if self.timer_label is not None:
            self.timer_label.config(fg=self.palette["alarm"])
        self._set_status(
            f"Time to do: {self._current_exercise_name()}. "
            "Click anywhere in the widget to mute alarm."
        )

        if self.reps_entry is not None:
            self.reps_entry.config(state="normal")
            self.reps_entry.focus_set()
        if self.log_reps_button is not None:
            self.log_reps_button.config(state="normal")
        if self.skip_button is not None:
            self.skip_button.config(state="disabled")
        self._sync_pause_buttons()

        self.root.bell()
        self._start_alarm_loop()

    def _log_reps(self) -> None:
        if not self.waiting_for_reps or not self.session_active:
            return

        self._stop_alarm_loop(muted_by_user=False)
        reps = self._safe_non_negative_int(self.reps_input_var.get())
        if reps is None:
            self._set_status("Reps must be a whole number (0 or more).", is_error=True)
            return

        current_exercise = self.exercises[self.current_index]
        current_exercise.total_reps += reps
        current_exercise.rounds_completed += 1
        completed_name = current_exercise.name

        self.current_index = (self.current_index + 1) % len(self.exercises)
        self.waiting_for_reps = False
        self.remaining_seconds = self.break_seconds
        self.reps_input_var.set("")
        self._apply_layout_mode()

        if self.reps_entry is not None:
            self.reps_entry.config(state="disabled")
        if self.log_reps_button is not None:
            self.log_reps_button.config(state="disabled")
        if self.skip_button is not None:
            self.skip_button.config(state="normal")
        if self.timer_label is not None:
            self.timer_label.config(fg=self.palette["accent"])
        self._sync_pause_buttons()

        self._refresh_stats_view()
        self._update_live_panel()
        self._set_status(
            f"Logged {reps} reps for {completed_name}. Break restarted. "
            f"Next: {self._current_exercise_name()}"
        )
        self._start_timer()

    def _skip_break(self) -> None:
        if not self.session_active or self.waiting_for_reps:
            return
        self.remaining_seconds = 0
        self._finish_break()

    def _start_session(self) -> None:
        count = self._safe_positive_int(self.exercise_count_var.get())
        if count is None:
            self._set_status("Exercise count must be a positive whole number.", is_error=True)
            return
        break_minutes = self._safe_positive_int(self.break_minutes_var.get())
        if break_minutes is None:
            self._set_status("Break length must be a positive whole number.", is_error=True)
            return

        names = [var.get().strip() for var in self.exercise_name_vars]
        if len(names) != count:
            self._set_status("Click Build before starting session.", is_error=True)
            return
        if any(not name for name in names):
            self._set_status("Every exercise needs a name.", is_error=True)
            return

        self._stop_alarm_loop(muted_by_user=False)
        self._cancel_timer()
        self.session_active = True
        self.waiting_for_reps = False
        self.timer_running = False
        self.exercises = [ExerciseStats(name=name) for name in names]
        self.break_seconds = break_minutes * 60
        self.remaining_seconds = self.break_seconds
        self.current_index = 0
        self.reps_input_var.set("")
        self._apply_layout_mode()

        self._set_setup_enabled(False)
        if self.skip_button is not None:
            self.skip_button.config(state="normal")
        if self.reps_entry is not None:
            self.reps_entry.config(state="disabled")
        if self.log_reps_button is not None:
            self.log_reps_button.config(state="disabled")
        if self.timer_label is not None:
            self.timer_label.config(fg=self.palette["accent"])
        self._sync_pause_buttons()

        self._refresh_stats_view()
        self._update_live_panel()
        self._set_status(f"Break running. Next: {self._current_exercise_name()}")
        self._start_timer()

    def _new_session(self) -> None:
        self._stop_alarm_loop(muted_by_user=False)
        self._cancel_timer()
        self.session_active = False
        self.timer_running = False
        self.waiting_for_reps = False
        self.exercises = []
        self.break_seconds = 0
        self.remaining_seconds = 0
        self.current_index = 0
        self.reps_input_var.set("")
        self._apply_layout_mode(force=True)

        self._set_setup_enabled(True)
        if self.skip_button is not None:
            self.skip_button.config(state="disabled")
        if self.reps_entry is not None:
            self.reps_entry.config(state="disabled")
        if self.log_reps_button is not None:
            self.log_reps_button.config(state="disabled")
        if self.timer_label is not None:
            self.timer_label.config(fg=self.palette["accent"])
        self._sync_pause_buttons()

        self._update_live_panel()
        self._refresh_stats_view()
        self._set_status("Configure routine and click Start session.")

    def _on_close(self) -> None:
        self._stop_alarm_loop(muted_by_user=False)
        self._cancel_timer()
        self._close_stats_popup()
        self.root.destroy()


def run() -> None:
    print("Starting fit coder...")

    if tk is None or ttk is None or tkfont is None:
        run_cli_fallback()
        return

    try:
        root = tk.Tk()
    except Exception:
        run_cli_fallback()
        return

    FitCoderWidgetApp(root)
    root.mainloop()


if __name__ == "__main__":
    run()
