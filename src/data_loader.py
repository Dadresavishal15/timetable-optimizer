"""
data_loader.py - Load timetable data from JSON or create it programmatically

Handles:
- Loading sample data from JSON file
- Converting raw dicts into typed data models
- Generating TimeSlots from days x periods
- Validating that loaded data is structurally complete
"""

import json
from pathlib import Path

from src.models import ClassSession, TimeSlot, Room, TimetableData


def load_from_json(filepath: str | Path) -> TimetableData:
    """
    Load timetable input data from a JSON file.

    Args:
        filepath: Path to the JSON file containing sessions, rooms, days, etc.

    Returns:
        TimetableData object with all sessions, slots, and rooms populated.
    """
    filepath = Path(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Build rooms
    rooms = [
        Room(
            room_id=r["room_id"],
            capacity=r.get("capacity"),
            room_type=r.get("room_type"),
        )
        for r in raw["rooms"]
    ]

    # Build time slots (day x period combinations)
    days = raw["days"]
    periods_per_day = raw["periods_per_day"]
    slots = []
    slot_id = 0
    for day in days:
        for period in range(1, periods_per_day + 1):
            slots.append(TimeSlot(slot_id=slot_id, day=day, period=period))
            slot_id += 1

    # Build class sessions
    sessions = [
        ClassSession(
            session_id=s["session_id"],
            subject=s["subject"],
            faculty=s["faculty"],
            student_group=s["student_group"],
            duration_slots=s.get("duration_slots", 1),
            required_room_type=s.get("required_room_type"),
        )
        for s in raw["sessions"]
    ]

    return TimetableData(sessions=sessions, slots=slots, rooms=rooms)


def validate_data(data: TimetableData) -> list[str]:
    """
    Check the loaded data for structural problems.

    Returns:
        A list of warning/error messages. Empty list means data is OK.
    """
    issues = []

    if not data.sessions:
        issues.append("ERROR: No class sessions defined.")
    if not data.slots:
        issues.append("ERROR: No time slots defined.")
    if not data.rooms:
        issues.append("ERROR: No rooms defined.")

    if not data.is_feasible():
        issues.append(
            f"WARNING: Not enough capacity. "
            f"{data.num_sessions} sessions need scheduling but only "
            f"{data.total_capacity} (slot x room) combinations exist."
        )

    # Check for duplicate session IDs
    ids = [s.session_id for s in data.sessions]
    if len(ids) != len(set(ids)):
        issues.append("ERROR: Duplicate session IDs found.")

    # Check for duplicate slot IDs
    slot_ids = [s.slot_id for s in data.slots]
    if len(slot_ids) != len(set(slot_ids)):
        issues.append("ERROR: Duplicate slot IDs found.")

    # Check for duplicate room IDs
    room_ids = [r.room_id for r in data.rooms]
    if len(room_ids) != len(set(room_ids)):
        issues.append("ERROR: Duplicate room IDs found.")

    return issues


# ─── Quick test: run this file directly ─────────────────────────────
if __name__ == "__main__":
    data_path = Path(__file__).parent.parent / "data" / "sample_data.json"
    data = load_from_json(data_path)

    # Validate
    issues = validate_data(data)
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  • {issue}")
    else:
        print("[OK] Data validation passed.\n")

    # Summary
    print(data.summary())

    # List all sessions
    print("\nClass Sessions:")
    for s in data.sessions:
        print(f"  {s}")

    # List all slots
    print(f"\nTime Slots ({data.num_slots} total):")
    for slot in data.slots:
        print(f"  {slot}")

    # List all rooms
    print(f"\nRooms ({data.num_rooms} total):")
    for room in data.rooms:
        print(f"  {room}")
