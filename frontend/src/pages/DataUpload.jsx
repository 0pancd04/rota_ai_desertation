import { useState } from 'react';
import useStore from '../store/useStore';
import { CloudArrowUpIcon } from '@heroicons/react/24/outline';

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
    <div>
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Upload Data</h2>

      <div className="max-w-3xl mx-auto">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* File Upload Area */}
          <div
            className={`relative border-2 border-dashed rounded-lg p-6 ${
              dragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div className="text-center">
              <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
              <div className="mt-4">
                <label htmlFor="file-upload" className="cursor-pointer">
                  <span className="mt-2 block text-sm font-medium text-gray-900">
                    {file ? file.name : 'Drop your Excel file here or click to browse'}
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
              <p className="text-xs text-gray-500 mt-2">
                Excel files only (.xlsx, .xls)
              </p>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-center">
            <button
              type="submit"
              disabled={!file || loading}
              className={`px-6 py-3 rounded-md text-white font-medium ${
                !file || loading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {loading ? 'Uploading...' : 'Upload File'}
            </button>
          </div>
        </form>

        {/* Status Messages */}
        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {uploadStatus && (
          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm text-green-600 font-medium">{uploadStatus.message}</p>
            <div className="mt-2 text-sm text-gray-600">
              <p>Employees loaded: {uploadStatus.employees_count}</p>
              <p>Patients loaded: {uploadStatus.patients_count}</p>
            </div>
          </div>
        )}

        {/* Instructions */}
        <div className="mt-8 bg-gray-50 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Instructions</h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li>• Upload an Excel file containing employee and patient data</li>
            <li>• The file must have two sheets: "EmployeeDetails" and "PatientDetails"</li>
            <li>• Ensure all required fields are filled according to the template</li>
            <li>• The system will validate and process the data automatically</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default DataUpload;
