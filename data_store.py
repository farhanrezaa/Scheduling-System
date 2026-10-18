"""CSV persistence helpers for MVP salary, payment, and session confirmations."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"

TEACHER_SALARY_COLUMNS = [
    "teacher_name",
    "rate_per_session",
    "status",
    "notes",
]

STUDENT_PAYMENT_COLUMNS = [
    "student_name",
    "class_name",
    "amount_due",
    "amount_paid",
    "notes",
]

# Flat log shaped for a later Google Sheets tab (one row per confirmed session)
CONFIRMED_SESSION_COLUMNS = [
    "session_key",
    "date",
    "day",
    "class_name",
    "subject",
    "teacher_name",
    "confirmed_at",
]

CONFIRMED_SESSIONS_FILE = "confirmed_sessions.csv"
TEACHER_SALARIES_FILE = "teacher_salaries.csv"
STUDENT_PAYMENTS_FILE = "student_payments.csv"


def ensure_data_dir() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def load_csv(filename: str, columns: list[str]) -> pd.DataFrame:
    """Load a CSV; create an empty framed file if missing."""
    ensure_data_dir()
    path = DATA_DIR / filename
    if not path.exists():
        empty = pd.DataFrame(columns=columns)
        empty.to_csv(path, index=False)
        return empty

    df = pd.read_csv(path)
    for col in columns:
        if col not in df.columns:
            if col in (
                "teacher_name",
                "student_name",
                "class_name",
                "status",
                "notes",
                "session_key",
                "date",
                "day",
                "subject",
                "confirmed_at",
            ):
                df[col] = ""
            else:
                df[col] = 0
    return df[columns].copy()


def save_csv(filename: str, df: pd.DataFrame) -> Path:
    ensure_data_dir()
    path = DATA_DIR / filename
    df.to_csv(path, index=False)
    return path


def dataframe_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Data") -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")
