import uuid
from datetime import datetime
from typing import Dict, List, Optional
from ..database import DatabaseManager

class NotificationService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def create_notification(self, notification_type: str, title: str, message: str, action_type: str = None, action_data: Dict = None) -> str:
        """Create a new notification and return the notification ID"""
        notification_id = str(uuid.uuid4())
        
        success = self.db_manager.create_notification(
            notification_id=notification_id,
            notification_type=notification_type,
            title=title,
            message=message,
            action_type=action_type,
            action_data=action_data
        )
        
        if success:
            return notification_id
        else:
            raise Exception("Failed to create notification")

    def get_notifications(self, include_deleted: bool = False, limit: int = 50) -> List[Dict]:
        """Get notifications with optional filtering"""
        return self.db_manager.get_notifications(include_deleted=include_deleted, limit=limit)

    def get_unread_notifications_count(self) -> int:
        """Get count of unread notifications"""
        return self.db_manager.get_unread_notifications_count()

    def mark_notification_read(self, notification_id: str) -> bool:
        """Mark a notification as read"""
        return self.db_manager.mark_notification_read(notification_id)

    def mark_notification_deleted(self, notification_id: str) -> bool:
        """Mark a notification as deleted"""
        return self.db_manager.mark_notification_deleted(notification_id)

    def mark_all_notifications_read(self) -> bool:
        """Mark all notifications as read"""
        return self.db_manager.mark_all_notifications_read()

    def delete_all_notifications(self) -> bool:
        """Delete all notifications"""
        return self.db_manager.delete_all_notifications()

    def create_task_completion_notification(self, task_type: str, result: Dict = None) -> str:
        """Create a notification for task completion"""
        if task_type == 'weekly_rota':
            title = 'Weekly Rota Generated'
            message = f"Successfully generated {len(result.get('assignments', []))} assignments for the week"
            action_type = 'navigate'
            action_data = {'route': '/assignments'}
        elif task_type == 'create_assignment':
            assignment = result.get('assignment', {})
            title = 'Assignment Created'
            message = f"{assignment.get('employee_name', 'Employee')} assigned to {assignment.get('patient_name', 'Patient')}"
            action_type = 'navigate'
            action_data = {'route': '/assignments'}
        else:
            title = 'Task Completed'
            message = 'Task completed successfully'
            action_type = None
            action_data = None

        return self.create_notification(
            notification_type='success',
            title=title,
            message=message,
            action_type=action_type,
            action_data=action_data
        )

    def create_task_failure_notification(self, task_type: str, error: str) -> str:
        """Create a notification for task failure"""
        if task_type == 'weekly_rota':
            title = 'Weekly Rota Generation Failed'
        elif task_type == 'create_assignment':
            title = 'Assignment Creation Failed'
        else:
            title = 'Task Failed'

        return self.create_notification(
            notification_type='error',
            title=title,
            message=error or 'An error occurred during processing',
            action_type=None,
            action_data=None
        )

    def create_system_notification(self, title: str, message: str, notification_type: str = 'info') -> str:
        """Create a system notification"""
        return self.create_notification(
            notification_type=notification_type,
            title=title,
            message=message,
            action_type=None,
            action_data=None
        ) 