use std::path::{Path, PathBuf};
use std::fs;
use std::io::{self, Write, Read};
use chrono::{DateTime, Utc};
use serde::{Serialize, Deserialize};
use uuid::Uuid;
use thiserror::Error;

/// File system abstraction layer for Lexicon
/// Provides safe, atomic file operations with backup/rollback capabilities
/// Designed for local-first architecture with data integrity guarantees

#[derive(Debug, Error)]
pub enum FileSystemError {
    #[error("IO operation failed: {message}")]
    IoError {
        message: String,
        source: io::Error,
    },
    
    #[error("Path does not exist: {path}")]
    PathNotFound { path: String },
    
    #[error("Permission denied for path: {path}")]
    PermissionDenied { path: String },
    
    #[error("Disk space insufficient for operation")]
    InsufficientSpace,
    
    #[error("File is locked or in use: {path}")]
    FileLocked { path: String },
    
    #[error("Backup operation failed: {reason}")]
    BackupFailed { reason: String },
    
    #[error("Rollback operation failed: {reason}")]
    RollbackFailed { reason: String },
    
    #[error("Directory structure validation failed: {reason}")]
    DirectoryStructureError { reason: String },
    
    #[error("Atomic operation failed: {operation}")]
    AtomicOperationFailed { operation: String },
}

pub type FileSystemResult<T> = Result<T, FileSystemError>;

/// Configuration for file system operations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileSystemConfig {
    /// Base directory for all Lexicon data
    pub app_data_dir: PathBuf,
    
    /// Enable automatic backups before write operations
    pub enable_auto_backup: bool,
    
    /// Maximum number of backup files to retain
    pub max_backup_files: usize,
    
    /// Minimum free disk space required (in bytes)
    pub min_free_space: u64,
    
    /// Enable atomic writes using temporary files
    pub enable_atomic_writes: bool,
    
    /// Timeout for file operations (in seconds)
    pub operation_timeout: u64,
}

impl Default for FileSystemConfig {
    fn default() -> Self {
        Self {
            app_data_dir: crate::windows_compat::get_app_data_dir(),
            enable_auto_backup: true,
            max_backup_files: 10,
            min_free_space: 1024 * 1024 * 100, // 100MB
            enable_atomic_writes: true,
            operation_timeout: 30,
        }
    }
}

/// Represents a backup of a file operation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileBackup {
    pub id: Uuid,
    pub original_path: PathBuf,
    pub backup_path: PathBuf,
    pub created_at: DateTime<Utc>,
    pub operation_type: BackupOperationType,
    pub file_size: u64,
    pub checksum: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum BackupOperationType {
    Write,
    Update,
    Delete,
    Move,
}

/// Main file system abstraction
pub struct FileSystem {
    config: FileSystemConfig,
    active_backups: std::collections::HashMap<Uuid, FileBackup>,
}

impl FileSystem {
    /// Create a new FileSystem instance with the given configuration
    pub fn new(config: FileSystemConfig) -> FileSystemResult<Self> {
        let fs = Self {
            config,
            active_backups: std::collections::HashMap::new(),
        };
        
        // Ensure directory structure exists
        fs.ensure_directory_structure()?;
        
        Ok(fs)
    }
    
    /// Create FileSystem with default configuration
    pub fn with_defaults() -> FileSystemResult<Self> {
        Self::new(FileSystemConfig::default())
    }
    
    /// Ensure all required directories exist
    pub fn ensure_directory_structure(&self) -> FileSystemResult<()> {
        let dirs_to_create = [
            &self.config.app_data_dir,
            &self.config.app_data_dir.join("books"),
            &self.config.app_data_dir.join("datasets"),
            &self.config.app_data_dir.join("exports"),
            &self.config.app_data_dir.join("backups"),
            &self.config.app_data_dir.join("temp"),
            &self.config.app_data_dir.join("logs"),
            &self.config.app_data_dir.join("cache"),
        ];
        
        for dir in dirs_to_create.iter() {
            if !dir.exists() {
                fs::create_dir_all(dir).map_err(|e| FileSystemError::IoError {
                    message: format!("Failed to create directory: {}", dir.display()),
                    source: e,
                })?;
            }
        }
        
        Ok(())
    }
    
    /// Get the path for a specific data type
    pub fn get_data_path(&self, data_type: DataType) -> PathBuf {
        match data_type {
            DataType::Books => self.config.app_data_dir.join("books"),
            DataType::Datasets => self.config.app_data_dir.join("datasets"),
            DataType::Exports => self.config.app_data_dir.join("exports"),
            DataType::Backups => self.config.app_data_dir.join("backups"),
            DataType::Temp => self.config.app_data_dir.join("temp"),
            DataType::Logs => self.config.app_data_dir.join("logs"),
            DataType::Cache => self.config.app_data_dir.join("cache"),
        }
    }
    
    /// Check if there's sufficient disk space for an operation
    pub fn check_disk_space(&self, required_bytes: u64) -> FileSystemResult<bool> {
        match fs2::available_space(&self.config.app_data_dir) {
            Ok(available) => Ok(available >= required_bytes + self.config.min_free_space),
            Err(e) => Err(FileSystemError::IoError {
                message: "Failed to check disk space".to_string(),
                source: e,
            }),
        }
    }
    
    /// Write data to a file atomically with optional backup
    pub fn write_file<P: AsRef<Path>>(
        &mut self,
        path: P,
        data: &[u8],
    ) -> FileSystemResult<Option<Uuid>> {
        let path = path.as_ref();
        
        // Check disk space
        if !self.check_disk_space(data.len() as u64)? {
            return Err(FileSystemError::InsufficientSpace);
        }
        
        // Create backup if file exists and auto-backup is enabled
        let backup_id = if path.exists() && self.config.enable_auto_backup {
            Some(self.create_backup(path, BackupOperationType::Write)?)
        } else {
            None
        };
        
        // Perform atomic write
        if self.config.enable_atomic_writes {
            self.atomic_write(path, data)?;
        } else {
            self.direct_write(path, data)?;
        }
        
        Ok(backup_id)
    }
    
    /// Read data from a file
    pub fn read_file<P: AsRef<Path>>(&self, path: P) -> FileSystemResult<Vec<u8>> {
        let path = path.as_ref();
        
        if !path.exists() {
            return Err(FileSystemError::PathNotFound {
                path: path.to_string_lossy().to_string(),
            });
        }
        
        fs::read(path).map_err(|e| {
            match e.kind() {
                io::ErrorKind::PermissionDenied => FileSystemError::PermissionDenied {
                    path: path.to_string_lossy().to_string(),
                },
                _ => FileSystemError::IoError {
                    message: format!("Failed to read file: {}", path.display()),
                    source: e,
                },
            }
        })
    }
    
    /// Delete a file with optional backup
    pub fn delete_file<P: AsRef<Path>>(
        &mut self,
        path: P,
    ) -> FileSystemResult<Option<Uuid>> {
        let path = path.as_ref();
        
        if !path.exists() {
            return Err(FileSystemError::PathNotFound {
                path: path.to_string_lossy().to_string(),
            });
        }
        
        // Create backup before deletion
        let backup_id = if self.config.enable_auto_backup {
            Some(self.create_backup(path, BackupOperationType::Delete)?)
        } else {
            None
        };
        
        fs::remove_file(path).map_err(|e| FileSystemError::IoError {
            message: format!("Failed to delete file: {}", path.display()),
            source: e,
        })?;
        
        Ok(backup_id)
    }
    
    /// Move/rename a file with backup
    pub fn move_file<P1: AsRef<Path>, P2: AsRef<Path>>(
        &mut self,
        from: P1,
        to: P2,
    ) -> FileSystemResult<Option<Uuid>> {
        let from = from.as_ref();
        let to = to.as_ref();
        
        if !from.exists() {
            return Err(FileSystemError::PathNotFound {
                path: from.to_string_lossy().to_string(),
            });
        }
        
        // Create backup of source file
        let backup_id = if self.config.enable_auto_backup {
            Some(self.create_backup(from, BackupOperationType::Move)?)
        } else {
            None
        };
        
        // Ensure destination directory exists
        if let Some(parent) = to.parent() {
            fs::create_dir_all(parent).map_err(|e| FileSystemError::IoError {
                message: format!("Failed to create destination directory: {}", parent.display()),
                source: e,
            })?;
        }
        
        fs::rename(from, to).map_err(|e| FileSystemError::IoError {
            message: format!("Failed to move file from {} to {}", from.display(), to.display()),
            source: e,
        })?;
        
        Ok(backup_id)
    }
    
    /// Create a backup of a file
    fn create_backup<P: AsRef<Path>>(
        &mut self,
        path: P,
        operation_type: BackupOperationType,
    ) -> FileSystemResult<Uuid> {
        let path = path.as_ref();
        let backup_id = Uuid::new_v4();
        
        // Generate backup filename with timestamp
        let timestamp = Utc::now().format("%Y%m%d_%H%M%S");
        let filename = path.file_name()
            .ok_or_else(|| FileSystemError::IoError {
                message: "Invalid file path for backup".to_string(),
                source: io::Error::new(io::ErrorKind::InvalidInput, "No filename"),
            })?;
        
        let backup_filename = format!("{}_{}_{}",
            timestamp,
            backup_id.to_string().split('-').next().unwrap_or("backup"),
            filename.to_string_lossy()
        );
        
        let backup_path = self.get_data_path(DataType::Backups).join(backup_filename);
        
        // Copy file to backup location
        fs::copy(path, &backup_path).map_err(|e| FileSystemError::BackupFailed {
            reason: format!("Failed to copy file to backup: {}", e),
        })?;
        
        // Calculate file metadata
        let metadata = fs::metadata(path).map_err(|e| FileSystemError::IoError {
            message: "Failed to read file metadata".to_string(),
            source: e,
        })?;
        
        let checksum = self.calculate_checksum(path)?;
        
        let backup = FileBackup {
            id: backup_id,
            original_path: path.to_path_buf(),
            backup_path,
            created_at: Utc::now(),
            operation_type,
            file_size: metadata.len(),
            checksum,
        };
        
        self.active_backups.insert(backup_id, backup);
        
        // Clean up old backups if needed
        self.cleanup_old_backups()?;
        
        Ok(backup_id)
    }
    
    /// Restore a file from backup
    pub fn restore_from_backup(&mut self, backup_id: Uuid) -> FileSystemResult<()> {
        let backup = self.active_backups.get(&backup_id)
            .ok_or_else(|| FileSystemError::RollbackFailed {
                reason: format!("Backup not found: {}", backup_id),
            })?.clone();
        
        if !backup.backup_path.exists() {
            return Err(FileSystemError::RollbackFailed {
                reason: "Backup file no longer exists".to_string(),
            });
        }
        
        // Ensure destination directory exists
        if let Some(parent) = backup.original_path.parent() {
            fs::create_dir_all(parent).map_err(|e| FileSystemError::IoError {
                message: format!("Failed to create directory for restore: {}", parent.display()),
                source: e,
            })?;
        }
        
        // Copy backup back to original location
        fs::copy(&backup.backup_path, &backup.original_path)
            .map_err(|e| FileSystemError::RollbackFailed {
                reason: format!("Failed to restore file: {}", e),
            })?;
        
        Ok(())
    }
    
    /// Clean up old backup files
    fn cleanup_old_backups(&self) -> FileSystemResult<()> {
        let backup_dir = self.get_data_path(DataType::Backups);
        
        if !backup_dir.exists() {
            return Ok(());
        }
        
        let mut backup_files: Vec<_> = fs::read_dir(&backup_dir)
            .map_err(|e| FileSystemError::IoError {
                message: "Failed to read backup directory".to_string(),
                source: e,
            })?
            .filter_map(|entry| entry.ok())
            .filter(|entry| entry.path().is_file())
            .collect();
        
        // Sort by modification time (oldest first)
        backup_files.sort_by(|a, b| {
            let a_time = a.metadata()
                .and_then(|m| m.modified())
                .unwrap_or(std::time::UNIX_EPOCH);
            let b_time = b.metadata()
                .and_then(|m| m.modified())
                .unwrap_or(std::time::UNIX_EPOCH);
            a_time.cmp(&b_time)
        });
        
        // Remove excess backup files
        if backup_files.len() > self.config.max_backup_files {
            let to_remove = backup_files.len() - self.config.max_backup_files;
            for entry in backup_files.iter().take(to_remove) {
                let _ = fs::remove_file(entry.path());
            }
        }
        
        Ok(())
    }
    
    /// Perform atomic write using temporary file
    fn atomic_write<P: AsRef<Path>>(&self, path: P, data: &[u8]) -> FileSystemResult<()> {
        let path = path.as_ref();
        let temp_path = self.get_data_path(DataType::Temp)
            .join(format!("atomic_write_{}", Uuid::new_v4()));
        
        // Write to temporary file first
        {
            let mut temp_file = fs::File::create(&temp_path)
                .map_err(|e| FileSystemError::AtomicOperationFailed {
                    operation: format!("create temp file: {}", e),
                })?;
            
            temp_file.write_all(data)
                .map_err(|e| FileSystemError::AtomicOperationFailed {
                    operation: format!("write to temp file: {}", e),
                })?;
            
            temp_file.sync_all()
                .map_err(|e| FileSystemError::AtomicOperationFailed {
                    operation: format!("sync temp file: {}", e),
                })?;
        }
        
        // Ensure destination directory exists
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|e| FileSystemError::IoError {
                message: format!("Failed to create destination directory: {}", parent.display()),
                source: e,
            })?;
        }
        
        // Atomically move temp file to final location
        fs::rename(&temp_path, path)
            .map_err(|e| FileSystemError::AtomicOperationFailed {
                operation: format!("move temp file to final location: {}", e),
            })?;
        
        Ok(())
    }
    
    /// Perform direct write (non-atomic)
    fn direct_write<P: AsRef<Path>>(&self, path: P, data: &[u8]) -> FileSystemResult<()> {
        let path = path.as_ref();
        
        // Ensure directory exists
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|e| FileSystemError::IoError {
                message: format!("Failed to create directory: {}", parent.display()),
                source: e,
            })?;
        }
        
        fs::write(path, data).map_err(|e| FileSystemError::IoError {
            message: format!("Failed to write file: {}", path.display()),
            source: e,
        })
    }
    
    /// Calculate checksum of a file
    fn calculate_checksum<P: AsRef<Path>>(&self, path: P) -> FileSystemResult<String> {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        
        let data = self.read_file(path)?;
        let mut hasher = DefaultHasher::new();
        data.hash(&mut hasher);
        Ok(format!("{:x}", hasher.finish()))
    }
    
    /// Get information about active backups
    pub fn get_backup_info(&self, backup_id: Uuid) -> Option<&FileBackup> {
        self.active_backups.get(&backup_id)
    }
    
    /// List all active backups
    pub fn list_backups(&self) -> Vec<&FileBackup> {
        self.active_backups.values().collect()
    }
    
    /// Get configuration
    pub fn get_config(&self) -> &FileSystemConfig {
        &self.config
    }
    
    /// Update configuration
    pub fn update_config(&mut self, config: FileSystemConfig) -> FileSystemResult<()> {
        self.config = config;
        self.ensure_directory_structure()?;
        Ok(())
    }
}

/// Data types for organizing files
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DataType {
    Books,
    Datasets,
    Exports,
    Backups,
    Temp,
    Logs,
    Cache,
}

// Utility functions for common file operations

/// Create a unique filename with timestamp
pub fn create_unique_filename(base_name: &str, extension: &str) -> String {
    let timestamp = Utc::now().format("%Y%m%d_%H%M%S");
    let uuid_short = Uuid::new_v4().to_string().split('-').next().unwrap_or("file").to_string();
    format!("{}_{}.{}", base_name, timestamp, extension)
}

/// Validate file path for security
pub fn validate_file_path<P: AsRef<Path>>(path: P, base_dir: P) -> FileSystemResult<()> {
    let path = path.as_ref();
    let base_dir = base_dir.as_ref();
    
    // Ensure the path is within the base directory (prevent directory traversal)
    let canonical_path = path.canonicalize().unwrap_or_else(|_| path.to_path_buf());
    let canonical_base = base_dir.canonicalize().unwrap_or_else(|_| base_dir.to_path_buf());
    
    if !canonical_path.starts_with(canonical_base) {
        return Err(FileSystemError::DirectoryStructureError {
            reason: "Path outside of allowed directory".to_string(),
        });
    }
    
    Ok(())
}

/// Get file size safely
pub fn get_file_size<P: AsRef<Path>>(path: P) -> FileSystemResult<u64> {
    let metadata = fs::metadata(path.as_ref()).map_err(|e| FileSystemError::IoError {
        message: "Failed to get file metadata".to_string(),
        source: e,
    })?;
    
    Ok(metadata.len())
}

/// Check if file exists and is readable
pub fn is_file_accessible<P: AsRef<Path>>(path: P) -> bool {
    let path = path.as_ref();
    path.exists() && path.is_file() && fs::metadata(path).is_ok()
}
