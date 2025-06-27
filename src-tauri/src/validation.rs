use crate::models::*;
use thiserror::Error;
use regex::Regex;

#[derive(Error, Debug)]
pub enum ValidationError {
    #[error("Field '{field}' is required but was empty")]
    RequiredFieldEmpty { field: String },
    
    #[error("Field '{field}' has invalid value: {message}")]
    InvalidValue { field: String, message: String },
    
    #[error("Field '{field}' exceeds maximum length of {max_length}")]
    TooLong { field: String, max_length: usize },
    
    #[error("Field '{field}' is below minimum length of {min_length}")]
    TooShort { field: String, min_length: usize },
    
    #[error("Field '{field}' has invalid format: {message}")]
    InvalidFormat { field: String, message: String },
    
    #[error("Value '{value}' is out of range [{min}, {max}] for field '{field}'")]
    OutOfRange { field: String, value: f64, min: f64, max: f64 },
    
    #[error("Multiple validation errors: {errors:?}")]
    Multiple { errors: Vec<ValidationError> },
}

pub type ValidationResult<T> = Result<T, ValidationError>;

/// Trait for validating data models
pub trait Validate {
    fn validate(&self) -> ValidationResult<()>;
}

impl Validate for SourceText {
    fn validate(&self) -> ValidationResult<()> {
        let mut errors = Vec::new();

        // Title validation
        if self.title.trim().is_empty() {
            errors.push(ValidationError::RequiredFieldEmpty {
                field: "title".to_string(),
            });
        } else if self.title.len() > 1000 {
            errors.push(ValidationError::TooLong {
                field: "title".to_string(),
                max_length: 1000,
            });
        }

        // Language validation
        if self.language.trim().is_empty() {
            errors.push(ValidationError::RequiredFieldEmpty {
                field: "language".to_string(),
            });
        } else if !is_valid_language_code(&self.language) {
            errors.push(ValidationError::InvalidFormat {
                field: "language".to_string(),
                message: "Must be a valid ISO 639-1 language code".to_string(),
            });
        }

        // URL validation if provided
        if let Some(ref url) = self.url {
            if !url.trim().is_empty() && !is_valid_url(url) {
                errors.push(ValidationError::InvalidFormat {
                    field: "url".to_string(),
                    message: "Must be a valid URL".to_string(),
                });
            }
        }

        // File path validation if provided
        if let Some(ref path) = self.file_path {
            if !path.trim().is_empty() && path.len() > 4096 {
                errors.push(ValidationError::TooLong {
                    field: "file_path".to_string(),
                    max_length: 4096,
                });
            }
        }

        // Metadata validation
        if let Err(e) = self.metadata.validate() {
            errors.push(e);
        }

        if errors.is_empty() {
            Ok(())
        } else if errors.len() == 1 {
            Err(errors.into_iter().next().unwrap())
        } else {
            Err(ValidationError::Multiple { errors })
        }
    }
}

impl Validate for TextMetadata {
    fn validate(&self) -> ValidationResult<()> {
        let mut errors = Vec::new();

        // Word count validation
        if let Some(word_count) = self.word_count {
            if word_count > 50_000_000 {
                errors.push(ValidationError::OutOfRange {
                    field: "word_count".to_string(),
                    value: word_count as f64,
                    min: 0.0,
                    max: 50_000_000.0,
                });
            }
        }

        // Character count validation
        if let Some(char_count) = self.character_count {
            if char_count > 200_000_000 {
                errors.push(ValidationError::OutOfRange {
                    field: "character_count".to_string(),
                    value: char_count as f64,
                    min: 0.0,
                    max: 200_000_000.0,
                });
            }
        }

        // ISBN validation
        if let Some(ref isbn) = self.isbn {
            if !isbn.trim().is_empty() && !is_valid_isbn(isbn) {
                errors.push(ValidationError::InvalidFormat {
                    field: "isbn".to_string(),
                    message: "Must be a valid ISBN-10 or ISBN-13".to_string(),
                });
            }
        }

        // Tag validation
        for tag in &self.tags {
            if tag.len() > 100 {
                errors.push(ValidationError::TooLong {
                    field: "tag".to_string(),
                    max_length: 100,
                });
            }
        }

        if errors.is_empty() {
            Ok(())
        } else if errors.len() == 1 {
            Err(errors.into_iter().next().unwrap())
        } else {
            Err(ValidationError::Multiple { errors })
        }
    }
}

impl Validate for Dataset {
    fn validate(&self) -> ValidationResult<()> {
        let mut errors = Vec::new();

        // Name validation
        if self.name.trim().is_empty() {
            errors.push(ValidationError::RequiredFieldEmpty {
                field: "name".to_string(),
            });
        } else if self.name.len() > 255 {
            errors.push(ValidationError::TooLong {
                field: "name".to_string(),
                max_length: 255,
            });
        }

        // Chunking strategy validation
        if let Err(e) = self.chunking_strategy.validate() {
            errors.push(e);
        }

        // Quality metrics validation
        if let Err(e) = self.quality_metrics.validate() {
            errors.push(e);
        }

        // Chunk validation
        for (i, chunk) in self.chunks.iter().enumerate() {
            if let Err(e) = chunk.validate() {
                errors.push(ValidationError::InvalidValue {
                    field: format!("chunks[{}]", i),
                    message: format!("Chunk validation failed: {}", e),
                });
            }
        }

        if errors.is_empty() {
            Ok(())
        } else if errors.len() == 1 {
            Err(errors.into_iter().next().unwrap())
        } else {
            Err(ValidationError::Multiple { errors })
        }
    }
}

impl Validate for TextChunk {
    fn validate(&self) -> ValidationResult<()> {
        let mut errors = Vec::new();

        // Content validation
        if self.content.trim().is_empty() {
            errors.push(ValidationError::RequiredFieldEmpty {
                field: "content".to_string(),
            });
        } else if self.content.len() > 100_000 {
            errors.push(ValidationError::TooLong {
                field: "content".to_string(),
                max_length: 100_000,
            });
        }

        // Quality score validation
        if let Some(score) = self.quality_score {
            if !(0.0..=1.0).contains(&score) {
                errors.push(ValidationError::OutOfRange {
                    field: "quality_score".to_string(),
                    value: score as f64,
                    min: 0.0,
                    max: 1.0,
                });
            }
        }

        // Metadata validation
        if let Err(e) = self.metadata.validate() {
            errors.push(e);
        }

        if errors.is_empty() {
            Ok(())
        } else if errors.len() == 1 {
            Err(errors.into_iter().next().unwrap())
        } else {
            Err(ValidationError::Multiple { errors })
        }
    }
}

impl Validate for ChunkMetadata {
    fn validate(&self) -> ValidationResult<()> {
        let mut errors = Vec::new();

        // Word count should be reasonable
        if self.word_count > 50_000 {
            errors.push(ValidationError::OutOfRange {
                field: "word_count".to_string(),
                value: self.word_count as f64,
                min: 0.0,
                max: 50_000.0,
            });
        }

        // Character count should be reasonable
        if self.character_count > 200_000 {
            errors.push(ValidationError::OutOfRange {
                field: "character_count".to_string(),
                value: self.character_count as f64,
                min: 0.0,
                max: 200_000.0,
            });
        }

        // Importance score validation
        if let Some(score) = self.importance_score {
            if !(0.0..=1.0).contains(&score) {
                errors.push(ValidationError::OutOfRange {
                    field: "importance_score".to_string(),
                    value: score as f64,
                    min: 0.0,
                    max: 1.0,
                });
            }
        }

        if errors.is_empty() {
            Ok(())
        } else if errors.len() == 1 {
            Err(errors.into_iter().next().unwrap())
        } else {
            Err(ValidationError::Multiple { errors })
        }
    }
}

impl Validate for ChunkingStrategy {
    fn validate(&self) -> ValidationResult<()> {
        let mut errors = Vec::new();

        // Target size validation
        if self.target_size == 0 {
            errors.push(ValidationError::InvalidValue {
                field: "target_size".to_string(),
                message: "Must be greater than 0".to_string(),
            });
        } else if self.target_size > 100_000 {
            errors.push(ValidationError::OutOfRange {
                field: "target_size".to_string(),
                value: self.target_size as f64,
                min: 1.0,
                max: 100_000.0,
            });
        }

        // Min/max chunk size validation
        if self.min_chunk_size > self.max_chunk_size {
            errors.push(ValidationError::InvalidValue {
                field: "min_chunk_size".to_string(),
                message: "Must be less than or equal to max_chunk_size".to_string(),
            });
        }

        if self.min_chunk_size > self.target_size {
            errors.push(ValidationError::InvalidValue {
                field: "min_chunk_size".to_string(),
                message: "Must be less than or equal to target_size".to_string(),
            });
        }

        // Overlap validation
        if self.overlap_size >= self.target_size {
            errors.push(ValidationError::InvalidValue {
                field: "overlap_size".to_string(),
                message: "Must be less than target_size".to_string(),
            });
        }

        if errors.is_empty() {
            Ok(())
        } else if errors.len() == 1 {
            Err(errors.into_iter().next().unwrap())
        } else {
            Err(ValidationError::Multiple { errors })
        }
    }
}

impl Validate for QualityMetrics {
    fn validate(&self) -> ValidationResult<()> {
        let mut errors = Vec::new();

        // Score validation (all should be 0.0-1.0)
        let scores = [
            ("completeness_score", self.completeness_score),
            ("consistency_score", self.consistency_score),
            ("readability_score", self.readability_score),
            ("semantic_coherence", self.semantic_coherence),
            ("duplicate_ratio", self.duplicate_ratio),
        ];

        for (field, score) in scores {
            if !(0.0..=1.0).contains(&score) {
                errors.push(ValidationError::OutOfRange {
                    field: field.to_string(),
                    value: score as f64,
                    min: 0.0,
                    max: 1.0,
                });
            }
        }

        // Size distribution validation
        if let Err(e) = self.chunk_size_distribution.validate() {
            errors.push(e);
        }

        if errors.is_empty() {
            Ok(())
        } else if errors.len() == 1 {
            Err(errors.into_iter().next().unwrap())
        } else {
            Err(ValidationError::Multiple { errors })
        }
    }
}

impl Validate for SizeDistribution {
    fn validate(&self) -> ValidationResult<()> {
        let mut errors = Vec::new();

        // Basic statistical validation
        if self.min > self.max {
            errors.push(ValidationError::InvalidValue {
                field: "min".to_string(),
                message: "Must be less than or equal to max".to_string(),
            });
        }

        if self.std_dev < 0.0 {
            errors.push(ValidationError::InvalidValue {
                field: "std_dev".to_string(),
                message: "Must be non-negative".to_string(),
            });
        }

        if self.mean < 0.0 {
            errors.push(ValidationError::InvalidValue {
                field: "mean".to_string(),
                message: "Must be non-negative".to_string(),
            });
        }

        if errors.is_empty() {
            Ok(())
        } else if errors.len() == 1 {
            Err(errors.into_iter().next().unwrap())
        } else {
            Err(ValidationError::Multiple { errors })
        }
    }
}

impl Validate for ProcessingJob {
    fn validate(&self) -> ValidationResult<()> {
        let mut errors = Vec::new();

        // Progress validation
        if let Err(e) = self.progress.validate() {
            errors.push(e);
        }

        // Timestamp consistency
        if let (Some(started), Some(completed)) = (self.started_at, self.completed_at) {
            if started > completed {
                errors.push(ValidationError::InvalidValue {
                    field: "completed_at".to_string(),
                    message: "Must be after started_at".to_string(),
                });
            }
        }

        if errors.is_empty() {
            Ok(())
        } else if errors.len() == 1 {
            Err(errors.into_iter().next().unwrap())
        } else {
            Err(ValidationError::Multiple { errors })
        }
    }
}

impl Validate for JobProgress {
    fn validate(&self) -> ValidationResult<()> {
        let mut errors = Vec::new();

        // Progress percent validation
        if self.progress_percent > 100 {
            errors.push(ValidationError::OutOfRange {
                field: "progress_percent".to_string(),
                value: self.progress_percent as f64,
                min: 0.0,
                max: 100.0,
            });
        }

        // Steps validation
        if self.steps_completed > self.total_steps {
            errors.push(ValidationError::InvalidValue {
                field: "steps_completed".to_string(),
                message: "Cannot exceed total_steps".to_string(),
            });
        }

        if errors.is_empty() {
            Ok(())
        } else if errors.len() == 1 {
            Err(errors.into_iter().next().unwrap())
        } else {
            Err(ValidationError::Multiple { errors })
        }
    }
}

// Helper functions for validation

fn is_valid_language_code(code: &str) -> bool {
    // Basic validation for ISO 639-1 codes (2 letters)
    let re = Regex::new(r"^[a-z]{2}$").unwrap();
    re.is_match(code)
}

fn is_valid_url(url: &str) -> bool {
    // Basic URL validation
    url.starts_with("http://") || url.starts_with("https://") || url.starts_with("file://")
}

fn is_valid_isbn(isbn: &str) -> bool {
    // Remove hyphens and spaces
    let cleaned = isbn.replace(['-', ' '], "");
    
    // Check ISBN-10 or ISBN-13
    if cleaned.len() == 10 {
        is_valid_isbn10(&cleaned)
    } else if cleaned.len() == 13 {
        is_valid_isbn13(&cleaned)
    } else {
        false
    }
}

fn is_valid_isbn10(isbn: &str) -> bool {
    if isbn.len() != 10 {
        return false;
    }
    
    let mut sum = 0;
    for (i, ch) in isbn.chars().enumerate() {
        if i == 9 && (ch == 'X' || ch == 'x') {
            sum += 10 * (10 - i);
        } else if let Some(digit) = ch.to_digit(10) {
            sum += digit as usize * (10 - i);
        } else {
            return false;
        }
    }
    
    sum % 11 == 0
}

fn is_valid_isbn13(isbn: &str) -> bool {
    if isbn.len() != 13 {
        return false;
    }
    
    let mut sum = 0;
    for (i, ch) in isbn.chars().enumerate() {
        if let Some(digit) = ch.to_digit(10) {
            let weight = if i % 2 == 0 { 1 } else { 3 };
            sum += digit as usize * weight;
        } else {
            return false;
        }
    }
    
    sum % 10 == 0
}

#[cfg(test)]
mod tests {
    use super::*;
    use uuid::Uuid;
    use chrono::Utc;

    #[test]
    fn test_source_text_validation() {
        let mut source = SourceText {
            id: Uuid::new_v4(),
            title: "Test Book".to_string(),
            author: Some("Test Author".to_string()),
            language: "en".to_string(),
            source_type: SourceType::Book,
            file_path: None,
            url: None,
            metadata: TextMetadata {
                word_count: Some(1000),
                character_count: Some(5000),
                page_count: Some(100),
                isbn: None,
                publisher: None,
                publication_date: None,
                genre: None,
                tags: Vec::new(),
                description: None,
                encoding: None,
                file_size_bytes: None,
                checksum: None,
                custom_fields: Default::default(),
            },
            processing_status: ProcessingStatus::Pending,
            created_at: Utc::now(),
            updated_at: Utc::now(),
        };

        assert!(source.validate().is_ok());

        // Test empty title
        source.title = "".to_string();
        assert!(source.validate().is_err());

        // Test invalid language
        source.title = "Test Book".to_string();
        source.language = "invalid".to_string();
        assert!(source.validate().is_err());
    }

    #[test]
    fn test_chunking_strategy_validation() {
        let mut strategy = ChunkingStrategy::default();
        assert!(strategy.validate().is_ok());

        // Test invalid target size
        strategy.target_size = 0;
        assert!(strategy.validate().is_err());

        // Test min > max
        strategy.target_size = 1000;
        strategy.min_chunk_size = 500;
        strategy.max_chunk_size = 300;
        assert!(strategy.validate().is_err());
    }

    #[test]
    fn test_isbn_validation() {
        assert!(is_valid_isbn("0-596-52068-9"));  // Valid ISBN-10
        assert!(is_valid_isbn("978-0-596-52068-7"));  // Valid ISBN-13
        assert!(!is_valid_isbn("123456789"));  // Invalid
        assert!(!is_valid_isbn("978-0-596-52068-8"));  // Invalid checksum
    }
}
