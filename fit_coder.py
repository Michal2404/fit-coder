#!/usr/bin/env python3

import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass

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


class SessionWidget:
    def __init__(self) -> None:
        self.enabled = False
        self._start_error = ""
        self._queue: queue.Queue[dict[str, object]] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._ready_event = threading.Event()
        self._stop_event = threading.Event()

    def start(self) -> bool:
        self._thread = threading.Thread(
            target=self._run_gui,
            name="fitcoder-widget",
            daemon=True,
        )
        self._thread.start()
        self._ready_event.wait(timeout=4)
        return self.enabled

    def stop(self) -> None:
        self._stop_event.set()
        self._queue.put({"event": "close"})
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)

    def update(
        self,
        timer: str,
        status: str,
        exercises: list[ExerciseStats],
        progress: float = 0.0,
    ) -> None:
        if not self.enabled:
            return

        total_reps = sum(ex.total_reps for ex in exercises)
        total_rounds = sum(ex.rounds_completed for ex in exercises)
        exercise_lines = [
            f"{ex.name}: {ex.total_reps} reps ({ex.rounds_completed} rounds)"
            for ex in exercises
        ]

        self._queue.put(
            {
                "timer": timer,
                "status": status,
                "progress": max(0.0, min(100.0, progress)),
                "total_reps": total_reps,
                "total_rounds": total_rounds,
                "exercise_lines": exercise_lines,
                "event": "update",
            }
        )

    def notify_alarm(self) -> None:
        if self.enabled:
            self._queue.put({"event": "alarm"})

    def _run_gui(self) -> None:
        try:
            import tkinter as tk
            from tkinter import font as tkfont
            from tkinter import ttk
        except Exception as exc:
            self._start_error = str(exc)
            self._ready_event.set()
            return

        try:
            root = tk.Tk()
        except Exception as exc:
            self._start_error = str(exc)
            self._ready_event.set()
            return

        palette = {
            "bg": "#f5f7fb",
            "panel": "#ffffff",
            "text": "#1f2937",
            "subtle": "#5b667a",
            "accent": "#0f766e",
            "alarm": "#dc2626",
            "track": "#dce3ef",
        }

        style = ttk.Style(root)
        for theme in ("clam", "alt", "default"):
            if theme in style.theme_names():
                style.theme_use(theme)
                break
        style.configure(
            "Widget.Horizontal.TProgressbar",
            troughcolor=palette["track"],
            background=palette["accent"],
            bordercolor=palette["track"],
            lightcolor=palette["accent"],
            darkcolor=palette["accent"],
            thickness=12,
        )

        root.title("FitCoder")
        root.geometry("370x330+50+50")
        root.minsize(300, 260)
        root.attributes("-topmost", True)
        root.configure(bg=palette["bg"])
        root.resizable(True, True)

        frame = tk.Frame(root, padx=12, pady=12, bg=palette["bg"])
        frame.pack(fill="both", expand=True)

        header = tk.Frame(frame, bg=palette["bg"])
        header.pack(fill="x")

        title_label = tk.Label(
            header,
            text="FITCODER LIVE",
            font=("Helvetica", 10, "bold"),
            fg=palette["subtle"],
            bg=palette["bg"],
        )
        title_label.pack(side="left")

        controls = tk.Frame(header, bg=palette["bg"])
        controls.pack(side="right")

        pin_var = tk.BooleanVar(value=True)

        def toggle_pin() -> None:
            root.attributes("-topmost", pin_var.get())

        pin_button = tk.Checkbutton(
            controls,
            text="Pin",
            variable=pin_var,
            command=toggle_pin,
            font=("Helvetica", 9),
            bg=palette["bg"],
            fg=palette["subtle"],
            activebackground=palette["bg"],
            activeforeground=palette["text"],
            selectcolor=palette["bg"],
            highlightthickness=0,
            bd=0,
        )
        pin_button.pack(side="left", padx=(0, 4))

        def apply_size(width: int, height: int) -> None:
            root.geometry(f"{width}x{height}")

        for label, size in (("S", (320, 280)), ("M", (370, 330)), ("L", (460, 420))):
            button = tk.Button(
                controls,
                text=label,
                command=lambda s=size: apply_size(*s),
                font=("Helvetica", 8, "bold"),
                bg=palette["panel"],
                fg=palette["subtle"],
                activebackground="#e8eef9",
                activeforeground=palette["text"],
                relief="flat",
                padx=6,
                pady=1,
                bd=0,
            )
            button.pack(side="left", padx=2)

        body = tk.Frame(
            frame,
            bg=palette["panel"],
            highlightbackground="#d8dfec",
            highlightthickness=1,
        )
        body.pack(fill="both", expand=True, pady=(10, 0))

        timer_font = tkfont.Font(family="Helvetica", size=40, weight="bold")
        timer_label = tk.Label(
            body,
            text="00:00",
            font=timer_font,
            fg=palette["accent"],
            bg=palette["panel"],
        )
        timer_label.pack(anchor="w", padx=14, pady=(12, 0))

        status_label = tk.Label(
            body,
            text="Waiting...",
            font=("Helvetica", 11),
            fg=palette["subtle"],
            bg=palette["panel"],
            justify="left",
            wraplength=320,
            anchor="w",
        )
        status_label.pack(fill="x", padx=14, pady=(0, 8))

        progress_var = tk.DoubleVar(value=0.0)
        progress_bar = ttk.Progressbar(
            body,
            style="Widget.Horizontal.TProgressbar",
            orient="horizontal",
            mode="determinate",
            maximum=100,
            variable=progress_var,
        )
        progress_bar.pack(fill="x", padx=14, pady=(0, 10))

        metrics = tk.Frame(body, bg=palette["panel"])
        metrics.pack(fill="x", padx=14, pady=(0, 8))

        reps_panel = tk.Frame(metrics, bg="#eefaf8")
        reps_panel.pack(side="left", fill="x", expand=True, padx=(0, 6))
        reps_title = tk.Label(
            reps_panel,
            text="TOTAL REPS",
            font=("Helvetica", 9, "bold"),
            fg=palette["subtle"],
            bg="#eefaf8",
        )
        reps_title.pack(anchor="w", padx=8, pady=(5, 0))
        reps_value = tk.Label(
            reps_panel,
            text="0",
            font=("Helvetica", 18, "bold"),
            fg=palette["text"],
            bg="#eefaf8",
        )
        reps_value.pack(anchor="w", padx=8, pady=(0, 5))

        rounds_panel = tk.Frame(metrics, bg="#fff4e8")
        rounds_panel.pack(side="left", fill="x", expand=True, padx=(6, 0))
        rounds_title = tk.Label(
            rounds_panel,
            text="ROUNDS",
            font=("Helvetica", 9, "bold"),
            fg=palette["subtle"],
            bg="#fff4e8",
        )
        rounds_title.pack(anchor="w", padx=8, pady=(5, 0))
        rounds_value = tk.Label(
            rounds_panel,
            text="0",
            font=("Helvetica", 18, "bold"),
            fg=palette["text"],
            bg="#fff4e8",
        )
        rounds_value.pack(anchor="w", padx=8, pady=(0, 5))

        exercises_title = tk.Label(
            body,
            text="EXERCISES",
            font=("Helvetica", 9, "bold"),
            fg=palette["subtle"],
            bg=palette["panel"],
        )
        exercises_title.pack(anchor="w", padx=14)

        exercises_text = tk.Text(
            body,
            height=7,
            font=("Helvetica", 10),
            bg=palette["panel"],
            fg=palette["text"],
            relief="flat",
            highlightthickness=0,
            padx=2,
            pady=2,
        )
        exercises_text.insert("1.0", "No session data yet.")
        exercises_text.config(state="disabled")
        exercises_text.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        def close_window() -> None:
            self.enabled = False
            try:
                root.destroy()
            except tk.TclError:
                pass

        def flash_alarm() -> None:
            timer_label.config(fg=palette["alarm"])
            root.bell()
            root.after(700, lambda: timer_label.config(fg=palette["accent"]))

        def pump_updates() -> None:
            while True:
                try:
                    payload = self._queue.get_nowait()
                except queue.Empty:
                    break

                event = payload.get("event")
                if event == "close":
                    close_window()
                    return
                if event == "alarm":
                    flash_alarm()
                    continue

                if event != "update":
                    continue

                timer_label.config(text=str(payload.get("timer", "00:00")))
                status_label.config(text=str(payload.get("status", "Waiting...")))
                progress_var.set(float(payload.get("progress", 0.0)))
                reps_value.config(text=str(payload.get("total_reps", 0)))
                rounds_value.config(text=str(payload.get("total_rounds", 0)))

                lines = payload.get("exercise_lines", [])
                if not isinstance(lines, list):
                    lines = []

                exercises_text.config(state="normal")
                exercises_text.delete("1.0", "end")
                exercises_text.insert("1.0", "\n".join(lines) if lines else "No session data yet.")
                exercises_text.config(state="disabled")

            if self._stop_event.is_set():
                close_window()
                return

            root.after(150, pump_updates)

        def on_resize(event: tk.Event) -> None:
            if event.widget is not root:
                return
            width = max(event.width, 300)
            status_label.config(wraplength=width - 56)
            timer_font.configure(size=max(30, min(58, width // 7)))

        root.protocol("WM_DELETE_WINDOW", close_window)
        root.bind("<Configure>", on_resize)
        self.enabled = True
        self._ready_event.set()
        root.after(150, pump_updates)
        root.mainloop()


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


def ask_exercise_name(index: int) -> str:
    while True:
        name = input(f"Give the name of exercise {index}: ").strip()
        if not name:
            print("Exercise name cannot be empty.")
            continue
        return name


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


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    options = "Y/n" if default else "y/N"
    while True:
        raw_value = input(f"{prompt} [{options}] ").strip().lower()
        if not raw_value:
            return default
        if raw_value in {"y", "yes"}:
            return True
        if raw_value in {"n", "no"}:
            return False
        print("Please answer with y or n.")


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


def ring_alarm(widget: SessionWidget | None = None) -> None:
    for _ in range(2):
        if widget:
            widget.notify_alarm()
        if not _play_system_alarm_once():
            print("\a", end="", flush=True)
        time.sleep(0.35)


def countdown(
    seconds: int,
    exercise_name: str,
    widget: SessionWidget | None,
    exercises: list[ExerciseStats],
) -> None:
    for remaining in range(seconds, 0, -1):
        timer = format_duration(remaining)
        status = f"Break time. Next: {exercise_name}"
        progress = ((seconds - remaining) / seconds) * 100 if seconds else 100.0
        print(
            f"\rBreak time. Next: {exercise_name} in {timer}. Press Ctrl+C to stop.",
            end="",
            flush=True,
        )
        if widget:
            widget.update(
                timer=timer,
                status=status,
                exercises=exercises,
                progress=progress,
            )
        time.sleep(1)
    print("\rBreak over. " + " " * 70)


def print_stats(exercises: list[ExerciseStats]) -> None:
    total_reps = sum(ex.total_reps for ex in exercises)
    total_rounds = sum(ex.rounds_completed for ex in exercises)

    print("\nSession stats")
    print(f"- Total reps: {total_reps}")
    print(f"- Total completed rounds: {total_rounds}")
    print("- Per exercise:")
    for ex in exercises:
        print(
            f"  {ex.name}: {ex.total_reps} reps across {ex.rounds_completed} rounds"
        )
    print()


def run() -> None:
    print("Starting the app...")
    print("Welcome to fit coder!")

    exercise_count = ask_positive_int(
        "How many exercises do you want to include into the routine? "
    )
    break_minutes = ask_positive_int(
        "How long should the break be between exercises? (mins) "
    )

    exercises = [ExerciseStats(name=ask_exercise_name(i + 1)) for i in range(exercise_count)]
    widget_enabled = ask_yes_no("Enable mini widget window with timer and stats?", default=True)

    widget: SessionWidget | None = None
    if widget_enabled:
        widget = SessionWidget()
        if not widget.start():
            print(
                f"Could not start widget ({widget._start_error or 'unknown error'}). "
                "Continuing in CLI-only mode."
            )
            widget = None

    input("\nSetup complete. Press Enter to start the timer...")
    print("Timer started. The app will keep running until you press Ctrl+C.\n")

    break_seconds = break_minutes * 60
    current_index = 0

    if widget:
        widget.update(
            timer=format_duration(break_seconds),
            status="Timer started.",
            exercises=exercises,
            progress=0.0,
        )

    try:
        while True:
            exercise = exercises[current_index]
            countdown(
                seconds=break_seconds,
                exercise_name=exercise.name,
                widget=widget,
                exercises=exercises,
            )

            ring_alarm(widget=widget)
            if widget:
                widget.update(
                    timer="00:00",
                    status=f"Time to do: {exercise.name}",
                    exercises=exercises,
                    progress=100.0,
                )

            print(f"\nTime to do: {exercise.name}")
            reps = ask_non_negative_int("How many reps did you do? ")

            exercise.total_reps += reps
            exercise.rounds_completed += 1

            print_stats(exercises)
            if widget:
                widget.update(
                    timer=format_duration(break_seconds),
                    status=f"Logged reps for {exercise.name}. Next break running soon.",
                    exercises=exercises,
                    progress=0.0,
                )
            current_index = (current_index + 1) % len(exercises)
    except KeyboardInterrupt:
        print("\n\nStopping fit coder...")
        print_stats(exercises)
        print("Goodbye.")
    finally:
        if widget:
            widget.stop()


if __name__ == "__main__":
    run()
