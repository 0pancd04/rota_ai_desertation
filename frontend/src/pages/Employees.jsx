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
  const { employees, fetchEmployees, loading } = useStore();
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
      color: 'from-blue-500 to-blue-600'
    },
    {
      name: 'Nurses',
      value: employees.filter(e => e.Qualification === 'Nurse').length,
      icon: AcademicCapIcon,
      color: 'from-green-500 to-green-600'
    },
    {
      name: 'Carers',
      value: employees.filter(e => e.Qualification === 'Carer' || e.Qualification === 'Senior Carer').length,
      icon: UserGroupIcon,
      color: 'from-purple-500 to-purple-600'
    }
  ];

  const getQualificationColor = (qualification) => {
    switch (qualification) {
      case 'Nurse':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'Senior Carer':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'Carer':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="space-y-8 fade-in">
      {/* Header */}
      <div className="text-center slide-up">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full mb-4 hover-lift">
          <UserGroupIcon className="h-8 w-8 text-white" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Employee Management</h1>
        <p className="text-lg text-gray-600">View and manage your healthcare staff</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
        {stats.map((stat, index) => (
          <div 
            key={stat.name} 
            className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 card-hover"
            style={{ animationDelay: `${index * 100}ms` }}
          >
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
          </div>
        ))}
      </div>

      {/* Search and Filter */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 card-hover">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 focus-ring"
              placeholder="Search employees..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <FunnelIcon className="h-5 w-5 text-gray-400" />
            </div>
            <select
              className="block w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl leading-5 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 focus-ring"
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
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden card-hover">
        {loading ? (
          <div className="p-12 text-center">
            <div className="loading-spinner h-12 w-12 mx-auto mb-4"></div>
            <p className="text-gray-500">Loading employees...</p>
          </div>
        ) : filteredEmployees.length === 0 ? (
          <div className="p-12 text-center">
            <UserGroupIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500 text-lg">No employees found</p>
            <p className="text-gray-400 text-sm mt-1">Try adjusting your search or filters</p>
          </div>
        ) : (
          <div className="overflow-x-auto smooth-scroll">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Employee
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Qualification
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Transport
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Languages
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Shifts
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Contact
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {filteredEmployees.map((employee, index) => (
                  <tr 
                    key={employee.EmployeeID} 
                    className="hover:bg-gray-50 transition-colors duration-200 slide-up"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full flex items-center justify-center hover-lift">
                          <span className="text-sm font-semibold text-white">
                            {employee.Name?.charAt(0)}
                          </span>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-semibold text-gray-900">
                            {employee.Name}
                          </div>
                          <div className="text-sm text-gray-500">
                            {employee.EmployeeID}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full border ${getQualificationColor(employee.Qualification)}`}>
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
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-100 card-hover">
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
