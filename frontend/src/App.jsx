import { useState } from 'react';
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Dashboard from './pages/Dashboard';
import DataUpload from './pages/DataUpload';
import Employees from './pages/Employees';
import Patients from './pages/Patients';
import Assignments from './pages/Assignments';
import CreateAssignment from './pages/CreateAssignment';
import { ProgressProvider, useProgress } from './contexts/ProgressContext';
import ProgressIndicator from './components/ProgressIndicator';
import NotificationTray from './components/NotificationTray';
import { 
  HomeIcon, 
  CloudArrowUpIcon, 
  UserGroupIcon, 
  UserIcon, 
  ClipboardDocumentListIcon,
  PlusCircleIcon,
  Bars3Icon,
  XMarkIcon
} from '@heroicons/react/24/outline';

function AppContent() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { 
    activeTasks, 
    notifications, 
    unreadCount,
    filterType,
    setFilterType,
    handleNotificationClick,
    handleNotificationDelete,
    handleMarkAllRead,
    handleDeleteAll
  } = useProgress();

  const navigation = [
    { 
      name: 'Dashboard', 
      href: '/', 
      icon: HomeIcon,
      current: location.pathname === '/'
    },
    { 
      name: 'Upload Data', 
      href: '/upload', 
      icon: CloudArrowUpIcon,
      current: location.pathname === '/upload'
    },
    { 
      name: 'Employees', 
      href: '/employees', 
      icon: UserGroupIcon,
      current: location.pathname === '/employees'
    },
    { 
      name: 'Patients', 
      href: '/patients', 
      icon: UserIcon,
      current: location.pathname === '/patients'
    },
    { 
      name: 'Assignments', 
      href: '/assignments', 
      icon: ClipboardDocumentListIcon,
      current: location.pathname === '/assignments'
    },
    { 
      name: 'Create Assignment', 
      href: '/create-assignment', 
      icon: PlusCircleIcon,
      current: location.pathname === '/create-assignment'
    },
  ];

  const handleNavigation = (href) => {
    navigate(href);
    setSidebarOpen(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="fixed inset-0 bg-gray-900/50" onClick={() => setSidebarOpen(false)} />
          <div className="fixed inset-y-0 left-0 flex w-64 flex-col bg-white shadow-xl">
            <div className="flex h-16 items-center justify-between px-6 border-b border-gray-200">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-white font-bold text-sm">HR</span>
                </div>
                <span className="text-lg font-semibold text-gray-900">Healthcare Rota</span>
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                className="text-gray-400 hover:text-gray-600 w-6 h-6 flex-shrink-0"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
            <nav className="flex-1 space-y-1 px-4 py-4">
              {navigation.map((item) => (
                <button
                  key={item.name}
                  onClick={() => handleNavigation(item.href)}
                  className={`group flex items-center w-full px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    item.current
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <item.icon className={`w-5 h-5 mr-3 flex-shrink-0 ${
                    item.current ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-500'
                  }`} />
                  {item.name}
                </button>
              ))}
            </nav>
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-grow bg-white shadow-sm border-r border-gray-200">
          <div className="flex h-16 items-center px-6 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
                <span className="text-white font-bold text-sm">HR</span>
              </div>
              <span className="text-lg font-semibold text-gray-900">Healthcare Rota</span>
            </div>
          </div>
          <nav className="flex-1 space-y-1 px-4 py-4">
            {navigation.map((item) => (
              <button
                key={item.name}
                onClick={() => handleNavigation(item.href)}
                className={`group flex items-center w-full px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                  item.current
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <item.icon className={`w-5 h-5 mr-3 flex-shrink-0 ${
                  item.current ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-500'
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
        <div className="sticky top-0 z-40 bg-white shadow-sm border-b border-gray-200">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden text-gray-500 hover:text-gray-700 w-6 h-6 flex-shrink-0"
              >
                <Bars3Icon className="w-6 h-6" />
              </button>
              <h1 className="text-xl font-semibold text-gray-900">
                {navigation.find(item => item.href === location.pathname)?.name || 'Dashboard'}
              </h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 bg-green-50 px-3 py-1 rounded-full">
                <div className="w-2 h-2 bg-green-400 rounded-full flex-shrink-0"></div>
                <span className="text-sm text-green-700 font-medium">Online</span>
              </div>
              
              {/* Notification Tray */}
              <NotificationTray
                notifications={notifications}
                unreadCount={unreadCount}
                filterType={filterType}
                setFilterType={setFilterType}
                onNotificationClick={handleNotificationClick}
                onNotificationDelete={handleNotificationDelete}
                onMarkAllRead={handleMarkAllRead}
                onDeleteAll={handleDeleteAll}
              />
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="py-8">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/upload" element={<DataUpload />} />
              <Route path="/employees" element={<Employees />} />
              <Route path="/patients" element={<Patients />} />
              <Route path="/assignments" element={<Assignments />} />
              <Route path="/create-assignment" element={<CreateAssignment />} />
            </Routes>
          </div>
        </main>
      </div>

      {/* Progress Indicators */}
      {activeTasks.map((task) => (
        <ProgressIndicator
          key={task.id}
          task={task}
          onClose={() => {
            // Task will be automatically removed by the context
          }}
        />
      ))}

      {/* Toast Notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 5000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 5000,
            iconTheme: {
              primary: '#10B981',
              secondary: '#fff',
            },
          },
          error: {
            duration: 5000,
            iconTheme: {
              primary: '#EF4444',
              secondary: '#fff',
            },
          },
        }}
      />
    </div>
  );
}

function App() {
  return (
    <ProgressProvider>
      <AppContent />
    </ProgressProvider>
  );
}

export default App;