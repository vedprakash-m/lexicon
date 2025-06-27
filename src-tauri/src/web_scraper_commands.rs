use tauri::{State, command};
use std::sync::Arc;
use tokio::sync::Mutex;
use uuid::Uuid;
use serde::{Deserialize, Serialize};
use log::{info, error};

use crate::web_scraper::{
    WebScraperManager, ScrapingConfig, ScrapingJob, ScrapingProgress,
    ScrapedPage, ScrapingError
};

/// Shared web scraper state for Tauri
pub type WebScraperState = Arc<Mutex<WebScraperManager>>;

/// Request to start a scraping job
#[derive(Debug, Deserialize)]
pub struct StartScrapingRequest {
    pub urls: Vec<String>,
    pub config: Option<ScrapingConfig>,
}

/// Request to scrape a single URL
#[derive(Debug, Deserialize)]
pub struct ScrapeSingleUrlRequest {
    pub url: String,
    pub config: Option<ScrapingConfig>,
}

/// Response wrapper for scraping commands
#[derive(Debug, Serialize)]
pub struct ScrapingResponse<T> {
    pub success: bool,
    pub data: Option<T>,
    pub error: Option<String>,
}

impl<T> ScrapingResponse<T> {
    pub fn success(data: T) -> Self {
        Self {
            success: true,
            data: Some(data),
            error: None,
        }
    }

    pub fn error(error: String) -> Self {
        Self {
            success: false,
            data: None,
            error: Some(error),
        }
    }
}

/// Initialize the web scraper
#[command]
pub async fn init_web_scraper(
    scraper: State<'_, WebScraperState>
) -> Result<ScrapingResponse<bool>, String> {
    info!("Initializing web scraper");

    let mut scraper_lock = scraper.lock().await;
    
    match scraper_lock.initialize().await {
        Ok(_) => {
            info!("Web scraper initialized successfully");
            Ok(ScrapingResponse::success(true))
        }
        Err(e) => {
            error!("Failed to initialize web scraper: {}", e);
            Ok(ScrapingResponse::error(e.to_string()))
        }
    }
}

/// Start a scraping job for multiple URLs
#[command]
pub async fn start_scraping_job(
    request: StartScrapingRequest,
    scraper: State<'_, WebScraperState>
) -> Result<ScrapingResponse<String>, String> {
    info!("Starting scraping job for {} URLs", request.urls.len());

    let mut scraper_lock = scraper.lock().await;
    
    let config = request.config.unwrap_or_default();
    
    match scraper_lock.start_scraping_job(request.urls, config).await {
        Ok(job_id) => {
            info!("Started scraping job: {}", job_id);
            Ok(ScrapingResponse::success(job_id.to_string()))
        }
        Err(e) => {
            error!("Failed to start scraping job: {}", e);
            Ok(ScrapingResponse::error(e.to_string()))
        }
    }
}

/// Get the status of a scraping job
#[command]
pub async fn get_scraping_job_status(
    job_id: String,
    scraper: State<'_, WebScraperState>
) -> Result<ScrapingResponse<ScrapingJob>, String> {
    let uuid = match Uuid::parse_str(&job_id) {
        Ok(uuid) => uuid,
        Err(e) => return Ok(ScrapingResponse::error(format!("Invalid job ID: {}", e))),
    };

    let scraper_lock = scraper.lock().await;
    
    match scraper_lock.get_job_status(uuid) {
        Some(job) => {
            Ok(ScrapingResponse::success(job.clone()))
        }
        None => {
            Ok(ScrapingResponse::error("Job not found".to_string()))
        }
    }
}

/// Get all active scraping jobs
#[command]
pub async fn get_active_scraping_jobs(
    scraper: State<'_, WebScraperState>
) -> Result<ScrapingResponse<Vec<ScrapingJob>>, String> {
    let scraper_lock = scraper.lock().await;
    
    let jobs: Vec<ScrapingJob> = scraper_lock.get_active_jobs()
        .into_iter()
        .cloned()
        .collect();
    
    Ok(ScrapingResponse::success(jobs))
}

/// Cancel a scraping job
#[command]
pub async fn cancel_scraping_job(
    job_id: String,
    scraper: State<'_, WebScraperState>
) -> Result<ScrapingResponse<bool>, String> {
    let uuid = match Uuid::parse_str(&job_id) {
        Ok(uuid) => uuid,
        Err(e) => return Ok(ScrapingResponse::error(format!("Invalid job ID: {}", e))),
    };

    let mut scraper_lock = scraper.lock().await;
    
    match scraper_lock.cancel_job(uuid) {
        Ok(_) => {
            info!("Cancelled scraping job: {}", job_id);
            Ok(ScrapingResponse::success(true))
        }
        Err(e) => {
            error!("Failed to cancel scraping job: {}", e);
            Ok(ScrapingResponse::error(e.to_string()))
        }
    }
}

/// Scrape a single URL (convenience method)
#[command]
pub async fn scrape_single_url(
    request: ScrapeSingleUrlRequest,
    scraper: State<'_, WebScraperState>
) -> Result<ScrapingResponse<ScrapedPage>, String> {
    info!("Scraping single URL: {}", request.url);

    let mut scraper_lock = scraper.lock().await;
    
    match scraper_lock.scrape_url(request.url, request.config).await {
        Ok(result) => {
            info!("Successfully scraped URL");
            Ok(ScrapingResponse::success(result))
        }
        Err(e) => {
            error!("Failed to scrape URL: {}", e);
            Ok(ScrapingResponse::error(e.to_string()))
        }
    }
}

/// Clean up completed scraping jobs
#[command]
pub async fn cleanup_scraping_jobs(
    scraper: State<'_, WebScraperState>
) -> Result<ScrapingResponse<usize>, String> {
    let mut scraper_lock = scraper.lock().await;
    
    let cleaned_count = scraper_lock.cleanup_completed_jobs();
    
    info!("Cleaned up {} completed scraping jobs", cleaned_count);
    Ok(ScrapingResponse::success(cleaned_count))
}

/// Get scraping progress for a specific job
#[command]
pub async fn get_scraping_progress(
    job_id: String,
    scraper: State<'_, WebScraperState>
) -> Result<ScrapingResponse<ScrapingProgress>, String> {
    let uuid = match Uuid::parse_str(&job_id) {
        Ok(uuid) => uuid,
        Err(e) => return Ok(ScrapingResponse::error(format!("Invalid job ID: {}", e))),
    };

    let scraper_lock = scraper.lock().await;
    
    match scraper_lock.get_job_status(uuid) {
        Some(job) => {
            Ok(ScrapingResponse::success(job.progress.clone()))
        }
        None => {
            Ok(ScrapingResponse::error("Job not found".to_string()))
        }
    }
}

/// Get default scraping configuration
#[command]
pub async fn get_default_scraping_config() -> Result<ScrapingResponse<ScrapingConfig>, String> {
    Ok(ScrapingResponse::success(ScrapingConfig::default()))
}

/// Validate a list of URLs
#[command]
pub async fn validate_urls(
    urls: Vec<String>
) -> Result<ScrapingResponse<Vec<bool>>, String> {
    let mut valid_urls = Vec::new();
    
    for url in &urls {
        let is_valid = url::Url::parse(url).is_ok();
        valid_urls.push(is_valid);
    }
    
    Ok(ScrapingResponse::success(valid_urls))
}

/// Test scraper connectivity and configuration
#[command]
pub async fn test_scraper_connectivity(
    scraper: State<'_, WebScraperState>
) -> Result<ScrapingResponse<bool>, String> {
    info!("Testing scraper connectivity");

    // Test with a reliable test URL
    let test_url = "https://httpbin.org/get".to_string();
    let config = ScrapingConfig {
        request_delay: 0.1,
        max_retries: 1,
        total_timeout: 10.0,
        ..Default::default()
    };

    let mut scraper_lock = scraper.lock().await;
    
    match scraper_lock.scrape_url(test_url, Some(config)).await {
        Ok(_) => {
            info!("Scraper connectivity test successful");
            Ok(ScrapingResponse::success(true))
        }
        Err(e) => {
            error!("Scraper connectivity test failed: {}", e);
            Ok(ScrapingResponse::error(e.to_string()))
        }
    }
}
