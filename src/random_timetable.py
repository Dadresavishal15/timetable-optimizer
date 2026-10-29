"""
random_timetable.py - Generate a random timetable as a baseline

Assigns each class session a random time slot and room.
This serves as:
1. A baseline to compare against the Genetic Algorithm
2. A way to verify the validator works correctly
"""

import random

from src.models import TimetableData, Assignment


def generate_random_timetable(
    data: TimetableData, seed: int | None = None
) -> list[Assignment]:
    """
    Generate a random timetable by assigning each session a random slot and room.

    Args:
        data: TimetableData with sessions, slots, and rooms.
        seed: Optional random seed for reproducibility.

    Returns:
        List of Assignment objects (one per session).
    """
    if seed is not None:
        random.seed(seed)

    assignments = []
    for session in data.sessions:
        slot = random.choice(data.slots)
        room = random.choice(data.rooms)
        assignments.append(Assignment(session=session, slot=slot, room=room))

    return assignments


# ─── Quick test: run this file directly ─────────────────────────────
if __name__ == "__main__":
    from pathlib import Path
    from src.data_loader import load_from_json
    from src.validator import validate_timetable

    data_path = Path(__file__).parent.parent / "data" / "sample_data.json"
    data = load_from_json(data_path)

    print("Generating 5 random timetables to test the validator...\n")

    for trial in range(5):
        assignments = generate_random_timetable(data, seed=trial)
        result = validate_timetable(assignments)

        print(f"--- Trial {trial + 1} (seed={trial}) ---")
        print(f"  Faculty conflicts:       {len(result.faculty_conflicts)}")
        print(f"  Room conflicts:          {len(result.room_conflicts)}")
        print(f"  Student group conflicts: {len(result.student_group_conflicts)}")
        print(f"  Total conflicts:         {result.total_conflicts}")
        print(f"  Valid: {result.is_valid}")
        print()

    # Show detailed output for the last trial
    print("Detailed report for last trial:")
    print(result.summary())

    # Show the assignments
    print("\nAssignments:")
    for a in assignments:
        print(f"  {a}")
