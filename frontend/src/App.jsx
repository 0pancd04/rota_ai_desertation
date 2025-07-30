import { useState } from 'react';
import Dashboard from './pages/Dashboard';
import DataUpload from './pages/DataUpload';
import Employees from './pages/Employees';
import Patients from './pages/Patients';
import Assignments from './pages/Assignments';
import CreateAssignment from './pages/CreateAssignment';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'upload':
        return <DataUpload />;
      case 'employees':
        return <Employees />;
      case 'patients':
        return <Patients />;
      case 'assignments':
        return <Assignments />;
      case 'create-assignment':
        return <CreateAssignment />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-3xl font-bold text-gray-900">
              Healthcare Rota System
            </h1>
            <p className="text-sm text-gray-500">
              AI-Powered Staff Assignment
            </p>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-blue-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`py-4 px-3 text-sm font-medium ${
                activeTab === 'dashboard'
                  ? 'text-white border-b-2 border-white'
                  : 'text-blue-200 hover:text-white'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab('upload')}
              className={`py-4 px-3 text-sm font-medium ${
                activeTab === 'upload'
                  ? 'text-white border-b-2 border-white'
                  : 'text-blue-200 hover:text-white'
              }`}
            >
              Upload Data
            </button>
            <button
              onClick={() => setActiveTab('employees')}
              className={`py-4 px-3 text-sm font-medium ${
                activeTab === 'employees'
                  ? 'text-white border-b-2 border-white'
                  : 'text-blue-200 hover:text-white'
              }`}
            >
              Employees
            </button>
            <button
              onClick={() => setActiveTab('patients')}
              className={`py-4 px-3 text-sm font-medium ${
                activeTab === 'patients'
                  ? 'text-white border-b-2 border-white'
                  : 'text-blue-200 hover:text-white'
              }`}
            >
              Patients
            </button>
            <button
              onClick={() => setActiveTab('assignments')}
              className={`py-4 px-3 text-sm font-medium ${
                activeTab === 'assignments'
                  ? 'text-white border-b-2 border-white'
                  : 'text-blue-200 hover:text-white'
              }`}
            >
              Assignments
            </button>
            <button
              onClick={() => setActiveTab('create-assignment')}
              className={`py-4 px-3 text-sm font-medium ${
                activeTab === 'create-assignment'
                  ? 'text-white border-b-2 border-white'
                  : 'text-blue-200 hover:text-white'
              }`}
            >
              Create Assignment
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderContent()}
      </main>
    </div>
  );
}

export default App;
