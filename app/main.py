from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import asyncio
import uuid
import io
from datetime import datetime
from pathlib import Path

from .services.data_processor import DataProcessor
from .services.openai_service import OpenAIService
from .services.rota_service import RotaService
from .services.travel_service import TravelService
from .services.progress_service import progress_service, ProgressType
from .services.notification_service import NotificationService
from .services.filter_service import FilterService
from .services.excel_export_service import ExcelExportService
from .services.stats_service import StatsService
from .models.schemas import RotaRequest, RotaResponse, EmployeeAssignment, AssignmentUpdateRequest
from .models.filter_schemas import FilterConfig, FilterGroup, FilterCondition
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
filter_service = FilterService(db_manager)
excel_export_service = ExcelExportService()
stats_service = StatsService(db_manager, openai_service)

# Startup connectivity checks
try:
    maps_status = travel_service.check_connectivity()
    ai_status = openai_service.check_connectivity()
    import logging
    logging.getLogger(__name__).info(f"Startup checks - Google Maps: {maps_status}, OpenAI: {ai_status}")
    db_manager.log_operation("startup_health", "Third-party connectivity checks", {
        "google_maps": maps_status,
        "openai": ai_status
    })
except Exception:
    pass

# Update progress service with notification service
progress_service.notification_service = notification_service

# Ensure input_files directory exists
INPUT_FILES_DIR = Path("input_files")
INPUT_FILES_DIR.mkdir(exist_ok=True)

class BulkDeleteRequest(BaseModel):
    mode: str | None = None  # 'all' | 'filtered' | 'selected'
    ids: list[int] | None = None
    filters: list[FilterGroup] | None = None

class EmployeeWeekRequest(BaseModel):
    employee_id: str
    week_start: str  # ISO date, Monday
    week_end: str    # ISO date, Sunday

class ReanalyzeRequest(BaseModel):
    assignment_ids: List[int]
    allow_time_change: bool = False

@app.get("/")
async def root():
    return {"message": "AI Rota System for Healthcare is running - Development Mode Active!"}

@app.get("/health")
async def health_check():
    maps_status = travel_service.check_connectivity()
    ai_status = openai_service.check_connectivity()
    overall = maps_status.get("available", False) and ai_status.get("available", False)
    return {
        "status": "healthy" if overall else "degraded",
        "service": "ai-rota-system",
        "google_maps": maps_status,
        "openai": ai_status
    }

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

# Filter endpoints
@app.get("/filters/suggestions/{page}")
async def get_filter_suggestions(page: str):
    """Get filter suggestions for a specific page"""
    try:
        if page == "assignments":
            suggestions = filter_service.get_assignment_filter_suggestions()
        elif page == "employees":
            suggestions = filter_service.get_employee_filter_suggestions()
        elif page == "patients":
            suggestions = filter_service.get_patient_filter_suggestions()
        else:
            raise HTTPException(status_code=400, detail="Invalid page")
        
        return suggestions.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching filter suggestions: {str(e)}")

@app.get("/filters/config/{page}")
async def get_filter_config(page: str):
    """Get saved filter configuration for a page"""
    try:
        config = filter_service.get_filter_config(page)
        if config:
            return config.dict()
        else:
            return {"page": page, "filters": [], "sort_by": None, "sort_order": "asc", "page_size": 50, "page_number": 1}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching filter config: {str(e)}")

@app.post("/filters/config/{page}")
async def save_filter_config(page: str, config: FilterConfig):
    """Save filter configuration for a page"""
    try:
        config_id = filter_service.update_filter_config(
            page=page,
            filters=config.filters,
            sort_by=config.sort_by,
            sort_order=config.sort_order,
            page_size=config.page_size,
            page_number=config.page_number
        )
        return {"config_id": config_id, "message": "Filter configuration saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving filter config: {str(e)}")

@app.post("/filters/apply/{page}")
async def apply_filters(page: str, filters: List[FilterGroup]):
    """Apply filters to data for a specific page"""
    try:
        if page == "assignments":
            filtered_data = filter_service.apply_filters_to_assignments(filters)
        elif page == "employees":
            filtered_data = filter_service.apply_filters_to_employees(filters)
        elif page == "patients":
            filtered_data = filter_service.apply_filters_to_patients(filters)
        else:
            raise HTTPException(status_code=400, detail="Invalid page")
        
        return {"data": filtered_data, "count": len(filtered_data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying filters: {str(e)}")

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
async def generate_weekly_rota(engine: str = Query("core", description="Scheduling engine: core or legacy")):
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
        assignments = await rota_service.generate_weekly_schedule(engine=engine)
        
        # Complete the task
        await progress_service.complete_task(task_id, {
            "success": True,
            "assignments": assignments
        })
        
        return {"success": True, "assignments": assignments}
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

@app.put("/assignments/{assignment_id}")
async def update_assignment(assignment_id: int, request: AssignmentUpdateRequest):
    """Update an existing assignment"""
    try:
        # Convert request to dict, filtering out None values
        updates = {k: v for k, v in request.dict().items() if v is not None}
        
        if not updates:
            raise HTTPException(status_code=400, detail="No update fields provided")
        
        success = rota_service.update_assignment(assignment_id, updates)
        
        if success:
            return {
                "success": True, 
                "message": f"Assignment {assignment_id} updated successfully"
            }
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"Assignment {assignment_id} not found or could not be updated"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error updating assignment {assignment_id}: {str(e)}"
        )

@app.delete("/assignments/{assignment_id}")
async def delete_assignment(assignment_id: int):
    """Delete an assignment"""
    try:
        success = rota_service.delete_assignment(assignment_id)
        
        if success:
            return {
                "success": True, 
                "message": f"Assignment {assignment_id} deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"Assignment {assignment_id} not found or could not be deleted"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error deleting assignment {assignment_id}: {str(e)}"
        )

@app.post("/assignments/bulk-delete")
async def bulk_delete_assignments(request: BulkDeleteRequest):
    """Bulk delete assignments by mode: all, filtered (with filters), or selected IDs."""
    try:
        cursor = db_manager.conn.cursor()

        if request.mode == "all":
            cursor.execute("DELETE FROM assignments")
            db_manager.conn.commit()
            return {"success": True, "deleted": cursor.rowcount}

        elif request.mode == "selected":
            if not request.ids:
                raise HTTPException(status_code=400, detail="No assignment IDs provided")
            placeholders = ",".join(["?"] * len(request.ids))
            cursor.execute(f"DELETE FROM assignments WHERE id IN ({placeholders})", tuple(request.ids))
            db_manager.conn.commit()
            return {"success": True, "deleted": cursor.rowcount}

        elif request.mode == "filtered":
            filters = request.filters or []
            matches = filter_service.apply_filters_to_assignments(filters)
            ids = [a.get("id") for a in matches if a.get("id") is not None]
            if not ids:
                return {"success": True, "deleted": 0}
            placeholders = ",".join(["?"] * len(ids))
            cursor.execute(f"DELETE FROM assignments WHERE id IN ({placeholders})", tuple(ids))
            db_manager.conn.commit()
            return {"success": True, "deleted": cursor.rowcount}

        else:
            raise HTTPException(status_code=400, detail="Invalid mode. Use 'all', 'filtered', or 'selected'.")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing bulk delete: {str(e)}")

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

@app.post("/employee/assignments/week")
async def get_employee_week_assignments(req: EmployeeWeekRequest):
    """Get a specific employee's assignments for a week, ordered by start_time."""
    try:
        data = db_manager.get_employee_assignments_for_week(req.employee_id, req.week_start, req.week_end)
        return {"assignments": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching employee weekly assignments: {str(e)}")

@app.post("/assignments/reanalyze")
async def reanalyze_assignments(req: ReanalyzeRequest):
    try:
        updated = rota_service.reanalyze_assignments(req.assignment_ids, allow_time_change=req.allow_time_change)
        return {"success": True, "updated": updated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reanalyzing assignments: {str(e)}")

@app.get("/export/assignments-excel")
async def export_assignments_excel():
    """Export assignments data to Excel with three sheets: assignments, patients, and employees"""
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        # Get all data
        assignments = db_manager.get_assignments()
        patients = db_manager.get_patients()
        employees = db_manager.get_employees()
        
        # Debug logging
        logger.info(f"Export data counts - Assignments: {len(assignments)}, Patients: {len(patients)}, Employees: {len(employees)}")
        logger.info(f"Assignments sample: {assignments[:2] if assignments else 'None'}")
        logger.info(f"Patients sample: {patients[:2] if patients else 'None'}")
        logger.info(f"Employees sample: {employees[:2] if employees else 'None'}")
        
        # Generate Excel file
        excel_data = excel_export_service.export_assignments_data(assignments, patients, employees)
        
        # Debug logging for Excel data
        logger.info(f"Excel data generated, size: {len(excel_data)} bytes")
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"assignments_export_{timestamp}.xlsx"
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error exporting Excel data: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error exporting Excel data: {str(e)}")

@app.get("/stats")
async def get_stats(force: bool = False, days: str = None, start_date: str = None, end_date: str = None):
    try:
        day_list = None
        if days:
            # days as comma-separated integers 0..6 where 0=Mon
            try:
                day_list = [int(x) for x in days.split(',') if x.strip() != '']
            except Exception:
                day_list = None
        data = await stats_service.get_or_generate_stats(force=force, days=day_list, start_date=start_date, end_date=end_date)
        # Back-compat: map stored ai_ideas to ai_suggestions in response
        if data and 'ai_ideas' in data and 'ai_suggestions' not in data:
            data['ai_suggestions'] = data.pop('ai_ideas')
        return {"stats": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating stats: {str(e)}")

@app.get("/test-excel")
async def test_excel_generation():
    """Test endpoint to verify Excel generation works"""
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        # Create test data
        test_assignments = [
            {
                "employee_id": "EMP001",
                "employee_name": "John Doe",
                "patient_id": "PAT001",
                "patient_name": "Jane Smith",
                "service_type": "medicine",
                "assigned_time": "2024-01-15T09:00:00",
                "start_time": "2024-01-15T09:00:00",
                "end_time": "2024-01-15T10:00:00",
                "estimated_duration": 60,
                "travel_time": 15,
                "priority_score": 8.5,
                "assignment_reason": "Test assignment"
            }
        ]
        
        test_patients = [
            {
                "PatientID": "PAT001",
                "PatientName": "Jane Smith",
                "Address": "123 Test St",
                "PostCode": "TE1 1ST",
                "Gender": "Female",
                "Ethnicity": "White",
                "Religion": "None",
                "RequiredSupport": "medicine",
                "RequiredHoursOfSupport": 2,
                "AdditionalRequirements": "None",
                "Illness": "Diabetes",
                "ContactNumber": "1234567890",
                "RequiresMedication": "Y",
                "EmergencyContact": "John Smith",
                "EmergencyRelation": "Spouse",
                "LanguagePreference": "English",
                "Notes": "Test patient"
            }
        ]
        
        test_employees = [
            {
                "EmployeeID": "EMP001",
                "Name": "John Doe",
                "Address": "456 Work St",
                "PostCode": "WO1 1RK",
                "Gender": "Male",
                "Ethnicity": "White",
                "Religion": "None",
                "TransportMode": "Car",
                "Qualification": "Nurse",
                "LanguageSpoken": "English",
                "CertificateExpiryDate": "2025-12-31",
                "EarliestStart": "08:00",
                "LatestEnd": "18:00",
                "Shifts": "Day",
                "ContactNumber": "0987654321",
                "Notes": "Test employee"
            }
        ]
        
        logger.info("Testing Excel generation with test data...")
        
        # Generate Excel file
        excel_data = excel_export_service.export_assignments_data(test_assignments, test_patients, test_employees)
        
        logger.info(f"Test Excel generated successfully, size: {len(excel_data)} bytes")
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=test_export.xlsx"}
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Test Excel generation failed: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test Excel generation failed: {str(e)}")

@app.get("/export/debug-data")
async def debug_export_data():
    """Debug endpoint to check what data is available for export"""
    try:
        # Get all data
        assignments = db_manager.get_assignments()
        patients = db_manager.get_patients()
        employees = db_manager.get_employees()
        
        return {
            "data_counts": {
                "assignments": len(assignments),
                "patients": len(patients),
                "employees": len(employees)
            },
            "assignments_sample": assignments[:2] if assignments else [],
            "patients_sample": patients[:2] if patients else [],
            "employees_sample": employees[:2] if employees else [],
            "assignments_keys": list(assignments[0].keys()) if assignments else [],
            "patients_keys": list(patients[0].keys()) if patients else [],
            "employees_keys": list(employees[0].keys()) if employees else []
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Debug data fetch failed: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Debug data fetch failed: {str(e)}")

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

@app.post("/database/clear-employees")
async def clear_employees():
    try:
        ok = db_manager.clear_employees()
        if ok:
            data_processor._load_from_database()
            return {"message": "All employees cleared successfully"}
        raise Exception("DB clear employees failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing employees: {str(e)}")

@app.post("/database/clear-patients")
async def clear_patients():
    try:
        ok = db_manager.clear_patients()
        if ok:
            data_processor._load_from_database()
            return {"message": "All patients cleared successfully"}
        raise Exception("DB clear patients failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing patients: {str(e)}")

@app.post("/database/clear-people")
async def clear_employees_and_patients():
    try:
        ok = db_manager.clear_employees_and_patients()
        if ok:
            data_processor._load_from_database()
            return {"message": "All employees and patients cleared successfully"}
        raise Exception("DB clear employees and patients failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing employees and patients: {str(e)}")

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