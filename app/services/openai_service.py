import openai
from typing import Dict, List, Optional, Any
import json
import logging
import os
from dotenv import load_dotenv

from ..models.schemas import Employee, Patient, ServiceType, EmployeeAssignment

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = "gpt-3.5-turbo"  # You can change to gpt-4 if needed
    
    async def extract_assignment_details(self, prompt: str) -> Dict[str, Any]:
        """
        Extract assignment details from natural language prompt
        """
        try:
            system_prompt = """
            You are an AI assistant for a healthcare rota system. 
            Extract the following information from the user's prompt:
            - patient_id: The patient identifier (e.g., P001, P002)
            - service_type: The type of service required (medicine, exercise, companionship, personal_care)
            - preferred_time: If mentioned, the preferred time for the service
            - urgency: How urgent the request is (high, medium, low)
            
            Return the information as a JSON object. If information is not provided, use null.
            
            Example:
            Input: "The patient P001 is required Exercise today can you assign available employee."
            Output: {
                "patient_id": "P001",
                "service_type": "exercise",
                "preferred_time": null,
                "urgency": "medium"
            }
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"Error extracting assignment details: {str(e)}")
            # Fallback: try to extract patient ID manually
            words = prompt.upper().split()
            patient_id = None
            for word in words:
                if word.startswith('P') and len(word) <= 5:
                    patient_id = word
                    break
            
            return {
                "patient_id": patient_id,
                "service_type": "medicine",  # Default assumption
                "preferred_time": None,
                "urgency": "medium"
            }
    
    async def find_best_assignment(
        self, 
        patient: Patient, 
        qualified_employees: List[Employee],
        service_type: ServiceType,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use AI to find the best employee assignment based on multiple criteria
        """
        try:
            # Prepare data for AI analysis
            patient_data = {
                "id": patient.patient_id,
                "name": patient.name,
                "location": patient.location,
                "preferred_language": patient.preferred_language,
                "medical_conditions": patient.medical_conditions,
                "priority_level": patient.priority_level
            }
            
            employees_data = []
            for emp in qualified_employees:
                employees_data.append({
                    "id": emp.employee_id,
                    "name": emp.name,
                    "type": emp.employee_type.value,
                    "location": emp.location,
                    "languages": emp.languages,
                    "vehicle": emp.vehicle.value,
                    "current_assignments": emp.current_assignments,
                    "max_patients": emp.max_patients_per_day,
                    "availability_start": emp.availability_start.strftime("%H:%M"),
                    "availability_end": emp.availability_end.strftime("%H:%M")
                })
            
            system_prompt = f"""
            You are an AI assistant for a healthcare rota system. Your task is to select the best employee for a patient assignment.
            
            Rules to follow:
            1. For medicine services, only nurses are qualified (already filtered)
            2. Prefer employees who speak the patient's preferred language
            3. Consider travel time based on location proximity and vehicle availability
            4. Balance workload - avoid overloading employees
            5. Consider employee availability times
            
            Patient Details: {json.dumps(patient_data, indent=2)}
            Service Required: {service_type.value}
            Qualified Employees: {json.dumps(employees_data, indent=2)}
            
            Select the best employee and provide:
            1. employee_id: The selected employee's ID
            2. reasoning: Detailed explanation of why this employee was selected
            3. priority_score: A score from 1-10 indicating how good this match is
            4. estimated_travel_time: Estimated travel time in minutes
            5. estimated_duration: Estimated service duration in minutes
            
            Return as JSON format only.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt}
                ],
                temperature=0.2
            )
            
            result = response.choices[0].message.content
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"Error finding best assignment: {str(e)}")
            # Fallback: select first available employee
            if qualified_employees:
                return {
                    "employee_id": qualified_employees[0].employee_id,
                    "reasoning": "Automatic selection due to AI service error",
                    "priority_score": 5.0,
                    "estimated_travel_time": 15,
                    "estimated_duration": 30
                }
            else:
                raise Exception("No qualified employees available")
    
    async def generate_schedule_optimization(
        self, 
        assignments: List[EmployeeAssignment]
    ) -> Dict[str, Any]:
        """
        Use AI to optimize the overall schedule
        """
        try:
            assignments_data = [
                {
                    "employee_id": a.employee_id,
                    "patient_id": a.patient_id,
                    "service_type": a.service_type.value,
                    "start_time": a.start_time,
                    "end_time": a.end_time,
                    "travel_time": a.travel_time
                }
                for a in assignments
            ]
            
            system_prompt = f"""
            You are an AI assistant for optimizing healthcare staff schedules.
            
            Current assignments: {json.dumps(assignments_data, indent=2)}
            
            Analyze the schedule and provide optimization suggestions:
            1. conflicts: Any time conflicts or overbooked employees
            2. efficiency_score: Overall efficiency score (1-10)
            3. suggestions: List of specific improvements
            4. workload_balance: Assessment of workload distribution
            
            Return as JSON format.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt}
                ],
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"Error generating schedule optimization: {str(e)}")
            return {
                "conflicts": [],
                "efficiency_score": 7,
                "suggestions": ["Unable to analyze due to AI service error"],
                "workload_balance": "Unknown"
            } 