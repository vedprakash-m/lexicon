use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use tauri::{command, State};
use tokio::sync::{RwLock, Mutex};
use uuid::Uuid;

use crate::python_manager::PythonManager;
use crate::background_tasks::{BackgroundTaskSystem, BackgroundTask, TaskType, TaskPriority};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchJobConfig {
    pub name: String,
    pub description: String,
    pub priority: String, // "low", "normal", "high", "urgent"
    pub sources: Vec<String>,
    pub parallel_sources: Option<bool>,
    pub parallel_pages: Option<bool>,
    pub chunk_size: Option<i32>,
    pub max_retries: Option<i32>,
    pub output_format: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchJob {
    pub id: String,
    pub name: String,
    pub description: String,
    pub priority: String,
    pub status: String,
    #[serde(rename = "sourceCount")]
    pub source_count: i32,
    #[serde(rename = "completedSources")]
    pub completed_sources: i32,
    #[serde(rename = "totalPages")]
    pub total_pages: i32,
    #[serde(rename = "processedPages")]
    pub processed_pages: i32,
    #[serde(rename = "startTime")]
    pub start_time: Option<String>,
    #[serde(rename = "endTime")]
    pub end_time: Option<String>,
    #[serde(rename = "estimatedDuration")]
    pub estimated_duration: Option<i32>,
    #[serde(rename = "parallelSources")]
    pub parallel_sources: bool,
    #[serde(rename = "parallelPages")]
    pub parallel_pages: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceUsage {
    #[serde(rename = "cpuPercent")]
    pub cpu_percent: f64,
    #[serde(rename = "memoryPercent")]
    pub memory_percent: f64,
    #[serde(rename = "memoryMb")]
    pub memory_mb: f64,
    #[serde(rename = "activeProcesses")]
    pub active_processes: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemStatus {
    #[serde(rename = "processorRunning")]
    pub processor_running: bool,
    #[serde(rename = "resourceUsage")]
    pub resource_usage: ResourceUsage,
    #[serde(rename = "resourceLimits")]
    pub resource_limits: HashMap<String, i32>,
    #[serde(rename = "queueStatus")]
    pub queue_status: HashMap<String, i32>,
    #[serde(rename = "shouldThrottle")]
    pub should_throttle: bool,
}

pub struct BatchProcessingState {
    pub jobs: Arc<RwLock<HashMap<String, BatchJob>>>,
    pub python_manager: Arc<Mutex<PythonManager>>,
    pub background_tasks: Arc<BackgroundTaskSystem>,
}

impl BatchProcessingState {
    pub fn new(python_manager: Arc<Mutex<PythonManager>>, background_tasks: Arc<BackgroundTaskSystem>) -> Self {
        Self {
            jobs: Arc::new(RwLock::new(HashMap::new())),
            python_manager,
            background_tasks,
        }
    }
}

/// Get all batch jobs
#[command]
pub async fn get_all_batch_jobs(
    state: State<'_, BatchProcessingState>,
) -> Result<Vec<BatchJob>, String> {
    let jobs = state.jobs.read().await;
    Ok(jobs.values().cloned().collect())
}

/// Get batch system status
#[command]
pub async fn get_batch_system_status(
    python_manager: State<'_, Arc<tokio::sync::Mutex<PythonManager>>>,
) -> Result<SystemStatus, String> {
    let python_manager_guard = python_manager.lock().await;
    
    let status_result = python_manager_guard
        .execute_code(
            r#"
import psutil
import json

def get_batch_system_status():
    try:
        # Get resource usage
        cpu_percent = psutil.cpu_percent(interval=1.0)
        memory = psutil.virtual_memory()
        
        resource_usage = {
            "cpuPercent": cpu_percent,
            "memoryPercent": memory.percent,
            "memoryMb": memory.used / (1024 * 1024),
            "activeProcesses": len(psutil.pids())
        }
        
        # Get resource limits (from system capabilities)
        cpu_count = psutil.cpu_count()
        total_memory_mb = memory.total / (1024 * 1024)
        
        resource_limits = {
            "maxCpuCores": max(1, cpu_count - 1),
            "maxMemoryMb": int(total_memory_mb * 0.8),
            "maxConcurrentJobs": 4
        }
        
        # Mock queue status (would come from actual batch processor)
        queue_status = {
            "queuedJobs": 0,
            "activeJobs": 0,
            "completedJobs": 0
        }
        
        return {
            "processorRunning": True,
            "resourceUsage": resource_usage,
            "resourceLimits": resource_limits,
            "queueStatus": queue_status,
            "shouldThrottle": cpu_percent > 80.0 or memory.percent > 85.0
        }
    except Exception as e:
        return {"error": str(e)}

result = get_batch_system_status()
print(json.dumps(result))
"#)
        .await
        .map_err(|e| format!("Failed to get batch system status: {}", e))?;

    // Parse the JSON response
    let status: SystemStatus = serde_json::from_str(&status_result.stdout)
        .map_err(|e| format!("Failed to parse batch system status: {}", e))?;
    
    Ok(status)
}

/// Create a new batch job
#[command]
pub async fn create_batch_job(
    job_data: BatchJobConfig,
    state: State<'_, BatchProcessingState>,
) -> Result<String, String> {
    let job_id = Uuid::new_v4().to_string();
    
    // Convert priority string to TaskPriority
    let priority = match job_data.priority.as_str() {
        "urgent" => TaskPriority::Critical,
        "high" => TaskPriority::High,
        "normal" => TaskPriority::Normal,
        "low" => TaskPriority::Low,
        _ => TaskPriority::Normal,
    };

    // Create batch job entry
    let batch_job = BatchJob {
        id: job_id.clone(),
        name: job_data.name.clone(),
        description: job_data.description.clone(),
        priority: job_data.priority.clone(),
        status: "pending".to_string(),
        source_count: job_data.sources.len() as i32,
        completed_sources: 0,
        total_pages: 0,
        processed_pages: 0,
        start_time: None,
        end_time: None,
        estimated_duration: None,
        parallel_sources: job_data.parallel_sources.unwrap_or(true),
        parallel_pages: job_data.parallel_pages.unwrap_or(false),
    };

    // Store the job
    {
        let mut jobs = state.jobs.write().await;
        jobs.insert(job_id.clone(), batch_job);
    }

    // Submit to background task system
    state.background_tasks.submit_task(
        TaskType::BatchProcessing,
        priority,
        serde_json::json!({
            "batch_job_config": job_data,
            "source_count": job_data.sources.len()
        })
    ).await
        .map_err(|e| format!("Failed to submit batch job: {}", e))?;

    // Clone necessary data for the async task
    let job_id_clone = job_id.clone();
    let job_id_for_error = job_id.clone();
    let python_manager_clone = state.python_manager.clone();
    let jobs_clone = state.jobs.clone();

    // Start real batch processing using Python
    tokio::spawn(async move {
        if let Err(e) = execute_batch_job(job_id_clone, job_data, python_manager_clone, jobs_clone).await {
            log::error!("Batch job {} failed: {}", job_id_for_error, e);
        }
    });

    Ok(job_id)
}

/// Execute the actual batch job using Python batch processor
async fn execute_batch_job(
    job_id: String,
    job_config: BatchJobConfig,
    python_manager: Arc<tokio::sync::Mutex<PythonManager>>,
    jobs: Arc<RwLock<HashMap<String, BatchJob>>>,
) -> Result<(), String> {
    // Update job status to running
    {
        let mut jobs_guard = jobs.write().await;
        if let Some(job) = jobs_guard.get_mut(&job_id) {
            job.status = "running".to_string();
            job.start_time = Some(chrono::Utc::now().to_rfc3339());
        }
    }

    // Create Python script to execute batch processing
    let script = format!(
        r#"
import sys
import json
import time
from pathlib import Path

# Add the processors directory to the path
sys.path.append(str(Path(__file__).parent / "processors"))

from batch_processor import BatchProcessor, BatchJobConfig, JobPriority, ResourceLimits

def execute_batch_job():
    try:
        # Parse job configuration
        job_config_data = {{}}
        job_config_data["name"] = "{}"
        job_config_data["description"] = "{}"
        job_config_data["priority"] = "{}"
        job_config_data["sources"] = {}
        job_config_data["parallel_sources"] = {}
        job_config_data["parallel_pages"] = {}
        
        # Map priority string to enum
        priority_map = {{
            "urgent": JobPriority.URGENT,
            "high": JobPriority.HIGH,
            "normal": JobPriority.NORMAL,
            "low": JobPriority.LOW
        }}
        priority = priority_map.get(job_config_data["priority"], JobPriority.NORMAL)
        
        # Create batch job configuration
        batch_config = BatchJobConfig(
            name=job_config_data["name"],
            description=job_config_data["description"],
            priority=priority,
            source_ids=job_config_data["sources"],
            parallel_sources=job_config_data["parallel_sources"],
            parallel_pages=job_config_data["parallel_pages"]
        )
        
        # Create resource limits
        limits = ResourceLimits(
            max_concurrent_jobs=2,
            max_cpu_cores=4,
            max_memory_mb=2048
        )
        
        # Create and start batch processor
        processor = BatchProcessor(limits)
        processor.start()
        
        try:
            # Submit the job
            job_id = processor.submit_job(batch_config)
            
            # Monitor job progress
            for i in range(30):  # Monitor for up to 30 seconds
                status = processor.get_job_status(job_id)
                if status:
                    print(f"Job status: {{status}}")
                    if status.get("status") in ["completed", "failed", "cancelled"]:
                        break
                time.sleep(1)
            
            return {{"status": "completed", "job_id": job_id}}
        
        finally:
            processor.stop()
            
    except Exception as e:
        return {{"error": str(e)}}

result = execute_batch_job()
print(json.dumps(result))
"#,
        job_config.name,
        job_config.description,
        job_config.priority,
        serde_json::to_string(&job_config.sources).unwrap_or_else(|_| "[]".to_string()),
        job_config.parallel_sources.unwrap_or(true),
        job_config.parallel_pages.unwrap_or(false)
    );

    let python_manager_guard = python_manager.lock().await;
    let result = python_manager_guard
        .execute_code(&script)
        .await
        .map_err(|e| format!("Failed to execute batch job: {}", e))?;

    // Parse result and update job status
    if let Ok(job_result) = serde_json::from_str::<serde_json::Value>(&result.stdout) {
        let mut jobs_guard = jobs.write().await;
        if let Some(job) = jobs_guard.get_mut(&job_id) {
            if job_result.get("error").is_some() {
                job.status = "failed".to_string();
            } else {
                job.status = "completed".to_string();
                job.completed_sources = job.source_count;
                job.processed_pages = job.total_pages; // Would be updated with real counts
            }
            job.end_time = Some(chrono::Utc::now().to_rfc3339());
        }
    }

    Ok(())
}

/// Pause a batch job
#[command]
pub async fn pause_batch_job(
    job_id: String,
    state: State<'_, BatchProcessingState>,
) -> Result<(), String> {
    let mut jobs = state.jobs.write().await;
    if let Some(job) = jobs.get_mut(&job_id) {
        if job.status == "running" {
            job.status = "paused".to_string();
            log::info!("Paused batch job: {}", job_id);
        } else {
            return Err("Job is not running".to_string());
        }
    } else {
        return Err("Job not found".to_string());
    }
    Ok(())
}

/// Resume a batch job
#[command]
pub async fn resume_batch_job(
    job_id: String,
    state: State<'_, BatchProcessingState>,
) -> Result<(), String> {
    let mut jobs = state.jobs.write().await;
    if let Some(job) = jobs.get_mut(&job_id) {
        if job.status == "paused" {
            job.status = "running".to_string();
            log::info!("Resumed batch job: {}", job_id);
        } else {
            return Err("Job is not paused".to_string());
        }
    } else {
        return Err("Job not found".to_string());
    }
    Ok(())
}

/// Cancel a batch job
#[command]
pub async fn cancel_batch_job(
    job_id: String,
    state: State<'_, BatchProcessingState>,
) -> Result<(), String> {
    let mut jobs = state.jobs.write().await;
    if let Some(job) = jobs.get_mut(&job_id) {
        if !matches!(job.status.as_str(), "completed" | "failed" | "cancelled") {
            job.status = "cancelled".to_string();
            job.end_time = Some(chrono::Utc::now().to_rfc3339());
            log::info!("Cancelled batch job: {}", job_id);
        } else {
            return Err("Job cannot be cancelled in current state".to_string());
        }
    } else {
        return Err("Job not found".to_string());
    }
    Ok(())
}

/// Delete a batch job
#[command]
pub async fn delete_batch_job(
    job_id: String,
    state: State<'_, BatchProcessingState>,
) -> Result<(), String> {
    let mut jobs = state.jobs.write().await;
    if jobs.remove(&job_id).is_some() {
        log::info!("Deleted batch job: {}", job_id);
        Ok(())
    } else {
        Err("Job not found".to_string())
    }
}

/// Export batch job results
#[command]
pub async fn export_batch_results(
    job_id: String,
    format: String,
    state: State<'_, BatchProcessingState>,
) -> Result<String, String> {
    let jobs = state.jobs.read().await;
    if let Some(job) = jobs.get(&job_id) {
        if job.status != "completed" {
            return Err("Job has not completed successfully".to_string());
        }

        // Create export script
        let script = format!(
            r#"
import json
from pathlib import Path

def export_batch_results():
    try:
        # Mock export functionality - would export actual results
        export_path = Path("/tmp") / f"batch_export_{}_{}.{}"
        
        # Create sample export data
        export_data = {{
            "job_id": "{}",
            "job_name": "{}",
            "export_format": "{}",
            "exported_at": "{}",
            "total_sources": {},
            "total_pages": {},
            "status": "exported"
        }}
        
        # Write to file based on format
        if "{}" == "json":
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
        else:
            # Handle other formats (CSV, JSONL, etc.)
            with open(export_path, 'w') as f:
                f.write(str(export_data))
        
        return {{"export_path": str(export_path), "status": "success"}}
    except Exception as e:
        return {{"error": str(e)}}

result = export_batch_results()
print(json.dumps(result))
"#,
            job_id,
            format,
            format,
            job_id,
            job.name,
            format,
            chrono::Utc::now().to_rfc3339(),
            job.source_count,
            job.total_pages,
            format
        );

        let python_manager_guard = state.python_manager.lock().await;
        let result = python_manager_guard
            .execute_code(&script)
            .await
            .map_err(|e| format!("Failed to export batch results: {}", e))?;

        // Parse result to get export path
        if let Ok(export_result) = serde_json::from_str::<serde_json::Value>(&result.stdout) {
            if let Some(export_path) = export_result.get("export_path") {
                Ok(export_path.as_str().unwrap_or("").to_string())
            } else {
                Err("Export failed".to_string())
            }
        } else {
            Err("Failed to parse export result".to_string())
        }
    } else {
        Err("Job not found".to_string())
    }
}
