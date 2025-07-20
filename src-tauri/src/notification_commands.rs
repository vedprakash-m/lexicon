use tauri::{State, command};
use std::sync::Arc;
use tokio::sync::Mutex;
use uuid::Uuid;
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use log::{info, error};

/// Notification types
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum NotificationType {
    Success,
    Error,
    Warning,
    Info,
}

/// Notification structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Notification {
    pub id: String,
    pub title: String,
    pub message: String,
    #[serde(rename = "type")]
    pub notification_type: NotificationType,
    pub timestamp: DateTime<Utc>,
    pub read: bool,
    #[serde(rename = "actionLabel")]
    pub action_label: Option<String>,
}

/// Notification manager for handling system notifications
#[derive(Debug)]
pub struct NotificationManager {
    notifications: Vec<Notification>,
}

impl NotificationManager {
    pub fn new() -> Self {
        Self {
            notifications: Vec::new(),
        }
    }

    pub fn add_notification(&mut self, title: String, message: String, notification_type: NotificationType) -> String {
        let notification = Notification {
            id: Uuid::new_v4().to_string(),
            title,
            message,
            notification_type,
            timestamp: Utc::now(),
            read: false,
            action_label: None,
        };

        let id = notification.id.clone();
        self.notifications.push(notification);
        
        // Keep only the last 100 notifications
        if self.notifications.len() > 100 {
            self.notifications.remove(0);
        }

        id
    }

    pub fn get_all_notifications(&self) -> Vec<Notification> {
        self.notifications.clone()
    }

    pub fn mark_as_read(&mut self, id: &str) -> bool {
        if let Some(notification) = self.notifications.iter_mut().find(|n| n.id == id) {
            notification.read = true;
            true
        } else {
            false
        }
    }

    pub fn mark_all_as_read(&mut self) {
        for notification in &mut self.notifications {
            notification.read = true;
        }
    }

    pub fn delete_notification(&mut self, id: &str) -> bool {
        if let Some(pos) = self.notifications.iter().position(|n| n.id == id) {
            self.notifications.remove(pos);
            true
        } else {
            false
        }
    }

    pub fn get_unread_count(&self) -> usize {
        self.notifications.iter().filter(|n| !n.read).count()
    }
}

impl Default for NotificationManager {
    fn default() -> Self {
        let mut manager = Self::new();
        
        // Add some initial notifications
        manager.add_notification(
            "System Initialized".to_string(),
            "Lexicon has been successfully initialized and is ready for use.".to_string(),
            NotificationType::Success,
        );

        manager.add_notification(
            "Environment Ready".to_string(),
            "Python environment is configured and all dependencies are installed.".to_string(),
            NotificationType::Info,
        );

        manager
    }
}

/// Shared notification manager state
pub type NotificationManagerState = Arc<Mutex<NotificationManager>>;

/// Get all notifications
#[command]
pub async fn get_notifications(
    notification_manager: State<'_, NotificationManagerState>
) -> Result<Vec<Notification>, String> {
    let manager = notification_manager.lock().await;
    Ok(manager.get_all_notifications())
}

/// Mark a notification as read
#[command]
pub async fn mark_notification_as_read(
    notification_id: String,
    notification_manager: State<'_, NotificationManagerState>
) -> Result<bool, String> {
    let mut manager = notification_manager.lock().await;
    Ok(manager.mark_as_read(&notification_id))
}

/// Mark all notifications as read
#[command]
pub async fn mark_all_notifications_as_read(
    notification_manager: State<'_, NotificationManagerState>
) -> Result<(), String> {
    let mut manager = notification_manager.lock().await;
    manager.mark_all_as_read();
    Ok(())
}

/// Delete a notification
#[command]
pub async fn delete_notification(
    notification_id: String,
    notification_manager: State<'_, NotificationManagerState>
) -> Result<bool, String> {
    let mut manager = notification_manager.lock().await;
    Ok(manager.delete_notification(&notification_id))
}

/// Add a new notification
#[command]
pub async fn add_notification(
    title: String,
    message: String,
    notification_type: NotificationType,
    notification_manager: State<'_, NotificationManagerState>
) -> Result<String, String> {
    let mut manager = notification_manager.lock().await;
    let id = manager.add_notification(title, message, notification_type);
    info!("Added notification with ID: {}", id);
    Ok(id)
}

/// Get unread notification count
#[command]
pub async fn get_unread_notification_count(
    notification_manager: State<'_, NotificationManagerState>
) -> Result<usize, String> {
    let manager = notification_manager.lock().await;
    Ok(manager.get_unread_count())
}
