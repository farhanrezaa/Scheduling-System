"""Confirmed teaching sessions — durable CSV log for salary counts."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from data_store import (
    CONFIRMED_SESSION_COLUMNS,
    CONFIRMED_SESSIONS_FILE,
    load_csv,
    save_csv,
)


def make_session_key(date: str, class_name: str, subject: str, teacher_name: str) -> str:
    """Stable idempotency key for one teacher assignment on a class/date/subject."""
    return "|".join(
        [
            str(date).strip(),
            str(class_name).strip(),
            str(subject).strip(),
            str(teacher_name).strip(),
        ]
    )


def load_confirmed_sessions() -> pd.DataFrame:
    df = load_csv(CONFIRMED_SESSIONS_FILE, CONFIRMED_SESSION_COLUMNS)
    for col in CONFIRMED_SESSION_COLUMNS:
        df[col] = df[col].fillna("").astype(str)
    # Drop blank header-only / empty keys
    df = df[df["session_key"].str.len() > 0].copy()
    return df.reset_index(drop=True)


def save_confirmed_sessions(df: pd.DataFrame):
    out = df.copy()
    for col in CONFIRMED_SESSION_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    return save_csv(CONFIRMED_SESSIONS_FILE, out[CONFIRMED_SESSION_COLUMNS])


def confirmed_key_set(df: pd.DataFrame | None = None) -> set[str]:
    if df is None:
        df = load_confirmed_sessions()
    return set(df["session_key"].astype(str).tolist())


def confirm_session(
    date: str,
    day: str,
    class_name: str,
    subject: str,
    teacher_name: str,
    confirmed_at: str | None = None,
) -> tuple[bool, str]:
    """Upsert one confirmed session. Returns (created_new, session_key)."""
    key = make_session_key(date, class_name, subject, teacher_name)
    df = load_confirmed_sessions()
    if key in confirmed_key_set(df):
        return False, key

    stamp = confirmed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    row = {
        "session_key": key,
        "date": str(date).strip(),
        "day": str(day).strip() if day is not None else "",
        "class_name": str(class_name).strip(),
        "subject": str(subject).strip(),
        "teacher_name": str(teacher_name).strip(),
        "confirmed_at": stamp,
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    save_confirmed_sessions(df)
    return True, key


def unconfirm_session(session_key: str) -> bool:
    """Remove a confirmed session by key. Returns True if a row was removed."""
    key = str(session_key).strip()
    df = load_confirmed_sessions()
    before = len(df)
    df = df[df["session_key"] != key].reset_index(drop=True)
    if len(df) == before:
        return False
    save_confirmed_sessions(df)
    return True


def count_sessions_by_teacher(df: pd.DataFrame | None = None) -> pd.Series:
    """Return Series indexed by teacher_name → confirmed session count."""
    if df is None:
        df = load_confirmed_sessions()
    if df.empty:
        return pd.Series(dtype=int)
    return (
        df.groupby(df["teacher_name"].astype(str).str.strip())
        .size()
        .astype(int)
        .rename("confirmed_sessions")
    )
