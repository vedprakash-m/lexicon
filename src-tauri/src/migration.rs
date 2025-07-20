use crate::schema_version::{SchemaVersion, SchemaVersionManager};
use rusqlite::{Connection, Result as SqliteResult, OptionalExtension};
use serde::{Deserialize, Serialize};
use std::fmt;
use std::time::Instant;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MigrationResult {
    pub success: bool,
    pub from_version: SchemaVersion,
    pub to_version: SchemaVersion,
    pub duration_ms: u64,
    pub steps_completed: u32,
    pub steps_total: u32,
    pub error: Option<String>,
}

#[derive(Debug)]
pub enum MigrationError {
    DatabaseError(rusqlite::Error),
    VersionError(String),
    ExecutionError(String),
}

impl fmt::Display for MigrationError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            MigrationError::DatabaseError(e) => write!(f, "Database error: {}", e),
            MigrationError::VersionError(e) => write!(f, "Version error: {}", e),
            MigrationError::ExecutionError(e) => write!(f, "Execution error: {}", e),
        }
    }
}

impl From<rusqlite::Error> for MigrationError {
    fn from(error: rusqlite::Error) -> Self {
        MigrationError::DatabaseError(error)
    }
}

pub trait Migration {
    fn version(&self) -> &SchemaVersion;
    fn description(&self) -> &str;
    fn up(&self, conn: &Connection) -> Result<(), MigrationError>;
    fn down(&self, conn: &Connection) -> Result<(), MigrationError>;
    fn validate(&self, conn: &Connection) -> Result<bool, MigrationError>;
}

pub struct MigrationEngine {
    migrations: Vec<Box<dyn Migration>>,
    schema_manager: SchemaVersionManager,
}

impl MigrationEngine {
    pub fn new(schema_manager: SchemaVersionManager) -> Self {
        Self {
            migrations: Vec::new(),
            schema_manager,
        }
    }

    pub fn register_migration(&mut self, migration: Box<dyn Migration>) {
        self.migrations.push(migration);
    }

    pub fn get_current_db_version(&self, conn: &mut Connection) -> Result<SchemaVersion, MigrationError> {
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_version (
                version TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )",
            [],
        )?;

        let version: Option<String> = conn.query_row(
            "SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1",
            [],
            |row| row.get(0),
        ).optional()?;

        match version {
            Some(v) => v.parse::<SchemaVersion>().map_err(|e| MigrationError::VersionError(e)),
            None => Ok(SchemaVersion::new(0, 0, 0)),
        }
    }

    pub fn migrate_to_latest(&self, conn: &mut Connection) -> Result<MigrationResult, MigrationError> {
        let current_version = self.get_current_db_version(conn)?;
        let target_version = self.schema_manager.get_current_version().clone();
        self.migrate(conn, &current_version, &target_version)
    }

    pub fn migrate(
        &self,
        conn: &mut Connection,
        from_version: &SchemaVersion,
        to_version: &SchemaVersion,
    ) -> Result<MigrationResult, MigrationError> {
        if from_version == to_version {
            return Ok(MigrationResult {
                success: true,
                from_version: from_version.clone(),
                to_version: to_version.clone(),
                duration_ms: 0,
                steps_completed: 0,
                steps_total: 0,
                error: None,
            });
        }

        let mut migrations_to_apply: Vec<&Box<dyn Migration>> = self
            .migrations
            .iter()
            .filter(|m| m.version() > from_version && m.version() <= to_version)
            .collect();
        migrations_to_apply.sort_by_key(|m| m.version());

        let steps_total = migrations_to_apply.len() as u32;
        let mut steps_completed = 0;
        let start_time = Instant::now();

        let tx = conn.transaction()?;

        for migration in migrations_to_apply {
            match migration.up(&tx) {
                Ok(_) => {
                    if !migration.validate(&tx)? {
                        return Ok(MigrationResult {
                            success: false,
                            from_version: from_version.clone(),
                            to_version: to_version.clone(),
                            duration_ms: start_time.elapsed().as_millis() as u64,
                            steps_completed,
                            steps_total,
                            error: Some(format!("Migration validation failed for version {}", migration.version())),
                        });
                    }

                    tx.execute(
                        "INSERT INTO schema_version (version) VALUES (?)",
                        [migration.version().to_string()],
                    )?;
                    steps_completed += 1;
                }
                Err(e) => {
                    return Ok(MigrationResult {
                        success: false,
                        from_version: from_version.clone(),
                        to_version: to_version.clone(),
                        duration_ms: start_time.elapsed().as_millis() as u64,
                        steps_completed,
                        steps_total,
                        error: Some(e.to_string()),
                    });
                }
            }
        }

        tx.commit()?;

        Ok(MigrationResult {
            success: true,
            from_version: from_version.clone(),
            to_version: to_version.clone(),
            duration_ms: start_time.elapsed().as_millis() as u64,
            steps_completed,
            steps_total,
            error: None,
        })
    }
}