# Google Sheets Integration Setup

The scheduling system now reads teacher, subject, class, and class days data from a Google Sheet.

## Quick Setup (Public Sheet - Easiest)

1. **Make your Google Sheet public:**
   - Open your Google Sheet: https://docs.google.com/spreadsheets/d/1NS5VVwq2ZBic90YqdbjeJ3XMp5oFmdZjySrPxiNQvOo/edit
   - Click "Share" → "Change to anyone with the link" → "Viewer"
   - The app will automatically load data via CSV export

2. **Sheet Format:**
   Your sheet should have these columns (in order):
   - Column A: TEACHERS
   - Column B: SUBJECTS
   - Column C: CLASSES
   - Column D: CLASS_DAYS (format: `["Monday", "Wednesday", "Friday"]`)

3. **Run the app:**
   ```bash
   pip install -r requirements.txt
   streamlit run scheduling_system.py
   ```

4. **Reload data:**
   - Click "🔄 Reload from Google Sheets" button in the sidebar
   - Data is cached for 5 minutes

## Advanced Setup (Service Account - For Private Sheets)

If you want to keep your sheet private, use service account authentication:

1. **Create a Google Service Account:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project (or use existing)
   - Enable "Google Sheets API" and "Google Drive API"
   - Go to "IAM & Admin" → "Service Accounts"
   - Create a new service account
   - Create a key (JSON format) and download it

2. **Share the sheet with service account:**
   - Open your Google Sheet
   - Click "Share"
   - Add the service account email (ends with @...iam.gserviceaccount.com)
   - Give it "Viewer" access

3. **Configure the app:**
   - Place the JSON key file in your project directory
   - Update the code to use the service account path (optional - currently uses public access by default)

## Current Sheet Configuration

- **Sheet ID:** `1NS5VVwq2ZBic90YqdbjeJ3XMp5oFmdZjySrPxiNQvOo`
- **Sheet Name:** `Sheet1` (first sheet)

To change these, edit the constants at the top of `scheduling_system.py`:
```python
GOOGLE_SHEET_ID = "your-sheet-id"
GOOGLE_SHEET_NAME = "Sheet1"
```

## How It Works

1. **Data Loading:**
   - On startup, the app tries to load data from Google Sheets
   - Uses CSV export for public sheets (no authentication needed)
   - Falls back to default values if loading fails

2. **Schedule Generation:**
   - Uses valid teacher-subject-class combinations from the sheet
   - Respects class days mapping from the sheet
   - Only assigns teachers who teach the subject for that class

3. **Caching:**
   - Data is cached for 5 minutes to reduce API calls
   - Click "Reload" button to refresh data immediately

## Troubleshooting

**Error: "Could not load from Google Sheets"**
- Make sure the sheet is public (Share → Anyone with link → Viewer)
- Or set up service account authentication
- Check that the sheet has data in columns A-D

**Error: "Authentication Error"**
- For public sheets: Make sure sharing is set to "Anyone with the link"
- For private sheets: Set up service account and share sheet with service account email

**Data not updating:**
- Click "🔄 Reload from Google Sheets" button
- Clear browser cache
- Check that sheet data format is correct

