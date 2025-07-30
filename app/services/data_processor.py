import pandas as pd
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import logging
from datetime import datetime, time

from ..models.schemas import Employee, Patient, EmployeeType, ServiceType, VehicleType, GenderEnum, TransportModeEnum, QualificationEnum

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.employees: List[Employee] = []
        self.patients: List[Patient] = []
        self.data_loaded = False
    
    async def process_excel_file(self, file_path: str) -> Dict:
        """Process Excel file containing employee and patient data"""
        try:
            logger.info(f"Processing Excel file: {file_path}")
            logger.info(f"File exists: {Path(file_path).exists()}")
            
            # Read both sheets
            employee_df = pd.read_excel(file_path, sheet_name='EmployeeDetails')
            patient_df = pd.read_excel(file_path, sheet_name='PatientDetails')
            
            logger.info(f"Employee data shape: {employee_df.shape}")
            logger.info(f"Patient data shape: {patient_df.shape}")
            
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
                employee = Employee(
                    EmployeeID=self._safe_str(row.get('EmployeeID', '')),
                    Name=self._safe_str(row.get('Name', '')),
                    Address=self._safe_str(row.get('Address', '')),
                    PostCode=self._safe_str(row.get('PostCode', '')),
                    Gender=self._safe_enum(row.get('Gender', ''), GenderEnum, GenderEnum.MALE),
                    Ethnicity=self._safe_str(row.get('Ethnicity', '')),
                    Religion=self._safe_str(row.get('Religion', '')),
                    TransportMode=self._safe_enum(row.get('TransportMode', ''), TransportModeEnum, TransportModeEnum.WALKING),
                    Qualification=self._safe_enum(row.get('Qualification', ''), QualificationEnum, QualificationEnum.CARER),
                    LanguageSpoken=self._safe_str(row.get('LanguageSpoken', '')),
                    CertificateExpiryDate=self._safe_str(row.get('CertificateExpiryDate', '')),
                    EarliestStart=self._safe_str(row.get('EarliestStart', '')),
                    LatestEnd=self._safe_str(row.get('LatestEnd', '')),
                    Shifts=self._safe_str(row.get('Shifts', '')),
                    ContactNumber=self._safe_str(row.get('ContactNumber', '')),
                    Notes=self._safe_str(row.get('Notes', ''))
                )
                employees.append(employee)
            except Exception as e:
                logger.warning(f"Skipping employee row: {str(e)}")
        return employees
    
    def _process_patients(self, df: pd.DataFrame) -> List[Patient]:
        """Process patient data from DataFrame"""
        patients = []
        
        for _, row in df.iterrows():
            try:
                patient = Patient(
                    PatientID=self._safe_str(row.get('PatientID', '')),
                    PatientName=self._safe_str(row.get('PatientName', '')),
                    Address=self._safe_str(row.get('Address', '')),
                    PostCode=self._safe_str(row.get('PostCode', '')),
                    Gender=self._safe_enum(row.get('Gender', ''), GenderEnum, GenderEnum.MALE),
                    Ethnicity=self._safe_str(row.get('Ethnicity', '')),
                    Religion=self._safe_str(row.get('Religion', '')),
                    RequiredSupport=self._safe_str(row.get('RequiredSupport', '')),
                    RequiredHoursOfSupport=self._safe_int(row.get('RequiredHoursOfSupport', 0)),
                    AdditionalRequirements=self._safe_str(row.get('AdditionalRequirements', '')),
                    Illness=self._safe_str(row.get('Illness', '')),
                    ContactNumber=self._safe_str(row.get('ContactNumber', '')),
                    RequiresMedication=self._safe_str(row.get('RequiresMedication', '')),
                    EmergencyContact=self._safe_str(row.get('EmergencyContact', '')),
                    EmergencyRelation=self._safe_str(row.get('EmergencyRelation', '')),
                    LanguagePreference=self._safe_str(row.get('LanguagePreference', '')),
                    Notes=self._safe_str(row.get('Notes', ''))
                )
                patients.append(patient)
            except Exception as e:
                logger.warning(f"Skipping patient row: {str(e)}")
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
    
    def _safe_enum(self, value: Any, enum_class, default_value):
        """Safely convert value to enum, handling NaN and None"""
        if pd.isna(value) or value is None:
            return default_value
        
        value_str = str(value).strip()
        
        # Try to match the value to enum values
        for enum_value in enum_class:
            if value_str.lower() == enum_value.value.lower():
                return enum_value
        
        # If no exact match, try partial matching
        for enum_value in enum_class:
            if enum_value.value.lower() in value_str.lower():
                return enum_value
        
        return default_value
    
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
            if emp.EmployeeID == employee_id:
                return emp
        return None
    
    def get_patient_by_id(self, patient_id: str) -> Optional[Patient]:
        """Get patient by ID"""
        for pat in self.patients:
            if pat.PatientID == patient_id:
                return pat
        return None
    
    def get_qualified_employees_for_service(self, service_type: ServiceType) -> List[Employee]:
        """Get employees qualified for a specific service type"""
        qualified = []
        
        for emp in self.employees:
            # Rule 1: For medicine, only nurses are qualified
            if service_type == ServiceType.MEDICINE:
                if emp.Qualification == QualificationEnum.NURSE:
                    qualified.append(emp)
            else:
                # Other services can be handled by both nurses and care workers
                qualified.append(emp)
        
        return qualified 