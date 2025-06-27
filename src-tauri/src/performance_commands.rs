use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tauri::command;
use crate::performance_monitor::{PerformanceMonitor, PerformanceMetrics};
use crate::background_tasks::{BackgroundTaskSystem, BackgroundTask, TaskType, TaskPriority};

#[derive(Debug, Serialize, Deserialize)]
pub struct TaskSubmissionRequest {
    pub task_type: String,
    pub priority: String,
    pub metadata: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SystemOptimizationRequest {
    pub optimization_type: String, // "low_memory" | "performance" | "balanced"
}

// Performance Monitoring Commands

#[command]
pub async fn get_performance_metrics(
    monitor: tauri::State<'_, Arc<PerformanceMonitor>>,
) -> Result<PerformanceMetrics, String> {
    Ok(monitor.get_metrics().await)
}

#[command]
pub async fn get_resource_recommendation(
    monitor: tauri::State<'_, Arc<PerformanceMonitor>>,
) -> Result<String, String> {
    Ok(monitor.get_resource_usage_recommendation().await)
}

#[command]
pub async fn optimize_system_performance(
    monitor: tauri::State<'_, Arc<PerformanceMonitor>>,
    request: SystemOptimizationRequest,
) -> Result<String, String> {
    match request.optimization_type.as_str() {
        "low_memory" => {
            monitor.optimize_for_low_memory().await;
            Ok("System optimized for low memory usage".to_string())
        }
        "performance" => {
            monitor.optimize_for_performance().await;
            Ok("System optimized for maximum performance".to_string())
        }
        "balanced" => {
            // Default balanced settings
            Ok("System configured with balanced settings".to_string())
        }
        _ => Err("Invalid optimization type".to_string()),
    }
}

#[command]
pub async fn export_performance_metrics(
    monitor: tauri::State<'_, Arc<PerformanceMonitor>>,
) -> Result<String, String> {
    monitor.export_metrics().await
}

#[command]
pub async fn cleanup_performance_data(
    monitor: tauri::State<'_, Arc<PerformanceMonitor>>,
) -> Result<String, String> {
    monitor.cleanup_old_metrics().await;
    Ok("Performance data cleaned up successfully".to_string())
}

// Background Task Commands

#[command]
pub async fn submit_background_task(
    task_system: tauri::State<'_, Arc<BackgroundTaskSystem>>,
    request: TaskSubmissionRequest,
) -> Result<String, String> {
    let task_type = match request.task_type.as_str() {
        "web_scraping" => TaskType::WebScraping,
        "text_processing" => TaskType::TextProcessing,
        "chunk_generation" => TaskType::ChunkGeneration,
        "export" => TaskType::Export,
        "metadata_enrichment" => TaskType::MetadataEnrichment,
        "visual_asset_download" => TaskType::VisualAssetDownload,
        "cloud_sync" => TaskType::CloudSync,
        "backup" => TaskType::Backup,
        "quality_analysis" => TaskType::QualityAnalysis,
        "batch_processing" => TaskType::BatchProcessing,
        _ => return Err(format!("Invalid task type: {}", request.task_type)),
    };

    let priority = match request.priority.as_str() {
        "low" => TaskPriority::Low,
        "normal" => TaskPriority::Normal,
        "high" => TaskPriority::High,
        "critical" => TaskPriority::Critical,
        _ => TaskPriority::Normal,
    };

    task_system.submit_task(task_type, priority, request.metadata).await
}

#[command]
pub async fn cancel_background_task(
    task_system: tauri::State<'_, Arc<BackgroundTaskSystem>>,
    task_id: String,
) -> Result<String, String> {
    task_system.cancel_task(&task_id).await?;
    Ok(format!("Task {} has been cancelled", task_id))
}

#[command]
pub async fn get_task_status(
    task_system: tauri::State<'_, Arc<BackgroundTaskSystem>>,
    task_id: String,
) -> Result<Option<BackgroundTask>, String> {
    Ok(task_system.get_task_status(&task_id).await)
}

#[command]
pub async fn get_all_background_tasks(
    task_system: tauri::State<'_, Arc<BackgroundTaskSystem>>,
) -> Result<Vec<BackgroundTask>, String> {
    Ok(task_system.get_all_tasks().await)
}

#[command]
pub async fn get_active_background_tasks(
    task_system: tauri::State<'_, Arc<BackgroundTaskSystem>>,
) -> Result<Vec<BackgroundTask>, String> {
    Ok(task_system.get_active_tasks().await)
}

#[command]
pub async fn get_task_queue_length(
    task_system: tauri::State<'_, Arc<BackgroundTaskSystem>>,
) -> Result<usize, String> {
    Ok(task_system.get_queue_length().await)
}

#[command]
pub async fn get_background_system_stats(
    task_system: tauri::State<'_, Arc<BackgroundTaskSystem>>,
) -> Result<serde_json::Value, String> {
    Ok(task_system.get_system_stats().await)
}

// Combined Performance and Task Management Commands

#[command]
pub async fn get_system_health_summary(
    monitor: tauri::State<'_, Arc<PerformanceMonitor>>,
    task_system: tauri::State<'_, Arc<BackgroundTaskSystem>>,
) -> Result<serde_json::Value, String> {
    let performance_metrics = monitor.get_metrics().await;
    let active_tasks = task_system.get_active_tasks().await;
    let queue_length = task_system.get_queue_length().await;
    let system_stats = task_system.get_system_stats().await;
    let recommendation = monitor.get_resource_usage_recommendation().await;

    let health_status = if performance_metrics.cpu_usage > 90.0 || 
                          (performance_metrics.memory_usage as f64 / performance_metrics.memory_total as f64) > 0.9 {
        "critical"
    } else if performance_metrics.cpu_usage > 70.0 || 
              (performance_metrics.memory_usage as f64 / performance_metrics.memory_total as f64) > 0.75 {
        "warning"
    } else {
        "healthy"
    };

    Ok(serde_json::json!({
        "health_status": health_status,
        "performance": {
            "cpu_usage": performance_metrics.cpu_usage,
            "memory_usage_mb": performance_metrics.memory_usage / 1024 / 1024,
            "memory_total_mb": performance_metrics.memory_total / 1024 / 1024,
            "memory_usage_percent": (performance_metrics.memory_usage as f64 / performance_metrics.memory_total as f64) * 100.0,
            "uptime_seconds": performance_metrics.uptime.as_secs(),
            "average_task_duration_seconds": performance_metrics.average_task_duration.as_secs_f64()
        },
        "tasks": {
            "active_count": active_tasks.len(),
            "queue_length": queue_length,
            "statistics": system_stats
        },
        "recommendation": recommendation,
        "timestamp": chrono::Utc::now()
    }))
}

#[command]
pub async fn start_performance_monitoring(
    monitor: tauri::State<'_, Arc<PerformanceMonitor>>,
) -> Result<String, String> {
    monitor.start_monitoring().await;
    Ok("Performance monitoring started".to_string())
}

#[command]
pub async fn emergency_system_cleanup(
    monitor: tauri::State<'_, Arc<PerformanceMonitor>>,
    task_system: tauri::State<'_, Arc<BackgroundTaskSystem>>,
) -> Result<String, String> {
    // Cancel all non-critical tasks
    let active_tasks = task_system.get_active_tasks().await;
    let mut cancelled_count = 0;
    
    for task in active_tasks {
        if !matches!(task.priority, TaskPriority::Critical) {
            if task_system.cancel_task(&task.id).await.is_ok() {
                cancelled_count += 1;
            }
        }
    }

    // Optimize for low memory
    monitor.optimize_for_low_memory().await;
    
    // Cleanup old performance data
    monitor.cleanup_old_metrics().await;

    Ok(format!("Emergency cleanup completed: {} tasks cancelled, system optimized for low memory usage", cancelled_count))
}

// Task progress streaming support
#[command]
pub async fn subscribe_to_task_progress(
    _task_id: String,
) -> Result<String, String> {
    // In a real implementation, this would set up a WebSocket or event stream
    // For now, return a success message
    Ok("Task progress subscription activated".to_string())
}

#[command]
pub async fn get_performance_history(
    monitor: tauri::State<'_, Arc<PerformanceMonitor>>,
    duration_minutes: Option<u64>,
) -> Result<serde_json::Value, String> {
    let duration = duration_minutes.unwrap_or(60); // Default to last hour
    
    // In a real implementation, this would return historical performance data
    // For now, return current metrics with timestamp
    let current_metrics = monitor.get_metrics().await;
    
    Ok(serde_json::json!({
        "duration_minutes": duration,
        "current_metrics": current_metrics,
        "data_points": [], // Would contain historical data points
        "timestamp": chrono::Utc::now()
    }))
}

#[command]
pub async fn estimate_task_completion(
    task_system: tauri::State<'_, Arc<BackgroundTaskSystem>>,
    task_type: String,
) -> Result<serde_json::Value, String> {
    // Estimate completion time based on task type and current system load
    let queue_length = task_system.get_queue_length().await;
    let active_tasks = task_system.get_active_tasks().await.len();
    
    let base_duration_minutes = match task_type.as_str() {
        "web_scraping" => 3.0,
        "text_processing" => 2.0,
        "chunk_generation" => 1.5,
        "export" => 1.0,
        "metadata_enrichment" => 4.0,
        "visual_asset_download" => 2.5,
        "cloud_sync" => 3.5,
        "backup" => 5.0,
        "quality_analysis" => 2.0,
        "batch_processing" => 8.0,
        _ => 3.0,
    };
    
    // Adjust for system load
    let load_multiplier = 1.0 + (queue_length as f64 * 0.1) + (active_tasks as f64 * 0.2);
    let estimated_minutes = base_duration_minutes * load_multiplier;
    
    Ok(serde_json::json!({
        "task_type": task_type,
        "estimated_duration_minutes": estimated_minutes,
        "queue_position": queue_length + 1,
        "factors": {
            "base_duration_minutes": base_duration_minutes,
            "queue_length": queue_length,
            "active_tasks": active_tasks,
            "load_multiplier": load_multiplier
        }
    }))
}
