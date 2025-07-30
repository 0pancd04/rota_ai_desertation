import requests
import os

def test_upload():
    url = "http://localhost:8000/upload-data"
    
    # Check if file exists
    file_path = "input_files/Updated_Healthcare_Rota_System_Data.xlsx"
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    # Upload the file
    with open(file_path, 'rb') as f:
        files = {'file': ('Updated_Healthcare_Rota_System_Data.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post(url, files=files)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test getting employees and patients
    if response.status_code == 200:
        print("\n--- Testing Employee Endpoint ---")
        emp_response = requests.get("http://localhost:8000/employees")
        print(f"Employees Status: {emp_response.status_code}")
        print(f"Employees Count: {len(emp_response.json().get('employees', []))}")
        
        print("\n--- Testing Patient Endpoint ---")
        pat_response = requests.get("http://localhost:8000/patients")
        print(f"Patients Status: {pat_response.status_code}")
        print(f"Patients Count: {len(pat_response.json().get('patients', []))}")

if __name__ == "__main__":
    test_upload() 