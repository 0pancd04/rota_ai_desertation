import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchWeekAssignments(weekStart, weekEnd) {
  const res = await axios.post(`${API_BASE_URL}/assignments/week`, {
    week_start: weekStart,
    week_end: weekEnd,
  });
  return res.data;
}

export async function fetchEmployeesWeeklySummary(weekStart, weekEnd) {
  const res = await axios.post(`${API_BASE_URL}/employees/weekly-summary`, {
    week_start: weekStart,
    week_end: weekEnd,
  });
  return res.data;
}

export async function fetchEmployeeDetails(employeeId) {
  const res = await axios.get(`${API_BASE_URL}/employees/details/${encodeURIComponent(employeeId)}`);
  return res.data;
}

export async function fetchPatientDetails(patientId) {
  const res = await axios.get(`${API_BASE_URL}/patients/details/${encodeURIComponent(patientId)}`);
  return res.data;
}

