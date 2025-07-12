use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use tauri::command;
use tokio::process::Command;

#[derive(Debug, Serialize, Deserialize)]
pub struct SyncStatus {
    pub enabled: bool,
    pub last_sync: Option<String>,
    pub provider: Option<String>,
    pub conflicts: u32,
    pub pending_uploads: u32,
    pub pending_downloads: u32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct BackupInfo {
    pub id: String,
    pub name: String,
    pub timestamp: String,
    pub size: u64,
    pub location: String,
    pub verified: bool,
    pub file_count: u32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SyncConfig {
    pub provider: String,
    pub credentials: HashMap<String, String>,
    pub sync_interval: u32,
    pub auto_sync: bool,
    pub encryption_enabled: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct BackupConfig {
    pub auto_backup: bool,
    pub backup_interval: u32,
    pub max_backups: u32,
    pub backup_location: String,
    pub compress: bool,
    pub encrypt: bool,
}

// Cloud Sync Commands

#[command]
pub async fn get_sync_status() -> Result<SyncStatus, String> {
    // Return empty sync status for new installation
    Ok(SyncStatus {
        enabled: false,
        last_sync: None,
        provider: None,
        conflicts: 0,
        pending_uploads: 0,
        pending_downloads: 0,
    })
}

#[command]
pub async fn configure_sync(config: SyncConfig) -> Result<bool, String> {
    let config_json = serde_json::to_string(&config)
        .map_err(|e| format!("Failed to serialize config: {}", e))?;

    let output = Command::new("python3")
        .arg("-c")
        .arg(&format!(r#"
import sys
import os
sys.path.append('/Users/vedprakashmishra/lexicon/python-engine')
from sync.cloud_storage_manager import CloudStorageManager
import json
import asyncio

async def main():
    config = json.loads('{}')
    manager = CloudStorageManager()
    success = await manager.configure_sync(config)
    print(json.dumps({{'success': success}}))

asyncio.run(main())
"#, config_json))
        .output()
        .await
        .map_err(|e| format!("Failed to execute Python command: {}", e))?;

    if !output.status.success() {
        return Err(format!("Python script failed: {}", String::from_utf8_lossy(&output.stderr)));
    }

    let output_str = String::from_utf8_lossy(&output.stdout);
    let result: serde_json::Value = serde_json::from_str(&output_str)
        .map_err(|e| format!("Failed to parse result: {}", e))?;
    
    Ok(result["success"].as_bool().unwrap_or(false))
}

#[command]
pub async fn start_sync() -> Result<bool, String> {
    let output = Command::new("python3")
        .arg("-c")
        .arg(r#"
import sys
import os
sys.path.append('/Users/vedprakashmishra/lexicon/python-engine')
from sync.cloud_storage_manager import CloudStorageManager
import json
import asyncio

async def main():
    manager = CloudStorageManager()
    success = await manager.start_sync()
    print(json.dumps({'success': success}))

asyncio.run(main())
"#)
        .output()
        .await
        .map_err(|e| format!("Failed to execute Python command: {}", e))?;

    if !output.status.success() {
        return Err(format!("Python script failed: {}", String::from_utf8_lossy(&output.stderr)));
    }

    let output_str = String::from_utf8_lossy(&output.stdout);
    let result: serde_json::Value = serde_json::from_str(&output_str)
        .map_err(|e| format!("Failed to parse result: {}", e))?;
    
    Ok(result["success"].as_bool().unwrap_or(false))
}

#[command]
pub async fn stop_sync() -> Result<bool, String> {
    let output = Command::new("python3")
        .arg("-c")
        .arg(r#"
import sys
import os
sys.path.append('/Users/vedprakashmishra/lexicon/python-engine')
from sync.cloud_storage_manager import CloudStorageManager
import json
import asyncio

async def main():
    manager = CloudStorageManager()
    success = await manager.stop_sync()
    print(json.dumps({'success': success}))

asyncio.run(main())
"#)
        .output()
        .await
        .map_err(|e| format!("Failed to execute Python command: {}", e))?;

    if !output.status.success() {
        return Err(format!("Python script failed: {}", String::from_utf8_lossy(&output.stderr)));
    }

    let output_str = String::from_utf8_lossy(&output.stdout);
    let result: serde_json::Value = serde_json::from_str(&output_str)
        .map_err(|e| format!("Failed to parse result: {}", e))?;
    
    Ok(result["success"].as_bool().unwrap_or(false))
}

// Backup Commands

#[command]
pub async fn list_backup_archives() -> Result<Vec<BackupInfo>, String> {
    let output = Command::new("python3")
        .arg("-c")
        .arg(r#"
import sys
import os
sys.path.append('/Users/vedprakashmishra/lexicon/python-engine')
from sync.backup_manager import BackupManager
import json
import asyncio

async def main():
    manager = BackupManager()
    backups = await manager.list_backups()
    print(json.dumps(backups))

asyncio.run(main())
"#)
        .output()
        .await
        .map_err(|e| format!("Failed to execute Python command: {}", e))?;

    if !output.status.success() {
        return Err(format!("Python script failed: {}", String::from_utf8_lossy(&output.stderr)));
    }

    let output_str = String::from_utf8_lossy(&output.stdout);
    serde_json::from_str(&output_str)
        .map_err(|e| format!("Failed to parse backup list: {}", e))
}

#[command]
pub async fn create_backup(name: String) -> Result<BackupInfo, String> {
    let output = Command::new("python3")
        .arg("-c")
        .arg(&format!(r#"
import sys
import os
sys.path.append('/Users/vedprakashmishra/lexicon/python-engine')
from sync.backup_manager import BackupManager
import json
import asyncio

async def main():
    manager = BackupManager()
    backup_info = await manager.create_backup('{}')
    print(json.dumps(backup_info))

asyncio.run(main())
"#, name))
        .output()
        .await
        .map_err(|e| format!("Failed to execute Python command: {}", e))?;

    if !output.status.success() {
        return Err(format!("Python script failed: {}", String::from_utf8_lossy(&output.stderr)));
    }

    let output_str = String::from_utf8_lossy(&output.stdout);
    serde_json::from_str(&output_str)
        .map_err(|e| format!("Failed to parse backup info: {}", e))
}

#[command]
pub async fn restore_backup(backup_id: String) -> Result<bool, String> {
    let output = Command::new("python3")
        .arg("-c")
        .arg(&format!(r#"
import sys
import os
sys.path.append('/Users/vedprakashmishra/lexicon/python-engine')
from sync.backup_manager import BackupManager
import json
import asyncio

async def main():
    manager = BackupManager()
    success = await manager.restore_backup('{}')
    print(json.dumps({{'success': success}}))

asyncio.run(main())
"#, backup_id))
        .output()
        .await
        .map_err(|e| format!("Failed to execute Python command: {}", e))?;

    if !output.status.success() {
        return Err(format!("Python script failed: {}", String::from_utf8_lossy(&output.stderr)));
    }

    let output_str = String::from_utf8_lossy(&output.stdout);
    let result: serde_json::Value = serde_json::from_str(&output_str)
        .map_err(|e| format!("Failed to parse result: {}", e))?;
    
    Ok(result["success"].as_bool().unwrap_or(false))
}

#[command]
pub async fn delete_backup(backup_id: String) -> Result<bool, String> {
    let output = Command::new("python3")
        .arg("-c")
        .arg(&format!(r#"
import sys
import os
sys.path.append('/Users/vedprakashmishra/lexicon/python-engine')
from sync.backup_manager import BackupManager
import json
import asyncio

async def main():
    manager = BackupManager()
    success = await manager.delete_backup('{}')
    print(json.dumps({{'success': success}}))

asyncio.run(main())
"#, backup_id))
        .output()
        .await
        .map_err(|e| format!("Failed to execute Python command: {}", e))?;

    if !output.status.success() {
        return Err(format!("Python script failed: {}", String::from_utf8_lossy(&output.stderr)));
    }

    let output_str = String::from_utf8_lossy(&output.stdout);
    let result: serde_json::Value = serde_json::from_str(&output_str)
        .map_err(|e| format!("Failed to parse result: {}", e))?;
    
    Ok(result["success"].as_bool().unwrap_or(false))
}

#[command]
pub async fn verify_backup(backup_id: String) -> Result<bool, String> {
    let output = Command::new("python3")
        .arg("-c")
        .arg(&format!(r#"
import sys
import os
sys.path.append('/Users/vedprakashmishra/lexicon/python-engine')
from sync.backup_manager import BackupManager
import json
import asyncio

async def main():
    manager = BackupManager()
    is_valid = await manager.verify_backup('{}')
    print(json.dumps({{'valid': is_valid}}))

asyncio.run(main())
"#, backup_id))
        .output()
        .await
        .map_err(|e| format!("Failed to execute Python command: {}", e))?;

    if !output.status.success() {
        return Err(format!("Python script failed: {}", String::from_utf8_lossy(&output.stderr)));
    }

    let output_str = String::from_utf8_lossy(&output.stdout);
    let result: serde_json::Value = serde_json::from_str(&output_str)
        .map_err(|e| format!("Failed to parse result: {}", e))?;
    
    Ok(result["valid"].as_bool().unwrap_or(false))
}

#[command]
pub async fn configure_backup(config: BackupConfig) -> Result<bool, String> {
    let config_json = serde_json::to_string(&config)
        .map_err(|e| format!("Failed to serialize config: {}", e))?;

    let output = Command::new("python3")
        .arg("-c")
        .arg(&format!(r#"
import sys
import os
sys.path.append('/Users/vedprakashmishra/lexicon/python-engine')
from sync.backup_manager import BackupManager
import json
import asyncio

async def main():
    config = json.loads('{}')
    manager = BackupManager()
    success = await manager.configure_backup(config)
    print(json.dumps({{'success': success}}))

asyncio.run(main())
"#, config_json))
        .output()
        .await
        .map_err(|e| format!("Failed to execute Python command: {}", e))?;

    if !output.status.success() {
        return Err(format!("Python script failed: {}", String::from_utf8_lossy(&output.stderr)));
    }

    let output_str = String::from_utf8_lossy(&output.stdout);
    let result: serde_json::Value = serde_json::from_str(&output_str)
        .map_err(|e| format!("Failed to parse result: {}", e))?;
    
    Ok(result["success"].as_bool().unwrap_or(false))
}
