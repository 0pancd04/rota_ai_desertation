import { useEffect, useState } from 'react';
import useStore from '../store/useStore';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';

function Patients() {
  const { patients, fetchPatients, loading } = useStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterMedication, setFilterMedication] = useState('all');

  useEffect(() => {
    fetchPatients();
  }, []);

  const filteredPatients = patients.filter(patient => {
    const matchesSearch = 
      patient.PatientName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      patient.PatientID?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      patient.Address?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesMedication = 
      filterMedication === 'all' || 
      (filterMedication === 'yes' && patient.RequiresMedication === 'Y') ||
      (filterMedication === 'no' && patient.RequiresMedication === 'N');
    
    return matchesSearch && matchesMedication;
  });

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Patients</h2>

      {/* Search and Filter */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Search patients..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <select
          className="block w-full px-3 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          value={filterMedication}
          onChange={(e) => setFilterMedication(e.target.value)}
        >
          <option value="all">All Patients</option>
          <option value="yes">Requires Medication</option>
          <option value="no">No Medication</option>
        </select>
      </div>

      {/* Patients Table */}
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        {loading ? (
          <div className="p-6 text-center">Loading patients...</div>
        ) : filteredPatients.length === 0 ? (
          <div className="p-6 text-center text-gray-500">No patients found</div>
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
                    Required Support
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Hours Needed
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Medication
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Language
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Emergency Contact
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredPatients.map((patient) => (
                  <tr key={patient.PatientID} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {patient.PatientID}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {patient.PatientName}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      <div className="max-w-xs">
                        {patient.RequiredSupport}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {patient.RequiredHoursOfSupport} hours
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        patient.RequiresMedication === 'Y' 
                          ? 'bg-red-100 text-red-800'
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {patient.RequiresMedication === 'Y' ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {patient.LanguagePreference || 'English'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {patient.EmergencyContact}
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
              Total Patients
            </dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">
              {patients.length}
            </dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">
              Requiring Medication
            </dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">
              {patients.filter(p => p.RequiresMedication === 'Y').length}
            </dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">
              Total Hours Needed
            </dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">
              {patients.reduce((sum, p) => sum + (p.RequiredHoursOfSupport || 0), 0)}
            </dd>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Patients;
