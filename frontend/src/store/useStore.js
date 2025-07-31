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
  activeTasks: [],
  notifications: [],
  unreadNotificationsCount: 0,

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

  // Create assignment with progress tracking
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

  // Generate weekly rota with progress tracking
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

  // Update active tasks
  updateActiveTasks: (tasks) => set({ activeTasks: tasks }),

  // Notification methods
  fetchNotifications: async (includeDeleted = false, limit = 50) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/notifications`, {
        params: { include_deleted: includeDeleted, limit }
      });
      set({ notifications: response.data.notifications || [] });
      return response.data.notifications;
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
      return [];
    }
  },

  fetchUnreadNotificationsCount: async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/notifications/unread-count`);
      set({ unreadNotificationsCount: response.data.unread_count || 0 });
      return response.data.unread_count;
    } catch (error) {
      console.error('Failed to fetch unread count:', error);
      return 0;
    }
  },

  markNotificationRead: async (notificationId) => {
    try {
      await axios.post(`${API_BASE_URL}/notifications/${notificationId}/read`);
      // Update local state
      set(state => ({
        notifications: state.notifications.map(notification =>
          notification.notification_id === notificationId
            ? { ...notification, is_read: true, read_at: new Date().toISOString() }
            : notification
        ),
        unreadNotificationsCount: Math.max(0, state.unreadNotificationsCount - 1)
      }));
      return true;
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
      return false;
    }
  },

  markNotificationDeleted: async (notificationId) => {
    try {
      await axios.post(`${API_BASE_URL}/notifications/${notificationId}/delete`);
      // Update local state
      set(state => ({
        notifications: state.notifications.map(notification =>
          notification.notification_id === notificationId
            ? { ...notification, is_deleted: true, deleted_at: new Date().toISOString() }
            : notification
        )
      }));
      return true;
    } catch (error) {
      console.error('Failed to mark notification as deleted:', error);
      return false;
    }
  },

  markAllNotificationsRead: async () => {
    try {
      await axios.post(`${API_BASE_URL}/notifications/read-all`);
      // Update local state
      set(state => ({
        notifications: state.notifications.map(notification => ({
          ...notification,
          is_read: true,
          read_at: new Date().toISOString()
        })),
        unreadNotificationsCount: 0
      }));
      return true;
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
      return false;
    }
  },

  deleteAllNotifications: async () => {
    try {
      await axios.delete(`${API_BASE_URL}/notifications`);
      // Update local state
      set(state => ({
        notifications: state.notifications.map(notification => ({
          ...notification,
          is_deleted: true,
          deleted_at: new Date().toISOString()
        }))
      }));
      return true;
    } catch (error) {
      console.error('Failed to delete all notifications:', error);
      return false;
    }
  },

  // Clear error
  clearError: () => set({ error: null })
}));

export default useStore;
