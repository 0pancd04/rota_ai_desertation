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
  rawUploads: [],
  activeTasks: [],
  notifications: [],
  unreadNotificationsCount: 0,
  stats: null,

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
      await get().fetchRawUploads();
      
      return response.data;
    } catch (error) {
      set({ 
        error: error.response?.data?.detail || 'Failed to upload file',
        loading: false 
      });
      throw error;
    }
  },

  // Raw uploads listing
  fetchRawUploads: async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/uploads/raw`);
      set({ rawUploads: res.data.raw_uploads || [] });
      return res.data.raw_uploads || [];
    } catch (e) {
      return [];
    }
  },

  // Raw upload sheet data
  fetchRawUploadSheet: async (uploadId, sheet) => {
    try {
      const res = await axios.get(`${API_BASE_URL}/uploads/raw/${uploadId}/sheet/${encodeURIComponent(sheet)}`);
      return res.data;
    } catch (e) {
      return { columns: [], rows: [] };
    }
  },

  // Raw upload metadata (sheet names)
  fetchRawUploadMeta: async (uploadId) => {
    try {
      const res = await axios.get(`${API_BASE_URL}/uploads/raw/${uploadId}`);
      return res.data || { sheet_names: [] };
    } catch (e) {
      return { sheet_names: [] };
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

  // Update assignment
  updateAssignment: async (assignmentId, updates) => {
    set({ loading: true, error: null });
    try {
      const response = await axios.put(`${API_BASE_URL}/assignments/${assignmentId}`, updates);
      
      if (response.data.success) {
        // Refresh assignments to get updated data
        await get().fetchAssignments();
        return response.data;
      } else {
        throw new Error(response.data.message);
      }
    } catch (error) {
      set({ 
        error: error.response?.data?.detail || error.message || 'Failed to update assignment',
        loading: false 
      });
      throw error;
    }
  },

  // Delete assignment
  deleteAssignment: async (assignmentId) => {
    set({ loading: true, error: null });
    try {
      const response = await axios.delete(`${API_BASE_URL}/assignments/${assignmentId}`);
      
      if (response.data.success) {
        // Remove assignment from state
        set(state => ({
          assignments: state.assignments.filter(assignment => 
            assignment.id !== assignmentId
          ),
          loading: false
        }));
        return response.data;
      } else {
        throw new Error(response.data.message);
      }
    } catch (error) {
      set({ 
        error: error.response?.data?.detail || error.message || 'Failed to delete assignment',
        loading: false 
      });
      throw error;
    }
  },

  // Bulk delete assignments
  bulkDeleteAssignments: async ({ mode = 'all', ids = [], filters = [] } = {}) => {
    set({ loading: true, error: null });
    try {
      const response = await axios.post(`${API_BASE_URL}/assignments/bulk-delete`, {
        mode,
        ids,
        filters
      });
      if (response.data.success) {
        // Refresh assignments
        await get().fetchAssignments();
        set({ loading: false });
        return response.data;
      } else {
        throw new Error('Bulk delete failed');
      }
    } catch (error) {
      set({ 
        error: error.response?.data?.detail || error.message || 'Failed to bulk delete',
        loading: false 
      });
      throw error;
    }
  },

  // Reanalyze selected assignments
  reanalyzeAssignments: async (assignmentIds, allowTimeChange = false) => {
    set({ loading: true, error: null });
    try {
      const response = await axios.post(`${API_BASE_URL}/assignments/reanalyze`, {
        assignment_ids: assignmentIds,
        allow_time_change: allowTimeChange
      });
      if (response.data.success) {
        await get().fetchAssignments();
        set({ loading: false });
        return response.data.updated || [];
      }
      throw new Error('Reanalysis failed');
    } catch (error) {
      set({ error: error.response?.data?.detail || error.message || 'Failed to reanalyze', loading: false });
      return [];
    }
  },

  // Fetch one employee's weekly assignments
  fetchEmployeeWeekAssignments: async (employeeId, weekStartIso, weekEndIso) => {
    set({ loading: true, error: null });
    try {
      const response = await axios.post(`${API_BASE_URL}/employee/assignments/week`, {
        employee_id: employeeId,
        week_start: weekStartIso,
        week_end: weekEndIso
      });
      set({ loading: false });
      return response.data.assignments || [];
    } catch (error) {
      set({ 
        error: error.response?.data?.detail || 'Failed to fetch employee week assignments',
        loading: false 
      });
      return [];
    }
  },

  // Fetch stats with optional force regenerate
  fetchStats: async (force = false, { days = null, startDate = null, endDate = null } = {}) => {
    set({ loading: true, error: null });
    try {
      const params = { force };
      if (Array.isArray(days) && days.length > 0) params.days = days.join(',');
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      const response = await axios.get(`${API_BASE_URL}/stats`, { params });
      set({ stats: response.data.stats || null, loading: false });
      return response.data.stats;
    } catch (error) {
      set({ error: error.response?.data?.detail || 'Failed to fetch stats', loading: false });
      return null;
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

  // Clear employees/patients helpers
  clearEmployees: async () => {
    set({ loading: true, error: null });
    try {
      await axios.post(`${API_BASE_URL}/database/clear-employees`);
      await get().fetchEmployees();
      set({ loading: false });
      return true;
    } catch (error) {
      set({ error: error.response?.data?.detail || 'Failed to clear employees', loading: false });
      return false;
    }
  },
  clearPatients: async () => {
    set({ loading: true, error: null });
    try {
      await axios.post(`${API_BASE_URL}/database/clear-patients`);
      await get().fetchPatients();
      set({ loading: false });
      return true;
    } catch (error) {
      set({ error: error.response?.data?.detail || 'Failed to clear patients', loading: false });
      return false;
    }
  },
  clearEmployeesAndPatients: async () => {
    set({ loading: true, error: null });
    try {
      await axios.post(`${API_BASE_URL}/database/clear-people`);
      await get().fetchEmployees();
      await get().fetchPatients();
      set({ loading: false });
      return true;
    } catch (error) {
      set({ error: error.response?.data?.detail || 'Failed to clear employees and patients', loading: false });
      return false;
    }
  },

  // Clear error
  clearError: () => set({ error: null })
}));

export default useStore;
