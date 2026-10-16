"""Education Institution Management — Streamlit MVP entrypoint."""

import streamlit as st

st.set_page_config(
    page_title="Education Institution Management",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

from payment_tracker import render_payment_tracker  # noqa: E402
from salary_tracker import render_salary_tracker  # noqa: E402
from scheduling_system import display_logo, render_scheduling_tab  # noqa: E402

VIEWS = [
    "Scheduling System",
    "Teacher Salary Tracker",
    "Payment Tracker",
]

# Header: WIDYS logo beside page title
logo_col, title_col = st.columns([1, 5], vertical_alignment="center")
with logo_col:
    display_logo(width=140)
with title_col:
    st.title("Education Institution Management")
    st.caption("MVP — Scheduling · Teacher Salaries · Student Payments")

# Radio (not st.tabs) so only the active view runs — gates sidebar widgets
view = st.radio(
    "Section",
    VIEWS,
    horizontal=True,
    label_visibility="collapsed",
    key="main_view",
)

is_scheduling = view == "Scheduling System"

# Hide sidebar chrome entirely when not on Scheduling (no empty sidebar)
if is_scheduling:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: block; }
        section[data-testid="stSidebar"] { min-width: 21rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    # Expand sidebar when entering Scheduling so Controls are visible
    if st.session_state.get("_sidebar_for_view") != view:
        st.session_state._sidebar_for_view = view
else:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            min-width: 0 !important;
            height: 0 !important;
            overflow: hidden !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state._sidebar_for_view = view

st.divider()

if is_scheduling:
    render_scheduling_tab()
elif view == "Teacher Salary Tracker":
    render_salary_tracker()
else:
    render_payment_tracker()
