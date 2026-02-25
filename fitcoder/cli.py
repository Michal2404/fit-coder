from __future__ import annotations

import time

from .alarm import ring_alarm
from .models import ExerciseStats
from .stats import format_duration, print_stats


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
