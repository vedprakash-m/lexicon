use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs::{self, File};
use std::io::{self, Read, Write};
use std::path::{Path, PathBuf};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackupMetadata {
    pub id: String,
    pub name: String,
    pub created_at: DateTime<Utc>,
    pub size_bytes: u64,
    pub checksum: String,
    pub version: String,
    pub description: Option<String>,
    pub is_auto: bool,
}

#[derive(Debug, thiserror::Error)]
pub enum BackupError {
    #[error("IO error: {0}")]
    IoError(#[from] io::Error),
    #[error("Serialization error: {0}")]
    SerializationError(String),
    #[error("Backup not found: {0}")]
    BackupNotFound(String),
    #[error("Checksum verification failed")]
    ChecksumError,
}

pub struct BackupManager {
    backup_dir: PathBuf,
    app_data_dir: PathBuf,
    retention_count: usize,
}

impl BackupManager {
    pub fn new(backup_dir: PathBuf, app_data_dir: PathBuf) -> Self {
        Self {
            backup_dir,
            app_data_dir,
            retention_count: 5,
        }
    }

    pub fn create_backup(
        &self,
        name: &str,
        description: Option<&str>,
        is_auto: bool,
    ) -> Result<BackupMetadata, BackupError> {
        fs::create_dir_all(&self.backup_dir)?;

        let backup_id = Uuid::new_v4().to_string();
        let backup_path = self.backup_dir.join(format!("{}.backup", backup_id));

        // Create tar archive
        let backup_file = File::create(&backup_path)?;
        let mut tar_builder = tar::Builder::new(backup_file);
        tar_builder.append_dir_all(".", &self.app_data_dir)?;
        tar_builder.finish()?;

        // Calculate checksum
        let mut file = File::open(&backup_path)?;
        let mut buffer = Vec::new();
        file.read_to_end(&mut buffer)?;
        let mut hasher = Sha256::new();
        hasher.update(&buffer);
        let checksum = format!("{:x}", hasher.finalize());

        let size_bytes = fs::metadata(&backup_path)?.len();

        let metadata = BackupMetadata {
            id: backup_id.clone(),
            name: name.to_string(),
            created_at: Utc::now(),
            size_bytes,
            checksum,
            version: env!("CARGO_PKG_VERSION").to_string(),
            description: description.map(|s| s.to_string()),
            is_auto,
        };

        // Save metadata
        let metadata_path = self.backup_dir.join(format!("{}.json", backup_id));
        let metadata_json = serde_json::to_string_pretty(&metadata)
            .map_err(|e| BackupError::SerializationError(e.to_string()))?;
        fs::write(metadata_path, metadata_json)?;

        Ok(metadata)
    }

    pub fn restore_backup(&self, backup_id: &str) -> Result<(), BackupError> {
        let backup_path = self.backup_dir.join(format!("{}.backup", backup_id));
        if !backup_path.exists() {
            return Err(BackupError::BackupNotFound(backup_id.to_string()));
        }

        // Verify checksum
        let metadata = self.get_backup_metadata(backup_id)?;
        let mut file = File::open(&backup_path)?;
        let mut buffer = Vec::new();
        file.read_to_end(&mut buffer)?;
        let mut hasher = Sha256::new();
        hasher.update(&buffer);
        let checksum = format!("{:x}", hasher.finalize());

        if checksum != metadata.checksum {
            return Err(BackupError::ChecksumError);
        }

        // Extract the backup
        let file = File::open(&backup_path)?;
        let mut archive = tar::Archive::new(file);
        archive.unpack(&self.app_data_dir)?;

        Ok(())
    }

    pub fn get_backup_metadata(&self, backup_id: &str) -> Result<BackupMetadata, BackupError> {
        let metadata_path = self.backup_dir.join(format!("{}.json", backup_id));
        if !metadata_path.exists() {
            return Err(BackupError::BackupNotFound(backup_id.to_string()));
        }

        let metadata_json = fs::read_to_string(metadata_path)?;
        let metadata = serde_json::from_str(&metadata_json)
            .map_err(|e| BackupError::SerializationError(e.to_string()))?;
        Ok(metadata)
    }

    pub fn list_backups(&self) -> Result<Vec<BackupMetadata>, BackupError> {
        let mut backups = Vec::new();
        if !self.backup_dir.exists() {
            return Ok(backups);
        }

        for entry in fs::read_dir(&self.backup_dir)? {
            let entry = entry?;
            let path = entry.path();
            if path.is_file() && path.extension().map_or(false, |ext| ext == "json") {
                if let Some(file_stem) = path.file_stem() {
                    if let Some(backup_id) = file_stem.to_str() {
                        if let Ok(metadata) = self.get_backup_metadata(backup_id) {
                            backups.push(metadata);
                        }
                    }
                }
            }
        }

        backups.sort_by(|a, b| b.created_at.cmp(&a.created_at));
        Ok(backups)
    }

    pub fn verify_backup(&self, backup_id: &str) -> Result<bool, BackupError> {
        let metadata = self.get_backup_metadata(backup_id)?;
        let backup_path = self.backup_dir.join(format!("{}.backup", backup_id));
        
        if !backup_path.exists() {
            return Err(BackupError::BackupNotFound(backup_id.to_string()));
        }

        let mut file = File::open(&backup_path)?;
        let mut buffer = Vec::new();
        file.read_to_end(&mut buffer)?;
        let mut hasher = Sha256::new();
        hasher.update(&buffer);
        let checksum = format!("{:x}", hasher.finalize());

        Ok(checksum == metadata.checksum)
    }
}