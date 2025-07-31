import asyncio
import json
import uuid
from typing import Dict, Optional, Callable
from datetime import datetime
from fastapi import WebSocket
from enum import Enum

class ProgressStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class ProgressType(Enum):
    WEEKLY_ROTA = "weekly_rota"
    CREATE_ASSIGNMENT = "create_assignment"

class ProgressService:
    def __init__(self, notification_service=None):
        self.active_connections: Dict[str, WebSocket] = {}
        self.progress_tasks: Dict[str, Dict] = {}
        self.task_callbacks: Dict[str, Callable] = {}
        self.notification_service = notification_service
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        """Disconnect a WebSocket client"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        print(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast_progress(self, task_id: str, progress_data: Dict):
        """Broadcast progress to all connected clients"""
        message = {
            "type": "progress_update",
            "task_id": task_id,
            "data": progress_data,
            "timestamp": datetime.now().isoformat()
        }
        
        disconnected_clients = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                print(f"Failed to send message to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    def create_task(self, task_type: ProgressType, description: str) -> str:
        """Create a new progress task"""
        task_id = str(uuid.uuid4())
        self.progress_tasks[task_id] = {
            "id": task_id,
            "type": task_type.value,
            "status": ProgressStatus.PENDING.value,
            "description": description,
            "progress": 0,
            "current_step": "",
            "total_steps": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "result": None,
            "error": None
        }
        return task_id
    
    async def update_progress(self, task_id: str, progress: int, current_step: str = "", total_steps: int = None):
        """Update progress for a specific task"""
        if task_id not in self.progress_tasks:
            return
        
        self.progress_tasks[task_id]["progress"] = progress
        self.progress_tasks[task_id]["current_step"] = current_step
        if total_steps:
            self.progress_tasks[task_id]["total_steps"] = total_steps
        self.progress_tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        await self.broadcast_progress(task_id, self.progress_tasks[task_id])
    
    async def complete_task(self, task_id: str, result: Dict = None, error: str = None):
        """Mark a task as completed"""
        if task_id not in self.progress_tasks:
            return
        
        self.progress_tasks[task_id]["status"] = ProgressStatus.COMPLETED.value if not error else ProgressStatus.FAILED.value
        self.progress_tasks[task_id]["progress"] = 100 if not error else 0
        self.progress_tasks[task_id]["updated_at"] = datetime.now().isoformat()
        self.progress_tasks[task_id]["result"] = result
        self.progress_tasks[task_id]["error"] = error
        
        # Create notification in database if notification service is available
        if self.notification_service:
            try:
                task_data = self.progress_tasks[task_id]
                if error:
                    self.notification_service.create_task_failure_notification(
                        task_data["type"], error
                    )
                else:
                    self.notification_service.create_task_completion_notification(
                        task_data["type"], result
                    )
            except Exception as e:
                print(f"Failed to create notification: {e}")
        
        await self.broadcast_progress(task_id, self.progress_tasks[task_id])
    
    async def start_task(self, task_id: str):
        """Start a task"""
        if task_id not in self.progress_tasks:
            return
        
        self.progress_tasks[task_id]["status"] = ProgressStatus.IN_PROGRESS.value
        self.progress_tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        await self.broadcast_progress(task_id, self.progress_tasks[task_id])
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task information"""
        return self.progress_tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, Dict]:
        """Get all tasks"""
        return self.progress_tasks
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        tasks_to_remove = []
        
        for task_id, task in self.progress_tasks.items():
            task_time = datetime.fromisoformat(task["created_at"]).timestamp()
            if task_time < cutoff_time and task["status"] in [ProgressStatus.COMPLETED.value, ProgressStatus.FAILED.value]:
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.progress_tasks[task_id]
        
        if tasks_to_remove:
            print(f"Cleaned up {len(tasks_to_remove)} old tasks")

# Global instance
progress_service = ProgressService() 