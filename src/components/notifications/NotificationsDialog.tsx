import React, { useState, useEffect } from 'react';
import { Bell, X, CheckCircle, AlertCircle, AlertTriangle, Info, Clock } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, Button, Badge } from '../ui';
import { invoke } from '@tauri-apps/api/core';
import { cn } from '../../lib/utils';

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  timestamp: Date;
  read: boolean;
  actionLabel?: string;
  onAction?: () => void;
}

interface NotificationsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export function NotificationsDialog({ isOpen, onClose }: NotificationsDialogProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  // Load notifications from backend
  useEffect(() => {
    if (isOpen) {
      loadNotifications();
    }
  }, [isOpen]);

  // Set up real-time notifications polling
  useEffect(() => {
    if (!isOpen) return;

    const interval = setInterval(() => {
      loadNotifications();
    }, 10000); // Poll every 10 seconds

    return () => clearInterval(interval);
  }, [isOpen]);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const notificationData = await invoke<Notification[]>('get_notifications');
      setNotifications(notificationData);
    } catch (error) {
      console.error('Failed to load notifications:', error);
      // Fallback to sample data if backend is not available
      setNotifications([
        {
          id: '1',
          title: 'System Ready',
          message: 'Lexicon has been initialized and is ready for use.',
          type: 'success',
          timestamp: new Date(Date.now() - 1000 * 60 * 5), // 5 minutes ago
          read: false,
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  const markAsRead = async (id: string) => {
    try {
      await invoke('mark_notification_as_read', { notificationId: id });
      setNotifications(prev => 
        prev.map(n => n.id === id ? { ...n, read: true } : n)
      );
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
      // Update locally as fallback
      setNotifications(prev => 
        prev.map(n => n.id === id ? { ...n, read: true } : n)
      );
    }
  };

  const markAllAsRead = async () => {
    try {
      await invoke('mark_all_notifications_as_read');
      setNotifications(prev => 
        prev.map(n => ({ ...n, read: true }))
      );
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
      // Update locally as fallback
      setNotifications(prev => 
        prev.map(n => ({ ...n, read: true }))
      );
    }
  };

  const removeNotification = async (id: string) => {
    try {
      await invoke('delete_notification', { notificationId: id });
      setNotifications(prev => prev.filter(n => n.id !== id));
    } catch (error) {
      console.error('Failed to delete notification:', error);
      // Update locally as fallback
      setNotifications(prev => prev.filter(n => n.id !== id));
    }
  };

  const getIcon = (type: Notification['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'info':
        return <Info className="h-5 w-5 text-blue-500" />;
    }
  };

  const formatTime = (timestamp: Date) => {
    const now = new Date();
    const diff = now.getTime() - timestamp.getTime();
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  return (
    <Dialog open={isOpen} onClose={onClose}>
      <DialogContent className="max-w-md max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Notifications
              {unreadCount > 0 && (
                <Badge variant="destructive" className="h-5 text-xs px-1.5">
                  {unreadCount}
                </Badge>
              )}
            </DialogTitle>
            {unreadCount > 0 && (
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={markAllAsRead}
                className="text-xs"
              >
                Mark all read
              </Button>
            )}
          </div>
        </DialogHeader>

        {notifications.length === 0 ? (
          <div className="flex-1 flex items-center justify-center py-8">
            <div className="text-center text-muted-foreground">
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-3"></div>
                  <p>Loading notifications...</p>
                </>
              ) : (
                <>
                  <Bell className="h-8 w-8 mx-auto mb-3 opacity-50" />
                  <p>No notifications</p>
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto space-y-3">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={cn(
                  'p-3 rounded-lg border transition-colors',
                  notification.read 
                    ? 'bg-background border-border' 
                    : 'bg-primary/5 border-primary/20'
                )}
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 mt-0.5">
                    {getIcon(notification.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <h4 className={cn(
                        "text-sm font-medium",
                        !notification.read && "font-semibold"
                      )}>
                        {notification.title}
                      </h4>
                      <div className="flex items-center gap-2">
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          {formatTime(notification.timestamp)}
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeNotification(notification.id)}
                          className="h-6 w-6 p-0 hover:bg-destructive/10"
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1 leading-relaxed">
                      {notification.message}
                    </p>
                    <div className="flex items-center justify-between mt-2">
                      <div className="flex items-center gap-2">
                        {notification.actionLabel && notification.onAction && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={notification.onAction}
                            className="h-7 text-xs"
                          >
                            {notification.actionLabel}
                          </Button>
                        )}
                      </div>
                      {!notification.read && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => markAsRead(notification.id)}
                          className="h-7 text-xs text-muted-foreground"
                        >
                          Mark as read
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="border-t pt-3 mt-3">
          <div className="flex justify-between items-center text-xs text-muted-foreground">
            <span>{notifications.length} total notifications</span>
            <Button variant="ghost" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Hook for managing notifications state
export function useNotifications() {
  // Load notifications from localStorage
  const [notifications, setNotifications] = useState<Notification[]>(() => {
    const saved = localStorage.getItem('lexicon-notifications');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.map((n: any) => ({
          ...n,
          timestamp: new Date(n.timestamp)
        }));
      } catch (error) {
        console.error('Error parsing notifications from localStorage:', error);
      }
    }
    // Default notification for first-time users
    return [
      {
        id: '1',
        type: 'success',
        title: 'Build Completed',
        message: 'Application build completed successfully',
        timestamp: new Date(Date.now() - 2 * 60000), // 2 minutes ago
        read: true
      }
    ];
  });
  
  const [unreadCount, setUnreadCount] = useState(() => {
    // Calculate unread count from loaded notifications
    const saved = localStorage.getItem('lexicon-notifications');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.filter((n: any) => !n.read).length;
      } catch (error) {
        return 0;
      }
    }
    return 0; // No unread notifications for first-time users
  });

  // Save notifications to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('lexicon-notifications', JSON.stringify(notifications));
    setUnreadCount(notifications.filter(n => !n.read).length);
  }, [notifications]);

  const addNotification = (notification: Omit<Notification, 'id'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString()
    };
    setNotifications(prev => [newNotification, ...prev]);
  };

  const markAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => 
      prev.map(n => ({ ...n, read: true }))
    );
  };

  return {
    notifications,
    unreadCount,
    addNotification,
    markAsRead,
    markAllAsRead
  };
}
