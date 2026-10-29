"""
timetable_view.py - Display timetables in readable grid format

Provides:
- Console grid view (days as columns, periods as rows)
- Per-group timetable view
- Per-faculty timetable view
- Conflict highlighting
- Pandas DataFrame export for Streamlit
"""

from collections import defaultdict

import pandas as pd

from src.models import Assignment, TimetableData
from src.fitness import evaluate_fitness, FitnessBreakdown


# ─── Grid builders ──────────────────────────────────────────────────

def _build_grid_data(
    assignments: list[Assignment],
    data: TimetableData,
) -> dict[tuple[str, int], list[Assignment]]:
    """
    Organize assignments into a (day, period) -> [assignments] lookup.

    Returns:
        Dict mapping (day, period) to list of assignments in that slot.
    """
    grid: dict[tuple[str, int], list[Assignment]] = defaultdict(list)
    for a in assignments:
        grid[(a.slot.day, a.slot.period)].append(a)
    return grid


def _get_days_and_periods(data: TimetableData) -> tuple[list[str], list[int]]:
    """Extract sorted unique days and periods from the data."""
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                 "Saturday", "Sunday"]
    days = sorted(set(s.day for s in data.slots),
                  key=lambda d: day_order.index(d) if d in day_order else 99)
    periods = sorted(set(s.period for s in data.slots))
    return days, periods


# ─── Console display ───────────────────────────────────────────────

def format_master_grid(
    assignments: list[Assignment],
    data: TimetableData,
) -> str:
    """
    Format the full timetable as a text grid.
    Each cell shows: Subject (Group) [Room]

    Returns:
        Multi-line string with the formatted grid.
    """
    grid = _build_grid_data(assignments, data)
    days, periods = _get_days_and_periods(data)

    col_width = 30
    lines = []

    # Header
    header = f"{'Period':<10}" + "".join(f"{d:<{col_width}}" for d in days)
    lines.append("=" * len(header))
    lines.append("MASTER TIMETABLE")
    lines.append("=" * len(header))
    lines.append(header)
    lines.append("-" * len(header))

    # Rows
    for period in periods:
        row_cells = []
        for day in days:
            cell_assignments = grid.get((day, period), [])
            if not cell_assignments:
                row_cells.append("---")
            else:
                entries = []
                for a in cell_assignments:
                    entry = f"{a.session.subject[:12]} ({a.session.student_group}) [{a.room.room_id}]"
                    entries.append(entry)
                row_cells.append(" | ".join(entries))

        row = f"{'P' + str(period):<10}" + "".join(
            f"{cell:<{col_width}}" for cell in row_cells
        )
        lines.append(row)

    lines.append("=" * len(header))
    return "\n".join(lines)


def format_group_timetable(
    assignments: list[Assignment],
    data: TimetableData,
    group: str,
) -> str:
    """
    Format the timetable for a specific student group.
    Each cell shows: Subject - Faculty [Room]
    """
    group_assignments = [a for a in assignments if a.session.student_group == group]
    grid = defaultdict(list)
    for a in group_assignments:
        grid[(a.slot.day, a.slot.period)].append(a)

    days, periods = _get_days_and_periods(data)
    col_width = 28
    lines = []

    header = f"{'Period':<10}" + "".join(f"{d:<{col_width}}" for d in days)
    lines.append(f"\n--- Timetable for {group} ---")
    lines.append(header)
    lines.append("-" * len(header))

    for period in periods:
        row_cells = []
        for day in days:
            cell_assignments = grid.get((day, period), [])
            if not cell_assignments:
                row_cells.append("---")
            elif len(cell_assignments) == 1:
                a = cell_assignments[0]
                row_cells.append(f"{a.session.subject[:12]} [{a.room.room_id}]")
            else:
                # Conflict! Multiple classes for same group
                entries = [f"*{a.session.subject[:10]}*" for a in cell_assignments]
                row_cells.append("CLASH: " + ",".join(entries))

        row = f"{'P' + str(period):<10}" + "".join(
            f"{cell:<{col_width}}" for cell in row_cells
        )
        lines.append(row)

    return "\n".join(lines)


def format_faculty_timetable(
    assignments: list[Assignment],
    data: TimetableData,
    faculty: str,
) -> str:
    """
    Format the timetable for a specific faculty member.
    Each cell shows: Subject (Group) [Room]
    """
    fac_assignments = [a for a in assignments if a.session.faculty == faculty]
    grid = defaultdict(list)
    for a in fac_assignments:
        grid[(a.slot.day, a.slot.period)].append(a)

    days, periods = _get_days_and_periods(data)
    col_width = 28
    lines = []

    header = f"{'Period':<10}" + "".join(f"{d:<{col_width}}" for d in days)
    lines.append(f"\n--- Timetable for {faculty} ---")
    lines.append(header)
    lines.append("-" * len(header))

    for period in periods:
        row_cells = []
        for day in days:
            cell_assignments = grid.get((day, period), [])
            if not cell_assignments:
                row_cells.append("---")
            elif len(cell_assignments) == 1:
                a = cell_assignments[0]
                row_cells.append(f"{a.session.subject[:12]} ({a.session.student_group})")
            else:
                entries = [f"*{a.session.subject[:10]}*" for a in cell_assignments]
                row_cells.append("CLASH: " + ",".join(entries))

        row = f"{'P' + str(period):<10}" + "".join(
            f"{cell:<{col_width}}" for cell in row_cells
        )
        lines.append(row)

    return "\n".join(lines)


# ─── Pandas DataFrame (for Streamlit) ──────────────────────────────

def to_master_dataframe(
    assignments: list[Assignment],
    data: TimetableData,
) -> pd.DataFrame:
    """
    Convert timetable to a Pandas DataFrame.
    Rows = periods, Columns = days, Cells = session info strings.
    """
    grid = _build_grid_data(assignments, data)
    days, periods = _get_days_and_periods(data)

    rows = []
    for period in periods:
        row = {"Period": f"P{period}"}
        for day in days:
            cell_assignments = grid.get((day, period), [])
            if not cell_assignments:
                row[day] = ""
            else:
                entries = []
                for a in cell_assignments:
                    entries.append(
                        f"{a.session.subject} ({a.session.student_group}) [{a.room.room_id}]"
                    )
                row[day] = "\n".join(entries)
        rows.append(row)

    return pd.DataFrame(rows).set_index("Period")


def to_group_dataframe(
    assignments: list[Assignment],
    data: TimetableData,
    group: str,
) -> pd.DataFrame:
    """
    Convert a single group's timetable to a Pandas DataFrame.
    """
    group_assignments = [a for a in assignments if a.session.student_group == group]
    grid = defaultdict(list)
    for a in group_assignments:
        grid[(a.slot.day, a.slot.period)].append(a)

    days, periods = _get_days_and_periods(data)

    rows = []
    for period in periods:
        row = {"Period": f"P{period}"}
        for day in days:
            cell_assignments = grid.get((day, period), [])
            if not cell_assignments:
                row[day] = ""
            elif len(cell_assignments) == 1:
                a = cell_assignments[0]
                row[day] = f"{a.session.subject}\n{a.session.faculty}\n[{a.room.room_id}]"
            else:
                row[day] = "CLASH!"
        rows.append(row)

    return pd.DataFrame(rows).set_index("Period")


# ─── Summary display ───────────────────────────────────────────────

def format_full_report(
    assignments: list[Assignment],
    data: TimetableData,
    fitness: FitnessBreakdown | None = None,
) -> str:
    """
    Generate a complete human-readable report with:
    - Master grid
    - Per-group grids
    - Per-faculty grids
    - Fitness summary
    """
    lines = []

    # Master grid
    lines.append(format_master_grid(assignments, data))

    # Per-group timetables
    groups = sorted(set(s.student_group for s in data.sessions))
    for group in groups:
        lines.append(format_group_timetable(assignments, data, group))

    # Per-faculty timetables
    faculty_list = sorted(set(s.faculty for s in data.sessions))
    for faculty in faculty_list:
        lines.append(format_faculty_timetable(assignments, data, faculty))

    # Fitness summary
    if fitness is None:
        fitness = evaluate_fitness(assignments)
    lines.append(f"\n{fitness.summary()}")

    return "\n".join(lines)


# ─── Quick test: run this file directly ─────────────────────────────
if __name__ == "__main__":
    from pathlib import Path
    from src.data_loader import load_from_json
    from src.genetic_algorithm import run_genetic_algorithm, GAConfig

    data_path = Path(__file__).parent.parent / "data" / "sample_data.json"
    data = load_from_json(data_path)

    # Run GA
    config = GAConfig(population_size=100, generations=100, random_seed=42)
    result = run_genetic_algorithm(data, config)

    # Show full report
    report = format_full_report(result.best_assignments, data, result.best_fitness)
    print(report)
