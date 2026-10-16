"""Teacher Salary Tracker tab — sessions × rate, paid/unpaid."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from data_store import (
    TEACHER_SALARY_COLUMNS,
    dataframe_to_csv_bytes,
    dataframe_to_excel_bytes,
    load_csv,
    save_csv,
)

SALARY_FILE = "teacher_salaries.csv"
STATUS_OPTIONS = ["unpaid", "paid"]


def _normalize_salary_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in TEACHER_SALARY_COLUMNS:
        if col not in out.columns:
            out[col] = 0 if col in ("sessions_completed", "rate_per_session") else ""

    out["teacher_name"] = out["teacher_name"].fillna("").astype(str)
    out["sessions_completed"] = pd.to_numeric(out["sessions_completed"], errors="coerce").fillna(0).astype(int)
    out["rate_per_session"] = pd.to_numeric(out["rate_per_session"], errors="coerce").fillna(0).astype(int)
    out["status"] = (
        out["status"]
        .fillna("unpaid")
        .astype(str)
        .str.lower()
        .replace({"": "unpaid"})
        .apply(lambda s: s if s in STATUS_OPTIONS else "unpaid")
    )
    out["notes"] = out["notes"].fillna("").astype(str)
    out["amount_owed"] = out["sessions_completed"] * out["rate_per_session"]
    return out[TEACHER_SALARY_COLUMNS + ["amount_owed"]]


def _persist_columns(df: pd.DataFrame) -> pd.DataFrame:
    return _normalize_salary_df(df)[TEACHER_SALARY_COLUMNS]


def render_salary_tracker():
    st.subheader("Teacher Salary Tracker")
    st.caption(
        "Salary owed = sessions completed × rate per session. "
        "Edit the table, then save to CSV under `data/`."
    )

    if "salary_df" not in st.session_state:
        st.session_state.salary_df = _normalize_salary_df(load_csv(SALARY_FILE, TEACHER_SALARY_COLUMNS))

    with st.expander("Add teacher row"):
        with st.form("add_salary_row", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            teacher = c1.text_input("Teacher name")
            sessions = c2.number_input("Sessions completed", min_value=0, value=0, step=1)
            rate = c3.number_input("Rate per session", min_value=0, value=75000, step=5000)
            c4, c5 = st.columns(2)
            status = c4.selectbox("Status", STATUS_OPTIONS, index=0)
            notes = c5.text_input("Notes", value="")
            if st.form_submit_button("Add row"):
                if not teacher.strip():
                    st.error("Teacher name is required.")
                else:
                    new_row = {
                        "teacher_name": teacher.strip(),
                        "sessions_completed": int(sessions),
                        "rate_per_session": int(rate),
                        "status": status,
                        "notes": notes,
                    }
                    base = _persist_columns(st.session_state.salary_df)
                    st.session_state.salary_df = _normalize_salary_df(
                        pd.concat([base, pd.DataFrame([new_row])], ignore_index=True)
                    )
                    st.success(f"Added {teacher.strip()}.")
                    st.rerun()

    edited = st.data_editor(
        st.session_state.salary_df,
        column_config={
            "teacher_name": st.column_config.TextColumn("Teacher", required=True),
            "sessions_completed": st.column_config.NumberColumn("Sessions", min_value=0, step=1),
            "rate_per_session": st.column_config.NumberColumn(
                "Rate / session", min_value=0, step=1000, format="%d"
            ),
            "amount_owed": st.column_config.NumberColumn(
                "Amount owed", disabled=True, format="%d"
            ),
            "status": st.column_config.SelectboxColumn("Status", options=STATUS_OPTIONS),
            "notes": st.column_config.TextColumn("Notes"),
        },
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="salary_editor",
    )

    normalized = _normalize_salary_df(edited)
    st.session_state.salary_df = normalized

    unpaid = normalized[normalized["status"] == "unpaid"]
    paid = normalized[normalized["status"] == "paid"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Teachers", len(normalized))
    m2.metric("Total owed", f"Rp {int(normalized['amount_owed'].sum()):,}")
    m3.metric("Unpaid", f"Rp {int(unpaid['amount_owed'].sum()):,}")
    m4.metric("Paid", f"Rp {int(paid['amount_owed'].sum()):,}")

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("💾 Save to CSV", key="save_salary"):
            path = save_csv(SALARY_FILE, _persist_columns(normalized))
            st.success(f"Saved to `{path}`.")
    with b2:
        st.download_button(
            "Download CSV",
            data=dataframe_to_csv_bytes(_persist_columns(normalized)),
            file_name=f"teacher_salaries_{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
            key="dl_salary_csv",
        )
    with b3:
        st.download_button(
            "Download Excel",
            data=dataframe_to_excel_bytes(normalized, sheet_name="Salaries"),
            file_name=f"teacher_salaries_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_salary_xlsx",
        )

    if st.button("Reload from disk", key="reload_salary"):
        st.session_state.salary_df = _normalize_salary_df(load_csv(SALARY_FILE, TEACHER_SALARY_COLUMNS))
        st.rerun()
