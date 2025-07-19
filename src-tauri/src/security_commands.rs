use std::path::PathBuf;
use tauri::{command, State};
use serde::{Deserialize, Serialize};
use anyhow::Result;
use log::{info, error};

use crate::security_manager::{SecurityManager, SecurityEvent, SecurityStats, AuditLogEntry, Permission, SecurityConfig};

/// Security state wrapper for Tauri
pub struct SecurityState {
    pub manager: SecurityManager,
}

impl SecurityState {
    pub fn new(app_data_dir: PathBuf) -> Result<Self> {
        let security_root = app_data_dir.join("security");
        let manager = SecurityManager::new(security_root)?;
        
        Ok(Self { manager })
    }
}

/// Request to encrypt data
#[derive(Debug, Deserialize)]
pub struct EncryptDataRequest {
    pub data: Vec<u8>,
    pub key_id: String,
}

/// Response from encryption operation
#[derive(Debug, Serialize)]
pub struct EncryptDataResponse {
    pub encrypted_data: Vec<u8>,
    pub success: bool,
    pub message: String,
}

/// Request to decrypt data
#[derive(Debug, Deserialize)]
pub struct DecryptDataRequest {
    pub encrypted_data: Vec<u8>,
    pub key_id: String,
}

/// Response from decryption operation
#[derive(Debug, Serialize)]
pub struct DecryptDataResponse {
    pub decrypted_data: Vec<u8>,
    pub success: bool,
    pub message: String,
}

/// Request to encrypt file
#[derive(Debug, Deserialize)]
pub struct EncryptFileRequest {
    pub file_path: String,
    pub key_id: String,
}

/// Response from file encryption
#[derive(Debug, Serialize)]
pub struct EncryptFileResponse {
    pub encrypted_path: String,
    pub success: bool,
    pub message: String,
}

/// Request to decrypt file
#[derive(Debug, Deserialize)]
pub struct DecryptFileRequest {
    pub encrypted_path: String,
    pub key_id: String,
}

/// Response from file decryption
#[derive(Debug, Serialize)]
pub struct DecryptFileResponse {
    pub decrypted_path: String,
    pub success: bool,
    pub message: String,
}

/// Request to generate new encryption key
#[derive(Debug, Deserialize)]
pub struct GenerateKeyRequest {
    pub key_id: String,
}

/// Response from key generation
#[derive(Debug, Serialize)]
pub struct GenerateKeyResponse {
    pub key_id: String,
    pub success: bool,
    pub message: String,
}

/// Request to check permissions
#[derive(Debug, Deserialize)]
pub struct CheckPermissionRequest {
    pub user_id: String,
    pub resource: String,
    pub permission: String,
}

/// Response from permission check
#[derive(Debug, Serialize)]
pub struct CheckPermissionResponse {
    pub has_permission: bool,
    pub success: bool,
    pub message: String,
}

/// Request to create user session
#[derive(Debug, Deserialize)]
pub struct CreateSessionRequest {
    pub user_id: String,
}

/// Response from session creation
#[derive(Debug, Serialize)]
pub struct CreateSessionResponse {
    pub session_id: String,
    pub success: bool,
    pub message: String,
}

/// Request to validate session
#[derive(Debug, Deserialize)]
pub struct ValidateSessionRequest {
    pub session_id: String,
}

/// Response from session validation
#[derive(Debug, Serialize)]
pub struct ValidateSessionResponse {
    pub is_valid: bool,
    pub success: bool,
    pub message: String,
}

/// Request to get audit log
#[derive(Debug, Deserialize)]
pub struct GetAuditLogRequest {
    pub limit: Option<usize>,
}

/// Response with audit log entries
#[derive(Debug, Serialize)]
pub struct GetAuditLogResponse {
    pub entries: Vec<AuditLogEntry>,
    pub success: bool,
    pub message: String,
}

/// Request to hash data
#[derive(Debug, Deserialize)]
pub struct HashDataRequest {
    pub data: Vec<u8>,
}

/// Response with hash
#[derive(Debug, Serialize)]
pub struct HashDataResponse {
    pub hash: String,
    pub success: bool,
    pub message: String,
}

/// Request to verify data integrity
#[derive(Debug, Deserialize)]
pub struct VerifyIntegrityRequest {
    pub data: Vec<u8>,
    pub expected_hash: String,
}

/// Response from integrity verification
#[derive(Debug, Serialize)]
pub struct VerifyIntegrityResponse {
    pub is_valid: bool,
    pub success: bool,
    pub message: String,
}

/// Encrypt data using specified key
#[command]
pub async fn encrypt_data(
    request: EncryptDataRequest,
    security_state: State<'_, SecurityState>,
) -> Result<EncryptDataResponse, String> {
    info!("Encrypting data with key: {}", request.key_id);
    
    match security_state.manager.encrypt_data(&request.data, &request.key_id).await {
        Ok(encrypted_data) => {
            info!("Data encrypted successfully");
            Ok(EncryptDataResponse {
                encrypted_data,
                success: true,
                message: "Data encrypted successfully".to_string(),
            })
        }
        Err(e) => {
            error!("Failed to encrypt data: {}", e);
            Ok(EncryptDataResponse {
                encrypted_data: Vec::new(),
                success: false,
                message: format!("Encryption failed: {}", e),
            })
        }
    }
}

/// Decrypt data using specified key
#[command]
pub async fn decrypt_data(
    request: DecryptDataRequest,
    security_state: State<'_, SecurityState>,
) -> Result<DecryptDataResponse, String> {
    info!("Decrypting data with key: {}", request.key_id);
    
    match security_state.manager.decrypt_data(&request.encrypted_data, &request.key_id).await {
        Ok(decrypted_data) => {
            info!("Data decrypted successfully");
            Ok(DecryptDataResponse {
                decrypted_data,
                success: true,
                message: "Data decrypted successfully".to_string(),
            })
        }
        Err(e) => {
            error!("Failed to decrypt data: {}", e);
            Ok(DecryptDataResponse {
                decrypted_data: Vec::new(),
                success: false,
                message: format!("Decryption failed: {}", e),
            })
        }
    }
}

/// Encrypt file at specified path
#[command]
pub async fn encrypt_file(
    request: EncryptFileRequest,
    security_state: State<'_, SecurityState>,
) -> Result<EncryptFileResponse, String> {
    info!("Encrypting file: {}", request.file_path);
    
    let file_path = PathBuf::from(&request.file_path);
    
    match security_state.manager.encrypt_file(&file_path, &request.key_id).await {
        Ok(encrypted_path) => {
            info!("File encrypted successfully: {}", encrypted_path.display());
            Ok(EncryptFileResponse {
                encrypted_path: encrypted_path.to_string_lossy().to_string(),
                success: true,
                message: "File encrypted successfully".to_string(),
            })
        }
        Err(e) => {
            error!("Failed to encrypt file: {}", e);
            Ok(EncryptFileResponse {
                encrypted_path: String::new(),
                success: false,
                message: format!("File encryption failed: {}", e),
            })
        }
    }
}

/// Decrypt file at specified path
#[command]
pub async fn decrypt_file(
    request: DecryptFileRequest,
    security_state: State<'_, SecurityState>,
) -> Result<DecryptFileResponse, String> {
    info!("Decrypting file: {}", request.encrypted_path);
    
    let encrypted_path = PathBuf::from(&request.encrypted_path);
    
    match security_state.manager.decrypt_file(&encrypted_path, &request.key_id).await {
        Ok(decrypted_path) => {
            info!("File decrypted successfully: {}", decrypted_path.display());
            Ok(DecryptFileResponse {
                decrypted_path: decrypted_path.to_string_lossy().to_string(),
                success: true,
                message: "File decrypted successfully".to_string(),
            })
        }
        Err(e) => {
            error!("Failed to decrypt file: {}", e);
            Ok(DecryptFileResponse {
                decrypted_path: String::new(),
                success: false,
                message: format!("File decryption failed: {}", e),
            })
        }
    }
}

/// Generate new encryption key
#[command]
pub async fn generate_encryption_key(
    request: GenerateKeyRequest,
    security_state: State<'_, SecurityState>,
) -> Result<GenerateKeyResponse, String> {
    info!("Generating new encryption key: {}", request.key_id);
    
    match security_state.manager.generate_key(&request.key_id).await {
        Ok(key_id) => {
            info!("Encryption key generated successfully: {}", key_id);
            Ok(GenerateKeyResponse {
                key_id,
                success: true,
                message: "Encryption key generated successfully".to_string(),
            })
        }
        Err(e) => {
            error!("Failed to generate encryption key: {}", e);
            Ok(GenerateKeyResponse {
                key_id: String::new(),
                success: false,
                message: format!("Key generation failed: {}", e),
            })
        }
    }
}

/// Rotate encryption key
#[command]
pub async fn rotate_encryption_key(
    request: GenerateKeyRequest,
    security_state: State<'_, SecurityState>,
) -> Result<GenerateKeyResponse, String> {
    info!("Rotating encryption key: {}", request.key_id);
    
    match security_state.manager.rotate_key(&request.key_id).await {
        Ok(new_key_id) => {
            info!("Encryption key rotated successfully: {}", new_key_id);
            Ok(GenerateKeyResponse {
                key_id: new_key_id,
                success: true,
                message: "Encryption key rotated successfully".to_string(),
            })
        }
        Err(e) => {
            error!("Failed to rotate encryption key: {}", e);
            Ok(GenerateKeyResponse {
                key_id: String::new(),
                success: false,
                message: format!("Key rotation failed: {}", e),
            })
        }
    }
}

/// Check user permissions
#[command]
pub async fn check_user_permission(
    request: CheckPermissionRequest,
    security_state: State<'_, SecurityState>,
) -> Result<CheckPermissionResponse, String> {
    info!("Checking permission for user: {} on resource: {}", request.user_id, request.resource);
    
    let permission = match request.permission.as_str() {
        "read" => Permission::Read,
        "write" => Permission::Write,
        "delete" => Permission::Delete,
        "execute" => Permission::Execute,
        "admin" => Permission::Admin,
        _ => {
            return Ok(CheckPermissionResponse {
                has_permission: false,
                success: false,
                message: format!("Unknown permission: {}", request.permission),
            });
        }
    };
    
    match security_state.manager.check_permission(&request.user_id, &request.resource, permission).await {
        Ok(has_permission) => {
            Ok(CheckPermissionResponse {
                has_permission,
                success: true,
                message: if has_permission { "Permission granted".to_string() } else { "Permission denied".to_string() },
            })
        }
        Err(e) => {
            error!("Failed to check permission: {}", e);
            Ok(CheckPermissionResponse {
                has_permission: false,
                success: false,
                message: format!("Permission check failed: {}", e),
            })
        }
    }
}

/// Create user session
#[command]
pub async fn create_user_session(
    request: CreateSessionRequest,
    security_state: State<'_, SecurityState>,
) -> Result<CreateSessionResponse, String> {
    info!("Creating session for user: {}", request.user_id);
    
    match security_state.manager.create_session(&request.user_id).await {
        Ok(session_id) => {
            info!("Session created successfully for user: {}", request.user_id);
            Ok(CreateSessionResponse {
                session_id,
                success: true,
                message: "Session created successfully".to_string(),
            })
        }
        Err(e) => {
            error!("Failed to create session: {}", e);
            Ok(CreateSessionResponse {
                session_id: String::new(),
                success: false,
                message: format!("Session creation failed: {}", e),
            })
        }
    }
}

/// Validate user session
#[command]
pub async fn validate_user_session(
    request: ValidateSessionRequest,
    security_state: State<'_, SecurityState>,
) -> Result<ValidateSessionResponse, String> {
    match security_state.manager.validate_session(&request.session_id).await {
        Ok(is_valid) => {
            Ok(ValidateSessionResponse {
                is_valid,
                success: true,
                message: if is_valid { "Session is valid".to_string() } else { "Session is invalid".to_string() },
            })
        }
        Err(e) => {
            error!("Failed to validate session: {}", e);
            Ok(ValidateSessionResponse {
                is_valid: false,
                success: false,
                message: format!("Session validation failed: {}", e),
            })
        }
    }
}

/// Get audit log entries
#[command]
pub async fn get_security_audit_log(
    request: GetAuditLogRequest,
    security_state: State<'_, SecurityState>,
) -> Result<GetAuditLogResponse, String> {
    info!("Getting audit log entries, limit: {:?}", request.limit);
    
    match security_state.manager.get_audit_log(request.limit).await {
        Ok(entries) => {
            info!("Retrieved {} audit log entries", entries.len());
            Ok(GetAuditLogResponse {
                entries,
                success: true,
                message: "Audit log retrieved successfully".to_string(),
            })
        }
        Err(e) => {
            error!("Failed to get audit log: {}", e);
            Ok(GetAuditLogResponse {
                entries: Vec::new(),
                success: false,
                message: format!("Failed to retrieve audit log: {}", e),
            })
        }
    }
}

/// Hash data for integrity verification
#[command]
pub async fn hash_data(
    request: HashDataRequest,
    security_state: State<'_, SecurityState>,
) -> Result<HashDataResponse, String> {
    let hash = security_state.manager.hash_data(&request.data);
    
    Ok(HashDataResponse {
        hash,
        success: true,
        message: "Data hashed successfully".to_string(),
    })
}

/// Verify data integrity
#[command]
pub async fn verify_data_integrity(
    request: VerifyIntegrityRequest,
    security_state: State<'_, SecurityState>,
) -> Result<VerifyIntegrityResponse, String> {
    let is_valid = security_state.manager.verify_integrity(&request.data, &request.expected_hash);
    
    Ok(VerifyIntegrityResponse {
        is_valid,
        success: true,
        message: if is_valid { "Data integrity verified".to_string() } else { "Data integrity check failed".to_string() },
    })
}

/// Get security statistics
#[command]
pub async fn get_security_statistics(
    security_state: State<'_, SecurityState>,
) -> Result<SecurityStats, String> {
    match security_state.manager.get_security_stats().await {
        Ok(stats) => {
            info!("Security statistics retrieved successfully");
            Ok(stats)
        }
        Err(e) => {
            error!("Failed to get security statistics: {}", e);
            Err(format!("Failed to retrieve security statistics: {}", e))
        }
    }
}

/// Log security event manually
#[command]
pub async fn log_security_event(
    event_type: String,
    resource: String,
    details: String,
    security_state: State<'_, SecurityState>,
) -> Result<bool, String> {
    let event = match event_type.as_str() {
        "data_access" => SecurityEvent::DataAccess { resource, action: details },
        "security_violation" => SecurityEvent::SecurityViolation { violation_type: resource, details },
        _ => SecurityEvent::SecurityViolation { violation_type: event_type, details },
    };
    
    security_state.manager.log_security_event(event).await;
    Ok(true)
}
