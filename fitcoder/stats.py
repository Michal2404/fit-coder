from __future__ import annotations

from .models import ExerciseStats


def format_duration(total_seconds: int) -> str:
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def stats_totals(exercises: list[ExerciseStats]) -> tuple[int, int]:
    total_reps = sum(ex.total_reps for ex in exercises)
    total_rounds = sum(ex.rounds_completed for ex in exercises)
    return total_reps, total_rounds


def stats_table(exercises: list[ExerciseStats]) -> str:
    headers = ("Exercise", "Reps", "Rounds")

    name_width = len(headers[0])
    reps_width = len(headers[1])
    rounds_width = len(headers[2])

    for ex in exercises:
        name_width = max(name_width, len(ex.name))
        reps_width = max(reps_width, len(str(ex.total_reps)))
        rounds_width = max(rounds_width, len(str(ex.rounds_completed)))

    border = (
        f"+-{'-' * name_width}-+-{'-' * reps_width}-+-{'-' * rounds_width}-+"
    )
    lines = [
        border,
        (
            f"| {headers[0].ljust(name_width)} | {headers[1].rjust(reps_width)} "
            f"| {headers[2].rjust(rounds_width)} |"
        ),
        border,
    ]
    for ex in exercises:
        lines.append(
            f"| {ex.name.ljust(name_width)} | {str(ex.total_reps).rjust(reps_width)} "
            f"| {str(ex.rounds_completed).rjust(rounds_width)} |"
        )
    lines.append(border)
    return "\n".join(lines)


def print_stats(exercises: list[ExerciseStats]) -> None:
    total_reps, total_rounds = stats_totals(exercises)
    table = stats_table(exercises)
    print("\nSession stats")
    print(f"Total reps: {total_reps}")
    print(f"Total completed rounds: {total_rounds}")
    print()
    print(table)
    print()
