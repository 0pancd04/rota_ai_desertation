from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, time
from enum import Enum

class EmployeeType(str, Enum):
    NURSE = "nurse"
    CARE_WORKER = "care_worker"

class ServiceType(str, Enum):
    MEDICINE = "medicine"
    EXERCISE = "exercise"
    COMPANIONSHIP = "companionship"
    PERSONAL_CARE = "personal_care"

class VehicleType(str, Enum):
    CAR = "car"
    BIKE = "bike"
    NONE = "none"

class Employee(BaseModel):
    employee_id: str = Field(..., description="Unique employee identifier")
    name: str = Field(..., description="Employee name")
    address: str = Field(..., description="Employee address")
    vehicle_available: Optional[str] = Field(None, description="Vehicle availability")
    qualification: Optional[str] = Field(None, description="Employee qualification")
    language_spoken: Optional[str] = Field(None, description="Languages spoken by employee")
    certificate_expiry_date: Optional[datetime] = Field(None, description="Certificate expiry date")
    earliest_start: Optional[str] = Field(None, description="Earliest start time")
    latest_end: Optional[str] = Field(None, description="Latest end time")
    availability: Optional[str] = Field(None, description="Availability schedule")
    contact_number: Optional[int] = Field(None, description="Contact number")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    # Derived fields for compatibility
    employee_type: EmployeeType = Field(default=EmployeeType.CARE_WORKER, description="Type of employee")
    languages: List[str] = Field(default=[], description="Parsed languages list")
    availability_start: time = Field(default=time(9, 0), description="Start time of availability")
    availability_end: time = Field(default=time(17, 0), description="End time of availability")
    vehicle: VehicleType = Field(default=VehicleType.NONE, description="Available vehicle type")
    max_patients_per_day: int = Field(default=8, description="Maximum patients per day")
    current_assignments: int = Field(default=0, description="Current number of assignments")
    specializations: List[str] = Field(default=[], description="Employee specializations")

class Patient(BaseModel):
    patient_id: str = Field(..., description="Unique patient identifier")
    patient_name: str = Field(..., description="Patient name")
    address: str = Field(..., description="Patient address")
    required_support: Optional[str] = Field(None, description="Required support services")
    required_hours_of_support: Optional[int] = Field(None, description="Required hours of support")
    additional_requirements: Optional[str] = Field(None, description="Additional requirements")
    illness: Optional[str] = Field(None, description="Patient illness/condition")
    contact_number: Optional[int] = Field(None, description="Contact number")
    requires_medication: Optional[str] = Field(None, description="Medication requirements")
    emergency_contact: Optional[str] = Field(None, description="Emergency contact")
    emergency_relation: Optional[str] = Field(None, description="Emergency contact relation")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    # Derived fields for compatibility
    name: str = Field(..., description="Patient name (alias for patient_name)")
    location: str = Field(..., description="Patient location (alias for address)")
    preferred_language: str = Field(default="English", description="Patient's preferred language")
    medical_conditions: List[str] = Field(default=[], description="Patient's medical conditions")
    required_services: List[ServiceType] = Field(default=[], description="Required services")
    service_times: Dict[str, str] = Field(default={}, description="Preferred times for each service")
    priority_level: int = Field(default=1, description="Priority level (1-5, 5 being highest)")

class EmployeeAssignment(BaseModel):
    employee_id: str
    employee_name: str
    patient_id: str
    patient_name: str
    service_type: ServiceType
    assigned_time: str
    estimated_duration: int  # in minutes
    travel_time: int  # in minutes
    start_time: str
    end_time: str
    priority_score: float
    assignment_reason: str

class RotaRequest(BaseModel):
    prompt: str = Field(..., description="Natural language request for employee assignment")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

class RotaResponse(BaseModel):
    success: bool
    message: str
    assignment: Optional[EmployeeAssignment] = None
    alternative_options: Optional[List[EmployeeAssignment]] = Field(default=None)

class DailySchedule(BaseModel):
    employee_id: str
    employee_name: str
    date: str
    assignments: List[EmployeeAssignment]
    total_working_hours: float
    total_travel_time: int
    workload_percentage: float 