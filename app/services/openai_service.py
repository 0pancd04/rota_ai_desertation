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
                "id": patient.PatientID,
                "name": patient.PatientName,
                "location": patient.Address,
                "preferred_language": patient.LanguagePreference,
                "medical_conditions": [patient.Illness] if patient.Illness else [],
                "priority_level": 1  # Default priority level
            }
            
            employees_data = []
            for emp in qualified_employees:
                employees_data.append({
                    "id": emp.EmployeeID,
                    "name": emp.Name,
                    "type": emp.Qualification.value,
                    "location": emp.Address,
                    "postcode": emp.PostCode,
                    "languages": emp.LanguageSpoken.split(','),
                    "transport": emp.TransportMode.value,
                    "shifts": emp.Shifts,
                    "earliest_start": emp.EarliestStart,
                    "latest_end": emp.LatestEnd,
                    "current_assignments": emp.current_assignments if hasattr(emp, 'current_assignments') else 0,
                    "travel_time_to_patient": context.get("employee_travel_times", {}).get(emp.EmployeeID, 15)
                })
            
            system_prompt = f"""
            You are an AI assistant for a healthcare rota system. Your task is to select the best employee for a patient assignment based on complex criteria.
            
            Key Rules and Priorities (in order):
            1. Qualification Matching: Only qualified nurses for medication tasks. Prioritize Senior Carer > Carer for complex cases. Verify certificate validity.
            2. Geographic Optimization: Minimize travel time based on transport mode, cluster assignments geographically, consider traffic.
            3. Language and Cultural Matching: Prioritize language match, consider cultural/religious compatibility.
            4. Schedule Optimization: Balance workload, respect shift constraints, ensure coverage, handle emergencies.
            5. Other: Respect earliest start/latest end times, transport limitations.
            
            Patient Details: {json.dumps(patient_data, indent=2)}
            Service Required: {service_type.value}
            Qualified Employees: {json.dumps(employees_data, indent=2)}
            
            Select the best employee and provide:
            1. employee_id: The selected employee's ID
            2. reasoning: Detailed explanation including how it matches each criterion
            3. priority_score: Score 1-10
            4. estimated_travel_time: Estimated in minutes (use reasonable estimate based on locations)
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
                    "employee_id": qualified_employees[0].EmployeeID,
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