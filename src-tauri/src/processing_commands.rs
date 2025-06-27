use tauri::{command, State};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use crate::python_manager::PythonManagerState;

/// Configuration for advanced chunking
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AdvancedChunkingConfig {
    pub max_chunk_size: u32,
    pub overlap_size: u32,
    pub intelligent_overlap: bool,
    pub track_relationships: bool,
    pub extract_entities: bool,
    pub extract_topics: bool,
    pub dynamic_sizing: bool,
    pub custom_rules: Vec<ChunkingRule>,
}

/// Custom chunking rule
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChunkingRule {
    pub id: String,
    pub name: String,
    pub description: String,
    pub pattern: String,
    pub pattern_type: String, // "regex" or "keyword"
    pub priority: u32,
    pub enabled: bool,
}

/// Result of advanced chunking operation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AdvancedChunkingResult {
    pub chunks: Vec<ChunkResult>,
    pub relationships: Vec<ChunkRelationship>,
    pub metadata: ChunkingMetadata,
    pub processing_time_ms: u64,
}

/// Individual chunk result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChunkResult {
    pub id: String,
    pub text: String,
    pub start_char: u32,
    pub end_char: u32,
    pub chunk_type: String,
    pub quality_score: f32,
    pub metadata: ChunkMetadata,
}

/// Metadata for a chunk
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChunkMetadata {
    pub word_count: u32,
    pub char_count: u32,
    pub complexity: f32,
    pub topics: Vec<String>,
    pub entities: Vec<String>,
    pub custom_fields: HashMap<String, String>,
}

/// Relationship between chunks
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChunkRelationship {
    pub source_chunk_id: String,
    pub target_chunk_id: String,
    pub relationship_type: String, // "semantic", "structural", "sequential"
    pub strength: f32,
    pub metadata: HashMap<String, String>,
}

/// Overall chunking operation metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChunkingMetadata {
    pub total_chunks: u32,
    pub total_relationships: u32,
    pub average_chunk_size: f32,
    pub quality_score: f32,
    pub processing_steps: Vec<ProcessingStep>,
}

/// Processing step information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessingStep {
    pub step_name: String,
    pub status: String,
    pub duration_ms: u64,
    pub details: Option<String>,
}

/// Process text using advanced chunking
#[command]
pub async fn process_advanced_chunking(
    text: String,
    config: AdvancedChunkingConfig,
    python_manager: State<'_, PythonManagerState>,
) -> Result<AdvancedChunkingResult, String> {
    let manager = python_manager.lock().await;
    
    // Prepare the Python code to execute
    let python_code = format!(r#"
import sys
import json
import os
from pathlib import Path

# Add the processors directory to Python path
processors_path = Path(__file__).parent / "processors"
if processors_path.exists():
    sys.path.insert(0, str(processors_path))
else:
    # Try relative path from python-engine directory
    processors_path = Path("processors")
    if processors_path.exists():
        sys.path.insert(0, str(processors_path.absolute()))

try:
    from advanced_chunking import AdvancedChunkingEngine
    
    # Load text and config from arguments
    text_content = r'''{}'''
    config_data = {{
        "max_chunk_size": {},
        "overlap_size": {},
        "intelligent_overlap": {},
        "track_relationships": {},
        "extract_entities": {},
        "extract_topics": {},
        "dynamic_sizing": {},
        "custom_rules": {}
    }}
    
    # Create chunking engine
    engine = AdvancedChunkingEngine()
    
    # Process the text
    result = engine.process_text(text_content, config_data)
    
    # Output result as JSON
    print(json.dumps(result))
    
except ImportError as e:
    print(json.dumps({{"error": f"Import error: {{str(e)}}. Please ensure the processors module is available."}}))
except Exception as e:
    print(json.dumps({{"error": f"Processing error: {{str(e)}}"}}))
"#, 
        text.replace("'", "\\'").replace("\n", "\\n"),
        config.max_chunk_size,
        config.overlap_size,
        config.intelligent_overlap,
        config.track_relationships,
        config.extract_entities,
        config.extract_topics,
        config.dynamic_sizing,
        serde_json::to_string(&config.custom_rules).unwrap_or_else(|_| "[]".to_string())
    );
    
    let result = manager.execute_code(&python_code).await
        .map_err(|e| format!("Failed to execute Python code: {}", e))?;
    
    // Parse the result
    let output = result.stdout.trim();
    if output.is_empty() {
        let error_msg = if !result.stderr.is_empty() {
            format!("Python error: {}", result.stderr)
        } else {
            "No output from Python script".to_string()
        };
        return Err(error_msg);
    }
    
    // Try to parse as JSON
    let parsed_result: serde_json::Value = serde_json::from_str(output)
        .map_err(|e| format!("Failed to parse Python output: {}\nOutput: {}\nStderr: {}", e, output, result.stderr))?;
    
    // Check for errors
    if let Some(error) = parsed_result.get("error") {
        return Err(format!("Python processing error: {}", error));
    }
    
    // Convert to our result type
    let chunking_result: AdvancedChunkingResult = serde_json::from_value(parsed_result)
        .map_err(|e| format!("Failed to convert result: {}", e))?;
    
    Ok(chunking_result)
}

/// Validate chunking configuration
#[command]
pub async fn validate_chunking_config(
    config: AdvancedChunkingConfig,
) -> Result<Vec<String>, String> {
    let mut validation_errors = Vec::new();
    
    // Validate basic settings
    if config.max_chunk_size == 0 {
        validation_errors.push("Max chunk size must be greater than 0".to_string());
    }
    
    if config.overlap_size >= config.max_chunk_size {
        validation_errors.push("Overlap size must be less than max chunk size".to_string());
    }
    
    // Validate custom rules
    for rule in &config.custom_rules {
        if rule.name.trim().is_empty() {
            validation_errors.push(format!("Rule '{}' has empty name", rule.id));
        }
        
        if rule.pattern.trim().is_empty() {
            validation_errors.push(format!("Rule '{}' has empty pattern", rule.name));
        }
        
        if rule.pattern_type != "regex" && rule.pattern_type != "keyword" {
            validation_errors.push(format!("Rule '{}' has invalid pattern type: {}", rule.name, rule.pattern_type));
        }
        
        // Validate regex patterns
        if rule.pattern_type == "regex" {
            if let Err(e) = regex::Regex::new(&rule.pattern) {
                validation_errors.push(format!("Rule '{}' has invalid regex pattern: {}", rule.name, e));
            }
        }
    }
    
    Ok(validation_errors)
}

/// Get available chunking strategies
#[command]
pub async fn get_chunking_strategies() -> Result<Vec<ChunkingStrategy>, String> {
    Ok(vec![
        ChunkingStrategy {
            id: "fixed".to_string(),
            name: "Fixed Size".to_string(),
            description: "Split text into fixed-size chunks".to_string(),
            supports_overlap: true,
            supports_custom_rules: false,
        },
        ChunkingStrategy {
            id: "semantic".to_string(),
            name: "Semantic".to_string(),
            description: "Split based on semantic boundaries".to_string(),
            supports_overlap: true,
            supports_custom_rules: true,
        },
        ChunkingStrategy {
            id: "structural".to_string(),
            name: "Structural".to_string(),
            description: "Split based on document structure".to_string(),
            supports_overlap: false,
            supports_custom_rules: true,
        },
        ChunkingStrategy {
            id: "adaptive".to_string(),
            name: "Adaptive".to_string(),
            description: "Dynamically adjust chunk size based on content".to_string(),
            supports_overlap: true,
            supports_custom_rules: true,
        },
    ])
}

/// Available chunking strategy
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChunkingStrategy {
    pub id: String,
    pub name: String,
    pub description: String,
    pub supports_overlap: bool,
    pub supports_custom_rules: bool,
}

/// Test chunking configuration with sample text
#[command]
pub async fn test_chunking_config(
    config: AdvancedChunkingConfig,
    python_manager: State<'_, PythonManagerState>,
) -> Result<AdvancedChunkingResult, String> {
    let sample_text = r#"Chapter 2: Contents of the Gita Summarized

Text 47
कर्मण्येवाधिकारस्ते मा फलेषु कदाचन ।
मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि ॥ ४७ ॥

Translation
You have a right to perform your prescribed duty, but you are not entitled 
to the fruits of action. Never consider yourself the cause of the results 
of your activities, and never be attached to not doing your duty.

Purport
This verse is the essence of karma-yoga. Lord Krishna explains the principle
of detached action, which is fundamental to spiritual progress. The soul
engaged in karma-yoga performs all activities without attachment to results."#;
    
    process_advanced_chunking(sample_text.to_string(), config, python_manager).await
}
