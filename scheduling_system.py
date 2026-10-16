import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import io
import json
import ast

# Optional imports for Google Sheets (only needed for private sheets)
try:
    import gspread
    from google.oauth2 import service_account
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

# Google Sheet Configuration
GOOGLE_SHEET_ID = "1NS5VVwq2ZBic90YqdbjeJ3XMp5oFmdZjySrPxiNQvOo"
GOOGLE_SHEET_NAME = "List"  # Change if your sheet has a different name

# Global parameters (will be loaded from Google Sheets)
SUBJECTS = []
CLASSES = []
TEACHERS = []
CLASS_DAYS = {}
TEACHER_SUBJECT_CLASS_MAPPING = []  # List of valid combinations

def parse_class_days(class_days_str):
    """Parse CLASS_DAYS from string format (JSON array or Python list)."""
    if not class_days_str or pd.isna(class_days_str):
        return []
    
    try:
        # Try parsing as JSON first
        return json.loads(class_days_str)
    except (json.JSONDecodeError, TypeError):
        try:
            # Try parsing as Python literal (ast.literal_eval)
            return ast.literal_eval(class_days_str)
        except (ValueError, SyntaxError):
            # If both fail, try splitting by comma
            return [day.strip() for day in str(class_days_str).replace('[', '').replace(']', '').replace('"', '').split(',')]

def load_data_from_google_sheets(use_service_account=False, service_account_path=None):
    """Load data from Google Sheets."""
    if not GSPREAD_AVAILABLE:
        st.error("gspread is not installed. Install it with: pip install gspread")
        return False
    try:
        if use_service_account and service_account_path:
            # Use service account authentication
            scope = ['https://www.googleapis.com/auth/spreadsheets.readonly']
            credentials = service_account.Credentials.from_service_account_file(
                service_account_path, scopes=scope
            )
            gc = gspread.authorize(credentials)
        else:
            # Try to access as public sheet (no authentication)
            gc = gspread.service_account()  # This will fail if no credentials
            # Alternative: use public access
            try:
                gc = gspread.open_by_url(f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}")
            except:
                # If that fails, try opening by key without auth
                gc = gspread.open_by_key(GOOGLE_SHEET_ID)
        
        # Open the spreadsheet
        spreadsheet = gc.open_by_key(GOOGLE_SHEET_ID)
        worksheet = spreadsheet.worksheet(GOOGLE_SHEET_NAME)
        
        # Get all values
        all_values = worksheet.get_all_values()
        
        if len(all_values) < 2:
            st.error("Sheet appears to be empty or has no data rows.")
            return False
        
        # Skip header row (row 1)
        data_rows = all_values[1:]
        
        # Parse data
        global SUBJECTS, CLASSES, TEACHERS, CLASS_DAYS, TEACHER_SUBJECT_CLASS_MAPPING
        
        SUBJECTS = []
        CLASSES = []
        TEACHERS = []
        CLASS_DAYS = {}
        TEACHER_SUBJECT_CLASS_MAPPING = []
        
        for row in data_rows:
            if len(row) < 4:
                continue
            
            teacher = row[0].strip() if row[0] else None
            subject = row[1].strip() if row[1] else None
            class_name = row[2].strip() if row[2] else None
            class_days_str = row[3].strip() if len(row) > 3 and row[3] else None
            
            if not all([teacher, subject, class_name, class_days_str]):
                continue
            
            # Add to unique lists
            if teacher not in TEACHERS:
                TEACHERS.append(teacher)
            if subject not in SUBJECTS:
                SUBJECTS.append(subject)
            if class_name not in CLASSES:
                CLASSES.append(class_name)
            
            # Parse class days
            days = parse_class_days(class_days_str)
            if days:
                CLASS_DAYS[class_name] = days
            
            # Store valid teacher-subject-class combinations
            TEACHER_SUBJECT_CLASS_MAPPING.append({
                'teacher': teacher,
                'subject': subject,
                'class': class_name,
                'days': days
            })
        
        if not CLASSES or not SUBJECTS or not TEACHERS:
            st.error("Failed to load data from Google Sheets. Please check the sheet format.")
            return False
        
        return True
        
    except gspread.exceptions.APIError as e:
        if "PERMISSION_DENIED" in str(e) or "401" in str(e):
            st.error("""
            **Authentication Error**: 
            Please either:
            1. Make the Google Sheet public (View access), OR
            2. Set up service account authentication
            """)
        else:
            st.error(f"Error accessing Google Sheets: {e}")
        return False
    except FileNotFoundError:
        st.error(f"Service account file not found: {service_account_path}")
        return False
    except Exception as e:
        st.error(f"Error loading data from Google Sheets: {e}")
        return False

# Try to load data on startup (with fallback to public access)
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_sheet_data(show_errors=False):
    """Load data from Google Sheets with caching."""
    global SUBJECTS, CLASSES, TEACHERS, CLASS_DAYS, TEACHER_SUBJECT_CLASS_MAPPING
    
    # Method 1: Try public CSV export (works for public sheets)
    try:
        csv_url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv&gid=0"
        if show_errors:
            st.info(f"Attempting to load from CSV export...")
        
        # Try to read the CSV
        import urllib.request
        try:
            response = urllib.request.urlopen(csv_url, timeout=10)
            content = response.read().decode('utf-8')
            if show_errors:
                st.info(f"CSV response length: {len(content)} characters")
            if len(content) < 100:  # Very short response might be an error page
                if show_errors:
                    st.warning("CSV response seems too short. Sheet might not be public.")
                raise Exception("CSV response too short - sheet may not be public")
        except urllib.error.HTTPError as e:
            if show_errors:
                st.error(f"HTTP Error {e.code}: {e.reason}")
                if e.code == 403:
                    st.error("❌ **Access Denied**: Please make your Google Sheet public (Share → Anyone with the link → Viewer)")
            raise
        
        df = pd.read_csv(csv_url)
        
        if show_errors:
            st.info(f"CSV loaded. Shape: {df.shape}, Columns: {list(df.columns)}")
        
        if df.empty:
            if show_errors:
                st.warning("CSV file is empty")
            return False
        
        if len(df.columns) < 4:
            if show_errors:
                st.warning(f"Expected 4 columns, found {len(df.columns)}: {list(df.columns)}")
            return False
        
        SUBJECTS = []
        CLASSES = []
        TEACHERS = []
        CLASS_DAYS = {}
        TEACHER_SUBJECT_CLASS_MAPPING = []
        
        # Assume columns are: TEACHERS, SUBJECTS, CLASSES, CLASS_DAYS
        rows_processed = 0
        for idx, row in df.iterrows():
            teacher = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
            subject = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else None
            class_name = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else None
            class_days_str = str(row.iloc[3]).strip() if len(row) > 3 and pd.notna(row.iloc[3]) else None
            
            # Skip header row if it matches column names
            if teacher and teacher.upper() == 'TEACHERS':
                continue
            
            if not all([teacher, subject, class_name, class_days_str]) or teacher == 'nan' or subject == 'nan':
                if show_errors and idx < 5:  # Show first few skipped rows
                    st.write(f"Skipping row {idx}: teacher={teacher}, subject={subject}, class={class_name}")
                continue
            
            if teacher not in TEACHERS:
                TEACHERS.append(teacher)
            if subject not in SUBJECTS:
                SUBJECTS.append(subject)
            if class_name not in CLASSES:
                CLASSES.append(class_name)
            
            days = parse_class_days(class_days_str)
            if days:
                CLASS_DAYS[class_name] = days
            
            TEACHER_SUBJECT_CLASS_MAPPING.append({
                'teacher': teacher,
                'subject': subject,
                'class': class_name,
                'days': days
            })
            rows_processed += 1
        
        if show_errors:
            st.info(f"Processed {rows_processed} rows. Found {len(CLASSES)} classes, {len(SUBJECTS)} subjects, {len(TEACHERS)} teachers")
        
        # Store in session state for persistence
        st.session_state.classes_data = CLASSES
        st.session_state.subjects_data = SUBJECTS
        st.session_state.teachers_data = TEACHERS
        st.session_state.class_days_data = CLASS_DAYS
        st.session_state.mapping_data = TEACHER_SUBJECT_CLASS_MAPPING
        
        return len(CLASSES) > 0 and len(SUBJECTS) > 0 and len(TEACHERS) > 0
        
    except pd.errors.EmptyDataError:
        if show_errors:
            st.error("CSV file is empty or cannot be parsed")
        return False
    except Exception as e:
        if show_errors:
            st.error(f"Error loading CSV: {str(e)}")
            st.info("Trying alternative method...")
        # Method 2: Try gspread (requires authentication)
        if not GSPREAD_AVAILABLE:
            return False
        try:
            gc = gspread.service_account()
            spreadsheet = gc.open_by_key(GOOGLE_SHEET_ID)
            try:
                worksheet = spreadsheet.worksheet(GOOGLE_SHEET_NAME)
            except:
                worksheet = spreadsheet.sheet1  # Fallback to first sheet
            
            all_values = worksheet.get_all_values()
            
            if len(all_values) < 2:
                return False
            
            data_rows = all_values[1:]
            
            SUBJECTS = []
            CLASSES = []
            TEACHERS = []
            CLASS_DAYS = {}
            TEACHER_SUBJECT_CLASS_MAPPING = []
            
            for row in data_rows:
                if len(row) < 4:
                    continue
                
                teacher = row[0].strip() if row[0] else None
                subject = row[1].strip() if row[1] else None
                class_name = row[2].strip() if row[2] else None
                class_days_str = row[3].strip() if len(row) > 3 and row[3] else None
                
                if not all([teacher, subject, class_name, class_days_str]):
                    continue
                
                if teacher not in TEACHERS:
                    TEACHERS.append(teacher)
                if subject not in SUBJECTS:
                    SUBJECTS.append(subject)
                if class_name not in CLASSES:
                    CLASSES.append(class_name)
                
                days = parse_class_days(class_days_str)
                if days:
                    CLASS_DAYS[class_name] = days
                
                TEACHER_SUBJECT_CLASS_MAPPING.append({
                    'teacher': teacher,
                    'subject': subject,
                    'class': class_name,
                    'days': days
                })
            
            # Store in session state for persistence
            st.session_state.classes_data = CLASSES
            st.session_state.subjects_data = SUBJECTS
            st.session_state.teachers_data = TEACHERS
            st.session_state.class_days_data = CLASS_DAYS
            st.session_state.mapping_data = TEACHER_SUBJECT_CLASS_MAPPING
            
            return len(CLASSES) > 0 and len(SUBJECTS) > 0 and len(TEACHERS) > 0
            
        except Exception as e2:
            return False

# Load data on startup and store in session state
def initialize_data():
    """Initialize data from Google Sheets or use defaults."""
    if 'data_initialized' not in st.session_state:
        if load_sheet_data():
            # Store in session state
            st.session_state.classes_data = CLASSES
            st.session_state.subjects_data = SUBJECTS
            st.session_state.teachers_data = TEACHERS
            st.session_state.class_days_data = CLASS_DAYS
            st.session_state.mapping_data = TEACHER_SUBJECT_CLASS_MAPPING
            st.session_state.data_initialized = True
        else:
            # Fallback to default values
            default_subjects = ["Math", "Science", "English", "History"]
            default_classes = ["A", "B", "C"]
            default_teachers = [f"Teacher {i}" for i in range(1, 6)]
            default_class_days = {
                "A": ["Monday", "Wednesday", "Friday"],
                "B": ["Tuesday", "Thursday", "Saturday"],
                "C": ["Monday", "Wednesday", "Friday"]
            }
            st.session_state.classes_data = default_classes
            st.session_state.subjects_data = default_subjects
            st.session_state.teachers_data = default_teachers
            st.session_state.class_days_data = default_class_days
            st.session_state.mapping_data = []
            st.session_state.data_initialized = True

# Function to generate the schedule
def generate_schedule(start_date, end_date, classes=None, class_days=None, subjects=None, teachers=None, mapping=None):
    # Generate date sequence excluding Sundays
    date_seq = []
    current_date = start_date
    while current_date <= end_date:
        if current_date.strftime("%A") != "Sunday":
            date_seq.append(current_date)
        current_date += timedelta(days=1)
    
    # Use provided parameters or fall back to globals
    use_classes = classes if classes is not None else CLASSES
    use_class_days = class_days if class_days is not None else CLASS_DAYS
    use_subjects = subjects if subjects is not None else SUBJECTS
    use_teachers = teachers if teachers is not None else TEACHERS
    use_mapping = mapping if mapping is not None else TEACHER_SUBJECT_CLASS_MAPPING
    
    schedule_data = []
    random.seed(123)
    np.random.seed(123)
    
    for class_name in use_classes:
        if class_name not in use_class_days:
            continue
        
        allowed_days = use_class_days[class_name]
        class_dates = [d for d in date_seq if d.strftime("%A") in allowed_days]
        
        # Get valid teacher-subject combinations for this class
        valid_combinations = [
            combo for combo in use_mapping 
            if combo['class'] == class_name
        ]
        
        if not valid_combinations:
            # Fallback: use any subject and teacher if no mapping found
            valid_combinations = [
                {'teacher': t, 'subject': s, 'class': class_name, 'days': allowed_days}
                for t in use_teachers for s in use_subjects
            ]
        
        # Calculate week numbers (matching R's ceiling function)
        week_nums = []
        for date in class_dates:
            days_diff = (date - start_date).days
            week_num = int(np.ceil(days_diff / 7))
            week_nums.append(week_num)
        
        unique_weeks = sorted(set(week_nums))
        
        for week in unique_weeks:
            week_dates = [class_dates[i] for i, w in enumerate(week_nums) if w == week]
            
            # Get unique subjects for this class from valid combinations
            available_subjects = list(set([combo['subject'] for combo in valid_combinations]))
            assigned_subjects = random.sample(available_subjects, min(3, len(available_subjects)))
            
            for i, date in enumerate(week_dates):
                day_name = date.strftime("%A")
                # Match R's modulo logic: i %% length(assigned_subjects) + 1 (1-indexed)
                subject_idx = (i % len(assigned_subjects))
                subject = assigned_subjects[subject_idx]
                
                # Find a valid teacher for this subject and class
                valid_teachers = [
                    combo['teacher'] for combo in valid_combinations
                    if combo['subject'] == subject
                ]
                
                if valid_teachers:
                    teacher = random.choice(valid_teachers)
                else:
                    # Fallback: use any teacher
                    teacher = random.choice(use_teachers)
                
                schedule_data.append({
                    "Date": date.strftime("%Y-%m-%d"),
                    "Day": day_name,
                    "Class": class_name,
                    "Subject": subject,
                    "Teacher": teacher
                })
    
    return pd.DataFrame(schedule_data)

def _ensure_scheduling_session_state():
    """Initialize scheduling-related session state keys (idempotent)."""
    if 'schedule_data' not in st.session_state:
        st.session_state.schedule_data = None
    if 'edited_data' not in st.session_state:
        st.session_state.edited_data = None
    if 'classes_data' not in st.session_state:
        st.session_state.classes_data = CLASSES
    if 'subjects_data' not in st.session_state:
        st.session_state.subjects_data = SUBJECTS
    if 'teachers_data' not in st.session_state:
        st.session_state.teachers_data = TEACHERS
    if 'class_days_data' not in st.session_state:
        st.session_state.class_days_data = CLASS_DAYS
    if 'mapping_data' not in st.session_state:
        st.session_state.mapping_data = TEACHER_SUBJECT_CLASS_MAPPING


# Define UI
def display_logo(width: int | None = None):
    """Display WIDYS logo if available.

    Args:
        width: Pixel width for header placement. If None, fill the container
            (legacy sidebar-style sizing when used alone).
    """
    import os
    from pathlib import Path

    # Get the script directory
    script_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()

    # Try to load logo from common locations (prioritize JPEG)
    logo_paths = [
        script_dir / "logo.jpg",
        script_dir / "logo.jpeg",
        script_dir / "logo.png",
        script_dir / "widys_logo.jpg",
        script_dir / "widys_logo.jpeg",
        script_dir / "widys_logo.png",
        script_dir / "assets" / "logo.jpg",
        script_dir / "assets" / "logo.jpeg",
        script_dir / "assets" / "logo.png",
        script_dir / "assets" / "widys_logo.jpg",
        script_dir / "assets" / "widys_logo.png",
        # Also try relative paths (for Streamlit)
        "logo.jpg",
        "logo.jpeg",
        "logo.png",
        "widys_logo.jpg",
        "widys_logo.jpeg",
        "widys_logo.png",
    ]

    logo_found = False
    for logo_path in logo_paths:
        # Handle both Path objects and strings
        path_str = str(logo_path) if isinstance(logo_path, Path) else logo_path

        if os.path.exists(path_str):
            try:
                # Try with PIL Image first (handles format mismatches better)
                try:
                    from PIL import Image
                    img = Image.open(path_str)
                    if width is not None:
                        st.image(img, width=width)
                    else:
                        st.image(img, use_container_width=True)
                    logo_found = True
                    break
                except Exception:
                    # Fallback to direct path
                    if width is not None:
                        st.image(path_str, width=width)
                    else:
                        st.image(path_str, use_container_width=True)
                    logo_found = True
                    break
            except Exception:
                continue

    if not logo_found:
        # Display text logo if image not found
        st.markdown("""
        <div style="padding: 4px 0;">
            <div style="color: #FF0000; font-weight: 700; font-size: 1.1rem; line-height: 1.2;">WIDYS</div>
            <div style="color: #FF0000; font-weight: 700; font-size: 0.75rem;">BIMBINGAN BELAJAR</div>
            <div style="color: #FF0000; font-style: italic; font-size: 0.7rem;">#EdukasiDenganHati</div>
        </div>
        """, unsafe_allow_html=True)

def render_scheduling_tab():
    """Render the WIDYS scheduling UI (algorithm unchanged; callable from app tabs)."""
    initialize_data()
    _ensure_scheduling_session_state()

    # Main page header
    st.title("System Jadwal Pelajaran Widys")

    st.divider()

    # Sidebar controls (only created when this view is rendered)
    with st.sidebar:
        st.header("Controls")
        
        # Google Sheets Configuration
        st.subheader("📊 Data Source")
        if st.button("🔄 Reload from Google Sheets", help="Reload teacher, subject, and class data from Google Sheets"):
            load_sheet_data.clear()  # Clear cache
            if load_sheet_data(show_errors=True):
                # Update session state
                st.session_state.classes_data = CLASSES
                st.session_state.subjects_data = SUBJECTS
                st.session_state.teachers_data = TEACHERS
                st.session_state.class_days_data = CLASS_DAYS
                st.session_state.mapping_data = TEACHER_SUBJECT_CLASS_MAPPING
                st.success(f"✅ Loaded {len(CLASSES)} classes, {len(SUBJECTS)} subjects, {len(TEACHERS)} teachers")
                st.rerun()
            else:
                st.error("❌ Failed to load data. Using default values.")
                st.info("💡 **Tip:** Make sure your Google Sheet is set to 'Anyone with the link can view'")
        
        # Display current data info
        with st.expander("📋 Current Data Info"):
            # Use session state (always available after initialization)
            display_classes = st.session_state.get('classes_data', [])
            display_subjects = st.session_state.get('subjects_data', [])
            display_teachers = st.session_state.get('teachers_data', [])
            display_class_days = st.session_state.get('class_days_data', {})
            display_mapping = st.session_state.get('mapping_data', [])
            
            if display_classes and display_subjects and display_teachers:
                st.write(f"**Classes:** {len(display_classes)}")
                st.write(f"**Subjects:** {len(display_subjects)}")
                st.write(f"**Teachers:** {len(display_teachers)}")
                st.write(f"**Mappings:** {len(display_mapping)}")
                st.write(f"**Class Days Configured:** {len(display_class_days)}")
                if display_class_days:
                    st.write("**Class Days Details:**")
                    for cls, days in display_class_days.items():
                        st.write(f"  - {cls}: {days}")
            else:
                st.warning("⚠️ No data loaded. Using default values or please reload from Google Sheets.")
                st.write(f"**Classes:** {display_classes}")
                st.write(f"**Class Days:** {display_class_days}")
        
        st.divider()
        
        date_range = st.date_input(
            "Select Date Range:",
            value=(datetime.now().date(), datetime.now().date() + timedelta(days=6)),
            min_value=datetime.now().date()
        )
        
        # Handle date range input (Streamlit returns tuple for range selection)
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        elif isinstance(date_range, tuple) and len(date_range) == 1:
            start_date = end_date = date_range[0]
        else:
            start_date = end_date = date_range
        
        if st.button("Generate Schedule"):
            # Get data from session state
            current_classes = st.session_state.get('classes_data', [])
            current_class_days = st.session_state.get('class_days_data', {})
            current_subjects = st.session_state.get('subjects_data', [])
            current_teachers = st.session_state.get('teachers_data', [])
            current_mapping = st.session_state.get('mapping_data', [])
            
            # Check if we have the necessary data
            if not current_classes:
                st.error("❌ No classes found! Please reload data from Google Sheets or check your data source.")
            elif not current_class_days:
                st.error("❌ No class days configured! Please check your Google Sheet data.")
            else:
                start_date_obj = datetime.combine(start_date, datetime.min.time())
                end_date_obj = datetime.combine(end_date, datetime.min.time())
                
                schedule = generate_schedule(
                    start_date_obj, 
                    end_date_obj,
                    classes=current_classes,
                    class_days=current_class_days,
                    subjects=current_subjects,
                    teachers=current_teachers,
                    mapping=current_mapping
                )
                
                if schedule.empty:
                    st.warning("⚠️ Generated schedule is empty. This might be because:")
                    st.write("- No valid date matches for the selected range")
                    st.write("- Class days don't match any dates in the range")
                    st.write(f"- Current classes: {current_classes}")
                    st.write(f"- Current class days: {current_class_days}")
                else:
                    st.session_state.schedule_data = schedule
                    st.session_state.edited_data = schedule.copy()
                    st.success(f"✅ Schedule generated with {len(schedule)} entries!")
                    st.rerun()
        
        if st.button("Apply Edits to Future Schedule"):
            if st.session_state.edited_data is not None and st.session_state.schedule_data is not None:
                # Get data from session state
                current_classes = st.session_state.get('classes_data', [])
                current_class_days = st.session_state.get('class_days_data', {})
                current_subjects = st.session_state.get('subjects_data', [])
                current_teachers = st.session_state.get('teachers_data', [])
                current_mapping = st.session_state.get('mapping_data', [])
                
                edited = st.session_state.edited_data.copy()
                schedule = st.session_state.schedule_data.copy()
                
                # Apply manual edits
                for idx, row in edited.iterrows():
                    mask = (schedule['Date'] == row['Date']) & (schedule['Class'] == row['Class'])
                    schedule.loc[mask, 'Subject'] = row['Subject']
                    schedule.loc[mask, 'Teacher'] = row['Teacher']
                
                # Adjust future schedules while keeping constraints
                if len(edited) > 0:
                    max_edited_date = edited['Date'].max()
                    future_dates = schedule[schedule['Date'] > max_edited_date]
                    
                    if len(future_dates) > 0:
                        future_start = pd.to_datetime(future_dates['Date'].min())
                        end_date_obj = pd.to_datetime(schedule['Date'].max())
                        
                        future_schedule = generate_schedule(
                            future_start, 
                            end_date_obj,
                            classes=current_classes,
                            class_days=current_class_days,
                            subjects=current_subjects,
                            teachers=current_teachers,
                            mapping=current_mapping
                        )
                        past_schedule = schedule[pd.to_datetime(schedule['Date']) < future_start]
                        
                        schedule = pd.concat([past_schedule, future_schedule], ignore_index=True)
                
                st.session_state.schedule_data = schedule
                st.session_state.edited_data = schedule.copy()
                st.rerun()
        
        # Download button
        if st.session_state.schedule_data is not None:
            # Create Excel file in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                st.session_state.schedule_data.to_excel(writer, index=False, sheet_name='Schedule')
            excel_data = output.getvalue()
            
            st.download_button(
                label="Download Schedule as Excel",
                data=excel_data,
                file_name=f"Schedule_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # Main panel
    if st.session_state.schedule_data is not None:
        st.header("Generated Schedule")
        st.dataframe(st.session_state.schedule_data, use_container_width=True, hide_index=True)
        
        st.header("Edit Schedule")
        # Get current data from session state
        editor_subjects = st.session_state.get('subjects_data', [])
        editor_teachers = st.session_state.get('teachers_data', [])
        
        # Create editable dataframe (Subject and Teacher columns)
        edited_df = st.data_editor(
            st.session_state.edited_data,
            column_config={
                "Date": st.column_config.TextColumn("Date", disabled=True),
                "Day": st.column_config.TextColumn("Day", disabled=True),
                "Class": st.column_config.TextColumn("Class", disabled=True),
                "Subject": st.column_config.SelectboxColumn("Subject", options=editor_subjects),
                "Teacher": st.column_config.SelectboxColumn("Teacher", options=editor_teachers)
            },
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key="schedule_editor"
        )
        
        # Update edited data in session state
        st.session_state.edited_data = edited_df
    else:
        st.info("Please select a date range and click 'Generate Schedule' to begin.")


if __name__ == "__main__":
    st.set_page_config(
        page_title="System Jadwal Pelajaran Widys",
        layout="wide",
    )
    render_scheduling_tab()
