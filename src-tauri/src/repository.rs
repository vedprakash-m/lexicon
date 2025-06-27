use sqlx::{Pool, Sqlite, Row};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use serde_json;
use log::{debug, error};

use crate::database::{Database, DatabaseError, DatabaseResult};
use crate::models::{
    SourceText, Dataset, TextChunk, ProcessingJob, 
    ExportConfig, AppSettings, JobStatus, ProcessingStatus
};

/// Repository for SourceText operations
pub struct SourceTextRepository<'a> {
    pool: &'a Pool<Sqlite>,
}

impl<'a> SourceTextRepository<'a> {
    pub fn new(pool: &'a Pool<Sqlite>) -> Self {
        Self { pool }
    }

    /// Create a new source text
    pub async fn create(&self, source_text: &SourceText) -> DatabaseResult<()> {
        let metadata_json = serde_json::to_string(&source_text.metadata)?;
        let processing_status_json = serde_json::to_string(&source_text.processing_status)?;

        sqlx::query(r#"
            INSERT INTO source_texts 
            (id, title, author, language, source_type, file_path, url, metadata, processing_status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        "#)
        .bind(source_text.id.to_string())
        .bind(&source_text.title)
        .bind(&source_text.author)
        .bind(&source_text.language)
        .bind(serde_json::to_string(&source_text.source_type)?)
        .bind(&source_text.file_path)
        .bind(&source_text.url)
        .bind(metadata_json)
        .bind(processing_status_json)
        .bind(source_text.created_at.to_rfc3339())
        .bind(source_text.updated_at.to_rfc3339())
        .execute(self.pool)
        .await?;

        // Update FTS index
        sqlx::query(r#"
            INSERT INTO source_texts_fts (id, title, author)
            VALUES (?, ?, ?)
        "#)
        .bind(source_text.id.to_string())
        .bind(&source_text.title)
        .bind(&source_text.author)
        .execute(self.pool)
        .await?;

        debug!("Created source text: {}", source_text.id);
        Ok(())
    }

    /// Get source text by ID
    pub async fn get_by_id(&self, id: Uuid) -> DatabaseResult<SourceText> {
        let row = sqlx::query(r#"
            SELECT id, title, author, language, source_type, file_path, url, 
                   metadata, processing_status, created_at, updated_at
            FROM source_texts WHERE id = ?
        "#)
        .bind(id.to_string())
        .fetch_optional(self.pool)
        .await?;

        match row {
            Some(row) => self.row_to_source_text(row),
            None => Err(DatabaseError::NotFound {
                entity_type: "SourceText".to_string(),
                id: id.to_string(),
            }),
        }
    }

    /// Get all source texts with optional filtering
    pub async fn get_all(&self, limit: Option<u32>, offset: Option<u32>) -> DatabaseResult<Vec<SourceText>> {
        let limit = limit.unwrap_or(100);
        let offset = offset.unwrap_or(0);

        let rows = sqlx::query(r#"
            SELECT id, title, author, language, source_type, file_path, url, 
                   metadata, processing_status, created_at, updated_at
            FROM source_texts 
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        "#)
        .bind(limit)
        .bind(offset)
        .fetch_all(self.pool)
        .await?;

        let mut source_texts = Vec::new();
        for row in rows {
            source_texts.push(self.row_to_source_text(row)?);
        }

        Ok(source_texts)
    }

    /// Update source text
    pub async fn update(&self, source_text: &SourceText) -> DatabaseResult<()> {
        let metadata_json = serde_json::to_string(&source_text.metadata)?;
        let processing_status_json = serde_json::to_string(&source_text.processing_status)?;

        let result = sqlx::query(r#"
            UPDATE source_texts 
            SET title = ?, author = ?, language = ?, source_type = ?, 
                file_path = ?, url = ?, metadata = ?, processing_status = ?, updated_at = ?
            WHERE id = ?
        "#)
        .bind(&source_text.title)
        .bind(&source_text.author)
        .bind(&source_text.language)
        .bind(serde_json::to_string(&source_text.source_type)?)
        .bind(&source_text.file_path)
        .bind(&source_text.url)
        .bind(metadata_json)
        .bind(processing_status_json)
        .bind(source_text.updated_at.to_rfc3339())
        .bind(source_text.id.to_string())
        .execute(self.pool)
        .await?;

        if result.rows_affected() == 0 {
            return Err(DatabaseError::NotFound {
                entity_type: "SourceText".to_string(),
                id: source_text.id.to_string(),
            });
        }

        // Update FTS index
        sqlx::query(r#"
            UPDATE source_texts_fts 
            SET title = ?, author = ?
            WHERE id = ?
        "#)
        .bind(&source_text.title)
        .bind(&source_text.author)
        .bind(source_text.id.to_string())
        .execute(self.pool)
        .await?;

        debug!("Updated source text: {}", source_text.id);
        Ok(())
    }

    /// Delete source text
    pub async fn delete(&self, id: Uuid) -> DatabaseResult<()> {
        let result = sqlx::query("DELETE FROM source_texts WHERE id = ?")
            .bind(id.to_string())
            .execute(self.pool)
            .await?;

        if result.rows_affected() == 0 {
            return Err(DatabaseError::NotFound {
                entity_type: "SourceText".to_string(),
                id: id.to_string(),
            });
        }

        // Remove from FTS index
        sqlx::query("DELETE FROM source_texts_fts WHERE id = ?")
            .bind(id.to_string())
            .execute(self.pool)
            .await?;

        debug!("Deleted source text: {}", id);
        Ok(())
    }

    /// Search source texts using full-text search
    pub async fn search(&self, query: &str, limit: Option<u32>) -> DatabaseResult<Vec<SourceText>> {
        let limit = limit.unwrap_or(50);

        let rows = sqlx::query(r#"
            SELECT st.id, st.title, st.author, st.language, st.source_type, st.file_path, st.url, 
                   st.metadata, st.processing_status, st.created_at, st.updated_at
            FROM source_texts st
            JOIN source_texts_fts fts ON st.id = fts.id
            WHERE source_texts_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        "#)
        .bind(query)
        .bind(limit)
        .fetch_all(self.pool)
        .await?;

        let mut source_texts = Vec::new();
        for row in rows {
            source_texts.push(self.row_to_source_text(row)?);
        }

        Ok(source_texts)
    }

    /// Get source texts by processing status
    pub async fn get_by_status(&self, status: ProcessingStatus) -> DatabaseResult<Vec<SourceText>> {
        let status_pattern = match status {
            ProcessingStatus::Pending => "%\"Pending\"%",
            ProcessingStatus::InProgress { .. } => "%\"InProgress\"%",
            ProcessingStatus::Completed { .. } => "%\"Completed\"%",
            ProcessingStatus::Failed { .. } => "%\"Failed\"%",
            ProcessingStatus::Cancelled { .. } => "%\"Cancelled\"%",
        };

        let rows = sqlx::query(r#"
            SELECT id, title, author, language, source_type, file_path, url, 
                   metadata, processing_status, created_at, updated_at
            FROM source_texts 
            WHERE processing_status LIKE ?
            ORDER BY created_at DESC
        "#)
        .bind(status_pattern)
        .fetch_all(self.pool)
        .await?;

        let mut source_texts = Vec::new();
        for row in rows {
            source_texts.push(self.row_to_source_text(row)?);
        }

        Ok(source_texts)
    }

    /// Convert database row to SourceText
    fn row_to_source_text(&self, row: sqlx::sqlite::SqliteRow) -> DatabaseResult<SourceText> {
        Ok(SourceText {
            id: Uuid::parse_str(&row.get::<String, _>("id"))
                .map_err(|e| DatabaseError::DataIntegrity(e.to_string()))?,
            title: row.get("title"),
            author: row.get("author"),
            language: row.get("language"),
            source_type: serde_json::from_str(&row.get::<String, _>("source_type"))?,
            file_path: row.get("file_path"),
            url: row.get("url"),
            metadata: serde_json::from_str(&row.get::<String, _>("metadata"))?,
            processing_status: serde_json::from_str(&row.get::<String, _>("processing_status"))?,
            created_at: DateTime::parse_from_rfc3339(&row.get::<String, _>("created_at"))
                .map_err(|e| DatabaseError::DataIntegrity(e.to_string()))?
                .with_timezone(&Utc),
            updated_at: DateTime::parse_from_rfc3339(&row.get::<String, _>("updated_at"))
                .map_err(|e| DatabaseError::DataIntegrity(e.to_string()))?
                .with_timezone(&Utc),
        })
    }
}

/// Repository for Dataset operations
pub struct DatasetRepository<'a> {
    pool: &'a Pool<Sqlite>,
}

impl<'a> DatasetRepository<'a> {
    pub fn new(pool: &'a Pool<Sqlite>) -> Self {
        Self { pool }
    }

    /// Create a new dataset
    pub async fn create(&self, dataset: &Dataset) -> DatabaseResult<()> {
        let chunking_strategy_json = serde_json::to_string(&dataset.chunking_strategy)?;
        let quality_metrics_json = serde_json::to_string(&dataset.quality_metrics)?;

        sqlx::query(r#"
            INSERT INTO datasets 
            (id, name, description, source_text_id, dataset_type, format, 
             chunking_strategy, quality_metrics, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        "#)
        .bind(dataset.id.to_string())
        .bind(&dataset.name)
        .bind(&dataset.description)
        .bind(dataset.source_text_id.to_string())
        .bind(serde_json::to_string(&dataset.dataset_type)?)
        .bind(serde_json::to_string(&dataset.format)?)
        .bind(chunking_strategy_json)
        .bind(quality_metrics_json)
        .bind(dataset.created_at.to_rfc3339())
        .bind(dataset.updated_at.to_rfc3339())
        .execute(self.pool)
        .await?;

        debug!("Created dataset: {}", dataset.id);
        Ok(())
    }

    /// Get dataset by ID
    pub async fn get_by_id(&self, id: Uuid) -> DatabaseResult<Dataset> {
        let row = sqlx::query(r#"
            SELECT id, name, description, source_text_id, dataset_type, format,
                   chunking_strategy, quality_metrics, created_at, updated_at
            FROM datasets WHERE id = ?
        "#)
        .bind(id.to_string())
        .fetch_optional(self.pool)
        .await?;

        match row {
            Some(row) => {
                let mut dataset = self.row_to_dataset(row)?;
                // Load chunks
                dataset.chunks = self.get_chunks_for_dataset(id).await?;
                // Load export configs
                dataset.export_configs = self.get_export_configs_for_dataset(id).await?;
                Ok(dataset)
            }
            None => Err(DatabaseError::NotFound {
                entity_type: "Dataset".to_string(),
                id: id.to_string(),
            }),
        }
    }

    /// Get all datasets for a source text
    pub async fn get_by_source_text(&self, source_text_id: Uuid) -> DatabaseResult<Vec<Dataset>> {
        let rows = sqlx::query(r#"
            SELECT id, name, description, source_text_id, dataset_type, format,
                   chunking_strategy, quality_metrics, created_at, updated_at
            FROM datasets 
            WHERE source_text_id = ?
            ORDER BY created_at DESC
        "#)
        .bind(source_text_id.to_string())
        .fetch_all(self.pool)
        .await?;

        let mut datasets = Vec::new();
        for row in rows {
            let mut dataset = self.row_to_dataset(row)?;
            // Load chunks and export configs for each dataset
            dataset.chunks = self.get_chunks_for_dataset(dataset.id).await?;
            dataset.export_configs = self.get_export_configs_for_dataset(dataset.id).await?;
            datasets.push(dataset);
        }

        Ok(datasets)
    }

    /// Update dataset
    pub async fn update(&self, dataset: &Dataset) -> DatabaseResult<()> {
        let chunking_strategy_json = serde_json::to_string(&dataset.chunking_strategy)?;
        let quality_metrics_json = serde_json::to_string(&dataset.quality_metrics)?;

        let result = sqlx::query(r#"
            UPDATE datasets 
            SET name = ?, description = ?, dataset_type = ?, format = ?, 
                chunking_strategy = ?, quality_metrics = ?, updated_at = ?
            WHERE id = ?
        "#)
        .bind(&dataset.name)
        .bind(&dataset.description)
        .bind(serde_json::to_string(&dataset.dataset_type)?)
        .bind(serde_json::to_string(&dataset.format)?)
        .bind(chunking_strategy_json)
        .bind(quality_metrics_json)
        .bind(dataset.updated_at.to_rfc3339())
        .bind(dataset.id.to_string())
        .execute(self.pool)
        .await?;

        if result.rows_affected() == 0 {
            return Err(DatabaseError::NotFound {
                entity_type: "Dataset".to_string(),
                id: dataset.id.to_string(),
            });
        }

        debug!("Updated dataset: {}", dataset.id);
        Ok(())
    }

    /// Delete dataset
    pub async fn delete(&self, id: Uuid) -> DatabaseResult<()> {
        let result = sqlx::query("DELETE FROM datasets WHERE id = ?")
            .bind(id.to_string())
            .execute(self.pool)
            .await?;

        if result.rows_affected() == 0 {
            return Err(DatabaseError::NotFound {
                entity_type: "Dataset".to_string(),
                id: id.to_string(),
            });
        }

        debug!("Deleted dataset: {}", id);
        Ok(())
    }

    /// Get chunks for a dataset
    async fn get_chunks_for_dataset(&self, dataset_id: Uuid) -> DatabaseResult<Vec<TextChunk>> {
        let chunk_repo = TextChunkRepository::new(self.pool);
        chunk_repo.get_by_dataset(dataset_id).await
    }

    /// Get export configs for a dataset
    async fn get_export_configs_for_dataset(&self, dataset_id: Uuid) -> DatabaseResult<Vec<ExportConfig>> {
        let export_repo = ExportConfigRepository::new(self.pool);
        export_repo.get_by_dataset(dataset_id).await
    }

    /// Convert database row to Dataset
    fn row_to_dataset(&self, row: sqlx::sqlite::SqliteRow) -> DatabaseResult<Dataset> {
        Ok(Dataset {
            id: Uuid::parse_str(&row.get::<String, _>("id"))
                .map_err(|e| DatabaseError::DataIntegrity(e.to_string()))?,
            name: row.get("name"),
            description: row.get("description"),
            source_text_id: Uuid::parse_str(&row.get::<String, _>("source_text_id"))
                .map_err(|e| DatabaseError::DataIntegrity(e.to_string()))?,
            dataset_type: serde_json::from_str(&row.get::<String, _>("dataset_type"))?,
            format: serde_json::from_str(&row.get::<String, _>("format"))?,
            chunking_strategy: serde_json::from_str(&row.get::<String, _>("chunking_strategy"))?,
            chunks: Vec::new(), // Will be loaded separately
            quality_metrics: serde_json::from_str(&row.get::<String, _>("quality_metrics"))?,
            export_configs: Vec::new(), // Will be loaded separately
            created_at: DateTime::parse_from_rfc3339(&row.get::<String, _>("created_at"))
                .map_err(|e| DatabaseError::DataIntegrity(e.to_string()))?
                .with_timezone(&Utc),
            updated_at: DateTime::parse_from_rfc3339(&row.get::<String, _>("updated_at"))
                .map_err(|e| DatabaseError::DataIntegrity(e.to_string()))?
                .with_timezone(&Utc),
        })
    }
}

/// Repository for TextChunk operations
pub struct TextChunkRepository<'a> {
    pool: &'a Pool<Sqlite>,
}

impl<'a> TextChunkRepository<'a> {
    pub fn new(pool: &'a Pool<Sqlite>) -> Self {
        Self { pool }
    }

    /// Create text chunks in batch
    pub async fn create_batch(&self, chunks: &[TextChunk], dataset_id: Uuid) -> DatabaseResult<()> {
        let mut tx = self.pool.begin().await?;

        for chunk in chunks {
            let metadata_json = serde_json::to_string(&chunk.metadata)?;
            let position_json = serde_json::to_string(&chunk.position)?;

            sqlx::query(r#"
                INSERT INTO text_chunks 
                (id, dataset_id, content, metadata, position, quality_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            "#)
            .bind(chunk.id.to_string())
            .bind(dataset_id.to_string())
            .bind(&chunk.content)
            .bind(metadata_json)
            .bind(position_json)
            .bind(chunk.quality_score)
            .bind(chunk.created_at.to_rfc3339())
            .execute(&mut *tx)
            .await?;

            // Add to FTS index
            sqlx::query(r#"
                INSERT INTO text_chunks_fts (id, content)
                VALUES (?, ?)
            "#)
            .bind(chunk.id.to_string())
            .bind(&chunk.content)
            .execute(&mut *tx)
            .await?;
        }

        tx.commit().await?;
        debug!("Created {} text chunks for dataset {}", chunks.len(), dataset_id);
        Ok(())
    }

    /// Get chunks for a dataset
    pub async fn get_by_dataset(&self, dataset_id: Uuid) -> DatabaseResult<Vec<TextChunk>> {
        let rows = sqlx::query(r#"
            SELECT id, content, metadata, position, quality_score, created_at
            FROM text_chunks 
            WHERE dataset_id = ?
            ORDER BY created_at ASC
        "#)
        .bind(dataset_id.to_string())
        .fetch_all(self.pool)
        .await?;

        let mut chunks = Vec::new();
        for row in rows {
            chunks.push(self.row_to_text_chunk(row)?);
        }

        Ok(chunks)
    }

    /// Search text chunks using full-text search
    pub async fn search(&self, query: &str, dataset_id: Option<Uuid>, limit: Option<u32>) -> DatabaseResult<Vec<TextChunk>> {
        let limit = limit.unwrap_or(50);

        let (sql, bind_params) = if let Some(dataset_id) = dataset_id {
            (
                r#"
                SELECT tc.id, tc.content, tc.metadata, tc.position, tc.quality_score, tc.created_at
                FROM text_chunks tc
                JOIN text_chunks_fts fts ON tc.id = fts.id
                WHERE text_chunks_fts MATCH ? AND tc.dataset_id = ?
                ORDER BY rank
                LIMIT ?
                "#,
                vec![query.to_string(), dataset_id.to_string(), limit.to_string()],
            )
        } else {
            (
                r#"
                SELECT tc.id, tc.content, tc.metadata, tc.position, tc.quality_score, tc.created_at
                FROM text_chunks tc
                JOIN text_chunks_fts fts ON tc.id = fts.id
                WHERE text_chunks_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                "#,
                vec![query.to_string(), limit.to_string()],
            )
        };

        let mut query_builder = sqlx::query(sql);
        for param in bind_params {
            query_builder = query_builder.bind(param);
        }

        let rows = query_builder.fetch_all(self.pool).await?;

        let mut chunks = Vec::new();
        for row in rows {
            chunks.push(self.row_to_text_chunk(row)?);
        }

        Ok(chunks)
    }

    /// Convert database row to TextChunk
    fn row_to_text_chunk(&self, row: sqlx::sqlite::SqliteRow) -> DatabaseResult<TextChunk> {
        Ok(TextChunk {
            id: Uuid::parse_str(&row.get::<String, _>("id"))
                .map_err(|e| DatabaseError::DataIntegrity(e.to_string()))?,
            content: row.get("content"),
            metadata: serde_json::from_str(&row.get::<String, _>("metadata"))?,
            position: serde_json::from_str(&row.get::<String, _>("position"))?,
            quality_score: row.get("quality_score"),
            created_at: DateTime::parse_from_rfc3339(&row.get::<String, _>("created_at"))
                .map_err(|e| DatabaseError::DataIntegrity(e.to_string()))?
                .with_timezone(&Utc),
        })
    }
}

// Additional repository implementations would continue here...
// For brevity, I'll include the key ones and indicate where others would go

/// Repository for ProcessingJob operations
pub struct ProcessingJobRepository<'a> {
    pool: &'a Pool<Sqlite>,
}

/// Repository for ExportConfig operations  
pub struct ExportConfigRepository<'a> {
    pool: &'a Pool<Sqlite>,
}

impl<'a> ExportConfigRepository<'a> {
    pub fn new(pool: &'a Pool<Sqlite>) -> Self {
        Self { pool }
    }

    /// Get export configs for a dataset
    pub async fn get_by_dataset(&self, dataset_id: Uuid) -> DatabaseResult<Vec<ExportConfig>> {
        // Implementation would be similar to other repositories
        // Returning empty vec for now to satisfy compiler
        Ok(Vec::new())
    }
}

/// Repository for AppSettings operations
pub struct AppSettingsRepository<'a> {
    pool: &'a Pool<Sqlite>,
}

impl<'a> AppSettingsRepository<'a> {
    pub fn new(pool: &'a Pool<Sqlite>) -> Self {
        Self { pool }
    }

    /// Get application settings (there should only be one)
    pub async fn get(&self) -> DatabaseResult<AppSettings> {
        let row = sqlx::query("SELECT settings FROM app_settings WHERE id = 1")
            .fetch_optional(self.pool)
            .await?;

        match row {
            Some(row) => {
                let settings_json: String = row.get("settings");
                Ok(serde_json::from_str(&settings_json)?)
            }
            None => {
                // Return default settings if none exist
                Ok(AppSettings::default())
            }
        }
    }

    /// Save application settings
    pub async fn save(&self, settings: &AppSettings) -> DatabaseResult<()> {
        let settings_json = serde_json::to_string(settings)?;

        sqlx::query(r#"
            INSERT OR REPLACE INTO app_settings (id, settings)
            VALUES (1, ?)
        "#)
        .bind(settings_json)
        .execute(self.pool)
        .await?;

        debug!("Saved application settings");
        Ok(())
    }
}
