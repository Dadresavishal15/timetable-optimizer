"""
models.py - Data models for the Timetable Optimizer

Defines the core data structures:
- ClassSession: A class that needs to be scheduled (subject + faculty + group)
- TimeSlot: A specific day + period combination
- Room: A physical room where classes happen
- Assignment: Maps a session to a slot and room
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ClassSession:
    """Represents a single class that needs a time slot and room."""
    session_id: str
    subject: str
    faculty: str
    student_group: str
    duration_slots: int = 1  # Start with single-slot classes
    required_room_type: Optional[str] = None

    def __repr__(self):
        return f"Session({self.session_id}: {self.subject}, {self.faculty}, {self.student_group})"


@dataclass
class TimeSlot:
    """Represents a specific time slot (day + period)."""
    slot_id: int
    day: str
    period: int  # 1-based period number within the day

    def __repr__(self):
        return f"Slot({self.day} P{self.period})"


@dataclass
class Room:
    """Represents a physical classroom."""
    room_id: str
    capacity: Optional[int] = None
    room_type: Optional[str] = None

    def __repr__(self):
        return f"Room({self.room_id})"


@dataclass
class Assignment:
    """Maps a class session to a time slot and room."""
    session: ClassSession
    slot: TimeSlot
    room: Room

    def __repr__(self):
        return f"Assign({self.session.session_id} -> {self.slot} in {self.room})"


@dataclass
class TimetableData:
    """Container for all input data needed to generate a timetable."""
    sessions: list[ClassSession] = field(default_factory=list)
    slots: list[TimeSlot] = field(default_factory=list)
    rooms: list[Room] = field(default_factory=list)

    @property
    def num_sessions(self) -> int:
        return len(self.sessions)

    @property
    def num_slots(self) -> int:
        return len(self.slots)

    @property
    def num_rooms(self) -> int:
        return len(self.rooms)

    @property
    def total_capacity(self) -> int:
        """Total number of (slot, room) combinations available."""
        return self.num_slots * self.num_rooms

    def is_feasible(self) -> bool:
        """Check if there are enough slot-room combos for all sessions."""
        return self.total_capacity >= self.num_sessions

    def summary(self) -> str:
        """Return a human-readable summary of the data."""
        days = sorted(set(s.day for s in self.slots))
        periods = sorted(set(s.period for s in self.slots))
        faculty = sorted(set(s.faculty for s in self.sessions))
        groups = sorted(set(s.student_group for s in self.sessions))

        lines = [
            "=" * 50,
            "TIMETABLE DATA SUMMARY",
            "=" * 50,
            f"Sessions:       {self.num_sessions}",
            f"Time Slots:     {self.num_slots} ({len(days)} days x {len(periods)} periods)",
            f"Rooms:          {self.num_rooms}",
            f"Total Capacity: {self.total_capacity} (slot x room combos)",
            f"Feasible:       {'Yes' if self.is_feasible() else 'NO - not enough slots!'}",
            f"",
            f"Days:           {', '.join(days)}",
            f"Periods/day:    {len(periods)}",
            f"Faculty:        {', '.join(faculty)}",
            f"Student Groups: {', '.join(groups)}",
            f"Rooms:          {', '.join(r.room_id for r in self.rooms)}",
            "=" * 50,
        ]
        return "\n".join(lines)
