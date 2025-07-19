use tauri::{command, State};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;
use chrono::{DateTime, Utc};
use tokio::sync::Mutex;
use std::path::PathBuf;
use tokio::fs;
use serde_json;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportConfig {
    pub format: String,
    pub output_path: String,
    pub compression: String,
    pub include_metadata: bool,
    pub flatten_nested: bool,
    pub custom_template: Option<String>,
    pub include_fields: Option<Vec<String>>,
    pub exclude_fields: Option<Vec<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportJob {
    pub id: String,
    pub config: ExportConfig,
    pub status: ExportStatus,
    pub progress: f64,
    pub records_exported: u64,
    pub file_size_bytes: u64,
    pub export_time_seconds: f64,
    pub start_time: DateTime<Utc>,
    pub end_time: Option<DateTime<Utc>>,
    pub error_message: Option<String>,
    pub source_dataset_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ExportStatus {
    Pending,
    Running,
    Completed,
    Failed,
    Cancelled,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportProgress {
    pub job_id: String,
    pub progress: f64,
    pub records_exported: u64,
    pub estimated_completion: Option<DateTime<Utc>>,
    pub current_file: Option<String>,
}

pub struct ExportManager {
    jobs: HashMap<String, ExportJob>,
}

impl ExportManager {
    pub fn new() -> Self {
        Self {
            jobs: HashMap::new(),
        }
    }

    pub fn create_export_job(&mut self, config: ExportConfig, source_dataset_id: Option<String>) -> Result<String, String> {
        let job_id = Uuid::new_v4().to_string();
        
        let job = ExportJob {
            id: job_id.clone(),
            config,
            status: ExportStatus::Pending,
            progress: 0.0,
            records_exported: 0,
            file_size_bytes: 0,
            export_time_seconds: 0.0,
            start_time: Utc::now(),
            end_time: None,
            error_message: None,
            source_dataset_id,
        };

        self.jobs.insert(job_id.clone(), job);
        Ok(job_id)
    }

    pub fn get_export_jobs(&self) -> Vec<ExportJob> {
        self.jobs.values().cloned().collect()
    }

    pub fn get_export_job(&self, job_id: &str) -> Option<ExportJob> {
        self.jobs.get(job_id).cloned()
    }

    pub fn update_job_progress(&mut self, job_id: &str, progress: f64, records_exported: u64) -> Result<(), String> {
        if let Some(job) = self.jobs.get_mut(job_id) {
            job.progress = progress;
            job.records_exported = records_exported;
            if progress >= 100.0 {
                job.status = ExportStatus::Completed;
                job.end_time = Some(Utc::now());
            } else {
                job.status = ExportStatus::Running;
            }
            Ok(())
        } else {
            Err(format!("Export job {} not found", job_id))
        }
    }

    pub fn cancel_export_job(&mut self, job_id: &str) -> Result<(), String> {
        if let Some(job) = self.jobs.get_mut(job_id) {
            job.status = ExportStatus::Cancelled;
            job.end_time = Some(Utc::now());
            Ok(())
        } else {
            Err(format!("Export job {} not found", job_id))
        }
    }

    pub fn fail_export_job(&mut self, job_id: &str, error: &str) -> Result<(), String> {
        if let Some(job) = self.jobs.get_mut(job_id) {
            job.status = ExportStatus::Failed;
            job.error_message = Some(error.to_string());
            job.end_time = Some(Utc::now());
            Ok(())
        } else {
            Err(format!("Export job {} not found", job_id))
        }
    }

    pub async fn execute_export(&mut self, job_id: &str, data: &serde_json::Value) -> Result<(), String> {
        let job = self.jobs.get(job_id).ok_or_else(|| format!("Export job {} not found", job_id))?;
        let config = job.config.clone();
        
        // Start the job
        self.update_job_progress(job_id, 0.0, 0)?;
        
        // Simulate export process (in real implementation, this would export actual data)
        let output_path = PathBuf::from(&config.output_path);
        
        // Ensure directory exists
        if let Some(parent) = output_path.parent() {
            fs::create_dir_all(parent).await.map_err(|e| format!("Failed to create output directory: {}", e))?;
        }

        // Export based on format
        match config.format.as_str() {
            "json" => self.export_json(job_id, &config, data).await?,
            "jsonl" => self.export_jsonl(job_id, &config, data).await?,
            "csv" => self.export_csv(job_id, &config, data).await?,
            "parquet" => self.export_parquet(job_id, &config, data).await?,
            _ => return Err(format!("Unsupported export format: {}", config.format)),
        }

        Ok(())
    }

    async fn export_json(&mut self, job_id: &str, config: &ExportConfig, data: &serde_json::Value) -> Result<(), String> {
        self.update_job_progress(job_id, 25.0, 0)?;
        
        let json_content = if config.include_metadata {
            serde_json::json!({
                "metadata": {
                    "export_time": Utc::now(),
                    "format": "json",
                    "total_records": data.as_array().map_or(1, |arr| arr.len())
                },
                "data": data
            })
        } else {
            data.clone()
        };

        self.update_job_progress(job_id, 75.0, json_content.as_array().map_or(1, |arr| arr.len()) as u64)?;

        let content = serde_json::to_string_pretty(&json_content).map_err(|e| format!("JSON serialization error: {}", e))?;
        
        fs::write(&config.output_path, content).await.map_err(|e| format!("File write error: {}", e))?;
        
        self.update_job_progress(job_id, 100.0, json_content.as_array().map_or(1, |arr| arr.len()) as u64)?;
        
        Ok(())
    }

    async fn export_jsonl(&mut self, job_id: &str, config: &ExportConfig, data: &serde_json::Value) -> Result<(), String> {
        self.update_job_progress(job_id, 25.0, 0)?;
        
        let records = data.as_array().ok_or("Data must be an array for JSONL export")?;
        let mut lines = Vec::new();
        
        for (i, record) in records.iter().enumerate() {
            let line = serde_json::to_string(record).map_err(|e| format!("JSONL serialization error: {}", e))?;
            lines.push(line);
            
            if i % 100 == 0 {
                let progress = 25.0 + (i as f64 / records.len() as f64) * 50.0;
                self.update_job_progress(job_id, progress, i as u64)?;
            }
        }

        self.update_job_progress(job_id, 75.0, records.len() as u64)?;

        let content = lines.join("\n");
        fs::write(&config.output_path, content).await.map_err(|e| format!("File write error: {}", e))?;
        
        self.update_job_progress(job_id, 100.0, records.len() as u64)?;
        
        Ok(())
    }

    async fn export_csv(&mut self, job_id: &str, config: &ExportConfig, data: &serde_json::Value) -> Result<(), String> {
        self.update_job_progress(job_id, 25.0, 0)?;
        
        let records = data.as_array().ok_or("Data must be an array for CSV export")?;
        if records.is_empty() {
            return Err("No data to export".to_string());
        }

        // Get headers from first record
        let first_record = records[0].as_object().ok_or("Records must be objects for CSV export")?;
        let headers: Vec<String> = first_record.keys().cloned().collect();
        
        let mut csv_lines = vec![headers.join(",")];
        
        for (i, record) in records.iter().enumerate() {
            let record_obj = record.as_object().ok_or("All records must be objects for CSV export")?;
            let row: Vec<String> = headers.iter()
                .map(|h| record_obj.get(h).map_or("".to_string(), |v| {
                    match v {
                        serde_json::Value::String(s) => format!("\"{}\"", s.replace("\"", "\"\"")),
                        _ => v.to_string(),
                    }
                }))
                .collect();
            csv_lines.push(row.join(","));
            
            if i % 100 == 0 {
                let progress = 25.0 + (i as f64 / records.len() as f64) * 50.0;
                self.update_job_progress(job_id, progress, i as u64)?;
            }
        }

        self.update_job_progress(job_id, 75.0, records.len() as u64)?;

        let content = csv_lines.join("\n");
        fs::write(&config.output_path, content).await.map_err(|e| format!("File write error: {}", e))?;
        
        self.update_job_progress(job_id, 100.0, records.len() as u64)?;
        
        Ok(())
    }

    async fn export_parquet(&mut self, _job_id: &str, _config: &ExportConfig, _data: &serde_json::Value) -> Result<(), String> {
        // Parquet export would require additional dependencies
        Err("Parquet export not yet implemented - requires additional dependencies".to_string())
    }
}

#[command]
pub async fn get_export_jobs(export_manager: State<'_, Mutex<ExportManager>>) -> Result<Vec<ExportJob>, String> {
    let manager = export_manager.lock().await;
    Ok(manager.get_export_jobs())
}

#[command]
pub async fn create_export_job(
    config: ExportConfig,
    source_dataset_id: Option<String>,
    export_manager: State<'_, Mutex<ExportManager>>
) -> Result<String, String> {
    let mut manager = export_manager.lock().await;
    manager.create_export_job(config, source_dataset_id)
}

#[command]
pub async fn get_export_job(
    job_id: String,
    export_manager: State<'_, Mutex<ExportManager>>
) -> Result<Option<ExportJob>, String> {
    let manager = export_manager.lock().await;
    Ok(manager.get_export_job(&job_id))
}

#[command]
pub async fn start_export_job(
    job_id: String,
    source_data: serde_json::Value,
    export_manager: State<'_, Mutex<ExportManager>>
) -> Result<(), String> {
    let mut manager = export_manager.lock().await;
    manager.execute_export(&job_id, &source_data).await
}

#[command]
pub async fn cancel_export_job(
    job_id: String,
    export_manager: State<'_, Mutex<ExportManager>>
) -> Result<(), String> {
    let mut manager = export_manager.lock().await;
    manager.cancel_export_job(&job_id)
}

#[command]
pub async fn delete_export_job(
    job_id: String,
    export_manager: State<'_, Mutex<ExportManager>>
) -> Result<(), String> {
    let mut manager = export_manager.lock().await;
    manager.jobs.remove(&job_id);
    Ok(())
}
