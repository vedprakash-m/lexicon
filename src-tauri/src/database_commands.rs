use tauri::{State, command};
use uuid::Uuid;
use std::sync::Arc;
use tokio::sync::Mutex;
use serde::{Deserialize, Serialize};
use log::{info, error, debug, warn};

use crate::database::{Database, DatabaseConfig, DatabaseStatistics, DatabaseError};
use crate::repository::{
    SourceTextRepository, DatasetRepository, TextChunkRepository,
    ProcessingJobRepository, ExportConfigRepository, AppSettingsRepository
};
use crate::models::{
    SourceText, Dataset, TextChunk, ProcessingJob,
    ExportConfig, AppSettings, ProcessingStatus
};

/// Shared database state for Tauri
pub type DatabaseState = Arc<Mutex<Database>>;

/// Database initialization parameters
#[derive(Debug, Deserialize)]
pub struct InitDatabaseParams {
    pub db_path: Option<String>,
    pub max_connections: Option<u32>,
}

/// Search parameters
#[derive(Debug, Deserialize)]
pub struct SearchParams {
    pub query: String,
    pub limit: Option<u32>,
    pub dataset_id: Option<String>, // UUID as string
}

/// Pagination parameters
#[derive(Debug, Deserialize)]
pub struct PaginationParams {
    pub limit: Option<u32>,
    pub offset: Option<u32>,
}

/// Standard API response wrapper
#[derive(Debug, Serialize)]
pub struct ApiResponse<T> {
    pub success: bool,
    pub data: Option<T>,
    pub error: Option<String>,
}

impl<T> ApiResponse<T> {
    pub fn success(data: T) -> Self {
        Self {
            success: true,
            data: Some(data),
            error: None,
        }
    }

    pub fn error(error: String) -> Self {
        Self {
            success: false,
            data: None,
            error: Some(error),
        }
    }
}

/// Initialize the database
#[command]
pub async fn init_database(
    params: InitDatabaseParams,
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<bool>, String> {
    info!("Initializing database with params: {:?}", params);

    let config = DatabaseConfig {
        db_path: params.db_path.unwrap_or_else(|| {
            dirs::data_dir()
                .unwrap_or_else(|| std::path::PathBuf::from("."))
                .join("com.lexicon.dataset-tool")
                .join("lexicon.db")
                .to_string_lossy()
                .to_string()
        }),
        max_connections: params.max_connections.unwrap_or(10),
        ..Default::default()
    };

    match Database::new(config).await {
        Ok(db) => {
            let mut database_lock = database.lock().await;
            *database_lock = db;
            info!("Database initialized successfully");
            Ok(ApiResponse::success(true))
        }
        Err(e) => {
            error!("Failed to initialize database: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

/// Get database health status
#[command]
pub async fn database_health_check(
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<bool>, String> {
    let database_lock = database.lock().await;
    
    match database_lock.health_check().await {
        Ok(healthy) => {
            debug!("Database health check: {}", healthy);
            Ok(ApiResponse::success(healthy))
        }
        Err(e) => {
            error!("Database health check failed: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

/// Get database statistics
#[command]
pub async fn get_database_statistics(
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<DatabaseStatistics>, String> {
    let database_lock = database.lock().await;
    
    match database_lock.get_statistics().await {
        Ok(stats) => {
            debug!("Retrieved database statistics");
            Ok(ApiResponse::success(stats))
        }
        Err(e) => {
            error!("Failed to get database statistics: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

// ==================== Source Text Commands ====================

/// Create a new source text
#[command]
pub async fn create_source_text(
    source_text: SourceText,
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<bool>, String> {
    let database_lock = database.lock().await;
    let repo = SourceTextRepository::new(database_lock.pool());

    match repo.create(&source_text).await {
        Ok(_) => {
            info!("Created source text: {}", source_text.id);
            Ok(ApiResponse::success(true))
        }
        Err(e) => {
            error!("Failed to create source text: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

/// Get source text by ID
#[command]
pub async fn get_source_text_by_id(
    id: String,
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<SourceText>, String> {
    let uuid = match Uuid::parse_str(&id) {
        Ok(uuid) => uuid,
        Err(e) => return Ok(ApiResponse::error(format!("Invalid UUID: {}", e))),
    };

    let database_lock = database.lock().await;
    let repo = SourceTextRepository::new(database_lock.pool());

    match repo.get_by_id(uuid).await {
        Ok(source_text) => {
            debug!("Retrieved source text: {}", id);
            Ok(ApiResponse::success(source_text))
        }
        Err(e) => {
            error!("Failed to get source text: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

/// Get all source texts with pagination
#[command]
pub async fn db_get_all_source_texts(
    pagination: PaginationParams,
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<Vec<SourceText>>, String> {
    let database_lock = database.lock().await;
    let repo = SourceTextRepository::new(database_lock.pool());

    match repo.get_all(pagination.limit, pagination.offset).await {
        Ok(source_texts) => {
            debug!("Retrieved {} source texts", source_texts.len());
            Ok(ApiResponse::success(source_texts))
        }
        Err(e) => {
            error!("Failed to get source texts: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

/// Update source text
#[command]
pub async fn update_source_text(
    source_text: SourceText,
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<bool>, String> {
    let database_lock = database.lock().await;
    let repo = SourceTextRepository::new(database_lock.pool());

    match repo.update(&source_text).await {
        Ok(_) => {
            info!("Updated source text: {}", source_text.id);
            Ok(ApiResponse::success(true))
        }
        Err(e) => {
            error!("Failed to update source text: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

/// Delete source text
#[command]
pub async fn db_delete_source_text(
    id: String,
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<bool>, String> {
    let uuid = match Uuid::parse_str(&id) {
        Ok(uuid) => uuid,
        Err(e) => return Ok(ApiResponse::error(format!("Invalid UUID: {}", e))),
    };

    let database_lock = database.lock().await;
    let repo = SourceTextRepository::new(database_lock.pool());

    match repo.delete(uuid).await {
        Ok(_) => {
            info!("Deleted source text: {}", id);
            Ok(ApiResponse::success(true))
        }
        Err(e) => {
            error!("Failed to delete source text: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

/// Search source texts
#[command]
pub async fn search_source_texts(
    search_params: SearchParams,
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<Vec<SourceText>>, String> {
    let database_lock = database.lock().await;
    let repo = SourceTextRepository::new(database_lock.pool());

    match repo.search(&search_params.query, search_params.limit).await {
        Ok(source_texts) => {
            debug!("Found {} source texts for query: {}", source_texts.len(), search_params.query);
            Ok(ApiResponse::success(source_texts))
        }
        Err(e) => {
            error!("Failed to search source texts: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

/// Get source texts by processing status
#[command]
pub async fn get_source_texts_by_status(
    status: ProcessingStatus,
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<Vec<SourceText>>, String> {
    let database_lock = database.lock().await;
    let repo = SourceTextRepository::new(database_lock.pool());

    match repo.get_by_status(status).await {
        Ok(source_texts) => {
            debug!("Retrieved {} source texts with status", source_texts.len());
            Ok(ApiResponse::success(source_texts))
        }
        Err(e) => {
            error!("Failed to get source texts by status: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

// ==================== Dataset Commands ====================

/// Create a new dataset
#[command]
pub async fn create_dataset(
    dataset: Dataset,
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<bool>, String> {
    let database_lock = database.lock().await;
    let repo = DatasetRepository::new(database_lock.pool());

    match repo.create(&dataset).await {
        Ok(_) => {
            info!("Created dataset: {}", dataset.id);
            Ok(ApiResponse::success(true))
        }
        Err(e) => {
            error!("Failed to create dataset: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

/// Get dataset by ID
#[command]
pub async fn get_dataset_by_id(
    id: String,
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<Dataset>, String> {
    let uuid = match Uuid::parse_str(&id) {
        Ok(uuid) => uuid,
        Err(e) => return Ok(ApiResponse::error(format!("Invalid UUID: {}", e))),
    };

    let database_lock = database.lock().await;
    let repo = DatasetRepository::new(database_lock.pool());

    match repo.get_by_id(uuid).await {
        Ok(dataset) => {
            debug!("Retrieved dataset: {}", id);
            Ok(ApiResponse::success(dataset))
        }
        Err(e) => {
            error!("Failed to get dataset: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

/// Get datasets by source text
#[command]
pub async fn get_datasets_by_source_text(
    source_text_id: String,
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<Vec<Dataset>>, String> {
    let uuid = match Uuid::parse_str(&source_text_id) {
        Ok(uuid) => uuid,
        Err(e) => return Ok(ApiResponse::error(format!("Invalid UUID: {}", e))),
    };

    let database_lock = database.lock().await;
    let repo = DatasetRepository::new(database_lock.pool());

    match repo.get_by_source_text(uuid).await {
        Ok(datasets) => {
            debug!("Retrieved {} datasets for source text: {}", datasets.len(), source_text_id);
            Ok(ApiResponse::success(datasets))
        }
        Err(e) => {
            error!("Failed to get datasets by source text: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

/// Update dataset
#[command]
pub async fn update_dataset(
    dataset: Dataset,
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<bool>, String> {
    let database_lock = database.lock().await;
    let repo = DatasetRepository::new(database_lock.pool());

    match repo.update(&dataset).await {
        Ok(_) => {
            info!("Updated dataset: {}", dataset.id);
            Ok(ApiResponse::success(true))
        }
        Err(e) => {
            error!("Failed to update dataset: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

/// Delete dataset
#[command]
pub async fn db_delete_dataset(
    id: String,
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<bool>, String> {
    let uuid = match Uuid::parse_str(&id) {
        Ok(uuid) => uuid,
        Err(e) => return Ok(ApiResponse::error(format!("Invalid UUID: {}", e))),
    };

    let database_lock = database.lock().await;
    let repo = DatasetRepository::new(database_lock.pool());

    match repo.delete(uuid).await {
        Ok(_) => {
            info!("Deleted dataset: {}", id);
            Ok(ApiResponse::success(true))
        }
        Err(e) => {
            error!("Failed to delete dataset: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

// ==================== Text Chunk Commands ====================

/// Create text chunks in batch
#[command]
pub async fn create_text_chunks_batch(
    chunks: Vec<TextChunk>,
    dataset_id: String,
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<bool>, String> {
    let uuid = match Uuid::parse_str(&dataset_id) {
        Ok(uuid) => uuid,
        Err(e) => return Ok(ApiResponse::error(format!("Invalid UUID: {}", e))),
    };

    let database_lock = database.lock().await;
    let repo = TextChunkRepository::new(database_lock.pool());

    match repo.create_batch(&chunks, uuid).await {
        Ok(_) => {
            info!("Created {} text chunks for dataset: {}", chunks.len(), dataset_id);
            Ok(ApiResponse::success(true))
        }
        Err(e) => {
            error!("Failed to create text chunks: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

/// Search text chunks
#[command]
pub async fn search_text_chunks(
    search_params: SearchParams,
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<Vec<TextChunk>>, String> {
    let dataset_id = if let Some(id_str) = &search_params.dataset_id {
        match Uuid::parse_str(id_str) {
            Ok(uuid) => Some(uuid),
            Err(e) => return Ok(ApiResponse::error(format!("Invalid dataset UUID: {}", e))),
        }
    } else {
        None
    };

    let database_lock = database.lock().await;
    let repo = TextChunkRepository::new(database_lock.pool());

    match repo.search(&search_params.query, dataset_id, search_params.limit).await {
        Ok(chunks) => {
            debug!("Found {} text chunks for query: {}", chunks.len(), search_params.query);
            Ok(ApiResponse::success(chunks))
        }
        Err(e) => {
            error!("Failed to search text chunks: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

// ==================== App Settings Commands ====================

/// Get application settings
#[command]
pub async fn get_app_settings(
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<AppSettings>, String> {
    let database_lock = database.lock().await;
    let repo = AppSettingsRepository::new(database_lock.pool());

    match repo.get().await {
        Ok(settings) => {
            debug!("Retrieved application settings");
            Ok(ApiResponse::success(settings))
        }
        Err(e) => {
            error!("Failed to get application settings: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

/// Save application settings
#[command]
pub async fn save_app_settings(
    settings: AppSettings,
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<bool>, String> {
    let database_lock = database.lock().await;
    let repo = AppSettingsRepository::new(database_lock.pool());

    match repo.save(&settings).await {
        Ok(_) => {
            info!("Saved application settings");
            Ok(ApiResponse::success(true))
        }
        Err(e) => {
            error!("Failed to save application settings: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

// ==================== Backup and Recovery Commands ====================

/// Create database backup
#[command]
pub async fn create_database_backup(
    backup_path: String,
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<bool>, String> {
    let database_lock = database.lock().await;
    
    // Use file system to copy database file
    match tokio::fs::copy(database_lock.db_path(), &backup_path).await {
        Ok(_) => {
            info!("Created database backup at: {}", backup_path);
            Ok(ApiResponse::success(true))
        }
        Err(e) => {
            error!("Failed to create database backup: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}

/// Restore database from backup
#[command]
pub async fn restore_database_from_backup(
    backup_path: String,
    database: State<'_, DatabaseState>
) -> Result<ApiResponse<bool>, String> {
    let database_lock = database.lock().await;
    
    // Close current connection
    database_lock.close().await;
    
    // Copy backup over current database
    match tokio::fs::copy(&backup_path, database_lock.db_path()).await {
        Ok(_) => {
            info!("Restored database from backup: {}", backup_path);
            // Would need to reinitialize database here
            Ok(ApiResponse::success(true))
        }
        Err(e) => {
            error!("Failed to restore database from backup: {}", e);
            Ok(ApiResponse::error(e.to_string()))
        }
    }
}
