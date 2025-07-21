use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs::{File, OpenOptions};
use std::io::{BufWriter, Write};
use std::path::PathBuf;
use tauri::command;
use chrono::{DateTime, Utc};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ErrorContext {
    pub user_id: Option<String>,
    pub session_id: String,
    pub user_agent: String,
    pub timestamp: String,
    pub url: String,
    pub component: Option<String>,
    pub action: Option<String>,
    pub metadata: Option<HashMap<String, serde_json::Value>>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ErrorReport {
    pub id: String,
    pub level: String, // "error", "warning", "info"
    pub message: String,
    pub stack: Option<String>,
    pub context: ErrorContext,
    pub fingerprint: String,
    pub tags: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ErrorMetrics {
    pub error_count: u32,
    pub error_rate: f64,
    pub top_errors: Vec<TopError>,
    pub affected_users: u32,
    pub time_range: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TopError {
    pub message: String,
    pub count: u32,
    pub last_seen: String,
}

pub struct ErrorTracker {
    log_file_path: PathBuf,
}

impl ErrorTracker {
    pub fn new(app_data_dir: &PathBuf) -> Result<Self, Box<dyn std::error::Error>> {
        let log_file_path = app_data_dir.join("error_log.jsonl");
        
        // Ensure the directory exists
        if let Some(parent) = log_file_path.parent() {
            std::fs::create_dir_all(parent)?;
        }

        Ok(ErrorTracker { log_file_path })
    }

    pub fn log_errors(&self, errors: Vec<ErrorReport>) -> Result<(), Box<dyn std::error::Error>> {
        let file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.log_file_path)?;

        let mut writer = BufWriter::new(file);

        for error in errors {
            let json_line = serde_json::to_string(&error)?;
            writeln!(writer, "{}", json_line)?;
        }

        writer.flush()?;
        Ok(())
    }

    pub fn get_error_metrics(&self, time_range: &str) -> Result<ErrorMetrics, Box<dyn std::error::Error>> {
        let cutoff_time = self.get_time_range_cutoff(time_range)?;
        let errors = self.read_errors_since(&cutoff_time)?;

        let mut error_counts: HashMap<String, u32> = HashMap::new();
        let mut last_seen: HashMap<String, String> = HashMap::new();
        let mut affected_users: std::collections::HashSet<String> = std::collections::HashSet::new();

        for error in &errors {
            let count = error_counts.entry(error.fingerprint.clone()).or_insert(0);
            *count += 1;
            last_seen.insert(error.fingerprint.clone(), error.context.timestamp.clone());

            if let Some(user_id) = &error.context.user_id {
                affected_users.insert(user_id.clone());
            }
        }

        let mut top_errors: Vec<TopError> = error_counts
            .into_iter()
            .map(|(fingerprint, count)| {
                let message = errors
                    .iter()
                    .find(|e| e.fingerprint == fingerprint)
                    .map(|e| e.message.clone())
                    .unwrap_or_else(|| "Unknown error".to_string());

                TopError {
                    message,
                    count,
                    last_seen: last_seen
                        .get(&fingerprint)
                        .cloned()
                        .unwrap_or_else(|| Utc::now().to_rfc3339()),
                }
            })
            .collect();

        top_errors.sort_by(|a, b| b.count.cmp(&a.count));
        top_errors.truncate(10);

        let error_rate = self.calculate_error_rate(&errors, time_range);

        Ok(ErrorMetrics {
            error_count: errors.len() as u32,
            error_rate,
            top_errors,
            affected_users: affected_users.len() as u32,
            time_range: time_range.to_string(),
        })
    }

    fn get_time_range_cutoff(&self, time_range: &str) -> Result<DateTime<Utc>, Box<dyn std::error::Error>> {
        let now = Utc::now();
        
        let hours = if time_range.ends_with('h') {
            time_range.trim_end_matches('h').parse::<i64>()?
        } else if time_range.ends_with('d') {
            time_range.trim_end_matches('d').parse::<i64>()? * 24
        } else {
            24 // Default to 24 hours
        };

        Ok(now - chrono::Duration::hours(hours))
    }

    fn read_errors_since(&self, cutoff_time: &DateTime<Utc>) -> Result<Vec<ErrorReport>, Box<dyn std::error::Error>> {
        use std::io::{BufRead, BufReader};

        if !self.log_file_path.exists() {
            return Ok(Vec::new());
        }

        let file = File::open(&self.log_file_path)?;
        let reader = BufReader::new(file);
        let mut errors = Vec::new();

        for line in reader.lines() {
            let line = line?;
            if let Ok(error) = serde_json::from_str::<ErrorReport>(&line) {
                if let Ok(error_time) = DateTime::parse_from_rfc3339(&error.context.timestamp) {
                    if error_time.with_timezone(&Utc) > *cutoff_time {
                        errors.push(error);
                    }
                }
            }
        }

        Ok(errors)
    }

    fn calculate_error_rate(&self, errors: &[ErrorReport], time_range: &str) -> f64 {
        if errors.is_empty() {
            return 0.0;
        }

        let hours = if time_range.ends_with('h') {
            time_range.trim_end_matches('h').parse::<f64>().unwrap_or(24.0)
        } else if time_range.ends_with('d') {
            time_range.trim_end_matches('d').parse::<f64>().unwrap_or(1.0) * 24.0
        } else {
            24.0
        };

        errors.len() as f64 / hours
    }

    pub fn clear_old_errors(&self, days_to_keep: u32) -> Result<(), Box<dyn std::error::Error>> {
        use std::io::{BufRead, BufReader};

        if !self.log_file_path.exists() {
            return Ok(());
        }

        let cutoff_time = Utc::now() - chrono::Duration::days(days_to_keep as i64);
        
        let file = File::open(&self.log_file_path)?;
        let reader = BufReader::new(file);
        let mut kept_errors = Vec::new();

        for line in reader.lines() {
            let line = line?;
            if let Ok(error) = serde_json::from_str::<ErrorReport>(&line) {
                if let Ok(error_time) = DateTime::parse_from_rfc3339(&error.context.timestamp) {
                    if error_time.with_timezone(&Utc) > cutoff_time {
                        kept_errors.push(line);
                    }
                }
            }
        }

        // Rewrite the file with only recent errors
        let file = File::create(&self.log_file_path)?;
        let mut writer = BufWriter::new(file);

        for error_line in kept_errors {
            writeln!(writer, "{}", error_line)?;
        }

        writer.flush()?;
        Ok(())
    }

    pub fn export_errors(&self, output_path: &PathBuf) -> Result<(), Box<dyn std::error::Error>> {
        std::fs::copy(&self.log_file_path, output_path)?;
        Ok(())
    }
}

// Tauri command handlers
#[command]
pub async fn log_errors(
    errors: Vec<ErrorReport>,
    app_handle: tauri::AppHandle,
) -> Result<(), String> {
    let app_data_dir = app_handle
        .path()
        .app_data_dir()
        .map_err(|e| format!("Failed to get app data directory: {}", e))?;

    let error_tracker = ErrorTracker::new(&app_data_dir)
        .map_err(|e| format!("Failed to create error tracker: {}", e))?;

    error_tracker
        .log_errors(errors)
        .map_err(|e| format!("Failed to log errors: {}", e))?;

    Ok(())
}

#[command]
pub async fn get_error_metrics(
    time_range: String,
    app_handle: tauri::AppHandle,
) -> Result<ErrorMetrics, String> {
    let app_data_dir = app_handle
        .path()
        .app_data_dir()
        .map_err(|e| format!("Failed to get app data directory: {}", e))?;

    let error_tracker = ErrorTracker::new(&app_data_dir)
        .map_err(|e| format!("Failed to create error tracker: {}", e))?;

    error_tracker
        .get_error_metrics(&time_range)
        .map_err(|e| format!("Failed to get error metrics: {}", e))
}

#[command]
pub async fn clear_error_log(app_handle: tauri::AppHandle) -> Result<(), String> {
    let app_data_dir = app_handle
        .path()
        .app_data_dir()
        .map_err(|e| format!("Failed to get app data directory: {}", e))?;

    let log_file_path = app_data_dir.join("error_log.jsonl");
    
    if log_file_path.exists() {
        std::fs::remove_file(log_file_path)
            .map_err(|e| format!("Failed to clear error log: {}", e))?;
    }

    Ok(())
}

#[command]
pub async fn export_error_log(
    output_path: String,
    app_handle: tauri::AppHandle,
) -> Result<(), String> {
    let app_data_dir = app_handle
        .path()
        .app_data_dir()
        .map_err(|e| format!("Failed to get app data directory: {}", e))?;

    let error_tracker = ErrorTracker::new(&app_data_dir)
        .map_err(|e| format!("Failed to create error tracker: {}", e))?;

    let output_path = PathBuf::from(output_path);
    error_tracker
        .export_errors(&output_path)
        .map_err(|e| format!("Failed to export error log: {}", e))?;

    Ok(())
}

#[command]
pub async fn cleanup_old_errors(
    days_to_keep: u32,
    app_handle: tauri::AppHandle,
) -> Result<(), String> {
    let app_data_dir = app_handle
        .path()
        .app_data_dir()
        .map_err(|e| format!("Failed to get app data directory: {}", e))?;

    let error_tracker = ErrorTracker::new(&app_data_dir)
        .map_err(|e| format!("Failed to create error tracker: {}", e))?;

    error_tracker
        .clear_old_errors(days_to_keep)
        .map_err(|e| format!("Failed to cleanup old errors: {}", e))?;

    Ok(())
}
