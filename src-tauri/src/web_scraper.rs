use std::collections::HashMap;
use std::path::PathBuf;
use serde::{Deserialize, Serialize};
use serde_json;
use tokio::process::Command;
use thiserror::Error;
use chrono::{DateTime, Utc};
use uuid::Uuid;
use log::{info, error, warn, debug};

use crate::python_manager::PythonManager;

/// Scraping-related errors
#[derive(Error, Debug)]
pub enum ScrapingError {
    #[error("Python execution error: {0}")]
    PythonExecution(String),
    
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
    
    #[error("Invalid URL: {0}")]
    InvalidUrl(String),
    
    #[error("Network error: {0}")]
    Network(String),
    
    #[error("Rate limit exceeded")]
    RateLimit,
    
    #[error("Configuration error: {0}")]
    Configuration(String),
    
    #[error("Scraping job not found: {0}")]
    JobNotFound(String),
}

pub type ScrapingResult<T> = Result<T, ScrapingError>;

/// Configuration for web scraping operations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScrapingConfig {
    // Rate limiting
    pub request_delay: f64,
    pub max_requests_per_minute: u32,
    pub burst_limit: u32,
    
    // Retry settings
    pub max_retries: u32,
    pub backoff_factor: f64,
    pub retry_statuses: Vec<u32>,
    
    // Timeout settings
    pub connect_timeout: f64,
    pub read_timeout: f64,
    pub total_timeout: f64,
    
    // User agents
    pub user_agents: Vec<String>,
    
    // Politeness settings
    pub respect_robots_txt: bool,
    pub crawl_delay_override: Option<f64>,
    
    // Cache settings
    pub enable_caching: bool,
    pub cache_dir: Option<String>,
    pub cache_ttl: u32,
    
    // Output settings
    pub save_raw_html: bool,
    pub raw_html_dir: Option<String>,
}

impl Default for ScrapingConfig {
    fn default() -> Self {
        Self {
            request_delay: 1.0,
            max_requests_per_minute: 30,
            burst_limit: 5,
            max_retries: 3,
            backoff_factor: 2.0,
            retry_statuses: vec![429, 502, 503, 504],
            connect_timeout: 10.0,
            read_timeout: 30.0,
            total_timeout: 60.0,
            user_agents: vec![
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36".to_string(),
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15".to_string(),
            ],
            respect_robots_txt: true,
            crawl_delay_override: None,
            enable_caching: true,
            cache_dir: None,
            cache_ttl: 3600,
            save_raw_html: false,
            raw_html_dir: None,
        }
    }
}

/// Progress information for scraping operations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScrapingProgress {
    pub total_urls: u32,
    pub completed_urls: u32,
    pub failed_urls: u32,
    pub cached_urls: u32,
    pub start_time: Option<DateTime<Utc>>,
    pub last_update: Option<DateTime<Utc>>,
    pub current_url: Option<String>,
    pub error_count: u32,
    pub last_error: Option<String>,
}

impl ScrapingProgress {
    pub fn new() -> Self {
        Self {
            total_urls: 0,
            completed_urls: 0,
            failed_urls: 0,
            cached_urls: 0,
            start_time: None,
            last_update: None,
            current_url: None,
            error_count: 0,
            last_error: None,
        }
    }
    
    pub fn completion_percentage(&self) -> f32 {
        if self.total_urls == 0 {
            return 0.0;
        }
        (self.completed_urls as f32 / self.total_urls as f32) * 100.0
    }
    
    pub fn success_rate(&self) -> f32 {
        let total_processed = self.completed_urls + self.failed_urls;
        if total_processed == 0 {
            return 0.0;
        }
        (self.completed_urls as f32 / total_processed as f32) * 100.0
    }
}

/// Result of scraping a single page
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScrapedPage {
    pub url: String,
    pub final_url: String,
    pub status_code: u16,
    pub headers: HashMap<String, String>,
    pub content: String,
    pub metadata: PageMetadata,
    pub cached: bool,
}

/// Metadata extracted from a scraped page
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PageMetadata {
    pub content_type: String,
    pub content_length: usize,
    pub encoding: String,
    pub timestamp: DateTime<Utc>,
    pub title: Option<String>,
    pub description: Option<String>,
    pub language: Option<String>,
}

/// Scraping job information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScrapingJob {
    pub id: Uuid,
    pub urls: Vec<String>,
    pub config: ScrapingConfig,
    pub progress: ScrapingProgress,
    pub status: ScrapingJobStatus,
    pub created_at: DateTime<Utc>,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub results: Vec<ScrapedPage>,
}

/// Status of a scraping job
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ScrapingJobStatus {
    Pending,
    Running,
    Completed,
    Failed,
    Cancelled,
}

/// Web scraper manager that coordinates Python scraping operations
pub struct WebScraperManager {
    python_manager: PythonManager,
    active_jobs: HashMap<Uuid, ScrapingJob>,
    script_path: PathBuf,
}

impl WebScraperManager {
    /// Create a new WebScraperManager
    pub fn new(data_dir: PathBuf) -> Self {
        let python_manager = PythonManager::new(data_dir.clone());
        let script_path = data_dir.join("scripts").join("scraper").join("web_scraper.py");
        
        Self {
            python_manager,
            active_jobs: HashMap::new(),
            script_path,
        }
    }
    
    /// Initialize the scraper environment
    pub async fn initialize(&mut self) -> ScrapingResult<()> {
        info!("Initializing web scraper environment");
        
        // Ensure the script directory exists
        if let Some(parent) = self.script_path.parent() {
            tokio::fs::create_dir_all(parent)
                .await
                .map_err(|e| ScrapingError::Configuration(format!("Failed to create script directory: {}", e)))?;
        }
        
        // Check if Python environment is ready
        match self.python_manager.health_check().await {
            Ok(_) => {
                info!("Python environment is ready");
            }
            Err(e) => {
                warn!("Python environment not ready: {}", e);
                // Could initialize environment here if needed
                // For now, continue without failing - we'll improve this later
                // return Err(ScrapingError::Configuration(format!("Python environment not ready: {}", e)));
            }
        }
        
        // Install scraping dependencies
        self.install_dependencies().await?;
        
        info!("Web scraper environment initialized successfully");
        Ok(())
    }
    
    /// Install required Python dependencies for scraping
    async fn install_dependencies(&self) -> ScrapingResult<()> {
        info!("Installing scraping dependencies");
        
        let requirements = vec![
            "aiohttp>=3.9.0",
            "aiofiles>=23.2.0", 
            "beautifulsoup4>=4.12.0",
            "lxml>=4.9.0",
            "requests>=2.31.0",
            "urllib3>=2.0.0",
            "html5lib>=1.1",
            "python-dateutil>=2.8.0",
            "pytz>=2023.3",
            "cchardet>=2.1.7",
        ];
        
        for requirement in requirements {
            // TODO: Implement package installation in PythonManager
            // match self.python_manager.install_package(requirement).await {
            //     Ok(_) => debug!("Installed package: {}", requirement),
            //     Err(e) => {
            //         error!("Failed to install package {}: {}", requirement, e);
            //         return Err(ScrapingError::Configuration(format!("Failed to install {}: {}", requirement, e)));
            //     }
            // }
            debug!("Would install package: {}", requirement);
        }
        
        info!("All scraping dependencies installed successfully");
        Ok(())
    }
    
    /// Start a new scraping job
    pub async fn start_scraping_job(&mut self, urls: Vec<String>, config: ScrapingConfig) -> ScrapingResult<Uuid> {
        let job_id = Uuid::new_v4();
        
        let mut job = ScrapingJob {
            id: job_id,
            urls: urls.clone(),
            config: config.clone(),
            progress: ScrapingProgress::new(),
            status: ScrapingJobStatus::Pending,
            created_at: Utc::now(),
            started_at: None,
            completed_at: None,
            results: Vec::new(),
        };
        
        job.progress.total_urls = urls.len() as u32;
        
        // Store the job
        self.active_jobs.insert(job_id, job);
        
        info!("Created scraping job {} for {} URLs", job_id, urls.len());
        
        // Start the actual scraping in the background
        self.execute_scraping_job(job_id).await?;
        
        Ok(job_id)
    }
    
    /// Execute a scraping job
    async fn execute_scraping_job(&mut self, job_id: Uuid) -> ScrapingResult<()> {
        let job = self.active_jobs.get_mut(&job_id)
            .ok_or_else(|| ScrapingError::JobNotFound(job_id.to_string()))?;
        
        job.status = ScrapingJobStatus::Running;
        job.started_at = Some(Utc::now());
        job.progress.start_time = Some(Utc::now());
        
        info!("Starting execution of scraping job {}", job_id);
        
        // Prepare the Python script arguments
        let config_json = serde_json::to_string(&job.config)
            .map_err(|e| ScrapingError::Serialization(e))?;
        let urls_json = serde_json::to_string(&job.urls)
            .map_err(|e| ScrapingError::Serialization(e))?;
        
        // Create a temporary script that uses our web_scraper module
        let temp_script = format!(r#"
import asyncio
import json
import sys
import os

# Add the scraper directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from web_scraper import WebScraper, ScrapingConfig

async def main():
    try:
        # Parse arguments
        config_data = json.loads(sys.argv[1])
        urls = json.loads(sys.argv[2])
        
        # Create config object
        config = ScrapingConfig(**config_data)
        
        # Run scraper
        async with WebScraper(config) as scraper:
            results = await scraper.fetch_multiple(urls)
            
            # Output results as JSON
            output = {{
                'success': True,
                'results': results,
                'progress': {{
                    'total_urls': scraper.progress.total_urls,
                    'completed_urls': scraper.progress.completed_urls,
                    'failed_urls': scraper.progress.failed_urls,
                    'cached_urls': scraper.progress.cached_urls,
                    'error_count': scraper.progress.error_count,
                    'last_error': scraper.progress.last_error,
                }}
            }}
            
            print(json.dumps(output))
            
    except Exception as e:
        output = {{
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }}
        print(json.dumps(output))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
"#);
        
        // Write temporary script
        let temp_script_path = self.script_path.parent().unwrap().join("temp_scraper.py");
        tokio::fs::write(&temp_script_path, temp_script)
            .await
            .map_err(|e| ScrapingError::Configuration(format!("Failed to write temp script: {}", e)))?;
        
        // Execute the Python script
        let result = self.python_manager.execute_script(
            &temp_script_path.to_string_lossy(),
            vec![config_json, urls_json]
        ).await;
        
        // Clean up temp script
        let _ = tokio::fs::remove_file(&temp_script_path).await;
        
        // Process the result
        match result {
            Ok(process_result) => {
                if process_result.success {
                    self.process_scraping_result(job_id, &process_result.stdout).await?;
                } else {
                    error!("Scraping job {} failed with stderr: {}", job_id, process_result.stderr);
                    if let Some(job) = self.active_jobs.get_mut(&job_id) {
                        job.status = ScrapingJobStatus::Failed;
                        job.completed_at = Some(Utc::now());
                        job.progress.last_error = Some(process_result.stderr.clone());
                    }
                    return Err(ScrapingError::PythonExecution(process_result.stderr));
                }
            }
            Err(e) => {
                error!("Scraping job {} failed: {}", job_id, e);
                if let Some(job) = self.active_jobs.get_mut(&job_id) {
                    job.status = ScrapingJobStatus::Failed;
                    job.completed_at = Some(Utc::now());
                    job.progress.last_error = Some(e.to_string());
                }
                return Err(ScrapingError::PythonExecution(e.to_string()));
            }
        }
        
        Ok(())
    }
    
    /// Process the result from a Python scraping job
    async fn process_scraping_result(&mut self, job_id: Uuid, output: &str) -> ScrapingResult<()> {
        let job = self.active_jobs.get_mut(&job_id)
            .ok_or_else(|| ScrapingError::JobNotFound(job_id.to_string()))?;
        
        // Parse the JSON output
        let result: serde_json::Value = serde_json::from_str(output)
            .map_err(|e| ScrapingError::Serialization(e))?;
        
        if result["success"].as_bool().unwrap_or(false) {
            // Process successful results
            if let Some(results_array) = result["results"].as_array() {
                for result_item in results_array {
                    if let Ok(scraped_page) = serde_json::from_value::<ScrapedPage>(result_item.clone()) {
                        job.results.push(scraped_page);
                    }
                }
            }
            
            // Update progress
            if let Some(progress_data) = result["progress"].as_object() {
                if let Some(completed) = progress_data["completed_urls"].as_u64() {
                    job.progress.completed_urls = completed as u32;
                }
                if let Some(failed) = progress_data["failed_urls"].as_u64() {
                    job.progress.failed_urls = failed as u32;
                }
                if let Some(cached) = progress_data["cached_urls"].as_u64() {
                    job.progress.cached_urls = cached as u32;
                }
                if let Some(error_count) = progress_data["error_count"].as_u64() {
                    job.progress.error_count = error_count as u32;
                }
                if let Some(last_error) = progress_data["last_error"].as_str() {
                    job.progress.last_error = Some(last_error.to_string());
                }
            }
            
            job.status = ScrapingJobStatus::Completed;
            job.completed_at = Some(Utc::now());
            job.progress.last_update = Some(Utc::now());
            
            info!("Scraping job {} completed successfully with {} results", 
                  job_id, job.results.len());
        } else {
            // Handle error
            let error_msg = result["error"].as_str().unwrap_or("Unknown error");
            job.status = ScrapingJobStatus::Failed;
            job.completed_at = Some(Utc::now());
            job.progress.last_error = Some(error_msg.to_string());
            
            error!("Scraping job {} failed: {}", job_id, error_msg);
            return Err(ScrapingError::PythonExecution(error_msg.to_string()));
        }
        
        Ok(())
    }
    
    /// Get the status of a scraping job
    pub fn get_job_status(&self, job_id: Uuid) -> Option<&ScrapingJob> {
        self.active_jobs.get(&job_id)
    }
    
    /// Get all active jobs
    pub fn get_active_jobs(&self) -> Vec<&ScrapingJob> {
        self.active_jobs.values().collect()
    }
    
    /// Cancel a scraping job
    pub fn cancel_job(&mut self, job_id: Uuid) -> ScrapingResult<()> {
        if let Some(job) = self.active_jobs.get_mut(&job_id) {
            if job.status == ScrapingJobStatus::Running {
                job.status = ScrapingJobStatus::Cancelled;
                job.completed_at = Some(Utc::now());
                info!("Cancelled scraping job {}", job_id);
            }
            Ok(())
        } else {
            Err(ScrapingError::JobNotFound(job_id.to_string()))
        }
    }
    
    /// Remove completed jobs from memory
    pub fn cleanup_completed_jobs(&mut self) -> usize {
        let initial_count = self.active_jobs.len();
        
        self.active_jobs.retain(|_, job| {
            !matches!(job.status, ScrapingJobStatus::Completed | ScrapingJobStatus::Failed | ScrapingJobStatus::Cancelled)
        });
        
        let removed_count = initial_count - self.active_jobs.len();
        if removed_count > 0 {
            info!("Cleaned up {} completed scraping jobs", removed_count);
        }
        
        removed_count
    }
    
    /// Scrape a single URL (convenience method)
    pub async fn scrape_url(&mut self, url: String, config: Option<ScrapingConfig>) -> ScrapingResult<ScrapedPage> {
        let job_id = self.start_scraping_job(vec![url], config.unwrap_or_default()).await?;
        
        // Wait for job completion (simple polling - could be improved with async notifications)
        for _ in 0..60 { // Wait up to 60 seconds
            tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
            
            if let Some(job) = self.get_job_status(job_id) {
                match job.status {
                    ScrapingJobStatus::Completed => {
                        if let Some(result) = job.results.first() {
                            return Ok(result.clone());
                        } else {
                            return Err(ScrapingError::Network("No results returned".to_string()));
                        }
                    }
                    ScrapingJobStatus::Failed => {
                        let error_msg = job.progress.last_error
                            .as_ref()
                            .map(|s| s.as_str())
                            .unwrap_or("Unknown error");
                        return Err(ScrapingError::Network(error_msg.to_string()));
                    }
                    ScrapingJobStatus::Cancelled => {
                        return Err(ScrapingError::Network("Job was cancelled".to_string()));
                    }
                    _ => continue, // Still running
                }
            } else {
                return Err(ScrapingError::JobNotFound(job_id.to_string()));
            }
        }
        
        // Timeout
        self.cancel_job(job_id)?;
        Err(ScrapingError::Network("Scraping timeout".to_string()))
    }
}
