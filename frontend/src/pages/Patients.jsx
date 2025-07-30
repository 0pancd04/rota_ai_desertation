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

  const stats = [
    {
      name: 'Total Patients',
      value: patients.length,
      icon: UserIcon,
      color: 'from-blue-500 to-blue-600'
    },
    {
      name: 'Requiring Medication',
      value: patients.filter(p => p.RequiresMedication === 'Y').length,
      icon: BeakerIcon,
      color: 'from-red-500 to-red-600'
    },
    {
      name: 'Total Hours Needed',
      value: patients.reduce((sum, p) => sum + (p.RequiredHoursOfSupport || 0), 0),
      icon: ClockIcon,
      color: 'from-green-500 to-green-600'
    }
  ];

  const getMedicationColor = (requiresMedication) => {
    return requiresMedication === 'Y' 
      ? 'bg-red-100 text-red-800 border-red-200' 
      : 'bg-green-100 text-green-800 border-green-200';
  };

  return (
    <div className="space-y-8 fade-in">
      {/* Header */}
      <div className="text-center slide-up">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-green-600 to-emerald-600 rounded-full mb-4 hover-lift">
          <UserIcon className="h-8 w-8 text-white" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Patient Management</h1>
        <p className="text-lg text-gray-600">View and manage patient care requirements</p>
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
              className="block w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200 focus-ring"
              placeholder="Search patients..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <FunnelIcon className="h-5 w-5 text-gray-400" />
            </div>
            <select
              className="block w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl leading-5 bg-white focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200 focus-ring"
              value={filterMedication}
              onChange={(e) => setFilterMedication(e.target.value)}
            >
              <option value="all">All Patients</option>
              <option value="yes">Requires Medication</option>
              <option value="no">No Medication</option>
            </select>
          </div>
        </div>
      </div>

      {/* Patients Table */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden card-hover">
        {loading ? (
          <div className="p-12 text-center">
            <div className="loading-spinner h-12 w-12 mx-auto mb-4"></div>
            <p className="text-gray-500">Loading patients...</p>
          </div>
        ) : filteredPatients.length === 0 ? (
          <div className="p-12 text-center">
            <UserIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500 text-lg">No patients found</p>
            <p className="text-gray-400 text-sm mt-1">Try adjusting your search or filters</p>
          </div>
        ) : (
          <div className="overflow-x-auto smooth-scroll">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Patient
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Required Support
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Hours Needed
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Medication
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Language
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Emergency Contact
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {filteredPatients.map((patient, index) => (
                  <tr 
                    key={patient.PatientID} 
                    className="hover:bg-gray-50 transition-colors duration-200 slide-up"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center hover-lift">
                          <span className="text-sm font-semibold text-white">
                            {patient.PatientName?.charAt(0)}
                          </span>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-semibold text-gray-900">
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
                      <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full border ${getMedicationColor(patient.RequiresMedication)}`}>
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
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Results Summary */}
      {filteredPatients.length > 0 && (
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-2xl p-6 border border-green-100 card-hover">
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
        <div className="bg-gradient-to-r from-red-50 to-pink-50 rounded-2xl p-6 border border-red-100 card-hover">
          <div className="flex items-center mb-4">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">High Priority Patients</h3>
          </div>
          <p className="text-sm text-gray-600 mb-3">
            {patients.filter(p => p.RequiresMedication === 'Y').length} patients require medication and need nurse assignments.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {patients.filter(p => p.RequiresMedication === 'Y').slice(0, 6).map((patient, index) => (
              <div 
                key={patient.PatientID} 
                className="bg-white rounded-lg p-3 border border-red-200 hover-lift"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center hover-lift">
                    <span className="text-xs font-semibold text-white">
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
