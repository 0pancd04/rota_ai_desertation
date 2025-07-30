import { useEffect } from 'react';
import useStore from '../store/useStore';
import { 
  UserGroupIcon, 
  UserIcon, 
  ClipboardDocumentListIcon,
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline';

function Dashboard() {
  const { 
    employees, 
    patients, 
    assignments, 
    fetchEmployees, 
    fetchPatients, 
    fetchAssignments 
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
      color: 'bg-blue-500'
    },
    {
      name: 'Total Patients',
      value: patients.length,
      icon: UserIcon,
      color: 'bg-green-500'
    },
    {
      name: 'Active Assignments',
      value: assignments.length,
      icon: ClipboardDocumentListIcon,
      color: 'bg-purple-500'
    },
    {
      name: 'Pending Assignments',
      value: patients.length - assignments.length,
      icon: ExclamationTriangleIcon,
      color: 'bg-yellow-500'
    }
  ];

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Dashboard</h2>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className={`flex-shrink-0 ${stat.color} rounded-md p-3`}>
                  <stat.icon className="h-6 w-6 text-white" aria-hidden="true" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {stat.name}
                    </dt>
                    <dd className="text-lg font-semibold text-gray-900">
                      {stat.value}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Assignments */}
      <div className="mt-8">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Assignments</h3>
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          {assignments.length > 0 ? (
            <ul className="divide-y divide-gray-200">
              {assignments.slice(0, 5).map((assignment, index) => (
                <li key={index} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {assignment.employee_name} → {assignment.patient_name}
                      </p>
                      <p className="text-sm text-gray-500">
                        Service: {assignment.service_type} | Time: {assignment.assigned_time}
                      </p>
                    </div>
                    <div className="text-sm text-gray-500">
                      Priority: {assignment.priority_score}/10
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="px-6 py-4 text-sm text-gray-500">No assignments yet</p>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-8">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
            Generate Weekly Rota
          </button>
          <button className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700">
            Create Assignment
          </button>
          <button className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700">
            Upload New Data
          </button>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
