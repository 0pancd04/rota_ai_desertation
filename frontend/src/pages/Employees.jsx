import { useEffect, useState } from 'react';
import useStore from '../store/useStore';
import { 
  MagnifyingGlassIcon, 
  UserGroupIcon,
  AcademicCapIcon,
  TruckIcon,
  LanguageIcon,
  ClockIcon,
  PhoneIcon,
  FunnelIcon
} from '@heroicons/react/24/outline';

function Employees() {
  const { employees, fetchEmployees, loading, clearEmployees, clearEmployeesAndPatients } = useStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterQualification, setFilterQualification] = useState('all');

  useEffect(() => {
    fetchEmployees();
  }, []);

  const filteredEmployees = employees.filter(employee => {
    const matchesSearch = 
      employee.Name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      employee.EmployeeID?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      employee.Address?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesQualification = 
      filterQualification === 'all' || 
      employee.Qualification === filterQualification;
    
    return matchesSearch && matchesQualification;
  });

  const stats = [
    {
      name: 'Total Employees',
      value: employees.length,
      icon: UserGroupIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      name: 'Nurses',
      value: employees.filter(e => e.Qualification === 'Nurse').length,
      icon: AcademicCapIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      name: 'Carers',
      value: employees.filter(e => e.Qualification === 'Carer' || e.Qualification === 'Senior Carer').length,
      icon: UserGroupIcon,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    }
  ];

  const getQualificationColor = (qualification) => {
    switch (qualification) {
      case 'Nurse':
        return 'bg-green-100 text-green-800';
      case 'Senior Carer':
        return 'bg-blue-100 text-blue-800';
      case 'Carer':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
          <UserGroupIcon className="h-8 w-8 text-blue-600" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Employee Management</h1>
        <p className="text-lg text-gray-600">View and manage your healthcare staff</p>
        <div className="mt-3 flex items-center justify-center space-x-2">
          <button
            onClick={clearEmployees}
            className="px-3 py-2 rounded border text-sm bg-white"
            disabled={loading}
          >Clear Employees</button>
          <button
            onClick={clearEmployeesAndPatients}
            className="px-3 py-2 rounded bg-red-600 text-white text-sm"
            disabled={loading}
          >Clear Employees & Patients</button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className={`flex-shrink-0 w-12 h-12 ${stat.bgColor} rounded-lg flex items-center justify-center`}>
                <stat.icon className={`h-6 w-6 ${stat.color}`} />
              </div>
              <div className="ml-4 flex-1">
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
          </div>
        ))}
      </div>

      {/* Search and Filter */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Search employees..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <FunnelIcon className="h-5 w-5 text-gray-400" />
            </div>
            <select
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg leading-5 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={filterQualification}
              onChange={(e) => setFilterQualification(e.target.value)}
            >
              <option value="all">All Qualifications</option>
              <option value="Nurse">Nurse</option>
              <option value="Senior Carer">Senior Carer</option>
              <option value="Carer">Carer</option>
            </select>
          </div>
        </div>
      </div>

      {/* Employees Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-500">Loading employees...</p>
          </div>
        ) : filteredEmployees.length === 0 ? (
          <div className="p-12 text-center">
            <UserGroupIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500 text-lg">No employees found</p>
            <p className="text-gray-400 text-sm mt-1">Try adjusting your search or filters</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Employee
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Qualification
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Transport
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Languages
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Shifts
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contact
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredEmployees.map((employee) => (
                  <tr key={employee.EmployeeID} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-blue-600">
                            {employee.Name?.charAt(0)}
                          </span>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {employee.Name}
                          </div>
                          <div className="text-sm text-gray-500">
                            {employee.EmployeeID}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getQualificationColor(employee.Qualification)}`}>
                        {employee.Qualification}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center text-sm text-gray-500">
                        <TruckIcon className="h-4 w-4 mr-2" />
                        {employee.TransportMode}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center text-sm text-gray-500">
                        <LanguageIcon className="h-4 w-4 mr-2" />
                        {employee.LanguageSpoken}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center text-sm text-gray-500">
                        <ClockIcon className="h-4 w-4 mr-2" />
                        {employee.Shifts}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center text-sm text-gray-500">
                        <PhoneIcon className="h-4 w-4 mr-2" />
                        {employee.ContactNumber}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Results Summary */}
      {filteredEmployees.length > 0 && (
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <UserGroupIcon className="h-5 w-5 text-blue-600 mr-2" />
              <span className="text-sm font-medium text-gray-900">
                Showing {filteredEmployees.length} of {employees.length} employees
              </span>
            </div>
            <div className="text-sm text-gray-500">
              {searchTerm && `Filtered by "${searchTerm}"`}
              {filterQualification !== 'all' && ` • ${filterQualification}`}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Employees;