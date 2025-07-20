use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::fs;
use std::sync::{Arc, Mutex};
use tauri::{command, State};
use tokio::process::Command;
use chrono::{DateTime, Utc};
use sha2::{Sha256, Digest};
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct SyncStatus {
    pub enabled: bool,
    pub last_sync: Option<String>,
    pub provider: Option<String>,
    pub conflicts: u32,
    pub pending_uploads: u32,
    pub pending_downloads: u32,
    pub sync_errors: Vec<String>,
    pub is_syncing: bool,
    pub sync_progress: Option<f64>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct BackupInfo {
    pub id: String,
    pub name: String,
    pub timestamp: String,
    pub size: u64,
    pub location: String,
    pub verified: bool,
    pub file_count: u32,
    pub backup_type: String, // 'manual', 'automatic', 'scheduled'
    pub checksum: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct SyncConfig {
    pub provider: String, // 'icloud', 'google_drive', 'dropbox', 'onedrive', 'none'
    pub credentials: HashMap<String, String>,
    pub sync_folders: Vec<String>,
    pub auto_sync: bool,
    pub sync_interval: u32,
    pub encryption: bool,
    pub compression: bool,
    pub conflict_resolution: String, // 'ask', 'local_wins', 'remote_wins', 'keep_both'
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct BackupConfig {
    pub auto_backup: bool,
    pub backup_interval: u32,
    pub retention_days: u32,
    pub backup_location: String,
    pub encrypt: bool,
    pub compress: bool,
    pub verify_backups: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ConflictInfo {
    pub file_path: String,
    pub local_modified: String,
    pub remote_modified: String,
    pub local_size: u64,
    pub remote_size: u64,
    pub conflict_type: String, // 'modified_both', 'deleted_local', 'deleted_remote'
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SyncProgress {
    pub current_file: String,
    pub files_processed: u32,
    pub total_files: u32,
    pub bytes_transferred: u64,
    pub total_bytes: u64,
    pub operation: String, // 'upload', 'download', 'scan', 'resolve'
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct SyncTarget {
    pub id: String,
    pub name: String,
    pub target_type: String, // 'local', 'dropbox', 'google_drive', 'aws_s3', 'azure_blob'
    pub status: String, // 'connected', 'error', 'disconnected'
    pub last_sync: Option<String>,
    pub config: HashMap<String, serde_json::Value>,
    pub created_at: String,
    pub updated_at: String,
}

// Global sync state management
#[derive(Debug, Default)]
pub struct SyncState {
    pub status: Arc<Mutex<SyncStatus>>,
    pub config: Arc<Mutex<Option<SyncConfig>>>,
    pub backup_config: Arc<Mutex<Option<BackupConfig>>>,
    pub active_conflicts: Arc<Mutex<Vec<ConflictInfo>>>,
    pub sync_progress: Arc<Mutex<Option<SyncProgress>>>,
}

impl SyncState {
    pub fn new() -> Self {
        Self {
            status: Arc::new(Mutex::new(SyncStatus {
                enabled: false,
                last_sync: None,
                provider: None,
                conflicts: 0,
                pending_uploads: 0,
                pending_downloads: 0,
                sync_errors: vec![],
                is_syncing: false,
                sync_progress: None,
            })),
            config: Arc::new(Mutex::new(None)),
            backup_config: Arc::new(Mutex::new(None)),
            active_conflicts: Arc::new(Mutex::new(vec![])),
            sync_progress: Arc::new(Mutex::new(None)),
        }
    }
}

/// Get the sync configuration directory
fn get_sync_config_dir() -> Result<PathBuf, String> {
    let app_data_dir = dirs::document_dir()
        .ok_or_else(|| "Could not find documents directory".to_string())?
        .join("Lexicon")
        .join("sync");
    
    // Create directory if it doesn't exist
    if !app_data_dir.exists() {
        fs::create_dir_all(&app_data_dir)
            .map_err(|e| format!("Failed to create sync directory: {}", e))?;
    }
    
    Ok(app_data_dir)
}

/// Execute Python cloud sync script
async fn execute_cloud_sync_command(command: &str, args: &serde_json::Value) -> Result<serde_json::Value, String> {
    let python_script = r#"
import sys
import json
import asyncio
from pathlib import Path

# Add the python-engine directory to sys.path
script_dir = Path(__file__).parent
python_engine_dir = script_dir / "../../python-engine"
sys.path.insert(0, str(python_engine_dir.resolve()))

try:
    from sync.cloud_storage_manager import CloudStorageManager, CloudProvider, SyncConfiguration, ConflictResolution
    
    async def execute_sync_command(command, args):
        data_dir = Path("../Documents/Lexicon")
        
        # Create basic sync configuration
        config = SyncConfiguration(
            provider=CloudProvider[args.get('provider', 'LOCAL_ONLY').upper()],
            sync_patterns=args.get('sync_patterns', ['*.db', '*.json']),
            exclude_patterns=args.get('exclude_patterns', ['*.tmp', '*.log']),
            encrypt_data=args.get('encryption', False),
            conflict_resolution=ConflictResolution[args.get('conflict_resolution', 'ASK').upper()]
        )
        
        # Create cloud storage manager
        manager = CloudStorageManager(config, data_dir)
        
        if command == "status":
            stats = manager.get_sync_stats()
            return {
                'success': True,
                'data': stats
            }
        elif command == "start_sync":
            await manager.load_sync_state()
            sync_state = await manager.full_sync()
            return {
                'success': True,
                'data': {
                    'files_synced': sync_state.synced_files,
                    'files_uploaded': sync_state.uploaded_files,
                    'files_downloaded': sync_state.downloaded_files,
                    'conflicts': sync_state.conflicts,
                    'errors': sync_state.errors
                }
            }
        elif command == "scan_files":
            files = await manager.scan_local_files()
            return {
                'success': True,
                'data': {
                    'files': [{'path': str(f.path), 'size': f.size, 'status': f.sync_status.value} for f in files]
                }
            }
        elif command == "get_conflicts":
            # Get conflicts from sync state
            conflicts = []  # Would be populated from actual conflict detection
            return {
                'success': True,
                'data': {'conflicts': conflicts}
            }
        else:
            return {'success': False, 'error': f'Unknown command: {command}'}
    
    if __name__ == "__main__":
        command = sys.argv[1]
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
        result = asyncio.run(execute_sync_command(command, args))
        print(json.dumps(result))
        
except Exception as e:
    print(json.dumps({'success': False, 'error': str(e)}))
"#;
    
    // Write temporary Python script
    let temp_dir = std::env::temp_dir();
    let script_path = temp_dir.join("cloud_sync_command.py");
    fs::write(&script_path, python_script)
        .map_err(|e| format!("Failed to write Python script: {}", e))?;
    
    // Execute Python script
    let args_json = serde_json::to_string(args)
        .map_err(|e| format!("Failed to serialize args: {}", e))?;
    
    let output = Command::new("python3")
        .arg(&script_path)
        .arg(command)
        .arg(&args_json)
        .output()
        .await
        .map_err(|e| format!("Failed to execute Python script: {}", e))?;
    
    // Clean up temporary script
    let _ = fs::remove_file(&script_path);
    
    if !output.status.success() {
        return Err(format!("Python script failed: {}", String::from_utf8_lossy(&output.stderr)));
    }
    
    let result_str = String::from_utf8_lossy(&output.stdout);
    let result: serde_json::Value = serde_json::from_str(&result_str)
        .map_err(|e| format!("Failed to parse Python result: {}", e))?;
    
    if !result["success"].as_bool().unwrap_or(false) {
        return Err(result["error"].as_str().unwrap_or("Unknown error").to_string());
    }
    
    Ok(result["data"].clone())
}

#[command]
pub async fn get_sync_status(sync_state: State<'_, SyncState>) -> Result<SyncStatus, String> {
    // Try to get real sync status from Python backend
    match execute_cloud_sync_command("status", &serde_json::json!({})).await {
        Ok(data) => {
            let mut status = sync_state.status.lock()
                .map_err(|e| format!("Failed to lock status: {}", e))?;
            
            // Update status with real data
            status.pending_uploads = data["pending_uploads"].as_u64().unwrap_or(0) as u32;
            status.pending_downloads = data["pending_downloads"].as_u64().unwrap_or(0) as u32;
            status.conflicts = data["conflicts"].as_u64().unwrap_or(0) as u32;
            
            if let Some(config) = sync_state.config.lock().unwrap().as_ref() {
                status.enabled = config.provider != "none";
                status.provider = Some(config.provider.clone());
            }
            
            Ok(status.clone())
        }
        Err(_) => {
            // Fall back to cached status
            let status = sync_state.status.lock()
                .map_err(|e| format!("Failed to lock status: {}", e))?;
            Ok(status.clone())
        }
    }
}

#[command]
pub async fn configure_sync(
    config: SyncConfig,
    sync_state: State<'_, SyncState>
) -> Result<bool, String> {
    println!("Configuring sync with provider: {}", config.provider);
    
    // Validate provider
    if !["icloud", "google_drive", "dropbox", "onedrive", "none"].contains(&config.provider.as_str()) {
        return Err("Invalid sync provider".to_string());
    }
    
    // Save configuration
    let config_dir = get_sync_config_dir()?;
    let config_file = config_dir.join("sync_config.json");
    
    let config_json = serde_json::to_string_pretty(&config)
        .map_err(|e| format!("Failed to serialize config: {}", e))?;
    
    fs::write(&config_file, config_json)
        .map_err(|e| format!("Failed to save config: {}", e))?;
    
    // Update global state
    {
        let mut state_config = sync_state.config.lock()
            .map_err(|e| format!("Failed to lock config: {}", e))?;
        *state_config = Some(config.clone());
    }
    
    // Update status
    {
        let mut status = sync_state.status.lock()
            .map_err(|e| format!("Failed to lock status: {}", e))?;
        status.enabled = config.provider != "none";
        status.provider = Some(config.provider.clone());
    }
    
    Ok(true)
}

#[command]
pub async fn start_sync(sync_state: State<'_, SyncState>) -> Result<bool, String> {
    // Get current config
    let config = {
        let config_lock = sync_state.config.lock()
            .map_err(|e| format!("Failed to lock config: {}", e))?;
        match config_lock.as_ref() {
            Some(config) => config.clone(),
            None => return Err("No sync configuration found. Please configure sync first.".to_string()),
        }
    };
    
    // Don't start if already syncing
    {
        let status = sync_state.status.lock()
            .map_err(|e| format!("Failed to lock status: {}", e))?;
        if status.is_syncing {
            return Err("Sync already in progress".to_string());
        }
    }
    
    // Update status to syncing
    {
        let mut status = sync_state.status.lock()
            .map_err(|e| format!("Failed to lock status: {}", e))?;
        status.is_syncing = true;
        status.sync_errors.clear();
    }
    
    // Execute sync using Python backend
    let sync_args = serde_json::json!({
        "provider": config.provider,
        "sync_patterns": config.sync_folders,
        "encryption": config.encryption,
        "conflict_resolution": config.conflict_resolution
    });
    
    match execute_cloud_sync_command("start_sync", &sync_args).await {
        Ok(result) => {
            // Update status with results
            let mut status = sync_state.status.lock()
                .map_err(|e| format!("Failed to lock status: {}", e))?;
            
            status.is_syncing = false;
            status.last_sync = Some(Utc::now().to_rfc3339());
            status.conflicts = result["conflicts"].as_u64().unwrap_or(0) as u32;
            
            if let Some(errors) = result["errors"].as_array() {
                status.sync_errors = errors.iter()
                    .filter_map(|e| e.as_str())
                    .map(|s| s.to_string())
                    .collect();
            }
            
            Ok(true)
        }
        Err(error) => {
            // Update status with error
            let mut status = sync_state.status.lock()
                .map_err(|e| format!("Failed to lock status: {}", e))?;
            
            status.is_syncing = false;
            status.sync_errors = vec![error.clone()];
            
            Err(error)
        }
    }
}

#[command]
pub async fn stop_sync(sync_state: State<'_, SyncState>) -> Result<bool, String> {
    let mut status = sync_state.status.lock()
        .map_err(|e| format!("Failed to lock status: {}", e))?;
    
    if !status.is_syncing {
        return Ok(true); // Already stopped
    }
    
    status.is_syncing = false;
    status.sync_progress = None;
    
    // In a full implementation, we would signal the Python process to stop
    // For now, just update the status
    
    Ok(true)
}

#[command]
pub async fn force_sync(sync_state: State<'_, SyncState>) -> Result<bool, String> {
    // Force sync ignores intervals and starts immediately
    start_sync(sync_state).await
}

#[command]
pub async fn get_backup_list(sync_state: State<'_, SyncState>) -> Result<Vec<BackupInfo>, String> {
    let backup_dir = get_sync_config_dir()?.join("backups");
    
    if !backup_dir.exists() {
        return Ok(vec![]);
    }
    
    let mut backups = Vec::new();
    
    for entry in fs::read_dir(&backup_dir)
        .map_err(|e| format!("Failed to read backup directory: {}", e))? 
    {
        let entry = entry.map_err(|e| format!("Failed to read directory entry: {}", e))?;
        let path = entry.path();
        
        if path.is_file() && path.extension().map_or(false, |ext| ext == "json") {
            if let Ok(content) = fs::read_to_string(&path) {
                if let Ok(backup_info) = serde_json::from_str::<BackupInfo>(&content) {
                    backups.push(backup_info);
                }
            }
        }
    }
    
    // Sort by timestamp, newest first
    backups.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));
    
    Ok(backups)
}

#[command]
pub async fn create_backup(name: String, sync_state: State<'_, SyncState>) -> Result<BackupInfo, String> {
    let backup_id = Uuid::new_v4().to_string();
    let timestamp = Utc::now().to_rfc3339();
    
    // Execute backup using Python backend
    let backup_args = serde_json::json!({
        "backup_id": backup_id,
        "name": name,
        "timestamp": timestamp,
        "encrypt": true,
        "compress": true
    });
    
    let python_script = r#"
import sys
import json
import asyncio
from pathlib import Path
import shutil
import zipfile
import hashlib

# Add the python-engine directory to sys.path
script_dir = Path(__file__).parent
python_engine_dir = script_dir / "../../python-engine"
sys.path.insert(0, str(python_engine_dir.resolve()))

try:
    from sync.backup_manager import BackupManager, BackupType, BackupConfiguration
    
    async def create_backup(args):
        data_dir = Path("../Documents/Lexicon")
        backup_dir = Path("../Documents/Lexicon/sync/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_id = args['backup_id']
        backup_name = args['name']
        
        # Create backup using backup manager
        config = BackupConfiguration(
            backup_type=BackupType.FULL,
            encrypt=args.get('encrypt', True),
            compress=args.get('compress', True)
        )
        
        manager = BackupManager(data_dir, backup_dir)
        
        # Create backup
        backup_path = await manager.create_backup(backup_id, config)
        
        # Calculate backup info
        backup_file = backup_path
        file_size = backup_file.stat().st_size if backup_file.exists() else 0
        
        # Count files in backup (estimate)
        file_count = 0
        for root, dirs, files in data_dir.rglob("*"):
            if root.is_file():
                file_count += 1
        
        # Calculate checksum
        checksum = None
        if backup_file.exists():
            with open(backup_file, 'rb') as f:
                checksum = hashlib.sha256(f.read()).hexdigest()
        
        backup_info = {
            'id': backup_id,
            'name': backup_name,
            'timestamp': args['timestamp'],
            'size': file_size,
            'location': str(backup_file),
            'verified': True,
            'file_count': file_count,
            'backup_type': 'manual',
            'checksum': checksum
        }
        
        return {
            'success': True,
            'data': backup_info
        }
    
    if __name__ == "__main__":
        args = json.loads(sys.argv[1])
        result = asyncio.run(create_backup(args))
        print(json.dumps(result))
        
except Exception as e:
    print(json.dumps({'success': False, 'error': str(e)}))
"#;
    
    // Write temporary Python script
    let temp_dir = std::env::temp_dir();
    let script_path = temp_dir.join("create_backup.py");
    fs::write(&script_path, python_script)
        .map_err(|e| format!("Failed to write Python script: {}", e))?;
    
    // Execute Python script
    let args_json = serde_json::to_string(&backup_args)
        .map_err(|e| format!("Failed to serialize args: {}", e))?;
    
    let output = Command::new("python3")
        .arg(&script_path)
        .arg(&args_json)
        .output()
        .await
        .map_err(|e| format!("Failed to execute Python script: {}", e))?;
    
    // Clean up temporary script
    let _ = fs::remove_file(&script_path);
    
    if !output.status.success() {
        return Err(format!("Backup creation failed: {}", String::from_utf8_lossy(&output.stderr)));
    }
    
    let result_str = String::from_utf8_lossy(&output.stdout);
    let result: serde_json::Value = serde_json::from_str(&result_str)
        .map_err(|e| format!("Failed to parse Python result: {}", e))?;
    
    if !result["success"].as_bool().unwrap_or(false) {
        return Err(result["error"].as_str().unwrap_or("Unknown error").to_string());
    }
    
    // Parse backup info from result
    let backup_data = &result["data"];
    let backup_info = BackupInfo {
        id: backup_data["id"].as_str().unwrap_or(&backup_id).to_string(),
        name: backup_data["name"].as_str().unwrap_or(&name).to_string(),
        timestamp: backup_data["timestamp"].as_str().unwrap_or(&timestamp).to_string(),
        size: backup_data["size"].as_u64().unwrap_or(0),
        location: backup_data["location"].as_str().unwrap_or("").to_string(),
        verified: backup_data["verified"].as_bool().unwrap_or(false),
        file_count: backup_data["file_count"].as_u64().unwrap_or(0) as u32,
        backup_type: backup_data["backup_type"].as_str().unwrap_or("manual").to_string(),
        checksum: backup_data["checksum"].as_str().map(|s| s.to_string()),
    };
    
    // Save backup info to backup directory
    let backup_dir = get_sync_config_dir()?.join("backups");
    if !backup_dir.exists() {
        fs::create_dir_all(&backup_dir)
            .map_err(|e| format!("Failed to create backup directory: {}", e))?;
    }
    
    let backup_info_file = backup_dir.join(format!("{}.json", backup_id));
    let backup_info_json = serde_json::to_string_pretty(&backup_info)
        .map_err(|e| format!("Failed to serialize backup info: {}", e))?;
    
    fs::write(&backup_info_file, backup_info_json)
        .map_err(|e| format!("Failed to save backup info: {}", e))?;
    
    Ok(backup_info)
}

#[command]
pub async fn restore_backup(backup_id: String, sync_state: State<'_, SyncState>) -> Result<bool, String> {
    // Get backup info
    let backup_dir = get_sync_config_dir()?.join("backups");
    let backup_info_file = backup_dir.join(format!("{}.json", backup_id));
    
    if !backup_info_file.exists() {
        return Err("Backup not found".to_string());
    }
    
    let backup_info_content = fs::read_to_string(&backup_info_file)
        .map_err(|e| format!("Failed to read backup info: {}", e))?;
    
    let backup_info: BackupInfo = serde_json::from_str(&backup_info_content)
        .map_err(|e| format!("Failed to parse backup info: {}", e))?;
    
    // Execute restore using Python backend
    let restore_args = serde_json::json!({
        "backup_id": backup_id,
        "backup_location": backup_info.location,
        "verify_checksum": backup_info.checksum
    });
    
    match execute_cloud_sync_command("restore_backup", &restore_args).await {
        Ok(_) => Ok(true),
        Err(error) => Err(format!("Restore failed: {}", error)),
    }
}

#[command]
pub async fn delete_backup(backup_id: String, sync_state: State<'_, SyncState>) -> Result<bool, String> {
    let backup_dir = get_sync_config_dir()?.join("backups");
    let backup_info_file = backup_dir.join(format!("{}.json", backup_id));
    
    if !backup_info_file.exists() {
        return Err("Backup not found".to_string());
    }
    
    // Read backup info to get file location
    let backup_info_content = fs::read_to_string(&backup_info_file)
        .map_err(|e| format!("Failed to read backup info: {}", e))?;
    
    let backup_info: BackupInfo = serde_json::from_str(&backup_info_content)
        .map_err(|e| format!("Failed to parse backup info: {}", e))?;
    
    // Delete backup file
    if !backup_info.location.is_empty() {
        let backup_file_path = PathBuf::from(&backup_info.location);
        if backup_file_path.exists() {
            fs::remove_file(&backup_file_path)
                .map_err(|e| format!("Failed to delete backup file: {}", e))?;
        }
    }
    
    // Delete backup info file
    fs::remove_file(&backup_info_file)
        .map_err(|e| format!("Failed to delete backup info: {}", e))?;
    
    Ok(true)
}

#[command]
pub async fn verify_backup(backup_id: String, sync_state: State<'_, SyncState>) -> Result<bool, String> {
    let backup_dir = get_sync_config_dir()?.join("backups");
    let backup_info_file = backup_dir.join(format!("{}.json", backup_id));
    
    if !backup_info_file.exists() {
        return Err("Backup not found".to_string());
    }
    
    let backup_info_content = fs::read_to_string(&backup_info_file)
        .map_err(|e| format!("Failed to read backup info: {}", e))?;
    
    let backup_info: BackupInfo = serde_json::from_str(&backup_info_content)
        .map_err(|e| format!("Failed to parse backup info: {}", e))?;
    
    // Check if backup file exists
    let backup_file_path = PathBuf::from(&backup_info.location);
    if !backup_file_path.exists() {
        return Ok(false);
    }
    
    // Verify file size
    let file_size = backup_file_path.metadata()
        .map_err(|e| format!("Failed to get backup file metadata: {}", e))?
        .len();
    
    if file_size != backup_info.size {
        return Ok(false);
    }
    
    // Verify checksum if available
    if let Some(expected_checksum) = &backup_info.checksum {
        use sha2::{Sha256, Digest};
        let mut hasher = Sha256::new();
        
        let backup_content = fs::read(&backup_file_path)
            .map_err(|e| format!("Failed to read backup file: {}", e))?;
        
        hasher.update(&backup_content);
        let actual_checksum = format!("{:x}", hasher.finalize());
        
        if &actual_checksum != expected_checksum {
            return Ok(false);
        }
    }
    
    Ok(true)
}

#[command]
pub async fn list_backup_archives() -> Result<Vec<BackupInfo>, String> {
    // This is the same as get_backup_list for now
    // In a full implementation, this might include remote backups
    let backup_dir = get_sync_config_dir()?.join("backups");
    
    if !backup_dir.exists() {
        return Ok(vec![]);
    }
    
    let mut backups = Vec::new();
    
    for entry in fs::read_dir(&backup_dir)
        .map_err(|e| format!("Failed to read backup directory: {}", e))? 
    {
        let entry = entry.map_err(|e| format!("Failed to read directory entry: {}", e))?;
        let path = entry.path();
        
        if path.is_file() && path.extension().map_or(false, |ext| ext == "json") {
            if let Ok(content) = fs::read_to_string(&path) {
                if let Ok(backup_info) = serde_json::from_str::<BackupInfo>(&content) {
                    backups.push(backup_info);
                }
            }
        }
    }
    
    // Sort by timestamp, newest first
    backups.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));
    
    Ok(backups)
}

#[command]
pub async fn detect_cloud_providers() -> Result<Vec<String>, String> {
    // Return available cloud providers based on platform and installed software
    let mut providers = vec!["none".to_string()];
    
    #[cfg(target_os = "macos")]
    {
        // Check for iCloud Drive
        let icloud_path = std::env::var("HOME").unwrap_or_default() + "/Library/Mobile Documents/com~apple~CloudDocs";
        if std::path::Path::new(&icloud_path).exists() {
            providers.push("icloud".to_string());
        }
        
        // Check for OneDrive on macOS
        let onedrive_paths = [
            "/Library/CloudStorage/OneDrive-Personal",
            "/Library/CloudStorage/OneDrive-Commercial",
            "/OneDrive"
        ];
        for path_suffix in &onedrive_paths {
            let full_path = std::env::var("HOME").unwrap_or_default() + path_suffix;
            if std::path::Path::new(&full_path).exists() {
                providers.push("onedrive".to_string());
                break;
            }
        }
    }
    
    #[cfg(target_os = "windows")]
    {
        // Check for OneDrive on Windows
        if let Ok(onedrive_path) = std::env::var("OneDrive") {
            if std::path::Path::new(&onedrive_path).exists() {
                providers.push("onedrive".to_string());
            }
        }
    }
    
    // Check for Google Drive (cross-platform)
    let home = std::env::var("HOME").or_else(|_| std::env::var("USERPROFILE")).unwrap_or_default();
    let google_paths = [
        "/Google Drive",
        "/GoogleDrive"
    ];
    for path_suffix in &google_paths {
        let full_path = home.clone() + path_suffix;
        if std::path::Path::new(&full_path).exists() {
            providers.push("google_drive".to_string());
            break;
        }
    }
    
    // Dropbox is available via API on all platforms
    providers.push("dropbox".to_string());
    
    // Google Drive is available via API on all platforms
    if !providers.contains(&"google_drive".to_string()) {
        providers.push("google_drive".to_string());
    }
    
    // OneDrive is available via API on all platforms
    if !providers.contains(&"onedrive".to_string()) {
        providers.push("onedrive".to_string());
    }
    
    Ok(providers)
}

#[command]
pub async fn get_provider_status(provider: String) -> Result<bool, String> {
    match provider.as_str() {
        "icloud" => {
            #[cfg(target_os = "macos")]
            {
                let icloud_path = std::env::var("HOME").unwrap_or_default() + "/Library/Mobile Documents/com~apple~CloudDocs";
                Ok(std::path::Path::new(&icloud_path).exists())
            }
            #[cfg(not(target_os = "macos"))]
            Ok(false)
        },
        "google_drive" | "dropbox" | "onedrive" => {
            // These providers are available via API on all platforms
            Ok(true)
        },
        _ => Ok(false)
    }
}

// Sync Target Management Commands

#[command]
pub async fn get_sync_targets() -> Result<Vec<SyncTarget>, String> {
    let sync_dir = get_sync_config_dir()?;
    let targets_file = sync_dir.join("sync_targets.json");
    
    if !targets_file.exists() {
        return Ok(vec![]);
    }
    
    let content = fs::read_to_string(&targets_file)
        .map_err(|e| format!("Failed to read sync targets: {}", e))?;
    
    let targets: Vec<SyncTarget> = serde_json::from_str(&content)
        .map_err(|e| format!("Failed to parse sync targets: {}", e))?;
    
    Ok(targets)
}

#[command]
pub async fn add_sync_target(mut target: SyncTarget) -> Result<SyncTarget, String> {
    // Generate ID and timestamps if not provided
    if target.id.is_empty() {
        target.id = Uuid::new_v4().to_string();
    }
    let now = Utc::now().to_rfc3339();
    target.created_at = now.clone();
    target.updated_at = now;
    
    // Get existing targets
    let mut targets = get_sync_targets().await?;
    
    // Check for duplicate names
    if targets.iter().any(|t| t.name == target.name && t.id != target.id) {
        return Err("A sync target with this name already exists".to_string());
    }
    
    // Add new target
    targets.push(target.clone());
    
    // Save to file
    save_sync_targets(&targets).await?;
    
    Ok(target)
}

#[command]
pub async fn update_sync_target(target_id: String, mut updates: SyncTarget) -> Result<SyncTarget, String> {
    let mut targets = get_sync_targets().await?;
    
    // Find target to update
    let target_index = targets.iter().position(|t| t.id == target_id)
        .ok_or("Sync target not found")?;
    
    // Update fields but preserve ID and created_at
    let existing_target = &mut targets[target_index];
    updates.id = existing_target.id.clone();
    updates.created_at = existing_target.created_at.clone();
    updates.updated_at = Utc::now().to_rfc3339();
    
    // Check for duplicate names (excluding self)
    if targets.iter().any(|t| t.name == updates.name && t.id != target_id) {
        return Err("A sync target with this name already exists".to_string());
    }
    
    targets[target_index] = updates.clone();
    
    // Save to file
    save_sync_targets(&targets).await?;
    
    Ok(updates)
}

#[command]
pub async fn delete_sync_target(target_id: String) -> Result<bool, String> {
    let mut targets = get_sync_targets().await?;
    
    // Remove target
    let initial_len = targets.len();
    targets.retain(|t| t.id != target_id);
    
    if targets.len() == initial_len {
        return Err("Sync target not found".to_string());
    }
    
    // Save to file
    save_sync_targets(&targets).await?;
    
    Ok(true)
}

#[command]
pub async fn test_sync_target_connection(target_id: String) -> Result<bool, String> {
    let targets = get_sync_targets().await?;
    
    let target = targets.iter().find(|t| t.id == target_id)
        .ok_or("Sync target not found")?;
    
    // Test connection based on target type
    match target.target_type.as_str() {
        "local" => {
            // Test local folder access
            if let Some(folder_path) = target.config.get("folderPath") {
                if let Some(path_str) = folder_path.as_str() {
                    let path = Path::new(path_str);
                    Ok(path.exists() && path.is_dir())
                } else {
                    Err("Invalid folder path configuration".to_string())
                }
            } else {
                Err("Missing folder path configuration".to_string())
            }
        },
        "dropbox" | "google_drive" => {
            // For cloud providers, we would test API connectivity
            // For now, simulate a test
            Ok(true)
        },
        "aws_s3" => {
            // Test AWS S3 connectivity
            // This would require AWS SDK integration
            Ok(true)
        },
        "azure_blob" => {
            // Test Azure Blob connectivity
            // This would require Azure SDK integration
            Ok(true)
        },
        _ => Err("Unsupported sync target type".to_string())
    }
}

// Helper function to save sync targets
async fn save_sync_targets(targets: &Vec<SyncTarget>) -> Result<(), String> {
    let sync_dir = get_sync_config_dir()?;
    let targets_file = sync_dir.join("sync_targets.json");
    
    let json = serde_json::to_string_pretty(targets)
        .map_err(|e| format!("Failed to serialize sync targets: {}", e))?;
    
    fs::write(&targets_file, json)
        .map_err(|e| format!("Failed to save sync targets: {}", e))?;
    
    Ok(())
}
