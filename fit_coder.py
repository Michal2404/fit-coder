#!/usr/bin/env python3

import time
from dataclasses import dataclass


@dataclass
class ExerciseStats:
    name: str
    total_reps: int = 0
    rounds_completed: int = 0


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


def format_duration(total_seconds: int) -> str:
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def countdown(seconds: int, exercise_name: str) -> None:
    for remaining in range(seconds, 0, -1):
        timer = format_duration(remaining)
        print(
            f"\rBreak time. Next: {exercise_name} in {timer}. Press Ctrl+C to stop.",
            end="",
            flush=True,
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

    input("\nSetup complete. Press Enter to start the timer...")
    print("Timer started. The app will keep running until you press Ctrl+C.\n")

    break_seconds = break_minutes * 60
    current_index = 0

    try:
        while True:
            exercise = exercises[current_index]
            countdown(break_seconds, exercise.name)

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


if __name__ == "__main__":
    run()
