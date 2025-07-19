use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use tokio::sync::{Mutex, RwLock};
use serde::{Deserialize, Serialize};
use log::{debug, info, warn, error};
use sysinfo::{System, ProcessesToUpdate};

// Helper function to convert Instant to Unix timestamp in milliseconds
fn instant_to_timestamp(instant: Instant) -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

// Helper function to convert Duration to milliseconds
fn duration_to_ms(duration: Duration) -> u64 {
    duration.as_millis() as u64
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceMetrics {
    pub cpu_usage: f64,
    pub memory_usage: u64,
    pub memory_total: u64,
    pub disk_usage: u64,
    pub disk_total: u64,
    pub active_tasks: u32,
    pub completed_tasks: u32,
    pub average_task_duration: Duration,
    pub uptime: Duration,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskMetrics {
    pub task_id: String,
    pub task_type: String,
    pub start_time: u64, // Unix timestamp in milliseconds
    pub end_time: Option<u64>, // Unix timestamp in milliseconds
    pub duration_ms: Option<u64>, // Duration in milliseconds
    pub memory_peak: u64,
    pub cpu_peak: f64,
    pub status: TaskStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TaskStatus {
    Running,
    Completed,
    Failed,
    Cancelled,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceLimits {
    pub max_memory_mb: u64,
    pub max_cpu_percent: f64,
    pub max_concurrent_tasks: u32,
    pub task_timeout_seconds: u64,
}

impl Default for ResourceLimits {
    fn default() -> Self {
        Self {
            max_memory_mb: 2048,      // 2GB default limit
            max_cpu_percent: 80.0,    // 80% CPU usage limit
            max_concurrent_tasks: 4,   // 4 concurrent tasks
            task_timeout_seconds: 1800, // 30 minute timeout
        }
    }
}

pub struct PerformanceMonitor {
    metrics: Arc<RwLock<PerformanceMetrics>>,
    active_tasks: Arc<RwLock<HashMap<String, TaskMetrics>>>,
    completed_tasks: Arc<RwLock<Vec<TaskMetrics>>>,
    resource_limits: Arc<RwLock<ResourceLimits>>,
    start_time: Instant,
    monitoring_enabled: bool,
    system: Arc<Mutex<System>>,
}

impl PerformanceMonitor {
    pub fn new() -> Self {
        let mut system = System::new_all();
        system.refresh_all();
        
        let initial_metrics = PerformanceMetrics {
            cpu_usage: 0.0,
            memory_usage: 0,
            memory_total: system.total_memory(),
            disk_usage: 0,
            disk_total: Self::get_total_disk_space_sysinfo(&system),
            active_tasks: 0,
            completed_tasks: 0,
            average_task_duration: Duration::from_secs(0),
            uptime: Duration::from_secs(0),
        };

        Self {
            metrics: Arc::new(RwLock::new(initial_metrics)),
            active_tasks: Arc::new(RwLock::new(HashMap::new())),
            completed_tasks: Arc::new(RwLock::new(Vec::new())),
            resource_limits: Arc::new(RwLock::new(ResourceLimits::default())),
            start_time: Instant::now(),
            monitoring_enabled: true,
            system: Arc::new(Mutex::new(system)),
        }
    }

    pub async fn start_monitoring(&self) {
        if !self.monitoring_enabled {
            return;
        }

        let metrics = Arc::clone(&self.metrics);
        let active_tasks = Arc::clone(&self.active_tasks);
        let system = Arc::clone(&self.system);
        let start_time = self.start_time;

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(5));
            
            loop {
                interval.tick().await;
                
                // Refresh system information
                {
                    let mut sys = system.lock().await;
                    sys.refresh_cpu_all();
                    sys.refresh_memory();
                    sys.refresh_processes(ProcessesToUpdate::All);
                }
                
                let cpu_usage = Self::get_cpu_usage_real(&system).await;
                let memory_usage = Self::get_memory_usage_real(&system).await;
                let disk_usage = Self::get_disk_usage_real().await;
                
                let active_count = active_tasks.read().await.len() as u32;
                let uptime = start_time.elapsed();

                {
                    let mut metrics_guard = metrics.write().await;
                    metrics_guard.cpu_usage = cpu_usage;
                    metrics_guard.memory_usage = memory_usage;
                    metrics_guard.disk_usage = disk_usage;
                    metrics_guard.active_tasks = active_count;
                    metrics_guard.uptime = uptime;
                }

                debug!("Performance metrics updated: CPU: {:.1}%, Memory: {}MB, Active tasks: {}", 
                       cpu_usage, memory_usage / 1024 / 1024, active_count);
            }
        });
    }

    pub async fn start_task(&self, task_id: String, task_type: String) -> Result<(), String> {
        let limits = self.resource_limits.read().await;
        let active_count = self.active_tasks.read().await.len() as u32;

        if active_count >= limits.max_concurrent_tasks {
            return Err(format!("Cannot start task: maximum concurrent tasks ({}) reached", 
                             limits.max_concurrent_tasks));
        }

        let current_memory = Self::get_memory_usage_real(&self.system).await;
        if current_memory > limits.max_memory_mb * 1024 * 1024 {
            return Err("Cannot start task: memory limit exceeded".to_string());
        }

        let task_metrics = TaskMetrics {
            task_id: task_id.clone(),
            task_type,
            start_time: instant_to_timestamp(Instant::now()),
            end_time: None,
            duration_ms: None,
            memory_peak: current_memory,
            cpu_peak: Self::get_cpu_usage_real(&self.system).await,
            status: TaskStatus::Running,
        };

        self.active_tasks.write().await.insert(task_id.clone(), task_metrics);
        info!("Task started: {}", task_id);
        
        Ok(())
    }

    pub async fn complete_task(&self, task_id: &str, success: bool) {
        let mut active_tasks = self.active_tasks.write().await;
        
        if let Some(mut task) = active_tasks.remove(task_id) {
            let now = instant_to_timestamp(Instant::now());
            task.end_time = Some(now);
            task.duration_ms = Some(now - task.start_time);
            task.status = if success { TaskStatus::Completed } else { TaskStatus::Failed };
            
            let duration_secs = task.duration_ms.unwrap() as f64 / 1000.0;
            info!("Task completed: {} in {:.2}s", task_id, duration_secs);
            
            // Update average task duration
            {
                let mut metrics = self.metrics.write().await;
                let mut completed_tasks = self.completed_tasks.write().await;
                
                completed_tasks.push(task.clone());
                metrics.completed_tasks = completed_tasks.len() as u32;
                
                // Calculate new average duration
                let total_duration_ms: u64 = completed_tasks
                    .iter()
                    .filter_map(|t| t.duration_ms)
                    .sum();
                
                if !completed_tasks.is_empty() {
                    let average_ms = total_duration_ms / completed_tasks.len() as u64;
                    metrics.average_task_duration = Duration::from_millis(average_ms);
                }
            }
        }
    }

    pub async fn cancel_task(&self, task_id: &str) {
        let mut active_tasks = self.active_tasks.write().await;
        
        if let Some(mut task) = active_tasks.remove(task_id) {
            let now = instant_to_timestamp(Instant::now());
            task.end_time = Some(now);
            task.duration_ms = Some(now - task.start_time);
            task.status = TaskStatus::Cancelled;
            
            warn!("Task cancelled: {}", task_id);
            self.completed_tasks.write().await.push(task);
        }
    }

    pub async fn get_metrics(&self) -> PerformanceMetrics {
        self.metrics.read().await.clone()
    }

    pub async fn get_active_tasks(&self) -> Vec<TaskMetrics> {
        self.active_tasks.read().await.values().cloned().collect()
    }

    pub async fn get_resource_usage_recommendation(&self) -> String {
        let metrics = self.get_metrics().await;
        let limits = self.resource_limits.read().await;
        
        let memory_usage_percent = (metrics.memory_usage as f64 / metrics.memory_total as f64) * 100.0;
        
        if metrics.cpu_usage > limits.max_cpu_percent {
            "High CPU usage detected. Consider reducing concurrent tasks or enabling background processing.".to_string()
        } else if memory_usage_percent > 85.0 {
            "High memory usage detected. Consider processing smaller batches or closing other applications.".to_string()
        } else if metrics.active_tasks > limits.max_concurrent_tasks - 1 {
            "Near maximum concurrent task limit. New tasks may be queued.".to_string()
        } else {
            "System resources are operating within normal limits.".to_string()
        }
    }

    pub async fn optimize_for_low_memory(&self) {
        let mut limits = self.resource_limits.write().await;
        limits.max_memory_mb = 1024; // 1GB limit
        limits.max_concurrent_tasks = 2; // Reduce concurrency
        info!("Performance optimization: Configured for low memory usage");
    }

    pub async fn optimize_for_performance(&self) {
        let mut limits = self.resource_limits.write().await;
        let total_memory_gb = Self::get_total_memory() / 1024 / 1024 / 1024;
        
        // Use up to 50% of available memory
        limits.max_memory_mb = (total_memory_gb * 512).max(2048);
        limits.max_concurrent_tasks = num_cpus::get() as u32;
        info!("Performance optimization: Configured for maximum performance");
    }

    // Real system metrics collection methods using sysinfo
    async fn get_cpu_usage_real(system: &Arc<Mutex<System>>) -> f64 {
        let sys = system.lock().await;
        let cpus = sys.cpus();
        if cpus.is_empty() {
            return 0.0;
        }
        
        let total_usage: f64 = cpus.iter().map(|cpu| cpu.cpu_usage() as f64).sum();
        total_usage / cpus.len() as f64
    }

    async fn get_memory_usage_real(system: &Arc<Mutex<System>>) -> u64 {
        let sys = system.lock().await;
        sys.used_memory()
    }

    async fn get_disk_usage_real() -> u64 {
        // Get current working directory disk usage
        match std::env::current_dir() {
            Ok(current_dir) => {
                // Use du command for accurate disk usage of current directory
                if cfg!(target_os = "macos") {
                    use std::process::Command;
                    if let Ok(output) = Command::new("du")
                        .args(&["-sk", current_dir.to_str().unwrap_or(".")])
                        .output()
                    {
                        let output_str = String::from_utf8_lossy(&output.stdout);
                        if let Some(first_line) = output_str.lines().next() {
                            if let Some(size_str) = first_line.split_whitespace().next() {
                                if let Ok(size_kb) = size_str.parse::<u64>() {
                                    return size_kb * 1024; // Convert KB to bytes
                                }
                            }
                        }
                    }
                }
                0
            }
            Err(_) => 0,
        }
    }

    fn get_total_disk_space_sysinfo(system: &System) -> u64 {
        // Fallback to a default approach using system commands for macOS
        if cfg!(target_os = "macos") {
            use std::process::Command;
            if let Ok(output) = Command::new("df")
                .args(&["-k", "."])
                .output()
            {
                let output_str = String::from_utf8_lossy(&output.stdout);
                // Parse the second line (first is header)
                if let Some(data_line) = output_str.lines().nth(1) {
                    let parts: Vec<&str> = data_line.split_whitespace().collect();
                    if parts.len() >= 2 {
                        if let Ok(total_kb) = parts[1].parse::<u64>() {
                            return total_kb * 1024; // Convert KB to bytes
                        }
                    }
                }
            }
        }
        
        // Ultimate fallback
        1024 * 1024 * 1024 * 1024 // 1TB default
    }

    // Legacy methods for backward compatibility - now use real implementations
    async fn get_cpu_usage() -> f64 {
        // Create a temporary System instance for this call
        let mut system = System::new();
        system.refresh_cpu_all();
        
        // Wait a moment for CPU measurement
        tokio::time::sleep(Duration::from_millis(200)).await;
        system.refresh_cpu_all();
        
        let cpus = system.cpus();
        if cpus.is_empty() {
            return 0.0;
        }
        
        let total_usage: f64 = cpus.iter().map(|cpu| cpu.cpu_usage() as f64).sum();
        total_usage / cpus.len() as f64
    }

    fn get_memory_usage() -> u64 {
        let mut system = System::new();
        system.refresh_memory();
        system.used_memory()
    }

    fn get_total_memory() -> u64 {
        let mut system = System::new();
        system.refresh_memory();
        system.total_memory()
    }

    fn get_disk_usage() -> u64 {
        // Use the async version synchronously for compatibility
        let rt = tokio::runtime::Handle::try_current();
        if let Ok(handle) = rt {
            tokio::task::block_in_place(|| {
                handle.block_on(Self::get_disk_usage_real())
            })
        } else {
            // Fallback for when not in async context
            match std::env::current_dir() {
                Ok(current_dir) => {
                    if cfg!(target_os = "macos") {
                        use std::process::Command;
                        if let Ok(output) = Command::new("du")
                            .args(&["-sk", current_dir.to_str().unwrap_or(".")])
                            .output()
                        {
                            let output_str = String::from_utf8_lossy(&output.stdout);
                            if let Some(first_line) = output_str.lines().next() {
                                if let Some(size_str) = first_line.split_whitespace().next() {
                                    if let Ok(size_kb) = size_str.parse::<u64>() {
                                        return size_kb * 1024;
                                    }
                                }
                            }
                        }
                    }
                    0
                }
                Err(_) => 0,
            }
        }
    }

    fn get_total_disk_space() -> u64 {
        // Use system commands for disk space on macOS
        if cfg!(target_os = "macos") {
            use std::process::Command;
            if let Ok(output) = Command::new("df")
                .args(&["-k", "."])
                .output()
            {
                let output_str = String::from_utf8_lossy(&output.stdout);
                // Parse the second line (first is header)
                if let Some(data_line) = output_str.lines().nth(1) {
                    let parts: Vec<&str> = data_line.split_whitespace().collect();
                    if parts.len() >= 2 {
                        if let Ok(total_kb) = parts[1].parse::<u64>() {
                            return total_kb * 1024; // Convert KB to bytes
                        }
                    }
                }
            }
        }
        
        1024 * 1024 * 1024 * 1024 // 1TB default
    }

    pub async fn cleanup_old_metrics(&self) {
        let mut completed_tasks = self.completed_tasks.write().await;
        
        // Keep only last 1000 completed tasks
        if completed_tasks.len() > 1000 {
            let excess = completed_tasks.len() - 1000;
            completed_tasks.drain(0..excess);
            info!("Cleaned up old performance metrics, keeping last 1000 tasks");
        }
    }

    pub async fn export_metrics(&self) -> Result<String, String> {
        let metrics = self.get_metrics().await;
        let active_tasks = self.get_active_tasks().await;
        let completed_tasks = self.completed_tasks.read().await.clone();
        
        let export_data = serde_json::json!({
            "timestamp": chrono::Utc::now(),
            "current_metrics": metrics,
            "active_tasks": active_tasks,
            "completed_tasks": completed_tasks,
            "resource_limits": *self.resource_limits.read().await
        });
        
        serde_json::to_string_pretty(&export_data)
            .map_err(|e| format!("Failed to export metrics: {}", e))
    }
}
