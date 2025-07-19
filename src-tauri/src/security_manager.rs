use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tokio::sync::Mutex;
use serde::{Deserialize, Serialize};
use anyhow::{Result, anyhow};
use chrono::{DateTime, Utc};
use aes_gcm::{Aes256Gcm, Key, Nonce, aead::{Aead, KeyInit}};
use rand::{RngCore, thread_rng};
use sha2::{Sha256, Digest};
use log::{info, error, debug};
use uuid::Uuid;

/// Security configuration for the application
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecurityConfig {
    pub encryption_enabled: bool,
    pub audit_logging_enabled: bool,
    pub access_control_enabled: bool,
    pub key_rotation_interval_days: u32,
    pub max_failed_attempts: u32,
    pub lockout_duration_minutes: u32,
}

impl Default for SecurityConfig {
    fn default() -> Self {
        Self {
            encryption_enabled: true,
            audit_logging_enabled: true,
            access_control_enabled: true,
            key_rotation_interval_days: 30,
            max_failed_attempts: 5,
            lockout_duration_minutes: 15,
        }
    }
}

/// Security event types for audit logging
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SecurityEvent {
    DataAccess { resource: String, action: String },
    AuthenticationAttempt { success: bool, user: String },
    EncryptionOperation { operation: String, resource: String },
    KeyRotation { key_id: String },
    AccessDenied { resource: String, reason: String },
    SecurityViolation { violation_type: String, details: String },
}

/// Audit log entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditLogEntry {
    pub id: String,
    pub timestamp: DateTime<Utc>,
    pub event: SecurityEvent,
    pub ip_address: Option<String>,
    pub user_agent: Option<String>,
    pub session_id: Option<String>,
}

/// Encryption key information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EncryptionKey {
    pub id: String,
    pub created_at: DateTime<Utc>,
    pub last_used: DateTime<Utc>,
    pub algorithm: String,
    pub key_size: u32,
    pub is_active: bool,
}

/// Access control permissions
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum Permission {
    Read,
    Write,
    Delete,
    Execute,
    Admin,
}

/// User access information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserAccess {
    pub user_id: String,
    pub permissions: Vec<Permission>,
    pub last_access: DateTime<Utc>,
    pub failed_attempts: u32,
    pub locked_until: Option<DateTime<Utc>>,
}

/// Security manager state
pub struct SecurityManager {
    config: SecurityConfig,
    encryption_keys: Arc<Mutex<HashMap<String, Vec<u8>>>>,
    key_metadata: Arc<Mutex<HashMap<String, EncryptionKey>>>,
    audit_log: Arc<Mutex<Vec<AuditLogEntry>>>,
    user_access: Arc<Mutex<HashMap<String, UserAccess>>>,
    active_sessions: Arc<Mutex<HashMap<String, DateTime<Utc>>>>,
    security_root: PathBuf,
}

impl SecurityManager {
    /// Create a new security manager
    pub fn new(security_root: PathBuf) -> Result<Self> {
        // Ensure security directory exists
        fs::create_dir_all(&security_root)?;
        
        let config = SecurityConfig::default();
        
        let manager = Self {
            config,
            encryption_keys: Arc::new(Mutex::new(HashMap::new())),
            key_metadata: Arc::new(Mutex::new(HashMap::new())),
            audit_log: Arc::new(Mutex::new(Vec::new())),
            user_access: Arc::new(Mutex::new(HashMap::new())),
            active_sessions: Arc::new(Mutex::new(HashMap::new())),
            security_root,
        };
        
        // Initialize with default master key
        manager.initialize_master_key()?;
        
        Ok(manager)
    }
    
    /// Initialize master encryption key
    fn initialize_master_key(&self) -> Result<()> {
        let key_id = "master".to_string();
        let mut key_data = vec![0u8; 32]; // AES-256 key size
        thread_rng().fill_bytes(&mut key_data);
        
        let _key_metadata = EncryptionKey {
            id: key_id.clone(),
            created_at: Utc::now(),
            last_used: Utc::now(),
            algorithm: "AES-256-GCM".to_string(),
            key_size: 256,
            is_active: true,
        };
        
        // Store key securely (in production, use secure key storage)
        let key_path = self.security_root.join("master.key");
        fs::write(&key_path, &key_data)?;
        
        info!("Master encryption key initialized");
        Ok(())
    }
    
    /// Encrypt data using the specified key
    pub async fn encrypt_data(&self, data: &[u8], key_id: &str) -> Result<Vec<u8>> {
        let keys = self.encryption_keys.lock().await;
        
        let key_data = if let Some(key) = keys.get(key_id) {
            key.clone()
        } else {
            // Try to load key from disk
            let key_path = self.security_root.join(format!("{}.key", key_id));
            if key_path.exists() {
                fs::read(&key_path)?
            } else {
                return Err(anyhow!("Encryption key not found: {}", key_id));
            }
        };
        
        let key = Key::<Aes256Gcm>::from_slice(&key_data);
        let cipher = Aes256Gcm::new(key);
        
        // Generate random nonce
        let mut nonce_bytes = [0u8; 12];
        thread_rng().fill_bytes(&mut nonce_bytes);
        let nonce = Nonce::from_slice(&nonce_bytes);
        
        // Encrypt data
        let ciphertext = cipher.encrypt(nonce, data)
            .map_err(|e| anyhow!("Encryption failed: {}", e))?;
        
        // Combine nonce and ciphertext
        let mut result = nonce_bytes.to_vec();
        result.extend_from_slice(&ciphertext);
        
        // Log security event
        self.log_security_event(SecurityEvent::EncryptionOperation {
            operation: "encrypt".to_string(),
            resource: key_id.to_string(),
        }).await;
        
        Ok(result)
    }
    
    /// Decrypt data using the specified key
    pub async fn decrypt_data(&self, encrypted_data: &[u8], key_id: &str) -> Result<Vec<u8>> {
        if encrypted_data.len() < 12 {
            return Err(anyhow!("Invalid encrypted data format"));
        }
        
        let keys = self.encryption_keys.lock().await;
        
        let key_data = if let Some(key) = keys.get(key_id) {
            key.clone()
        } else {
            // Try to load key from disk
            let key_path = self.security_root.join(format!("{}.key", key_id));
            if key_path.exists() {
                fs::read(&key_path)?
            } else {
                return Err(anyhow!("Decryption key not found: {}", key_id));
            }
        };
        
        let key = Key::<Aes256Gcm>::from_slice(&key_data);
        let cipher = Aes256Gcm::new(key);
        
        // Extract nonce and ciphertext
        let nonce = Nonce::from_slice(&encrypted_data[..12]);
        let ciphertext = &encrypted_data[12..];
        
        // Decrypt data
        let plaintext = cipher.decrypt(nonce, ciphertext)
            .map_err(|e| anyhow!("Decryption failed: {}", e))?;
        
        // Log security event
        self.log_security_event(SecurityEvent::EncryptionOperation {
            operation: "decrypt".to_string(),
            resource: key_id.to_string(),
        }).await;
        
        Ok(plaintext)
    }
    
    /// Encrypt file at the specified path
    pub async fn encrypt_file(&self, file_path: &Path, key_id: &str) -> Result<PathBuf> {
        let data = fs::read(file_path)?;
        let encrypted_data = self.encrypt_data(&data, key_id).await?;
        
        let encrypted_path = file_path.with_extension("encrypted");
        fs::write(&encrypted_path, encrypted_data)?;
        
        info!("File encrypted: {} -> {}", file_path.display(), encrypted_path.display());
        Ok(encrypted_path)
    }
    
    /// Decrypt file at the specified path
    pub async fn decrypt_file(&self, encrypted_path: &Path, key_id: &str) -> Result<PathBuf> {
        let encrypted_data = fs::read(encrypted_path)?;
        let decrypted_data = self.decrypt_data(&encrypted_data, key_id).await?;
        
        let decrypted_path = encrypted_path.with_extension("");
        fs::write(&decrypted_path, decrypted_data)?;
        
        info!("File decrypted: {} -> {}", encrypted_path.display(), decrypted_path.display());
        Ok(decrypted_path)
    }
    
    /// Generate a new encryption key
    pub async fn generate_key(&self, key_id: &str) -> Result<String> {
        let mut key_data = vec![0u8; 32]; // AES-256 key size
        thread_rng().fill_bytes(&mut key_data);
        
        let key_metadata = EncryptionKey {
            id: key_id.to_string(),
            created_at: Utc::now(),
            last_used: Utc::now(),
            algorithm: "AES-256-GCM".to_string(),
            key_size: 256,
            is_active: true,
        };
        
        // Store key securely
        let key_path = self.security_root.join(format!("{}.key", key_id));
        fs::write(&key_path, &key_data)?;
        
        // Update in-memory storage
        let mut keys = self.encryption_keys.lock().await;
        keys.insert(key_id.to_string(), key_data);
        
        let mut metadata = self.key_metadata.lock().await;
        metadata.insert(key_id.to_string(), key_metadata);
        
        self.log_security_event(SecurityEvent::KeyRotation {
            key_id: key_id.to_string(),
        }).await;
        
        info!("New encryption key generated: {}", key_id);
        Ok(key_id.to_string())
    }
    
    /// Rotate encryption key
    pub async fn rotate_key(&self, key_id: &str) -> Result<String> {
        let new_key_id = format!("{}_v{}", key_id, Utc::now().timestamp());
        self.generate_key(&new_key_id).await?;
        
        // Mark old key as inactive
        let mut metadata = self.key_metadata.lock().await;
        if let Some(old_key) = metadata.get_mut(key_id) {
            old_key.is_active = false;
        }
        
        info!("Key rotated: {} -> {}", key_id, new_key_id);
        Ok(new_key_id)
    }
    
    /// Check if user has permission for resource
    pub async fn check_permission(&self, user_id: &str, resource: &str, permission: Permission) -> Result<bool> {
        let access_map = self.user_access.lock().await;
        
        if let Some(user_access) = access_map.get(user_id) {
            // Check if user is locked out
            if let Some(locked_until) = user_access.locked_until {
                if Utc::now() < locked_until {
                    self.log_security_event(SecurityEvent::AccessDenied {
                        resource: resource.to_string(),
                        reason: "User locked out".to_string(),
                    }).await;
                    return Ok(false);
                }
            }
            
            // Check permissions
            let has_permission = user_access.permissions.contains(&permission) || 
                                user_access.permissions.contains(&Permission::Admin);
            
            if !has_permission {
                self.log_security_event(SecurityEvent::AccessDenied {
                    resource: resource.to_string(),
                    reason: "Insufficient permissions".to_string(),
                }).await;
            }
            
            Ok(has_permission)
        } else {
            self.log_security_event(SecurityEvent::AccessDenied {
                resource: resource.to_string(),
                reason: "User not found".to_string(),
            }).await;
            Ok(false)
        }
    }
    
    /// Log security event
    pub async fn log_security_event(&self, event: SecurityEvent) {
        let entry = AuditLogEntry {
            id: Uuid::new_v4().to_string(),
            timestamp: Utc::now(),
            event,
            ip_address: None, // Could be populated from request context
            user_agent: None,
            session_id: None,
        };
        
        let mut log = self.audit_log.lock().await;
        log.push(entry.clone());
        
        // Write to audit log file
        let log_path = self.security_root.join("audit.log");
        if let Ok(log_content) = serde_json::to_string(&entry) {
            if let Err(e) = fs::OpenOptions::new()
                .create(true)
                .append(true)
                .open(&log_path)
                .and_then(|mut file| {
                    use std::io::Write;
                    writeln!(file, "{}", log_content)
                })
            {
                error!("Failed to write audit log: {}", e);
            }
        }
        
        debug!("Security event logged: {:?}", entry);
    }
    
    /// Get audit log entries
    pub async fn get_audit_log(&self, limit: Option<usize>) -> Result<Vec<AuditLogEntry>> {
        let log = self.audit_log.lock().await;
        let entries = if let Some(limit) = limit {
            log.iter().rev().take(limit).cloned().collect()
        } else {
            log.clone()
        };
        Ok(entries)
    }
    
    /// Create user session
    pub async fn create_session(&self, user_id: &str) -> Result<String> {
        let session_id = Uuid::new_v4().to_string();
        let mut sessions = self.active_sessions.lock().await;
        sessions.insert(session_id.clone(), Utc::now());
        
        self.log_security_event(SecurityEvent::AuthenticationAttempt {
            success: true,
            user: user_id.to_string(),
        }).await;
        
        Ok(session_id)
    }
    
    /// Validate session
    pub async fn validate_session(&self, session_id: &str) -> Result<bool> {
        let sessions = self.active_sessions.lock().await;
        Ok(sessions.contains_key(session_id))
    }
    
    /// Hash sensitive data
    pub fn hash_data(&self, data: &[u8]) -> String {
        let mut hasher = Sha256::new();
        hasher.update(data);
        format!("{:x}", hasher.finalize())
    }
    
    /// Verify data integrity
    pub fn verify_integrity(&self, data: &[u8], expected_hash: &str) -> bool {
        let actual_hash = self.hash_data(data);
        actual_hash == expected_hash
    }
    
    /// Get security statistics
    pub async fn get_security_stats(&self) -> Result<SecurityStats> {
        let log = self.audit_log.lock().await;
        let keys = self.key_metadata.lock().await;
        let sessions = self.active_sessions.lock().await;
        
        let total_events = log.len();
        let active_keys = keys.values().filter(|k| k.is_active).count();
        let active_sessions = sessions.len();
        
        let recent_events = log.iter()
            .rev()
            .take(100)
            .filter(|entry| {
                let hours_ago = Utc::now() - chrono::Duration::hours(24);
                entry.timestamp > hours_ago
            })
            .count();
        
        Ok(SecurityStats {
            total_audit_events: total_events,
            recent_events_24h: recent_events,
            active_encryption_keys: active_keys,
            active_sessions,
            last_key_rotation: keys.values()
                .filter(|k| k.is_active)
                .map(|k| k.created_at)
                .max(),
        })
    }
}

/// Security statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecurityStats {
    pub total_audit_events: usize,
    pub recent_events_24h: usize,
    pub active_encryption_keys: usize,
    pub active_sessions: usize,
    pub last_key_rotation: Option<DateTime<Utc>>,
}

/// Security error types
#[derive(Debug, thiserror::Error)]
pub enum SecurityError {
    #[error("Encryption failed: {0}")]
    EncryptionError(String),
    
    #[error("Decryption failed: {0}")]
    DecryptionError(String),
    
    #[error("Key not found: {0}")]
    KeyNotFound(String),
    
    #[error("Access denied: {0}")]
    AccessDenied(String),
    
    #[error("Authentication failed: {0}")]
    AuthenticationFailed(String),
    
    #[error("Security violation: {0}")]
    SecurityViolation(String),
    
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
    
    #[error("Serialization error: {0}")]
    SerializationError(#[from] serde_json::Error),
}

pub type SecurityResult<T> = std::result::Result<T, SecurityError>;
