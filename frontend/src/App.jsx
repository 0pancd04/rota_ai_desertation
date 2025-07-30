import { useState } from 'react';
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import DataUpload from './pages/DataUpload';
import Employees from './pages/Employees';
import Patients from './pages/Patients';
import Assignments from './pages/Assignments';
import CreateAssignment from './pages/CreateAssignment';
import { 
  HomeIcon, 
  CloudArrowUpIcon, 
  UserGroupIcon, 
  UserIcon, 
  ClipboardDocumentListIcon,
  PlusCircleIcon,
  Bars3Icon,
  XMarkIcon,
  SignalIcon
} from '@heroicons/react/24/outline';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: HomeIcon, current: location.pathname === '/' },
    { name: 'Upload Data', href: '/upload', icon: CloudArrowUpIcon, current: location.pathname === '/upload' },
    { name: 'Employees', href: '/employees', icon: UserGroupIcon, current: location.pathname === '/employees' },
    { name: 'Patients', href: '/patients', icon: UserIcon, current: location.pathname === '/patients' },
    { name: 'Assignments', href: '/assignments', icon: ClipboardDocumentListIcon, current: location.pathname === '/assignments' },
    { name: 'Create Assignment', href: '/create-assignment', icon: PlusCircleIcon, current: location.pathname === '/create-assignment' },
  ];

  const handleNavigation = (href) => {
    navigate(href);
    setSidebarOpen(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Mobile sidebar */}
      <div className={`fixed inset-0 z-50 lg:hidden ${sidebarOpen ? 'block' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75 transition-opacity" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 flex w-64 flex-col bg-white/95 backdrop-blur-sm shadow-2xl transform transition-transform duration-300 ease-in-out">
          <div className="flex h-16 items-center justify-between px-6 border-b border-gray-200">
            <div className="flex items-center">
              <div className="h-8 w-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center shadow-lg">
                <HomeIcon className="h-5 w-5 text-white" />
              </div>
              <h1 className="ml-3 text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">Healthcare Rota</h1>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="text-gray-400 hover:text-gray-600 transition-colors duration-200 p-1 rounded-lg hover:bg-gray-100"
              aria-label="Close sidebar"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
          <nav className="flex-1 space-y-1 px-4 py-4">
            {navigation.map((item) => (
              <button
                key={item.name}
                onClick={() => handleNavigation(item.href)}
                className={`group flex items-center px-3 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                  item.current
                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg'
                    : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                }`}
                aria-current={item.current ? 'page' : undefined}
              >
                <item.icon className={`mr-3 h-5 w-5 flex-shrink-0 ${
                  item.current ? 'text-white' : 'text-gray-400 group-hover:text-gray-500'
                }`} />
                {item.name}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-grow bg-white/95 backdrop-blur-sm shadow-2xl border-r border-gray-200">
          <div className="flex h-16 items-center px-6 border-b border-gray-200">
            <div className="flex items-center">
              <div className="h-8 w-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center shadow-lg">
                <HomeIcon className="h-5 w-5 text-white" />
              </div>
              <h1 className="ml-3 text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">Healthcare Rota</h1>
            </div>
          </div>
          <nav className="flex-1 space-y-1 px-4 py-4">
            {navigation.map((item) => (
              <button
                key={item.name}
                onClick={() => handleNavigation(item.href)}
                className={`group flex items-center px-3 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                  item.current
                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg'
                    : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                }`}
                aria-current={item.current ? 'page' : undefined}
              >
                <item.icon className={`mr-3 h-5 w-5 flex-shrink-0 ${
                  item.current ? 'text-white' : 'text-gray-400 group-hover:text-gray-500'
                }`} />
                {item.name}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <div className="sticky top-0 z-40 bg-white/80 backdrop-blur-sm border-b border-gray-200 shadow-sm">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
            <div className="flex items-center">
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden text-gray-500 hover:text-gray-700 transition-colors duration-200 p-2 rounded-lg hover:bg-gray-100"
                aria-label="Open sidebar"
              >
                <Bars3Icon className="h-6 w-6" />
              </button>
              <div className="hidden sm:block ml-4">
                <h2 className="text-lg font-semibold text-gray-900">
                  {navigation.find(item => item.href === location.pathname)?.name || 'Dashboard'}
                </h2>
                <p className="text-sm text-gray-500">Healthcare Rota Management</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 bg-green-50 px-3 py-2 rounded-full border border-green-200 shadow-sm">
                <div className="h-2 w-2 bg-green-400 rounded-full status-pulse"></div>
                <span className="text-sm text-green-700 font-medium">System Online</span>
              </div>
              <div className="hidden sm:flex items-center space-x-2 text-sm text-gray-500">
                <SignalIcon className="h-4 w-4" />
                <span>AI-Powered</span>
              </div>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="py-8">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-6">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/upload" element={<DataUpload />} />
                <Route path="/employees" element={<Employees />} />
                <Route path="/patients" element={<Patients />} />
                <Route path="/assignments" element={<Assignments />} />
                <Route path="/create-assignment" element={<CreateAssignment />} />
              </Routes>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
