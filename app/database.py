import sqlite3
from datetime import datetime
import logging
from typing import List, Dict, Any
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use data directory for persistence
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "rota_operations.db"
        
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Table for employees
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                postcode TEXT NOT NULL,
                gender TEXT NOT NULL,
                ethnicity TEXT NOT NULL,
                religion TEXT NOT NULL,
                transport_mode TEXT NOT NULL,
                qualification TEXT NOT NULL,
                language_spoken TEXT NOT NULL,
                certificate_expiry_date TEXT NOT NULL,
                earliest_start TEXT NOT NULL,
                latest_end TEXT NOT NULL,
                shifts TEXT NOT NULL,
                contact_number TEXT NOT NULL,
                notes TEXT,
                source_filename TEXT,
                source_uploaded_at TEXT,
                upload_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table for patients
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT UNIQUE NOT NULL,
                patient_name TEXT NOT NULL,
                address TEXT NOT NULL,
                postcode TEXT NOT NULL,
                gender TEXT NOT NULL,
                ethnicity TEXT NOT NULL,
                religion TEXT NOT NULL,
                required_support TEXT NOT NULL,
                required_hours_of_support INTEGER NOT NULL,
                additional_requirements TEXT NOT NULL,
                illness TEXT NOT NULL,
                contact_number TEXT NOT NULL,
                requires_medication TEXT NOT NULL,
                emergency_contact TEXT NOT NULL,
                emergency_relation TEXT NOT NULL,
                language_preference TEXT NOT NULL,
                notes TEXT,
                source_filename TEXT,
                source_uploaded_at TEXT,
                upload_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table for assignments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                employee_name TEXT NOT NULL,
                patient_id TEXT NOT NULL,
                patient_name TEXT NOT NULL,
                service_type TEXT NOT NULL,
                assigned_time TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                duration INTEGER,
                travel_time INTEGER,
                priority_score REAL,
                reasoning TEXT,
                group_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table for operations log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operations_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                description TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table for data uploads
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                employees_count INTEGER,
                patients_count INTEGER,
                status TEXT NOT NULL
            )
        ''')

        # Table for raw uploads storage (sheets JSON)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS raw_uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sheets_json TEXT NOT NULL
            )
        ''')
        
        # Table for notifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                is_deleted BOOLEAN DEFAULT FALSE,
                action_type TEXT,
                action_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read_at TIMESTAMP,
                deleted_at TIMESTAMP
            )
        ''')

        # Table for stats cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                generated_at TEXT NOT NULL,
                assignments_count INTEGER NOT NULL,
                metrics_json TEXT NOT NULL,
                ai_summary TEXT,
                ai_ideas TEXT
            )
        ''')
        
        # Table for unassigned reasons (patients or employees)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unassigned (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL, -- 'patient' | 'employee'
                entity_id TEXT NOT NULL,
                date TEXT NOT NULL, -- ISO date (YYYY-MM-DD)
                reasons TEXT NOT NULL, -- JSON array of strings
                context TEXT, -- JSON object with extra fields
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Cache table for AI summaries of unassigned (per entity/week)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unassigned_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                week_start TEXT NOT NULL,
                week_end TEXT NOT NULL,
                summary TEXT,
                reasons TEXT, -- JSON array
                dates TEXT,   -- JSON array
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(entity_type, entity_id, week_start, week_end)
            )
        ''')
        
        self.conn.commit()

        # Create helpful indices for performance and integrity checks
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_assign_emp_time ON assignments(employee_id, start_time, end_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_assign_patient_time ON assignments(patient_id, start_time, end_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_assign_start_time ON assignments(start_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_unassigned_entity_date ON unassigned(entity_type, entity_id, date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_unassigned_summary_entity_week ON unassigned_summaries(entity_type, entity_id, week_start, week_end)')
            self.conn.commit()
        except Exception as e:
            logger.warning(f"Index creation failed: {e}")

        # Ensure backward-compatible columns exist for source metadata
        try:
            self._ensure_column('employees', 'source_filename', 'TEXT')
            self._ensure_column('employees', 'source_uploaded_at', 'TEXT')
            self._ensure_column('employees', 'upload_id', 'INTEGER')
            # New employee columns
            self._ensure_column('employees', 'role_level', 'TEXT')
            self._ensure_column('employees', 'weekly_capacity_minutes', 'INTEGER')
            self._ensure_column('patients', 'source_filename', 'TEXT')
            self._ensure_column('patients', 'source_uploaded_at', 'TEXT')
            self._ensure_column('patients', 'upload_id', 'INTEGER')
            # New patient columns
            self._ensure_column('patients', 'sat_sun_support', 'TEXT')
            self._ensure_column('patients', 'days_of_support', 'TEXT')
            self._ensure_column('patients', 'preference_of_carer', 'TEXT')
            self._ensure_column('patients', 'required_carer_support', 'INTEGER')
            self._ensure_column('patients', 'meal_prep_required', 'INTEGER')
            self._ensure_column('patients', 'breakfast_time', 'TEXT')
            self._ensure_column('patients', 'lunch_time', 'TEXT')
            self._ensure_column('patients', 'dinner_time', 'TEXT')
            # New assignments columns
            self._ensure_column('assignments', 'group_id', 'TEXT')
        except Exception as e:
            logger.warning(f"Column ensure failed: {e}")

    def _ensure_column(self, table: str, column: str, coltype: str):
        """Ensure a column exists on a table; add it if missing (SQLite)."""
        cur = self.conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        cols = [r[1] for r in cur.fetchall()]
        if column not in cols:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
            self.conn.commit()

    def store_employees(self, employees: List[Dict[str, Any]]):
        """Store employees in the database"""
        cursor = self.conn.cursor()
        
        # Clear existing employees
        cursor.execute("DELETE FROM employees")
        
        for emp in employees:
            cursor.execute('''
                INSERT INTO employees (
                    employee_id, name, address, postcode, gender, ethnicity, religion,
                    transport_mode, qualification, language_spoken, certificate_expiry_date,
                    earliest_start, latest_end, shifts, contact_number, notes,
                    source_filename, source_uploaded_at, upload_id,
                    role_level, weekly_capacity_minutes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                emp.get('EmployeeID'), emp.get('Name'), emp.get('Address'), emp.get('PostCode'),
                emp.get('Gender'), emp.get('Ethnicity'), emp.get('Religion'), emp.get('TransportMode'),
                emp.get('Qualification'), emp.get('LanguageSpoken'), emp.get('CertificateExpiryDate'),
                emp.get('EarliestStart'), emp.get('LatestEnd'), emp.get('Shifts'), emp.get('ContactNumber'),
                emp.get('Notes', ''),
                emp.get('SourceFilename'), emp.get('SourceUploadedAt'), emp.get('UploadID'),
                emp.get('RoleLevel'), emp.get('weekly_capacity_minutes')
            ))
        
        self.conn.commit()
        logger.info(f"Stored {len(employees)} employees in database")

    def store_patients(self, patients: List[Dict[str, Any]]):
        """Store patients in the database"""
        cursor = self.conn.cursor()
        
        # Clear existing patients
        cursor.execute("DELETE FROM patients")
        
        for pat in patients:
            cursor.execute('''
                INSERT INTO patients (
                    patient_id, patient_name, address, postcode, gender, ethnicity, religion,
                    required_support, required_hours_of_support, additional_requirements,
                    illness, contact_number, requires_medication, emergency_contact,
                    emergency_relation, language_preference, notes,
                    source_filename, source_uploaded_at, upload_id,
                    sat_sun_support, days_of_support, preference_of_carer, required_carer_support,
                    meal_prep_required, breakfast_time, lunch_time, dinner_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pat.get('PatientID'), pat.get('PatientName'), pat.get('Address'), pat.get('PostCode'),
                pat.get('Gender'), pat.get('Ethnicity'), pat.get('Religion'), pat.get('RequiredSupport'),
                pat.get('RequiredHoursOfSupport'), pat.get('AdditionalRequirements'), pat.get('Illness'),
                pat.get('ContactNumber'), pat.get('RequiresMedication'), pat.get('EmergencyContact'),
                pat.get('EmergencyRelation'), pat.get('LanguagePreference'), pat.get('Notes', ''),
                pat.get('SourceFilename'), pat.get('SourceUploadedAt'), pat.get('UploadID'),
                pat.get('SatSunSupport'), pat.get('DaysOfSupport'), pat.get('PreferenceOfCarer'), pat.get('RequiredCarerSupport'),
                (1 if pat.get('MealPrepRequired') in (True, 'Y', 'y', 'yes', 'Yes', 1) else 0),
                pat.get('BreakfastTime'), pat.get('LunchTime'), pat.get('DinnerTime')
            ))
        
        self.conn.commit()
        logger.info(f"Stored {len(patients)} patients in database")

    # --- Raw uploads ---
    def save_raw_upload(self, filename: str, sheets: Dict[str, Any]) -> int:
        """Store raw upload sheets as JSON and return upload id."""
        try:
            cursor = self.conn.cursor()
            payload = json.dumps(sheets)
            cursor.execute('''
                INSERT INTO raw_uploads (filename, sheets_json)
                VALUES (?, ?)
            ''', (filename, payload))
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error saving raw upload: {e}")
            return None

    def get_raw_uploads(self) -> List[Dict]:
        """List raw uploads with basic info."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, filename, uploaded_at FROM raw_uploads ORDER BY uploaded_at DESC")
            cols = [c[0] for c in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching raw uploads: {e}")
            return []

    def get_raw_upload(self, upload_id: int) -> Dict:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, filename, uploaded_at, sheets_json FROM raw_uploads WHERE id = ?", (upload_id,))
            row = cursor.fetchone()
            if not row:
                return None
            data = {
                "id": row[0],
                "filename": row[1],
                "uploaded_at": row[2],
                "sheets": {}
            }
            try:
                data["sheets"] = json.loads(row[3])
            except Exception:
                data["sheets"] = {}
            return data
        except Exception as e:
            logger.error(f"Error fetching raw upload {upload_id}: {e}")
            return None

    def get_raw_upload_sheet(self, upload_id: int, sheet_name: str) -> Dict:
        """Return columns and rows for a specific sheet from a raw upload."""
        try:
            data = self.get_raw_upload(upload_id)
            if not data:
                return None
            sheets = data.get("sheets", {})
            # Try exact, then case-insensitive match
            if sheet_name in sheets:
                rows = sheets[sheet_name]
            else:
                match = None
                for key in sheets.keys():
                    if key.lower() == sheet_name.lower():
                        match = key
                        break
                rows = sheets.get(match, []) if match else []
            # Sanitize rows for strict JSON (replace NaN/Inf with None)
            import math
            def _san(v):
                if isinstance(v, float):
                    if math.isnan(v) or math.isinf(v):
                        return None
                    return v
                if isinstance(v, dict):
                    return {k: _san(x) for k, x in v.items()}
                if isinstance(v, list):
                    return [_san(x) for x in v]
                return v
            safe_rows = [_san(r) for r in rows]
            columns = list(safe_rows[0].keys()) if safe_rows else []
            return {"columns": columns, "rows": safe_rows}
        except Exception as e:
            logger.error(f"Error fetching raw upload sheet: {e}")
            return {"columns": [], "rows": []}

    def get_employees(self) -> List[Dict]:
        """Get all employees from database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM employees ORDER BY employee_id")
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_patients(self) -> List[Dict]:
        """Get all patients from database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM patients ORDER BY patient_id")
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def log_data_upload(self, filename: str, employees_count: int, patients_count: int, status: str = "success"):
        """Log data upload operation"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO data_uploads (filename, employees_count, patients_count, status)
            VALUES (?, ?, ?, ?)
        ''', (filename, employees_count, patients_count, status))
        self.conn.commit()
        logger.info(f"Logged data upload: {filename} - {employees_count} employees, {patients_count} patients")

    def log_assignment(self, assignment: Dict[str, Any]) -> int:
        """Insert an assignment and return its row ID."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO assignments (
                employee_id, employee_name, patient_id, patient_name, service_type, assigned_time,
                start_time, end_time, duration, travel_time,
                priority_score, reasoning, group_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            assignment['employee_id'],
            assignment['employee_name'],
            assignment['patient_id'],
            assignment['patient_name'],
            assignment['service_type'],
            assignment['assigned_time'],
            assignment.get('start_time'),
            assignment.get('end_time'),
            assignment.get('estimated_duration'),
            assignment.get('travel_time'),
            assignment.get('priority_score'),
            assignment.get('assignment_reason'),
            assignment.get('group_id')
        ))
        self.conn.commit()
        row_id = cursor.lastrowid
        logger.info(f"Logged assignment: {assignment['employee_id']} to {assignment['patient_id']} (id={row_id})")
        return row_id

    def log_operation(self, operation_type: str, description: str, details: Dict[str, Any] = None):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO operations_log (operation_type, description, details)
            VALUES (?, ?, ?)
        ''', (operation_type, description, json.dumps(details) if details else None))
        self.conn.commit()
        logger.info(f"Logged operation: {operation_type} - {description}")

    def get_assignments(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM assignments ORDER BY created_at DESC")
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def update_assignment(self, assignment_id: int, updates: Dict[str, Any]) -> bool:
        """Update an existing assignment in the database"""
        try:
            cursor = self.conn.cursor()
            
            # Build dynamic UPDATE query based on provided updates
            set_clauses = []
            values = []
            
            for field, value in updates.items():
                if field in ['employee_id', 'employee_name', 'patient_id', 'patient_name', 
                           'service_type', 'assigned_time', 'start_time', 'end_time', 
                           'duration', 'travel_time', 'priority_score', 'reasoning']:
                    set_clauses.append(f"{field} = ?")
                    values.append(value)
            
            if not set_clauses:
                return False
                
            values.append(assignment_id)
            query = f"UPDATE assignments SET {', '.join(set_clauses)} WHERE id = ?"
            
            cursor.execute(query, values)
            self.conn.commit()
            
            updated_rows = cursor.rowcount
            logger.info(f"Updated assignment {assignment_id}: {updated_rows} rows affected")
            return updated_rows > 0
            
        except Exception as e:
            logger.error(f"Error updating assignment {assignment_id}: {str(e)}")
            return False
    
    def delete_assignment(self, assignment_id: int) -> bool:
        """Delete an assignment from the database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
            self.conn.commit()
            
            deleted_rows = cursor.rowcount
            logger.info(f"Deleted assignment {assignment_id}: {deleted_rows} rows affected")
            return deleted_rows > 0
            
        except Exception as e:
            logger.error(f"Error deleting assignment {assignment_id}: {str(e)}")
            return False
    
    def get_assignment_by_id(self, assignment_id: int) -> Dict:
        """Get a specific assignment by its ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM assignments WHERE id = ?", (assignment_id,))
            columns = [col[0] for col in cursor.description]
            result = cursor.fetchone()
            return dict(zip(columns, result)) if result else None
            
        except Exception as e:
            logger.error(f"Error fetching assignment {assignment_id}: {str(e)}")
            return None

    def get_logs(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM operations_log ORDER BY created_at DESC")
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_data_uploads(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM data_uploads ORDER BY upload_date DESC")
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    # --- Stats cache helpers ---
    def get_latest_stats(self) -> Dict:
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM stats_cache ORDER BY generated_at DESC LIMIT 1')
            row = cursor.fetchone()
            if not row:
                return None
            columns = [col[0] for col in cursor.description]
            data = dict(zip(columns, row))
            # Parse JSON metrics
            try:
                data['metrics'] = json.loads(data.pop('metrics_json'))
            except Exception:
                data['metrics'] = {}
            return data
        except Exception as e:
            logger.error(f"Error reading latest stats: {e}")
            return None

    def save_stats(self, assignments_count: int, metrics: Dict, ai_summary: str = None, ai_ideas: str = None) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO stats_cache (generated_at, assignments_count, metrics_json, ai_summary, ai_ideas)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                assignments_count,
                json.dumps(metrics),
                ai_summary,
                ai_ideas
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
            return False

    # Notification methods
    def create_notification(self, notification_id: str, notification_type: str, title: str, message: str, action_type: str = None, action_data: Dict = None) -> bool:
        """Create a new notification"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO notifications (
                    notification_id, type, title, message, action_type, action_data
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                notification_id,
                notification_type,
                title,
                message,
                action_type,
                json.dumps(action_data) if action_data else None
            ))
            self.conn.commit()
            logger.info(f"Created notification: {notification_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return False

    def get_notifications(self, include_deleted: bool = False, limit: int = 50) -> List[Dict]:
        """Get notifications with optional filtering"""
        cursor = self.conn.cursor()
        
        if include_deleted:
            cursor.execute('''
                SELECT * FROM notifications 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
        else:
            cursor.execute('''
                SELECT * FROM notifications 
                WHERE is_deleted = FALSE 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
        
        columns = [col[0] for col in cursor.description]
        notifications = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Parse action_data JSON
        for notification in notifications:
            if notification.get('action_data'):
                try:
                    notification['action_data'] = json.loads(notification['action_data'])
                except:
                    notification['action_data'] = None
        
        return notifications

    def get_unread_notifications_count(self) -> int:
        """Get count of unread notifications"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM notifications 
            WHERE is_read = FALSE AND is_deleted = FALSE
        ''')
        return cursor.fetchone()[0]

    def mark_notification_read(self, notification_id: str) -> bool:
        """Mark a notification as read"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE notifications 
                SET is_read = TRUE, read_at = CURRENT_TIMESTAMP 
                WHERE notification_id = ?
            ''', (notification_id,))
            self.conn.commit()
            logger.info(f"Marked notification as read: {notification_id}")
            return True
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False

    def mark_notification_deleted(self, notification_id: str) -> bool:
        """Mark a notification as deleted"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE notifications 
                SET is_deleted = TRUE, deleted_at = CURRENT_TIMESTAMP 
                WHERE notification_id = ?
            ''', (notification_id,))
            self.conn.commit()
            logger.info(f"Marked notification as deleted: {notification_id}")
            return True
        except Exception as e:
            logger.error(f"Error marking notification as deleted: {e}")
            return False

    def mark_all_notifications_read(self) -> bool:
        """Mark all notifications as read"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE notifications 
                SET is_read = TRUE, read_at = CURRENT_TIMESTAMP 
                WHERE is_read = FALSE AND is_deleted = FALSE
            ''')
            self.conn.commit()
            logger.info("Marked all notifications as read")
            return True
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            return False

    def delete_all_notifications(self) -> bool:
        """Delete all notifications"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE notifications 
                SET is_deleted = TRUE, deleted_at = CURRENT_TIMESTAMP 
                WHERE is_deleted = FALSE
            ''')
            self.conn.commit()
            logger.info("Deleted all notifications")
            return True
        except Exception as e:
            logger.error(f"Error deleting all notifications: {e}")
            return False

    def has_data(self) -> bool:
        """Check if there's any data in the database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees")
        employee_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM patients")
        patient_count = cursor.fetchone()[0]
        return employee_count > 0 or patient_count > 0

    def clear_all_data(self):
        """Clear all data from database (for testing/reset)"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM employees")
        cursor.execute("DELETE FROM patients")
        cursor.execute("DELETE FROM assignments")
        cursor.execute("DELETE FROM unassigned")
        cursor.execute("DELETE FROM unassigned_summaries")
        cursor.execute("DELETE FROM operations_log")
        cursor.execute("DELETE FROM data_uploads")
        cursor.execute("DELETE FROM notifications")
        self.conn.commit()
        logger.info("Cleared all data from database")

    def clear_employees(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM employees")
            self.conn.commit()
            logger.info("Cleared all employees from database")
            return True
        except Exception as e:
            logger.error(f"Error clearing employees: {e}")
            return False

    def clear_patients(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM patients")
            self.conn.commit()
            logger.info("Cleared all patients from database")
            return True
        except Exception as e:
            logger.error(f"Error clearing patients: {e}")
            return False

    def clear_employees_and_patients(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM employees")
            cursor.execute("DELETE FROM patients")
            self.conn.commit()
            logger.info("Cleared all employees and patients from database")
            return True
        except Exception as e:
            logger.error(f"Error clearing employees and patients: {e}")
            return False

    def clear_unassigned(self) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM unassigned")
            cursor.execute("DELETE FROM unassigned_summaries")
            self.conn.commit()
            logger.info("Cleared unassigned data and summaries from database")
            return True
        except Exception as e:
            logger.error(f"Error clearing unassigned: {e}")
            return False

    def close(self):
        self.conn.close() 

    # --- Scheduling helpers ---
    def has_overlap_for_employee(self, employee_id: str, start_iso: str, end_iso: str) -> bool:
        """Check if an employee has any assignment overlapping the given interval.

        Only ISO-like datetime rows are considered for robust comparison.
        """
        try:
            from datetime import datetime

            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT start_time, end_time FROM assignments WHERE employee_id = ?",
                (employee_id,)
            )
            rows = cursor.fetchall()

            try:
                new_start = datetime.fromisoformat(start_iso)
                new_end = datetime.fromisoformat(end_iso)
            except Exception:
                # If the proposed times aren't ISO, fail-safe to no-overlap
                return False

            for row in rows:
                existing_start_raw, existing_end_raw = row[0], row[1]
                if not existing_start_raw or not existing_end_raw:
                    continue
                try:
                    existing_start = datetime.fromisoformat(existing_start_raw)
                    existing_end = datetime.fromisoformat(existing_end_raw)
                except Exception:
                    # Skip non-ISO rows (legacy HH:MM values)
                    continue

                # Overlap if intervals intersect
                if not (existing_end <= new_start or existing_start >= new_end):
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking overlap for employee {employee_id}: {e}")
            return False

    def get_overlapping_assignments_for_employee(self, employee_id: str, start_iso: str, end_iso: str) -> List[Dict]:
        """Return list of overlapping assignment rows for an employee in [start_iso, end_iso].

        Only rows with ISO-like datetimes are considered for comparison.
        """
        try:
            from datetime import datetime
            try:
                new_start = datetime.fromisoformat(start_iso)
                new_end = datetime.fromisoformat(end_iso)
            except Exception:
                return []
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM assignments WHERE employee_id = ?",
                (employee_id,)
            )
            columns = [col[0] for col in cursor.description]
            results: List[Dict] = []
            for row in cursor.fetchall():
                data = dict(zip(columns, row))
                st = data.get('start_time')
                en = data.get('end_time')
                if not st or not en:
                    continue
                try:
                    est = datetime.fromisoformat(st)
                    een = datetime.fromisoformat(en)
                except Exception:
                    continue
                if not (een <= new_start or est >= new_end):
                    results.append(data)
            return results
        except Exception as e:
            logger.error(f"Error fetching overlapping assignments for employee {employee_id}: {e}")
            return []

    def has_employee_patient_assignment_on_date(self, employee_id: str, patient_id: str, date_iso: str) -> bool:
        """Check if an employee already has an assignment with the patient on the given date.

        date_iso can be any ISO datetime on that date; SQLite DATE() will extract the date.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT 1 FROM assignments
                WHERE employee_id = ?
                  AND patient_id = ?
                  AND DATE(start_time) = DATE(?)
                LIMIT 1
                """,
                (employee_id, patient_id, date_iso)
            )
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking employee-patient daily assignment ({employee_id}, {patient_id}): {e}")
            return False

    def get_employee_patient_assignments_on_date(self, employee_id: str, patient_id: str, date_iso: str) -> List[Dict]:
        """Return all assignments for the given employee↔patient on the specified date."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT * FROM assignments
                WHERE employee_id = ?
                  AND patient_id = ?
                  AND DATE(start_time) = DATE(?)
                ORDER BY start_time ASC
                """,
                (employee_id, patient_id, date_iso)
            )
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching employee-patient assignments on date: {e}")
            return []

    def get_assignments_for_patient_on_date(self, patient_id: str, date_iso: str) -> List[Dict]:
        """Return assignments for a patient on a date, sorted by start_time."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT * FROM assignments
                WHERE patient_id = ?
                  AND DATE(start_time) = DATE(?)
                ORDER BY start_time ASC
                """,
                (patient_id, date_iso)
            )
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching patient assignments for date: {e}")
            return []

    def get_employee_assignments_for_date(self, employee_id: str, date_iso: str) -> List[Dict]:
        """Return assignments for an employee on a date, sorted by start_time."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT * FROM assignments
                WHERE employee_id = ?
                  AND DATE(start_time) = DATE(?)
                ORDER BY start_time ASC
                """,
                (employee_id, date_iso)
            )
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching employee assignments for date: {e}")
            return []

    def get_employee_assignments_for_week(self, employee_id: str, start_date_iso: str, end_date_iso: str) -> List[Dict]:
        """Return assignments for an employee in [start_date, end_date], sorted by start_time."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT * FROM assignments
                WHERE employee_id = ?
                  AND DATE(start_time) BETWEEN DATE(?) AND DATE(?)
                ORDER BY start_time ASC
                """,
                (employee_id, start_date_iso, end_date_iso)
            )
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching employee assignments for week: {e}")
            return []

    def get_assignments_for_week(self, start_date_iso: str, end_date_iso: str) -> List[Dict]:
        """Return all assignments in [start_date, end_date], sorted by start_time."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT * FROM assignments
                WHERE DATE(start_time) BETWEEN DATE(?) AND DATE(?)
                ORDER BY start_time ASC
                """,
                (start_date_iso, end_date_iso)
            )
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching assignments for week: {e}")
            return []

    def sum_employee_minutes_for_week(self, employee_id: str, week_start_iso: str, week_end_iso: str) -> int:
        """Sum of assignment durations for employee across the given ISO week window."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT COALESCE(SUM(duration), 0) FROM assignments
                WHERE employee_id = ?
                  AND DATE(start_time) BETWEEN DATE(?) AND DATE(?)
                """,
                (employee_id, week_start_iso, week_end_iso)
            )
            row = cursor.fetchone()
            return int(row[0]) if row and row[0] is not None else 0
        except Exception as e:
            logger.error(f"Error summing weekly minutes for {employee_id}: {e}")
            return 0

    def count_patient_overlaps(self, patient_id: str, start_iso: str, end_iso: str) -> int:
        """Count concurrent assignments for a patient overlapping [start_iso, end_iso]."""
        try:
            from datetime import datetime
            # Ensure proposed times are ISO parseable
            try:
                new_start = datetime.fromisoformat(start_iso)
                new_end = datetime.fromisoformat(end_iso)
            except Exception:
                return 0
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT start_time, end_time FROM assignments
                WHERE patient_id = ?
                """,
                (patient_id,)
            )
            rows = cursor.fetchall()
            overlaps = 0
            for st, en in rows:
                if not st or not en:
                    continue
                try:
                    est = datetime.fromisoformat(st)
                    een = datetime.fromisoformat(en)
                except Exception:
                    continue
                if not (een <= new_start or est >= new_end):
                    overlaps += 1
            return overlaps
        except Exception as e:
            logger.error(f"Error counting overlaps for patient {patient_id}: {e}")
            return 0

    def get_overlapping_assignments_for_patient(self, patient_id: str, start_iso: str, end_iso: str) -> List[Dict]:
        """Return assignments for a patient that overlap [start_iso, end_iso]."""
        try:
            from datetime import datetime
            try:
                new_start = datetime.fromisoformat(start_iso)
                new_end = datetime.fromisoformat(end_iso)
            except Exception:
                return []
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT * FROM assignments
                WHERE patient_id = ?
                """,
                (patient_id,)
            )
            columns = [col[0] for col in cursor.description]
            results: List[Dict] = []
            for row in cursor.fetchall():
                data = dict(zip(columns, row))
                st = data.get('start_time')
                en = data.get('end_time')
                if not st or not en:
                    continue
                try:
                    est = datetime.fromisoformat(st)
                    een = datetime.fromisoformat(en)
                except Exception:
                    continue
                if not (een <= new_start or est >= new_end):
                    results.append(data)
            return results
        except Exception as e:
            logger.error(f"Error fetching overlapping assignments for patient {patient_id}: {e}")
            return []

    # --- Unassigned logging and queries ---
    def log_unassigned(self, entity_type: str, entity_id: str, date_iso: str, reasons: List[str], context: Dict[str, Any] | None = None) -> int:
        """Log an unassigned record for a patient or employee with reasons (JSON).

        entity_type: 'patient' | 'employee'
        date_iso: any ISO datetime or date string; DATE() will normalize
        reasons: list of strings (will be de-duplicated here for compactness)
        context: optional dict for additional context details
        """
        try:
            # Normalize reasons (dedupe, trim)
            unique_reasons = []
            seen = set()
            for r in reasons or []:
                try:
                    key = (r or '').strip()
                except Exception:
                    key = str(r)
                if key and key not in seen:
                    seen.add(key)
                    unique_reasons.append(key)
            payload_reasons = json.dumps(unique_reasons or ["No feasible assignment found"])
            payload_context = json.dumps(context) if context else None
            cursor = self.conn.cursor()
            cursor.execute(
                '''
                INSERT INTO unassigned (entity_type, entity_id, date, reasons, context)
                VALUES (?, ?, DATE(?), ?, ?)
                ''',
                (entity_type, entity_id, date_iso, payload_reasons, payload_context)
            )
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error logging unassigned for {entity_type} {entity_id} on {date_iso}: {e}")
            return None

    def _fetch_unassigned_rows(self, entity_type: str, week_start_iso: str, week_end_iso: str) -> List[Dict[str, Any]]:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                '''
                SELECT id, entity_type, entity_id, date, reasons, context, created_at
                FROM unassigned
                WHERE entity_type = ? AND DATE(date) BETWEEN DATE(?) AND DATE(?)
                ORDER BY date ASC, created_at ASC
                ''',
                (entity_type, week_start_iso, week_end_iso)
            )
            cols = [c[0] for c in cursor.description]
            rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
            # Parse JSON fields
            for r in rows:
                try:
                    r['reasons'] = json.loads(r.get('reasons') or '[]')
                except Exception:
                    r['reasons'] = []
                try:
                    r['context'] = json.loads(r.get('context') or '{}')
                except Exception:
                    r['context'] = {}
            return rows
        except Exception as e:
            logger.error(f"Error fetching unassigned rows: {e}")
            return []

    def get_unassigned_patients_for_week(self, week_start_iso: str, week_end_iso: str) -> List[Dict[str, Any]]:
        """Return aggregated unassigned patients for the week with merged reasons per patient/date."""
        rows = self._fetch_unassigned_rows('patient', week_start_iso, week_end_iso)
        aggregated: Dict[tuple, Dict[str, Any]] = {}
        for r in rows:
            key = (r.get('entity_id'), r.get('date'))
            entry = aggregated.get(key)
            if not entry:
                aggregated[key] = {
                    'patient_id': r.get('entity_id'),
                    'date': r.get('date'),
                    'reasons': list(r.get('reasons') or []),
                    'context': r.get('context') or {},
                }
            else:
                # Merge reasons/context
                seen = set(entry['reasons'])
                for rr in r.get('reasons') or []:
                    if rr not in seen:
                        entry['reasons'].append(rr)
                        seen.add(rr)
                # Context merge with special handling for list fields
                try:
                    incoming_ctx = r.get('context') or {}
                    existing_ctx = entry['context']
                    # Merge generic scalar keys if missing
                    for k, v in incoming_ctx.items():
                        if k not in existing_ctx and not isinstance(v, list):
                            existing_ctx[k] = v
                    def _dedupe_objects(items: List[Dict[str, Any]], key_fn):
                        seen_keys = set()
                        out = []
                        for it in items:
                            try:
                                k = key_fn(it)
                            except Exception:
                                k = None
                            key_tuple = tuple(k) if isinstance(k, (list, tuple)) else k
                            if key_tuple in seen_keys:
                                continue
                            seen_keys.add(key_tuple)
                            out.append(it)
                        return out
                    # Merge lists by de-duplicating
                    def _merge_list(key: str, uniq_key_getter):
                        inc = incoming_ctx.get(key) or []
                        if not isinstance(inc, list):
                            return
                        ex = existing_ctx.get(key) or []
                        existing_ctx[key] = _dedupe_objects(ex + inc, uniq_key_getter)
                    _merge_list('issues', lambda d: (d.get('type'), d.get('assignment_ids'), d.get('details')))
                    _merge_list('attempts', lambda d: (
                        d.get('employee_id'), d.get('patient_id'), d.get('service_type'), d.get('start_time'), d.get('end_time'),
                        tuple(d.get('violations') or [])
                    ))
                    if isinstance(incoming_ctx.get('suggestions'), dict):
                        ex_sug = existing_ctx.get('suggestions') or {}
                        in_sug = incoming_ctx['suggestions']
                        # potential_employees
                        if isinstance(in_sug.get('potential_employees'), list):
                            ex_list = ex_sug.get('potential_employees') or []
                            merged = _dedupe_objects(ex_list + in_sug.get('potential_employees', []), lambda d: d.get('employee_id'))
                            ex_sug['potential_employees'] = merged
                        # potential_patients
                        if isinstance(in_sug.get('potential_patients'), list):
                            ex_list = ex_sug.get('potential_patients') or []
                            merged = _dedupe_objects(ex_list + in_sug.get('potential_patients', []), lambda d: d.get('patient_id'))
                            ex_sug['potential_patients'] = merged
                        existing_ctx['suggestions'] = ex_sug
                except Exception:
                    pass
        return list(aggregated.values())

    def get_unassigned_employees_for_week(self, week_start_iso: str, week_end_iso: str) -> List[Dict[str, Any]]:
        """Return aggregated unassigned employees for the week with merged reasons per employee/date."""
        rows = self._fetch_unassigned_rows('employee', week_start_iso, week_end_iso)
        aggregated: Dict[tuple, Dict[str, Any]] = {}
        for r in rows:
            key = (r.get('entity_id'), r.get('date'))
            entry = aggregated.get(key)
            if not entry:
                aggregated[key] = {
                    'employee_id': r.get('entity_id'),
                    'date': r.get('date'),
                    'reasons': list(r.get('reasons') or []),
                    'context': r.get('context') or {},
                }
            else:
                seen = set(entry['reasons'])
                for rr in r.get('reasons') or []:
                    if rr not in seen:
                        entry['reasons'].append(rr)
                        seen.add(rr)
                try:
                    incoming_ctx = r.get('context') or {}
                    existing_ctx = entry['context']
                    for k, v in incoming_ctx.items():
                        if k not in existing_ctx and not isinstance(v, list):
                            existing_ctx[k] = v
                    def _dedupe_objects(items: List[Dict[str, Any]], key_fn):
                        seen_keys = set()
                        out = []
                        for it in items:
                            try:
                                k = key_fn(it)
                            except Exception:
                                k = None
                            key_tuple = tuple(k) if isinstance(k, (list, tuple)) else k
                            if key_tuple in seen_keys:
                                continue
                            seen_keys.add(key_tuple)
                            out.append(it)
                        return out
                    def _merge_list(key: str, uniq_key_getter):
                        inc = incoming_ctx.get(key) or []
                        if not isinstance(inc, list):
                            return
                        ex = existing_ctx.get(key) or []
                        existing_ctx[key] = _dedupe_objects(ex + inc, uniq_key_getter)
                    _merge_list('issues', lambda d: (d.get('type'), d.get('assignment_ids'), d.get('details')))
                    _merge_list('attempts', lambda d: (
                        d.get('employee_id'), d.get('patient_id'), d.get('service_type'), d.get('start_time'), d.get('end_time'),
                        tuple(d.get('violations') or [])
                    ))
                    if isinstance(incoming_ctx.get('suggestions'), dict):
                        ex_sug = existing_ctx.get('suggestions') or {}
                        in_sug = incoming_ctx['suggestions']
                        if isinstance(in_sug.get('potential_employees'), list):
                            ex_list = ex_sug.get('potential_employees') or []
                            merged = _dedupe_objects(ex_list + in_sug.get('potential_employees', []), lambda d: d.get('employee_id'))
                            ex_sug['potential_employees'] = merged
                        if isinstance(in_sug.get('potential_patients'), list):
                            ex_list = ex_sug.get('potential_patients') or []
                            merged = _dedupe_objects(ex_list + in_sug.get('potential_patients', []), lambda d: d.get('patient_id'))
                            ex_sug['potential_patients'] = merged
                        existing_ctx['suggestions'] = ex_sug
                except Exception:
                    pass
        return list(aggregated.values())

    def get_unassigned_for_entity_week(self, entity_type: str, entity_id: str, week_start_iso: str, week_end_iso: str) -> List[Dict[str, Any]]:
        """Return raw unassigned rows for a specific entity across a week (ordered by date)."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                '''
                SELECT id, entity_type, entity_id, date, reasons, context, created_at
                FROM unassigned
                WHERE entity_type = ? AND entity_id = ? AND DATE(date) BETWEEN DATE(?) AND DATE(?)
                ORDER BY date ASC, created_at ASC
                ''',
                (entity_type, entity_id, week_start_iso, week_end_iso)
            )
            cols = [c[0] for c in cursor.description]
            rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
            for r in rows:
                try:
                    r['reasons'] = json.loads(r.get('reasons') or '[]')
                except Exception:
                    r['reasons'] = []
                try:
                    r['context'] = json.loads(r.get('context') or '{}')
                except Exception:
                    r['context'] = {}
            return rows
        except Exception as e:
            logger.error(f"Error fetching unassigned for {entity_type} {entity_id}: {e}")
            return []

    # --- Unassigned summaries cache ---
    def get_unassigned_summary(self, entity_type: str, entity_id: str, week_start_iso: str, week_end_iso: str) -> Dict[str, Any] | None:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                '''
                SELECT entity_type, entity_id, week_start, week_end, summary, reasons, dates, created_at
                FROM unassigned_summaries
                WHERE entity_type = ? AND entity_id = ? AND week_start = ? AND week_end = ?
                LIMIT 1
                ''',
                (entity_type, entity_id, week_start_iso, week_end_iso)
            )
            row = cursor.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cursor.description]
            data = dict(zip(cols, row))
            # Parse JSON arrays
            try:
                data['reasons'] = json.loads(data.get('reasons') or '[]')
            except Exception:
                data['reasons'] = []
            try:
                data['dates'] = json.loads(data.get('dates') or '[]')
            except Exception:
                data['dates'] = []
            return data
        except Exception as e:
            logger.error(f"Error reading unassigned summary cache: {e}")
            return None

    def save_unassigned_summary(self, entity_type: str, entity_id: str, week_start_iso: str, week_end_iso: str, summary: str, reasons: List[str], dates: List[str]) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                '''
                INSERT INTO unassigned_summaries (entity_type, entity_id, week_start, week_end, summary, reasons, dates)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(entity_type, entity_id, week_start, week_end)
                DO UPDATE SET summary=excluded.summary, reasons=excluded.reasons, dates=excluded.dates, created_at=CURRENT_TIMESTAMP
                ''',
                (entity_type, entity_id, week_start_iso, week_end_iso, summary, json.dumps(reasons or []), json.dumps(dates or []))
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving unassigned summary: {e}")
            return False

    # --- Simple transaction helpers ---
    def begin_transaction(self):
        try:
            self.conn.execute('BEGIN')
            return True
        except Exception as e:
            logger.error(f"BEGIN transaction failed: {e}")
            return False

    def commit(self):
        try:
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"COMMIT failed: {e}")
            return False

    def rollback(self):
        try:
            self.conn.rollback()
            return True
        except Exception as e:
            logger.error(f"ROLLBACK failed: {e}")
            return False