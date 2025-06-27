use tauri::State;
use std::collections::HashMap;
use std::sync::Mutex;
use chrono::Utc;

use crate::models::{SourceText, Dataset, ProcessingStatus, ProcessingStep};
use crate::validation::Validate;

// In-memory storage for the state (in a real app, this would be a database)
#[derive(Default)]
pub struct StateStorage {
    source_texts: Mutex<HashMap<String, SourceText>>,
    datasets: Mutex<HashMap<String, Dataset>>,
}

impl StateStorage {
    pub fn new() -> Self {
        Self {
            source_texts: Mutex::new(HashMap::new()),
            datasets: Mutex::new(HashMap::new()),
        }
    }
}

// Tauri commands for state management
#[tauri::command]
pub async fn get_all_source_texts(
    storage: State<'_, StateStorage>,
) -> Result<Vec<SourceText>, String> {
    let source_texts = storage.source_texts.lock()
        .map_err(|e| format!("Failed to acquire lock: {}", e))?;
    
    Ok(source_texts.values().cloned().collect())
}

#[tauri::command]
pub async fn get_source_text(
    id: String,
    storage: State<'_, StateStorage>,
) -> Result<Option<SourceText>, String> {
    let source_texts = storage.source_texts.lock()
        .map_err(|e| format!("Failed to acquire lock: {}", e))?;
    
    Ok(source_texts.get(&id).cloned())
}

#[tauri::command]
pub async fn save_source_text(
    source_text: SourceText,
    storage: State<'_, StateStorage>,
) -> Result<(), String> {
    // Validate the source text
    source_text.validate()
        .map_err(|e| format!("Validation failed: {:?}", e))?;

    let mut source_texts = storage.source_texts.lock()
        .map_err(|e| format!("Failed to acquire lock: {}", e))?;
    
    source_texts.insert(source_text.id.to_string(), source_text);
    Ok(())
}

#[tauri::command]
pub async fn delete_source_text(
    id: String,
    storage: State<'_, StateStorage>,
) -> Result<bool, String> {
    let mut source_texts = storage.source_texts.lock()
        .map_err(|e| format!("Failed to acquire lock: {}", e))?;
    
    Ok(source_texts.remove(&id).is_some())
}

#[tauri::command]
pub async fn get_all_datasets(
    storage: State<'_, StateStorage>,
) -> Result<Vec<Dataset>, String> {
    let datasets = storage.datasets.lock()
        .map_err(|e| format!("Failed to acquire lock: {}", e))?;
    
    Ok(datasets.values().cloned().collect())
}

#[tauri::command]
pub async fn get_dataset(
    id: String,
    storage: State<'_, StateStorage>,
) -> Result<Option<Dataset>, String> {
    let datasets = storage.datasets.lock()
        .map_err(|e| format!("Failed to acquire lock: {}", e))?;
    
    Ok(datasets.get(&id).cloned())
}

#[tauri::command]
pub async fn save_dataset(
    dataset: Dataset,
    storage: State<'_, StateStorage>,
) -> Result<(), String> {
    // Validate the dataset
    dataset.validate()
        .map_err(|e| format!("Validation failed: {:?}", e))?;

    let mut datasets = storage.datasets.lock()
        .map_err(|e| format!("Failed to acquire lock: {}", e))?;
    
    datasets.insert(dataset.id.to_string(), dataset);
    Ok(())
}

#[tauri::command]
pub async fn delete_dataset(
    id: String,
    storage: State<'_, StateStorage>,
) -> Result<bool, String> {
    let mut datasets = storage.datasets.lock()
        .map_err(|e| format!("Failed to acquire lock: {}", e))?;
    
    Ok(datasets.remove(&id).is_some())
}

#[tauri::command]
pub async fn process_source_text(
    source_text_id: String,
    chunking_strategy: Option<serde_json::Value>,
    storage: State<'_, StateStorage>,
) -> Result<serde_json::Value, String> {
    // Get the source text
    let source_text = {
        let source_texts = storage.source_texts.lock()
            .map_err(|e| format!("Failed to acquire lock: {}", e))?;
        
        source_texts.get(&source_text_id)
            .cloned()
            .ok_or("Source text not found")?
    };

    // Update status to processing
    {
        let mut source_texts = storage.source_texts.lock()
            .map_err(|e| format!("Failed to acquire lock: {}", e))?;
        
        if let Some(st) = source_texts.get_mut(&source_text_id) {
            st.processing_status = ProcessingStatus::InProgress {
                current_step: ProcessingStep::Parsing,
                progress_percent: 0,
                started_at: Utc::now(),
            };
            st.updated_at = Utc::now();
        }
    }

    // Simulate processing (in real implementation, this would call Python scripts)
    tokio::time::sleep(tokio::time::Duration::from_millis(1000)).await;

    // Update status to completed
    {
        let mut source_texts = storage.source_texts.lock()
            .map_err(|e| format!("Failed to acquire lock: {}", e))?;
        
        if let Some(st) = source_texts.get_mut(&source_text_id) {
            st.processing_status = ProcessingStatus::Completed {
                completed_at: Utc::now(),
                processing_time_ms: 1000,
            };
            st.updated_at = Utc::now();
        }
    }

    Ok(serde_json::json!({
        "success": true,
        "source_text_id": source_text_id,
        "chunks_created": 42, // Placeholder
        "processing_time_ms": 1000
    }))
}

#[tauri::command]
pub async fn generate_dataset(
    dataset_id: String,
    export_config: Option<serde_json::Value>,
    storage: State<'_, StateStorage>,
) -> Result<serde_json::Value, String> {
    // Get the dataset
    let dataset = {
        let datasets = storage.datasets.lock()
            .map_err(|e| format!("Failed to acquire lock: {}", e))?;
        
        datasets.get(&dataset_id)
            .cloned()
            .ok_or("Dataset not found")?
    };

    // Simulate dataset generation
    tokio::time::sleep(tokio::time::Duration::from_millis(2000)).await;

    // Update dataset updated_at timestamp
    {
        let mut datasets = storage.datasets.lock()
            .map_err(|e| format!("Failed to acquire lock: {}", e))?;
        
        if let Some(ds) = datasets.get_mut(&dataset_id) {
            ds.updated_at = Utc::now();
        }
    }

    Ok(serde_json::json!({
        "success": true,
        "dataset_id": dataset_id,
        "output_path": format!("/tmp/dataset_{}.jsonl", dataset_id),
        "total_chunks": dataset.chunks.len(),
        "file_size_bytes": 1024000
    }))
}

#[tauri::command]
pub async fn clear_all_data(
    storage: State<'_, StateStorage>,
) -> Result<(), String> {
    let mut source_texts = storage.source_texts.lock()
        .map_err(|e| format!("Failed to acquire lock: {}", e))?;
    let mut datasets = storage.datasets.lock()
        .map_err(|e| format!("Failed to acquire lock: {}", e))?;
    
    source_texts.clear();
    datasets.clear();
    
    Ok(())
}

#[tauri::command]
pub async fn get_state_stats(
    storage: State<'_, StateStorage>,
) -> Result<serde_json::Value, String> {
    let source_texts = storage.source_texts.lock()
        .map_err(|e| format!("Failed to acquire lock: {}", e))?;
    let datasets = storage.datasets.lock()
        .map_err(|e| format!("Failed to acquire lock: {}", e))?;
    
    Ok(serde_json::json!({
        "source_texts_count": source_texts.len(),
        "datasets_count": datasets.len(),
        "total_chunks": datasets.values().map(|d| d.chunks.len()).sum::<usize>(),
    }))
}
