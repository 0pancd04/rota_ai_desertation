import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useStore from '../store/useStore';
import { useFilterManager } from '../hooks/useFilterManager';
import FilterPanel from '../components/FilterPanel';
import { 
  PlusIcon, 
  FunnelIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  ClockIcon,
  UserIcon,
  UserGroupIcon,
  XMarkIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline';

function Assignments() {
  const navigate = useNavigate();
  const { 
    assignments, 
    fetchAssignments, 
    updateAssignment,
    deleteAssignment,
    loading, 
    error 
  } = useStore();

  const {
    filters,
    suggestions,
    sortBy,
    sortOrder,
    pageSize,
    pageNumber,
    isLoading: filterLoading,
    error: filterError,
    handleFiltersChange,
    handleClearFilters,
    handleSaveFilters,
    handleApplyFiltersToData,
    handleSortChange,
    handlePageSizeChange,
    handlePageNumberChange,
    handleClearError
  } = useFilterManager('assignments');

  const [filteredAssignments, setFilteredAssignments] = useState([]);
  const [displayedAssignments, setDisplayedAssignments] = useState([]);
  
  // Edit modal state
  const [editingAssignment, setEditingAssignment] = useState(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editFormData, setEditFormData] = useState({});
  
  // Delete confirmation state
  const [deletingAssignment, setDeletingAssignment] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    fetchAssignments();
  }, [fetchAssignments]);

  // Apply filters and sorting when data or filters change
  useEffect(() => {
    const applyFiltersAndSort = async () => {
      if (assignments.length === 0) {
        setFilteredAssignments([]);
        setDisplayedAssignments([]);
        return;
      }

      // Apply filters
      let filtered = await handleApplyFiltersToData(assignments);
      setFilteredAssignments(filtered);

      // Apply sorting
      if (sortBy) {
        filtered = [...filtered].sort((a, b) => {
          const aValue = a[sortBy];
          const bValue = b[sortBy];
          
          if (aValue === bValue) return 0;
          if (aValue === null || aValue === undefined) return 1;
          if (bValue === null || bValue === undefined) return -1;
          
          const comparison = aValue < bValue ? -1 : 1;
          return sortOrder === 'desc' ? -comparison : comparison;
        });
      }

      // Apply pagination
      const startIndex = (pageNumber - 1) * pageSize;
      const endIndex = startIndex + pageSize;
      setDisplayedAssignments(filtered.slice(startIndex, endIndex));
    };

    applyFiltersAndSort();
  }, [assignments, filters, sortBy, sortOrder, pageSize, pageNumber, handleApplyFiltersToData]);

  const getTotalPages = () => {
    return Math.ceil(filteredAssignments.length / pageSize);
  };

  const handleSort = (field) => {
    const newSortOrder = sortBy === field && sortOrder === 'asc' ? 'desc' : 'asc';
    handleSortChange(field, newSortOrder);
  };

  // Edit assignment handlers
  const handleEditClick = (assignment) => {
    setEditingAssignment(assignment);
    setEditFormData({
      employee_id: assignment.employee_id,
      patient_id: assignment.patient_id,
      service_type: assignment.service_type,
      assigned_time: assignment.assigned_time,
      estimated_duration: assignment.estimated_duration,
      travel_time: assignment.travel_time,
      start_time: assignment.start_time,
      end_time: assignment.end_time,
      priority_score: assignment.priority_score,
      assignment_reason: assignment.assignment_reason
    });
    setShowEditModal(true);
  };

  const handleEditFormChange = (field, value) => {
    setEditFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleEditSubmit = async () => {
    try {
      if (!editingAssignment?.id) {
        alert('Cannot edit assignment: Missing assignment ID');
        return;
      }

      await updateAssignment(editingAssignment.id, editFormData);
      setShowEditModal(false);
      setEditingAssignment(null);
      setEditFormData({});
      // Success message could be added here
    } catch (error) {
      console.error('Error updating assignment:', error);
      // Error is already handled by the store
    }
  };

  const handleEditCancel = () => {
    setShowEditModal(false);
    setEditingAssignment(null);
    setEditFormData({});
  };

  // Delete assignment handlers
  const handleDeleteClick = (assignment) => {
    setDeletingAssignment(assignment);
    setShowDeleteConfirm(true);
  };

  const handleDeleteConfirm = async () => {
    try {
      if (!deletingAssignment?.id) {
        alert('Cannot delete assignment: Missing assignment ID');
        return;
      }

      await deleteAssignment(deletingAssignment.id);
      setShowDeleteConfirm(false);
      setDeletingAssignment(null);
      // Success message could be added here
    } catch (error) {
      console.error('Error deleting assignment:', error);
      // Error is already handled by the store
    }
  };

  const handleDeleteCancel = () => {
    setShowDeleteConfirm(false);
    setDeletingAssignment(null);
  };



  const getSortIcon = (field) => {
    if (sortBy !== field) return null;
    return sortOrder === 'asc' ? 
      <ArrowUpIcon className="w-4 h-4" /> : 
      <ArrowDownIcon className="w-4 h-4" />;
  };

  const formatTime = (timeString) => {
    if (!timeString) return 'N/A';
    try {
      const date = new Date(timeString);
      return date.toLocaleString();
    } catch {
      return timeString;
    }
  };

  const getPriorityColor = (score) => {
    if (score >= 8) return 'bg-red-100 text-red-800';
    if (score >= 6) return 'bg-orange-100 text-orange-800';
    if (score >= 4) return 'bg-yellow-100 text-yellow-800';
    return 'bg-green-100 text-green-800';
  };

  const getServiceTypeColor = (type) => {
    switch (type?.toLowerCase()) {
      case 'medicine': return 'bg-blue-100 text-blue-800';
      case 'exercise': return 'bg-green-100 text-green-800';
      case 'companionship': return 'bg-purple-100 text-purple-800';
      case 'personal_care': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleExportExcel = async () => {
    try {
      // Try using proxy first, then fallback to direct API call
      let response;
      try {
        // First try the proxy approach
        response = await fetch('/api/export/assignments-excel');
      } catch (proxyError) {
        console.log('Proxy failed, trying direct API call:', proxyError);
        // Fallback to direct API call
        const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        response = await fetch(`${API_BASE_URL}/export/assignments-excel`);
      }
      
      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }
      
      // Get the filename from the response headers
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'assignments_export.xlsx';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
    } catch (error) {
      console.error('Export failed:', error);
      // You could add a toast notification here
      alert('Export failed. Please try again.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Assignments</h1>
          <p className="text-gray-600">
            {filteredAssignments.length} of {assignments.length} assignments
            {filters.length > 0 && ` (filtered)`}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <FilterPanel
            page="assignments"
            suggestions={suggestions}
            filters={filters}
            onFiltersChange={handleFiltersChange}
            onClearFilters={handleClearFilters}
            onSaveFilters={handleSaveFilters}
            isLoading={filterLoading}
          />
          <button
            onClick={handleExportExcel}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            title="Export assignments data to Excel"
          >
            <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
            Export Excel
          </button>
          <button
            onClick={() => navigate('/create-assignment')}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Create Assignment
          </button>
        </div>
      </div>

      {/* Error Display */}
      {(error || filterError) && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-5 h-5 bg-red-400 rounded-full flex items-center justify-center">
                <span className="text-white text-xs">!</span>
              </div>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="text-sm text-red-600 mt-1">
                {error || filterError}
              </p>
            </div>
            <div className="ml-auto pl-3">
              <button
                onClick={handleClearError}
                className="text-red-400 hover:text-red-600"
              >
                <span className="sr-only">Dismiss</span>
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {(loading || filterLoading) && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-500">Loading assignments...</p>
        </div>
      )}

      {/* Assignments Table */}
      {!loading && !filterLoading && (
        <div className="bg-white shadow-sm border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('employee_name')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>Employee</span>
                      {getSortIcon('employee_name')}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('patient_name')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>Patient</span>
                      {getSortIcon('patient_name')}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('service_type')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>Service</span>
                      {getSortIcon('service_type')}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('assigned_time')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>Assigned Time</span>
                      {getSortIcon('assigned_time')}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('priority_score')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>Priority</span>
                      {getSortIcon('priority_score')}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('travel_time')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>Travel Time</span>
                      {getSortIcon('travel_time')}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {displayedAssignments.map((assignment, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                          <UserIcon className="w-4 h-4 text-blue-600" />
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {assignment.employee_name}
                          </div>
                          <div className="text-sm text-gray-500">
                            {assignment.employee_id}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
                          <UserGroupIcon className="w-4 h-4 text-green-600" />
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {assignment.patient_name}
                          </div>
                          <div className="text-sm text-gray-500">
                            {assignment.patient_id}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getServiceTypeColor(assignment.service_type)}`}>
                        {assignment.service_type?.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatTime(assignment.assigned_time)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(assignment.priority_score)}`}>
                        {assignment.priority_score}/10
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center">
                        <ClockIcon className="w-4 h-4 mr-1 text-gray-400" />
                        {assignment.travel_time || 0} min
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center space-x-2">
                        <button 
                          className="text-blue-600 hover:text-blue-900"
                          title="View assignment details"
                        >
                          <EyeIcon className="w-4 h-4" />
                        </button>
                        <button 
                          className="text-green-600 hover:text-green-900"
                          onClick={() => handleEditClick(assignment)}
                          title="Edit assignment"
                        >
                          <PencilIcon className="w-4 h-4" />
                        </button>
                        <button 
                          className="text-red-600 hover:text-red-900"
                          onClick={() => handleDeleteClick(assignment)}
                          title="Delete assignment"
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {getTotalPages() > 1 && (
            <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
              <div className="flex-1 flex justify-between sm:hidden">
                <button
                  onClick={() => handlePageNumberChange(pageNumber - 1)}
                  disabled={pageNumber === 1}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => handlePageNumberChange(pageNumber + 1)}
                  disabled={pageNumber === getTotalPages()}
                  className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
              <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700">
                    Showing{' '}
                    <span className="font-medium">{(pageNumber - 1) * pageSize + 1}</span>
                    {' '}to{' '}
                    <span className="font-medium">
                      {Math.min(pageNumber * pageSize, filteredAssignments.length)}
                    </span>
                    {' '}of{' '}
                    <span className="font-medium">{filteredAssignments.length}</span>
                    {' '}results
                  </p>
                </div>
                <div>
                  <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                    <button
                      onClick={() => handlePageNumberChange(pageNumber - 1)}
                      disabled={pageNumber === 1}
                      className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                    >
                      Previous
                    </button>
                    {Array.from({ length: getTotalPages() }, (_, i) => i + 1).map((page) => (
                      <button
                        key={page}
                        onClick={() => handlePageNumberChange(page)}
                        className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                          page === pageNumber
                            ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                            : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                        }`}
                      >
                        {page}
                      </button>
                    ))}
                    <button
                      onClick={() => handlePageNumberChange(pageNumber + 1)}
                      disabled={pageNumber === getTotalPages()}
                      className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                    >
                      Next
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!loading && !filterLoading && displayedAssignments.length === 0 && (
        <div className="text-center py-12">
          <div className="mx-auto w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <UserGroupIcon className="w-6 h-6 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No assignments found</h3>
          <p className="text-gray-500 mb-6">
            {filters.length > 0 
              ? 'Try adjusting your filters to see more results.'
              : 'Get started by creating your first assignment.'
            }
          </p>
          {filters.length === 0 && (
            <button
              onClick={() => navigate('/create-assignment')}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Create Assignment
            </button>
          )}
        </div>
      )}

      {/* Edit Assignment Modal */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={handleEditCancel}></div>
            
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <div className="sm:flex sm:items-start">
                <div className="w-full">
                  <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                    Edit Assignment
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Assigned Time</label>
                      <input
                        type="datetime-local"
                        value={editFormData.assigned_time?.substring(0, 16) || ''}
                        onChange={(e) => handleEditFormChange('assigned_time', e.target.value)}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Service Type</label>
                      <select
                        value={editFormData.service_type || ''}
                        onChange={(e) => handleEditFormChange('service_type', e.target.value)}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="medicine">Medicine</option>
                        <option value="exercise">Exercise</option>
                        <option value="companionship">Companionship</option>
                        <option value="personal_care">Personal Care</option>
                      </select>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Duration (min)</label>
                        <input
                          type="number"
                          value={editFormData.estimated_duration || ''}
                          onChange={(e) => handleEditFormChange('estimated_duration', parseInt(e.target.value))}
                          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Travel Time (min)</label>
                        <input
                          type="number"
                          value={editFormData.travel_time || ''}
                          onChange={(e) => handleEditFormChange('travel_time', parseInt(e.target.value))}
                          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Priority Score</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="10"
                        value={editFormData.priority_score || ''}
                        onChange={(e) => handleEditFormChange('priority_score', parseFloat(e.target.value))}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Assignment Reason</label>
                      <textarea
                        value={editFormData.assignment_reason || ''}
                        onChange={(e) => handleEditFormChange('assignment_reason', e.target.value)}
                        rows={3}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="mt-5 sm:mt-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                  onClick={handleEditSubmit}
                >
                  Save Changes
                </button>
                <button
                  type="button"
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:w-auto sm:text-sm"
                  onClick={handleEditCancel}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={handleDeleteCancel}></div>
            
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <div className="sm:flex sm:items-start">
                <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
                  <TrashIcon className="h-6 w-6 text-red-600" />
                </div>
                <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Delete Assignment
                  </h3>
                  <div className="mt-2">
                    <p className="text-sm text-gray-500">
                      Are you sure you want to delete the assignment for{' '}
                      <span className="font-medium">{deletingAssignment?.employee_name}</span>{' '}
                      to care for{' '}
                      <span className="font-medium">{deletingAssignment?.patient_name}</span>?
                      This action cannot be undone.
                    </p>
                  </div>
                </div>
              </div>
              <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm"
                  onClick={handleDeleteConfirm}
                >
                  Delete
                </button>
                <button
                  type="button"
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:w-auto sm:text-sm"
                  onClick={handleDeleteCancel}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Assignments;