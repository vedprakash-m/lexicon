use sqlx::{
    sqlite::{SqlitePool, SqlitePoolOptions, SqliteConnectOptions},
    Pool, Sqlite, Error as SqlxError, Row,
    migrate::MigrateDatabase,
};
use std::path::Path;
use std::time::Duration;
use chrono::{DateTime, Utc};
use uuid::Uuid;
use serde_json;
use serde::{Serialize, Deserialize};
use thiserror::Error;
use log::{info, error, warn, debug};

use crate::models::{
    SourceText, Dataset, ProcessingJob, AppSettings,
    TextChunk, ExportConfig, QualityMetrics
};

/// Database-related errors
#[derive(Error, Debug)]
pub enum DatabaseError {
    #[error("Database connection error: {0}")]
    Connection(#[from] SqlxError),
    
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
    
    #[error("Entity not found: {entity_type} with id {id}")]
    NotFound { entity_type: String, id: String },
    
    #[error("Database constraint violation: {0}")]
    Constraint(String),
    
    #[error("Database migration error: {0}")]
    Migration(String),
    
    #[error("Backup/Recovery error: {0}")]
    BackupRecovery(String),
    
    #[error("Data integrity error: {0}")]
    DataIntegrity(String),
}

pub type DatabaseResult<T> = Result<T, DatabaseError>;

/// Main database manager for local storage
pub struct Database {
    pool: Pool<Sqlite>,
    db_path: String,
}

/// Configuration for database connection
#[derive(Debug, Clone)]
pub struct DatabaseConfig {
    pub db_path: String,
    pub max_connections: u32,
    pub connection_timeout: Duration,
    pub enable_foreign_keys: bool,
    pub enable_wal_mode: bool,
    pub cache_size: i32,
}

impl Default for DatabaseConfig {
    fn default() -> Self {
        Self {
            db_path: "lexicon.db".to_string(),
            max_connections: 10,
            connection_timeout: Duration::from_secs(30),
            enable_foreign_keys: true,
            enable_wal_mode: true,
            cache_size: -64000, // 64MB cache
        }
    }
}

impl Database {
    /// Create a new database instance with the given configuration
    pub async fn new(config: DatabaseConfig) -> DatabaseResult<Self> {
        // Ensure the database directory exists
        if let Some(parent) = Path::new(&config.db_path).parent() {
            tokio::fs::create_dir_all(parent)
                .await
                .map_err(|e| DatabaseError::Connection(SqlxError::Io(e)))?;
        }

        // Create database if it doesn't exist
        if !Sqlite::database_exists(&config.db_path).await? {
            info!("Creating new database at: {}", config.db_path);
            Sqlite::create_database(&config.db_path).await?;
        }

        // Configure connection options
        let mut options = SqliteConnectOptions::new()
            .filename(&config.db_path)
            .create_if_missing(true);

        if config.enable_foreign_keys {
            options = options.foreign_keys(true);
        }

        if config.enable_wal_mode {
            options = options.journal_mode(sqlx::sqlite::SqliteJournalMode::Wal);
        }

        // Create connection pool
        let pool = SqlitePoolOptions::new()
            .max_connections(config.max_connections)
            .acquire_timeout(config.connection_timeout)
            .connect_with(options)
            .await?;

        // Set additional pragmas
        sqlx::query(&format!("PRAGMA cache_size = {}", config.cache_size))
            .execute(&pool)
            .await?;

        sqlx::query("PRAGMA temp_store = memory")
            .execute(&pool)
            .await?;

        sqlx::query("PRAGMA mmap_size = 268435456") // 256MB
            .execute(&pool)
            .await?;

        let database = Self {
            pool,
            db_path: config.db_path,
        };

        // Run migrations
        database.migrate().await?;

        info!("Database initialized successfully");
        Ok(database)
    }

    /// Run database migrations
    pub async fn migrate(&self) -> DatabaseResult<()> {
        info!("Running database migrations");

        // Create tables in dependency order
        self.create_source_texts_table().await?;
        self.create_datasets_table().await?;
        self.create_text_chunks_table().await?;
        self.create_processing_jobs_table().await?;
        self.create_export_configs_table().await?;
        self.create_app_settings_table().await?;
        
        // Create indexes for performance
        self.create_indexes().await?;

        info!("Database migrations completed successfully");
        Ok(())
    }

    /// Create the source_texts table
    async fn create_source_texts_table(&self) -> DatabaseResult<()> {
        sqlx::query(r#"
            CREATE TABLE IF NOT EXISTS source_texts (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT,
                language TEXT NOT NULL,
                source_type TEXT NOT NULL,
                file_path TEXT,
                url TEXT,
                metadata TEXT NOT NULL, -- JSON
                processing_status TEXT NOT NULL, -- JSON
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        "#)
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    /// Create the datasets table
    async fn create_datasets_table(&self) -> DatabaseResult<()> {
        sqlx::query(r#"
            CREATE TABLE IF NOT EXISTS datasets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                source_text_id TEXT NOT NULL,
                dataset_type TEXT NOT NULL,
                format TEXT NOT NULL,
                chunking_strategy TEXT NOT NULL, -- JSON
                quality_metrics TEXT NOT NULL, -- JSON
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (source_text_id) REFERENCES source_texts (id) ON DELETE CASCADE
            )
        "#)
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    /// Create the text_chunks table
    async fn create_text_chunks_table(&self) -> DatabaseResult<()> {
        sqlx::query(r#"
            CREATE TABLE IF NOT EXISTS text_chunks (
                id TEXT PRIMARY KEY,
                dataset_id TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT NOT NULL, -- JSON
                position TEXT NOT NULL, -- JSON
                quality_score REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (dataset_id) REFERENCES datasets (id) ON DELETE CASCADE
            )
        "#)
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    /// Create the processing_jobs table
    async fn create_processing_jobs_table(&self) -> DatabaseResult<()> {
        sqlx::query(r#"
            CREATE TABLE IF NOT EXISTS processing_jobs (
                id TEXT PRIMARY KEY,
                job_type TEXT NOT NULL,
                source_text_id TEXT,
                dataset_id TEXT,
                status TEXT NOT NULL,
                progress TEXT NOT NULL, -- JSON
                parameters TEXT NOT NULL, -- JSON
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                error_message TEXT,
                FOREIGN KEY (source_text_id) REFERENCES source_texts (id) ON DELETE SET NULL,
                FOREIGN KEY (dataset_id) REFERENCES datasets (id) ON DELETE SET NULL
            )
        "#)
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    /// Create the export_configs table
    async fn create_export_configs_table(&self) -> DatabaseResult<()> {
        sqlx::query(r#"
            CREATE TABLE IF NOT EXISTS export_configs (
                id TEXT PRIMARY KEY,
                dataset_id TEXT NOT NULL,
                name TEXT NOT NULL,
                platform TEXT NOT NULL,
                format TEXT NOT NULL,
                compression TEXT,
                filters TEXT NOT NULL, -- JSON
                transformations TEXT NOT NULL, -- JSON
                output_path TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (dataset_id) REFERENCES datasets (id) ON DELETE CASCADE
            )
        "#)
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    /// Create the app_settings table
    async fn create_app_settings_table(&self) -> DatabaseResult<()> {
        sqlx::query(r#"
            CREATE TABLE IF NOT EXISTS app_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                settings TEXT NOT NULL -- JSON
            )
        "#)
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    /// Create database indexes for performance
    async fn create_indexes(&self) -> DatabaseResult<()> {
        // Source texts indexes
        sqlx::query("CREATE INDEX IF NOT EXISTS idx_source_texts_title ON source_texts (title)")
            .execute(&self.pool).await?;
        
        sqlx::query("CREATE INDEX IF NOT EXISTS idx_source_texts_author ON source_texts (author)")
            .execute(&self.pool).await?;
        
        sqlx::query("CREATE INDEX IF NOT EXISTS idx_source_texts_language ON source_texts (language)")
            .execute(&self.pool).await?;
        
        sqlx::query("CREATE INDEX IF NOT EXISTS idx_source_texts_created_at ON source_texts (created_at)")
            .execute(&self.pool).await?;

        // Datasets indexes
        sqlx::query("CREATE INDEX IF NOT EXISTS idx_datasets_name ON datasets (name)")
            .execute(&self.pool).await?;
        
        sqlx::query("CREATE INDEX IF NOT EXISTS idx_datasets_source_text_id ON datasets (source_text_id)")
            .execute(&self.pool).await?;
        
        sqlx::query("CREATE INDEX IF NOT EXISTS idx_datasets_created_at ON datasets (created_at)")
            .execute(&self.pool).await?;

        // Text chunks indexes
        sqlx::query("CREATE INDEX IF NOT EXISTS idx_text_chunks_dataset_id ON text_chunks (dataset_id)")
            .execute(&self.pool).await?;
        
        sqlx::query("CREATE INDEX IF NOT EXISTS idx_text_chunks_quality_score ON text_chunks (quality_score)")
            .execute(&self.pool).await?;

        // Full-text search indexes
        sqlx::query(r#"
            CREATE VIRTUAL TABLE IF NOT EXISTS source_texts_fts USING fts5(
                id UNINDEXED,
                title,
                author,
                content='source_texts',
                content_rowid='rowid'
            )
        "#)
        .execute(&self.pool).await?;

        sqlx::query(r#"
            CREATE VIRTUAL TABLE IF NOT EXISTS text_chunks_fts USING fts5(
                id UNINDEXED,
                content,
                content='text_chunks',
                content_rowid='rowid'
            )
        "#)
        .execute(&self.pool).await?;

        // Processing jobs indexes
        sqlx::query("CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs (status)")
            .execute(&self.pool).await?;
        
        sqlx::query("CREATE INDEX IF NOT EXISTS idx_processing_jobs_created_at ON processing_jobs (created_at)")
            .execute(&self.pool).await?;

        debug!("Database indexes created successfully");
        Ok(())
    }

    /// Get the database connection pool
    pub fn pool(&self) -> &Pool<Sqlite> {
        &self.pool
    }

    /// Get the database file path
    pub fn db_path(&self) -> &str {
        &self.db_path
    }

    /// Check database health and integrity
    pub async fn health_check(&self) -> DatabaseResult<bool> {
        // Test basic connectivity
        sqlx::query("SELECT 1")
            .execute(&self.pool)
            .await?;

        // Check integrity
        let integrity_check = sqlx::query_scalar::<_, String>("PRAGMA integrity_check")
            .fetch_one(&self.pool)
            .await?;

        if integrity_check != "ok" {
            error!("Database integrity check failed: {}", integrity_check);
            return Err(DatabaseError::DataIntegrity(integrity_check));
        }

        debug!("Database health check passed");
        Ok(true)
    }

    /// Get database statistics
    pub async fn get_statistics(&self) -> DatabaseResult<DatabaseStatistics> {
        let source_texts_count = sqlx::query_scalar::<_, i64>(
            "SELECT COUNT(*) FROM source_texts"
        ).fetch_one(&self.pool).await?;

        let datasets_count = sqlx::query_scalar::<_, i64>(
            "SELECT COUNT(*) FROM datasets"
        ).fetch_one(&self.pool).await?;

        let text_chunks_count = sqlx::query_scalar::<_, i64>(
            "SELECT COUNT(*) FROM text_chunks"
        ).fetch_one(&self.pool).await?;

        let processing_jobs_count = sqlx::query_scalar::<_, i64>(
            "SELECT COUNT(*) FROM processing_jobs"
        ).fetch_one(&self.pool).await?;

        let db_size = sqlx::query_scalar::<_, i64>(
            "SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()"
        ).fetch_one(&self.pool).await?;

        Ok(DatabaseStatistics {
            source_texts_count: source_texts_count as u64,
            datasets_count: datasets_count as u64,
            text_chunks_count: text_chunks_count as u64,
            processing_jobs_count: processing_jobs_count as u64,
            database_size_bytes: db_size as u64,
        })
    }

    /// Close the database connection
    pub async fn close(&self) {
        self.pool.close().await;
        info!("Database connection closed");
    }
}

/// Database statistics
#[derive(Debug, Clone, Serialize)]
pub struct DatabaseStatistics {
    pub source_texts_count: u64,
    pub datasets_count: u64,
    pub text_chunks_count: u64,
    pub processing_jobs_count: u64,
    pub database_size_bytes: u64,
}
