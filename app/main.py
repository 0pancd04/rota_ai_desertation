from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from pathlib import Path

from .services.data_processor import DataProcessor
from .services.openai_service import OpenAIService
from .services.rota_service import RotaService
from .models.schemas import RotaRequest, RotaResponse, EmployeeAssignment

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
data_processor = DataProcessor()
openai_service = OpenAIService()
rota_service = RotaService(data_processor, openai_service)

# Ensure input_files directory exists
INPUT_FILES_DIR = Path("input_files")
INPUT_FILES_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    return {"message": "AI Rota System for Healthcare is running"}

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
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process the data
        result = await data_processor.process_excel_file(str(file_path))
        
        return {
            "message": "File uploaded and processed successfully",
            "filename": file.filename,
            "employees_count": len(result.get("employees", [])),
            "patients_count": len(result.get("patients", []))
        }
    except Exception as e:
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 