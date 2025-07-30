import { useEffect } from 'react';
import useStore from '../store/useStore';
import { 
  CalendarIcon, 
  ClockIcon, 
  TruckIcon,
  ClipboardDocumentListIcon,
  SparklesIcon,
  UserGroupIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline';

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
      medicine: 'bg-red-100 text-red-800 border-red-200',
      exercise: 'bg-blue-100 text-blue-800 border-blue-200',
      companionship: 'bg-green-100 text-green-800 border-green-200',
      personal_care: 'bg-purple-100 text-purple-800 border-purple-200'
    };
    return colors[serviceType] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const stats = [
    {
      name: 'Total Assignments',
      value: assignments.length,
      icon: ClipboardDocumentListIcon,
      color: 'from-blue-500 to-blue-600'
    },
    {
      name: 'Average Priority',
      value: assignments.length > 0 ? (assignments.reduce((sum, a) => sum + a.priority_score, 0) / assignments.length).toFixed(1) : '0',
      icon: ArrowTrendingUpIcon,
      color: 'from-green-500 to-green-600'
    },
    {
      name: 'Total Travel Time',
      value: assignments.reduce((sum, a) => sum + a.travel_time, 0),
      icon: TruckIcon,
      color: 'from-purple-500 to-purple-600'
    },
    {
      name: 'Total Service Time',
      value: assignments.reduce((sum, a) => sum + a.estimated_duration, 0),
      icon: ClockIcon,
      color: 'from-orange-500 to-orange-600'
    }
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full mb-4">
          <ClipboardDocumentListIcon className="h-8 w-8 text-white" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Assignment Management</h1>
        <p className="text-lg text-gray-600">View and manage staff-patient assignments</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
            <div className="flex items-center">
              <div className={`flex-shrink-0 w-12 h-12 bg-gradient-to-r ${stat.color} rounded-xl flex items-center justify-center shadow-lg`}>
                <stat.icon className="h-6 w-6 text-white" aria-hidden="true" />
              </div>
              <div className="ml-4 flex-1">
                <p className="text-sm font-medium text-gray-500 truncate">
                  {stat.name}
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {stat.name.includes('Time') ? `${stat.value} mins` : stat.value}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Action Button */}
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-2xl p-6 border border-purple-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <SparklesIcon className="h-6 w-6 text-purple-600 mr-3" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">AI-Powered Assignment</h3>
              <p className="text-sm text-gray-600">Generate optimal assignments using AI</p>
            </div>
          </div>
          <button
            onClick={handleGenerateWeeklyRota}
            disabled={loading}
            className={`group relative px-6 py-3 rounded-xl text-white font-semibold transition-all duration-200 shadow-lg ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 hover:shadow-xl transform hover:-translate-y-1'
            }`}
          >
            {loading ? (
              <div className="flex items-center">
                <div className="loading-spinner h-5 w-5 mr-2"></div>
                Generating...
              </div>
            ) : (
              <div className="flex items-center">
                <SparklesIcon className="h-5 w-5 mr-2" />
                Generate Weekly Rota
              </div>
            )}
          </button>
        </div>
      </div>

      {/* Assignments List */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
                          <div className="loading-spinner h-12 w-12 mx-auto mb-4"></div>
            <p className="text-gray-500">Loading assignments...</p>
          </div>
        ) : assignments.length === 0 ? (
          <div className="p-12 text-center">
            <ClipboardDocumentListIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500 text-lg">No assignments yet</p>
            <p className="text-gray-400 text-sm mt-1">Upload data and create assignments to get started</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {assignments.map((assignment, index) => (
              <div key={index} className="p-6 hover:bg-gray-50 transition-colors duration-200">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-4 mb-3">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                          <UserGroupIcon className="h-5 w-5 text-white" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">
                            {assignment.employee_name} → {assignment.patient_name}
                          </h3>
                          <p className="text-sm text-gray-500">Assignment #{index + 1}</p>
                        </div>
                      </div>
                      <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full border ${getServiceTypeColor(assignment.service_type)}`}>
                        {assignment.service_type}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 text-sm text-gray-500 mb-3">
                      <div className="flex items-center">
                        <CalendarIcon className="h-4 w-4 mr-2 text-purple-500" />
                        <span>Assigned: {assignment.assigned_time}</span>
                      </div>
                      <div className="flex items-center">
                        <ClockIcon className="h-4 w-4 mr-2 text-green-500" />
                        <span>Duration: {assignment.estimated_duration} mins</span>
                      </div>
                      <div className="flex items-center">
                        <TruckIcon className="h-4 w-4 mr-2 text-blue-500" />
                        <span>Travel: {assignment.travel_time} mins</span>
                      </div>
                    </div>
                    
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-sm text-gray-700">
                        <span className="font-medium">Reason:</span> {assignment.assignment_reason}
                      </p>
                    </div>
                  </div>
                  
                  <div className="ml-6 flex-shrink-0">
                    <div className="text-center">
                      <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                        <span className="text-lg font-bold text-white">
                          {assignment.priority_score}/10
                        </span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">Priority</div>
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
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-2xl p-6 border border-purple-100">
          <div className="flex items-center mb-4">
            <CheckCircleIcon className="h-5 w-5 text-purple-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">Assignment Summary</h3>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Total Assignments:</span>
              <span className="font-semibold text-gray-900">{assignments.length}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Average Priority:</span>
              <span className="font-semibold text-gray-900">
                {(assignments.reduce((sum, a) => sum + a.priority_score, 0) / assignments.length).toFixed(1)}/10
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Total Travel Time:</span>
              <span className="font-semibold text-gray-900">
                {assignments.reduce((sum, a) => sum + a.travel_time, 0)} mins
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Total Service Time:</span>
              <span className="font-semibold text-gray-900">
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
