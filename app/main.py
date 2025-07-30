from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from pathlib import Path

from .services.data_processor import DataProcessor
from .services.openai_service import OpenAIService
from .services.rota_service import RotaService
from .services.travel_service import TravelService
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

# Ensure input_files directory exists
INPUT_FILES_DIR = Path("/app/input_files")
INPUT_FILES_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    return {"message": "AI Rota System for Healthcare is running - Development Mode Active!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-rota-system"}

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
        
        # Process the assignment request
        assignment = await rota_service.process_assignment_request(request.prompt)
        
        return RotaResponse(
            success=True,
            message="Employee assigned successfully",
            assignment=assignment
        )
    
    except Exception as e:
        return RotaResponse(
            success=False,
            message=f"Error processing assignment: {str(e)}",
            assignment=None
        )

@app.post("/generate-weekly-rota")
async def generate_weekly_rota():
    try:
        assignments = await rota_service.generate_weekly_schedule()
        return {"success": True, "assignments": [a.dict() for a in assignments]}
    except Exception as e:
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