# Education Institution Management

Streamlit MVP for an education institute: class scheduling (WIDYS), teacher salary tracking, and student payment tracking.

Built on [farhanrezaa/Scheduling-System](https://github.com/farhanrezaa/Scheduling-System).

## Features

1. **Scheduling System** — generate and edit class schedules (existing WIDYS scheduler); **Confirm** a row when the teacher taught to log 1 session
2. **Teacher Salary Tracker** — `confirmed_sessions × rate_per_session`, paid/unpaid; rates editable; session counts come from confirmations
3. **Payment Tracker** — per student `amount_due`, `amount_paid`, `remaining = due − paid`

## Installation

```bash
pip install -r requirements.txt
```

## Running locally

```bash
streamlit run app.py
```

Open `http://localhost:8501`.

The scheduling module can still be run alone:

```bash
streamlit run scheduling_system.py
```

## Confirm → salary flow

1. On **Scheduling System**, generate a schedule (and edit subject/teacher if needed).
2. In **Confirm sessions**, click **Confirm** on a row when the session happened.  
   - Key: `date|class|subject|teacher` — confirming twice does not double-count.  
   - **Undo** removes that log entry.
3. Open **Teacher Salary Tracker** — that teacher’s **Confirmed sessions** increases by 1; amount owed = confirmed × rate.

Persisted in `data/confirmed_sessions.csv` (flat log, easy to mirror later in Google Sheets). Undo also via the sessions log editor on the Salary view.

## Demo data

Seed CSVs live under `data/`:

- `data/teacher_salaries.csv` — teacher rate / paid status / notes
- `data/confirmed_sessions.csv` — confirmed teaching sessions (starts empty)
- `data/student_payments.csv` — student payment demo rows

Edit in the app and click **Save**. Reloads work offline without Google Sheets for salary/payments. Scheduling still loads master data from Google Sheets when available (see `GOOGLE_SHEETS_SETUP.md`), with built-in defaults as fallback.

## Deploy on Streamlit Community Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select the repo and branch
4. Set **Main file path** to `app.py`
5. Deploy

**Note:** Streamlit Cloud’s filesystem is ephemeral. Saved CSV edits may not persist across restarts; keep downloads/exports for durable copies, or move to Google Sheets/DB later (see Project docs on payment storage options).

## Docker

```bash
docker build -t education-mgmt-mvp .
docker run -p 8501:8501 education-mgmt-mvp
```

## Project layout

```
app.py                     # Streamlit entry (3 views via radio; scheduling sidebar gated)
scheduling_system.py       # WIDYS scheduler + Confirm sessions UI
session_confirmations.py   # Confirm / unconfirm / counts (CSV log)
salary_tracker.py          # Teacher salary view (uses confirmed counts)
payment_tracker.py         # Student payment view
data_store.py              # CSV helpers
data/                      # Seed / persisted CSV data
requirements.txt
Dockerfile
Procfile
```

## Google Sheets (scheduling)

See `GOOGLE_SHEETS_SETUP.md` for configuring teacher/subject/class source data.
