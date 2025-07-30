import { useState } from 'react';
import useStore from '../store/useStore';
import { 
  CloudArrowUpIcon, 
  DocumentTextIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline';

function DataUpload() {
  const { uploadDataFile, uploadStatus, loading, error } = useStore();
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.endsWith('.xlsx') || droppedFile.name.endsWith('.xls')) {
        setFile(droppedFile);
      } else {
        alert('Please upload an Excel file (.xlsx or .xls)');
      }
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      alert('Please select a file to upload');
      return;
    }

    try {
      await uploadDataFile(file);
      setFile(null);
    } catch (err) {
      console.error('Upload failed:', err);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
          <CloudArrowUpIcon className="h-8 w-8 text-blue-600" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Data</h1>
        <p className="text-lg text-gray-600">Upload employee and patient data to get started</p>
      </div>

      {/* Upload Area */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* File Upload Area */}
          <div
            className={`relative border-2 border-dashed rounded-lg p-12 transition-colors ${
              dragActive 
                ? 'border-blue-400 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div className="text-center">
              <div className="mx-auto h-16 w-16 mb-4">
                {file ? (
                  <div className="h-16 w-16 bg-green-100 rounded-full flex items-center justify-center">
                    <CheckCircleIcon className="h-8 w-8 text-green-600" />
                  </div>
                ) : (
                  <div className="h-16 w-16 bg-gray-100 rounded-full flex items-center justify-center">
                    <CloudArrowUpIcon className="h-8 w-8 text-gray-400" />
                  </div>
                )}
              </div>
              
              <div className="mt-4">
                <label htmlFor="file-upload" className="cursor-pointer">
                  <span className="mt-2 block text-lg font-medium text-gray-900">
                    {file ? file.name : 'Drop your Excel file here or click to browse'}
                  </span>
                  <span className="mt-1 block text-sm text-gray-500">
                    {file ? (
                      <span className="text-green-600">✓ File selected successfully</span>
                    ) : (
                      'Supports .xlsx and .xls files • Max size: 10MB'
                    )}
                  </span>
                  <input
                    id="file-upload"
                    name="file-upload"
                    type="file"
                    className="sr-only"
                    accept=".xlsx,.xls"
                    onChange={handleChange}
                  />
                </label>
              </div>
              
              {!file && (
                <div className="mt-6">
                  <ArrowDownTrayIcon className="mx-auto h-8 w-8 text-gray-400" />
                </div>
              )}
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-center">
            <button
              type="submit"
              disabled={!file || loading}
              className={`px-8 py-3 rounded-lg text-white font-medium transition-colors ${
                !file || loading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Uploading...
                </div>
              ) : (
                <div className="flex items-center">
                  <CloudArrowUpIcon className="h-5 w-5 mr-2" />
                  Upload File
                </div>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-6 w-6 text-red-600 mr-3" />
            <div>
              <h3 className="text-sm font-medium text-red-800">Upload Error</h3>
              <p className="text-sm text-red-600 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {uploadStatus && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-center">
            <CheckCircleIcon className="h-6 w-6 text-green-600 mr-3" />
            <div>
              <h3 className="text-sm font-medium text-green-800">Upload Successful!</h3>
              <p className="text-sm text-green-600 mt-1">{uploadStatus.message}</p>
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="bg-white rounded-lg p-3 border border-green-200">
                  <p className="text-xs text-gray-500">Employees Loaded</p>
                  <p className="text-lg font-semibold text-green-600">{uploadStatus.employees_count}</p>
                </div>
                <div className="bg-white rounded-lg p-3 border border-green-200">
                  <p className="text-xs text-gray-500">Patients Loaded</p>
                  <p className="text-lg font-semibold text-green-600">{uploadStatus.patients_count}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
        <div className="flex items-center mb-4">
          <InformationCircleIcon className="h-6 w-6 text-blue-600 mr-3" />
          <h3 className="text-lg font-medium text-gray-900">Upload Instructions</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">
                1
              </div>
              <div>
                <p className="font-medium text-gray-900">Prepare Excel File</p>
                <p className="text-sm text-gray-600">Ensure your file has "EmployeeDetails" and "PatientDetails" sheets</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">
                2
              </div>
              <div>
                <p className="font-medium text-gray-900">Upload File</p>
                <p className="text-sm text-gray-600">Drag and drop or click to browse for your Excel file</p>
              </div>
            </div>
          </div>
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">
                3
              </div>
              <div>
                <p className="font-medium text-gray-900">Data Validation</p>
                <p className="text-sm text-gray-600">The system will validate and process your data</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">
                4
              </div>
              <div>
                <p className="font-medium text-gray-900">Start Using</p>
                <p className="text-sm text-gray-600">Create assignments and manage your rota</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* File Requirements */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <DocumentTextIcon className="h-5 w-5 text-gray-600 mr-2" />
          File Requirements
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-gray-900 mb-3">EmployeeDetails Sheet</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• EmployeeID, Name, Address, PostCode</li>
              <li>• Gender, Ethnicity, Religion</li>
              <li>• TransportMode, Qualification</li>
              <li>• LanguageSpoken, CertificateExpiryDate</li>
              <li>• EarliestStart, LatestEnd, Shifts</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 mb-3">PatientDetails Sheet</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• PatientID, PatientName, Address</li>
              <li>• Gender, Ethnicity, Religion</li>
              <li>• RequiredSupport, RequiredHoursOfSupport</li>
              <li>• Illness, RequiresMedication</li>
              <li>• EmergencyContact, LanguagePreference</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DataUpload;