from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

from .data_processor import DataProcessor
from .openai_service import OpenAIService
from .travel_service import TravelService
from ..models.schemas import (
    EmployeeAssignment, Employee, Patient, ServiceType, 
    EmployeeType, DailySchedule, QualificationEnum
)
from ..database import DatabaseManager

logger = logging.getLogger(__name__)

class RotaService:
    def __init__(self, data_processor: DataProcessor, openai_service: OpenAIService, db_manager: DatabaseManager, travel_service: TravelService):
        self.data_processor = data_processor
        self.openai_service = openai_service
        self.current_assignments: List[EmployeeAssignment] = []
        self.db_manager = db_manager
        self.travel_service = travel_service
    
    async def process_assignment_request(self, prompt: str) -> EmployeeAssignment:
        """
        Process a natural language assignment request and return the best assignment
        """
        try:
            # Step 1: Extract details from the prompt using AI
            assignment_details = await self.openai_service.extract_assignment_details(prompt)
            
            patient_id = assignment_details.get("patient_id")
            service_type_str = assignment_details.get("service_type", "medicine")
            preferred_time = assignment_details.get("preferred_time")
            urgency = assignment_details.get("urgency", "medium")
            
            if not patient_id:
                raise Exception("Could not identify patient ID from the request")
            
            # Step 2: Get patient information
            patient = self.data_processor.get_patient_by_id(patient_id)
            if not patient:
                raise Exception(f"Patient {patient_id} not found")
            
            # Step 3: Map service type
            service_type = self._map_service_type(service_type_str)
            
            # Step 4: Get qualified employees for this service
            qualified_employees = self.data_processor.get_qualified_employees_for_service(service_type)
            
            if not qualified_employees:
                raise Exception(f"No qualified employees available for {service_type.value} service")
            
            # Step 5: Filter available employees based on current workload
            available_employees = self._filter_available_employees(qualified_employees)
            
            if not available_employees:
                raise Exception("No employees available at this time")
            
            # Calculate travel times
            employee_travel_times = {}
            for emp in available_employees:
                travel_time = self.travel_service.calculate_travel_time(emp.Address, patient.Address, emp.TransportMode.value.lower())
                employee_travel_times[emp.EmployeeID] = travel_time

            # Enhanced context with more details
            context = {
                "preferred_time": preferred_time,
                "urgency": urgency,
                "current_assignments": len(self.current_assignments),
                "requirements": "Follow all system requirements for matching",
                "employee_travel_times": employee_travel_times
            }
            
            ai_result = await self.openai_service.find_best_assignment(
                patient, available_employees, service_type, context
            )
            
            # Step 7: Create the assignment
            selected_employee = self.data_processor.get_employee_by_id(ai_result["employee_id"])
            if not selected_employee:
                raise Exception("Selected employee not found")
            
            assignment = self._create_assignment(
                employee=selected_employee,
                patient=patient,
                service_type=service_type,
                ai_result=ai_result,
                preferred_time=preferred_time
            )
            
            # Step 8: Add to current assignments
            self.current_assignments.append(assignment)
            
            # Step 9: Update employee's current assignment count
            selected_employee.current_assignments += 1
            
            logger.info(f"Assignment created: {selected_employee.Name} -> {patient.PatientName} for {service_type.value}")
            
            # Log operation
            self.db_manager.log_operation(
                operation_type="assignment_request",
                description=f"Processed assignment for patient {patient_id}",
                details={"prompt": prompt, "service_type": service_type_str}
            )

            # After creating assignment
            self.db_manager.log_assignment(assignment.dict())

            return assignment
            
        except Exception as e:
            logger.error(f"Error processing assignment request: {str(e)}")
            raise
    
    async def generate_weekly_schedule(self):
        """Generate weekly schedule for all patients"""
        self.db_manager.log_operation("weekly_schedule", "Starting weekly schedule generation")
        assignments = []
        for patient in self.data_processor.patients:
            try:
                prompt = f"Assign employee for patient {patient.PatientID} requiring {patient.RequiredSupport}"
                assignment = await self.process_assignment_request(prompt)
                assignments.append(assignment)
            except Exception as e:
                logger.error(f"Failed to assign for {patient.PatientID}: {str(e)}")
        # Simple optimization: sort by time
        assignments.sort(key=lambda a: a.assigned_time)
        self.db_manager.log_operation("weekly_schedule", "Completed weekly schedule", {"assignments_count": len(assignments)})
        return assignments
    
    def _map_service_type(self, service_str: str) -> ServiceType:
        """Map string to ServiceType enum"""
        service_mapping = {
            "medicine": ServiceType.MEDICINE,
            "exercise": ServiceType.EXERCISE,
            "companionship": ServiceType.COMPANIONSHIP,
            "personal_care": ServiceType.PERSONAL_CARE,
            "personal": ServiceType.PERSONAL_CARE,
            "care": ServiceType.PERSONAL_CARE
        }
        
        return service_mapping.get(service_str.lower(), ServiceType.MEDICINE)
    
    def _filter_available_employees(self, employees: List[Employee]) -> List[Employee]:
        """Filter employees based on availability and current workload"""
        available = []
        
        for emp in employees:
            # Check if employee is not overloaded
            if emp.current_assignments < emp.max_patients_per_day:
                available.append(emp)
        
        return available
    
    def _create_assignment(
        self, 
        employee: Employee, 
        patient: Patient, 
        service_type: ServiceType,
        ai_result: Dict[str, Any],
        preferred_time: Optional[str] = None
    ) -> EmployeeAssignment:
        """Create an EmployeeAssignment object"""
        
        # Calculate timing
        current_time = datetime.now()
        
        # Use preferred time if provided, otherwise use current time + 1 hour
        if preferred_time:
            try:
                assigned_time = datetime.strptime(preferred_time, "%H:%M").time()
                start_datetime = current_time.replace(
                    hour=assigned_time.hour, 
                    minute=assigned_time.minute, 
                    second=0, 
                    microsecond=0
                )
            except:
                start_datetime = current_time + timedelta(hours=1)
        else:
            start_datetime = current_time + timedelta(hours=1)
        
        # Get durations from AI result
        travel_time = ai_result.get("estimated_travel_time", 15)
        service_duration = ai_result.get("estimated_duration", 30)
        
        # Calculate end time
        end_datetime = start_datetime + timedelta(minutes=service_duration)
        
        assignment = EmployeeAssignment(
            employee_id=employee.EmployeeID,
            employee_name=employee.Name,
            patient_id=patient.PatientID,
            patient_name=patient.PatientName,
            service_type=service_type,
            assigned_time=start_datetime.strftime("%H:%M"),
            estimated_duration=service_duration,
            travel_time=travel_time,
            start_time=start_datetime.strftime("%H:%M"),
            end_time=end_datetime.strftime("%H:%M"),
            priority_score=ai_result.get("priority_score", 5.0),
            assignment_reason=ai_result.get("reasoning", "Automatic assignment")
        )
        
        return assignment
    
    def get_current_assignments(self) -> List[Dict]:
        """Get all current assignments"""
        return [assignment.dict() for assignment in self.current_assignments]
    
    def get_employee_schedule(self, employee_id: str, date: str = None) -> DailySchedule:
        """Get daily schedule for a specific employee"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        employee = self.data_processor.get_employee_by_id(employee_id)
        if not employee:
            raise Exception(f"Employee {employee_id} not found")
        
        # Filter assignments for this employee and date
        employee_assignments = [
            assignment for assignment in self.current_assignments
            if assignment.employee_id == employee_id
        ]
        
        # Calculate metrics
        total_working_hours = sum(
            assignment.estimated_duration for assignment in employee_assignments
        ) / 60.0  # Convert to hours
        
        total_travel_time = sum(
            assignment.travel_time for assignment in employee_assignments
        )
        
        # Calculate workload percentage (assuming 8-hour workday)
        workload_percentage = (total_working_hours / 8.0) * 100
        
        return DailySchedule(
            employee_id=employee_id,
            employee_name=employee.Name,
            date=date,
            assignments=employee_assignments,
            total_working_hours=total_working_hours,
            total_travel_time=total_travel_time,
            workload_percentage=workload_percentage
        )
    
    def optimize_schedule(self) -> Dict[str, Any]:
        """Optimize the current schedule using AI"""
        if not self.current_assignments:
            return {"message": "No assignments to optimize"}
        
        # This would use the OpenAI service to optimize
        # For now, return basic analysis
        employees_workload = {}
        for assignment in self.current_assignments:
            emp_id = assignment.employee_id
            if emp_id not in employees_workload:
                employees_workload[emp_id] = []
            employees_workload[emp_id].append(assignment)
        
        return {
            "total_assignments": len(self.current_assignments),
            "employees_involved": len(employees_workload),
            "average_assignments_per_employee": len(self.current_assignments) / max(1, len(employees_workload))
        }
    
    def clear_assignments(self):
        """Clear all current assignments (for testing/reset)"""
        self.current_assignments = []
        # Reset employee assignment counts
        for employee in self.data_processor.employees:
            employee.current_assignments = 0
    
    def validate_assignment_rules(self, assignment: EmployeeAssignment) -> List[str]:
        """Validate that an assignment follows all the rules"""
        violations = []
        
        employee = self.data_processor.get_employee_by_id(assignment.employee_id)
        patient = self.data_processor.get_patient_by_id(assignment.patient_id)
        
        if not employee or not patient:
            violations.append("Employee or patient not found")
            return violations
        
        # Rule 1: Medicine services require qualified personnel (nurses)
        if assignment.service_type == ServiceType.MEDICINE:
            if employee.Qualification != QualificationEnum.NURSE:
                violations.append("Medicine services require a qualified nurse")
        
        # Rule 3: Language preference check
        if patient.LanguagePreference not in employee.LanguageSpoken and patient.LanguagePreference != "English":
            violations.append(f"Employee doesn't speak patient's preferred language ({patient.LanguagePreference})")
        
        # Workload check
        if employee.current_assignments >= employee.max_patients_per_day:
            violations.append("Employee workload exceeds maximum daily capacity")
        
        return violations 