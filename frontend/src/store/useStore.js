import { create } from 'zustand';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const useStore = create((set, get) => ({
  // State
  employees: [],
  patients: [],
  assignments: [],
  loading: false,
  error: null,
  uploadStatus: null,

  // Actions
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),

  // Upload data file
  uploadDataFile: async (file) => {
    set({ loading: true, error: null });
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${API_BASE_URL}/upload-data`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      set({ 
        uploadStatus: response.data,
        loading: false 
      });
      
      // Refresh data after upload
      await get().fetchEmployees();
      await get().fetchPatients();
      
      return response.data;
    } catch (error) {
      set({ 
        error: error.response?.data?.detail || 'Failed to upload file',
        loading: false 
      });
      throw error;
    }
  },

  // Fetch employees
  fetchEmployees: async () => {
    set({ loading: true, error: null });
    try {
      const response = await axios.get(`${API_BASE_URL}/employees`);
      set({ 
        employees: response.data.employees || [],
        loading: false 
      });
    } catch (error) {
      set({ 
        error: error.response?.data?.detail || 'Failed to fetch employees',
        loading: false 
      });
    }
  },

  // Fetch patients
  fetchPatients: async () => {
    set({ loading: true, error: null });
    try {
      const response = await axios.get(`${API_BASE_URL}/patients`);
      set({ 
        patients: response.data.patients || [],
        loading: false 
      });
    } catch (error) {
      set({ 
        error: error.response?.data?.detail || 'Failed to fetch patients',
        loading: false 
      });
    }
  },

  // Fetch assignments
  fetchAssignments: async () => {
    set({ loading: true, error: null });
    try {
      const response = await axios.get(`${API_BASE_URL}/assignments`);
      set({ 
        assignments: response.data.assignments || [],
        loading: false 
      });
    } catch (error) {
      set({ 
        error: error.response?.data?.detail || 'Failed to fetch assignments',
        loading: false 
      });
    }
  },

  // Create assignment
  createAssignment: async (prompt) => {
    set({ loading: true, error: null });
    try {
      const response = await axios.post(`${API_BASE_URL}/assign-employee`, {
        prompt
      });
      
      if (response.data.success) {
        // Add new assignment to state
        set(state => ({
          assignments: [...state.assignments, response.data.assignment],
          loading: false
        }));
        return response.data;
      } else {
        throw new Error(response.data.message);
      }
    } catch (error) {
      set({ 
        error: error.response?.data?.detail || error.message || 'Failed to create assignment',
        loading: false 
      });
      throw error;
    }
  },

  // Generate weekly rota
  generateWeeklyRota: async () => {
    set({ loading: true, error: null });
    try {
      const response = await axios.post(`${API_BASE_URL}/generate-weekly-rota`);
      
      if (response.data.success) {
        set({ 
          assignments: response.data.assignments || [],
          loading: false 
        });
        return response.data;
      } else {
        throw new Error('Failed to generate weekly rota');
      }
    } catch (error) {
      set({ 
        error: error.response?.data?.detail || 'Failed to generate weekly rota',
        loading: false 
      });
      throw error;
    }
  },

  // Clear error
  clearError: () => set({ error: null })
}));

export default useStore;
