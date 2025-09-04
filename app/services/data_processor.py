import pandas as pd
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import logging
from datetime import datetime, time

from ..models.schemas import Employee, Patient, EmployeeType, ServiceType, VehicleType, GenderEnum, TransportModeEnum, QualificationEnum
from ..database import DatabaseManager

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.employees: List[Employee] = []
        self.patients: List[Patient] = []
        self.data_loaded = False
        # Try to load existing data from database
        self._load_from_database()
    
    def _load_from_database(self):
        """Load existing data from database"""
        try:
            if self.db_manager.has_data():
                # Load employees from database
                db_employees = self.db_manager.get_employees()
                self.employees = []
                for emp_data in db_employees:
                    try:
                        employee = Employee(
                            EmployeeID=emp_data['employee_id'],
                            Name=emp_data['name'],
                            Address=emp_data['address'],
                            PostCode=emp_data['postcode'],
                            Gender=GenderEnum(emp_data['gender']),
                            Ethnicity=emp_data['ethnicity'],
                            Religion=emp_data['religion'],
                            TransportMode=TransportModeEnum(emp_data['transport_mode']),
                            Qualification=QualificationEnum(emp_data['qualification']),
                            LanguageSpoken=emp_data['language_spoken'],
                            CertificateExpiryDate=emp_data['certificate_expiry_date'],
                            EarliestStart=emp_data['earliest_start'],
                            LatestEnd=emp_data['latest_end'],
                            Shifts=emp_data['shifts'],
                            ContactNumber=emp_data['contact_number'],
                            Notes=emp_data.get('notes', ''),
                            SourceFilename=emp_data.get('source_filename'),
                            SourceUploadedAt=emp_data.get('source_uploaded_at'),
                            UploadID=emp_data.get('upload_id')
                        )
                        self.employees.append(employee)
                    except Exception as e:
                        logger.warning(f"Error loading employee {emp_data.get('employee_id', 'unknown')}: {str(e)}")
                
                # Load patients from database
                db_patients = self.db_manager.get_patients()
                self.patients = []
                for pat_data in db_patients:
                    try:
                        patient = Patient(
                            PatientID=pat_data['patient_id'],
                            PatientName=pat_data['patient_name'],
                            Address=pat_data['address'],
                            PostCode=pat_data['postcode'],
                            Gender=GenderEnum(pat_data['gender']),
                            Ethnicity=pat_data['ethnicity'],
                            Religion=pat_data['religion'],
                            RequiredSupport=pat_data['required_support'],
                            RequiredHoursOfSupport=pat_data['required_hours_of_support'],
                            AdditionalRequirements=pat_data['additional_requirements'],
                            Illness=pat_data['illness'],
                            ContactNumber=pat_data['contact_number'],
                            RequiresMedication=pat_data['requires_medication'],
                            EmergencyContact=pat_data['emergency_contact'],
                            EmergencyRelation=pat_data['emergency_relation'],
                            LanguagePreference=pat_data['language_preference'],
                            Notes=pat_data.get('notes', ''),
                            SourceFilename=pat_data.get('source_filename'),
                            SourceUploadedAt=pat_data.get('source_uploaded_at'),
                            UploadID=pat_data.get('upload_id')
                        )
                        self.patients.append(patient)
                    except Exception as e:
                        logger.warning(f"Error loading patient {pat_data.get('patient_id', 'unknown')}: {str(e)}")
                
                self.data_loaded = True
                logger.info(f"Loaded {len(self.employees)} employees and {len(self.patients)} patients from database")
            else:
                logger.info("No existing data found in database")
        except Exception as e:
            logger.error(f"Error loading data from database: {str(e)}")
    
    async def process_excel_file(self, file_path: str) -> Dict:
        """Process Excel file containing employee and patient data

        - Accepts flexible sheet names (EmployeeDetails/Employee, PatientDetails/Patients)
        - Normalizes columns to internal schema
        - Saves raw upload (all sheets) for history/inspection
        - Attaches source metadata to stored rows
        """
        try:
            logger.info(f"Processing Excel file: {file_path}")
            logger.info(f"File exists: {Path(file_path).exists()}")
            
            # Read workbook
            xls = pd.ExcelFile(file_path)
            sheet_names = xls.sheet_names
            logger.info(f"Found sheets: {sheet_names}")

            # Save raw upload (all sheets -> list of dicts)
            raw_sheets: Dict[str, Any] = {}
            try:
                raw_dict = pd.read_excel(file_path, sheet_name=None)
                for sname, sdf in raw_dict.items():
                    # Convert to list of dicts, ensure JSON-safe by replacing NaN/Inf with None
                    temp = sdf.copy()
                    temp = temp.where(pd.notna(temp), None)
                    recs = temp.to_dict(orient='records')
                    # deep sanitize (handles float NaN/Inf leaked via dtype)
                    import math
                    def _san(v):
                        if isinstance(v, float):
                            if math.isnan(v) or math.isinf(v):
                                return None
                            return v
                        if isinstance(v, dict):
                            return {k: _san(x) for k, x in v.items()}
                        if isinstance(v, list):
                            return [_san(x) for x in v]
                        return v
                    recs = [_san(r) for r in recs]
                    raw_sheets[sname] = recs
            except Exception as e:
                logger.warning(f"Failed to capture raw sheets: {e}")

            filename = Path(file_path).name
            uploaded_at = datetime.now().isoformat()
            upload_id = self.db_manager.save_raw_upload(filename, raw_sheets) if raw_sheets else None
            logger.info(f"Saved raw upload id: {upload_id}")

            # Resolve sheet names (case-insensitive)
            emp_aliases = ['EmployeeDetails', 'Employee', 'Employees']
            pat_aliases = ['PatientDetails', 'Patients', 'Service Users', 'ServiceUsers']
            def _find_sheet(aliases: List[str]) -> Optional[str]:
                for alias in aliases:
                    for s in sheet_names:
                        if s.strip().lower() == alias.strip().lower():
                            return s
                return None

            emp_sheet = _find_sheet(emp_aliases)
            pat_sheet = _find_sheet(pat_aliases)

            if not emp_sheet and not pat_sheet:
                raise Exception("No recognizable sheets found. Expected EmployeeDetails/Employee and PatientDetails/Patients")

            employee_df = pd.read_excel(xls, emp_sheet) if emp_sheet else pd.DataFrame()
            patient_df = pd.read_excel(xls, pat_sheet) if pat_sheet else pd.DataFrame()

            # Normalize dataframes to internal schema
            employee_df = self._normalize_employees_df(employee_df, filename, uploaded_at, upload_id)
            patient_df = self._normalize_patients_df(patient_df, filename, uploaded_at, upload_id)
            
            logger.info(f"Employee data shape: {employee_df.shape}")
            logger.info(f"Patient data shape: {patient_df.shape}")
            
            # Process employees
            self.employees = self._process_employees(employee_df)
            
            # Process patients
            self.patients = self._process_patients(patient_df)
            
            # Store in database
            employees_dict = [emp.dict() for emp in self.employees]
            patients_dict = [pat.dict() for pat in self.patients]
            
            self.db_manager.store_employees(employees_dict)
            self.db_manager.store_patients(patients_dict)
            
            # Log the upload
            self.db_manager.log_data_upload(
                filename=filename,
                employees_count=len(self.employees),
                patients_count=len(self.patients)
            )
            
            self.data_loaded = True
            
            logger.info(f"Processed and stored {len(self.employees)} employees and {len(self.patients)} patients")
            
            return {
                "employees": employees_dict,
                "patients": patients_dict,
                "upload_id": upload_id,
                "sheets": sheet_names
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
                    Notes=self._safe_str(row.get('Notes', '')),
                    SourceFilename=self._safe_str(row.get('SourceFilename', '')) or None,
                    SourceUploadedAt=self._safe_str(row.get('SourceUploadedAt', '')) or None,
                    UploadID=self._safe_int(row.get('UploadID'))
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
                    Notes=self._safe_str(row.get('Notes', '')),
                    SourceFilename=self._safe_str(row.get('SourceFilename', '')) or None,
                    SourceUploadedAt=self._safe_str(row.get('SourceUploadedAt', '')) or None,
                    UploadID=self._safe_int(row.get('UploadID'))
                )
                patients.append(patient)
            except Exception as e:
                logger.warning(f"Skipping patient row: {str(e)}")
        return patients

    # --- Normalization helpers ---
    def _normalize_employees_df(self, df: pd.DataFrame, filename: str, uploaded_at: str, upload_id: Optional[int]) -> pd.DataFrame:
        if df is None or df.empty:
            # Ensure canonical columns exist
            cols = ['EmployeeID','Name','Address','PostCode','Gender','Ethnicity','Religion','TransportMode','Qualification','LanguageSpoken','CertificateExpiryDate','EarliestStart','LatestEnd','Shifts','ContactNumber','Notes']
            out = pd.DataFrame(columns=cols)
        else:
            out = df.copy()

        # Map alternative columns
        def col_in(*names):
            for n in names:
                for c in out.columns:
                    if c.strip().lower() == n.strip().lower():
                        return c
            return None

        # EmployeeID
        if 'EmployeeID' not in out.columns:
            uid_col = col_in('User Id','UserId','Employee Id','EmployeeID')
            if uid_col:
                out['EmployeeID'] = out[uid_col].astype(str)
            else:
                out['EmployeeID'] = ''

        # Name
        if 'Name' not in out.columns:
            first = col_in('First Name','FirstName')
            last = col_in('Last Name','LastName','Surname')
            if first or last:
                out['Name'] = ((out[first] if first else '').astype(str).fillna('') + ' ' + (out[last] if last else '').astype(str).fillna('')).str.strip()
            else:
                out['Name'] = ''

        # Address
        if 'Address' not in out.columns:
            parts = [col_in('First Line','Address1','Address Line 1'), col_in('Second Line','Address2','Address Line 2'), col_in('City','Town'), col_in('County','State'), col_in('Country')]
            addr_parts = [p for p in parts if p]
            if addr_parts:
                out['Address'] = out[addr_parts].astype(str).apply(lambda r: ', '.join([x for x in r if x and str(x).strip()!='' and str(x).strip().lower()!='nan']), axis=1)
            else:
                out['Address'] = ''

        # PostCode
        if 'PostCode' not in out.columns:
            pc = col_in('Postcode','Post Code','ZIP','Zip')
            out['PostCode'] = out[pc].astype(str) if pc else ''

        # Gender/Ethnicity/Religion
        for c in [('Gender',('Gender',)), ('Ethnicity',('Ethnicity',)), ('Religion',('Religion',))]:
            cname, aliases = c
            if cname not in out.columns:
                alt = col_in(*aliases)
                out[cname] = out[alt] if alt else ''

        # TransportMode
        if 'TransportMode' not in out.columns:
            tm = col_in('TransportMode','Transport','Mode')
            out['TransportMode'] = out[tm] if tm else 'Walking'

        # Qualification from Role
        if 'Qualification' not in out.columns:
            role = col_in('Qualification','Role')
            if role:
                def map_role(x: Any) -> str:
                    s = str(x).strip().lower() if x is not None else ''
                    if 'nurse' in s:
                        return 'Nurse'
                    if 'senior' in s:
                        return 'Senior Carer'
                    if 'carer' in s:
                        return 'Carer'
                    return 'Carer'
                out['Qualification'] = out[role].apply(map_role)
            else:
                out['Qualification'] = 'Carer'

        # LanguageSpoken
        if 'LanguageSpoken' not in out.columns:
            ls = col_in('LanguageSpoken','Languages')
            out['LanguageSpoken'] = out[ls] if ls else ''
        out['LanguageSpoken'] = out['LanguageSpoken'].astype(str).str.replace('/', ', ')

        # CertificateExpiryDate, EarliestStart, LatestEnd, Shifts, ContactNumber, Notes
        for cname, aliases in [
            ('CertificateExpiryDate', ('CertificateExpiryDate','Certificate Expiry','Certificate Expiry Date')),
            ('EarliestStart', ('EarliestStart','Earliest Start')),
            ('LatestEnd', ('LatestEnd','Latest End')),
            ('Shifts', ('Shifts',)),
            ('ContactNumber', ('ContactNumber','Phone','Phone Number','Contact')),
            ('Notes', ('Notes','Remarks'))
        ]:
            if cname not in out.columns:
                alt = col_in(*aliases)
                out[cname] = out[alt] if alt else ''

        # Clean shifts
        out['Shifts'] = out['Shifts'].astype(str).str.replace('/', ', ')

        # Filter active employees if Status present
        status_col = col_in('Status')
        if status_col:
            try:
                out = out[out[status_col].astype(str).str.lower().str.contains('active')]
            except Exception:
                pass

        # Attach source metadata
        out['SourceFilename'] = filename
        out['SourceUploadedAt'] = uploaded_at
        out['UploadID'] = upload_id

        # Ensure canonical order
        canon = ['EmployeeID','Name','Address','PostCode','Gender','Ethnicity','Religion','TransportMode','Qualification','LanguageSpoken','CertificateExpiryDate','EarliestStart','LatestEnd','Shifts','ContactNumber','Notes','SourceFilename','SourceUploadedAt','UploadID']
        for c in canon:
            if c not in out.columns:
                out[c] = ''
        return out[canon].copy()

    def _normalize_patients_df(self, df: pd.DataFrame, filename: str, uploaded_at: str, upload_id: Optional[int]) -> pd.DataFrame:
        if df is None or df.empty:
            cols = ['PatientID','PatientName','Address','PostCode','Gender','Ethnicity','Religion','RequiredSupport','RequiredHoursOfSupport','AdditionalRequirements','Illness','ContactNumber','RequiresMedication','EmergencyContact','EmergencyRelation','LanguagePreference','Notes']
            out = pd.DataFrame(columns=cols)
        else:
            out = df.copy()

        def col_in(*names):
            for n in names:
                for c in out.columns:
                    if c.strip().lower() == n.strip().lower():
                        return c
            return None

        # PatientID
        if 'PatientID' not in out.columns:
            pid = col_in('Tenant Service User Id','User Id','UserId','PatientID')
            out['PatientID'] = out[pid].astype(str) if pid else ''

        # PatientName
        if 'PatientName' not in out.columns:
            first = col_in('First Name','FirstName')
            last = col_in('Last Name','LastName','Surname')
            usern = col_in('Username')
            if first or last:
                out['PatientName'] = ((out[first] if first else '').astype(str).fillna('') + ' ' + (out[last] if last else '').astype(str).fillna('')).str.strip()
            elif usern:
                out['PatientName'] = out[usern].astype(str)
            else:
                out['PatientName'] = ''

        # Address
        if 'Address' not in out.columns:
            parts = [col_in('First Line','Address1','Address Line 1'), col_in('Second Line','Address2','Address Line 2'), col_in('City','Town'), col_in('County','State'), col_in('Country')]
            addr_parts = [p for p in parts if p]
            if addr_parts:
                out['Address'] = out[addr_parts].astype(str).apply(lambda r: ', '.join([x for x in r if x and str(x).strip()!='' and str(x).strip().lower()!='nan']), axis=1)
            else:
                out['Address'] = ''

        # PostCode
        if 'PostCode' not in out.columns:
            pc = col_in('Postcode','Post Code','ZIP','Zip')
            out['PostCode'] = out[pc].astype(str) if pc else ''

        # Gender/Ethnicity/Religion (often absent)
        for c in [('Gender',('Gender',)), ('Ethnicity',('Ethnicity',)), ('Religion',('Religion',))]:
            cname, aliases = c
            if cname not in out.columns:
                alt = col_in(*aliases)
                out[cname] = out[alt] if alt else ''

        # RequiredSupport from Visit Type
        if 'RequiredSupport' not in out.columns:
            vt = col_in('Visit Type','VisitType')
            def map_visit(val: Any) -> str:
                if val is None:
                    return ''
                s = str(val)
                # Split by comma or '/'
                tokens = []
                for part in s.replace('/', ',').split(','):
                    t = part.strip().lower()
                    if not t:
                        continue
                    if 'medic' in t:
                        tokens.append('medicine')
                    elif 'exerc' in t:
                        tokens.append('exercise')
                    elif 'shop' in t or 'compan' in t:
                        tokens.append('companionship')
                    elif 'meal' in t or 'laundry' in t or 'personal' in t or 'care' in t:
                        tokens.append('personal care')
                return ', '.join(dict.fromkeys(tokens))
            out['RequiredSupport'] = out[vt].apply(map_visit) if vt else ''

        # RequiredHoursOfSupport
        if 'RequiredHoursOfSupport' not in out.columns:
            rhs = col_in('RequiredHoursOfSupport','Hours','Hours Needed')
            out['RequiredHoursOfSupport'] = out[rhs] if rhs else 0

        # AdditionalRequirements, Illness, ContactNumber, RequiresMedication, EmergencyContact, EmergencyRelation, LanguagePreference, Notes
        for cname, aliases in [
            ('AdditionalRequirements', ('AdditionalRequirements','Additional Requirements')),
            ('Illness', ('Illness','Medical Conditions')),
            ('ContactNumber', ('ContactNumber','Phone','Phone Number','Contact')),
            ('RequiresMedication', ('RequiresMedication','Medication Needed')),
            ('EmergencyContact', ('EmergencyContact','Emergency Contact')),
            ('EmergencyRelation', ('EmergencyRelation','Emergency Relation')),
            ('LanguagePreference', ('LanguagePreference','Preferred Language')),
            ('Notes', ('Notes','Remarks'))
        ]:
            if cname not in out.columns:
                alt = col_in(*aliases)
                out[cname] = out[alt] if alt else ''

        # Normalize language pref separators
        out['LanguagePreference'] = out['LanguagePreference'].astype(str).str.replace('/', ', ')

        # Normalize RequiresMedication to Y/N if common Yes/No present
        try:
            out['RequiresMedication'] = out['RequiresMedication'].apply(lambda x: 'Y' if str(x).strip().lower() in ['y','yes','true'] else ('N' if str(x).strip().lower() in ['n','no','false'] else str(x)))
        except Exception:
            pass

        # Attach source metadata
        out['SourceFilename'] = filename
        out['SourceUploadedAt'] = uploaded_at
        out['UploadID'] = upload_id

        canon = ['PatientID','PatientName','Address','PostCode','Gender','Ethnicity','Religion','RequiredSupport','RequiredHoursOfSupport','AdditionalRequirements','Illness','ContactNumber','RequiresMedication','EmergencyContact','EmergencyRelation','LanguagePreference','Notes','SourceFilename','SourceUploadedAt','UploadID']
        for c in canon:
            if c not in out.columns:
                out[c] = ''
        return out[canon].copy()
    
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

    # --- Derived helpers for scheduling ---
    def get_patient_services(self, patient: Patient) -> List[ServiceType]:
        """Parse patient's RequiredSupport string into a list of ServiceType."""
        return self._parse_services(patient.RequiredSupport)

    def get_default_service_duration(self, service_type: ServiceType) -> int:
        """Default minutes per service when not otherwise specified."""
        defaults = {
            ServiceType.MEDICINE: 30,
            ServiceType.PERSONAL_CARE: 45,
            ServiceType.EXERCISE: 30,
            ServiceType.COMPANIONSHIP: 60,
        }
        return defaults.get(service_type, 30)

    def derive_patient_daily_demand(self, patient: Patient) -> int:
        """Estimate daily minutes of support required for a patient.

        - If weekly hours provided: distribute evenly across 7 days
        - Else: sum of default durations for listed services (at least 60)
        """
        weekly_hours = patient.RequiredHoursOfSupport
        if isinstance(weekly_hours, int) and weekly_hours and weekly_hours > 0:
            return max(15, int((weekly_hours * 60) / 7))

        services = self.get_patient_services(patient)
        if services:
            total = sum(self.get_default_service_duration(s) for s in services)
            return max(60, total)
        return 60