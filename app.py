"""
AgMachineX — Streamlit prototype

Flow: Work Area -> Crop Category -> Land Size -> Task -> Machine Shortlist

All dataset values (work areas, crop categories, tasks, machinery
categories) are read from the CSV files in data/ at runtime. Nothing
about the dataset itself is hardcoded here -- only UI copy/labels.
"""

import os
import streamlit as st

from utils.data_loader import load_work_areas, load_machinery_data, validate_data_files
from utils.logic import get_crop_categories, get_filtered_tasks, get_machine_shortlist, total_land_area

# ---------------------------------------------------------------------------
# Page config + styling
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AgMachineX",
    page_icon="🚜",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def _inject_css():
    css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


_inject_css()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STEPS = [
    ("work_area", "Work Area"),
    ("crop_category", "Crop Category"),
    ("land_size", "Land Size"),
    ("task", "Tasks"),
    ("shortlist", "Machinery"),
]

UNIT_OPTIONS = ["Acres", "Hectares", "Guntas", "Bigha"]

# A light visual touch for the Work Area page only. Falls back to a
# generic icon for any value not in this map, so unmapped/renamed CSV
# values still display correctly -- this never filters or hides data.
WORK_AREA_ICONS = {
    "land preparation": "🌱",
    "irrigation": "💧",
    "crop care": "🌿",
    "harvest": "🌾",
    "precision farming": "🛰️",
    "livestock": "🐄",
    "beekeeping": "🐝",
    "gardening": "🌳",
    "landscaping": "🌳",
}


def _icon_for_work_area(value: str) -> str:
    lowered = value.lower()
    for key, icon in WORK_AREA_ICONS.items():
        if key in lowered:
            return icon
    return "🚜"


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def init_session_state():
    defaults = {
        "step": "work_area",
        "selected_work_areas": [],
        "selected_crop_categories": [],
        "crop_category_areas": {},
        "land_unit": "Acres",
        "selected_tasks": [],
        "machine_shortlist": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go_to(step_key: str):
    st.session_state["step"] = step_key


def current_step_index() -> int:
    keys = [s[0] for s in STEPS]
    return keys.index(st.session_state["step"])


# ---------------------------------------------------------------------------
# Reusable UI pieces
# ---------------------------------------------------------------------------

def render_progress():
    idx = current_step_index()
    html = ['<div class="am-progress-wrap">']
    for i, (key, label) in enumerate(STEPS):
        state = "done" if i < idx else ("current" if i == idx else "")
        dot_content = "✓" if i < idx else str(i + 1)
        html.append(
            f'<div class="am-step {state}">'
            f'<div class="dot">{dot_content}</div>'
            f'<div class="label">{label}</div>'
            f"</div>"
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_header(title: str, subtitle: str):
    st.markdown(f'<h1 class="am-title">{title}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="am-subtitle">{subtitle}</p>', unsafe_allow_html=True)


def toggle_selection(session_key: str, value: str):
    current = st.session_state[session_key]
    if value in current:
        current.remove(value)
    else:
        current.append(value)
    st.session_state[session_key] = current


def render_selectable_list(items: list[str], session_key: str, key_prefix: str, with_icons: bool = False,
                            columns: int = 2):
    """Render items as toggle 'card' buttons in a grid (default 2 per row) instead of one long stacked list."""
    selected = st.session_state[session_key]

    # Group items into rows of `columns` so the grid still reads
    # top-to-bottom, left-to-right, but takes far less vertical space.
    rows = [items[i:i + columns] for i in range(0, len(items), columns)]

    for row_items in rows:
        cols = st.columns(len(row_items))
        for col, item in zip(cols, row_items):
            with col:
                is_selected = item in selected
                prefix = "✅  " if is_selected else ("🌱  " if with_icons is False else f"{_icon_for_work_area(item)}  ")
                label = f"{prefix}{item}"
                if st.button(label, key=f"{key_prefix}_{item}", type="primary" if is_selected else "secondary",
                             use_container_width=True):
                    toggle_selection(session_key, item)
                    st.rerun()


def render_nav(back_step: str | None, on_continue, continue_label: str = "Continue →"):
    st.write("")
    st.markdown('<div class="am-nav">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])
    with col1:
        if back_step is not None:
            if st.button("← Back", key=f"back_{st.session_state['step']}", type="secondary", use_container_width=True):
                go_to(back_step)
                st.rerun()
    with col2:
        if st.button(continue_label, key=f"continue_{st.session_state['step']}", type="primary",
                     use_container_width=True):
            on_continue()
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def page_work_area(work_areas: list[str]):
    render_header(
        "What kind of farm work are you planning to do?",
        "Choose the area of work you need machinery for. You can select more than one.",
    )

    if not work_areas:
        st.warning("No work areas were found in the data file. Please contact support.")
        return

    render_selectable_list(work_areas, "selected_work_areas", "wa", with_icons=True)

    def _continue():
        if not st.session_state["selected_work_areas"]:
            st.warning("Please select at least one work area to continue.")
            return
        # Selecting a new work area can change which crop categories
        # are valid, so reset anything that depended on the old choice.
        st.session_state["selected_crop_categories"] = []
        st.session_state["crop_category_areas"] = {}
        st.session_state["selected_tasks"] = []
        st.session_state["machine_shortlist"] = []
        go_to("crop_category")
        st.rerun()

    render_nav(back_step=None, on_continue=_continue)


def page_crop_category(machinery_df):
    render_header(
        "Which type of crops are you working with?",
        "Select all that apply.",
    )

    crop_categories = get_crop_categories(machinery_df, st.session_state["selected_work_areas"])

    if not crop_categories:
        st.warning("No crop categories are available for the work area(s) you selected.")
    else:
        render_selectable_list(crop_categories, "selected_crop_categories", "cc")

    def _continue():
        if not st.session_state["selected_crop_categories"]:
            st.warning("Please select at least one crop category to continue.")
            return
        # Keep areas only for categories still selected; add blanks for new ones.
        existing = st.session_state["crop_category_areas"]
        st.session_state["crop_category_areas"] = {
            cc: existing.get(cc, None) for cc in st.session_state["selected_crop_categories"]
        }
        st.session_state["selected_tasks"] = []
        st.session_state["machine_shortlist"] = []
        go_to("land_size")
        st.rerun()

    render_nav(back_step="work_area", on_continue=_continue)


def page_land_size():
    selected_categories = st.session_state["selected_crop_categories"]
    multiple = len(selected_categories) > 1

    if multiple:
        render_header(
            "Tell us the land area for each crop category.",
            "This helps us understand the scale of the machinery you need.",
        )
    else:
        render_header(
            "How much land are you working with?",
            "This helps us understand the scale of the machinery you need.",
        )

    unit = st.selectbox("Unit", UNIT_OPTIONS, index=UNIT_OPTIONS.index(st.session_state["land_unit"])
                         if st.session_state["land_unit"] in UNIT_OPTIONS else 0)
    st.session_state["land_unit"] = unit

    areas = st.session_state["crop_category_areas"]
    for cc in selected_categories:
        current_value = areas.get(cc) or 0.0
        value = st.number_input(
            f"{cc}",
            min_value=0.0,
            value=float(current_value),
            step=0.5,
            key=f"land_{cc}",
            help=f"Land area for {cc}, in {unit.lower()}.",
        )
        areas[cc] = value
    st.session_state["crop_category_areas"] = areas

    if multiple:
        total = total_land_area(areas)
        st.markdown(
            f'<div class="am-summary-box">Total land area across all selected crop categories: '
            f'<b>{total:g} {unit.lower()}</b></div>',
            unsafe_allow_html=True,
        )

    def _continue():
        areas = st.session_state["crop_category_areas"]
        missing = [cc for cc in selected_categories if not areas.get(cc) or areas.get(cc) <= 0]
        if missing:
            st.warning("Please enter the land area before continuing.")
            return
        st.session_state["selected_tasks"] = []
        st.session_state["machine_shortlist"] = []
        go_to("task")
        st.rerun()

    render_nav(back_step="crop_category", on_continue=_continue)


def page_task(machinery_df):
    render_header(
        "What work do you need machinery for?",
        "Select all the tasks that apply.",
    )

    filtered_df, tasks = get_filtered_tasks(
        machinery_df,
        st.session_state["selected_work_areas"],
        st.session_state["selected_crop_categories"],
    )
    st.session_state["_filtered_df_cache"] = filtered_df

    if not tasks:
        st.warning("No tasks were found for the choices you made so far.")
    else:
        render_selectable_list(tasks, "selected_tasks", "tk")

    def _continue():
        if not st.session_state["selected_tasks"]:
            st.warning("Please select at least one task to continue.")
            return
        go_to("shortlist")
        st.rerun()

    render_nav(back_step="land_size", on_continue=_continue)


def page_shortlist(machinery_df):
    render_header(
        "Here's your machinery shortlist",
        "Based on the work area, crops, and tasks you selected.",
    )

    filtered_df, _ = get_filtered_tasks(
        machinery_df,
        st.session_state["selected_work_areas"],
        st.session_state["selected_crop_categories"],
    )

    shortlist = get_machine_shortlist(
        filtered_df,
        st.session_state["selected_tasks"],
        st.session_state["crop_category_areas"],
    )
    st.session_state["machine_shortlist"] = [m["machine"] for m in shortlist]

    unit = st.session_state["land_unit"].lower()

    if not shortlist:
        st.warning("No machinery categories matched your selections. Try going back and choosing different tasks.")
    else:
        for record in shortlist:
            area = record.get("applicable_area") or 0
            area_text = f" · Applicable area: {area:g} {unit}" if area else ""
            st.markdown(
                f'<div class="am-card">'
                f'<div class="am-card-title">{record["machine"]}</div>'
                f'<div class="am-card-sub">Relevant for the work you selected{area_text}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
            with st.expander("Show details"):
                st.write("**Tasks:** " + ", ".join(record["tasks"]))
                st.write("**Crop categories:** " + ", ".join(record["crop_categories"]))

    st.write("")
    st.markdown('<div class="am-nav">', unsafe_allow_html=True)
    if st.button("← Back", key="back_shortlist", type="secondary", use_container_width=True):
        go_to("task")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    validate_data_files()
    work_areas = load_work_areas()
    machinery_df = load_machinery_data()

    init_session_state()

    render_progress()

    step = st.session_state["step"]
    if step == "work_area":
        page_work_area(work_areas)
    elif step == "crop_category":
        page_crop_category(machinery_df)
    elif step == "land_size":
        page_land_size()
    elif step == "task":
        page_task(machinery_df)
    elif step == "shortlist":
        page_shortlist(machinery_df)


if __name__ == "__main__":
    main()
