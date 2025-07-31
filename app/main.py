from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import asyncio
import uuid
from pathlib import Path

from .services.data_processor import DataProcessor
from .services.openai_service import OpenAIService
from .services.rota_service import RotaService
from .services.travel_service import TravelService
from .services.progress_service import progress_service, ProgressType
from .services.notification_service import NotificationService
from .models.schemas import RotaRequest, RotaResponse, EmployeeAssignment
from .database import DatabaseManager

app = FastAPI(
    title="AI Rota System for Healthcare",
    description="An AI-powered system for assigning healthcare employees to patients based on various rules and constraints",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db_manager = DatabaseManager()
data_processor = DataProcessor(db_manager)
openai_service = OpenAIService()
travel_service = TravelService()
rota_service = RotaService(data_processor, openai_service, db_manager, travel_service)
notification_service = NotificationService(db_manager)

# Update progress service with notification service
progress_service.notification_service = notification_service

# Ensure input_files directory exists
INPUT_FILES_DIR = Path("/app/input_files")
INPUT_FILES_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    return {"message": "AI Rota System for Healthcare is running - Development Mode Active!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-rota-system"}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time progress updates"""
    await progress_service.connect(websocket, client_id)
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # For now, we don't need to handle incoming messages
            # but we could add features like task cancellation here
    except WebSocketDisconnect:
        progress_service.disconnect(client_id)

@app.get("/progress/{task_id}")
async def get_progress(task_id: str):
    """Get progress for a specific task"""
    task = progress_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.get("/progress")
async def get_all_progress():
    """Get all progress tasks"""
    return progress_service.get_all_tasks()

# Notification endpoints
@app.get("/notifications")
async def get_notifications(include_deleted: bool = False, limit: int = 50):
    """Get notifications with optional filtering"""
    try:
        notifications = notification_service.get_notifications(include_deleted=include_deleted, limit=limit)
        return {"notifications": notifications}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching notifications: {str(e)}")

@app.get("/notifications/unread-count")
async def get_unread_notifications_count():
    """Get count of unread notifications"""
    try:
        count = notification_service.get_unread_notifications_count()
        return {"unread_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching unread count: {str(e)}")

@app.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    """Mark a notification as read"""
    try:
        success = notification_service.mark_notification_read(notification_id)
        if success:
            return {"message": "Notification marked as read"}
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking notification as read: {str(e)}")

@app.post("/notifications/{notification_id}/delete")
async def mark_notification_deleted(notification_id: str):
    """Mark a notification as deleted"""
    try:
        success = notification_service.mark_notification_deleted(notification_id)
        if success:
            return {"message": "Notification marked as deleted"}
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking notification as deleted: {str(e)}")

@app.post("/notifications/read-all")
async def mark_all_notifications_read():
    """Mark all notifications as read"""
    try:
        success = notification_service.mark_all_notifications_read()
        if success:
            return {"message": "All notifications marked as read"}
        else:
            raise HTTPException(status_code=500, detail="Failed to mark notifications as read")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking notifications as read: {str(e)}")

@app.delete("/notifications")
async def delete_all_notifications():
    """Delete all notifications"""
    try:
        success = notification_service.delete_all_notifications()
        if success:
            return {"message": "All notifications deleted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete notifications")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting notifications: {str(e)}")

@app.post("/upload-data")
async def upload_data(file: UploadFile = File(...)):
    """Upload employee and patient data file"""
    try:
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")
        
        file_path = INPUT_FILES_DIR / file.filename
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Uploading file: {file.filename}")
        logger.info(f"File path: {file_path}")
        logger.info(f"File path exists: {file_path.exists()}")
        logger.info(f"INPUT_FILES_DIR: {INPUT_FILES_DIR}")
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"File saved successfully")
        logger.info(f"File exists after save: {file_path.exists()}")
        
        # Process the data
        result = await data_processor.process_excel_file(str(file_path))
        
        return {
            "message": "File uploaded and processed successfully",
            "filename": file.filename,
            "employees_count": len(result.get("employees", [])),
            "patients_count": len(result.get("patients", []))
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in upload_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/assign-employee", response_model=RotaResponse)
async def assign_employee(request: RotaRequest):
    """
    Assign an employee to a patient based on the requirements.
    Example: "The patient P001 is required Exercise today can you assign available employee."
    """
    try:
        # Check if we have data loaded
        if not data_processor.has_data():
            raise HTTPException(
                status_code=400, 
                detail="No data loaded. Please upload employee and patient data first."
            )
        
        # Create progress task
        task_id = progress_service.create_task(
            ProgressType.CREATE_ASSIGNMENT,
            f"Creating assignment for: {request.prompt[:50]}..."
        )
        
        # Start the task
        await progress_service.start_task(task_id)
        
        # Update progress
        await progress_service.update_progress(task_id, 20, "Analyzing request...", 5)
        
        # Process the assignment request
        await progress_service.update_progress(task_id, 40, "Processing assignment...", 5)
        assignment = await rota_service.process_assignment_request(request.prompt)
        
        await progress_service.update_progress(task_id, 80, "Finalizing assignment...", 5)
        
        # Complete the task
        await progress_service.complete_task(task_id, {
            "success": True,
            "message": "Employee assigned successfully",
            "assignment": assignment
        })
        
        return RotaResponse(
            success=True,
            message="Employee assigned successfully",
            assignment=assignment
        )
    
    except Exception as e:
        # Mark task as failed
        if 'task_id' in locals():
            await progress_service.complete_task(task_id, error=str(e))
        
        return RotaResponse(
            success=False,
            message=f"Error processing assignment: {str(e)}",
            assignment=None
        )

@app.post("/generate-weekly-rota")
async def generate_weekly_rota():
    """Generate weekly rota with progress tracking"""
    try:
        # Create progress task
        task_id = progress_service.create_task(
            ProgressType.WEEKLY_ROTA,
            "Generating weekly rota schedule..."
        )
        
        # Start the task
        await progress_service.start_task(task_id)
        
        # Simulate progress updates for weekly rota generation
        steps = [
            ("Analyzing employee availability...", 10),
            ("Calculating patient requirements...", 25),
            ("Optimizing assignments...", 50),
            ("Applying travel constraints...", 75),
            ("Finalizing schedule...", 90)
        ]
        
        for step, progress in steps:
            await progress_service.update_progress(task_id, progress, step, len(steps))
            await asyncio.sleep(1)  # Simulate processing time
        
        # Generate the actual rota
        assignments = await rota_service.generate_weekly_schedule()
        
        # Complete the task
        await progress_service.complete_task(task_id, {
            "success": True,
            "assignments": [a.dict() for a in assignments]
        })
        
        return {"success": True, "assignments": [a.dict() for a in assignments]}
    except Exception as e:
        # Mark task as failed
        if 'task_id' in locals():
            await progress_service.complete_task(task_id, error=str(e))
        
        raise HTTPException(status_code=500, detail=f"Error generating weekly rota: {str(e)}")

@app.get("/employees")
async def get_employees():
    """Get all employees data"""
    try:
        employees = data_processor.get_employees()
        return {"employees": employees}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching employees: {str(e)}")

@app.get("/patients")
async def get_patients():
    """Get all patients data"""
    try:
        patients = data_processor.get_patients()
        return {"patients": patients}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching patients: {str(e)}")

@app.get("/assignments")
async def get_assignments():
    """Get all current assignments"""
    try:
        assignments = rota_service.get_current_assignments()
        return {"assignments": assignments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching assignments: {str(e)}")

@app.get("/data-status")
async def get_data_status():
    """Get the current status of data in the system"""
    try:
        return {
            "has_data": data_processor.has_data(),
            "employees_count": len(data_processor.employees),
            "patients_count": len(data_processor.patients),
            "assignments_count": len(rota_service.get_current_assignments()),
            "database_has_data": db_manager.has_data()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data status: {str(e)}")

@app.get("/database/employees")
async def get_database_employees():
    """Get all employees from database"""
    try:
        employees = db_manager.get_employees()
        return {"employees": employees}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching employees from database: {str(e)}")

@app.get("/database/patients")
async def get_database_patients():
    """Get all patients from database"""
    try:
        patients = db_manager.get_patients()
        return {"patients": patients}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching patients from database: {str(e)}")

@app.get("/database/assignments")
async def get_database_assignments():
    """Get all assignments from database"""
    try:
        assignments = db_manager.get_assignments()
        return {"assignments": assignments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching assignments from database: {str(e)}")

@app.get("/database/logs")
async def get_database_logs():
    """Get all operation logs from database"""
    try:
        logs = db_manager.get_logs()
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching logs from database: {str(e)}")

@app.get("/database/uploads")
async def get_database_uploads():
    """Get all data upload history from database"""
    try:
        uploads = db_manager.get_data_uploads()
        return {"uploads": uploads}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching uploads from database: {str(e)}")

@app.post("/database/clear")
async def clear_database():
    """Clear all data from database (for testing/reset)"""
    try:
        db_manager.clear_all_data()
        # Reset in-memory data
        data_processor.employees = []
        data_processor.patients = []
        data_processor.data_loaded = False
        rota_service.clear_assignments()
        return {"message": "All data cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing database: {str(e)}")

@app.post("/database/reload")
async def reload_from_database():
    """Reload data from database into memory"""
    try:
        data_processor._load_from_database()
        return {
            "message": "Data reloaded from database",
            "employees_count": len(data_processor.employees),
            "patients_count": len(data_processor.patients)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reloading from database: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 