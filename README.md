# Automatic Timetable Conflict Minimizer 📅

A **Soft Computing** project demonstrating timetable scheduling optimization using **Genetic Algorithms (DEAP)**, **Pandas**, and **Streamlit**.

---

## 📌 Project Overview
Scheduling academic timetables is an NP-hard combinatorial optimization problem. This project generates conflict-free schedules by assigning class sessions (subject, faculty, student group) to time slots and classrooms while minimizing hard and soft clashes.

### Core Soft Computing Concepts
- **Genetic Algorithm (GA)**: Evolutionary search inspired by natural selection.
- **Genome Representation**: An individual is a list of `(slot_id, room_id)` pairs, one per class session.
- **Fitness Function**: Penalty-based minimization scoring hard clashes (100 pts) and soft consecutive classes (2 pts).
- **Genetic Operators**:
  - **Selection**: Tournament selection ($k=3$)
  - **Crossover**: Uniform crossover ($p_c = 0.7$)
  - **Mutation**: Random gene reassignment ($p_m = 0.2$)
  - **Elitism**: Top 5 candidate schedules directly cloned into next generation
  - **Early Stopping**: Halts as soon as a 0-penalty schedule is found.

---

## 🚀 Benchmark & Evaluation Results (10 Random Seeds)

Evaluating across 10 random seeds comparing the baseline **Random Assignment** vs the **Genetic Algorithm**:

| Metric | Random Timetable | Genetic Algorithm (Ours) |
|---|:---:|:---:|
| **Success Rate (0 Clashes)** | 30.0% (3/10) | **100.0% (10/10)** |
| **Mean Hard Conflicts** | 1.1 (max 3) | **0.0 (max 0)** |
| **Mean Total Penalty** | 112.6 (max 304) | **0.0 (max 0)** |
| **Mean Runtime** | < 0.01 ms | ~5.3 ms |

> The Genetic Algorithm achieves a **100% collision-free timetable generation rate** within milliseconds on CPU without requiring GPU acceleration.

---

## 📂 Project Structure

```text
timetable_optimizer/
├── app.py                     # Interactive Streamlit web interface
├── evaluate.py                # 10-seed benchmarking evaluation script
├── requirements.txt           # Python dependencies
├── evaluation_results.csv     # Exported benchmark CSV
├── README.md                  # Project documentation
├── data/
│   └── sample_data.json       # Configurable academic sessions, rooms, slots
├── src/
│   ├── __init__.py
│   ├── models.py              # Dataclasses (ClassSession, TimeSlot, Room, TimetableData)
│   ├── data_loader.py         # JSON loader & feasibility validator
│   ├── validator.py           # Conflict detector (faculty, room, student group)
│   ├── fitness.py             # Weighted penalty fitness function
│   ├── random_timetable.py    # Random generation baseline
│   ├── genetic_algorithm.py   # DEAP-based GA implementation
│   └── timetable_view.py      # Console & DataFrame timetable formatting
└── tests/
    ├── __init__.py
    ├── test_validator.py      # 9 unit tests for constraint checking
    └── test_fitness.py        # 11 unit tests for scoring logic
```

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)

### 1. Install Dependencies
```bash
cd timetable_optimizer
pip install -r requirements.txt
```

### 2. Run Unit Tests (20/20 Passing)
```bash
pytest tests/ -v
```

### 3. Run Benchmark Evaluation
```bash
python evaluate.py
```

### 4. Launch the Streamlit Web Application
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🖥️ Streamlit Features
- **Sidebar Tuning**: Adjust population size, max generations, crossover rate, mutation rate, and conflict weights interactively.
- **One-Click Generation**: Runs GA and random baseline side-by-side.
- **Conflict Highlighting**: Validates hard constraints and flags any remaining double-bookings.
- **Multi-Tab Schedules**: View master timetable, per-student group timetable (`CS-A`, `CS-B`, `IT-A`), and per-faculty schedules.
- **Fitness History Chart**: Real-time line plot showing population best, average, and worst penalties over generations.
- **CSV Export**: Download generated schedules directly.

---

## 🧩 Constraints Modeled

### Hard Constraints (Penalty: 100 each)
1. **Faculty Conflict**: A faculty member cannot be scheduled in two places at the same time slot.
2. **Room Double-Booking**: A room cannot host more than one session in the same slot.
3. **Student Group Clashes**: A student group cannot have two classes simultaneously.

### Soft Constraints (Penalty: 2 each)
1. **Consecutive Classes**: Discourages back-to-back classes for both faculty and students.

---

## 🔮 Limitations & Future Enhancements
- Support for multi-slot lab sessions ($>1$ period).
- Room type matching (e.g. lab vs lecture hall capacity matching).
- Custom instructor unavailabilities (off-periods/days).
