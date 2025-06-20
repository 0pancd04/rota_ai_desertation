# AI Rota System Setup Guide

## Prerequisites

1. **Python 3.9 or higher** - [Download from python.org](https://www.python.org/downloads/)
2. **OpenAI API Key** - [Get from OpenAI](https://platform.openai.com/api-keys)

## Quick Start (Recommended)

### Option 1: Using the Setup Script

1. **Download/Clone the project**
2. **Run the setup script**:
   ```bash
   python setup_and_run.py setup
   ```
3. **Add your OpenAI API key** to the `.env` file that was created
4. **Start the server**:
   ```bash
   python setup_and_run.py start
   ```

### Option 2: Manual Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

3. **Create sample data**:
   ```bash
   python sample_data.py
   ```

4. **Start the server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Using UV Package Manager (Alternative)

If you prefer to use UV (faster Python package manager):

1. **Install UV**:
   ```bash
   pip install uv
   ```

2. **Use the provided scripts**:
   - **Linux/Mac**: `./start.sh`
   - **Windows**: `start.bat`

### For Windows Users with UV

If you're using Windows and have UV installed, you can activate the virtual environment and run commands:

```bash
# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
uv sync

# Run the application
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Verification

After setup, you should be able to:

1. **Visit the API documentation**: http://localhost:8000/docs
2. **Check the health endpoint**: http://localhost:8000/health
3. **Run tests**: `python setup_and_run.py test`

## Project Structure

```
rota_ai_desertation/
├── app/                          # Main application
│   ├── main.py                   # FastAPI app
│   ├── models/schemas.py         # Data models
│   └── services/                 # Business logic
│       ├── data_processor.py     # Excel processing
│       ├── openai_service.py     # AI integration
│       └── rota_service.py       # Assignment logic
├── input_files/                  # Excel upload directory
├── sample_data.py               # Sample data generator
├── test_assignment.py           # Test suite
├── setup_and_run.py            # Setup and run script
├── requirements.txt             # Python dependencies
├── .env                         # Configuration (create this)
└── README.md                    # Documentation
```

## API Usage Examples

### 1. Upload Employee/Patient Data

**Note:** A sample Excel file is already provided at `input_files/Final_Employee_Patient_Data.xlsx`

```bash
curl -X POST "http://localhost:8000/upload-data" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@input_files/Final_Employee_Patient_Data.xlsx"
```

### 2. Make Assignment Request

```bash
curl -X POST "http://localhost:8000/assign-employee" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Patient P001 needs medicine today, assign available employee"
     }'
```

### 3. View Current Assignments

```bash
curl -X GET "http://localhost:8000/assignments"
```

## Excel File Format

Your Excel file should have two sheets:

### Sheet 1: "EmployeeDetails"
| Column | Required | Example |
|--------|----------|--------|
| EmployeeID | Yes | E001 |
| Name | Yes | Sarah Johnson |
| Address | Yes | 123 Main St, London |
| VehicleAvailable | No | Yes |
| Qualification | No | Registered Nurse |
| LanguageSpoken | No | English, Spanish |
| CertificateExpiryDate | No | 2025-12-31 |
| EarliestStart | No | 08:00 |
| LatestEnd | No | 18:00 |
| Availability | No | Mon-Fri |
| ContactNumber | No | 1234567890 |
| Notes | No | Allergic to latex |

### Sheet 2: "PatientDetails"
| Column | Required | Example |
|--------|----------|--------|
| PatientID | Yes | P001 |
| PatientName | Yes | John Smith |
| Address | Yes | 456 Oak St, London |
| RequiredSupport | No | Personal care, Medication |
| RequiredHoursOfSupport | No | 4 |
| AdditionalRequirements | No | Wheelchair access |
| Illness | No | Diabetes, Hypertension |
| ContactNumber | No | 9876543210 |
| RequiresMedication | No | Yes |
| EmergencyContact | No | Sarah Smith |
| EmergencyRelation | No | Daughter |
| Notes | No | Check blood pressure daily |

## Rules Implemented

1. **Medicine → Nurses Only**: Only qualified nurses can administer medicine (not care workers)
2. **Location Proximity**: System considers travel time based on employee and patient locations
3. **Language Preference**: Matches employees who speak the patient's preferred language
4. **Workload Balance**: Prevents overloading employees beyond their daily capacity

## Troubleshooting

### Common Issues

1. **"Python not found"**
   - Install Python from python.org
   - Make sure Python is added to your system PATH

2. **"OpenAI API key not set"**
   - Create a `.env` file with your API key
   - Get an API key from https://platform.openai.com/api-keys

3. **"Port 8000 already in use"**
   - Change the port in the startup command: `--port 8001`
   - Or kill the process using port 8000

4. **"Module not found"**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`

5. **Excel file errors**
   - Ensure your Excel file has sheets named "EmployeeDetails" and "PatientDetails"
   - Check that required columns are present

### Getting Help

1. **Check the logs** - The server prints detailed error messages
2. **Use the test suite** - Run `python setup_and_run.py test`
3. **Verify sample data** - Use the provided sample Excel file first
4. **API Documentation** - Visit http://localhost:8000/docs when the server is running

## Development Mode

For development, you can:

1. **Enable auto-reload**: The server automatically reloads when you change code
2. **View detailed logs**: Set `DEBUG=True` in `.env`
3. **Test without OpenAI**: The system has fallback logic for testing

## Production Deployment

For production use:

1. Set `DEBUG=False` in `.env`
2. Use a production WSGI server
3. Set up proper authentication
4. Configure HTTPS
5. Set up database for persistent storage (currently uses in-memory storage) 