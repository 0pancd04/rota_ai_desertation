import pandas as pd
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import logging
from datetime import datetime, time

from ..models.schemas import Employee, Patient, EmployeeType, ServiceType, VehicleType

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.employees: List[Employee] = []
        self.patients: List[Patient] = []
        self.data_loaded = False
    
    async def process_excel_file(self, file_path: str) -> Dict:
        """Process Excel file containing employee and patient data"""
        try:
            # Read both sheets
            employee_df = pd.read_excel(file_path, sheet_name='EmployeeDetails')
            patient_df = pd.read_excel(file_path, sheet_name='PatientDetails')
            
            # Process employees
            self.employees = self._process_employees(employee_df)
            
            # Process patients
            self.patients = self._process_patients(patient_df)
            
            self.data_loaded = True
            
            logger.info(f"Processed {len(self.employees)} employees and {len(self.patients)} patients")
            
            return {
                "employees": [emp.dict() for emp in self.employees],
                "patients": [pat.dict() for pat in self.patients]
            }
            
        except Exception as e:
            logger.error(f"Error processing Excel file: {str(e)}")
            raise
    
    def _process_employees(self, df: pd.DataFrame) -> List[Employee]:
        """Process employee data from DataFrame"""
        employees = []
        
        for _, row in df.iterrows():
            try:
                # Parse employee type from qualification
                qualification = self._safe_str(row.get('Qualification', ''))
                emp_type = EmployeeType.NURSE if 'nurse' in qualification.lower() else EmployeeType.CARE_WORKER
                
                # Parse availability times
                start_time = self._parse_time(self._safe_str(row.get('EarliestStart', '09:00')))
                end_time = self._parse_time(self._safe_str(row.get('LatestEnd', '17:00')))
                
                # Parse vehicle type
                vehicle = self._parse_vehicle(self._safe_str(row.get('VehicleAvailable', 'none')))
                
                # Parse languages
                languages = self._parse_list(self._safe_str(row.get('LanguageSpoken', '')))
                
                employee = Employee(
                    employee_id=self._safe_str(row.get('EmployeeID', '')),
                    name=self._safe_str(row.get('Name', '')),
                    address=self._safe_str(row.get('Address', '')),
                    vehicle_available=self._safe_str(row.get('VehicleAvailable', '')),
                    qualification=qualification,
                    language_spoken=self._safe_str(row.get('LanguageSpoken', '')),
                    certificate_expiry_date=self._safe_datetime(row.get('CertificateExpiryDate')),
                    earliest_start=self._safe_str(row.get('EarliestStart', '')),
                    latest_end=self._safe_str(row.get('LatestEnd', '')),
                    availability=self._safe_str(row.get('Availability', '')),
                    contact_number=self._safe_int(row.get('ContactNumber')),
                    notes=self._safe_str(row.get('Notes', '')),
                    
                    # Derived fields for compatibility
                    employee_type=emp_type,
                    languages=languages,
                    availability_start=start_time,
                    availability_end=end_time,
                    vehicle=vehicle,
                    max_patients_per_day=8,
                    current_assignments=0,
                    specializations=[]
                )
                
                employees.append(employee)
                
            except Exception as e:
                logger.warning(f"Skipping employee row due to error: {str(e)}")
                continue
        
        return employees
    
    def _process_patients(self, df: pd.DataFrame) -> List[Patient]:
        """Process patient data from DataFrame"""
        patients = []
        
        for _, row in df.iterrows():
            try:
                # Parse required services
                services = self._parse_services(self._safe_str(row.get('RequiredSupport', '')))
                
                # Parse medical conditions
                conditions = self._parse_list(self._safe_str(row.get('Illness', '')))
                
                patient_name = self._safe_str(row.get('PatientName', ''))
                address = self._safe_str(row.get('Address', ''))
                
                patient = Patient(
                    patient_id=self._safe_str(row.get('PatientID', '')),
                    patient_name=patient_name,
                    address=address,
                    required_support=self._safe_str(row.get('RequiredSupport', '')),
                    required_hours_of_support=self._safe_int(row.get('RequiredHoursOfSupport')),
                    additional_requirements=self._safe_str(row.get('AdditionalRequirements', '')),
                    illness=self._safe_str(row.get('Illness', '')),
                    contact_number=self._safe_int(row.get('ContactNumber')),
                    requires_medication=self._safe_str(row.get('RequiresMedication', '')),
                    emergency_contact=self._safe_str(row.get('EmergencyContact', '')),
                    emergency_relation=self._safe_str(row.get('EmergencyRelation', '')),
                    notes=self._safe_str(row.get('Notes', '')),
                    
                    # Derived fields for compatibility
                    name=patient_name,
                    location=address,
                    preferred_language="English",
                    medical_conditions=conditions,
                    required_services=services,
                    service_times={},
                    priority_level=1
                )
                
                patients.append(patient)
                
            except Exception as e:
                logger.warning(f"Skipping patient row due to error: {str(e)}")
                continue
        
        return patients
    
    def _safe_str(self, value: Any) -> str:
        """Safely convert value to string, handling NaN and None"""
        if pd.isna(value) or value is None:
            return ""
        return str(value).strip()
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to int, handling NaN and None"""
        if pd.isna(value) or value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_datetime(self, value: Any) -> Optional[datetime]:
        """Safely convert value to datetime, handling NaN and None"""
        if pd.isna(value) or value is None:
            return None
        if isinstance(value, datetime):
            return value
        return None
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string to time object"""
        try:
            if not time_str or pd.isna(time_str):
                return time(9, 0)  # Default to 9:00 AM
            
            time_str = str(time_str).strip()
            if ':' in time_str:
                hour, minute = map(int, time_str.split(':'))
                return time(hour, minute)
            else:
                return time(int(time_str), 0)
        except:
            return time(9, 0)
    
    def _parse_vehicle(self, vehicle_str: str) -> VehicleType:
        """Parse vehicle string to VehicleType enum"""
        if not vehicle_str or pd.isna(vehicle_str):
            return VehicleType.NONE
        
        vehicle_str = str(vehicle_str).lower().strip()
        if 'car' in vehicle_str or 'yes' in vehicle_str:
            return VehicleType.CAR
        elif 'bike' in vehicle_str:
            return VehicleType.BIKE
        else:
            return VehicleType.NONE
    
    def _parse_list(self, list_str: str) -> List[str]:
        """Parse comma-separated string to list"""
        if not list_str or pd.isna(list_str):
            return []
        
        return [item.strip() for item in str(list_str).split(',') if item.strip()]
    
    def _parse_services(self, services_str: str) -> List[ServiceType]:
        """Parse services string to list of ServiceType"""
        if not services_str or pd.isna(services_str):
            return []
        
        services = []
        service_list = self._parse_list(services_str)
        
        for service in service_list:
            service_lower = service.lower()
            if 'medicine' in service_lower:
                services.append(ServiceType.MEDICINE)
            elif 'exercise' in service_lower:
                services.append(ServiceType.EXERCISE)
            elif 'companion' in service_lower:
                services.append(ServiceType.COMPANIONSHIP)
            elif 'personal' in service_lower or 'care' in service_lower:
                services.append(ServiceType.PERSONAL_CARE)
        
        return services
    
    def _parse_service_times(self, times_str: str) -> Dict[str, str]:
        """Parse service times string to dictionary"""
        if not times_str or pd.isna(times_str):
            return {}
        
        times_dict = {}
        try:
            # Assuming format like "medicine:10:00,exercise:14:00"
            pairs = str(times_str).split(',')
            for pair in pairs:
                if ':' in pair:
                    parts = pair.split(':')
                    if len(parts) >= 3:
                        service = parts[0].strip()
                        time_part = ':'.join(parts[1:]).strip()
                        times_dict[service] = time_part
        except:
            pass
        
        return times_dict
    
    def get_employees(self) -> List[Dict]:
        """Get all employees as dictionaries"""
        return [emp.dict() for emp in self.employees]
    
    def get_patients(self) -> List[Dict]:
        """Get all patients as dictionaries"""
        return [pat.dict() for pat in self.patients]
    
    def has_data(self) -> bool:
        """Check if data is loaded"""
        return self.data_loaded and len(self.employees) > 0 and len(self.patients) > 0
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Employee]:
        """Get employee by ID"""
        for emp in self.employees:
            if emp.employee_id == employee_id:
                return emp
        return None
    
    def get_patient_by_id(self, patient_id: str) -> Optional[Patient]:
        """Get patient by ID"""
        for pat in self.patients:
            if pat.patient_id == patient_id:
                return pat
        return None
    
    def get_qualified_employees_for_service(self, service_type: ServiceType) -> List[Employee]:
        """Get employees qualified for a specific service type"""
        qualified = []
        
        for emp in self.employees:
            # Rule 1: For medicine, only nurses are qualified
            if service_type == ServiceType.MEDICINE:
                if emp.employee_type == EmployeeType.NURSE:
                    qualified.append(emp)
            else:
                # Other services can be handled by both nurses and care workers
                qualified.append(emp)
        
        return qualified 