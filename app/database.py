import sqlite3
from datetime import datetime
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "rota_operations.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Table for assignments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                patient_id TEXT NOT NULL,
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
        
        self.conn.commit()

    def log_assignment(self, assignment: Dict[str, Any]):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO assignments (
                employee_id, patient_id, service_type, assigned_time,
                start_time, end_time, duration, travel_time,
                priority_score, reasoning
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            assignment['employee_id'],
            assignment['patient_id'],
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
        ''', (operation_type, description, str(details) if details else None))
        self.conn.commit()
        logger.info(f"Logged operation: {operation_type} - {description}")

    def get_assignments(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM assignments")
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_logs(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM operations_log")
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def close(self):
        self.conn.close() 