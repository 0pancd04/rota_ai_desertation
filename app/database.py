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
                    earliest_start, latest_end, shifts, contact_number, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                emp['EmployeeID'], emp['Name'], emp['Address'], emp['PostCode'],
                emp['Gender'], emp['Ethnicity'], emp['Religion'], emp['TransportMode'],
                emp['Qualification'], emp['LanguageSpoken'], emp['CertificateExpiryDate'],
                emp['EarliestStart'], emp['LatestEnd'], emp['Shifts'], emp['ContactNumber'],
                emp.get('Notes', '')
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
                    emergency_relation, language_preference, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pat['PatientID'], pat['PatientName'], pat['Address'], pat['PostCode'],
                pat['Gender'], pat['Ethnicity'], pat['Religion'], pat['RequiredSupport'],
                pat['RequiredHoursOfSupport'], pat['AdditionalRequirements'], pat['Illness'],
                pat['ContactNumber'], pat['RequiresMedication'], pat['EmergencyContact'],
                pat['EmergencyRelation'], pat['LanguagePreference'], pat.get('Notes', '')
            ))
        
        self.conn.commit()
        logger.info(f"Stored {len(patients)} patients in database")

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

    def log_assignment(self, assignment: Dict[str, Any]):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO assignments (
                employee_id, employee_name, patient_id, patient_name, service_type, assigned_time,
                start_time, end_time, duration, travel_time,
                priority_score, reasoning
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            assignment.get('assignment_reason')
        ))
        self.conn.commit()
        logger.info(f"Logged assignment: {assignment['employee_id']} to {assignment['patient_id']}")

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
        cursor.execute("DELETE FROM operations_log")
        cursor.execute("DELETE FROM data_uploads")
        cursor.execute("DELETE FROM notifications")
        self.conn.commit()
        logger.info("Cleared all data from database")

    def close(self):
        self.conn.close() 