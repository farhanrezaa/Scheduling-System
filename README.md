# Education Institution Management

Streamlit MVP for an education institute: class scheduling (WIDYS), teacher salary tracking, and student payment tracking.

Built on [farhanrezaa/Scheduling-System](https://github.com/farhanrezaa/Scheduling-System).

## Features

1. **Scheduling System** — generate and edit class schedules (existing WIDYS scheduler)
2. **Teacher Salary Tracker** — `sessions_completed × rate_per_session`, paid/unpaid, CSV persistence
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

## Demo data

Seed CSVs live under `data/`:

- `data/teacher_salaries.csv`
- `data/student_payments.csv`

Edit in the app and click **Save to CSV**. Reloads work offline without Google Sheets for salary/payments. Scheduling still loads master data from Google Sheets when available (see `GOOGLE_SHEETS_SETUP.md`), with built-in defaults as fallback.

## Deploy on Streamlit Community Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select the repo and branch
4. Set **Main file path** to `app.py`
5. Deploy

**Note:** Streamlit Cloud’s filesystem is ephemeral. Saved CSV edits may not persist across restarts; keep downloads/exports for durable copies, or move to Google Sheets/DB later.

## Docker

```bash
docker build -t education-mgmt-mvp .
docker run -p 8501:8501 education-mgmt-mvp
```

## Project layout

```
app.py                 # Streamlit entry (3 views via radio; scheduling sidebar gated)
scheduling_system.py   # WIDYS scheduler (wrapped for the Scheduling view)
salary_tracker.py      # Teacher salary view
payment_tracker.py     # Student payment view
data_store.py          # CSV helpers
data/                  # Seed / persisted CSV data
requirements.txt
Dockerfile
Procfile
```

## Google Sheets (scheduling)

See `GOOGLE_SHEETS_SETUP.md` for configuring teacher/subject/class source data.
