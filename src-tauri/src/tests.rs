use crate::models::*;
use crate::validation::Validate;
use uuid::Uuid;
use chrono::Utc;
use std::collections::HashMap;

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_source_text() -> SourceText {
        SourceText {
            id: Uuid::new_v4(),
            title: "Test Book".to_string(),
            author: Some("Test Author".to_string()),
            language: "en".to_string(),
            source_type: SourceType::Book,
            file_path: Some("/path/to/book.txt".to_string()),
            url: None,
            metadata: TextMetadata {
                word_count: Some(10000),
                character_count: Some(50000),
                page_count: Some(200),
                isbn: Some("978-0-123456-78-6".to_string()),
                publisher: Some("Test Publisher".to_string()),
                publication_date: Some(Utc::now()),
                genre: Some("Fiction".to_string()),
                tags: vec!["classic".to_string(), "literature".to_string()],
                description: Some("A test book for validation".to_string()),
                encoding: Some("UTF-8".to_string()),
                file_size_bytes: Some(1024000),
                checksum: Some("abc123def456".to_string()),
                custom_fields: HashMap::new(),
            },
            processing_status: ProcessingStatus::Pending,
            created_at: Utc::now(),
            updated_at: Utc::now(),
        }
    }

    fn create_test_dataset() -> Dataset {
        let chunks = vec![
            TextChunk {
                id: Uuid::new_v4(),
                content: "This is the first chunk of text content.".to_string(),
                metadata: ChunkMetadata {
                    word_count: 8,
                    character_count: 41,
                    language: Some("en".to_string()),
                    semantic_type: Some(SemanticType::Narrative),
                    importance_score: Some(0.8),
                    tags: vec!["introduction".to_string()],
                    custom_fields: HashMap::new(),
                },
                position: ChunkPosition {
                    chapter: Some("Chapter 1".to_string()),
                    section: Some("Introduction".to_string()),
                    page_number: Some(1),
                    paragraph_index: Some(0),
                    start_offset: 0,
                    end_offset: 41,
                },
                quality_score: Some(0.9),
                created_at: Utc::now(),
            }
        ];

        Dataset {
            id: Uuid::new_v4(),
            name: "Test Dataset".to_string(),
            description: Some("A test dataset for validation".to_string()),
            source_text_id: Uuid::new_v4(),
            dataset_type: DatasetType::Standard,
            format: DatasetFormat::JSONL,
            chunking_strategy: ChunkingStrategy::default(),
            chunks,
            quality_metrics: QualityMetrics {
                completeness_score: 0.95,
                consistency_score: 0.90,
                readability_score: 0.85,
                semantic_coherence: 0.80,
                chunk_size_distribution: SizeDistribution {
                    mean: 500.0,
                    median: 480.0,
                    std_dev: 150.0,
                    min: 100,
                    max: 1200,
                    percentiles: HashMap::from([
                        (25, 350),
                        (50, 480),
                        (75, 650),
                        (95, 1000),
                    ]),
                },
                language_distribution: HashMap::from([
                    ("en".to_string(), 1.0),
                ]),
                duplicate_ratio: 0.02,
                error_count: 0,
                warning_count: 1,
            },
            export_configs: vec![],
            created_at: Utc::now(),
            updated_at: Utc::now(),
        }
    }

    #[test]
    fn test_source_text_serialization() {
        let source_text = create_test_source_text();
        
        // Test serialization
        let json = serde_json::to_string(&source_text).expect("Failed to serialize SourceText");
        assert!(!json.is_empty());
        
        // Test deserialization
        let deserialized: SourceText = serde_json::from_str(&json).expect("Failed to deserialize SourceText");
        assert_eq!(source_text.id, deserialized.id);
        assert_eq!(source_text.title, deserialized.title);
        assert_eq!(source_text.language, deserialized.language);
    }

    #[test]
    fn test_dataset_serialization() {
        let dataset = create_test_dataset();
        
        // Test serialization
        let json = serde_json::to_string(&dataset).expect("Failed to serialize Dataset");
        assert!(!json.is_empty());
        
        // Test deserialization
        let deserialized: Dataset = serde_json::from_str(&json).expect("Failed to deserialize Dataset");
        assert_eq!(dataset.id, deserialized.id);
        assert_eq!(dataset.name, deserialized.name);
        assert_eq!(dataset.chunks.len(), deserialized.chunks.len());
    }

    #[test]
    fn test_source_text_validation() {
        let source_text = create_test_source_text();
        assert!(source_text.validate().is_ok());
        
        // Test invalid source text
        let mut invalid_source = source_text.clone();
        invalid_source.title = "".to_string(); // Empty title should fail validation
        assert!(invalid_source.validate().is_err());
    }

    #[test]
    fn test_dataset_validation() {
        let dataset = create_test_dataset();
        assert!(dataset.validate().is_ok());
        
        // Test invalid dataset
        let mut invalid_dataset = dataset.clone();
        invalid_dataset.name = "".to_string(); // Empty name should fail validation
        assert!(invalid_dataset.validate().is_err());
    }

    #[test]
    fn test_chunking_strategy_validation() {
        let strategy = ChunkingStrategy::default();
        assert!(strategy.validate().is_ok());
        
        // Test invalid strategy
        let mut invalid_strategy = strategy.clone();
        invalid_strategy.min_chunk_size = 1000;
        invalid_strategy.max_chunk_size = 500; // min > max should fail
        assert!(invalid_strategy.validate().is_err());
    }

    #[test]
    fn test_processing_status_variants() {
        // Test all ProcessingStatus variants
        let statuses = vec![
            ProcessingStatus::Pending,
            ProcessingStatus::InProgress {
                current_step: ProcessingStep::Parsing,
                progress_percent: 50,
                started_at: Utc::now(),
            },
            ProcessingStatus::Completed {
                completed_at: Utc::now(),
                processing_time_ms: 5000,
            },
            ProcessingStatus::Failed {
                error_message: "Test error".to_string(),
                failed_at: Utc::now(),
                retry_count: 1,
            },
            ProcessingStatus::Cancelled {
                cancelled_at: Utc::now(),
            },
        ];

        for status in statuses {
            let json = serde_json::to_string(&status).expect("Failed to serialize ProcessingStatus");
            let deserialized: ProcessingStatus = serde_json::from_str(&json).expect("Failed to deserialize ProcessingStatus");
            
            // Check that the variant type matches
            match (&status, &deserialized) {
                (ProcessingStatus::Pending, ProcessingStatus::Pending) => {},
                (ProcessingStatus::InProgress { .. }, ProcessingStatus::InProgress { .. }) => {},
                (ProcessingStatus::Completed { .. }, ProcessingStatus::Completed { .. }) => {},
                (ProcessingStatus::Failed { .. }, ProcessingStatus::Failed { .. }) => {},
                (ProcessingStatus::Cancelled { .. }, ProcessingStatus::Cancelled { .. }) => {},
                _ => panic!("ProcessingStatus variant mismatch"),
            }
        }
    }

    #[test]
    fn test_source_type_variants() {
        let types = vec![
            SourceType::Book,
            SourceType::Article,
            SourceType::Website,
            SourceType::PDF,
            SourceType::PlainText,
            SourceType::Epub,
            SourceType::Docx,
            SourceType::Other("CustomType".to_string()),
        ];

        for source_type in types {
            let json = serde_json::to_string(&source_type).expect("Failed to serialize SourceType");
            let deserialized: SourceType = serde_json::from_str(&json).expect("Failed to deserialize SourceType");
            assert_eq!(source_type, deserialized);
        }
    }

    #[test]
    fn test_app_settings_defaults() {
        let settings = AppSettings::default();
        
        // Verify default values
        assert_eq!(settings.general.default_language, "en");
        assert_eq!(settings.processing.quality_threshold, 0.7);
        assert_eq!(settings.export.default_format, DatasetFormat::JSONL);
        assert_eq!(settings.ui.theme, "system");
        
        // Test serialization
        let json = serde_json::to_string(&settings).expect("Failed to serialize AppSettings");
        let deserialized: AppSettings = serde_json::from_str(&json).expect("Failed to deserialize AppSettings");
        assert_eq!(settings.general.default_language, deserialized.general.default_language);
    }

    #[test]
    fn test_export_config_creation() {
        let export_config = ExportConfig {
            id: Uuid::new_v4(),
            name: "OpenAI Export".to_string(),
            platform: TargetPlatform::OpenAI,
            format: DatasetFormat::JSONL,
            compression: Some(CompressionType::Gzip),
            filters: vec![
                DataFilter {
                    field: "quality_score".to_string(),
                    operator: FilterOperator::GreaterThan,
                    value: FilterValue::Number(0.8),
                },
            ],
            transformations: vec![
                DataTransformation {
                    transformation_type: TransformationType::RemoveHtml,
                    parameters: HashMap::new(),
                },
            ],
            output_path: "/exports/openai_dataset.jsonl".to_string(),
            is_active: true,
            created_at: Utc::now(),
        };

        // Test serialization
        let json = serde_json::to_string(&export_config).expect("Failed to serialize ExportConfig");
        let deserialized: ExportConfig = serde_json::from_str(&json).expect("Failed to deserialize ExportConfig");
        assert_eq!(export_config.name, deserialized.name);
        assert_eq!(export_config.platform, deserialized.platform);
    }
}
