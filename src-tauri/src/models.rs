use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use std::collections::HashMap;
use uuid::Uuid;

/// Core entity representing a source text (book, document, etc.)
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SourceText {
    pub id: Uuid,
    pub title: String,
    pub author: Option<String>,
    pub language: String,
    pub source_type: SourceType,
    pub file_path: Option<String>,
    pub url: Option<String>,
    pub metadata: TextMetadata,
    pub processing_status: ProcessingStatus,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// Type of source text
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SourceType {
    Book,
    Article,
    Website,
    PDF,
    PlainText,
    Epub,
    Docx,
    Other(String),
}

/// Comprehensive metadata for source texts
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TextMetadata {
    pub word_count: Option<u32>,
    pub character_count: Option<u32>,
    pub page_count: Option<u32>,
    pub isbn: Option<String>,
    pub publisher: Option<String>,
    pub publication_date: Option<DateTime<Utc>>,
    pub genre: Option<String>,
    pub tags: Vec<String>,
    pub description: Option<String>,
    pub encoding: Option<String>,
    pub file_size_bytes: Option<u64>,
    pub checksum: Option<String>,
    pub custom_fields: HashMap<String, String>,
}

/// Processing status of a source text
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ProcessingStatus {
    Pending,
    InProgress { 
        current_step: ProcessingStep,
        progress_percent: u8,
        started_at: DateTime<Utc>,
    },
    Completed {
        completed_at: DateTime<Utc>,
        processing_time_ms: u64,
    },
    Failed {
        error_message: String,
        failed_at: DateTime<Utc>,
        retry_count: u8,
    },
    Cancelled {
        cancelled_at: DateTime<Utc>,
    },
}

/// Individual processing steps
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ProcessingStep {
    Parsing,
    TextExtraction,
    Cleaning,
    Segmentation,
    Chunking,
    Validation,
    Export,
}

/// Processed dataset ready for RAG
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Dataset {
    pub id: Uuid,
    pub name: String,
    pub description: Option<String>,
    pub source_text_id: Uuid,
    pub dataset_type: DatasetType,
    pub format: DatasetFormat,
    pub chunking_strategy: ChunkingStrategy,
    pub chunks: Vec<TextChunk>,
    pub quality_metrics: QualityMetrics,
    pub export_configs: Vec<ExportConfig>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// Type of dataset for different use cases
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum DatasetType {
    Standard,        // General purpose RAG
    Conversational,  // Chat/dialogue focused
    QnA,            // Question-answer pairs
    Summarization,  // Summary generation
    FineTuning,     // Model fine-tuning
    Embedding,      // Vector embeddings
    Custom(String), // User-defined type
}

/// Output format for datasets
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum DatasetFormat {
    JSONL,
    JSON,
    CSV,
    Parquet,
    HuggingFace,
    OpenAI,
    Custom(String),
}

/// Individual text chunk within a dataset
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TextChunk {
    pub id: Uuid,
    pub content: String,
    pub metadata: ChunkMetadata,
    pub position: ChunkPosition,
    pub quality_score: Option<f32>,
    pub created_at: DateTime<Utc>,
}

/// Metadata for individual chunks
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ChunkMetadata {
    pub word_count: u32,
    pub character_count: u32,
    pub language: Option<String>,
    pub semantic_type: Option<SemanticType>,
    pub importance_score: Option<f32>,
    pub tags: Vec<String>,
    pub custom_fields: HashMap<String, String>,
}

/// Position information for chunks within source
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ChunkPosition {
    pub chapter: Option<String>,
    pub section: Option<String>,
    pub page_number: Option<u32>,
    pub paragraph_index: Option<u32>,
    pub start_offset: u32,
    pub end_offset: u32,
}

/// Semantic classification of content
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SemanticType {
    Narrative,
    Dialogue,
    Description,
    Instruction,
    Question,
    Answer,
    Definition,
    Example,
    Summary,
    Introduction,
    Conclusion,
    Other(String),
}

/// Chunking strategy configuration
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ChunkingStrategy {
    pub strategy_type: ChunkingType,
    pub target_size: u32,
    pub overlap_size: u32,
    pub respect_boundaries: bool,
    pub min_chunk_size: u32,
    pub max_chunk_size: u32,
    pub separator_patterns: Vec<String>,
}

/// Types of chunking strategies
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ChunkingType {
    FixedSize,      // Fixed character/word count
    Semantic,       // Based on meaning/topics
    Structural,     // Based on document structure
    Paragraph,      // Paragraph boundaries
    Sentence,       // Sentence boundaries
    Hybrid,         // Combination approach
}

/// Quality metrics for datasets
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct QualityMetrics {
    pub completeness_score: f32,     // 0.0 - 1.0
    pub consistency_score: f32,      // 0.0 - 1.0
    pub readability_score: f32,      // 0.0 - 1.0
    pub semantic_coherence: f32,     // 0.0 - 1.0
    pub chunk_size_distribution: SizeDistribution,
    pub language_distribution: HashMap<String, f32>,
    pub duplicate_ratio: f32,
    pub error_count: u32,
    pub warning_count: u32,
}

/// Statistical distribution of chunk sizes
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SizeDistribution {
    pub mean: f32,
    pub median: f32,
    pub std_dev: f32,
    pub min: u32,
    pub max: u32,
    pub percentiles: HashMap<u8, u32>, // e.g., 25th, 50th, 75th, 95th
}

/// Export configuration for different platforms
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ExportConfig {
    pub id: Uuid,
    pub name: String,
    pub platform: TargetPlatform,
    pub format: DatasetFormat,
    pub compression: Option<CompressionType>,
    pub filters: Vec<DataFilter>,
    pub transformations: Vec<DataTransformation>,
    pub output_path: String,
    pub is_active: bool,
    pub created_at: DateTime<Utc>,
}

/// Target platforms for export
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TargetPlatform {
    OpenAI,
    HuggingFace,
    Anthropic,
    Cohere,
    Local,
    S3,
    GCS,
    Azure,
    Custom(String),
}

/// Compression options
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum CompressionType {
    Gzip,
    Bzip2,
    Xz,
    Zstd,
}

/// Data filtering options
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct DataFilter {
    pub field: String,
    pub operator: FilterOperator,
    pub value: FilterValue,
}

/// Filter operators
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum FilterOperator {
    Equals,
    NotEquals,
    Contains,
    NotContains,
    GreaterThan,
    LessThan,
    GreaterThanOrEqual,
    LessThanOrEqual,
    In,
    NotIn,
    Regex,
}

/// Filter values (union type)
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum FilterValue {
    String(String),
    Number(f64),
    Boolean(bool),
    Array(Vec<String>),
}

/// Data transformation operations
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct DataTransformation {
    pub transformation_type: TransformationType,
    pub parameters: HashMap<String, String>,
}

/// Types of data transformations
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TransformationType {
    RemoveHtml,
    NormalizeWhitespace,
    RemoveEmptyLines,
    TrimWhitespace,
    ReplacePattern,
    AddPrefix,
    AddSuffix,
    Lowercase,
    Uppercase,
    RemoveStopWords,
    Custom(String),
}

/// Processing job for async operations
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ProcessingJob {
    pub id: Uuid,
    pub job_type: JobType,
    pub source_text_id: Option<Uuid>,
    pub dataset_id: Option<Uuid>,
    pub status: JobStatus,
    pub progress: JobProgress,
    pub parameters: HashMap<String, String>,
    pub created_at: DateTime<Utc>,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub error_message: Option<String>,
}

/// Types of processing jobs
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum JobType {
    TextParsing,
    DatasetGeneration,
    QualityAnalysis,
    Export,
    Import,
    Validation,
}

/// Job execution status
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum JobStatus {
    Queued,
    Running,
    Completed,
    Failed,
    Cancelled,
    Paused,
}

/// Detailed job progress
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct JobProgress {
    pub current_step: String,
    pub steps_completed: u32,
    pub total_steps: u32,
    pub progress_percent: u8,
    pub estimated_remaining_ms: Option<u64>,
    pub throughput_items_per_second: Option<f32>,
}

/// Application settings
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct AppSettings {
    pub general: GeneralSettings,
    pub processing: ProcessingSettings,
    pub export: ExportSettings,
    pub ui: UISettings,
}

/// General application settings
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct GeneralSettings {
    pub auto_save_interval_seconds: u32,
    pub max_concurrent_jobs: u8,
    pub default_language: String,
    pub data_directory: String,
    pub temp_directory: String,
    pub log_level: String,
    pub check_updates: bool,
    pub analytics_enabled: bool,
}

/// Processing-specific settings
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ProcessingSettings {
    pub default_chunking_strategy: ChunkingStrategy,
    pub quality_threshold: f32,
    pub auto_retry_failed_jobs: bool,
    pub max_retry_attempts: u8,
    pub parallel_processing: bool,
    pub memory_limit_mb: u32,
    pub timeout_seconds: u32,
}

/// Export-specific settings
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ExportSettings {
    pub default_format: DatasetFormat,
    pub default_compression: Option<CompressionType>,
    pub include_metadata: bool,
    pub validate_before_export: bool,
    pub backup_before_overwrite: bool,
}

/// UI/UX settings
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct UISettings {
    pub theme: String,
    pub font_size: u8,
    pub show_advanced_options: bool,
    pub auto_refresh_interval_seconds: u32,
    pub notifications_enabled: bool,
    pub sound_enabled: bool,
}

impl Default for ChunkingStrategy {
    fn default() -> Self {
        Self {
            strategy_type: ChunkingType::Paragraph,
            target_size: 1000,
            overlap_size: 100,
            respect_boundaries: true,
            min_chunk_size: 100,
            max_chunk_size: 2000,
            separator_patterns: vec![
                "\n\n".to_string(),
                ". ".to_string(),
                "! ".to_string(),
                "? ".to_string(),
            ],
        }
    }
}

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            general: GeneralSettings {
                auto_save_interval_seconds: 300,
                max_concurrent_jobs: 4,
                default_language: "en".to_string(),
                data_directory: "~/Lexicon/data".to_string(),
                temp_directory: "~/Lexicon/temp".to_string(),
                log_level: "info".to_string(),
                check_updates: true,
                analytics_enabled: false,
            },
            processing: ProcessingSettings {
                default_chunking_strategy: ChunkingStrategy::default(),
                quality_threshold: 0.7,
                auto_retry_failed_jobs: true,
                max_retry_attempts: 3,
                parallel_processing: true,
                memory_limit_mb: 2048,
                timeout_seconds: 3600,
            },
            export: ExportSettings {
                default_format: DatasetFormat::JSONL,
                default_compression: Some(CompressionType::Gzip),
                include_metadata: true,
                validate_before_export: true,
                backup_before_overwrite: true,
            },
            ui: UISettings {
                theme: "system".to_string(),
                font_size: 14,
                show_advanced_options: false,
                auto_refresh_interval_seconds: 30,
                notifications_enabled: true,
                sound_enabled: false,
            },
        }
    }
}
