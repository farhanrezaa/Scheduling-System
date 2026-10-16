"""Education Institution Management — Streamlit MVP entrypoint."""

import streamlit as st

st.set_page_config(
    page_title="Education Institution Management",
    page_icon="📚",
    layout="wide",
)

from payment_tracker import render_payment_tracker  # noqa: E402
from salary_tracker import render_salary_tracker  # noqa: E402
from scheduling_system import render_scheduling_tab  # noqa: E402

st.title("Education Institution Management")
st.caption("MVP — Scheduling · Teacher Salaries · Student Payments")

tab_scheduling, tab_salary, tab_payment = st.tabs(
    ["Scheduling System", "Teacher Salary Tracker", "Payment Tracker"]
)

with tab_scheduling:
    render_scheduling_tab()

with tab_salary:
    render_salary_tracker()

with tab_payment:
    render_payment_tracker()
