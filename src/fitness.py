"""
fitness.py - Score a timetable for the Genetic Algorithm

Computes a penalty score based on constraint violations:
  - Hard constraints (high penalty):  faculty, room, student-group conflicts
  - Soft constraints (low penalty):   consecutive classes for same group/faculty

Lower penalty = better timetable. A score of 0 means no conflicts at all.
"""

from dataclasses import dataclass
from collections import defaultdict

from src.models import Assignment, TimetableData


@dataclass
class FitnessWeights:
    """Configurable penalty weights for each conflict type."""
    faculty_conflict: int = 100
    room_conflict: int = 100
    student_group_conflict: int = 100
    consecutive_classes: int = 2  # Soft penalty per consecutive pair


@dataclass
class FitnessBreakdown:
    """Detailed breakdown of the fitness score."""
    faculty_conflicts: int = 0
    room_conflicts: int = 0
    student_group_conflicts: int = 0
    consecutive_pairs: int = 0
    weights: FitnessWeights = None

    def __post_init__(self):
        if self.weights is None:
            self.weights = FitnessWeights()

    @property
    def hard_penalty(self) -> int:
        """Total penalty from hard constraint violations."""
        return (
            self.faculty_conflicts * self.weights.faculty_conflict
            + self.room_conflicts * self.weights.room_conflict
            + self.student_group_conflicts * self.weights.student_group_conflict
        )

    @property
    def soft_penalty(self) -> int:
        """Total penalty from soft constraint violations."""
        return self.consecutive_pairs * self.weights.consecutive_classes

    @property
    def total_penalty(self) -> int:
        """Combined penalty score. Lower is better."""
        return self.hard_penalty + self.soft_penalty

    @property
    def hard_conflicts_count(self) -> int:
        """Total number of hard conflicts."""
        return (
            self.faculty_conflicts
            + self.room_conflicts
            + self.student_group_conflicts
        )

    def summary(self) -> str:
        lines = [
            "--- Fitness Breakdown ---",
            f"  Faculty conflicts:       {self.faculty_conflicts} x {self.weights.faculty_conflict} = {self.faculty_conflicts * self.weights.faculty_conflict}",
            f"  Room conflicts:          {self.room_conflicts} x {self.weights.room_conflict} = {self.room_conflicts * self.weights.room_conflict}",
            f"  Student group conflicts: {self.student_group_conflicts} x {self.weights.student_group_conflict} = {self.student_group_conflicts * self.weights.student_group_conflict}",
            f"  Consecutive pairs:       {self.consecutive_pairs} x {self.weights.consecutive_classes} = {self.consecutive_pairs * self.weights.consecutive_classes}",
            f"  -------------------------",
            f"  Hard penalty:  {self.hard_penalty}",
            f"  Soft penalty:  {self.soft_penalty}",
            f"  TOTAL PENALTY: {self.total_penalty}",
        ]
        return "\n".join(lines)


def _count_hard_conflicts(assignments: list[Assignment]) -> tuple[int, int, int]:
    """
    Count faculty, room, and student-group conflicts.

    Returns:
        (faculty_conflicts, room_conflicts, student_group_conflicts)
    """
    faculty_conflicts = 0
    room_conflicts = 0
    student_group_conflicts = 0

    # Group assignments by slot_id
    by_slot: dict[int, list[Assignment]] = defaultdict(list)
    for a in assignments:
        by_slot[a.slot.slot_id].append(a)

    for slot_id, slot_assignments in by_slot.items():
        n = len(slot_assignments)
        for i in range(n):
            for j in range(i + 1, n):
                a1 = slot_assignments[i]
                a2 = slot_assignments[j]

                if a1.session.faculty == a2.session.faculty:
                    faculty_conflicts += 1
                if a1.room.room_id == a2.room.room_id:
                    room_conflicts += 1
                if a1.session.student_group == a2.session.student_group:
                    student_group_conflicts += 1

    return faculty_conflicts, room_conflicts, student_group_conflicts


def _count_consecutive_classes(assignments: list[Assignment]) -> int:
    """
    Count how many times a faculty member or student group has
    back-to-back classes (consecutive periods on the same day).
    """
    consecutive = 0

    # Build lookup: (day, entity_type, entity_name) -> sorted list of periods
    schedule: dict[tuple[str, str, str], list[int]] = defaultdict(list)

    for a in assignments:
        day = a.slot.day
        period = a.slot.period
        # Track by faculty
        schedule[(day, "faculty", a.session.faculty)].append(period)
        # Track by student group
        schedule[(day, "group", a.session.student_group)].append(period)

    for key, periods in schedule.items():
        periods_sorted = sorted(periods)
        for i in range(len(periods_sorted) - 1):
            if periods_sorted[i + 1] - periods_sorted[i] == 1:
                consecutive += 1

    return consecutive


def evaluate_fitness(
    assignments: list[Assignment],
    weights: FitnessWeights | None = None,
) -> FitnessBreakdown:
    """
    Evaluate the fitness of a timetable.

    Args:
        assignments: List of Assignment objects.
        weights: Optional custom penalty weights.

    Returns:
        FitnessBreakdown with all counts and the total penalty.
    """
    if weights is None:
        weights = FitnessWeights()

    fc, rc, sgc = _count_hard_conflicts(assignments)
    consec = _count_consecutive_classes(assignments)

    return FitnessBreakdown(
        faculty_conflicts=fc,
        room_conflicts=rc,
        student_group_conflicts=sgc,
        consecutive_pairs=consec,
        weights=weights,
    )


# ─── Quick test: run this file directly ─────────────────────────────
if __name__ == "__main__":
    from pathlib import Path
    from src.data_loader import load_from_json
    from src.random_timetable import generate_random_timetable

    data_path = Path(__file__).parent.parent / "data" / "sample_data.json"
    data = load_from_json(data_path)

    print("Fitness scores for 5 random timetables:\n")
    for seed in range(5):
        assignments = generate_random_timetable(data, seed=seed)
        breakdown = evaluate_fitness(assignments)
        print(f"Seed {seed}: penalty = {breakdown.total_penalty:4d}  "
              f"(hard={breakdown.hard_penalty}, soft={breakdown.soft_penalty}, "
              f"conflicts={breakdown.hard_conflicts_count})")

    # Detailed breakdown for last one
    print(f"\n{breakdown.summary()}")
