import React, { useState } from 'react';
import { Bell, X, Check, AlertTriangle, TrendingUp, Activity, Users } from 'lucide-react';

interface NotificationCenterProps {
  notifications: any[];
  setNotifications: (notifications: any[]) => void;
}

const NotificationCenter: React.FC<NotificationCenterProps> = ({ notifications, setNotifications }) => {
  const [showNotifications, setShowNotifications] = useState(false);

  const markAsRead = (id: number) => {
    setNotifications(notifications.map(n => 
      n.id === id ? { ...n, read: true } : n
    ));
  };

  const markAllAsRead = () => {
    setNotifications(notifications.map(n => ({ ...n, read: true })));
  };

  const removeNotification = (id: number) => {
    setNotifications(notifications.filter(n => n.id !== id));
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'performance':
        return <TrendingUp className="h-5 w-5 text-green-400" />;
      case 'market':
        return <AlertTriangle className="h-5 w-5 text-yellow-400" />;
      case 'tactical':
        return <Activity className="h-5 w-5 text-blue-400" />;
      case 'player':
        return <Users className="h-5 w-5 text-purple-400" />;
      default:
        return <Bell className="h-5 w-5 text-slate-400" />;
    }
  };

  if (!showNotifications) {
    return (
      <button
        onClick={() => setShowNotifications(true)}
        className="fixed top-4 right-4 z-50 p-3 bg-slate-800 hover:bg-slate-700 rounded-full border border-slate-700 transition-colors"
      >
        <Bell className="h-6 w-6 text-white" />
        {notifications.filter(n => !n.read).length > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full px-2 py-1 min-w-[20px] text-center">
            {notifications.filter(n => !n.read).length}
          </span>
        )}
      </button>
    );
  }

  return (
    <div className="fixed top-4 right-4 z-50 w-96 bg-slate-800 rounded-xl border border-slate-700 shadow-2xl">
      <div className="p-4 border-b border-slate-700">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold flex items-center">
            <Bell className="h-5 w-5 mr-2 text-yellow-400" />
            Notifications
          </h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={markAllAsRead}
              className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
            >
              Mark all read
            </button>
            <button
              onClick={() => setShowNotifications(false)}
              className="p-1 hover:bg-slate-700 rounded transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="max-h-96 overflow-y-auto">
        {notifications.length === 0 ? (
          <div className="p-6 text-center text-slate-400">
            <Bell className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>No notifications</p>
          </div>
        ) : (
          <div className="space-y-1">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={`p-4 border-b border-slate-700 hover:bg-slate-700 transition-colors ${
                  !notification.read ? 'bg-slate-750' : ''
                }`}
              >
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 mt-1">
                    {getNotificationIcon(notification.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm ${!notification.read ? 'font-medium' : ''}`}>
                      {notification.message}
                    </p>
                    <p className="text-xs text-slate-400 mt-1">{notification.time}</p>
                  </div>
                  <div className="flex items-center space-x-1">
                    {!notification.read && (
                      <button
                        onClick={() => markAsRead(notification.id)}
                        className="p-1 hover:bg-slate-600 rounded transition-colors"
                        title="Mark as read"
                      >
                        <Check className="h-3 w-3 text-green-400" />
                      </button>
                    )}
                    <button
                      onClick={() => removeNotification(notification.id)}
                      className="p-1 hover:bg-slate-600 rounded transition-colors"
                      title="Remove"
                    >
                      <X className="h-3 w-3 text-red-400" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {notifications.length > 0 && (
        <div className="p-3 border-t border-slate-700">
          <button className="w-full text-sm text-blue-400 hover:text-blue-300 transition-colors">
            View all notifications
          </button>
        </div>
      )}
    </div>
  );
};

export default NotificationCenter;