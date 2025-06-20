# AI Rota System - API Usage Guide

This guide shows you how to use all the API endpoints in the correct sequence with sample requests and responses.

## 🚀 Prerequisites

1. **Server is running** on http://localhost:8000
2. **OpenAI API key** is set in `.env` file (optional for basic testing)
3. **Excel file** with employee and patient data is ready

## 📋 Step-by-Step API Usage

### Step 1: Check Server Health

**Endpoint:** `GET /health`

**Request:**
```bash
curl -X GET "http://localhost:8000/health"
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "ai-rota-system"
}
```

### Step 2: Create Sample Data (If Needed)

**Command:**
```bash
python sample_data.py
```

### Step 3: Upload Employee and Patient Data

**Endpoint:** `POST /upload-data`

**Request:**
```bash
curl -X POST "http://localhost:8000/upload-data" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@input_files/Sample_Employee_Patient_Data.xlsx"
```

**Expected Response:**
```json
{
  "message": "File uploaded and processed successfully",
  "filename": "Sample_Employee_Patient_Data.xlsx",
  "employees_count": 5,
  "patients_count": 5
}
```

### Step 4: View Uploaded Data (Optional)

**View Employees:**
```bash
curl -X GET "http://localhost:8000/employees"
```

**View Patients:**
```bash
curl -X GET "http://localhost:8000/patients"
```

### Step 5: Make Assignment Requests

**Endpoint:** `POST /assign-employee`

#### Example 1: Medicine Assignment (Tests Rule 1)

**Request:**
```bash
curl -X POST "http://localhost:8000/assign-employee" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Patient P001 needs medicine today, assign available employee"
     }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Employee assigned successfully",
  "assignment": {
    "employee_id": "E001",
    "employee_name": "Sarah Johnson",
    "patient_id": "P001",
    "patient_name": "John Smith",
    "service_type": "medicine",
    "assigned_time": "10:30",
    "estimated_duration": 30,
    "travel_time": 15,
    "start_time": "10:30",
    "end_time": "11:00",
    "priority_score": 8.5,
    "assignment_reason": "Selected nurse qualified for medicine"
  }
}
```

#### Example 2: Exercise Assignment

**Request:**
```bash
curl -X POST "http://localhost:8000/assign-employee" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Patient P004 needs exercise therapy this afternoon"
     }'
```

#### Example 3: Language-Specific Assignment

**Request:**
```bash
curl -X POST "http://localhost:8000/assign-employee" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Patient P002 who speaks Spanish needs companionship"
     }'
```

### Step 6: View All Assignments

**Endpoint:** `GET /assignments`

**Request:**
```bash
curl -X GET "http://localhost:8000/assignments"
```

## 🔧 Environment Setup

Create `.env` file from template:

```bash
copy env.template .env
```

Edit `.env` and add your OpenAI API key:
```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

## 🌐 Interactive Testing

Visit http://localhost:8000/docs for interactive API documentation.

## 💡 Rule Testing

The system implements Rule 1: Only nurses can administer medicine.
Test this by requesting medicine assignments and verifying only nurses are selected. 
