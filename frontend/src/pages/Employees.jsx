import { useEffect, useState } from 'react';
import useStore from '../store/useStore';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';

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

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Employees</h2>

      {/* Search and Filter */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Search employees..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <select
          className="block w-full px-3 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          value={filterQualification}
          onChange={(e) => setFilterQualification(e.target.value)}
        >
          <option value="all">All Qualifications</option>
          <option value="Nurse">Nurse</option>
          <option value="Senior Carer">Senior Carer</option>
          <option value="Carer">Carer</option>
        </select>
      </div>

      {/* Employees Table */}
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        {loading ? (
          <div className="p-6 text-center">Loading employees...</div>
        ) : filteredEmployees.length === 0 ? (
          <div className="p-6 text-center text-gray-500">No employees found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {employee.EmployeeID}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {employee.Name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        employee.Qualification === 'Nurse' 
                          ? 'bg-green-100 text-green-800'
                          : employee.Qualification === 'Senior Carer'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {employee.Qualification}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {employee.TransportMode}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {employee.LanguageSpoken}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {employee.Shifts}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {employee.ContactNumber}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-3">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">
              Total Employees
            </dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">
              {employees.length}
            </dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">
              Nurses
            </dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">
              {employees.filter(e => e.Qualification === 'Nurse').length}
            </dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">
              Carers
            </dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">
              {employees.filter(e => e.Qualification === 'Carer' || e.Qualification === 'Senior Carer').length}
            </dd>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Employees;
