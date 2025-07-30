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
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full mb-4">
          <CloudArrowUpIcon className="h-8 w-8 text-white" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Data</h1>
        <p className="text-lg text-gray-600">Upload employee and patient data to get started</p>
      </div>

      {/* Upload Area */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* File Upload Area */}
          <div
            className={`relative border-2 border-dashed rounded-2xl p-12 transition-all duration-300 ${
              dragActive 
                ? 'border-blue-400 bg-blue-50 shadow-lg' 
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
                  <div className="h-16 w-16 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center">
                    <CheckCircleIcon className="h-8 w-8 text-white" />
                  </div>
                ) : (
                  <div className="h-16 w-16 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full flex items-center justify-center">
                    <CloudArrowUpIcon className="h-8 w-8 text-white" />
                  </div>
                )}
              </div>
              
              <div className="mt-4">
                <label htmlFor="file-upload" className="cursor-pointer">
                  <span className="mt-2 block text-lg font-semibold text-gray-900">
                    {file ? file.name : 'Drop your Excel file here or click to browse'}
                  </span>
                  <span className="mt-2 block text-sm text-gray-500">
                    {file ? 'File selected successfully' : 'Supports .xlsx and .xls files'}
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
                <div className="mt-4">
                  <ArrowDownTrayIcon className="mx-auto h-8 w-8 text-gray-400 animate-bounce" />
                </div>
              )}
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-center">
            <button
              type="submit"
              disabled={!file || loading}
              className={`group relative px-8 py-4 rounded-xl text-white font-semibold transition-all duration-200 shadow-lg ${
                !file || loading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 hover:shadow-xl transform hover:-translate-y-1'
              }`}
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="loading-spinner h-5 w-5 mr-2"></div>
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
        <div className="bg-red-50 border border-red-200 rounded-2xl p-6">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-6 w-6 text-red-600 mr-3" />
            <div>
              <h3 className="text-sm font-semibold text-red-800">Upload Error</h3>
              <p className="text-sm text-red-600 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {uploadStatus && (
        <div className="bg-green-50 border border-green-200 rounded-2xl p-6">
          <div className="flex items-center">
            <CheckCircleIcon className="h-6 w-6 text-green-600 mr-3" />
            <div>
              <h3 className="text-sm font-semibold text-green-800">Upload Successful!</h3>
              <p className="text-sm text-green-600 mt-1">{uploadStatus.message}</p>
              <div className="mt-3 grid grid-cols-2 gap-4">
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs text-gray-500">Employees Loaded</p>
                  <p className="text-lg font-bold text-green-600">{uploadStatus.employees_count}</p>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs text-gray-500">Patients Loaded</p>
                  <p className="text-lg font-bold text-green-600">{uploadStatus.patients_count}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-100">
        <div className="flex items-center mb-4">
          <InformationCircleIcon className="h-6 w-6 text-blue-600 mr-3" />
          <h3 className="text-lg font-semibold text-gray-900">Upload Instructions</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold mt-0.5">
                1
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Prepare Excel File</p>
                <p className="text-sm text-gray-600">Ensure your file has two sheets: "EmployeeDetails" and "PatientDetails"</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold mt-0.5">
                2
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Upload File</p>
                <p className="text-sm text-gray-600">Drag and drop or click to browse for your Excel file</p>
              </div>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold mt-0.5">
                3
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Data Validation</p>
                <p className="text-sm text-gray-600">The system will automatically validate and process your data</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold mt-0.5">
                4
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Start Using</p>
                <p className="text-sm text-gray-600">Once uploaded, you can create assignments and manage your rota</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* File Requirements */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <DocumentTextIcon className="h-5 w-5 mr-2 text-blue-600" />
          File Requirements
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">EmployeeDetails Sheet</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• EmployeeID, Name, Address, PostCode</li>
              <li>• Gender, Ethnicity, Religion</li>
              <li>• TransportMode, Qualification</li>
              <li>• LanguageSpoken, CertificateExpiryDate</li>
              <li>• EarliestStart, LatestEnd, Shifts</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 mb-2">PatientDetails Sheet</h4>
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
