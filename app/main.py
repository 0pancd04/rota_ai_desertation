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

class WeekRange(BaseModel):
    week_start: str
    week_end: str

class UnassignedWeekRequest(BaseModel):
    week_start: str
    week_end: str
    summarize: bool | None = False

class UnassignedSummarizeRequest(BaseModel):
    entity_type: str  # 'patient' | 'employee'
    entity_id: str
    week_start: str
    week_end: str
    regenerate: bool | None = False

class UnassignedCommonIssuesRequest(BaseModel):
    entity_type: str  # 'patient' | 'employee'
    week_start: str
    week_end: str
    top_n: int | None = 5

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

@app.get("/health/travel")
async def travel_health():
    """Detailed Google Maps travel health."""
    try:
        status = travel_service.check_connectivity()
        fast_env = os.getenv("FAST_SCHEDULER", "true").strip().lower() in ("1","true","yes","y")
        return {
            "available": status.get("available", False),
            "reason": status.get("reason"),
            "key_present": bool(travel_service.client),
            "mode": "api" if status.get("available", False) and not fast_env else "fast"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Travel health error: {e}")

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
            "patients_count": len(result.get("patients", [])),
            "upload_id": result.get("upload_id"),
            "sheets": result.get("sheets", [])
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
async def generate_weekly_rota(engine: str = Query("core", description="Scheduling engine: core or legacy"), fast: bool = Query(True, description="Use fast travel estimates instead of Google Maps API")):
    """Generate weekly rota with progress tracking"""
    try:
        # Create progress task
        task_id = progress_service.create_task(
            ProgressType.WEEKLY_ROTA,
            "Generating weekly rota schedule..."
        )
        
        # Start the task
        await progress_service.start_task(task_id)
        
        # Emit initial Google Maps mode and connectivity
        maps_status = travel_service.check_connectivity()
        mode = "fast" if fast or not maps_status.get("available", False) else "api"
        await progress_service.update_progress(task_id, 5, f"Travel mode: {mode.upper()} (key {'present' if maps_status.get('available') else 'missing/unavailable'})", 6)

        # Set fast mode for this request scope
        import os
        if fast:
            os.environ["FAST_SCHEDULER"] = "true"
        else:
            os.environ["FAST_SCHEDULER"] = "false"

        # Simulate progress updates for weekly rota generation
        steps = [
            ("Analyzing employee availability...", 15),
            ("Calculating patient requirements...", 30),
            ("Optimizing assignments...", 55),
            (f"Applying travel constraints ({mode})...", 80),
            ("Finalizing schedule...", 95)
        ]
        for step, progress in steps:
            await progress_service.update_progress(task_id, progress, step, len(steps))
            await asyncio.sleep(0.3)

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
            try:
                db_manager.clear_unassigned()
            except Exception:
                pass
            return {"success": True, "deleted": cursor.rowcount}

        elif request.mode == "selected":
            if not request.ids:
                raise HTTPException(status_code=400, detail="No assignment IDs provided")
            placeholders = ",".join(["?"] * len(request.ids))
            cursor.execute(f"DELETE FROM assignments WHERE id IN ({placeholders})", tuple(request.ids))
            db_manager.conn.commit()
            # When deleting by specific IDs, also clear unassigned to avoid stale diagnostics
            try:
                db_manager.clear_unassigned()
            except Exception:
                pass
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
            try:
                db_manager.clear_unassigned()
            except Exception:
                pass
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

@app.post("/assignments/week")
async def get_week_assignments(req: WeekRange):
    """Get all assignments across a week for grid view."""
    try:
        data = db_manager.get_assignments_for_week(req.week_start, req.week_end)
        return {"assignments": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weekly assignments: {str(e)}")

@app.post("/unassigned/week")
async def get_unassigned_week(req: UnassignedWeekRequest):
    """Get unassigned patients and employees for a given ISO week range, optionally with AI summaries."""
    try:
        patients = db_manager.get_unassigned_patients_for_week(req.week_start, req.week_end)
        employees = db_manager.get_unassigned_employees_for_week(req.week_start, req.week_end)
        result = {"patients": patients, "employees": employees}

        if req.summarize:
            # Build simple prompts for AI summaries per patient/employee over the week
            try:
                # Summarize patients
                for item in result["patients"]:
                    pid = item.get("patient_id")
                    date = item.get("date")
                    reasons = item.get("reasons", [])
                    context = item.get("context", {})
                    prompt = (
                        f"Summarize why patient {pid} on {date} had no assignment. "
                        f"Reasons: {reasons}. Context: {context}. "
                        "Provide a one-paragraph explanation and 2 bullet suggestions to resolve."
                    )
                    try:
                        resp = openai_service.client.chat.completions.create(
                            model=openai_service.model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.2
                        )
                        item["ai_summary"] = resp.choices[0].message.content
                    except Exception as e:
                        item["ai_summary"] = ""
                # Summarize employees
                for item in result["employees"]:
                    eid = item.get("employee_id")
                    date = item.get("date")
                    reasons = item.get("reasons", [])
                    context = item.get("context", {})
                    prompt = (
                        f"Summarize why employee {eid} on {date} received no assignment. "
                        f"Reasons: {reasons}. Context: {context}. "
                        "Provide a one-paragraph explanation and 2 bullet suggestions to resolve."
                    )
                    try:
                        resp = openai_service.client.chat.completions.create(
                            model=openai_service.model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.2
                        )
                        item["ai_summary"] = resp.choices[0].message.content
                    except Exception:
                        item["ai_summary"] = ""
            except Exception:
                pass

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching unassigned: {str(e)}")

@app.post("/unassigned/summarize")
async def summarize_unassigned(req: UnassignedSummarizeRequest):
    """Generate an AI summary for a specific patient/employee across the given week."""
    try:
        if req.entity_type not in ("patient", "employee"):
            raise HTTPException(status_code=400, detail="Invalid entity_type")
        # Check cache unless regenerate is requested
        if not req.regenerate:
            cached = db_manager.get_unassigned_summary(req.entity_type, req.entity_id, req.week_start, req.week_end)
            if cached:
                return {"summary": cached.get('summary') or "", "reasons": cached.get('reasons') or [], "dates": cached.get('dates') or [], "entity_type": req.entity_type, "entity_id": req.entity_id, "cached": True}

        # Background task with progress + notification
        task_id = progress_service.create_task(ProgressType.UNASSIGNED_SUMMARY, f"Generating summary for {req.entity_type} {req.entity_id}")
        await progress_service.start_task(task_id)
        try:
            await progress_service.update_progress(task_id, 10, "Collecting data...", 4)
            rows = db_manager.get_unassigned_for_entity_week(req.entity_type, req.entity_id, req.week_start, req.week_end)
            reasons = []
            contexts = []
            dates = []
            for r in rows:
                for v in r.get('reasons', []):
                    if v not in reasons:
                        reasons.append(v)
                contexts.append(r.get('context', {}))
                dates.append(r.get('date'))
            await progress_service.update_progress(task_id, 40, "Preparing AI prompt...", 4)
            prompt = (
                f"Summarize why {req.entity_type} {req.entity_id} had unassigned entries between {req.week_start} and {req.week_end}. "
                f"Reasons: {reasons}. Contexts: {contexts}. Dates: {dates}. "
                "Provide a concise paragraph and then 3 bullet suggestions to improve scheduling."
            )
            await progress_service.update_progress(task_id, 70, "Calling OpenAI...", 4)
            try:
                resp = openai_service.client.chat.completions.create(
                    model=openai_service.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                text = resp.choices[0].message.content or ""
            except Exception as e:
                text = ""
            # Save in cache
            try:
                db_manager.save_unassigned_summary(req.entity_type, req.entity_id, req.week_start, req.week_end, text, reasons, dates)
            except Exception:
                pass
            result = {"summary": text, "reasons": reasons, "dates": dates, "entity_type": req.entity_type, "entity_id": req.entity_id}
            await progress_service.complete_task(task_id, result=result)
            # Create notification
            try:
                notification_service.create_task_completion_notification('unassigned_summary', result)
            except Exception:
                pass
            return result
        except Exception as e:
            await progress_service.complete_task(task_id, error=str(e))
            raise HTTPException(status_code=500, detail=f"Error generating unassigned summary: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating unassigned summary: {str(e)}")

@app.post("/unassigned/common-issues")
async def summarize_common_unassigned_issues(req: UnassignedCommonIssuesRequest):
    """Summarize common unassigned issues across the requested entity type and week using OpenAI."""
    try:
        if req.entity_type not in ("patient", "employee"):
            raise HTTPException(status_code=400, detail="Invalid entity_type")
        # Collect weekly unassigned
        if req.entity_type == 'patient':
            rows = db_manager.get_unassigned_patients_for_week(req.week_start, req.week_end)
        else:
            rows = db_manager.get_unassigned_employees_for_week(req.week_start, req.week_end)
        # Build frequency maps
        reason_counts = {}
        issue_counts = {}
        rule_counts = {}
        example_attempts = []
        for r in rows:
            for v in r.get('reasons', []) or []:
                reason_counts[v] = reason_counts.get(v, 0) + 1
            ctx = r.get('context') or {}
            for it in (ctx.get('issues') or []):
                t = (it.get('type') or 'issue')
                issue_counts[t] = issue_counts.get(t, 0) + 1
            for att in (ctx.get('attempts') or [])[:2]:
                # collect a few example violations
                example_attempts.append({
                    "counterpart": att.get('employee_id') if req.entity_type == 'patient' else att.get('patient_id'),
                    "service_type": att.get('service_type'),
                    "time": f"{att.get('start_time')}→{att.get('end_time')}",
                    "violations": att.get('violations') or []
                })
                for vv in att.get('violations') or []:
                    rule_counts[vv] = rule_counts.get(vv, 0) + 1
        # Top N
        def top_items(d: dict, n: int):
            return sorted(([{"key": k, "count": v} for k, v in d.items()]), key=lambda x: (-x['count'], x['key']))[:n]
        top_n = req.top_n or 5
        top_reasons = top_items(reason_counts, top_n)
        top_issues = top_items(issue_counts, top_n)
        top_rules = top_items(rule_counts, top_n)
        # Prepare prompt for OpenAI
        prompt = (
            f"You are analyzing unassigned {req.entity_type}s for {req.week_start} to {req.week_end}.\n"
            f"Top Reasons: {top_reasons}.\nTop Issues: {top_issues}.\nTop Violations/Rules: {top_rules}.\n"
            f"Example Attempts (trimmed): {example_attempts[:10]}.\n"
            "Summarize the common causes concisely (one paragraph), then provide 5 specific, actionable recommendations."
        )
        try:
            resp = openai_service.client.chat.completions.create(
                model=openai_service.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            text = resp.choices[0].message.content or ""
        except Exception as e:
            text = ""
        return {
            "entity_type": req.entity_type,
            "week_start": req.week_start,
            "week_end": req.week_end,
            "top_reasons": top_reasons,
            "top_issues": top_issues,
            "top_rule_violations": top_rules,
            "ai_summary": text
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error summarizing common issues: {e}")

class UnassignedBulkSummarizeRequest(BaseModel):
    entity_type: str  # 'patient' | 'employee'
    ids: list[str] | None = None  # if None or empty, summarize for all entities present in unassigned for the week
    week_start: str
    week_end: str
    regenerate: bool | None = False

@app.post("/unassigned/summarize/bulk")
async def summarize_unassigned_bulk(req: UnassignedBulkSummarizeRequest):
    try:
        if req.entity_type not in ("patient", "employee"):
            raise HTTPException(status_code=400, detail="Invalid entity_type")

        # determine target ids
        targets: list[str] = []
        if req.ids:
            targets = list({x for x in req.ids if x})
        else:
            # collect from weekly unassigned
            if req.entity_type == 'patient':
                rows = db_manager.get_unassigned_patients_for_week(req.week_start, req.week_end)
                targets = sorted({r.get('patient_id') for r in rows if r.get('patient_id')})
            else:
                rows = db_manager.get_unassigned_employees_for_week(req.week_start, req.week_end)
                targets = sorted({r.get('employee_id') for r in rows if r.get('employee_id')})

        task_id = progress_service.create_task(ProgressType.UNASSIGNED_SUMMARY, f"Generating summaries for {req.entity_type}s ({len(targets)})")
        await progress_service.start_task(task_id)

        results = []
        total = max(1, len(targets))
        for idx, eid in enumerate(targets):
            pct = int(100 * (idx / total))
            await progress_service.update_progress(task_id, min(95, pct), f"Summarizing {req.entity_type} {eid} ({idx+1}/{total})", total)
            # Use cache unless regenerate
            if not req.regenerate:
                cached = db_manager.get_unassigned_summary(req.entity_type, eid, req.week_start, req.week_end)
                if cached:
                    results.append({
                        "entity_type": req.entity_type,
                        "entity_id": eid,
                        "summary": cached.get('summary') or "",
                        "reasons": cached.get('reasons') or [],
                        "dates": cached.get('dates') or [],
                        "cached": True
                    })
                    continue
            # compute fresh
            rows = db_manager.get_unassigned_for_entity_week(req.entity_type, eid, req.week_start, req.week_end)
            reasons, contexts, dates = [], [], []
            for r in rows:
                for v in r.get('reasons', []):
                    if v not in reasons:
                        reasons.append(v)
                contexts.append(r.get('context', {}))
                dates.append(r.get('date'))
            prompt = (
                f"Summarize why {req.entity_type} {eid} had unassigned entries between {req.week_start} and {req.week_end}. "
                f"Reasons: {reasons}. Contexts: {contexts}. Dates: {dates}. "
                "Provide a concise paragraph and then 3 bullet suggestions to improve scheduling."
            )
            try:
                resp = openai_service.client.chat.completions.create(
                    model=openai_service.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                text = resp.choices[0].message.content or ""
            except Exception:
                text = ""
            db_manager.save_unassigned_summary(req.entity_type, eid, req.week_start, req.week_end, text, reasons, dates)
            results.append({
                "entity_type": req.entity_type,
                "entity_id": eid,
                "summary": text,
                "reasons": reasons,
                "dates": dates
            })

        await progress_service.complete_task(task_id, result={"entity_type": req.entity_type, "count": len(results), "results": results})
        # One notification for bulk
        try:
            notification_service.create_task_completion_notification('unassigned_summary', {"entity_type": f"{req.entity_type}s", "entity_id": f"{len(results)} items"})
        except Exception:
            pass
        return {"results": results}
    except HTTPException:
        raise
    except Exception as e:
        try:
            await progress_service.complete_task(task_id, error=str(e))
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Bulk summarize failed: {e}")
    

@app.post("/employees/weekly-summary")
async def get_employees_weekly_summary(req: WeekRange):
    """Return employees with weekly used minutes and remaining capacity for the week."""
    try:
        employees = data_processor.get_employees()  # list of dicts
        summary = []
        for emp in employees:
            # Dict keys are Pydantic field names: 'EmployeeID', 'Name', 'TransportMode', etc.
            emp_id = emp.get('EmployeeID')
            used = db_manager.sum_employee_minutes_for_week(emp_id, req.week_start, req.week_end)
            role_level = emp.get('RoleLevel')
            cap = emp.get('weekly_capacity_minutes')
            if isinstance(cap, int) and cap > 0:
                capacity = cap
            else:
                rl = (role_level or '').strip().lower()
                capacity = 1200 if rl == 'junior' else 2160

            # Enums may be present; coerce to string values when possible
            def enum_val(v):
                try:
                    return v.value
                except Exception:
                    return v

            summary.append({
                "employee_id": emp_id,
                "name": emp.get('Name'),
                "gender": enum_val(emp.get('Gender')),
                "qualification": enum_val(emp.get('Qualification')),
                "role_level": role_level,
                "transport_mode": enum_val(emp.get('TransportMode')),
                "languages": emp.get('LanguageSpoken', ''),
                "address": emp.get('Address'),
                "postcode": emp.get('PostCode'),
                "earliest_start": emp.get('EarliestStart'),
                "latest_end": emp.get('LatestEnd'),
                "weekly_capacity_minutes": capacity,
                "used_minutes": used,
                "remaining_minutes": max(0, capacity - used),
            })
        return {"employees": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching employees weekly summary: {str(e)}")

@app.get("/patients/details/{patient_id}")
async def get_patient_details(patient_id: str):
    try:
        pat = data_processor.get_patient_by_id(patient_id)
        if not pat:
            raise HTTPException(status_code=404, detail="Patient not found")
        return pat.dict(by_alias=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching patient: {str(e)}")

@app.get("/employees/details/{employee_id}")
async def get_employee_details(employee_id: str):
    try:
        emp = data_processor.get_employee_by_id(employee_id)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        return emp.dict(by_alias=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching employee: {str(e)}")

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

@app.get("/uploads/raw")
async def list_raw_uploads():
    """List raw uploads stored for history (filename, uploaded_at, id)."""
    try:
        rows = db_manager.get_raw_uploads()
        return {"raw_uploads": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing raw uploads: {str(e)}")

@app.get("/uploads/raw/{upload_id}")
async def get_raw_upload(upload_id: int):
    """Get a raw upload record (sheets listing only)."""
    try:
        data = db_manager.get_raw_upload(upload_id)
        if not data:
            raise HTTPException(status_code=404, detail="Raw upload not found")
        # Don't return full sheets by default to keep payload small
        return {"id": data["id"], "filename": data["filename"], "uploaded_at": data["uploaded_at"], "sheet_names": list(data.get("sheets", {}).keys())}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching raw upload: {str(e)}")

@app.get("/uploads/raw/{upload_id}/sheet/{sheet}")
async def get_raw_upload_sheet(upload_id: int, sheet: str):
    """Return columns and rows for a specific sheet of a raw upload."""
    try:
        data = db_manager.get_raw_upload_sheet(upload_id, sheet)
        if data is None:
            raise HTTPException(status_code=404, detail="Raw upload or sheet not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching raw upload sheet: {str(e)}")

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