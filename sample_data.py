 #!/usr/bin/env python3
"""
Sample data generator for testing the AI Rota System
This creates sample employee and patient data for testing purposes
"""

import pandas as pd
from pathlib import Path
import os

def create_sample_excel_file():
    """Create a sample Excel file with employee and patient data"""
    
    # Sample Employee Data
    employees_data = [
        {
            'Employee_ID': 'E001',
            'Name': 'Sarah Johnson',
            'Role': 'Nurse',
            'Location': 'Central London',
            'Languages': 'English, Spanish',
            'Availability_Start': '09:00',
            'Availability_End': '17:00',
            'Vehicle': 'Car',
            'Max_Patients_Per_Day': 8,
            'Specializations': 'Diabetes care, Wound care'
        },
        {
            'Employee_ID': 'E002',
            'Name': 'Michael Brown',
            'Role': 'Care Worker',
            'Location': 'West London',
            'Languages': 'English',
            'Availability_Start': '08:00',
            'Availability_End': '16:00',
            'Vehicle': 'Bike',
            'Max_Patients_Per_Day': 6,
            'Specializations': 'Exercise therapy, Companionship'
        },
        {
            'Employee_ID': 'E003',
            'Name': 'Emma Wilson',
            'Role': 'Nurse',
            'Location': 'East London',
            'Languages': 'English, French',
            'Availability_Start': '10:00',
            'Availability_End': '18:00',
            'Vehicle': 'Car',
            'Max_Patients_Per_Day': 7,
            'Specializations': 'Medication management, Blood pressure monitoring'
        },
        {
            'Employee_ID': 'E004',
            'Name': 'James Davis',
            'Role': 'Care Worker',
            'Location': 'South London',
            'Languages': 'English, Hindi',
            'Availability_Start': '07:00',
            'Availability_End': '15:00',
            'Vehicle': 'None',
            'Max_Patients_Per_Day': 5,
            'Specializations': 'Personal care, Mobility assistance'
        },
        {
            'Employee_ID': 'E005',
            'Name': 'Lisa Garcia',
            'Role': 'Nurse',
            'Location': 'North London',
            'Languages': 'English, Spanish, Portuguese',
            'Availability_Start': '12:00',
            'Availability_End': '20:00',
            'Vehicle': 'Car',
            'Max_Patients_Per_Day': 8,
            'Specializations': 'Mental health, Medication administration'
        }
    ]
    
    # Sample Patient Data
    patients_data = [
        {
            'Patient_ID': 'P001',
            'Name': 'John Smith',
            'Location': 'Central London',
            'Preferred_Language': 'English',
            'Medical_Conditions': 'Diabetes, Hypertension',
            'Required_Services': 'Medicine, Exercise',
            'Service_Times': 'medicine:10:00,exercise:14:00',
            'Priority_Level': 3
        },
        {
            'Patient_ID': 'P002',
            'Name': 'Maria Rodriguez',
            'Location': 'West London',
            'Preferred_Language': 'Spanish',
            'Medical_Conditions': 'Arthritis, Depression',
            'Required_Services': 'Medicine, Companionship',
            'Service_Times': 'medicine:09:00,companionship:15:00',
            'Priority_Level': 4
        },
        {
            'Patient_ID': 'P003',
            'Name': 'Robert Taylor',
            'Location': 'East London',
            'Preferred_Language': 'English',
            'Medical_Conditions': 'Heart disease, Mobility issues',
            'Required_Services': 'Medicine, Personal care',
            'Service_Times': 'medicine:11:00,personal_care:16:00',
            'Priority_Level': 5
        },
        {
            'Patient_ID': 'P004',
            'Name': 'Priya Patel',
            'Location': 'South London',
            'Preferred_Language': 'Hindi',
            'Medical_Conditions': 'Chronic pain, Anxiety',
            'Required_Services': 'Exercise, Companionship',
            'Service_Times': 'exercise:13:00,companionship:17:00',
            'Priority_Level': 2
        },
        {
            'Patient_ID': 'P005',
            'Name': 'Jean Dubois',
            'Location': 'North London',
            'Preferred_Language': 'French',
            'Medical_Conditions': 'Alzheimer, High blood pressure',
            'Required_Services': 'Medicine, Personal care',
            'Service_Times': 'medicine:12:00,personal_care:18:00',
            'Priority_Level': 5
        }
    ]
    
    # Create DataFrames
    employees_df = pd.DataFrame(employees_data)
    patients_df = pd.DataFrame(patients_data)
    
    # Ensure input_files directory exists
    input_dir = Path('input_files')
    input_dir.mkdir(exist_ok=True)
    
    # Create Excel file with both sheets
    excel_file_path = input_dir / 'Sample_Employee_Patient_Data.xlsx'
    
    with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
        employees_df.to_excel(writer, sheet_name='EmployeeDetails', index=False)
        patients_df.to_excel(writer, sheet_name='PatientDetails', index=False)
    
    print(f"Sample Excel file created: {excel_file_path}")
    print(f"Employees: {len(employees_data)}")
    print(f"Patients: {len(patients_data)}")
    
    return excel_file_path

def display_sample_data():
    """Display the sample data structure"""
    print("\n=== SAMPLE EMPLOYEE DATA ===")
    print("Columns: Employee_ID, Name, Role, Location, Languages, Availability_Start, Availability_End, Vehicle, Max_Patients_Per_Day, Specializations")
    print("\nExample Employee:")
    print("E001 | Sarah Johnson | Nurse | Central London | English, Spanish | 09:00-17:00 | Car | 8 patients/day")
    
    print("\n=== SAMPLE PATIENT DATA ===")
    print("Columns: Patient_ID, Name, Location, Preferred_Language, Medical_Conditions, Required_Services, Service_Times, Priority_Level")
    print("\nExample Patient:")
    print("P001 | John Smith | Central London | English | Diabetes, Hypertension | Medicine, Exercise | medicine:10:00,exercise:14:00 | Priority: 3")
    
    print("\n=== ASSIGNMENT RULES ===")
    print("1. Medicine services → Only NURSES qualified (not care workers)")
    print("2. Location proximity → Shorter travel time preferred")
    print("3. Language preference → Match employee language with patient preference")
    print("4. Workload balance → Avoid overloading employees")

if __name__ == "__main__":
    print("AI Rota System - Sample Data Generator")
    print("=====================================")
    
    # Create sample Excel file
    excel_path = create_sample_excel_file()
    
    # Display data structure
    display_sample_data()
    
    print(f"\nSample file created at: {excel_path}")
    print("\nYou can now:")
    print("1. Start the API server: ./start.sh (Linux/Mac) or start.bat (Windows)")
    print("2. Upload this sample file via the API")
    print("3. Test assignment requests like: 'Patient P001 needs medicine, assign available employee'")