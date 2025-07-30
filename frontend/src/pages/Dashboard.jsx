import { useEffect } from 'react';
import useStore from '../store/useStore';
import { 
  UserGroupIcon, 
  UserIcon, 
  ClipboardDocumentListIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  ClockIcon,
  CheckCircleIcon,
  SparklesIcon,
  PlusCircleIcon,
  CloudArrowUpIcon
} from '@heroicons/react/24/outline';

function Dashboard() {
  const { 
    employees, 
    patients, 
    assignments, 
    fetchEmployees, 
    fetchPatients, 
    fetchAssignments,
    loading 
  } = useStore();

  useEffect(() => {
    fetchEmployees();
    fetchPatients();
    fetchAssignments();
  }, []);

  const stats = [
    {
      name: 'Total Employees',
      value: employees.length,
      icon: UserGroupIcon,
      color: 'from-blue-500 to-blue-600',
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-600'
    },
    {
      name: 'Total Patients',
      value: patients.length,
      icon: UserIcon,
      color: 'from-green-500 to-green-600',
      bgColor: 'bg-green-50',
      textColor: 'text-green-600'
    },
    {
      name: 'Active Assignments',
      value: assignments.length,
      icon: ClipboardDocumentListIcon,
      color: 'from-purple-500 to-purple-600',
      bgColor: 'bg-purple-50',
      textColor: 'text-purple-600'
    },
    {
      name: 'Pending Assignments',
      value: Math.max(0, patients.length - assignments.length),
      icon: ExclamationTriangleIcon,
      color: 'from-yellow-500 to-yellow-600',
      bgColor: 'bg-yellow-50',
      textColor: 'text-yellow-600'
    }
  ];

  const recentAssignments = assignments.slice(0, 5);
  const pendingCount = Math.max(0, patients.length - assignments.length);

  return (
    <div className="space-y-8 fade-in">
      {/* Welcome Section */}
      <div className="text-center mb-8 slide-up">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full mb-4 hover-lift">
          <SparklesIcon className="h-8 w-8 text-white" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome to Healthcare Rota</h1>
        <p className="text-lg text-gray-600">AI-Powered Staff Assignment System</p>
      </div>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => (
          <div 
            key={stat.name} 
            className="group relative bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100 card-hover"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <div className="p-6">
              <div className="flex items-center">
                <div className={`flex-shrink-0 w-12 h-12 bg-gradient-to-r ${stat.color} rounded-xl flex items-center justify-center shadow-lg hover-lift`}>
                  <stat.icon className="h-6 w-6 text-white" aria-hidden="true" />
                </div>
                <div className="ml-4 flex-1">
                  <p className="text-sm font-medium text-gray-500 truncate">
                    {stat.name}
                  </p>
                  <p className="text-2xl font-bold text-gray-900">
                    {loading ? (
                      <div className="shimmer h-8 w-16 rounded"></div>
                    ) : (
                      stat.value
                    )}
                  </p>
                </div>
              </div>
              <div className="mt-4">
                <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${stat.bgColor} ${stat.textColor}`}>
                  <ArrowTrendingUpIcon className="h-3 w-3 mr-1" />
                  Active
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-100 card-hover">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <SparklesIcon className="h-5 w-5 mr-2 text-blue-600" />
          Quick Actions
        </h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <button className="group bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-3 rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-1 btn-press">
            <div className="flex items-center justify-center">
              <ClockIcon className="h-5 w-5 mr-2" />
              Generate Weekly Rota
            </div>
          </button>
          <button className="group bg-gradient-to-r from-green-600 to-emerald-600 text-white px-6 py-3 rounded-xl hover:from-green-700 hover:to-emerald-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-1 btn-press">
            <div className="flex items-center justify-center">
              <PlusCircleIcon className="h-5 w-5 mr-2" />
              Create Assignment
            </div>
          </button>
          <button className="group bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-1 btn-press">
            <div className="flex items-center justify-center">
              <CloudArrowUpIcon className="h-5 w-5 mr-2" />
              Upload New Data
            </div>
          </button>
        </div>
      </div>

      {/* Recent Assignments */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 card-hover">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <ClipboardDocumentListIcon className="h-5 w-5 mr-2 text-blue-600" />
            Recent Assignments
          </h3>
        </div>
        <div className="divide-y divide-gray-100">
          {loading ? (
            <div className="p-12 text-center">
              <div className="loading-spinner h-12 w-12 mx-auto mb-4"></div>
              <p className="text-gray-500">Loading assignments...</p>
            </div>
          ) : recentAssignments.length > 0 ? (
            recentAssignments.map((assignment, index) => (
              <div key={index} className="px-6 py-4 hover:bg-gray-50 transition-colors duration-200 slide-up" style={{ animationDelay: `${index * 50}ms` }}>
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full flex items-center justify-center hover-lift">
                        <UserIcon className="h-4 w-4 text-white" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-gray-900">
                          {assignment.employee_name} → {assignment.patient_name}
                        </p>
                        <p className="text-sm text-gray-500">
                          {assignment.service_type} • {assignment.assigned_time}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      <CheckCircleIcon className="h-3 w-3 mr-1" />
                      Active
                    </div>
                    <div className="text-sm font-medium text-gray-900">
                      {assignment.priority_score}/10
                    </div>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="px-6 py-8 text-center">
              <ClipboardDocumentListIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p className="text-gray-500 text-sm">No assignments yet</p>
              <p className="text-gray-400 text-xs mt-1">Create your first assignment to get started</p>
            </div>
          )}
        </div>
      </div>

      {/* System Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 card-hover">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <CheckCircleIcon className="h-5 w-5 mr-2 text-green-600" />
            System Status
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Database Connection</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-1 status-pulse"></div>
                Connected
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">AI Service</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-1 status-pulse"></div>
                Active
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Data Processing</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-1 status-pulse"></div>
                Ready
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 card-hover">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <ExclamationTriangleIcon className="h-5 w-5 mr-2 text-yellow-600" />
            Pending Tasks
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Unassigned Patients</span>
              <span className="text-sm font-semibold text-gray-900">
                {loading ? (
                  <div className="shimmer h-4 w-8 rounded"></div>
                ) : (
                  pendingCount
                )}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Weekly Rota Due</span>
              <span className="text-sm font-semibold text-gray-900">2 days</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Data Updates</span>
              <span className="text-sm font-semibold text-gray-900">Current</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
