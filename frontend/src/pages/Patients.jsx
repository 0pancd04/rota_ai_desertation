import { useEffect, useState } from 'react';
import useStore from '../store/useStore';
import { 
  MagnifyingGlassIcon, 
  UserIcon,
  HeartIcon,
  ClockIcon,
  BeakerIcon,
  LanguageIcon,
  PhoneIcon,
  FunnelIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

function Patients() {
  const { patients, fetchPatients, loading, clearPatients, clearEmployeesAndPatients } = useStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterMedication, setFilterMedication] = useState('all');
  const [showSourceMeta, setShowSourceMeta] = useState(false);

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

  const stats = [
    {
      name: 'Total Patients',
      value: patients.length,
      icon: UserIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      name: 'Requiring Medication',
      value: patients.filter(p => p.RequiresMedication === 'Y').length,
      icon: BeakerIcon,
      color: 'text-red-600',
      bgColor: 'bg-red-50'
    },
    {
      name: 'Total Hours Needed',
      value: patients.reduce((sum, p) => sum + (p.RequiredHoursOfSupport || 0), 0),
      icon: ClockIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    }
  ];

  const getMedicationColor = (requiresMedication) => {
    return requiresMedication === 'Y' 
      ? 'bg-red-100 text-red-800' 
      : 'bg-green-100 text-green-800';
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
          <UserIcon className="h-8 w-8 text-green-600" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Patient Management</h1>
        <p className="text-lg text-gray-600">View and manage patient care requirements</p>
        <div className="mt-3 flex items-center justify-center space-x-2">
          <button
            onClick={clearPatients}
            className="px-3 py-2 rounded border text-sm bg-white"
            disabled={loading}
          >Clear Patients</button>
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
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
              placeholder="Search patients..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <FunnelIcon className="h-5 w-5 text-gray-400" />
            </div>
            <select
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg leading-5 bg-white focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
              value={filterMedication}
              onChange={(e) => setFilterMedication(e.target.value)}
            >
              <option value="all">All Patients</option>
              <option value="yes">Requires Medication</option>
              <option value="no">No Medication</option>
            </select>
          </div>
          <div className="flex items-center justify-end">
            <label className="mr-2 text-sm text-gray-600">Show Source Columns</label>
            <input type="checkbox" checked={showSourceMeta} onChange={(e) => setShowSourceMeta(e.target.checked)} />
          </div>
        </div>
      </div>

      {/* Patients Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto mb-4"></div>
            <p className="text-gray-500">Loading patients...</p>
          </div>
        ) : filteredPatients.length === 0 ? (
          <div className="p-12 text-center">
            <UserIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500 text-lg">No patients found</p>
            <p className="text-gray-400 text-sm mt-1">Try adjusting your search or filters</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Patient
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
                  {/* Hidden by default source metadata */}
                  <th className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${showSourceMeta ? '' : 'hidden'}`}>
                    Source File
                  </th>
                  <th className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${showSourceMeta ? '' : 'hidden'}`}>
                    Uploaded At
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredPatients.map((patient) => (
                  <tr key={patient.PatientID} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-green-600">
                            {patient.PatientName?.charAt(0)}
                          </span>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {patient.PatientName}
                          </div>
                          <div className="text-sm text-gray-500">
                            {patient.PatientID}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      <div className="max-w-xs">
                        <div className="flex items-center">
                          <HeartIcon className="h-4 w-4 mr-2 text-red-500" />
                          {patient.RequiredSupport}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center text-sm text-gray-500">
                        <ClockIcon className="h-4 w-4 mr-2" />
                        {patient.RequiredHoursOfSupport} hours
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getMedicationColor(patient.RequiresMedication)}`}>
                        <BeakerIcon className="h-3 w-3 mr-1" />
                        {patient.RequiresMedication === 'Y' ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center text-sm text-gray-500">
                        <LanguageIcon className="h-4 w-4 mr-2" />
                        {patient.LanguagePreference || 'English'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center text-sm text-gray-500">
                        <PhoneIcon className="h-4 w-4 mr-2" />
                        {patient.EmergencyContact}
                      </div>
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap ${showSourceMeta ? '' : 'hidden'}`}>
                      <div className="text-xs text-gray-500">{patient.SourceFilename}</div>
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap ${showSourceMeta ? '' : 'hidden'}`}>
                      <div className="text-xs text-gray-500">{patient.SourceUploadedAt}</div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Results Summary */}
      {filteredPatients.length > 0 && (
        <div className="bg-green-50 rounded-lg p-4 border border-green-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <UserIcon className="h-5 w-5 text-green-600 mr-2" />
              <span className="text-sm font-medium text-gray-900">
                Showing {filteredPatients.length} of {patients.length} patients
              </span>
            </div>
            <div className="text-sm text-gray-500">
              {searchTerm && `Filtered by "${searchTerm}"`}
              {filterMedication !== 'all' && ` • ${filterMedication === 'yes' ? 'Requires Medication' : 'No Medication'}`}
            </div>
          </div>
        </div>
      )}

      {/* High Priority Patients */}
      {patients.filter(p => p.RequiresMedication === 'Y').length > 0 && (
        <div className="bg-red-50 rounded-lg p-6 border border-red-200">
          <div className="flex items-center mb-4">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-600 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">High Priority Patients</h3>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            {patients.filter(p => p.RequiresMedication === 'Y').length} patients require medication and need nurse assignments.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {patients.filter(p => p.RequiresMedication === 'Y').slice(0, 6).map((patient) => (
              <div key={patient.PatientID} className="bg-white rounded-lg p-3 border border-red-200">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                    <span className="text-xs font-medium text-red-600">
                      {patient.PatientName?.charAt(0)}
                    </span>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">{patient.PatientName}</p>
                    <p className="text-xs text-gray-500">{patient.PatientID}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Patients;