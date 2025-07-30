import { useEffect } from 'react';
import useStore from '../store/useStore';
import { CalendarIcon, ClockIcon, TruckIcon } from '@heroicons/react/24/outline';

function Assignments() {
  const { assignments, fetchAssignments, generateWeeklyRota, loading } = useStore();

  useEffect(() => {
    fetchAssignments();
  }, []);

  const handleGenerateWeeklyRota = async () => {
    if (window.confirm('This will generate assignments for all patients. Continue?')) {
      try {
        await generateWeeklyRota();
        alert('Weekly rota generated successfully!');
      } catch (error) {
        alert('Failed to generate weekly rota: ' + error.message);
      }
    }
  };

  const getServiceTypeColor = (serviceType) => {
    const colors = {
      medicine: 'bg-red-100 text-red-800',
      exercise: 'bg-blue-100 text-blue-800',
      companionship: 'bg-green-100 text-green-800',
      personal_care: 'bg-purple-100 text-purple-800'
    };
    return colors[serviceType] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold text-gray-900">Assignments</h2>
        <button
          onClick={handleGenerateWeeklyRota}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
        >
          Generate Weekly Rota
        </button>
      </div>

      {/* Assignments List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        {loading ? (
          <div className="p-6 text-center">Loading assignments...</div>
        ) : assignments.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <p>No assignments yet.</p>
            <p className="mt-2">Upload data and create assignments to get started.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {assignments.map((assignment, index) => (
              <div key={index} className="p-6 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-lg font-medium text-gray-900">
                        {assignment.employee_name} → {assignment.patient_name}
                      </h3>
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getServiceTypeColor(assignment.service_type)}`}>
                        {assignment.service_type}
                      </span>
                    </div>
                    
                    <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-3 text-sm text-gray-500">
                      <div className="flex items-center">
                        <CalendarIcon className="h-4 w-4 mr-1" />
                        <span>Assigned: {assignment.assigned_time}</span>
                      </div>
                      <div className="flex items-center">
                        <ClockIcon className="h-4 w-4 mr-1" />
                        <span>Duration: {assignment.estimated_duration} mins</span>
                      </div>
                      <div className="flex items-center">
                        <TruckIcon className="h-4 w-4 mr-1" />
                        <span>Travel: {assignment.travel_time} mins</span>
                      </div>
                    </div>
                    
                    <div className="mt-2 text-sm text-gray-600">
                      <p className="font-medium">Reason: {assignment.assignment_reason}</p>
                    </div>
                  </div>
                  
                  <div className="ml-4 flex-shrink-0">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {assignment.priority_score}/10
                      </div>
                      <div className="text-xs text-gray-500">Priority</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Summary */}
      {assignments.length > 0 && (
        <div className="mt-6 bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-900 mb-2">Summary</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Total Assignments:</span>
              <span className="ml-2 font-medium">{assignments.length}</span>
            </div>
            <div>
              <span className="text-gray-500">Average Priority:</span>
              <span className="ml-2 font-medium">
                {(assignments.reduce((sum, a) => sum + a.priority_score, 0) / assignments.length).toFixed(1)}/10
              </span>
            </div>
            <div>
              <span className="text-gray-500">Total Travel Time:</span>
              <span className="ml-2 font-medium">
                {assignments.reduce((sum, a) => sum + a.travel_time, 0)} mins
              </span>
            </div>
            <div>
              <span className="text-gray-500">Total Service Time:</span>
              <span className="ml-2 font-medium">
                {assignments.reduce((sum, a) => sum + a.estimated_duration, 0)} mins
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Assignments;
