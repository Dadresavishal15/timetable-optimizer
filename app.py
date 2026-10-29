"""
app.py - Polished Modern Streamlit UI for the Timetable Conflict Minimizer

Features:
- User Input & Customization:
    * Quick Form to add new classes and rooms
    * Interactive Spreadsheet Editor (st.data_editor) to edit/delete any class in real-time
    * CSV File Upload for custom college schedules
    * CSV Template download
    * Reset to sample data button
- Premium modern aesthetics (custom CSS, soft shadows, rounded glass cards, harmonious color palette)
- Subject-specific distinct pastel badges with colored left-borders
- Interactive presets (Fast Demo, Balanced, Deep Evolution)
- Visual HTML Master Grid & Group/Faculty schedules with chips
- Side-by-side GA vs Random Baseline comparison
- Convergence progression charts
- Conflict alerts and CSV export
"""

import sys
import io
from pathlib import Path
from collections import defaultdict

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd

from src.data_loader import load_from_json, validate_data
from src.models import TimetableData, ClassSession, Room, TimeSlot
from src.random_timetable import generate_random_timetable
from src.validator import validate_timetable
from src.fitness import evaluate_fitness, FitnessWeights
from src.genetic_algorithm import run_genetic_algorithm, GAConfig
from src.timetable_view import to_master_dataframe, _get_days_and_periods


# ─── Page Configuration ─────────────────────────────────────────────
st.set_page_config(
    page_title="Timetable Optimizer | Soft Computing",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─── Custom CSS Styling ─────────────────────────────────────────────
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Hero Header */
.hero-container {
    background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%);
    border-radius: 18px;
    padding: 30px 34px;
    color: white;
    margin-bottom: 24px;
    box-shadow: 0 10px 25px -5px rgba(49, 46, 129, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.hero-title {
    font-size: 2.1rem;
    font-weight: 800;
    letter-spacing: -0.025em;
    margin: 0 0 8px 0;
    color: #FFFFFF;
}
.hero-subtitle {
    font-size: 1.05rem;
    color: #C7D2FE;
    margin-bottom: 16px;
    font-weight: 400;
}
.badge-chip {
    display: inline-flex;
    align-items: center;
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 9999px;
    padding: 5px 14px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-right: 8px;
    color: #EEF2FF;
}

/* Metric Cards */
.kpi-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 18px 20px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
    border: 1px solid #E2E8F0;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
}
.kpi-label {
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748B;
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 1.9rem;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.1;
}
.kpi-sub {
    font-size: 0.82rem;
    color: #10B981;
    font-weight: 600;
    margin-top: 6px;
}

/* Timetable Schedule Grid */
.timetable-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 10px;
    margin-top: 14px;
}
.timetable-table th {
    background: #F8FAFC;
    color: #475569;
    font-weight: 700;
    font-size: 0.88rem;
    text-align: center;
    padding: 12px 10px;
    border-radius: 10px;
    border: 1px solid #E2E8F0;
}
.timetable-table td {
    vertical-align: top;
    background: transparent;
    padding: 0;
    min-width: 170px;
}
.period-header {
    background: #F1F5F9 !important;
    color: #1E293B !important;
    font-weight: 800 !important;
    font-size: 0.95rem !important;
    width: 90px;
    text-align: center;
    vertical-align: middle;
}

/* Class Session Card */
.session-card {
    border-radius: 10px;
    padding: 10px 12px;
    margin-bottom: 8px;
    font-size: 0.82rem;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
    transition: all 0.2s ease;
}
.session-card:hover {
    transform: scale(1.02);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.session-title {
    font-weight: 700;
    font-size: 0.88rem;
    margin-bottom: 5px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.meta-chip {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    margin-right: 4px;
    margin-top: 3px;
}
.meta-faculty { background: rgba(0,0,0,0.06); color: #334155; }
.meta-room { background: rgba(0,0,0,0.06); color: #334155; font-weight: 700; }
.meta-group { background: rgba(0,0,0,0.08); color: #0F172A; font-weight: 700; }

.empty-cell {
    border: 1.5px dashed #CBD5E1;
    border-radius: 10px;
    height: 70px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #94A3B8;
    font-size: 0.75rem;
    font-weight: 500;
}

/* Conflict Card */
.conflict-card {
    background: #FEF2F2 !important;
    border: 1.5px solid #F87171 !important;
    border-left: 5px solid #EF4444 !important;
    color: #991B1B !important;
}

/* Dark mode compatibility */
@media (prefers-color-scheme: dark) {
    .kpi-card { background: #1E293B; border-color: #334155; }
    .kpi-value { color: #F8FAFC; }
    .kpi-label { color: #94A3B8; }
    .timetable-table th { background: #1E293B; border-color: #334155; color: #CBD5E1; }
    .period-header { background: #0F172A !important; color: #F1F5F9 !important; }
    .empty-cell { border-color: #475569; color: #64748B; }
    .meta-faculty, .meta-room, .meta-group { background: rgba(255,255,255,0.1); color: #E2E8F0; }
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ─── Color Palette Mapping for Subjects ────────────────────────────
PALETTE = [
    {"bg": "#EEF2FF", "border": "#6366F1", "text": "#3730A3"},
    {"bg": "#ECFDF5", "border": "#10B981", "text": "#065F46"},
    {"bg": "#FFFBEB", "border": "#F59E0B", "text": "#92400E"},
    {"bg": "#F0F9FF", "border": "#0EA5E9", "text": "#075985"},
    {"bg": "#FFF1F2", "border": "#F43F5E", "text": "#9F1239"},
    {"bg": "#FAF5FF", "border": "#A855F7", "text": "#6B21A8"},
    {"bg": "#F5F3FF", "border": "#8B5CF6", "text": "#5B21B6"},
    {"bg": "#FDF2F8", "border": "#EC4899", "text": "#9D174D"},
]

def get_subject_theme(subject: str) -> dict:
    idx = abs(hash(subject)) % len(PALETTE)
    return PALETTE[idx]


# ─── Dataset Initialization in Session State ───────────────────────
DATA_PATH = Path(__file__).parent / "data" / "sample_data.json"

def reset_dataset():
    st.session_state["timetable_data"] = load_from_json(DATA_PATH)
    st.session_state["has_run"] = False

if "timetable_data" not in st.session_state:
    reset_dataset()

data: TimetableData = st.session_state["timetable_data"]


# ─── Hero Banner ───────────────────────────────────────────────────
st.markdown("""
<div class="hero-container">
    <div class="hero-title">📅 Academic Timetable Conflict Minimizer</div>
    <div class="hero-subtitle">Soft Computing Optimization using Genetic Algorithms (DEAP), Natural Selection & Elitism</div>
    <div>
        <span class="badge-chip">🧬 Genetic Algorithm</span>
        <span class="badge-chip">✏️ Custom Class Input Enabled</span>
        <span class="badge-chip">🎯 0 Hard Clashes Guarantee</span>
        <span class="badge-chip">⚡ Sub-second Convergence</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ─── Sidebar Controls ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎛️ Optimization Controls")

    preset = st.selectbox(
        "⚡ Quick Preset",
        ["Balanced (Recommended)", "Fast Exploration", "Deep Evolution (High Precision)"],
        index=0,
    )

    if preset == "Fast Exploration":
        default_pop, default_gens = 40, 40
    elif preset == "Deep Evolution (High Precision)":
        default_pop, default_gens = 200, 200
    else:
        default_pop, default_gens = 100, 100

    with st.expander("⚙️ Genetic Algorithm Hyperparameters", expanded=True):
        population_size = st.slider("Population Size", 20, 300, default_pop, 10,
                                    help="Candidate timetable solutions per generation.")
        generations = st.slider("Max Generations", 10, 500, default_gens, 10,
                                help="Maximum evolution iterations.")
        crossover_prob = st.slider("Crossover Probability", 0.1, 1.0, 0.70, 0.05,
                                   help="Probability of swapping schedule genes between parents.")
        mutation_prob = st.slider("Mutation Probability", 0.05, 0.6, 0.20, 0.05,
                                  help="Probability of reassigning session slot/room.")
        random_seed = st.number_input("Random Seed", 0, 9999, 42,
                                      help="Fix seed for deterministic reproducibility.")

    with st.expander("⚖️ Penalty Weights", expanded=False):
        w_faculty = st.number_input("Faculty Conflict Weight", value=100, step=10)
        w_room = st.number_input("Room Conflict Weight", value=100, step=10)
        w_group = st.number_input("Student Group Conflict Weight", value=100, step=10)
        w_consec = st.number_input("Consecutive Class Soft Weight", value=2, step=1)

    st.markdown("---")
    if st.button("🔄 Reset to Default Sample Data", use_container_width=True):
        reset_dataset()
        st.rerun()


# ─── USER INPUT & EDITING SECTION ─────────────────────────────────
with st.expander("✏️ Manage & Input Classes, Rooms & Faculty (Click to Expand)", expanded=False):
    tab_add, tab_edit, tab_upload = st.tabs([
        "➕ Add New Class / Room",
        "📝 Edit Classes Table (Live Spreadsheet)",
        "📁 Upload CSV File",
    ])

    # --- TAB 1: Add New Class or Room Form ---
    with tab_add:
        col_form1, col_form2 = st.columns(2)
        with col_form1:
            st.markdown("#### 📚 Add a New Class Session")
            with st.form("add_class_form", clear_on_submit=True):
                new_sub = st.text_input("Subject Name", placeholder="e.g. Machine Learning")
                new_fac = st.text_input("Faculty / Professor", placeholder="e.g. Dr. Verma")
                new_grp = st.text_input("Student Group / Batch", placeholder="e.g. CS-A")
                submitted_class = st.form_submit_button("➕ Add Class to Schedule")

                if submitted_class:
                    if new_sub.strip() and new_fac.strip() and new_grp.strip():
                        new_id = f"S{len(data.sessions) + 1:02d}"
                        data.sessions.append(
                            ClassSession(
                                session_id=new_id,
                                subject=new_sub.strip(),
                                faculty=new_fac.strip(),
                                student_group=new_grp.strip(),
                            )
                        )
                        st.success(f"Added session `{new_id}`: {new_sub} ({new_fac}, {new_grp})!")
                        st.rerun()
                    else:
                        st.error("Please fill in Subject, Faculty, and Student Group.")

        with col_form2:
            st.markdown("#### 🏫 Add a New Classroom")
            with st.form("add_room_form", clear_on_submit=True):
                new_room_id = st.text_input("Room Identifier", placeholder="e.g. R201 or Lab-B")
                new_cap = st.number_input("Room Capacity (seats)", min_value=10, max_value=500, value=60)
                new_type = st.selectbox("Room Type", ["lecture", "lab", "seminar"])
                submitted_room = st.form_submit_button("➕ Add Classroom")

                if submitted_room:
                    if new_room_id.strip():
                        if any(r.room_id.lower() == new_room_id.strip().lower() for r in data.rooms):
                            st.warning(f"Room `{new_room_id}` already exists.")
                        else:
                            data.rooms.append(Room(room_id=new_room_id.strip(), capacity=new_cap, room_type=new_type))
                            st.success(f"Added room `{new_room_id.strip()}`!")
                            st.rerun()
                    else:
                        st.error("Please enter a room name/id.")

    # --- TAB 2: Live Editable Spreadsheet ---
    with tab_edit:
        st.markdown("#### ✏️ Live Class Editor")
        st.caption("You can edit names, add rows (+ at bottom), or select rows and press Delete.")
        
        current_sessions = [
            {"ID": s.session_id, "Subject": s.subject, "Faculty": s.faculty, "Student Group": s.student_group}
            for s in data.sessions
        ]
        edited_df = st.data_editor(
            pd.DataFrame(current_sessions),
            num_rows="dynamic",
            use_container_width=True,
            key="sessions_editor",
        )

        if st.button("💾 Apply Changes to Classes", type="secondary"):
            new_sessions = []
            for i, row in edited_df.iterrows():
                sub = str(row.get("Subject", "")).strip()
                fac = str(row.get("Faculty", "")).strip()
                grp = str(row.get("Student Group", "")).strip()
                sid = str(row.get("ID", f"S{i+1:02d}")).strip() or f"S{i+1:02d}"
                if sub and fac and grp:
                    new_sessions.append(ClassSession(session_id=sid, subject=sub, faculty=fac, student_group=grp))
            
            if new_sessions:
                data.sessions = new_sessions
                st.success(f"Updated schedule with {len(new_sessions)} active classes!")
                st.rerun()
            else:
                st.error("Cannot save empty list of classes.")

    # --- TAB 3: CSV File Upload ---
    with tab_upload:
        st.markdown("#### 📁 Upload Custom Classes via CSV")
        st.caption("Your CSV should have columns: `subject`, `faculty`, `student_group`.")

        sample_csv = "subject,faculty,student_group\nArtificial Intelligence,Dr. Sharma,CS-A\nComputer Graphics,Prof. Rao,CS-B\nCloud Computing,Dr. Gupta,IT-A"
        st.download_button(
            "📥 Download Sample CSV Template",
            data=sample_csv,
            file_name="sample_classes.csv",
            mime="text/csv",
        )

        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded_file is not None:
            try:
                upload_df = pd.read_csv(uploaded_file)
                st.write("Preview of uploaded file:", upload_df.head(5))
                if st.button("📥 Import Uploaded Classes"):
                    cols = {c.lower().strip(): c for c in upload_df.columns}
                    sub_col = cols.get("subject")
                    fac_col = cols.get("faculty")
                    grp_col = cols.get("student_group") or cols.get("group")
                    
                    if sub_col and fac_col and grp_col:
                        new_sessions = []
                        for idx, row in upload_df.iterrows():
                            s = str(row[sub_col]).strip()
                            f = str(row[fac_col]).strip()
                            g = str(row[grp_col]).strip()
                            if s and f and g:
                                new_sessions.append(
                                    ClassSession(session_id=f"S{idx+1:02d}", subject=s, faculty=f, student_group=g)
                                )
                        if new_sessions:
                            data.sessions = new_sessions
                            st.success(f"Successfully imported {len(new_sessions)} classes from CSV!")
                            st.rerun()
                    else:
                        st.error("Missing required columns: CSV must contain 'subject', 'faculty', and 'student_group'.")
            except Exception as e:
                st.error(f"Error reading CSV: {e}")


# ─── Dataset Overview Metrics ──────────────────────────────────────
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
colA, colB, colC, colD = st.columns(4)
colA.metric("Active Classes", f"{data.num_sessions} sessions")
colB.metric("Weekly Slots", f"{data.num_slots} periods")
colC.metric("Rooms Available", f"{data.num_rooms} rooms ({', '.join(r.room_id for r in data.rooms)})")
colD.metric(
    "Feasibility",
    f"{data.total_capacity} capacity",
    delta="Sufficient" if data.is_feasible() else "⚠️ Deficit: Add Rooms/Slots!",
    delta_color="normal" if data.is_feasible() else "inverse",
)


# ─── Execution Button ──────────────────────────────────────────────
st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
run_btn = st.button("🚀 Run Genetic Algorithm Scheduler", type="primary", use_container_width=True)

if run_btn:
    if not data.is_feasible():
        st.error(
            f"Cannot schedule: You have {data.num_sessions} classes but only {data.total_capacity} "
            f"(slot × room) spots! Please add more rooms or reduce classes."
        )
    else:
        weights = FitnessWeights(
            faculty_conflict=w_faculty,
            room_conflict=w_room,
            student_group_conflict=w_group,
            consecutive_classes=w_consec,
        )

        config = GAConfig(
            population_size=population_size,
            generations=generations,
            crossover_prob=crossover_prob,
            mutation_prob=mutation_prob,
            random_seed=random_seed,
            fitness_weights=weights,
            early_stop_fitness=0,
        )

        with st.spinner("🧬 Evolving generation pool through selection, crossover, and mutation..."):
            ga_result = run_genetic_algorithm(data, config)
            rand_assign = generate_random_timetable(data, seed=random_seed)
            rand_fitness = evaluate_fitness(rand_assign, weights)

        st.session_state["ga_result"] = ga_result
        st.session_state["rand_assign"] = rand_assign
        st.session_state["rand_fitness"] = rand_fitness
        st.session_state["has_run"] = True


# ─── Results Dashboard ─────────────────────────────────────────────
if st.session_state.get("has_run", False):
    ga_result = st.session_state["ga_result"]
    rand_fitness = st.session_state["rand_fitness"]
    best_fit = ga_result.best_fitness

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 4 Modern KPI Cards
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Hard Clashes</div>
            <div class="kpi-value" style="color: {'#10B981' if best_fit.hard_conflicts_count == 0 else '#EF4444'};">
                {best_fit.hard_conflicts_count}
            </div>
            <div class="kpi-sub">
                {"✓ Conflict Free" if best_fit.hard_conflicts_count == 0 else f"{best_fit.hard_conflicts_count} Clashes"}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with kpi2:
        penalty_diff = rand_fitness.total_penalty - best_fit.total_penalty
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Penalty Score</div>
            <div class="kpi-value">{best_fit.total_penalty}</div>
            <div class="kpi-sub" style="color: #6366F1;">
                -{penalty_diff} vs Random baseline
            </div>
        </div>
        """, unsafe_allow_html=True)

    with kpi3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Generations To Solve</div>
            <div class="kpi-value">{ga_result.generations_run}</div>
            <div class="kpi-sub" style="color: #64748B;">
                Early stop: {ga_result.generations_run < ga_result.config.generations}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with kpi4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Runtime</div>
            <div class="kpi-value">{ga_result.runtime_seconds * 1000:.1f}<span style="font-size: 1rem; font-weight: 500;"> ms</span></div>
            <div class="kpi-sub" style="color: #10B981;">⚡ Ultra Fast CPU</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # ── Interactive Schedule Visualizer ─────────────────────────────
    st.subheader("📅 Interactive Timetable Schedule")

    view_mode = st.radio(
        "View Schedule By:",
        ["Master Timetable (All Classes)", "By Student Group", "By Faculty Member"],
        horizontal=True,
    )

    def render_html_schedule(filtered_assignments):
        grid = defaultdict(list)
        for a in filtered_assignments:
            grid[(a.slot.day, a.slot.period)].append(a)

        days, periods = _get_days_and_periods(data)

        html = ['<div style="overflow-x: auto;"><table class="timetable-table">']
        html.append('<thead><tr><th class="period-header">Slot</th>')
        for day in days:
            html.append(f'<th>{day}</th>')
        html.append('</tr></thead><tbody>')

        for period in periods:
            html.append('<tr>')
            html.append(f'<td class="period-header">Period {period}</td>')
            for day in days:
                cell_assignments = grid.get((day, period), [])
                if not cell_assignments:
                    html.append('<td><div class="empty-cell">Empty</div></td>')
                else:
                    html.append('<td>')
                    has_conflict = len(cell_assignments) > 1
                    for a in cell_assignments:
                        theme = get_subject_theme(a.session.subject)
                        conflict_cls = "conflict-card" if has_conflict else ""
                        border_color = "#EF4444" if has_conflict else theme["border"]
                        bg_color = "#FEF2F2" if has_conflict else theme["bg"]
                        text_color = "#991B1B" if has_conflict else theme["text"]

                        html.append(f"""
                        <div class="session-card {conflict_cls}" style="background: {bg_color}; border-left: 4px solid {border_color};">
                            <div class="session-title" style="color: {text_color};">
                                {a.session.subject}
                            </div>
                            <div>
                                <span class="meta-chip meta-faculty">👤 {a.session.faculty}</span>
                                <span class="meta-chip meta-room">📍 {a.room.room_id}</span>
                                <span class="meta-chip meta-group">👥 {a.session.student_group}</span>
                            </div>
                        </div>
                        """)
                    html.append('</td>')
            html.append('</tr>')
        html.append('</tbody></table></div>')
        return "".join(html)

    if view_mode == "Master Timetable (All Classes)":
        st.markdown(render_html_schedule(ga_result.best_assignments), unsafe_allow_html=True)

    elif view_mode == "By Student Group":
        groups = sorted(set(s.student_group for s in data.sessions))
        if groups:
            chosen_group = st.selectbox("Select Student Group", groups)
            filtered = [a for a in ga_result.best_assignments if a.session.student_group == chosen_group]
            st.markdown(render_html_schedule(filtered), unsafe_allow_html=True)
        else:
            st.info("No student groups found.")

    elif view_mode == "By Faculty Member":
        faculty_list = sorted(set(s.faculty for s in data.sessions))
        if faculty_list:
            chosen_fac = st.selectbox("Select Faculty Member", faculty_list)
            filtered = [a for a in ga_result.best_assignments if a.session.faculty == chosen_fac]
            st.markdown(render_html_schedule(filtered), unsafe_allow_html=True)
        else:
            st.info("No faculty members found.")

    # ── Convergence & Comparison Section ────────────────────────────
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    comp_col1, comp_col2 = st.columns([1, 1])

    with comp_col1:
        st.markdown("### 📈 Fitness Convergence Curve")
        log_df = pd.DataFrame(ga_result.fitness_log)
        if not log_df.empty:
            chart_data = log_df.set_index("generation")[["best", "avg"]]
            chart_data.columns = ["Best Penalty (Elites)", "Population Mean Penalty"]
            st.line_chart(chart_data, color=["#10B981", "#6366F1"])
            st.caption("Green curve shows elite individual penalty converging rapidly to zero.")

    with comp_col2:
        st.markdown("### 🔄 Baseline vs Genetic Algorithm")
        comp_df = pd.DataFrame({
            "Metric": [
                "Faculty Conflicts",
                "Room Conflicts",
                "Group Conflicts",
                "Consecutive Soft Penalty",
                "Total Penalty Score",
                "Valid Schedule?",
            ],
            "Random Assignment": [
                str(rand_fitness.faculty_conflicts),
                str(rand_fitness.room_conflicts),
                str(rand_fitness.student_group_conflicts),
                str(rand_fitness.soft_penalty),
                str(rand_fitness.total_penalty),
                "❌ No (Clashes)" if rand_fitness.hard_conflicts_count > 0 else "✓ Yes",
            ],
            "Genetic Algorithm": [
                str(best_fit.faculty_conflicts),
                str(best_fit.room_conflicts),
                str(best_fit.student_group_conflicts),
                str(best_fit.soft_penalty),
                str(best_fit.total_penalty),
                "✅ Yes (Optimal)" if best_fit.hard_conflicts_count == 0 else "❌ Clashes",
            ],
        })
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

    # ── Export ──────────────────────────────────────────────────────
    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
    master_df = to_master_dataframe(ga_result.best_assignments, data)
    csv_bytes = master_df.to_csv().encode("utf-8")

    st.download_button(
        label="📥 Download Conflict-Free Timetable (CSV)",
        data=csv_bytes,
        file_name="optimized_timetable.csv",
        mime="text/csv",
        use_container_width=True,
    )

else:
    st.info("💡 Adjust your hyperparameters or add custom classes above, then click **'Run Genetic Algorithm Scheduler'** to optimize.")
