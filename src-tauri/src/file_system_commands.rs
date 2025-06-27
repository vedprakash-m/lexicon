use tokio::sync::Mutex;
use tauri::State;
use uuid::Uuid;
use serde::{Serialize, Deserialize};
use base64::{Engine, engine::general_purpose};

use crate::file_system::{
    FileSystem, FileSystemConfig, DataType
};

/// State wrapper for FileSystem
pub type FileSystemState<'a> = State<'a, Mutex<FileSystem>>;

/// Request structure for writing files
#[derive(Debug, Deserialize)]
pub struct WriteFileRequest {
    pub path: String,
    pub data: String, // Base64 encoded for binary data or plain text
    pub is_binary: bool,
}

/// Request structure for moving files
#[derive(Debug, Deserialize)]
pub struct MoveFileRequest {
    pub from: String,
    pub to: String,
}

/// Response structure for file operations
#[derive(Debug, Serialize)]
pub struct FileOperationResponse {
    pub success: bool,
    pub backup_id: Option<String>,
    pub message: Option<String>,
}

/// Response structure for reading files
#[derive(Debug, Serialize)]
pub struct ReadFileResponse {
    pub success: bool,
    pub data: Option<String>, // Base64 encoded for binary or plain text
    pub is_binary: bool,
    pub size: u64,
    pub message: Option<String>,
}

/// Response structure for backup information
#[derive(Debug, Serialize)]
pub struct BackupInfoResponse {
    pub id: String,
    pub original_path: String,
    pub backup_path: String,
    pub created_at: String,
    pub operation_type: String,
    pub file_size: u64,
    pub checksum: String,
}

/// Initialize file system with default configuration
#[tauri::command]
pub async fn init_file_system() -> Result<String, String> {
    match FileSystem::with_defaults() {
        Ok(_) => Ok("File system initialized successfully".to_string()),
        Err(e) => Err(format!("Failed to initialize file system: {}", e)),
    }
}

/// Write data to a file
#[tauri::command]
pub async fn write_file(
    file_system: FileSystemState<'_>,
    request: WriteFileRequest,
) -> Result<FileOperationResponse, String> {
    let mut fs = file_system.lock().await;
    
    let data = if request.is_binary {
        general_purpose::STANDARD.decode(&request.data)
            .map_err(|e| format!("Failed to decode base64 data: {}", e))?
    } else {
        request.data.into_bytes()
    };
    
    match fs.write_file(&request.path, &data) {
        Ok(backup_id) => Ok(FileOperationResponse {
            success: true,
            backup_id: backup_id.map(|id| id.to_string()),
            message: Some("File written successfully".to_string()),
        }),
        Err(e) => Ok(FileOperationResponse {
            success: false,
            backup_id: None,
            message: Some(format!("Failed to write file: {}", e)),
        }),
    }
}

/// Read data from a file
#[tauri::command]
pub async fn read_file(
    file_system: FileSystemState<'_>,
    path: String,
) -> Result<ReadFileResponse, String> {
    let fs = file_system.lock().await;
    
    match fs.read_file(&path) {
        Ok(data) => {
            // Try to determine if the file is binary
            let is_binary = is_binary_data(&data);
            
            let encoded_data = if is_binary {
                general_purpose::STANDARD.encode(&data)
            } else {
                String::from_utf8_lossy(&data).to_string()
            };
            
            Ok(ReadFileResponse {
                success: true,
                data: Some(encoded_data),
                is_binary,
                size: data.len() as u64,
                message: None,
            })
        },
        Err(e) => Ok(ReadFileResponse {
            success: false,
            data: None,
            is_binary: false,
            size: 0,
            message: Some(format!("Failed to read file: {}", e)),
        }),
    }
}

/// Delete a file
#[tauri::command]
pub async fn delete_file(
    file_system: FileSystemState<'_>,
    path: String,
) -> Result<FileOperationResponse, String> {
    let mut fs = file_system.lock().await;
    
    match fs.delete_file(&path) {
        Ok(backup_id) => Ok(FileOperationResponse {
            success: true,
            backup_id: backup_id.map(|id| id.to_string()),
            message: Some("File deleted successfully".to_string()),
        }),
        Err(e) => Ok(FileOperationResponse {
            success: false,
            backup_id: None,
            message: Some(format!("Failed to delete file: {}", e)),
        }),
    }
}

/// Move/rename a file
#[tauri::command]
pub async fn move_file(
    file_system: FileSystemState<'_>,
    request: MoveFileRequest,
) -> Result<FileOperationResponse, String> {
    let mut fs = file_system.lock().await;
    
    match fs.move_file(&request.from, &request.to) {
        Ok(backup_id) => Ok(FileOperationResponse {
            success: true,
            backup_id: backup_id.map(|id| id.to_string()),
            message: Some("File moved successfully".to_string()),
        }),
        Err(e) => Ok(FileOperationResponse {
            success: false,
            backup_id: None,
            message: Some(format!("Failed to move file: {}", e)),
        }),
    }
}

/// Restore a file from backup
#[tauri::command]
pub async fn restore_from_backup(
    file_system: FileSystemState<'_>,
    backup_id: String,
) -> Result<FileOperationResponse, String> {
    let mut fs = file_system.lock().await;
    
    let uuid = Uuid::parse_str(&backup_id)
        .map_err(|e| format!("Invalid backup ID: {}", e))?;
    
    match fs.restore_from_backup(uuid) {
        Ok(_) => Ok(FileOperationResponse {
            success: true,
            backup_id: Some(backup_id),
            message: Some("File restored successfully".to_string()),
        }),
        Err(e) => Ok(FileOperationResponse {
            success: false,
            backup_id: None,
            message: Some(format!("Failed to restore file: {}", e)),
        }),
    }
}

/// Get backup information
#[tauri::command]
pub async fn get_backup_info(
    file_system: FileSystemState<'_>,
    backup_id: String,
) -> Result<BackupInfoResponse, String> {
    let fs = file_system.lock().await;
    
    let uuid = Uuid::parse_str(&backup_id)
        .map_err(|e| format!("Invalid backup ID: {}", e))?;
    
    match fs.get_backup_info(uuid) {
        Some(backup) => Ok(BackupInfoResponse {
            id: backup.id.to_string(),
            original_path: backup.original_path.to_string_lossy().to_string(),
            backup_path: backup.backup_path.to_string_lossy().to_string(),
            created_at: backup.created_at.to_rfc3339(),
            operation_type: format!("{:?}", backup.operation_type),
            file_size: backup.file_size,
            checksum: backup.checksum.clone(),
        }),
        None => Err("Backup not found".to_string()),
    }
}

/// List all backups
#[tauri::command]
pub async fn list_backups(
    file_system: FileSystemState<'_>,
) -> Result<Vec<BackupInfoResponse>, String> {
    let fs = file_system.lock().await;
    
    let backups = fs.list_backups();
    let backup_responses: Vec<BackupInfoResponse> = backups
        .into_iter()
        .map(|backup| BackupInfoResponse {
            id: backup.id.to_string(),
            original_path: backup.original_path.to_string_lossy().to_string(),
            backup_path: backup.backup_path.to_string_lossy().to_string(),
            created_at: backup.created_at.to_rfc3339(),
            operation_type: format!("{:?}", backup.operation_type),
            file_size: backup.file_size,
            checksum: backup.checksum.clone(),
        })
        .collect();
    
    Ok(backup_responses)
}

/// Get data path for a specific data type
#[tauri::command]
pub async fn get_data_path(
    file_system: FileSystemState<'_>,
    data_type: String,
) -> Result<String, String> {
    let fs = file_system.lock().await;
    
    let dt = match data_type.to_lowercase().as_str() {
        "books" => DataType::Books,
        "datasets" => DataType::Datasets,
        "exports" => DataType::Exports,
        "backups" => DataType::Backups,
        "temp" => DataType::Temp,
        "logs" => DataType::Logs,
        "cache" => DataType::Cache,
        _ => return Err("Invalid data type".to_string()),
    };
    
    let path = fs.get_data_path(dt);
    Ok(path.to_string_lossy().to_string())
}

/// Check disk space
#[tauri::command]
pub async fn check_disk_space(
    file_system: FileSystemState<'_>,
    required_bytes: u64,
) -> Result<bool, String> {
    let fs = file_system.lock().await;
    
    match fs.check_disk_space(required_bytes) {
        Ok(has_space) => Ok(has_space),
        Err(e) => Err(format!("Failed to check disk space: {}", e)),
    }
}

/// Ensure directory structure exists
#[tauri::command]
pub async fn ensure_directory_structure(
    file_system: FileSystemState<'_>,
) -> Result<String, String> {
    let fs = file_system.lock().await;
    
    match fs.ensure_directory_structure() {
        Ok(_) => Ok("Directory structure ensured".to_string()),
        Err(e) => Err(format!("Failed to ensure directory structure: {}", e)),
    }
}

/// Get file system configuration
#[tauri::command]
pub async fn get_file_system_config(
    file_system: FileSystemState<'_>,
) -> Result<FileSystemConfig, String> {
    let fs = file_system.lock().await;
    Ok(fs.get_config().clone())
}

/// Update file system configuration
#[tauri::command]
pub async fn update_file_system_config(
    file_system: FileSystemState<'_>,
    config: FileSystemConfig,
) -> Result<String, String> {
    let mut fs = file_system.lock().await;
    
    match fs.update_config(config) {
        Ok(_) => Ok("Configuration updated successfully".to_string()),
        Err(e) => Err(format!("Failed to update configuration: {}", e)),
    }
}

/// Utility function to detect binary data
fn is_binary_data(data: &[u8]) -> bool {
    // Simple heuristic: if data contains null bytes or non-printable characters
    // in the first 512 bytes, consider it binary
    let sample_size = std::cmp::min(data.len(), 512);
    let sample = &data[..sample_size];
    
    // Check for null bytes
    if sample.contains(&0) {
        return true;
    }
    
    // Check for non-UTF8 sequences
    if String::from_utf8(sample.to_vec()).is_err() {
        return true;
    }
    
    // Check ratio of non-printable characters
    let non_printable_count = sample
        .iter()
        .filter(|&&b| b < 32 && b != 9 && b != 10 && b != 13) // Tab, LF, CR are printable
        .count();
    
    let ratio = non_printable_count as f64 / sample_size as f64;
    ratio > 0.3 // If more than 30% non-printable, consider binary
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_is_binary_data() {
        // Text data
        assert!(!is_binary_data(b"Hello, world!"));
        assert!(!is_binary_data(b"This is a test file with some text content."));
        
        // Binary data
        assert!(is_binary_data(&[0, 1, 2, 3, 4, 5]));
        assert!(is_binary_data(b"\x00\x01\x02\x03Hello"));
        
        // Mixed content
        assert!(!is_binary_data(b"Hello\nWorld\tTest"));
        assert!(is_binary_data(b"Hello\x00\x01\x02\x03\x04\x05\x06World"));
    }
}
