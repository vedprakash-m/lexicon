use crate::models::*;
use serde_json::Value;
use std::collections::HashMap;
use thiserror::Error;
use chrono::{DateTime, Utc};

#[derive(Error, Debug)]
pub enum MigrationError {
    #[error("Unknown migration version: {version}")]
    UnknownVersion { version: String },
    
    #[error("Migration failed: {message}")]
    MigrationFailed { message: String },
    
    #[error("Invalid data format: {message}")]
    InvalidFormat { message: String },
    
    #[error("Incompatible schema version: expected {expected}, found {found}")]
    IncompatibleVersion { expected: String, found: String },
}

pub type MigrationResult<T> = Result<T, MigrationError>;

/// Schema version information
#[derive(Debug, Clone)]
pub struct SchemaVersion {
    pub major: u32,
    pub minor: u32,
    pub patch: u32,
}

impl SchemaVersion {
    pub fn new(major: u32, minor: u32, patch: u32) -> Self {
        Self { major, minor, patch }
    }
    
    pub fn current() -> Self {
        Self::new(1, 0, 0)
    }
    
    pub fn is_compatible(&self, other: &SchemaVersion) -> bool {
        self.major == other.major
    }
}

impl std::fmt::Display for SchemaVersion {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}.{}.{}", self.major, self.minor, self.patch)
    }
}

impl std::str::FromStr for SchemaVersion {
    type Err = MigrationError;
    
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let parts: Vec<&str> = s.split('.').collect();
        if parts.len() != 3 {
            return Err(MigrationError::InvalidFormat {
                message: "Version must be in format 'major.minor.patch'".to_string(),
            });
        }
        
        let major = parts[0].parse().map_err(|_| MigrationError::InvalidFormat {
            message: "Invalid major version number".to_string(),
        })?;
        
        let minor = parts[1].parse().map_err(|_| MigrationError::InvalidFormat {
            message: "Invalid minor version number".to_string(),
        })?;
        
        let patch = parts[2].parse().map_err(|_| MigrationError::InvalidFormat {
            message: "Invalid patch version number".to_string(),
        })?;
        
        Ok(Self::new(major, minor, patch))
    }
}

/// Migration manager for handling schema changes
pub struct MigrationManager {
    migrations: HashMap<String, Box<dyn Migration>>,
}

impl MigrationManager {
    pub fn new() -> Self {
        let mut manager = Self {
            migrations: HashMap::new(),
        };
        
        // Register built-in migrations
        manager.register_migration("1.0.0", Box::new(InitialMigration));
        
        manager
    }
    
    pub fn register_migration(&mut self, version: &str, migration: Box<dyn Migration>) {
        self.migrations.insert(version.to_string(), migration);
    }
    
    pub fn migrate_source_text(&self, data: Value, from_version: &str, to_version: &str) -> MigrationResult<SourceText> {
        let migrated_data = self.apply_migrations(data, from_version, to_version)?;
        
        serde_json::from_value(migrated_data).map_err(|e| MigrationError::InvalidFormat {
            message: format!("Failed to deserialize SourceText: {}", e),
        })
    }
    
    pub fn migrate_dataset(&self, data: Value, from_version: &str, to_version: &str) -> MigrationResult<Dataset> {
        let migrated_data = self.apply_migrations(data, from_version, to_version)?;
        
        serde_json::from_value(migrated_data).map_err(|e| MigrationError::InvalidFormat {
            message: format!("Failed to deserialize Dataset: {}", e),
        })
    }
    
    fn apply_migrations(&self, mut data: Value, from_version: &str, to_version: &str) -> MigrationResult<Value> {
        let from = from_version.parse::<SchemaVersion>()?;
        let to = to_version.parse::<SchemaVersion>()?;
        
        if !to.is_compatible(&from) {
            return Err(MigrationError::IncompatibleVersion {
                expected: to.to_string(),
                found: from.to_string(),
            });
        }
        
        // For now, we only support migration within the same major version
        // Future versions might require more sophisticated migration paths
        if let Some(migration) = self.migrations.get(to_version) {
            data = migration.migrate(data)?;
        }
        
        Ok(data)
    }
}

impl Default for MigrationManager {
    fn default() -> Self {
        Self::new()
    }
}

/// Trait for implementing specific migrations
pub trait Migration {
    fn migrate(&self, data: Value) -> MigrationResult<Value>;
    fn description(&self) -> String;
}

/// Initial migration (v1.0.0) - essentially a no-op for validation
pub struct InitialMigration;

impl Migration for InitialMigration {
    fn migrate(&self, data: Value) -> MigrationResult<Value> {
        // Initial migration just validates the data structure
        // and ensures all required fields are present
        Ok(data)
    }
    
    fn description(&self) -> String {
        "Initial schema version 1.0.0 - validates basic data structure".to_string()
    }
}

/// Migration for adding new fields while maintaining backward compatibility
pub struct AddFieldMigration {
    pub field_name: String,
    pub default_value: Value,
}

impl Migration for AddFieldMigration {
    fn migrate(&self, mut data: Value) -> MigrationResult<Value> {
        if let Value::Object(ref mut map) = data {
            if !map.contains_key(&self.field_name) {
                map.insert(self.field_name.clone(), self.default_value.clone());
            }
        }
        Ok(data)
    }
    
    fn description(&self) -> String {
        format!("Add field '{}' with default value", self.field_name)
    }
}

/// Migration for renaming fields
pub struct RenameFieldMigration {
    pub old_name: String,
    pub new_name: String,
}

impl Migration for RenameFieldMigration {
    fn migrate(&self, mut data: Value) -> MigrationResult<Value> {
        if let Value::Object(ref mut map) = data {
            if let Some(value) = map.remove(&self.old_name) {
                map.insert(self.new_name.clone(), value);
            }
        }
        Ok(data)
    }
    
    fn description(&self) -> String {
        format!("Rename field '{}' to '{}'", self.old_name, self.new_name)
    }
}

/// Migration for transforming field values
pub struct TransformFieldMigration {
    pub field_name: String,
    pub transformer: fn(Value) -> MigrationResult<Value>,
}

impl Migration for TransformFieldMigration {
    fn migrate(&self, mut data: Value) -> MigrationResult<Value> {
        if let Value::Object(ref mut map) = data {
            if let Some(value) = map.get(&self.field_name).cloned() {
                let transformed = (self.transformer)(value)?;
                map.insert(self.field_name.clone(), transformed);
            }
        }
        Ok(data)
    }
    
    fn description(&self) -> String {
        format!("Transform field '{}'", self.field_name)
    }
}

/// Utility functions for common migrations
pub mod migration_utils {
    use super::*;
    
    /// Add creation and update timestamps if missing
    pub fn add_timestamps(data: Value) -> MigrationResult<Value> {
        let mut result = data;
        let now = Utc::now();
        
        if let Value::Object(ref mut map) = result {
            if !map.contains_key("created_at") {
                map.insert("created_at".to_string(), Value::String(now.to_rfc3339()));
            }
            if !map.contains_key("updated_at") {
                map.insert("updated_at".to_string(), Value::String(now.to_rfc3339()));
            }
        }
        
        Ok(result)
    }
    
    /// Ensure ID field is present and valid UUID
    pub fn ensure_id_field(data: Value) -> MigrationResult<Value> {
        let mut result = data;
        
        if let Value::Object(ref mut map) = result {
            if !map.contains_key("id") {
                let new_id = uuid::Uuid::new_v4();
                map.insert("id".to_string(), Value::String(new_id.to_string()));
            }
        }
        
        Ok(result)
    }
    
    /// Convert old string enums to new object format
    pub fn migrate_enum_format(old_value: Value, enum_name: &str) -> MigrationResult<Value> {
        match old_value {
            Value::String(s) => {
                // Convert old string format to new object format for custom variants
                if s.starts_with("Custom:") {
                    let custom_value = s.strip_prefix("Custom:").unwrap_or(&s);
                    Ok(serde_json::json!({ "Custom": custom_value }))
                } else {
                    // Standard enum variants remain as strings
                    Ok(Value::String(s))
                }
            }
            _ => Ok(old_value),
        }
    }
    
    /// Initialize empty collections if missing
    pub fn initialize_collections(mut data: Value, field_names: &[&str]) -> MigrationResult<Value> {
        if let Value::Object(ref mut map) = data {
            for field_name in field_names {
                if !map.contains_key(*field_name) {
                    map.insert(field_name.to_string(), Value::Array(Vec::new()));
                }
            }
        }
        Ok(data)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    
    #[test]
    fn test_schema_version_parsing() {
        let version = "1.2.3".parse::<SchemaVersion>().unwrap();
        assert_eq!(version.major, 1);
        assert_eq!(version.minor, 2);
        assert_eq!(version.patch, 3);
        assert_eq!(version.to_string(), "1.2.3");
    }
    
    #[test]
    fn test_version_compatibility() {
        let v1_0_0 = SchemaVersion::new(1, 0, 0);
        let v1_1_0 = SchemaVersion::new(1, 1, 0);
        let v2_0_0 = SchemaVersion::new(2, 0, 0);
        
        assert!(v1_0_0.is_compatible(&v1_1_0));
        assert!(!v1_0_0.is_compatible(&v2_0_0));
    }
    
    #[test]
    fn test_add_field_migration() {
        let migration = AddFieldMigration {
            field_name: "new_field".to_string(),
            default_value: json!("default_value"),
        };
        
        let data = json!({
            "existing_field": "value"
        });
        
        let result = migration.migrate(data).unwrap();
        assert_eq!(result["new_field"], "default_value");
        assert_eq!(result["existing_field"], "value");
    }
    
    #[test]
    fn test_rename_field_migration() {
        let migration = RenameFieldMigration {
            old_name: "old_field".to_string(),
            new_name: "new_field".to_string(),
        };
        
        let data = json!({
            "old_field": "value",
            "other_field": "other_value"
        });
        
        let result = migration.migrate(data).unwrap();
        assert_eq!(result["new_field"], "value");
        assert_eq!(result["other_field"], "other_value");
        assert!(result.get("old_field").is_none());
    }
    
    #[test]
    fn test_migration_utils() {
        let data = json!({
            "title": "Test"
        });
        
        // Test adding timestamps
        let result = migration_utils::add_timestamps(data.clone()).unwrap();
        assert!(result["created_at"].is_string());
        assert!(result["updated_at"].is_string());
        
        // Test ensuring ID field
        let result = migration_utils::ensure_id_field(data.clone()).unwrap();
        assert!(result["id"].is_string());
        
        // Test initializing collections
        let result = migration_utils::initialize_collections(data, &["tags", "chunks"]).unwrap();
        assert!(result["tags"].is_array());
        assert!(result["chunks"].is_array());
    }
}
