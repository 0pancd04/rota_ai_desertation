import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from ..models.filter_schemas import FilterConfig, FilterGroup, FilterCondition, FilterSuggestion, FilterPageConfig
from ..database import DatabaseManager

class FilterService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._init_filter_tables()

    def _init_filter_tables(self):
        """Initialize filter-related tables in database"""
        cursor = self.db_manager.conn.cursor()
        
        # Table for saved filter configurations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS filter_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_id TEXT UNIQUE NOT NULL,
                page TEXT NOT NULL,
                filters TEXT NOT NULL,
                sort_by TEXT,
                sort_order TEXT DEFAULT 'asc',
                page_size INTEGER DEFAULT 50,
                page_number INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.db_manager.conn.commit()

    def save_filter_config(self, page: str, filters: List[FilterGroup], 
                          sort_by: str = None, sort_order: str = "asc",
                          page_size: int = 50, page_number: int = 1) -> str:
        """Save filter configuration to database"""
        config_id = str(uuid.uuid4())
        
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            INSERT INTO filter_configs (
                config_id, page, filters, sort_by, sort_order, page_size, page_number
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            config_id,
            page,
            json.dumps([group.dict() for group in filters]),
            sort_by,
            sort_order,
            page_size,
            page_number
        ))
        
        self.db_manager.conn.commit()
        return config_id

    def get_filter_config(self, page: str) -> Optional[FilterConfig]:
        """Get the latest filter configuration for a page"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            SELECT * FROM filter_configs 
            WHERE page = ? 
            ORDER BY updated_at DESC 
            LIMIT 1
        ''', (page,))
        
        row = cursor.fetchone()
        if row:
            columns = [col[0] for col in cursor.description]
            data = dict(zip(columns, row))
            
            filters_data = json.loads(data['filters'])
            filters = [FilterGroup(**group) for group in filters_data]
            
            return FilterConfig(
                page=data['page'],
                filters=filters,
                sort_by=data['sort_by'],
                sort_order=data['sort_order'],
                page_size=data['page_size'],
                page_number=data['page_number'],
                created_at=datetime.fromisoformat(data['created_at']),
                updated_at=datetime.fromisoformat(data['updated_at'])
            )
        
        return None

    def update_filter_config(self, page: str, filters: List[FilterGroup], 
                           sort_by: str = None, sort_order: str = "asc",
                           page_size: int = 50, page_number: int = 1) -> str:
        """Update existing filter configuration or create new one"""
        # Delete existing config for this page
        cursor = self.db_manager.conn.cursor()
        cursor.execute('DELETE FROM filter_configs WHERE page = ?', (page,))
        
        # Save new config
        return self.save_filter_config(page, filters, sort_by, sort_order, page_size, page_number)

    def get_assignment_filter_suggestions(self) -> FilterPageConfig:
        """Get filter suggestions for assignments page"""
        suggestions = [
            FilterSuggestion(
                field="employee_name",
                label="Employee Name",
                type="text",
                placeholder="Enter employee name"
            ),
            FilterSuggestion(
                field="patient_name",
                label="Patient Name",
                type="text",
                placeholder="Enter patient name"
            ),
            FilterSuggestion(
                field="service_type",
                label="Service Type",
                type="select",
                options=[
                    {"value": "medicine", "label": "Medicine"},
                    {"value": "exercise", "label": "Exercise"},
                    {"value": "companionship", "label": "Companionship"},
                    {"value": "personal_care", "label": "Personal Care"}
                ]
            ),
            FilterSuggestion(
                field="priority_score",
                label="Priority Score",
                type="number",
                min_value=1,
                max_value=10,
                placeholder="Enter priority score"
            ),
            FilterSuggestion(
                field="travel_time",
                label="Travel Time (minutes)",
                type="number",
                min_value=0,
                max_value=300,
                placeholder="Enter travel time"
            ),
            FilterSuggestion(
                field="assigned_time",
                label="Assigned Time",
                type="date",
                placeholder="Select date"
            ),
            FilterSuggestion(
                field="is_unassigned",
                label="Unassigned Patients",
                type="select",
                options=[
                    {"value": "true", "label": "Show Unassigned Only"},
                    {"value": "false", "label": "Show Assigned Only"}
                ]
            )
        ]
        
        return FilterPageConfig(page="assignments", suggestions=suggestions)

    def get_employee_filter_suggestions(self) -> FilterPageConfig:
        """Get filter suggestions for employees page"""
        suggestions = [
            FilterSuggestion(
                field="name",
                label="Employee Name",
                type="text",
                placeholder="Enter employee name"
            ),
            FilterSuggestion(
                field="qualification",
                label="Qualification",
                type="select",
                options=[
                    {"value": "nurse", "label": "Nurse"},
                    {"value": "carer", "label": "Carer"},
                    {"value": "specialist", "label": "Specialist"}
                ]
            ),
            FilterSuggestion(
                field="language_spoken",
                label="Language",
                type="text",
                placeholder="Enter language"
            ),
            FilterSuggestion(
                field="transport_mode",
                label="Transport Mode",
                type="select",
                options=[
                    {"value": "car", "label": "Car"},
                    {"value": "public_transport", "label": "Public Transport"},
                    {"value": "walking", "label": "Walking"}
                ]
            ),
            FilterSuggestion(
                field="available_hours",
                label="Available Hours",
                type="number",
                min_value=0,
                max_value=168,
                placeholder="Enter available hours"
            ),
            FilterSuggestion(
                field="is_available",
                label="Availability",
                type="select",
                options=[
                    {"value": "true", "label": "Available"},
                    {"value": "false", "label": "Unavailable"}
                ]
            )
        ]
        
        return FilterPageConfig(page="employees", suggestions=suggestions)

    def get_patient_filter_suggestions(self) -> FilterPageConfig:
        """Get filter suggestions for patients page"""
        suggestions = [
            FilterSuggestion(
                field="patient_name",
                label="Patient Name",
                type="text",
                placeholder="Enter patient name"
            ),
            FilterSuggestion(
                field="required_support",
                label="Required Support",
                type="select",
                options=[
                    {"value": "medicine", "label": "Medicine"},
                    {"value": "exercise", "label": "Exercise"},
                    {"value": "companionship", "label": "Companionship"},
                    {"value": "personal_care", "label": "Personal Care"}
                ]
            ),
            FilterSuggestion(
                field="required_hours_of_support",
                label="Required Hours",
                type="number",
                min_value=1,
                max_value=168,
                placeholder="Enter required hours"
            ),
            FilterSuggestion(
                field="requires_medication",
                label="Requires Medication",
                type="select",
                options=[
                    {"value": "yes", "label": "Yes"},
                    {"value": "no", "label": "No"}
                ]
            ),
            FilterSuggestion(
                field="is_assigned",
                label="Assignment Status",
                type="select",
                options=[
                    {"value": "true", "label": "Assigned"},
                    {"value": "false", "label": "Unassigned"}
                ]
            )
        ]
        
        return FilterPageConfig(page="patients", suggestions=suggestions)

    def apply_filters_to_assignments(self, filters: List[FilterGroup]) -> List[Dict]:
        """Apply filters to assignments data"""
        assignments = self.db_manager.get_assignments()
        
        if not filters:
            return assignments
        
        filtered_assignments = []
        
        for assignment in assignments:
            if self._evaluate_filters(assignment, filters):
                filtered_assignments.append(assignment)
        
        return filtered_assignments

    def apply_filters_to_employees(self, filters: List[FilterGroup]) -> List[Dict]:
        """Apply filters to employees data"""
        employees = self.db_manager.get_employees()
        
        if not filters:
            return employees
        
        filtered_employees = []
        
        for employee in employees:
            # Calculate available hours based on assignments
            available_hours = self._calculate_employee_available_hours(employee)
            employee['available_hours'] = available_hours
            employee['is_available'] = available_hours > 0
            
            if self._evaluate_filters(employee, filters):
                filtered_employees.append(employee)
        
        return filtered_employees

    def apply_filters_to_patients(self, filters: List[FilterGroup]) -> List[Dict]:
        """Apply filters to patients data"""
        patients = self.db_manager.get_patients()
        assignments = self.db_manager.get_assignments()
        
        if not filters:
            return patients
        
        # Add assignment status to patients
        assigned_patient_ids = {a['patient_id'] for a in assignments}
        
        for patient in patients:
            patient['is_assigned'] = patient['patient_id'] in assigned_patient_ids
        
        filtered_patients = []
        
        for patient in patients:
            if self._evaluate_filters(patient, filters):
                filtered_patients.append(patient)
        
        return filtered_patients

    def _evaluate_filters(self, item: Dict, filters: List[FilterGroup]) -> bool:
        """Evaluate if an item matches the given filters"""
        for group in filters:
            group_result = True
            
            for condition in group.conditions:
                condition_result = self._evaluate_condition(item, condition)
                
                if group.operator == "AND":
                    group_result = group_result and condition_result
                else:  # OR
                    group_result = group_result or condition_result
            
            if not group_result:
                return False
        
        return True

    def _evaluate_condition(self, item: Dict, condition: FilterCondition) -> bool:
        """Evaluate a single filter condition"""
        field_value = item.get(condition.field)
        
        if condition.operator.value == "equals":
            return field_value == condition.value
        elif condition.operator.value == "not_equals":
            return field_value != condition.value
        elif condition.operator.value == "contains":
            return str(field_value).lower().find(str(condition.value).lower()) != -1
        elif condition.operator.value == "not_contains":
            return str(field_value).lower().find(str(condition.value).lower()) == -1
        elif condition.operator.value == "greater_than":
            return field_value > condition.value
        elif condition.operator.value == "less_than":
            return field_value < condition.value
        elif condition.operator.value == "greater_than_equal":
            return field_value >= condition.value
        elif condition.operator.value == "less_than_equal":
            return field_value <= condition.value
        elif condition.operator.value == "in":
            return field_value in condition.value
        elif condition.operator.value == "not_in":
            return field_value not in condition.value
        elif condition.operator.value == "between":
            return condition.value <= field_value <= condition.value2
        elif condition.operator.value == "is_null":
            return field_value is None
        elif condition.operator.value == "is_not_null":
            return field_value is not None
        
        return True

    def _calculate_employee_available_hours(self, employee: Dict) -> int:
        """Calculate available hours for an employee based on assignments"""
        assignments = self.db_manager.get_assignments()
        employee_assignments = [a for a in assignments if a['employee_id'] == employee['employee_id']]
        
        # Calculate total assigned hours
        total_assigned_hours = sum(
            a.get('duration', 0) or 0 for a in employee_assignments
        )
        
        # Assume 40 hours per week as standard
        standard_hours = 40
        available_hours = max(0, standard_hours - total_assigned_hours)
        
        return available_hours 