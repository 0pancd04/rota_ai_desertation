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

class GenderEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    NON_BINARY = "Non-binary"

class TransportModeEnum(str, Enum):
    CAR = "Car"
    PUBLIC_TRANSPORT = "Public Transport"
    BICYCLE = "Bicycle"
    WALKING = "Walking"

class QualificationEnum(str, Enum):
    SENIOR_CARER = "Senior Carer"
    CARER = "Carer"
    NURSE = "Nurse"

class Employee(BaseModel):
    EmployeeID: str = Field(..., alias="EmployeeID")
    Name: str = Field(..., alias="Name")
    Address: str = Field(..., alias="Address")
    PostCode: str = Field(..., alias="PostCode")
    Gender: GenderEnum = Field(..., alias="Gender")
    Ethnicity: str = Field(..., alias="Ethnicity")
    Religion: str = Field(..., alias="Religion")
    TransportMode: TransportModeEnum = Field(..., alias="TransportMode")
    Qualification: QualificationEnum = Field(..., alias="Qualification")
    LanguageSpoken: str = Field(..., alias="LanguageSpoken")  # Multiple languages supported
    CertificateExpiryDate: str = Field(..., alias="CertificateExpiryDate")  # YYYY-MM-DD
    EarliestStart: str = Field(..., alias="EarliestStart")  # HH:MM
    LatestEnd: str = Field(..., alias="LatestEnd")  # HH:MM
    Shifts: str = Field(..., alias="Shifts")  # Combination of Breakfast/Lunch/Evening
    ContactNumber: str = Field(..., alias="ContactNumber")
    Notes: Optional[str] = Field(None, alias="Notes")
    
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
    PatientID: str = Field(..., alias="PatientID")
    PatientName: str = Field(..., alias="PatientName")
    Address: str = Field(..., alias="Address")
    PostCode: str = Field(..., alias="PostCode")
    Gender: GenderEnum = Field(..., alias="Gender")
    Ethnicity: str = Field(..., alias="Ethnicity")
    Religion: str = Field(..., alias="Religion")
    RequiredSupport: str = Field(..., alias="RequiredSupport")  # Comma-separated services
    RequiredHoursOfSupport: int = Field(..., alias="RequiredHoursOfSupport")
    AdditionalRequirements: str = Field(..., alias="AdditionalRequirements")
    Illness: str = Field(..., alias="Illness")
    ContactNumber: str = Field(..., alias="ContactNumber")
    RequiresMedication: str = Field(..., alias="RequiresMedication")  # Y/N
    EmergencyContact: str = Field(..., alias="EmergencyContact")
    EmergencyRelation: str = Field(..., alias="EmergencyRelation")
    LanguagePreference: str = Field(..., alias="LanguagePreference")
    Notes: Optional[str] = Field(None, alias="Notes")
    
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