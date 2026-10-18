"""Teacher Salary Tracker — confirmed_sessions × rate, paid/unpaid."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from data_store import (
    TEACHER_SALARIES_FILE,
    TEACHER_SALARY_COLUMNS,
    dataframe_to_csv_bytes,
    dataframe_to_excel_bytes,
    load_csv,
    save_csv,
)
from session_confirmations import (
    count_sessions_by_teacher,
    load_confirmed_sessions,
    save_confirmed_sessions,
)

STATUS_OPTIONS = ["unpaid", "paid"]


def _load_salary_base() -> pd.DataFrame:
    """Load editable salary fields (rate/status/notes); migrate old CSVs."""
    path_df = load_csv(TEACHER_SALARIES_FILE, TEACHER_SALARY_COLUMNS)
    # Backward compat: older files had sessions_completed
    raw_path = __import__("pathlib").Path(__file__).resolve().parent / "data" / TEACHER_SALARIES_FILE
    if raw_path.exists():
        raw = pd.read_csv(raw_path)
        for col in TEACHER_SALARY_COLUMNS:
            if col not in raw.columns:
                raw[col] = "" if col in ("teacher_name", "status", "notes") else 0
        path_df = raw[TEACHER_SALARY_COLUMNS].copy()
    return path_df


def _normalize_salary_base(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in TEACHER_SALARY_COLUMNS:
        if col not in out.columns:
            out[col] = 0 if col == "rate_per_session" else ""

    out["teacher_name"] = out["teacher_name"].fillna("").astype(str).str.strip()
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
    out = out[out["teacher_name"] != ""].copy()
    # One row per teacher (last wins if duplicates)
    out = out.drop_duplicates(subset=["teacher_name"], keep="last")
    return out[TEACHER_SALARY_COLUMNS].reset_index(drop=True)


def _with_confirmed_counts(base: pd.DataFrame) -> pd.DataFrame:
    """Merge salary profile with confirmed session counts from the log."""
    counts = count_sessions_by_teacher()
    base = _normalize_salary_base(base)

    teachers_from_log = [t for t in counts.index.tolist() if t]
    all_teachers = list(dict.fromkeys(base["teacher_name"].tolist() + teachers_from_log))

    rows = []
    rate_map = dict(zip(base["teacher_name"], base["rate_per_session"]))
    status_map = dict(zip(base["teacher_name"], base["status"]))
    notes_map = dict(zip(base["teacher_name"], base["notes"]))

    for teacher in all_teachers:
        confirmed = int(counts.get(teacher, 0))
        rate = int(rate_map.get(teacher, 75000))
        rows.append(
            {
                "teacher_name": teacher,
                "confirmed_sessions": confirmed,
                "rate_per_session": rate,
                "amount_owed": confirmed * rate,
                "status": status_map.get(teacher, "unpaid"),
                "notes": notes_map.get(teacher, ""),
            }
        )

    return pd.DataFrame(rows)


def _persist_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Persist only editable profile fields (sessions come from the confirm log)."""
    out = df.copy()
    if "teacher_name" not in out.columns:
        return pd.DataFrame(columns=TEACHER_SALARY_COLUMNS)
    slim = pd.DataFrame(
        {
            "teacher_name": out["teacher_name"],
            "rate_per_session": out.get("rate_per_session", 0),
            "status": out.get("status", "unpaid"),
            "notes": out.get("notes", ""),
        }
    )
    return _normalize_salary_base(slim)


def render_salary_tracker():
    st.subheader("Teacher Salary Tracker")
    st.caption(
        "Salary owed = **confirmed sessions** × rate per session. "
        "Confirm sessions on the Scheduling System view; rates and paid/unpaid stay editable here."
    )

    # Always refresh counts from disk so Scheduling confirms show up immediately
    display_df = _with_confirmed_counts(_load_salary_base())

    with st.expander("Add teacher (rate / status)"):
        with st.form("add_salary_row", clear_on_submit=True):
            c1, c2 = st.columns(2)
            teacher = c1.text_input("Teacher name")
            rate = c2.number_input("Rate per session", min_value=0, value=75000, step=5000)
            c3, c4 = st.columns(2)
            status = c3.selectbox("Status", STATUS_OPTIONS, index=0)
            notes = c4.text_input("Notes", value="")
            if st.form_submit_button("Add row"):
                if not teacher.strip():
                    st.error("Teacher name is required.")
                else:
                    base = _normalize_salary_base(_load_salary_base())
                    new_row = {
                        "teacher_name": teacher.strip(),
                        "rate_per_session": int(rate),
                        "status": status,
                        "notes": notes,
                    }
                    # Replace existing teacher profile if present
                    base = base[base["teacher_name"] != teacher.strip()]
                    base = pd.concat([base, pd.DataFrame([new_row])], ignore_index=True)
                    save_csv(TEACHER_SALARIES_FILE, _normalize_salary_base(base))
                    st.success(f"Saved profile for {teacher.strip()}. Confirmed sessions come from Scheduling.")
                    st.rerun()

    edited = st.data_editor(
        display_df,
        column_config={
            "teacher_name": st.column_config.TextColumn("Teacher", required=True),
            "confirmed_sessions": st.column_config.NumberColumn(
                "Confirmed sessions",
                disabled=True,
                help="From Scheduling → Confirm (data/confirmed_sessions.csv)",
                format="%d",
            ),
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

    # Recompute owed from confirmed counts (ignore any editor attempt to change them)
    counts = count_sessions_by_teacher()
    normalized = edited.copy()
    normalized["teacher_name"] = normalized["teacher_name"].fillna("").astype(str).str.strip()
    normalized["rate_per_session"] = pd.to_numeric(
        normalized["rate_per_session"], errors="coerce"
    ).fillna(0).astype(int)
    normalized["confirmed_sessions"] = normalized["teacher_name"].map(
        lambda t: int(counts.get(t, 0))
    )
    normalized["amount_owed"] = normalized["confirmed_sessions"] * normalized["rate_per_session"]
    normalized["status"] = (
        normalized["status"]
        .fillna("unpaid")
        .astype(str)
        .str.lower()
        .apply(lambda s: s if s in STATUS_OPTIONS else "unpaid")
    )
    normalized["notes"] = normalized["notes"].fillna("").astype(str)

    unpaid = normalized[normalized["status"] == "unpaid"]
    paid = normalized[normalized["status"] == "paid"]
    total_sessions = int(normalized["confirmed_sessions"].sum())

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Teachers", len(normalized))
    m2.metric("Confirmed sessions", total_sessions)
    m3.metric("Total owed", f"Rp {int(normalized['amount_owed'].sum()):,}")
    m4.metric("Unpaid", f"Rp {int(unpaid['amount_owed'].sum()):,}")
    m5.metric("Paid", f"Rp {int(paid['amount_owed'].sum()):,}")

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("💾 Save rates / status to CSV", key="save_salary"):
            path = save_csv(TEACHER_SALARIES_FILE, _persist_columns(normalized))
            st.success(f"Saved teacher profiles to `{path}`. Session counts stay in the confirm log.")
    with b2:
        st.download_button(
            "Download salary CSV",
            data=dataframe_to_csv_bytes(
                normalized[
                    [
                        "teacher_name",
                        "confirmed_sessions",
                        "rate_per_session",
                        "amount_owed",
                        "status",
                        "notes",
                    ]
                ]
            ),
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

    log = load_confirmed_sessions()
    with st.expander(f"Confirmed sessions log ({len(log)} rows) — edit/delete to adjust counts"):
        st.caption(
            "Source of truth for session counts: `data/confirmed_sessions.csv`. "
            "Delete rows here and save to undo confirmations (or use Undo on Scheduling)."
        )
        if log.empty:
            st.info("No confirmed sessions yet. Generate a schedule and click **Confirm** on a row.")
        else:
            edited_log = st.data_editor(
                log,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key="confirmed_sessions_editor",
                column_config={
                    "session_key": st.column_config.TextColumn("Session key", disabled=True),
                    "confirmed_at": st.column_config.TextColumn("Confirmed at", disabled=True),
                },
            )
            if st.button("💾 Save sessions log", key="save_sessions_log"):
                # Drop blank keys; keep unique keys
                cleaned = edited_log.copy()
                cleaned["session_key"] = cleaned["session_key"].fillna("").astype(str)
                cleaned = cleaned[cleaned["session_key"].str.len() > 0]
                cleaned = cleaned.drop_duplicates(subset=["session_key"], keep="last")
                path = save_confirmed_sessions(cleaned)
                st.success(f"Saved sessions log to `{path}`.")
                st.rerun()
