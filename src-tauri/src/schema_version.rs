use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fmt;
use std::str::FromStr;

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct SchemaVersion {
    major: u32,
    minor: u32,
    patch: u32,
}

impl SchemaVersion {
    pub fn new(major: u32, minor: u32, patch: u32) -> Self {
        Self { major, minor, patch }
    }

    pub fn is_compatible_with(&self, other: &SchemaVersion) -> bool {
        self.major == other.major
    }

    pub fn requires_migration_from(&self, other: &SchemaVersion) -> bool {
        self > other
    }
}

impl fmt::Display for SchemaVersion {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}.{}.{}", self.major, self.minor, self.patch)
    }
}

impl FromStr for SchemaVersion {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let parts: Vec<&str> = s.split('.').collect();
        if parts.len() != 3 {
            return Err(format!("Invalid schema version format: {}", s));
        }

        let major = parts[0].parse::<u32>()
            .map_err(|_| format!("Invalid major version: {}", parts[0]))?;
        let minor = parts[1].parse::<u32>()
            .map_err(|_| format!("Invalid minor version: {}", parts[1]))?;
        let patch = parts[2].parse::<u32>()
            .map_err(|_| format!("Invalid patch version: {}", parts[2]))?;

        Ok(SchemaVersion { major, minor, patch })
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SchemaDefinition {
    pub version: SchemaVersion,
    pub description: String,
    pub tables: Vec<TableDefinition>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TableDefinition {
    pub name: String,
    pub columns: Vec<ColumnDefinition>,
    pub indices: Vec<IndexDefinition>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ColumnDefinition {
    pub name: String,
    pub data_type: String,
    pub nullable: bool,
    pub default_value: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IndexDefinition {
    pub name: String,
    pub columns: Vec<String>,
    pub unique: bool,
}

pub struct SchemaVersionManager {
    registry: HashMap<SchemaVersion, SchemaDefinition>,
    current_version: SchemaVersion,
}

impl SchemaVersionManager {
    pub fn new(current_version: SchemaVersion) -> Self {
        Self {
            registry: HashMap::new(),
            current_version,
        }
    }

    pub fn register_schema(&mut self, schema: SchemaDefinition) {
        self.registry.insert(schema.version.clone(), schema);
    }

    pub fn get_current_version(&self) -> &SchemaVersion {
        &self.current_version
    }

    pub fn get_schema(&self, version: &SchemaVersion) -> Option<&SchemaDefinition> {
        self.registry.get(version)
    }

    pub fn is_compatible_with(&self, version: &SchemaVersion) -> bool {
        self.current_version.is_compatible_with(version)
    }

    pub fn requires_migration_from(&self, version: &SchemaVersion) -> bool {
        self.current_version.requires_migration_from(version)
    }
}