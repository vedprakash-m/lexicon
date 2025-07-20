use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::fs;
use reqwest::Client;
use sha2::{Digest, Sha256};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum CloudProvider {
    ICloud,
    Dropbox,
    GoogleDrive,
    OneDrive,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CloudConfig {
    pub provider: CloudProvider,
    pub enabled: bool,
    pub auto_sync: bool,
    pub sync_interval: u64, // minutes
    pub encryption: bool,
    pub compression: bool,
    pub sync_patterns: Vec<String>,
    pub exclude_patterns: Vec<String>,
    pub credentials: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncStatus {
    pub enabled: bool,
    pub last_sync: Option<SystemTime>,
    pub provider: Option<CloudProvider>,
    pub conflicts: u32,
    pub pending_uploads: u32,
    pub pending_downloads: u32,
    pub sync_in_progress: bool,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileMetadata {
    pub path: String,
    pub size: u64,
    pub modified: SystemTime,
    pub checksum: String,
    pub cloud_id: Option<String>,
    pub version: u32,
}

pub struct CloudSyncManager {
    config: CloudConfig,
    client: Client,
    local_base_path: PathBuf,
    metadata_cache: HashMap<String, FileMetadata>,
}

impl CloudSyncManager {
    pub fn new(config: CloudConfig, local_base_path: PathBuf) -> Self {
        Self {
            config,
            client: Client::new(),
            local_base_path,
            metadata_cache: HashMap::new(),
        }
    }

    pub async fn sync_all(&mut self) -> Result<SyncStatus, Box<dyn std::error::Error>> {
        if !self.config.enabled {
            return Ok(SyncStatus {
                enabled: false,
                last_sync: None,
                provider: None,
                conflicts: 0,
                pending_uploads: 0,
                pending_downloads: 0,
                sync_in_progress: false,
                error: Some("Sync disabled".to_string()),
            });
        }

        match self.config.provider {
            CloudProvider::ICloud => self.sync_icloud().await,
            CloudProvider::Dropbox => self.sync_dropbox().await,
            CloudProvider::GoogleDrive => self.sync_google_drive().await,
            CloudProvider::OneDrive => self.sync_onedrive().await,
        }
    }

    async fn sync_icloud(&mut self) -> Result<SyncStatus, Box<dyn std::error::Error>> {
        // iCloud Drive integration using native macOS APIs
        let icloud_path = self.get_icloud_drive_path()?;
        
        // Create sync directory if it doesn't exist
        let sync_dir = icloud_path.join("Lexicon");
        fs::create_dir_all(&sync_dir).await?;

        let mut pending_uploads = 0;
        let mut pending_downloads = 0;
        let mut conflicts = 0;

        // Scan local files
        let local_files = self.scan_local_files().await?;
        
        // Scan cloud files
        let cloud_files = self.scan_cloud_files(&sync_dir).await?;

        // Compare and sync
        for (path, local_meta) in &local_files {
            if let Some(cloud_meta) = cloud_files.get(path) {
                // File exists in both locations
                if local_meta.modified > cloud_meta.modified {
                    // Local is newer, upload
                    self.upload_file_to_icloud(path, &sync_dir).await?;
                    pending_uploads += 1;
                } else if cloud_meta.modified > local_meta.modified {
                    // Cloud is newer, download
                    self.download_file_from_icloud(path, &sync_dir).await?;
                    pending_downloads += 1;
                } else if local_meta.checksum != cloud_meta.checksum {
                    // Same timestamp but different content - conflict
                    conflicts += 1;
                }
            } else {
                // File only exists locally, upload
                self.upload_file_to_icloud(path, &sync_dir).await?;
                pending_uploads += 1;
            }
        }

        // Download cloud-only files
        for (path, _cloud_meta) in &cloud_files {
            if !local_files.contains_key(path) {
                self.download_file_from_icloud(path, &sync_dir).await?;
                pending_downloads += 1;
            }
        }

        Ok(SyncStatus {
            enabled: true,
            last_sync: Some(SystemTime::now()),
            provider: Some(CloudProvider::ICloud),
            conflicts,
            pending_uploads,
            pending_downloads,
            sync_in_progress: false,
            error: None,
        })
    }

    async fn sync_dropbox(&mut self) -> Result<SyncStatus, Box<dyn std::error::Error>> {
        let access_token = self.config.credentials.get("access_token")
            .ok_or("Dropbox access token not found")?;

        // Dropbox API integration
        let mut pending_uploads = 0;
        let mut pending_downloads = 0;
        let mut conflicts = 0;

        // List files in Dropbox
        let url = "https://api.dropboxapi.com/2/files/list_folder";
        let body = serde_json::json!({
            "path": "/Lexicon",
            "recursive": true
        });

        let response = self.client
            .post(url)
            .header("Authorization", format!("Bearer {}", access_token))
            .header("Content-Type", "application/json")
            .json(&body)
            .send()
            .await?;

        if response.status().is_success() {
            let cloud_files: serde_json::Value = response.json().await?;
            
            // Process sync logic similar to iCloud
            // Implementation would handle Dropbox-specific API calls
        }

        Ok(SyncStatus {
            enabled: true,
            last_sync: Some(SystemTime::now()),
            provider: Some(CloudProvider::Dropbox),
            conflicts,
            pending_uploads,
            pending_downloads,
            sync_in_progress: false,
            error: None,
        })
    }

    async fn sync_google_drive(&mut self) -> Result<SyncStatus, Box<dyn std::error::Error>> {
        let access_token = self.config.credentials.get("access_token")
            .ok_or("Google Drive access token not found")?;

        // Google Drive API integration
        let mut pending_uploads = 0;
        let mut pending_downloads = 0;
        let mut conflicts = 0;

        // List files in Google Drive
        let url = "https://www.googleapis.com/drive/v3/files";
        let response = self.client
            .get(url)
            .header("Authorization", format!("Bearer {}", access_token))
            .query(&[("q", "name contains 'Lexicon'")])
            .send()
            .await?;

        if response.status().is_success() {
            let cloud_files: serde_json::Value = response.json().await?;
            
            // Process sync logic similar to other providers
            // Implementation would handle Google Drive-specific API calls
        }

        Ok(SyncStatus {
            enabled: true,
            last_sync: Some(SystemTime::now()),
            provider: Some(CloudProvider::GoogleDrive),
            conflicts,
            pending_uploads,
            pending_downloads,
            sync_in_progress: false,
            error: None,
        })
    }

    async fn sync_onedrive(&mut self) -> Result<SyncStatus, Box<dyn std::error::Error>> {
        // OneDrive integration for future Windows support
        Ok(SyncStatus {
            enabled: false,
            last_sync: None,
            provider: Some(CloudProvider::OneDrive),
            conflicts: 0,
            pending_uploads: 0,
            pending_downloads: 0,
            sync_in_progress: false,
            error: Some("OneDrive not yet implemented".to_string()),
        })
    }

    fn get_icloud_drive_path(&self) -> Result<PathBuf, Box<dyn std::error::Error>> {
        // Get iCloud Drive path on macOS
        let home = std::env::var("HOME")?;
        let icloud_path = PathBuf::from(home)
            .join("Library")
            .join("Mobile Documents")
            .join("com~apple~CloudDocs");
        
        if !icloud_path.exists() {
            return Err("iCloud Drive not available".into());
        }
        
        Ok(icloud_path)
    }

    async fn scan_local_files(&self) -> Result<HashMap<String, FileMetadata>, Box<dyn std::error::Error>> {
        let mut files = HashMap::new();
        
        // Recursively scan local directory
        self.scan_directory(&self.local_base_path, &mut files).await?;
        
        Ok(files)
    }

    async fn scan_directory(&self, dir: &Path, files: &mut HashMap<String, FileMetadata>) -> Result<(), Box<dyn std::error::Error>> {
        let mut entries = fs::read_dir(dir).await?;
        
        while let Some(entry) = entries.next_entry().await? {
            let path = entry.path();
            
            if path.is_dir() {
                self.scan_directory(&path, files).await?;
            } else {
                // Check if file matches sync patterns
                let relative_path = path.strip_prefix(&self.local_base_path)?;
                let path_str = relative_path.to_string_lossy().to_string();
                
                if self.should_sync_file(&path_str) {
                    let metadata = self.get_file_metadata(&path).await?;
                    files.insert(path_str, metadata);
                }
            }
        }
        
        Ok(())
    }

    async fn scan_cloud_files(&self, cloud_dir: &Path) -> Result<HashMap<String, FileMetadata>, Box<dyn std::error::Error>> {
        let mut files = HashMap::new();
        
        if cloud_dir.exists() {
            self.scan_directory(cloud_dir, &mut files).await?;
        }
        
        Ok(files)
    }

    fn should_sync_file(&self, path: &str) -> bool {
        // Check include patterns
        let matches_include = self.config.sync_patterns.iter().any(|pattern| {
            glob_match::glob_match(pattern, path)
        });
        
        if !matches_include {
            return false;
        }
        
        // Check exclude patterns
        let matches_exclude = self.config.exclude_patterns.iter().any(|pattern| {
            glob_match::glob_match(pattern, path)
        });
        
        !matches_exclude
    }

    async fn get_file_metadata(&self, path: &Path) -> Result<FileMetadata, Box<dyn std::error::Error>> {
        let metadata = fs::metadata(path).await?;
        let modified = metadata.modified()?;
        let size = metadata.len();
        
        // Calculate checksum
        let content = fs::read(path).await?;
        let mut hasher = Sha256::new();
        hasher.update(&content);
        let checksum = format!("{:x}", hasher.finalize());
        
        Ok(FileMetadata {
            path: path.to_string_lossy().to_string(),
            size,
            modified,
            checksum,
            cloud_id: None,
            version: 1,
        })
    }

    async fn upload_file_to_icloud(&self, relative_path: &str, sync_dir: &Path) -> Result<(), Box<dyn std::error::Error>> {
        let local_path = self.local_base_path.join(relative_path);
        let cloud_path = sync_dir.join(relative_path);
        
        // Create parent directories
        if let Some(parent) = cloud_path.parent() {
            fs::create_dir_all(parent).await?;
        }
        
        // Copy file to iCloud Drive
        fs::copy(&local_path, &cloud_path).await?;
        
        Ok(())
    }

    async fn download_file_from_icloud(&self, relative_path: &str, sync_dir: &Path) -> Result<(), Box<dyn std::error::Error>> {
        let cloud_path = sync_dir.join(relative_path);
        let local_path = self.local_base_path.join(relative_path);
        
        // Create parent directories
        if let Some(parent) = local_path.parent() {
            fs::create_dir_all(parent).await?;
        }
        
        // Copy file from iCloud Drive
        fs::copy(&cloud_path, &local_path).await?;
        
        Ok(())
    }

    pub async fn resolve_conflict(&mut self, path: &str, resolution: ConflictResolution) -> Result<(), Box<dyn std::error::Error>> {
        match resolution {
            ConflictResolution::UseLocal => {
                // Upload local version
                match self.config.provider {
                    CloudProvider::ICloud => {
                        let icloud_path = self.get_icloud_drive_path()?;
                        let sync_dir = icloud_path.join("Lexicon");
                        self.upload_file_to_icloud(path, &sync_dir).await?;
                    },
                    _ => {
                        // Handle other providers
                    }
                }
            },
            ConflictResolution::UseCloud => {
                // Download cloud version
                match self.config.provider {
                    CloudProvider::ICloud => {
                        let icloud_path = self.get_icloud_drive_path()?;
                        let sync_dir = icloud_path.join("Lexicon");
                        self.download_file_from_icloud(path, &sync_dir).await?;
                    },
                    _ => {
                        // Handle other providers
                    }
                }
            },
            ConflictResolution::CreateBoth => {
                // Create both versions with different names
                let timestamp = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
                let conflict_path = format!("{}.conflict.{}", path, timestamp);
                
                // Rename local file and download cloud version
                let local_path = self.local_base_path.join(path);
                let conflict_local_path = self.local_base_path.join(&conflict_path);
                fs::rename(&local_path, &conflict_local_path).await?;
                
                match self.config.provider {
                    CloudProvider::ICloud => {
                        let icloud_path = self.get_icloud_drive_path()?;
                        let sync_dir = icloud_path.join("Lexicon");
                        self.download_file_from_icloud(path, &sync_dir).await?;
                    },
                    _ => {
                        // Handle other providers
                    }
                }
            }
        }
        
        Ok(())
    }

    pub fn get_status(&self) -> SyncStatus {
        SyncStatus {
            enabled: self.config.enabled,
            last_sync: None, // Would be tracked in persistent storage
            provider: Some(self.config.provider.clone()),
            conflicts: 0,
            pending_uploads: 0,
            pending_downloads: 0,
            sync_in_progress: false,
            error: None,
        }
    }
}

#[derive(Debug, Clone)]
pub enum ConflictResolution {
    UseLocal,
    UseCloud,
    CreateBoth,
}

// Placeholder for glob matching - would use a proper glob crate
mod glob_match {
    pub fn glob_match(pattern: &str, text: &str) -> bool {
        // Simple pattern matching - in real implementation would use glob crate
        if pattern == "*" {
            return true;
        }
        
        if pattern.starts_with("*.") {
            let ext = &pattern[2..];
            return text.ends_with(ext);
        }
        
        pattern == text
    }
}