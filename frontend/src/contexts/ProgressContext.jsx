import { createContext, useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import websocketService from '../services/websocketService';
import useStore from '../store/useStore';

const ProgressContext = createContext();

export const useProgress = () => {
  const context = useContext(ProgressContext);
  if (!context) {
    throw new Error('useProgress must be used within a ProgressProvider');
  }
  return context;
};

export const ProgressProvider = ({ children }) => {
  const [activeTasks, setActiveTasks] = useState(new Map());
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [filterType, setFilterType] = useState('all'); // all, unread, read, deleted
  const navigate = useNavigate();
  const { 
    fetchNotifications, 
    fetchUnreadNotificationsCount,
    markNotificationRead,
    markNotificationDeleted,
    markAllNotificationsRead,
    deleteAllNotifications
  } = useStore();

  useEffect(() => {
    // Connect to WebSocket on mount
    websocketService.connect().catch(console.error);

    // Load notifications from database
    loadNotifications();
    loadUnreadCount();

    // Add progress update listener
    const handleProgressUpdate = (data) => {
      const { task_id, data: taskData } = data;
      
      setActiveTasks(prev => {
        const newTasks = new Map(prev);
        newTasks.set(task_id, taskData);
        return newTasks;
      });

      // Handle task completion
      if (taskData.status === 'completed') {
        handleTaskCompletion(task_id, taskData);
      } else if (taskData.status === 'failed') {
        handleTaskFailure(task_id, taskData);
      }
    };

    websocketService.addListener('progress_update', handleProgressUpdate);

    // Cleanup on unmount
    return () => {
      websocketService.removeListener('progress_update', handleProgressUpdate);
      websocketService.disconnect();
    };
  }, []);

  const loadNotifications = async () => {
    try {
      const dbNotifications = await fetchNotifications(false, 100);
      setNotifications(dbNotifications);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  };

  const loadUnreadCount = async () => {
    try {
      const count = await fetchUnreadNotificationsCount();
      setUnreadCount(count);
    } catch (error) {
      console.error('Failed to load unread count:', error);
    }
  };

  const handleTaskCompletion = async (taskId, taskData) => {
    const taskType = taskData.type;
    const result = taskData.result;

    // Reload notifications from database
    await loadNotifications();
    await loadUnreadCount();

    // Show toast
    toast.success(
      <div>
        <div className="font-medium">{getTaskTitle(taskType)}</div>
        <div className="text-sm text-gray-600">{getTaskMessage(taskType, result)}</div>
      </div>,
      {
        duration: 5000,
        onClick: () => navigateToTaskResult(taskType, result),
        style: {
          cursor: 'pointer'
        }
      }
    );

    // Remove from active tasks after a delay
    setTimeout(() => {
      setActiveTasks(prev => {
        const newTasks = new Map(prev);
        newTasks.delete(taskId);
        return newTasks;
      });
    }, 3000);
  };

  const handleTaskFailure = async (taskId, taskData) => {
    const taskType = taskData.type;
    const error = taskData.error;

    // Reload notifications from database
    await loadNotifications();
    await loadUnreadCount();

    // Show toast
    toast.error(
      <div>
        <div className="font-medium">{getTaskTitle(taskType)} Failed</div>
        <div className="text-sm text-gray-600">{error || 'An error occurred during processing'}</div>
      </div>,
      {
        duration: 5000
      }
    );

    // Remove from active tasks after a delay
    setTimeout(() => {
      setActiveTasks(prev => {
        const newTasks = new Map(prev);
        newTasks.delete(taskId);
        return newTasks;
      });
    }, 3000);
  };

  const getTaskTitle = (taskType) => {
    switch (taskType) {
      case 'weekly_rota':
        return 'Weekly Rota Generated';
      case 'create_assignment':
        return 'Assignment Created';
      default:
        return 'Task Completed';
    }
  };

  const getTaskMessage = (taskType, result) => {
    switch (taskType) {
      case 'weekly_rota':
        const assignmentCount = result?.assignments?.length || 0;
        return `Successfully generated ${assignmentCount} assignments for the week`;
      case 'create_assignment':
        const assignment = result?.assignment;
        if (assignment) {
          return `${assignment.employee_name} assigned to ${assignment.patient_name}`;
        }
        return 'Assignment created successfully';
      default:
        return 'Task completed successfully';
    }
  };

  const navigateToTaskResult = (taskType, result) => {
    switch (taskType) {
      case 'weekly_rota':
        navigate('/assignments');
        break;
      case 'create_assignment':
        navigate('/assignments');
        break;
      default:
        navigate('/');
    }
  };

  const handleNotificationClick = async (notification) => {
    // Mark as read if not already read
    if (!notification.is_read) {
      await markNotificationRead(notification.notification_id);
      setUnreadCount(prev => Math.max(0, prev - 1));
    }

    // Handle action if present
    if (notification.action_type === 'navigate' && notification.action_data?.route) {
      navigate(notification.action_data.route);
    }
  };

  const handleNotificationDelete = async (notificationId) => {
    await markNotificationDeleted(notificationId);
    // Reload notifications to reflect the change
    await loadNotifications();
  };

  const handleMarkAllRead = async () => {
    await markAllNotificationsRead();
    setUnreadCount(0);
    // Reload notifications to reflect the change
    await loadNotifications();
  };

  const handleDeleteAll = async () => {
    await deleteAllNotifications();
    // Reload notifications to reflect the change
    await loadNotifications();
  };

  const getFilteredNotifications = () => {
    switch (filterType) {
      case 'unread':
        return notifications.filter(n => !n.is_read && !n.is_deleted);
      case 'read':
        return notifications.filter(n => n.is_read && !n.is_deleted);
      case 'deleted':
        return notifications.filter(n => n.is_deleted);
      default:
        return notifications.filter(n => !n.is_deleted);
    }
  };

  const getActiveTask = (taskType) => {
    for (const [taskId, task] of activeTasks) {
      if (task.type === taskType && task.status === 'in_progress') {
        return { taskId, ...task };
      }
    }
    return null;
  };

  const value = {
    activeTasks: Array.from(activeTasks.values()),
    notifications: getFilteredNotifications(),
    unreadCount,
    filterType,
    setFilterType,
    getActiveTask,
    handleNotificationClick,
    handleNotificationDelete,
    handleMarkAllRead,
    handleDeleteAll,
    refreshNotifications: loadNotifications
  };

  return (
    <ProgressContext.Provider value={value}>
      {children}
    </ProgressContext.Provider>
  );
}; 