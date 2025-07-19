use super::*;
use std::collections::HashMap;

#[tokio::test]
async fn test_get_sync_status_default() {
    let result = get_sync_status().await;
    assert!(result.is_ok());
    
    let status = result.unwrap();
    assert!(!status.enabled);
    assert!(status.last_sync.is_none());
    assert!(status.provider.is_none());
    assert_eq!(status.conflicts, 0);
    assert_eq!(status.pending_uploads, 0);
    assert_eq!(status.pending_downloads, 0);
}

#[tokio::test]
async fn test_detect_cloud_providers() {
    let result = detect_cloud_providers().await;
    assert!(result.is_ok());
    
    let providers = result.unwrap();
    // Should always include 'none' as an option
    assert!(providers.contains(&"none".to_string()));
    
    // Should include API-based providers
    assert!(providers.contains(&"dropbox".to_string()));
    assert!(providers.contains(&"google_drive".to_string()));
    assert!(providers.contains(&"onedrive".to_string()));
    
    // On macOS, should detect iCloud if available
    #[cfg(target_os = "macos")]
    {
        if std::path::Path::new(&format!("{}/Library/Mobile Documents/com~apple~CloudDocs", 
            std::env::var("HOME").unwrap_or_default())).exists() {
            assert!(providers.contains(&"icloud".to_string()));
        }
    }
}

#[tokio::test]
async fn test_get_provider_status() {
    // Test none provider
    let result = get_provider_status("none".to_string()).await;
    assert!(result.is_ok());
    assert!(!result.unwrap()); // 'none' should return false
    
    // Test API providers (should be available)
    let providers = ["google_drive", "dropbox", "onedrive"];
    for provider in &providers {
        let result = get_provider_status(provider.to_string()).await;
        assert!(result.is_ok());
        assert!(result.unwrap()); // API providers should be available
    }
    
    // Test invalid provider
    let result = get_provider_status("invalid_provider".to_string()).await;
    assert!(result.is_ok());
    assert!(!result.unwrap()); // Invalid provider should return false
}

#[tokio::test]
async fn test_configure_sync() {
    let config = SyncConfig {
        provider: "icloud".to_string(),
        credentials: HashMap::new(),
        sync_folders: vec!["*.db".to_string(), "*.json".to_string()],
        auto_sync: true,
        sync_interval: 300,
        encryption: true,
        compression: true,
    };
    
    let result = configure_sync(config).await;
    // Currently disabled, so should return Ok(false)
    assert!(result.is_ok());
    assert!(!result.unwrap());
}

#[tokio::test]
async fn test_sync_config_serialization() {
    let config = SyncConfig {
        provider: "google_drive".to_string(),
        credentials: {
            let mut creds = HashMap::new();
            creds.insert("access_token".to_string(), "test_token".to_string());
            creds
        },
        sync_folders: vec!["*.db".to_string(), "enrichment_*.json".to_string()],
        auto_sync: true,
        sync_interval: 600,
        encryption: true,
        compression: false,
    };
    
    // Test serialization
    let serialized = serde_json::to_string(&config);
    assert!(serialized.is_ok());
    
    // Test deserialization
    let deserialized: Result<SyncConfig, _> = serde_json::from_str(&serialized.unwrap());
    assert!(deserialized.is_ok());
    
    let config_restored = deserialized.unwrap();
    assert_eq!(config_restored.provider, "google_drive");
    assert_eq!(config_restored.sync_interval, 600);
    assert!(config_restored.encryption);
    assert!(!config_restored.compression);
}

#[tokio::test]
async fn test_backup_info_creation() {
    let backup_info = BackupInfo {
        id: "test-backup-001".to_string(),
        name: "Test Backup".to_string(),
        timestamp: "2025-07-14T12:00:00Z".to_string(),
        size: 1024000,
        location: "/path/to/backup".to_string(),
        verified: true,
        file_count: 42,
    };
    
    assert_eq!(backup_info.id, "test-backup-001");
    assert_eq!(backup_info.size, 1024000);
    assert!(backup_info.verified);
    assert_eq!(backup_info.file_count, 42);
}

#[tokio::test]
async fn test_get_backup_list() {
    let result = get_backup_list().await;
    assert!(result.is_ok());
    
    let backups = result.unwrap();
    // Should return empty list for new installations
    assert!(backups.is_empty());
}

#[tokio::test]
async fn test_create_backup_disabled() {
    let result = create_backup("test-backup".to_string()).await;
    assert!(result.is_err());
    assert!(result.unwrap_err().contains("not available"));
}

#[tokio::test]
async fn test_sync_operations_disabled() {
    // All sync operations should return false/disabled for new installations
    assert!(!start_sync().await.unwrap_or(true));
    assert!(!stop_sync().await.unwrap_or(true));
    assert!(!force_sync().await.unwrap_or(true));
    assert!(!restore_backup("test".to_string()).await.unwrap_or(true));
}

#[cfg(test)]
mod platform_specific_tests {
    use super::*;
    
    #[cfg(target_os = "macos")]
    #[tokio::test]
    async fn test_macos_icloud_detection() {
        let home = std::env::var("HOME").unwrap_or_default();
        let icloud_path = format!("{}/Library/Mobile Documents/com~apple~CloudDocs", home);
        
        if std::path::Path::new(&icloud_path).exists() {
            let result = get_provider_status("icloud".to_string()).await;
            assert!(result.is_ok());
            assert!(result.unwrap());
        }
    }
    
    #[cfg(target_os = "windows")]
    #[tokio::test]
    async fn test_windows_onedrive_detection() {
        if let Ok(onedrive_path) = std::env::var("OneDrive") {
            if std::path::Path::new(&onedrive_path).exists() {
                let result = get_provider_status("onedrive".to_string()).await;
                assert!(result.is_ok());
                assert!(result.unwrap());
            }
        }
    }
}

#[cfg(test)]
mod integration_tests {
    use super::*;
    
    #[tokio::test]
    async fn test_provider_detection_flow() {
        // 1. Get available providers
        let providers_result = detect_cloud_providers().await;
        assert!(providers_result.is_ok());
        let providers = providers_result.unwrap();
        
        // 2. Test status for each detected provider
        for provider in &providers {
            let status_result = get_provider_status(provider.clone()).await;
            assert!(status_result.is_ok());
            
            // 'none' should be false, others depend on system
            if provider == "none" {
                assert!(!status_result.unwrap());
            }
        }
        
        // 3. Test sync configuration for a valid provider
        if providers.len() > 1 { // More than just 'none'
            let test_provider = providers.iter()
                .find(|p| p.as_str() != "none")
                .unwrap();
            
            let config = SyncConfig {
                provider: test_provider.clone(),
                credentials: HashMap::new(),
                sync_folders: vec!["*.db".to_string()],
                auto_sync: true,
                sync_interval: 300,
                encryption: true,
                compression: true,
            };
            
            let config_result = configure_sync(config).await;
            assert!(config_result.is_ok());
        }
    }
}

// Helper functions for testing
#[cfg(test)]
mod test_helpers {
    use super::*;
    
    pub fn create_test_sync_config(provider: &str) -> SyncConfig {
        SyncConfig {
            provider: provider.to_string(),
            credentials: HashMap::new(),
            sync_folders: vec![
                "*.db".to_string(),
                "*.json".to_string(),
                "enrichment_*.json".to_string(),
            ],
            auto_sync: true,
            sync_interval: 300,
            encryption: true,
            compression: true,
        }
    }
    
    pub fn create_test_backup_info(id: &str) -> BackupInfo {
        BackupInfo {
            id: id.to_string(),
            name: format!("Test Backup {}", id),
            timestamp: "2025-07-14T12:00:00Z".to_string(),
            size: 1024000,
            location: format!("/test/backup/{}", id),
            verified: true,
            file_count: 10,
        }
    }
}
