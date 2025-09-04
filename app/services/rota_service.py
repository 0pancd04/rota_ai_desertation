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
from .scheduler_core import SchedulerCore

logger = logging.getLogger(__name__)

class RotaService:
    def __init__(self, data_processor: DataProcessor, openai_service: OpenAIService, db_manager: DatabaseManager, travel_service: TravelService):
        self.data_processor = data_processor
        self.openai_service = openai_service
        self.current_assignments: List[EmployeeAssignment] = []
        self.db_manager = db_manager
        self.travel_service = travel_service
        self.scheduler_core = SchedulerCore(self.data_processor, self.travel_service, self.db_manager)
        # Load existing assignments from database
        self._load_assignments_from_database()
    
    def _load_assignments_from_database(self):
        """Load existing assignments from database"""
        try:
            db_assignments = self.db_manager.get_assignments()
            self.current_assignments = []
            for assignment_data in db_assignments:
                try:
                    assignment = EmployeeAssignment(
                        employee_id=assignment_data['employee_id'],
                        employee_name=assignment_data['employee_name'],
                        patient_id=assignment_data['patient_id'],
                        patient_name=assignment_data['patient_name'],
                        service_type=ServiceType(assignment_data['service_type']),
                        assigned_time=assignment_data['assigned_time'],
                        estimated_duration=assignment_data.get('duration', 30),
                        travel_time=assignment_data.get('travel_time', 15),
                        start_time=assignment_data.get('start_time', ''),
                        end_time=assignment_data.get('end_time', ''),
                        priority_score=assignment_data.get('priority_score', 5.0),
                        assignment_reason=assignment_data.get('reasoning', '')
                    )
                    self.current_assignments.append(assignment)
                except Exception as e:
                    logger.warning(f"Error loading assignment {assignment_data.get('id', 'unknown')}: {str(e)}")
            
            logger.info(f"Loaded {len(self.current_assignments)} assignments from database")
        except Exception as e:
            logger.error(f"Error loading assignments from database: {str(e)}")
    
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
            
            # Calculate travel times (cached) using full addresses with postcodes when available
            employee_travel_times = {}
            patient_origin_full = f"{patient.Address}, {patient.PostCode}" if patient.PostCode and patient.PostCode not in patient.Address else patient.Address
            for emp in available_employees:
                emp_origin_full = f"{emp.Address}, {emp.PostCode}" if emp.PostCode and emp.PostCode not in emp.Address else emp.Address
                travel_time = self.travel_service.get_travel_time(
                    origin=emp_origin_full,
                    destination=patient_origin_full,
                    mode=emp.TransportMode.value
                )
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
    
    async def generate_weekly_schedule(self, engine: str = "core"):
        """Generate weekly schedule using the requested engine.

        Returns DB-shaped assignments (with IDs) for frontend compatibility.
        """
        self.db_manager.log_operation("weekly_schedule", f"Starting weekly schedule generation (engine={engine})")
        try:
            if engine == "core":
                summary = self.scheduler_core.generate_weekly_rota()
                logger.info(f"SchedulerCore summary: {summary}")
                # Return DB rows with IDs
                assignments = self.db_manager.get_assignments()
                self.db_manager.log_operation("weekly_schedule", "Completed weekly schedule (core)", {"assignments_count": len(assignments)})
                return assignments
            else:
                # Legacy AI-driven per-patient flow
                legacy_assignments: List[EmployeeAssignment] = []
                for patient in self.data_processor.patients:
                    try:
                        prompt = f"Assign employee for patient {patient.PatientID} requiring {patient.RequiredSupport}"
                        assignment = await self.process_assignment_request(prompt)
                        legacy_assignments.append(assignment)
                    except Exception as e:
                        logger.error(f"Failed to assign for {patient.PatientID}: {str(e)}")
                legacy_assignments.sort(key=lambda a: a.assigned_time)
                self.db_manager.log_operation("weekly_schedule", "Completed weekly schedule (legacy)", {"assignments_count": len(legacy_assignments)})
                # For compatibility with frontend editing, return DB rows instead
                return self.db_manager.get_assignments()
        except Exception as e:
            logger.error(f"Error in generate_weekly_schedule: {e}")
            raise
    
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
        
        # Use ISO datetimes to standardize for DB/frontend
        assigned_iso = start_datetime.replace(second=0, microsecond=0).isoformat()
        end_iso = end_datetime.replace(second=0, microsecond=0).isoformat()

        assignment = EmployeeAssignment(
            employee_id=employee.EmployeeID,
            employee_name=employee.Name,
            patient_id=patient.PatientID,
            patient_name=patient.PatientName,
            service_type=service_type,
            assigned_time=assigned_iso,
            estimated_duration=service_duration,
            travel_time=travel_time,
            start_time=assigned_iso,
            end_time=end_iso,
            priority_score=ai_result.get("priority_score", 5.0),
            assignment_reason=ai_result.get("reasoning", "Automatic assignment")
        )
        
        return assignment
    
    def get_current_assignments(self) -> List[Dict]:
        """Get all current assignments with database IDs"""
        # Get fresh data from database to ensure we have IDs
        db_assignments = self.db_manager.get_assignments()
        return db_assignments
    
    def update_assignment(self, assignment_id: int, updates: Dict[str, Any]) -> bool:
        """Update an existing assignment"""
        try:
            # First get the assignment from database to get all details
            db_assignment = self.db_manager.get_assignment_by_id(assignment_id)
            if not db_assignment:
                logger.error(f"Assignment {assignment_id} not found in database")
                return False
            
            # Update the database
            db_updates = {}
            for field, value in updates.items():
                # Map frontend field names to database field names
                if field == 'estimated_duration':
                    db_updates['duration'] = value
                elif field == 'assignment_reason':
                    db_updates['reasoning'] = value
                else:
                    db_updates[field] = value
            
            success = self.db_manager.update_assignment(assignment_id, db_updates)
            
            if success:
                # Update the in-memory assignment
                for i, assignment in enumerate(self.current_assignments):
                    # Try to match by all unique identifiers since we don't store DB ID in memory
                    if (assignment.employee_id == db_assignment['employee_id'] and 
                        assignment.patient_id == db_assignment['patient_id'] and
                        assignment.assigned_time == db_assignment['assigned_time']):
                        
                        # Apply updates to the in-memory assignment
                        assignment_dict = assignment.dict()
                        assignment_dict.update(updates)
                        
                        # Create updated assignment object
                        updated_assignment = EmployeeAssignment(**assignment_dict)
                        self.current_assignments[i] = updated_assignment
                        
                        logger.info(f"Updated assignment {assignment_id} in memory and database")
                        break
                
                # Log operation
                self.db_manager.log_operation(
                    operation_type="assignment_update",
                    description=f"Updated assignment {assignment_id}",
                    details={"updates": updates, "assignment_id": assignment_id}
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating assignment {assignment_id}: {str(e)}")
            return False
    
    def delete_assignment(self, assignment_id: int) -> bool:
        """Delete an assignment"""
        try:
            # First get the assignment from database
            db_assignment = self.db_manager.get_assignment_by_id(assignment_id)
            if not db_assignment:
                logger.error(f"Assignment {assignment_id} not found in database")
                return False
            
            # Delete from database
            success = self.db_manager.delete_assignment(assignment_id)
            
            if success:
                # Remove from in-memory assignments
                for i, assignment in enumerate(self.current_assignments):
                    if (assignment.employee_id == db_assignment['employee_id'] and 
                        assignment.patient_id == db_assignment['patient_id'] and
                        assignment.assigned_time == db_assignment['assigned_time']):
                        
                        del self.current_assignments[i]
                        logger.info(f"Removed assignment {assignment_id} from memory")
                        break
                
                # Update employee assignment count if possible
                employee = self.data_processor.get_employee_by_id(db_assignment['employee_id'])
                if employee and employee.current_assignments > 0:
                    employee.current_assignments -= 1
                
                # Log operation
                self.db_manager.log_operation(
                    operation_type="assignment_delete",
                    description=f"Deleted assignment {assignment_id}",
                    details={"assignment_id": assignment_id, "employee_id": db_assignment['employee_id'], "patient_id": db_assignment['patient_id']}
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting assignment {assignment_id}: {str(e)}")
            return False
    
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
        # Clear assignments from database
        cursor = self.db_manager.conn.cursor()
        cursor.execute("DELETE FROM assignments")
        self.db_manager.conn.commit()
        # Reset employee assignment counts
        for employee in self.data_processor.employees:
            employee.current_assignments = 0
        logger.info("Cleared all assignments from memory and database")
    
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

        # No multiple same-employee-to-same-patient visits per day (post-clean) safeguard
        try:
            start_iso = assignment.start_time
            if self.db_manager.has_employee_patient_assignment_on_date(employee.EmployeeID, patient.PatientID, start_iso):
                violations.append("Employee already assigned to this patient today")
        except Exception:
            pass
        
        return violations 

    def _parse_shift_bounds(self, earliest: str, latest: str):
        from datetime import time as dtime
        def _parse(t: str, default: dtime) -> dtime:
            try:
                if not t:
                    return default
                parts = t.strip().split(":")
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                return dtime(hour, minute)
            except Exception:
                return default
        return _parse(earliest, dtime(9,0)), _parse(latest, dtime(17,0))

    def _in_shift(self, employee: Employee, start_iso: str, end_iso: str) -> bool:
        try:
            start_dt = datetime.fromisoformat(start_iso)
            end_dt = datetime.fromisoformat(end_iso)
            e, l = self._parse_shift_bounds(getattr(employee, 'EarliestStart', ''), getattr(employee, 'LatestEnd', ''))
            day = start_dt.date()
            shift_start = start_dt.replace(hour=e.hour, minute=e.minute, second=0, microsecond=0)
            shift_end = start_dt.replace(hour=l.hour, minute=l.minute, second=0, microsecond=0)
            return start_dt >= shift_start and end_dt <= shift_end
        except Exception:
            return True

    def _employee_same_day_assigned(self, employee_id: str, date_iso: str) -> bool:
        records = self.db_manager.get_employee_assignments_for_date(employee_id, date_iso)
        return len(records) > 0

    def _calc_travel_minutes(self, employee: Employee, patient: Patient) -> int:
        origin = f"{employee.Address}, {employee.PostCode}" if employee.PostCode and employee.PostCode not in employee.Address else employee.Address
        destination = f"{patient.Address}, {patient.PostCode}" if patient.PostCode and patient.PostCode not in patient.Address else patient.Address
        return self.travel_service.get_travel_time(origin=origin, destination=destination, mode=employee.TransportMode.value)

    def _choose_best_employee_for_reassignment(self, candidates: List[Employee], patient: Patient, start_iso: str, end_iso: str) -> Optional[Employee]:
        # Rank: has same-day assignments (True first), then by travel time ascending
        scored: List[tuple[int, int, Employee]] = []
        for emp in candidates:
            same_day = 1 if self._employee_same_day_assigned(emp.EmployeeID, start_iso) else 0
            travel = self._calc_travel_minutes(emp, patient)
            scored.append(( -same_day, travel, emp ))
        if not scored:
            return None
        scored.sort()
        return scored[0][2]

    def _get_candidate_employees(self, start_iso: str, end_iso: str, current_employee_id: str) -> List[Employee]:
        candidates: List[Employee] = []
        for emp in self.data_processor.employees:
            if emp.EmployeeID == current_employee_id:
                continue
            if not self._in_shift(emp, start_iso, end_iso):
                continue
            if self.db_manager.has_overlap_for_employee(emp.EmployeeID, start_iso, end_iso):
                continue
            candidates.append(emp)
        return candidates

    def _update_assignment_employee(self, assignment_id: int, new_employee: Employee, patient: Patient, start_iso: str, end_iso: str) -> bool:
        travel_min = self._calc_travel_minutes(new_employee, patient)
        updates = {
            'employee_id': new_employee.EmployeeID,
            'employee_name': new_employee.Name,
            'travel_time': travel_min,
            'reasoning': 'Reanalyzed and reassigned to nearer available employee',
            'priority_score': 5.0
        }
        return self.db_manager.update_assignment(assignment_id, updates)

    def reanalyze_assignments(self, assignment_ids: List[int], allow_time_change: bool = False) -> List[Dict[str, Any]]:
        """Reanalyze and reassign selected assignments based on availability and proximity.

        - Prefer employees who already have assignments the same day but are free in the time window
        - Exclude employees with overlapping assignments
        - Fallback to nearest available employee even if no same-day assignments
        - Optional future enhancement: time change when allow_time_change=True (not implemented yet)
        """
        updated: List[Dict[str, Any]] = []
        for aid in assignment_ids:
            row = self.db_manager.get_assignment_by_id(aid)
            if not row:
                continue
            start_iso = row.get('start_time')
            end_iso = row.get('end_time')
            if not start_iso or not end_iso:
                continue
            patient = self.data_processor.get_patient_by_id(row.get('patient_id'))
            if not patient:
                continue
            current_emp_id = row.get('employee_id')
            candidates = self._get_candidate_employees(start_iso, end_iso, current_emp_id)
            chosen = self._choose_best_employee_for_reassignment(candidates, patient, start_iso, end_iso)
            if not chosen:
                # fallback: nearest overall ignoring shift bounds but still non-overlapping
                fallback = []
                for emp in self.data_processor.employees:
                    if emp.EmployeeID == current_emp_id:
                        continue
                    if self.db_manager.has_overlap_for_employee(emp.EmployeeID, start_iso, end_iso):
                        continue
                    travel = self._calc_travel_minutes(emp, patient)
                    fallback.append((travel, emp))
                fallback.sort()
                chosen = fallback[0][1] if fallback else None
            if not chosen:
                continue
            if self._update_assignment_employee(aid, chosen, patient, start_iso, end_iso):
                updated.append(self.db_manager.get_assignment_by_id(aid))
        # Log operation
        try:
            self.db_manager.log_operation(
                operation_type="reanalysis",
                description="Reanalyzed selected assignments",
                details={"assignment_ids": assignment_ids, "updated": [a.get('id') for a in updated]}
            )
        except Exception:
            pass
        return updated