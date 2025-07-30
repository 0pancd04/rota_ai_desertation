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
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      change: '+12%',
      changeType: 'increase'
    },
    {
      name: 'Total Patients',
      value: patients.length,
      icon: UserIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      change: '+8%',
      changeType: 'increase'
    },
    {
      name: 'Active Assignments',
      value: assignments.length,
      icon: ClipboardDocumentListIcon,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      change: '+24%',
      changeType: 'increase'
    },
    {
      name: 'Pending Assignments',
      value: Math.max(0, patients.length - assignments.length),
      icon: ExclamationTriangleIcon,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      change: '-15%',
      changeType: 'decrease'
    }
  ];

  const recentAssignments = assignments.slice(0, 5);

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-xl shadow-lg">
        <div className="px-8 py-12 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white/20 rounded-full mb-4">
            <SparklesIcon className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">
            Welcome to Healthcare Rota
          </h1>
          <p className="text-blue-100 text-lg">
            AI-Powered Staff Assignment System
          </p>
        </div>
      </div>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className={`flex-shrink-0 w-12 h-12 ${stat.bgColor} rounded-lg flex items-center justify-center`}>
                <stat.icon className={`w-6 h-6 ${stat.color}`} />
              </div>
              <div className="ml-4 flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-500 truncate">
                  {stat.name}
                </p>
                <p className="text-2xl font-semibold text-gray-900">
                  {loading ? (
                    <div className="h-8 w-16 bg-gray-200 rounded animate-pulse"></div>
                  ) : (
                    stat.value
                  )}
                </p>
              </div>
            </div>
            <div className="mt-4 flex items-center justify-between">
              <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${stat.bgColor} ${stat.color}`}>
                Active
              </div>
              <div className={`flex items-center text-sm font-medium ${
                stat.changeType === 'increase' ? 'text-green-600' : 'text-red-600'
              }`}>
                <ArrowTrendingUpIcon className={`w-4 h-4 mr-1 flex-shrink-0 ${
                  stat.changeType === 'decrease' ? 'rotate-180' : ''
                }`} />
                {stat.change}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <button className="flex items-center justify-center px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <ClockIcon className="w-5 h-5 mr-2 flex-shrink-0" />
            Generate Weekly Rota
          </button>
          <button className="flex items-center justify-center px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
            <PlusCircleIcon className="w-5 h-5 mr-2 flex-shrink-0" />
            Create Assignment
          </button>
          <button className="flex items-center justify-center px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
            <CloudArrowUpIcon className="w-5 h-5 mr-2 flex-shrink-0" />
            Upload New Data
          </button>
        </div>
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Assignments */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Recent Assignments</h3>
            </div>
            <div className="divide-y divide-gray-200">
              {loading ? (
                <div className="p-8 text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-500">Loading assignments...</p>
                </div>
              ) : recentAssignments.length > 0 ? (
                recentAssignments.map((assignment, index) => (
                  <div key={index} className="px-6 py-4 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                            <UserIcon className="w-5 h-5 text-blue-600" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {assignment.employee_name} → {assignment.patient_name}
                            </p>
                            <p className="text-sm text-gray-500 truncate">
                              {assignment.service_type} • {assignment.assigned_time}
                            </p>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 ml-4">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          <CheckCircleIcon className="w-3 h-3 mr-1 flex-shrink-0" />
                          Active
                        </span>
                        <div className="text-center">
                          <div className="text-sm font-medium text-gray-900">
                            {assignment.priority_score}/10
                          </div>
                          <div className="text-xs text-gray-500">Priority</div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="px-6 py-8 text-center">
                  <ClipboardDocumentListIcon className="mx-auto w-12 h-12 text-gray-400 mb-4" />
                  <p className="text-gray-500">No assignments yet</p>
                  <p className="text-gray-400 text-sm mt-1">Create your first assignment to get started</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* System Status */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">System Status</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Database</span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  <div className="w-2 h-2 bg-green-400 rounded-full mr-2 flex-shrink-0"></div>
                  Connected
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">AI Service</span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  <div className="w-2 h-2 bg-blue-400 rounded-full mr-2 flex-shrink-0"></div>
                  Active
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Processing</span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                  <div className="w-2 h-2 bg-purple-400 rounded-full mr-2 flex-shrink-0"></div>
                  Ready
                </span>
              </div>
            </div>
          </div>

          {/* Pending Tasks */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Pending Tasks</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Unassigned Patients</span>
                <span className="text-lg font-semibold text-orange-600">
                  {loading ? (
                    <div className="h-6 w-8 bg-gray-200 rounded animate-pulse"></div>
                  ) : (
                    Math.max(0, patients.length - assignments.length)
                  )}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Weekly Rota Due</span>
                <span className="text-lg font-semibold text-blue-600">2 days</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Data Updates</span>
                <span className="text-lg font-semibold text-green-600">Current</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;