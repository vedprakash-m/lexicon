use crate::models::*;
use serde_json::{json, Value};

/// Generate JSON schema for any model type
pub trait JsonSchema {
    fn json_schema() -> Value;
}

impl JsonSchema for SourceText {
    fn json_schema() -> Value {
        json!({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "SourceText",
            "description": "A source text entity representing a book, document, or other content",
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "Unique identifier for the source text"
                },
                "title": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 1000,
                    "description": "Title of the source text"
                },
                "author": {
                    "type": ["string", "null"],
                    "maxLength": 500,
                    "description": "Author of the source text"
                },
                "language": {
                    "type": "string",
                    "pattern": "^[a-z]{2}$",
                    "description": "ISO 639-1 language code"
                },
                "source_type": {
                    "$ref": "#/definitions/SourceType"
                },
                "file_path": {
                    "type": ["string", "null"],
                    "maxLength": 4096,
                    "description": "Local file path to the source"
                },
                "url": {
                    "type": ["string", "null"],
                    "format": "uri",
                    "description": "URL to the source content"
                },
                "metadata": {
                    "$ref": "#/definitions/TextMetadata"
                },
                "processing_status": {
                    "$ref": "#/definitions/ProcessingStatus"
                },
                "created_at": {
                    "type": "string",
                    "format": "date-time"
                },
                "updated_at": {
                    "type": "string",
                    "format": "date-time"
                }
            },
            "required": ["id", "title", "language", "source_type", "metadata", "processing_status", "created_at", "updated_at"],
            "definitions": {
                "SourceType": {
                    "oneOf": [
                        { "const": "Book" },
                        { "const": "Article" },
                        { "const": "Website" },
                        { "const": "PDF" },
                        { "const": "PlainText" },
                        { "const": "Epub" },
                        { "const": "Docx" },
                        {
                            "type": "object",
                            "properties": {
                                "Other": { "type": "string" }
                            },
                            "required": ["Other"],
                            "additionalProperties": false
                        }
                    ]
                },
                "TextMetadata": TextMetadata::json_schema()["definitions"]["TextMetadata"].clone(),
                "ProcessingStatus": ProcessingStatus::json_schema()["definitions"]["ProcessingStatus"].clone()
            }
        })
    }
}

impl JsonSchema for TextMetadata {
    fn json_schema() -> Value {
        json!({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "definitions": {
                "TextMetadata": {
                    "type": "object",
                    "properties": {
                        "word_count": {
                            "type": ["integer", "null"],
                            "minimum": 0,
                            "maximum": 50000000
                        },
                        "character_count": {
                            "type": ["integer", "null"],
                            "minimum": 0,
                            "maximum": 200000000
                        },
                        "page_count": {
                            "type": ["integer", "null"],
                            "minimum": 0
                        },
                        "isbn": {
                            "type": ["string", "null"],
                            "pattern": "^(?:ISBN(?:-1[03])?:? )?(?=[0-9X]{10}$|(?=(?:[0-9]+[- ]){3})[- 0-9X]{13}$|97[89][0-9]{10}$|(?=(?:[0-9]+[- ]){4})[- 0-9]{17}$)(?:97[89][- ]?)?[0-9]{1,5}[- ]?[0-9]+[- ]?[0-9]+[- ]?[0-9X]$"
                        },
                        "publisher": {
                            "type": ["string", "null"],
                            "maxLength": 500
                        },
                        "publication_date": {
                            "type": ["string", "null"],
                            "format": "date-time"
                        },
                        "genre": {
                            "type": ["string", "null"],
                            "maxLength": 100
                        },
                        "tags": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "maxLength": 100
                            }
                        },
                        "description": {
                            "type": ["string", "null"],
                            "maxLength": 5000
                        },
                        "encoding": {
                            "type": ["string", "null"]
                        },
                        "file_size_bytes": {
                            "type": ["integer", "null"],
                            "minimum": 0
                        },
                        "checksum": {
                            "type": ["string", "null"]
                        },
                        "custom_fields": {
                            "type": "object",
                            "additionalProperties": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["tags", "custom_fields"]
                }
            }
        })
    }
}

impl JsonSchema for ProcessingStatus {
    fn json_schema() -> Value {
        json!({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "definitions": {
                "ProcessingStatus": {
                    "oneOf": [
                        { "const": "Pending" },
                        {
                            "type": "object",
                            "properties": {
                                "InProgress": {
                                    "type": "object",
                                    "properties": {
                                        "current_step": { "$ref": "#/definitions/ProcessingStep" },
                                        "progress_percent": {
                                            "type": "integer",
                                            "minimum": 0,
                                            "maximum": 100
                                        },
                                        "started_at": {
                                            "type": "string",
                                            "format": "date-time"
                                        }
                                    },
                                    "required": ["current_step", "progress_percent", "started_at"]
                                }
                            },
                            "required": ["InProgress"],
                            "additionalProperties": false
                        },
                        {
                            "type": "object",
                            "properties": {
                                "Completed": {
                                    "type": "object",
                                    "properties": {
                                        "completed_at": {
                                            "type": "string",
                                            "format": "date-time"
                                        },
                                        "processing_time_ms": {
                                            "type": "integer",
                                            "minimum": 0
                                        }
                                    },
                                    "required": ["completed_at", "processing_time_ms"]
                                }
                            },
                            "required": ["Completed"],
                            "additionalProperties": false
                        },
                        {
                            "type": "object",
                            "properties": {
                                "Failed": {
                                    "type": "object",
                                    "properties": {
                                        "error_message": { "type": "string" },
                                        "failed_at": {
                                            "type": "string",
                                            "format": "date-time"
                                        },
                                        "retry_count": {
                                            "type": "integer",
                                            "minimum": 0
                                        }
                                    },
                                    "required": ["error_message", "failed_at", "retry_count"]
                                }
                            },
                            "required": ["Failed"],
                            "additionalProperties": false
                        },
                        {
                            "type": "object",
                            "properties": {
                                "Cancelled": {
                                    "type": "object",
                                    "properties": {
                                        "cancelled_at": {
                                            "type": "string",
                                            "format": "date-time"
                                        }
                                    },
                                    "required": ["cancelled_at"]
                                }
                            },
                            "required": ["Cancelled"],
                            "additionalProperties": false
                        }
                    ]
                },
                "ProcessingStep": {
                    "enum": ["Parsing", "TextExtraction", "Cleaning", "Segmentation", "Chunking", "Validation", "Export"]
                }
            }
        })
    }
}

impl JsonSchema for Dataset {
    fn json_schema() -> Value {
        json!({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Dataset",
            "description": "A processed dataset ready for RAG applications",
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "format": "uuid"
                },
                "name": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 255
                },
                "description": {
                    "type": ["string", "null"],
                    "maxLength": 5000
                },
                "source_text_id": {
                    "type": "string",
                    "format": "uuid"
                },
                "dataset_type": {
                    "$ref": "#/definitions/DatasetType"
                },
                "format": {
                    "$ref": "#/definitions/DatasetFormat"
                },
                "chunking_strategy": {
                    "$ref": "#/definitions/ChunkingStrategy"
                },
                "chunks": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/TextChunk"
                    }
                },
                "quality_metrics": {
                    "$ref": "#/definitions/QualityMetrics"
                },
                "export_configs": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/ExportConfig"
                    }
                },
                "created_at": {
                    "type": "string",
                    "format": "date-time"
                },
                "updated_at": {
                    "type": "string",
                    "format": "date-time"
                }
            },
            "required": ["id", "name", "source_text_id", "dataset_type", "format", "chunking_strategy", "chunks", "quality_metrics", "export_configs", "created_at", "updated_at"],
            "definitions": {
                "DatasetType": {
                    "oneOf": [
                        { "const": "Standard" },
                        { "const": "Conversational" },
                        { "const": "QnA" },
                        { "const": "Summarization" },
                        { "const": "FineTuning" },
                        { "const": "Embedding" },
                        {
                            "type": "object",
                            "properties": {
                                "Custom": { "type": "string" }
                            },
                            "required": ["Custom"],
                            "additionalProperties": false
                        }
                    ]
                },
                "DatasetFormat": {
                    "oneOf": [
                        { "const": "JSONL" },
                        { "const": "JSON" },
                        { "const": "CSV" },
                        { "const": "Parquet" },
                        { "const": "HuggingFace" },
                        { "const": "OpenAI" },
                        {
                            "type": "object",
                            "properties": {
                                "Custom": { "type": "string" }
                            },
                            "required": ["Custom"],
                            "additionalProperties": false
                        }
                    ]
                },
                "ChunkingStrategy": ChunkingStrategy::json_schema()["definitions"]["ChunkingStrategy"].clone(),
                "TextChunk": TextChunk::json_schema()["definitions"]["TextChunk"].clone(),
                "QualityMetrics": QualityMetrics::json_schema()["definitions"]["QualityMetrics"].clone(),
                "ExportConfig": ExportConfig::json_schema()["definitions"]["ExportConfig"].clone()
            }
        })
    }
}

impl JsonSchema for ChunkingStrategy {
    fn json_schema() -> Value {
        json!({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "definitions": {
                "ChunkingStrategy": {
                    "type": "object",
                    "properties": {
                        "strategy_type": {
                            "$ref": "#/definitions/ChunkingType"
                        },
                        "target_size": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100000
                        },
                        "overlap_size": {
                            "type": "integer",
                            "minimum": 0
                        },
                        "respect_boundaries": {
                            "type": "boolean"
                        },
                        "min_chunk_size": {
                            "type": "integer",
                            "minimum": 1
                        },
                        "max_chunk_size": {
                            "type": "integer",
                            "minimum": 1
                        },
                        "separator_patterns": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["strategy_type", "target_size", "overlap_size", "respect_boundaries", "min_chunk_size", "max_chunk_size", "separator_patterns"]
                },
                "ChunkingType": {
                    "enum": ["FixedSize", "Semantic", "Structural", "Paragraph", "Sentence", "Hybrid"]
                }
            }
        })
    }
}

impl JsonSchema for TextChunk {
    fn json_schema() -> Value {
        json!({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "definitions": {
                "TextChunk": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "format": "uuid"
                        },
                        "content": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 100000
                        },
                        "metadata": {
                            "$ref": "#/definitions/ChunkMetadata"
                        },
                        "position": {
                            "$ref": "#/definitions/ChunkPosition"
                        },
                        "quality_score": {
                            "type": ["number", "null"],
                            "minimum": 0.0,
                            "maximum": 1.0
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time"
                        }
                    },
                    "required": ["id", "content", "metadata", "position", "created_at"]
                },
                "ChunkMetadata": {
                    "type": "object",
                    "properties": {
                        "word_count": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 50000
                        },
                        "character_count": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 200000
                        },
                        "language": {
                            "type": ["string", "null"],
                            "pattern": "^[a-z]{2}$"
                        },
                        "semantic_type": {
                            "type": ["string", "null"]
                        },
                        "importance_score": {
                            "type": ["number", "null"],
                            "minimum": 0.0,
                            "maximum": 1.0
                        },
                        "tags": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "maxLength": 100
                            }
                        },
                        "custom_fields": {
                            "type": "object",
                            "additionalProperties": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["word_count", "character_count", "tags", "custom_fields"]
                },
                "ChunkPosition": {
                    "type": "object",
                    "properties": {
                        "chapter": {
                            "type": ["string", "null"]
                        },
                        "section": {
                            "type": ["string", "null"]
                        },
                        "page_number": {
                            "type": ["integer", "null"],
                            "minimum": 1
                        },
                        "paragraph_index": {
                            "type": ["integer", "null"],
                            "minimum": 0
                        },
                        "start_offset": {
                            "type": "integer",
                            "minimum": 0
                        },
                        "end_offset": {
                            "type": "integer",
                            "minimum": 0
                        }
                    },
                    "required": ["start_offset", "end_offset"]
                }
            }
        })
    }
}

impl JsonSchema for QualityMetrics {
    fn json_schema() -> Value {
        json!({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "definitions": {
                "QualityMetrics": {
                    "type": "object",
                    "properties": {
                        "completeness_score": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0
                        },
                        "consistency_score": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0
                        },
                        "readability_score": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0
                        },
                        "semantic_coherence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0
                        },
                        "chunk_size_distribution": {
                            "$ref": "#/definitions/SizeDistribution"
                        },
                        "language_distribution": {
                            "type": "object",
                            "additionalProperties": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0
                            }
                        },
                        "duplicate_ratio": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0
                        },
                        "error_count": {
                            "type": "integer",
                            "minimum": 0
                        },
                        "warning_count": {
                            "type": "integer",
                            "minimum": 0
                        }
                    },
                    "required": ["completeness_score", "consistency_score", "readability_score", "semantic_coherence", "chunk_size_distribution", "language_distribution", "duplicate_ratio", "error_count", "warning_count"]
                },
                "SizeDistribution": {
                    "type": "object",
                    "properties": {
                        "mean": {
                            "type": "number",
                            "minimum": 0.0
                        },
                        "median": {
                            "type": "number",
                            "minimum": 0.0
                        },
                        "std_dev": {
                            "type": "number",
                            "minimum": 0.0
                        },
                        "min": {
                            "type": "integer",
                            "minimum": 0
                        },
                        "max": {
                            "type": "integer",
                            "minimum": 0
                        },
                        "percentiles": {
                            "type": "object",
                            "additionalProperties": {
                                "type": "integer",
                                "minimum": 0
                            }
                        }
                    },
                    "required": ["mean", "median", "std_dev", "min", "max", "percentiles"]
                }
            }
        })
    }
}

impl JsonSchema for ExportConfig {
    fn json_schema() -> Value {
        json!({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "definitions": {
                "ExportConfig": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "format": "uuid"
                        },
                        "name": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 255
                        },
                        "platform": {
                            "$ref": "#/definitions/TargetPlatform"
                        },
                        "format": {
                            "$ref": "#/definitions/DatasetFormat"
                        },
                        "compression": {
                            "type": ["string", "null"],
                            "enum": ["Gzip", "Bzip2", "Xz", "Zstd", null]
                        },
                        "filters": {
                            "type": "array",
                            "items": {
                                "$ref": "#/definitions/DataFilter"
                            }
                        },
                        "transformations": {
                            "type": "array",
                            "items": {
                                "$ref": "#/definitions/DataTransformation"
                            }
                        },
                        "output_path": {
                            "type": "string",
                            "minLength": 1
                        },
                        "is_active": {
                            "type": "boolean"
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time"
                        }
                    },
                    "required": ["id", "name", "platform", "format", "filters", "transformations", "output_path", "is_active", "created_at"]
                },
                "TargetPlatform": {
                    "oneOf": [
                        { "const": "OpenAI" },
                        { "const": "HuggingFace" },
                        { "const": "Anthropic" },
                        { "const": "Cohere" },
                        { "const": "Local" },
                        { "const": "S3" },
                        { "const": "GCS" },
                        { "const": "Azure" },
                        {
                            "type": "object",
                            "properties": {
                                "Custom": { "type": "string" }
                            },
                            "required": ["Custom"],
                            "additionalProperties": false
                        }
                    ]
                },
                "DataFilter": {
                    "type": "object",
                    "properties": {
                        "field": {
                            "type": "string",
                            "minLength": 1
                        },
                        "operator": {
                            "enum": ["Equals", "NotEquals", "Contains", "NotContains", "GreaterThan", "LessThan", "GreaterThanOrEqual", "LessThanOrEqual", "In", "NotIn", "Regex"]
                        },
                        "value": {
                            "$ref": "#/definitions/FilterValue"
                        }
                    },
                    "required": ["field", "operator", "value"]
                },
                "FilterValue": {
                    "oneOf": [
                        {
                            "type": "object",
                            "properties": {
                                "String": { "type": "string" }
                            },
                            "required": ["String"],
                            "additionalProperties": false
                        },
                        {
                            "type": "object",
                            "properties": {
                                "Number": { "type": "number" }
                            },
                            "required": ["Number"],
                            "additionalProperties": false
                        },
                        {
                            "type": "object",
                            "properties": {
                                "Boolean": { "type": "boolean" }
                            },
                            "required": ["Boolean"],
                            "additionalProperties": false
                        },
                        {
                            "type": "object",
                            "properties": {
                                "Array": {
                                    "type": "array",
                                    "items": { "type": "string" }
                                }
                            },
                            "required": ["Array"],
                            "additionalProperties": false
                        }
                    ]
                },
                "DataTransformation": {
                    "type": "object",
                    "properties": {
                        "transformation_type": {
                            "$ref": "#/definitions/TransformationType"
                        },
                        "parameters": {
                            "type": "object",
                            "additionalProperties": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["transformation_type", "parameters"]
                },
                "TransformationType": {
                    "oneOf": [
                        { "const": "RemoveHtml" },
                        { "const": "NormalizeWhitespace" },
                        { "const": "RemoveEmptyLines" },
                        { "const": "TrimWhitespace" },
                        { "const": "ReplacePattern" },
                        { "const": "AddPrefix" },
                        { "const": "AddSuffix" },
                        { "const": "Lowercase" },
                        { "const": "Uppercase" },
                        { "const": "RemoveStopWords" },
                        {
                            "type": "object",
                            "properties": {
                                "Custom": { "type": "string" }
                            },
                            "required": ["Custom"],
                            "additionalProperties": false
                        }
                    ]
                }
            }
        })
    }
}

/// Generate all schemas as a combined collection
pub fn generate_all_schemas() -> Value {
    json!({
        "schemas": {
            "SourceText": SourceText::json_schema(),
            "Dataset": Dataset::json_schema(),
            "TextChunk": TextChunk::json_schema(),
            "ChunkingStrategy": ChunkingStrategy::json_schema(),
            "QualityMetrics": QualityMetrics::json_schema(),
            "ExportConfig": ExportConfig::json_schema(),
            "TextMetadata": TextMetadata::json_schema(),
            "ProcessingStatus": ProcessingStatus::json_schema()
        },
        "version": "1.0.0",
        "description": "JSON schemas for Lexicon data models"
    })
}
