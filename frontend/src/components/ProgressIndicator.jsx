import { useState, useEffect } from 'react';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  ClockIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const ProgressIndicator = ({ task, onClose }) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    // Auto-hide after completion with delay
    if (task.status === 'completed' || task.status === 'failed') {
      const timer = setTimeout(() => {
        setIsVisible(false);
        setTimeout(() => onClose?.(), 300); // Allow animation to complete
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [task.status, onClose]);

  if (!isVisible) return null;

  const getStatusIcon = () => {
    switch (task.status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-600" />;
      case 'failed':
        return <ExclamationTriangleIcon className="w-5 h-5 text-red-600" />;
      default:
        return <ClockIcon className="w-5 h-5 text-blue-600 animate-spin" />;
    }
  };

  const getStatusColor = () => {
    switch (task.status) {
      case 'completed':
        return 'border-green-200 bg-green-50';
      case 'failed':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-blue-200 bg-blue-50';
    }
  };

  const getProgressColor = () => {
    switch (task.status) {
      case 'completed':
        return 'bg-green-600';
      case 'failed':
        return 'bg-red-600';
      default:
        return 'bg-blue-600';
    }
  };

  const getTaskTitle = (taskType) => {
    switch (taskType) {
      case 'weekly_rota':
        return 'Generating Weekly Rota';
      case 'create_assignment':
        return 'Creating Assignment';
      default:
        return 'Processing Task';
    }
  };

  return (
    <div className={`fixed bottom-4 right-4 w-80 border rounded-lg shadow-lg transition-all duration-300 ${getStatusColor()}`}>
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            {getStatusIcon()}
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-medium text-gray-900">
                {getTaskTitle(task.type)}
              </h4>
              <p className="text-xs text-gray-600 mt-1">
                {task.current_step || task.description}
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              setIsVisible(false);
              setTimeout(() => onClose?.(), 300);
            }}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XMarkIcon className="w-4 h-4" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="mt-3">
          <div className="flex justify-between text-xs text-gray-600 mb-1">
            <span>Progress</span>
            <span>{task.progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${getProgressColor()}`}
              style={{ width: `${task.progress}%` }}
            />
          </div>
        </div>

        {/* Status */}
        <div className="mt-2 flex items-center justify-between">
          <span className={`text-xs font-medium ${
            task.status === 'completed' ? 'text-green-700' :
            task.status === 'failed' ? 'text-red-700' :
            'text-blue-700'
          }`}>
            {task.status === 'completed' ? 'Completed' :
             task.status === 'failed' ? 'Failed' :
             'In Progress'}
          </span>
          {task.total_steps > 0 && (
            <span className="text-xs text-gray-500">
              Step {Math.ceil((task.progress / 100) * task.total_steps)} of {task.total_steps}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProgressIndicator; 