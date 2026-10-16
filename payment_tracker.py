"""Student Payment Tracker tab — due, paid, remaining."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from data_store import (
    STUDENT_PAYMENT_COLUMNS,
    dataframe_to_csv_bytes,
    dataframe_to_excel_bytes,
    load_csv,
    save_csv,
)

PAYMENT_FILE = "student_payments.csv"


def _normalize_payment_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in STUDENT_PAYMENT_COLUMNS:
        if col not in out.columns:
            out[col] = 0 if col in ("amount_due", "amount_paid") else ""

    out["student_name"] = out["student_name"].fillna("").astype(str)
    out["class_name"] = out["class_name"].fillna("").astype(str)
    out["amount_due"] = pd.to_numeric(out["amount_due"], errors="coerce").fillna(0).astype(int)
    out["amount_paid"] = pd.to_numeric(out["amount_paid"], errors="coerce").fillna(0).astype(int)
    out["notes"] = out["notes"].fillna("").astype(str)
    out["remaining"] = out["amount_due"] - out["amount_paid"]
    return out[STUDENT_PAYMENT_COLUMNS + ["remaining"]]


def _persist_columns(df: pd.DataFrame) -> pd.DataFrame:
    return _normalize_payment_df(df)[STUDENT_PAYMENT_COLUMNS]


def render_payment_tracker():
    st.subheader("Payment Tracker")
    st.caption(
        "Per student: remaining = amount due − amount paid. "
        "Edit the table, then save to CSV under `data/`."
    )

    if "payment_df" not in st.session_state:
        st.session_state.payment_df = _normalize_payment_df(
            load_csv(PAYMENT_FILE, STUDENT_PAYMENT_COLUMNS)
        )

    with st.expander("Add student payment row"):
        with st.form("add_payment_row", clear_on_submit=True):
            c1, c2 = st.columns(2)
            student = c1.text_input("Student name")
            class_name = c2.text_input("Class", value="")
            c3, c4 = st.columns(2)
            due = c3.number_input("Amount due", min_value=0, value=1500000, step=50000)
            paid = c4.number_input("Amount paid", min_value=0, value=0, step=50000)
            notes = st.text_input("Notes", value="")
            if st.form_submit_button("Add row"):
                if not student.strip():
                    st.error("Student name is required.")
                else:
                    new_row = {
                        "student_name": student.strip(),
                        "class_name": class_name.strip(),
                        "amount_due": int(due),
                        "amount_paid": int(paid),
                        "notes": notes,
                    }
                    base = _persist_columns(st.session_state.payment_df)
                    st.session_state.payment_df = _normalize_payment_df(
                        pd.concat([base, pd.DataFrame([new_row])], ignore_index=True)
                    )
                    st.success(f"Added {student.strip()}.")
                    st.rerun()

    edited = st.data_editor(
        st.session_state.payment_df,
        column_config={
            "student_name": st.column_config.TextColumn("Student", required=True),
            "class_name": st.column_config.TextColumn("Class"),
            "amount_due": st.column_config.NumberColumn("Amount due", min_value=0, step=10000, format="%d"),
            "amount_paid": st.column_config.NumberColumn("Amount paid", min_value=0, step=10000, format="%d"),
            "remaining": st.column_config.NumberColumn("Remaining", disabled=True, format="%d"),
            "notes": st.column_config.TextColumn("Notes"),
        },
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="payment_editor",
    )

    normalized = _normalize_payment_df(edited)
    st.session_state.payment_df = normalized

    total_due = int(normalized["amount_due"].sum())
    total_paid = int(normalized["amount_paid"].sum())
    total_remaining = int(normalized["remaining"].sum())
    fully_paid = int((normalized["remaining"] <= 0).sum())

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Students", len(normalized))
    m2.metric("Total due", f"Rp {total_due:,}")
    m3.metric("Total paid", f"Rp {total_paid:,}")
    m4.metric("Remaining", f"Rp {total_remaining:,}")

    st.caption(f"Fully paid students: {fully_paid} / {len(normalized)}")

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("💾 Save to CSV", key="save_payment"):
            path = save_csv(PAYMENT_FILE, _persist_columns(normalized))
            st.success(f"Saved to `{path}`.")
    with b2:
        st.download_button(
            "Download CSV",
            data=dataframe_to_csv_bytes(_persist_columns(normalized)),
            file_name=f"student_payments_{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
            key="dl_payment_csv",
        )
    with b3:
        st.download_button(
            "Download Excel",
            data=dataframe_to_excel_bytes(normalized, sheet_name="Payments"),
            file_name=f"student_payments_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_payment_xlsx",
        )

    if st.button("Reload from disk", key="reload_payment"):
        st.session_state.payment_df = _normalize_payment_df(
            load_csv(PAYMENT_FILE, STUDENT_PAYMENT_COLUMNS)
        )
        st.rerun()
