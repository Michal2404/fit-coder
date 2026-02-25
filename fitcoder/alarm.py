from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import time

LINUX_OGA_SOUNDS = (
    "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga",
    "/usr/share/sounds/freedesktop/stereo/complete.oga",
    "/usr/share/sounds/freedesktop/stereo/bell.oga",
)
LINUX_WAV_SOUNDS = (
    "/usr/share/sounds/alsa/Front_Center.wav",
    "/usr/share/sounds/alsa/Noise.wav",
)


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
    if _run_alarm_command(
        ["canberra-gtk-play", "-i", "alarm-clock-elapsed", "-d", "fitcoder"]
    ):
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
