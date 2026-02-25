from dataclasses import dataclass


@dataclass
class ExerciseStats:
    name: str
    total_reps: int = 0
    rounds_completed: int = 0
