import { useState } from 'react';
import { 
  BellIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  XMarkIcon,
  TrashIcon,
  FunnelIcon,
  CheckIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';

const NotificationTray = ({ 
  notifications, 
  unreadCount,
  filterType,
  setFilterType,
  onNotificationClick, 
  onNotificationDelete, 
  onMarkAllRead,
  onDeleteAll 
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircleIcon className="w-5 h-5 text-green-600" />;
      case 'error':
        return <ExclamationTriangleIcon className="w-5 h-5 text-red-600" />;
      default:
        return <CheckCircleIcon className="w-5 h-5 text-blue-600" />;
    }
  };

  const getNotificationColor = (type) => {
    switch (type) {
      case 'success':
        return 'border-green-200 bg-green-50';
      case 'error':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-blue-200 bg-blue-50';
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInMinutes = Math.floor((now - date) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return date.toLocaleDateString();
  };

  const getFilterOptions = () => [
    { value: 'all', label: 'All', count: notifications.length },
    { value: 'unread', label: 'Unread', count: unreadCount },
    { value: 'read', label: 'Read', count: notifications.filter(n => n.is_read && !n.is_deleted).length },
    { value: 'deleted', label: 'Deleted', count: notifications.filter(n => n.is_deleted).length }
  ];

  const handleNotificationClick = (notification) => {
    onNotificationClick(notification);
    // Don't close the tray when clicking on a notification
  };

  const handleFilterChange = (newFilterType) => {
    setFilterType(newFilterType);
  };

  return (
    <div className="relative">
      {/* Notification Bell */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 transition-colors"
      >
        <BellIcon className="w-6 h-6" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Notification Panel */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Panel */}
          <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
            {/* Header */}
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-medium text-gray-900">Notifications</h3>
                <div className="flex items-center space-x-2">
                  {notifications.length > 0 && (
                    <>
                      <button
                        onClick={onMarkAllRead}
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                        title="Mark all as read"
                      >
                        <CheckIcon className="w-4 h-4" />
                      </button>
                      <button
                        onClick={onDeleteAll}
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                        title="Delete all notifications"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </>
                  )}
                  <button
                    onClick={() => setIsOpen(false)}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <XMarkIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Filter Tabs */}
              <div className="flex space-x-1">
                {getFilterOptions().map((option) => (
                  <button
                    key={option.value}
                    onClick={() => handleFilterChange(option.value)}
                    className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                      filterType === option.value
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    {option.label}
                    {option.count > 0 && (
                      <span className="ml-1 bg-gray-200 text-gray-700 px-1.5 py-0.5 rounded-full text-xs">
                        {option.count}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Notifications List */}
            <div className="max-h-96 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="p-6 text-center">
                  <BellIcon className="mx-auto w-8 h-8 text-gray-400 mb-2" />
                  <p className="text-gray-500 text-sm">
                    {filterType === 'all' ? 'No notifications' : `No ${filterType} notifications`}
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {notifications.map((notification) => (
                    <div
                      key={notification.notification_id}
                      className={`p-4 hover:bg-gray-50 transition-colors ${
                        notification.action_type ? 'cursor-pointer' : 'cursor-default'
                      } ${!notification.is_read ? 'bg-blue-50' : ''}`}
                      onClick={() => handleNotificationClick(notification)}
                    >
                      <div className="flex items-start space-x-3">
                        {getNotificationIcon(notification.type)}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <h4 className="text-sm font-medium text-gray-900">
                                {notification.title}
                              </h4>
                              {!notification.is_read && (
                                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                              )}
                            </div>
                            <div className="flex items-center space-x-1">
                              {notification.action_type && (
                                <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded">
                                  Click to view
                                </span>
                              )}
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onNotificationDelete(notification.notification_id);
                                }}
                                className="text-gray-400 hover:text-gray-600 transition-colors"
                              >
                                <XMarkIcon className="w-3 h-3" />
                              </button>
                            </div>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">
                            {notification.message}
                          </p>
                          <div className="flex items-center justify-between mt-2">
                            <p className="text-xs text-gray-400">
                              {formatTimestamp(notification.created_at)}
                            </p>
                            <div className="flex items-center space-x-2">
                              {notification.is_read ? (
                                <EyeIcon className="w-3 h-3 text-gray-400" />
                              ) : (
                                <EyeSlashIcon className="w-3 h-3 text-blue-500" />
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default NotificationTray; 