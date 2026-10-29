"""
validator.py - Detect conflicts in a timetable

Checks three hard constraints:
1. Faculty conflict:      Same faculty teaching two classes in the same slot
2. Room conflict:         Same room used by two classes in the same slot
3. Student group conflict: Same student group in two classes in the same slot

Returns detailed conflict information for debugging and scoring.
"""

from dataclasses import dataclass, field
from collections import defaultdict

from src.models import Assignment


@dataclass
class Conflict:
    """Describes a single conflict between two assignments."""
    conflict_type: str          # "faculty", "room", or "student_group"
    slot_day: str
    slot_period: int
    detail: str                 # Human-readable description
    session_ids: tuple[str, str]  # The two conflicting session IDs


@dataclass
class ValidationResult:
    """Full validation result for a timetable."""
    faculty_conflicts: list[Conflict] = field(default_factory=list)
    room_conflicts: list[Conflict] = field(default_factory=list)
    student_group_conflicts: list[Conflict] = field(default_factory=list)

    @property
    def total_conflicts(self) -> int:
        return (
            len(self.faculty_conflicts)
            + len(self.room_conflicts)
            + len(self.student_group_conflicts)
        )

    @property
    def is_valid(self) -> bool:
        return self.total_conflicts == 0

    def summary(self) -> str:
        lines = [
            "=" * 50,
            "VALIDATION RESULT",
            "=" * 50,
            f"Faculty conflicts:       {len(self.faculty_conflicts)}",
            f"Room conflicts:          {len(self.room_conflicts)}",
            f"Student group conflicts: {len(self.student_group_conflicts)}",
            f"Total conflicts:         {self.total_conflicts}",
            f"Valid timetable:         {'YES' if self.is_valid else 'NO'}",
            "=" * 50,
        ]

        if self.faculty_conflicts:
            lines.append("\nFaculty Conflicts:")
            for c in self.faculty_conflicts:
                lines.append(f"  - {c.detail}")

        if self.room_conflicts:
            lines.append("\nRoom Conflicts:")
            for c in self.room_conflicts:
                lines.append(f"  - {c.detail}")

        if self.student_group_conflicts:
            lines.append("\nStudent Group Conflicts:")
            for c in self.student_group_conflicts:
                lines.append(f"  - {c.detail}")

        return "\n".join(lines)


def validate_timetable(assignments: list[Assignment]) -> ValidationResult:
    """
    Check a list of assignments for all hard-constraint conflicts.

    Args:
        assignments: List of Assignment objects (session -> slot + room)

    Returns:
        ValidationResult with all detected conflicts.
    """
    result = ValidationResult()

    # Group assignments by slot_id for pairwise comparison
    by_slot: dict[int, list[Assignment]] = defaultdict(list)
    for a in assignments:
        by_slot[a.slot.slot_id].append(a)

    for slot_id, slot_assignments in by_slot.items():
        n = len(slot_assignments)
        for i in range(n):
            for j in range(i + 1, n):
                a1 = slot_assignments[i]
                a2 = slot_assignments[j]

                # --- Faculty conflict ---
                if a1.session.faculty == a2.session.faculty:
                    result.faculty_conflicts.append(Conflict(
                        conflict_type="faculty",
                        slot_day=a1.slot.day,
                        slot_period=a1.slot.period,
                        detail=(
                            f"{a1.session.faculty} double-booked on "
                            f"{a1.slot.day} P{a1.slot.period}: "
                            f"{a1.session.session_id} ({a1.session.subject}) vs "
                            f"{a2.session.session_id} ({a2.session.subject})"
                        ),
                        session_ids=(a1.session.session_id, a2.session.session_id),
                    ))

                # --- Room conflict ---
                if a1.room.room_id == a2.room.room_id:
                    result.room_conflicts.append(Conflict(
                        conflict_type="room",
                        slot_day=a1.slot.day,
                        slot_period=a1.slot.period,
                        detail=(
                            f"Room {a1.room.room_id} double-booked on "
                            f"{a1.slot.day} P{a1.slot.period}: "
                            f"{a1.session.session_id} vs {a2.session.session_id}"
                        ),
                        session_ids=(a1.session.session_id, a2.session.session_id),
                    ))

                # --- Student group conflict ---
                if a1.session.student_group == a2.session.student_group:
                    result.student_group_conflicts.append(Conflict(
                        conflict_type="student_group",
                        slot_day=a1.slot.day,
                        slot_period=a1.slot.period,
                        detail=(
                            f"Group {a1.session.student_group} double-booked on "
                            f"{a1.slot.day} P{a1.slot.period}: "
                            f"{a1.session.session_id} ({a1.session.subject}) vs "
                            f"{a2.session.session_id} ({a2.session.subject})"
                        ),
                        session_ids=(a1.session.session_id, a2.session.session_id),
                    ))

    return result
