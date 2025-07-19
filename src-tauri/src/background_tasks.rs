use std::collections::HashMap;
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::{Mutex, RwLock, mpsc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use log::{debug, info, warn, error};

use crate::performance_monitor::{PerformanceMonitor, TaskStatus};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackgroundTask {
    pub id: String,
    pub task_type: TaskType,
    pub priority: TaskPriority,
    pub status: TaskStatus,
    pub progress: f64,
    pub message: String,
    pub created_at: chrono::DateTime<chrono::Utc>,
    pub started_at: Option<chrono::DateTime<chrono::Utc>>,
    pub completed_at: Option<chrono::DateTime<chrono::Utc>>,
    pub error_message: Option<String>,
    pub metadata: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TaskType {
    WebScraping,
    TextProcessing,
    ChunkGeneration,
    Export,
    MetadataEnrichment,
    VisualAssetDownload,
    CloudSync,
    Backup,
    QualityAnalysis,
    BatchProcessing,
    AdvancedChunking,
    QualityAssessment,
    RelationshipExtraction,
    PythonPackageInstall,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub enum TaskPriority {
    Low = 1,
    Normal = 2,
    High = 3,
    Critical = 4,
}

#[derive(Debug, Clone)]
pub struct TaskProgress {
    pub task_id: String,
    pub progress: f64,
    pub message: String,
    pub metadata: Option<serde_json::Value>,
}

#[derive(Debug, Clone)]
pub enum TaskCommand {
    Start(BackgroundTask),
    Cancel(String),
    UpdateProgress(TaskProgress),
    Pause(String),
    Resume(String),
    GetStatus(String),
}

pub struct BackgroundTaskSystem {
    tasks: Arc<RwLock<HashMap<String, BackgroundTask>>>,
    task_queue: Arc<Mutex<Vec<BackgroundTask>>>,
    active_workers: Arc<RwLock<u32>>,
    max_workers: u32,
    performance_monitor: Arc<PerformanceMonitor>,
    command_sender: mpsc::UnboundedSender<TaskCommand>,
    progress_sender: mpsc::UnboundedSender<TaskProgress>,
    shutdown_signal: Arc<tokio::sync::Notify>,
}

impl BackgroundTaskSystem {
    pub fn new(max_workers: u32, performance_monitor: Arc<PerformanceMonitor>) -> Self {
        let (command_sender, command_receiver) = mpsc::unbounded_channel();
        let (progress_sender, progress_receiver) = mpsc::unbounded_channel();
        
        let system = Self {
            tasks: Arc::new(RwLock::new(HashMap::new())),
            task_queue: Arc::new(Mutex::new(Vec::new())),
            active_workers: Arc::new(RwLock::new(0)),
            max_workers,
            performance_monitor,
            command_sender,
            progress_sender,
            shutdown_signal: Arc::new(tokio::sync::Notify::new()),
        };

        // Start the command processor
        system.start_command_processor(command_receiver);
        // Start the progress processor
        system.start_progress_processor(progress_receiver);
        // Start the task scheduler
        system.start_task_scheduler();

        system
    }

    pub async fn submit_task(&self, task_type: TaskType, priority: TaskPriority, metadata: serde_json::Value) -> Result<String, String> {
        let task_id = Uuid::new_v4().to_string();
        
        let task = BackgroundTask {
            id: task_id.clone(),
            task_type: task_type.clone(),
            priority: priority.clone(),
            status: TaskStatus::Running,
            progress: 0.0,
            message: "Task queued".to_string(),
            created_at: chrono::Utc::now(),
            started_at: None,
            completed_at: None,
            error_message: None,
            metadata,
        };

        // Add to queue
        {
            let mut queue = self.task_queue.lock().await;
            queue.push(task.clone());
            queue.sort_by(|a, b| b.priority.cmp(&a.priority)); // Higher priority first
        }

        // Add to tasks registry
        self.tasks.write().await.insert(task_id.clone(), task);

        info!("Task submitted: {} (type: {:?}, priority: {:?})", task_id, task_type, priority);
        Ok(task_id)
    }

    pub async fn cancel_task(&self, task_id: &str) -> Result<(), String> {
        self.command_sender
            .send(TaskCommand::Cancel(task_id.to_string()))
            .map_err(|e| format!("Failed to send cancel command: {}", e))?;
        Ok(())
    }

    pub async fn get_task_status(&self, task_id: &str) -> Option<BackgroundTask> {
        self.tasks.read().await.get(task_id).cloned()
    }

    pub async fn get_all_tasks(&self) -> Vec<BackgroundTask> {
        self.tasks.read().await.values().cloned().collect()
    }

    pub async fn get_active_tasks(&self) -> Vec<BackgroundTask> {
        self.tasks
            .read()
            .await
            .values()
            .filter(|task| matches!(task.status, TaskStatus::Running))
            .cloned()
            .collect()
    }

    pub async fn get_queue_length(&self) -> usize {
        self.task_queue.lock().await.len()
    }

    pub async fn update_progress(&self, task_id: String, progress: f64, message: String) {
        let progress_update = TaskProgress {
            task_id,
            progress: progress.clamp(0.0, 100.0),
            message,
            metadata: None,
        };

        if let Err(e) = self.progress_sender.send(progress_update) {
            warn!("Failed to send progress update: {}", e);
        }
    }

    fn start_command_processor(&self, mut receiver: mpsc::UnboundedReceiver<TaskCommand>) {
        let tasks = Arc::clone(&self.tasks);
        let performance_monitor = Arc::clone(&self.performance_monitor);

        tokio::spawn(async move {
            while let Some(command) = receiver.recv().await {
                match command {
                    TaskCommand::Cancel(task_id) => {
                        if let Some(mut task) = tasks.write().await.get_mut(&task_id) {
                            task.status = TaskStatus::Cancelled;
                            task.completed_at = Some(chrono::Utc::now());
                            performance_monitor.cancel_task(&task_id).await;
                            info!("Task cancelled: {}", task_id);
                        }
                    }
                    TaskCommand::Pause(task_id) => {
                        if let Some(mut task) = tasks.write().await.get_mut(&task_id) {
                            task.message = "Task paused".to_string();
                            info!("Task paused: {}", task_id);
                        }
                    }
                    TaskCommand::Resume(task_id) => {
                        if let Some(mut task) = tasks.write().await.get_mut(&task_id) {
                            task.message = "Task resumed".to_string();
                            info!("Task resumed: {}", task_id);
                        }
                    }
                    _ => {
                        debug!("Processed command: {:?}", command);
                    }
                }
            }
        });
    }

    fn start_progress_processor(&self, mut receiver: mpsc::UnboundedReceiver<TaskProgress>) {
        let tasks = Arc::clone(&self.tasks);

        tokio::spawn(async move {
            while let Some(progress) = receiver.recv().await {
                if let Some(mut task) = tasks.write().await.get_mut(&progress.task_id) {
                    task.progress = progress.progress;
                    task.message = progress.message;
                    
                    if let Some(metadata) = progress.metadata {
                        task.metadata = metadata;
                    }

                    debug!("Progress updated for task {}: {:.1}% - {}", 
                           progress.task_id, progress.progress, task.message);
                }
            }
        });
    }

    fn start_task_scheduler(&self) {
        let tasks = Arc::clone(&self.tasks);
        let task_queue = Arc::clone(&self.task_queue);
        let active_workers = Arc::clone(&self.active_workers);
        let performance_monitor = Arc::clone(&self.performance_monitor);
        let progress_sender = self.progress_sender.clone();
        let max_workers = self.max_workers;
        let shutdown_signal = Arc::clone(&self.shutdown_signal);

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(1));
            
            loop {
                tokio::select! {
                    _ = interval.tick() => {
                        // Check if we can start new tasks
                        let current_workers = *active_workers.read().await;
                        
                        if current_workers < max_workers {
                            let mut queue = task_queue.lock().await;
                            
                            if let Some(mut task) = queue.pop() {
                                // Start the task
                                task.status = TaskStatus::Running;
                                task.started_at = Some(chrono::Utc::now());
                                
                                let task_id = task.id.clone();
                                let task_type_str = format!("{:?}", task.task_type);
                                
                                // Update tasks registry
                                tasks.write().await.insert(task_id.clone(), task.clone());
                                
                                // Increment active workers
                                *active_workers.write().await += 1;
                                
                                // Start performance monitoring for this task
                                if let Err(e) = performance_monitor.start_task(task_id.clone(), task_type_str).await {
                                    error!("Failed to start performance monitoring for task {}: {}", task_id, e);
                                }
                                
                                // Spawn the actual task execution
                                Self::execute_task(
                                    task,
                                    Arc::clone(&tasks),
                                    Arc::clone(&active_workers),
                                    Arc::clone(&performance_monitor),
                                    progress_sender.clone(),
                                ).await;
                            }
                        }
                    }
                    _ = shutdown_signal.notified() => {
                        info!("Task scheduler shutting down");
                        break;
                    }
                }
            }
        });
    }

    async fn execute_task(
        mut task: BackgroundTask,
        tasks: Arc<RwLock<HashMap<String, BackgroundTask>>>,
        active_workers: Arc<RwLock<u32>>,
        performance_monitor: Arc<PerformanceMonitor>,
        progress_sender: mpsc::UnboundedSender<TaskProgress>,
    ) {
        let task_id = task.id.clone();
        let task_type = task.task_type.clone();
        
        tokio::spawn(async move {
            info!("Starting execution of task: {} ({:?})", task_id, task_type);
            
            let result = Self::run_task_logic(&mut task, &progress_sender).await;
            
            // Update task completion status
            {
                let mut tasks_guard = tasks.write().await;
                if let Some(task_entry) = tasks_guard.get_mut(&task_id) {
                    match result {
                        Ok(_) => {
                            task_entry.status = TaskStatus::Completed;
                            task_entry.progress = 100.0;
                            task_entry.message = "Task completed successfully".to_string();
                        }
                        Err(ref error) => {
                            task_entry.status = TaskStatus::Failed;
                            task_entry.message = "Task failed".to_string();
                            task_entry.error_message = Some(error.clone());
                        }
                    }
                    task_entry.completed_at = Some(chrono::Utc::now());
                }
            }
            
            // Complete performance monitoring
            performance_monitor.complete_task(&task_id, result.is_ok()).await;
            
            // Decrement active workers
            *active_workers.write().await -= 1;
            
            match result {
                Ok(_) => info!("Task completed successfully: {}", task_id),
                Err(e) => error!("Task failed: {} - {}", task_id, e),
            }
        });
    }

    async fn run_task_logic(
        task: &mut BackgroundTask,
        progress_sender: &mpsc::UnboundedSender<TaskProgress>,
    ) -> Result<(), String> {
        let task_id = task.id.clone();
        
        // Send initial progress
        let _ = progress_sender.send(TaskProgress {
            task_id: task_id.clone(),
            progress: 0.0,
            message: "Initializing task".to_string(),
            metadata: None,
        });

        // Simulate task execution based on type
        match &task.task_type {
            TaskType::WebScraping => {
                Self::simulate_web_scraping(&task_id, progress_sender).await
            }
            TaskType::TextProcessing => {
                Self::simulate_text_processing(&task_id, progress_sender).await
            }
            TaskType::ChunkGeneration => {
                Self::simulate_chunk_generation(&task_id, progress_sender).await
            }
            TaskType::Export => {
                Self::simulate_export(&task_id, progress_sender).await
            }
            TaskType::MetadataEnrichment => {
                Self::simulate_metadata_enrichment(&task_id, progress_sender).await
            }
            TaskType::VisualAssetDownload => {
                Self::simulate_visual_asset_download(&task_id, progress_sender).await
            }
            TaskType::CloudSync => {
                Self::simulate_cloud_sync(&task_id, progress_sender).await
            }
            TaskType::Backup => {
                Self::simulate_backup(&task_id, progress_sender).await
            }
            TaskType::QualityAnalysis => {
                Self::simulate_quality_analysis(&task_id, progress_sender).await
            }
            TaskType::BatchProcessing => {
                Self::simulate_batch_processing(&task_id, progress_sender).await
            }
            TaskType::AdvancedChunking => {
                Self::simulate_advanced_chunking(&task_id, progress_sender).await
            }
            TaskType::QualityAssessment => {
                Self::simulate_quality_assessment(&task_id, progress_sender).await
            }
            TaskType::RelationshipExtraction => {
                Self::simulate_relationship_extraction(&task_id, progress_sender).await
            }
            TaskType::PythonPackageInstall => {
                Self::simulate_python_package_install(&task_id, progress_sender).await
            }
        }
    }

    // Simulation methods for different task types
    async fn simulate_web_scraping(
        task_id: &str,
        progress_sender: &mpsc::UnboundedSender<TaskProgress>,
    ) -> Result<(), String> {
        let steps = vec![
            (10.0, "Connecting to source"),
            (25.0, "Downloading content"),
            (50.0, "Parsing HTML structure"),
            (75.0, "Extracting text content"),
            (100.0, "Scraping completed"),
        ];

        for (progress, message) in steps {
            let _ = progress_sender.send(TaskProgress {
                task_id: task_id.to_string(),
                progress,
                message: message.to_string(),
                metadata: None,
            });
            
            tokio::time::sleep(Duration::from_millis(500)).await;
        }

        Ok(())
    }

    async fn simulate_text_processing(
        task_id: &str,
        progress_sender: &mpsc::UnboundedSender<TaskProgress>,
    ) -> Result<(), String> {
        let steps = vec![
            (15.0, "Analyzing text structure"),
            (35.0, "Cleaning text content"),
            (60.0, "Normalizing formatting"),
            (85.0, "Validating quality"),
            (100.0, "Text processing completed"),
        ];

        for (progress, message) in steps {
            let _ = progress_sender.send(TaskProgress {
                task_id: task_id.to_string(),
                progress,
                message: message.to_string(),
                metadata: None,
            });
            
            tokio::time::sleep(Duration::from_millis(400)).await;
        }

        Ok(())
    }

    async fn simulate_chunk_generation(
        task_id: &str,
        progress_sender: &mpsc::UnboundedSender<TaskProgress>,
    ) -> Result<(), String> {
        let steps = vec![
            (20.0, "Analyzing content boundaries"),
            (40.0, "Applying chunking strategy"),
            (70.0, "Generating chunks"),
            (90.0, "Validating chunk quality"),
            (100.0, "Chunking completed"),
        ];

        for (progress, message) in steps {
            let _ = progress_sender.send(TaskProgress {
                task_id: task_id.to_string(),
                progress,
                message: message.to_string(),
                metadata: None,
            });
            
            tokio::time::sleep(Duration::from_millis(300)).await;
        }

        Ok(())
    }

    async fn simulate_export(
        task_id: &str,
        progress_sender: &mpsc::UnboundedSender<TaskProgress>,
    ) -> Result<(), String> {
        let steps = vec![
            (25.0, "Preparing export data"),
            (50.0, "Formatting output"),
            (75.0, "Writing files"),
            (100.0, "Export completed"),
        ];

        for (progress, message) in steps {
            let _ = progress_sender.send(TaskProgress {
                task_id: task_id.to_string(),
                progress,
                message: message.to_string(),
                metadata: None,
            });
            
            tokio::time::sleep(Duration::from_millis(250)).await;
        }

        Ok(())
    }

    async fn simulate_metadata_enrichment(
        task_id: &str,
        progress_sender: &mpsc::UnboundedSender<TaskProgress>,
    ) -> Result<(), String> {
        let steps = vec![
            (20.0, "Querying external APIs"),
            (45.0, "Processing metadata"),
            (70.0, "Enriching book information"),
            (90.0, "Validating enrichments"),
            (100.0, "Metadata enrichment completed"),
        ];

        for (progress, message) in steps {
            let _ = progress_sender.send(TaskProgress {
                task_id: task_id.to_string(),
                progress,
                message: message.to_string(),
                metadata: None,
            });
            
            tokio::time::sleep(Duration::from_millis(600)).await;
        }

        Ok(())
    }

    async fn simulate_visual_asset_download(
        task_id: &str,
        progress_sender: &mpsc::UnboundedSender<TaskProgress>,
    ) -> Result<(), String> {
        let steps = vec![
            (30.0, "Downloading cover images"),
            (60.0, "Processing images"),
            (85.0, "Caching assets"),
            (100.0, "Visual assets ready"),
        ];

        for (progress, message) in steps {
            let _ = progress_sender.send(TaskProgress {
                task_id: task_id.to_string(),
                progress,
                message: message.to_string(),
                metadata: None,
            });
            
            tokio::time::sleep(Duration::from_millis(400)).await;
        }

        Ok(())
    }

    async fn simulate_cloud_sync(
        task_id: &str,
        progress_sender: &mpsc::UnboundedSender<TaskProgress>,
    ) -> Result<(), String> {
        let steps = vec![
            (25.0, "Connecting to cloud storage"),
            (50.0, "Uploading changes"),
            (75.0, "Syncing metadata"),
            (100.0, "Sync completed"),
        ];

        for (progress, message) in steps {
            let _ = progress_sender.send(TaskProgress {
                task_id: task_id.to_string(),
                progress,
                message: message.to_string(),
                metadata: None,
            });
            
            tokio::time::sleep(Duration::from_millis(800)).await;
        }

        Ok(())
    }

    async fn simulate_backup(
        task_id: &str,
        progress_sender: &mpsc::UnboundedSender<TaskProgress>,
    ) -> Result<(), String> {
        let steps = vec![
            (20.0, "Preparing backup"),
            (40.0, "Compressing data"),
            (70.0, "Creating archive"),
            (90.0, "Verifying backup"),
            (100.0, "Backup completed"),
        ];

        for (progress, message) in steps {
            let _ = progress_sender.send(TaskProgress {
                task_id: task_id.to_string(),
                progress,
                message: message.to_string(),
                metadata: None,
            });
            
            tokio::time::sleep(Duration::from_millis(500)).await;
        }

        Ok(())
    }

    async fn simulate_quality_analysis(
        task_id: &str,
        progress_sender: &mpsc::UnboundedSender<TaskProgress>,
    ) -> Result<(), String> {
        let steps = vec![
            (30.0, "Analyzing content quality"),
            (60.0, "Checking completeness"),
            (85.0, "Generating quality report"),
            (100.0, "Quality analysis completed"),
        ];

        for (progress, message) in steps {
            let _ = progress_sender.send(TaskProgress {
                task_id: task_id.to_string(),
                progress,
                message: message.to_string(),
                metadata: None,
            });
            
            tokio::time::sleep(Duration::from_millis(350)).await;
        }

        Ok(())
    }

    async fn simulate_batch_processing(
        task_id: &str,
        progress_sender: &mpsc::UnboundedSender<TaskProgress>,
    ) -> Result<(), String> {
        let steps = vec![
            (10.0, "Initializing batch"),
            (25.0, "Processing items 1-10"),
            (45.0, "Processing items 11-20"),
            (65.0, "Processing items 21-30"),
            (85.0, "Finalizing batch"),
            (100.0, "Batch processing completed"),
        ];

        for (progress, message) in steps {
            let _ = progress_sender.send(TaskProgress {
                task_id: task_id.to_string(),
                progress,
                message: message.to_string(),
                metadata: None,
            });
            
            tokio::time::sleep(Duration::from_millis(700)).await;
        }

        Ok(())
    }

    async fn simulate_advanced_chunking(
        task_id: &str,
        progress_sender: &mpsc::UnboundedSender<TaskProgress>,
    ) -> Result<(), String> {
        let steps = vec![
            (15.0, "Initializing advanced chunking"),
            (30.0, "Analyzing text structure"),
            (50.0, "Applying chunking strategies"),
            (75.0, "Optimizing chunk boundaries"),
            (90.0, "Validating chunks"),
            (100.0, "Advanced chunking completed"),
        ];

        for (progress, message) in steps {
            let _ = progress_sender.send(TaskProgress {
                task_id: task_id.to_string(),
                progress,
                message: message.to_string(),
                metadata: None,
            });
            
            tokio::time::sleep(Duration::from_millis(600)).await;
        }

        Ok(())
    }

    async fn simulate_quality_assessment(
        task_id: &str,
        progress_sender: &mpsc::UnboundedSender<TaskProgress>,
    ) -> Result<(), String> {
        let steps = vec![
            (20.0, "Loading ML models"),
            (40.0, "Analyzing text quality"),
            (60.0, "Computing readability scores"),
            (80.0, "Assessing coherence"),
            (95.0, "Generating quality report"),
            (100.0, "Quality assessment completed"),
        ];

        for (progress, message) in steps {
            let _ = progress_sender.send(TaskProgress {
                task_id: task_id.to_string(),
                progress,
                message: message.to_string(),
                metadata: None,
            });
            
            tokio::time::sleep(Duration::from_millis(800)).await;
        }

        Ok(())
    }

    async fn simulate_relationship_extraction(
        task_id: &str,
        progress_sender: &mpsc::UnboundedSender<TaskProgress>,
    ) -> Result<(), String> {
        let steps = vec![
            (10.0, "Initializing relationship extraction"),
            (25.0, "Computing semantic embeddings"),
            (45.0, "Analyzing chunk similarities"),
            (65.0, "Extracting relationships"),
            (85.0, "Building relationship graph"),
            (100.0, "Relationship extraction completed"),
        ];

        for (progress, message) in steps {
            let _ = progress_sender.send(TaskProgress {
                task_id: task_id.to_string(),
                progress,
                message: message.to_string(),
                metadata: None,
            });
            
            tokio::time::sleep(Duration::from_millis(700)).await;
        }

        Ok(())
    }

    async fn simulate_python_package_install(
        task_id: &str,
        progress_sender: &mpsc::UnboundedSender<TaskProgress>,
    ) -> Result<(), String> {
        let steps = vec![
            (10.0, "Checking Python environment"),
            (25.0, "Downloading packages"),
            (50.0, "Installing dependencies"),
            (75.0, "Compiling native extensions"),
            (90.0, "Verifying installation"),
            (100.0, "Package installation completed"),
        ];

        for (progress, message) in steps {
            let _ = progress_sender.send(TaskProgress {
                task_id: task_id.to_string(),
                progress,
                message: message.to_string(),
                metadata: None,
            });
            
            tokio::time::sleep(Duration::from_millis(1200)).await; // Longer for package installs
        }

        Ok(())
    }

    pub async fn shutdown(&self) {
        info!("Shutting down background task system");
        self.shutdown_signal.notify_waiters();
        
        // Cancel all running tasks
        let active_tasks = self.get_active_tasks().await;
        for task in active_tasks {
            let _ = self.cancel_task(&task.id).await;
        }
    }

    pub async fn get_system_stats(&self) -> serde_json::Value {
        let tasks = self.tasks.read().await;
        let queue_length = self.get_queue_length().await;
        let active_workers = *self.active_workers.read().await;
        
        let total_tasks = tasks.len();
        let completed_tasks = tasks.values().filter(|t| matches!(t.status, TaskStatus::Completed)).count();
        let failed_tasks = tasks.values().filter(|t| matches!(t.status, TaskStatus::Failed)).count();
        let running_tasks = tasks.values().filter(|t| matches!(t.status, TaskStatus::Running)).count();
        
        serde_json::json!({
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "running_tasks": running_tasks,
            "queued_tasks": queue_length,
            "active_workers": active_workers,
            "max_workers": self.max_workers,
            "success_rate": if total_tasks > 0 { completed_tasks as f64 / total_tasks as f64 * 100.0 } else { 0.0 }
        })
    }
}
