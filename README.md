# AI Rota System for Healthcare

An AI-powered system for assigning healthcare employees to patients based on various rules and constraints.

## Features

- **Rule-based Assignment**: Implements healthcare-specific rules for employee-patient assignments
- **AI-Powered Decision Making**: Uses OpenAI to make intelligent assignment decisions
- **Excel Data Processing**: Processes employee and patient data from Excel files
- **RESTful API**: FastAPI-based API for easy integration
- **Real-time Assignment**: Natural language prompts for assignment requests

## Rules Implemented

1. **Qualified Personnel**: For medicine administration, only nurses (not care workers) can be assigned
2. **Location-based Assignment**: Considers proximity and vehicle availability for travel time optimization
3. **Language Preference**: Matches employees who speak the patient's preferred language when possible
4. **Travel Time Calculation**: Calculates optimal routes based on location and vehicle type

## Prerequisites

- Python 3.9+
- uv package manager
- OpenAI API key

## Installation

1. **Install uv package manager** (if not already installed):
   ```bash
   pip install uv
   ```

2. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd rota_ai_desertation
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env file and add your OpenAI API key
   ```

4. **Make scripts executable** (Linux/Mac):
   ```bash
   chmod +x start.sh stop.sh
   ```

## Running the Application

### On Linux/Mac:
```bash
./start.sh
```

### On Windows:
```bash
start.bat
```

The API will be available at `http://localhost:8000`

### Stopping the Application

### On Linux/Mac:
```bash
./stop.sh
```

### On Windows:
```bash
stop.bat
```

## API Documentation

Once the application is running, visit:
- API Documentation: `http://localhost:8000/docs`
- Alternative Documentation: `http://localhost:8000/redoc`

## Usage

### 1. Upload Employee and Patient Data

First, upload an Excel file with two sheets:
- `EmployeeDetails`: Contains employee information
- `PatientDetails`: Contains patient information

**Note:** A sample Excel file is provided at `input_files/Final_Employee_Patient_Data.xlsx` with the correct format.

```bash
curl -X POST "http://localhost:8000/upload-data" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@input_files/Final_Employee_Patient_Data.xlsx"
```

### 2. Make Assignment Requests

Use natural language to request employee assignments:

```bash
curl -X POST "http://localhost:8000/assign-employee" \
     -H "accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Patient P001 needs exercise support today. Can you assign an available employee?"
     }'
```

#### Sample Request Bodies:

**Basic Assignment:**
```json
{
  "prompt": "Patient P001 needs exercise support today. Can you assign an available employee?"
}
```

**Medication Request (Requires Nurse):**
```json
{
  "prompt": "Patient P003 requires medication administration at 10:00 AM. Please assign a qualified nurse."
}
```

**Language-Specific Request:**
```json
{
  "prompt": "Patient P002 prefers Spanish-speaking care worker for personal care assistance this afternoon."
}
```

**Complex Request with Context:**
```json
{
  "prompt": "Patient P005 with diabetes needs medication support and has mobility issues. Assign experienced nurse with vehicle access.",
  "context": {
    "priority": "high",
    "medical_condition": "diabetes",
    "special_requirements": ["vehicle_needed", "experienced_staff"]
  }
}
```

### 3. View Assignments

```bash
curl -X GET "http://localhost:8000/assignments"
```

### 4. View Employees and Patients

```bash
# Get all employees
curl -X GET "http://localhost:8000/employees"

# Get all patients
curl -X GET "http://localhost:8000/patients"
```

## Excel File Format

### EmployeeDetails Sheet

| Column | Description | Example |
|--------|-------------|---------|
| EmployeeID | Unique identifier | E001 |
| Name | Employee name | John Smith |
| Address | Employee address | 123 Main St, London |
| VehicleAvailable | Vehicle availability | Yes |
| Qualification | Job qualification | Registered Nurse |
| LanguageSpoken | Spoken languages | English, Spanish |
| CertificateExpiryDate | Certificate expiry | 2025-12-31 |
| EarliestStart | Earliest start time | 08:00 |
| LatestEnd | Latest end time | 18:00 |
| Availability | General availability | Mon-Fri |
| ContactNumber | Phone number | 1234567890 |
| Notes | Additional notes | Allergic to latex |

### PatientDetails Sheet

| Column | Description | Example |
|--------|-------------|---------|
| PatientID | Unique identifier | P001 |
| PatientName | Patient name | Jane Doe |
| Address | Patient address | 456 Oak St, London |
| RequiredSupport | Support services needed | Personal care, Medication |
| RequiredHoursOfSupport | Hours needed per day | 4 |
| AdditionalRequirements | Special requirements | Wheelchair access |
| Illness | Medical conditions | Diabetes, Hypertension |
| ContactNumber | Phone number | 9876543210 |
| RequiresMedication | Medication needs | Yes |
| EmergencyContact | Emergency contact name | Sarah Doe |
| EmergencyRelation | Relation to patient | Daughter |
| Notes | Additional notes | Check blood pressure daily |

## Development

### Project Structure

```
app/
├── __init__.py
├── main.py                 # FastAPI application
├── models/
│   ├── __init__.py
│   └── schemas.py          # Pydantic models
└── services/
    ├── __init__.py
    ├── data_processor.py    # Excel processing
    ├── openai_service.py    # AI integration
    └── rota_service.py      # Main business logic
```

### Adding New Rules

To add new assignment rules, modify the `validate_assignment_rules` method in `app/services/rota_service.py`.

### Customizing AI Behavior

Modify the prompts in `app/services/openai_service.py` to change how the AI makes decisions.

## Troubleshooting

1. **OpenAI API Key Error**: Ensure your OpenAI API key is correctly set in `.env`
2. **Excel File Error**: Check that your Excel file has the correct sheet names and column headers
3. **Port Already in Use**: Change the port in the start scripts if 8000 is occupied

## License

This project is part of a dissertation on AI-based healthcare rota systems. 
