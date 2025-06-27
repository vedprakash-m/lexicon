use crate::cache_manager::{CacheManager, CacheConfig, CacheStats};
use tauri::State;
use tokio::sync::Mutex;
use std::sync::Arc;
use serde::{Deserialize, Serialize};
use anyhow::Result;

pub type CacheManagerState = Arc<Mutex<CacheManager>>;

#[derive(Debug, Serialize, Deserialize)]
pub struct CacheConfigUpdate {
    pub max_size_mb: Option<u64>,
    pub max_entries: Option<u64>,
    pub enable_http_cache: Option<bool>,
    pub enable_file_cache: Option<bool>,
    pub cleanup_interval_seconds: Option<u64>,
}

/// Get current cache statistics
#[tauri::command]
pub async fn get_cache_stats(
    cache_manager: State<'_, CacheManagerState>,
) -> Result<CacheStats, String> {
    let cache = cache_manager.lock().await;
    Ok(cache.get_stats().await)
}

/// Get current cache configuration
#[tauri::command]
pub async fn get_cache_config(
    cache_manager: State<'_, CacheManagerState>,
) -> Result<CacheConfig, String> {
    let cache = cache_manager.lock().await;
    Ok(cache.config.clone())
}

/// Update cache configuration
#[tauri::command]
pub async fn update_cache_config(
    cache_manager: State<'_, CacheManagerState>,
    config_update: CacheConfigUpdate,
) -> Result<(), String> {
    let mut cache = cache_manager.lock().await;
    let mut current_config = cache.config.clone();
    
    // Apply updates
    if let Some(max_size_mb) = config_update.max_size_mb {
        current_config.max_size_mb = max_size_mb;
    }
    if let Some(max_entries) = config_update.max_entries {
        current_config.max_entries = max_entries;
    }
    if let Some(enable_http_cache) = config_update.enable_http_cache {
        current_config.enable_http_cache = enable_http_cache;
    }
    if let Some(enable_file_cache) = config_update.enable_file_cache {
        current_config.enable_file_cache = enable_file_cache;
    }
    if let Some(cleanup_interval_seconds) = config_update.cleanup_interval_seconds {
        current_config.cleanup_interval = std::time::Duration::from_secs(cleanup_interval_seconds);
    }
    
    cache.update_config(current_config)
        .await
        .map_err(|e| e.to_string())
}

/// Clear all cached data
#[tauri::command]
pub async fn clear_cache(
    cache_manager: State<'_, CacheManagerState>,
) -> Result<(), String> {
    let cache = cache_manager.lock().await;
    cache.clear_all().await.map_err(|e| e.to_string())
}

/// Force cleanup of expired entries
#[tauri::command]
pub async fn cleanup_cache(
    cache_manager: State<'_, CacheManagerState>,
) -> Result<u64, String> {
    let cache = cache_manager.lock().await;
    cache.cleanup_expired().await.map_err(|e| e.to_string())
}

/// Cache a specific URL response
#[tauri::command]
pub async fn cache_url_response(
    cache_manager: State<'_, CacheManagerState>,
    url: String,
) -> Result<Vec<u8>, String> {
    let cache = cache_manager.lock().await;
    
    // Create HTTP client and fetch response
    let client = reqwest::Client::new();
    let response = client.get(&url)
        .send()
        .await
        .map_err(|e| format!("Failed to fetch URL: {}", e))?;
    
    cache.cache_http_response(&url, response)
        .await
        .map_err(|e| e.to_string())
}

/// Get cached data by key
#[tauri::command]
pub async fn get_cached_data(
    cache_manager: State<'_, CacheManagerState>,
    key: String,
) -> Result<Option<Vec<u8>>, String> {
    let cache = cache_manager.lock().await;
    cache.get(&key).await.map_err(|e| e.to_string())
}

/// Store data in cache with optional TTL
#[tauri::command]
pub async fn store_in_cache(
    cache_manager: State<'_, CacheManagerState>,
    key: String,
    data: Vec<u8>,
    ttl_seconds: Option<u64>,
) -> Result<(), String> {
    let cache = cache_manager.lock().await;
    let ttl = ttl_seconds.map(std::time::Duration::from_secs);
    cache.put(key, data, ttl).await.map_err(|e| e.to_string())
}

/// Get cache usage recommendations based on current performance
#[tauri::command]
pub async fn get_cache_recommendations(
    cache_manager: State<'_, CacheManagerState>,
) -> Result<Vec<String>, String> {
    let cache = cache_manager.lock().await;
    let stats = cache.get_stats().await;
    let mut recommendations = Vec::new();
    
    // Analyze cache performance and provide recommendations
    if stats.hit_ratio < 0.3 {
        recommendations.push("Low cache hit ratio detected. Consider increasing cache size or TTL values.".to_string());
    }
    
    if stats.memory_usage_mb > 400.0 {
        recommendations.push("High memory usage detected. Consider reducing cache size limit.".to_string());
    }
    
    if stats.eviction_count > stats.total_entries {
        recommendations.push("High eviction rate detected. Consider increasing max entries limit.".to_string());
    }
    
    if stats.hit_ratio > 0.8 && stats.memory_usage_mb < 100.0 {
        recommendations.push("Excellent cache performance! You could potentially increase cache size for even better performance.".to_string());
    }
    
    if recommendations.is_empty() {
        recommendations.push("Cache performance is optimal.".to_string());
    }
    
    Ok(recommendations)
}

/// Export cache performance metrics for analysis
#[tauri::command]
pub async fn export_cache_metrics(
    cache_manager: State<'_, CacheManagerState>,
) -> Result<String, String> {
    let cache = cache_manager.lock().await;
    let stats = cache.get_stats().await;
    
    let metrics = serde_json::json!({
        "timestamp": chrono::Utc::now().to_rfc3339(),
        "cache_stats": stats,
        "cache_config": cache.config,
        "performance_analysis": {
            "efficiency_score": stats.hit_ratio * 100.0,
            "memory_efficiency": if stats.memory_usage_mb > 0.0 { 
                stats.total_entries as f64 / stats.memory_usage_mb 
            } else { 
                0.0 
            },
            "turnover_rate": if stats.total_entries > 0 { 
                stats.eviction_count as f64 / stats.total_entries as f64 
            } else { 
                0.0 
            }
        }
    });
    
    serde_json::to_string_pretty(&metrics).map_err(|e| e.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cache_manager::CacheConfig;
    use std::path::PathBuf;
    
    async fn create_test_cache_manager() -> CacheManagerState {
        let mut config = CacheConfig::default();
        config.cache_directory = PathBuf::from("test_cache");
        
        let cache_manager = CacheManager::new(config).unwrap();
        Arc::new(Mutex::new(cache_manager))
    }
    
    #[tokio::test]
    async fn test_cache_commands() {
        let cache_manager = create_test_cache_manager().await;
        
        // Test storing and retrieving data
        let key = "test_key".to_string();
        let data = b"test_data".to_vec();
        
        store_in_cache(
            tauri::State::from(&cache_manager),
            key.clone(),
            data.clone(),
            None,
        ).await.unwrap();
        
        let retrieved = get_cached_data(
            tauri::State::from(&cache_manager),
            key,
        ).await.unwrap().unwrap();
        
        assert_eq!(retrieved, data);
        
        // Test stats
        let stats = get_cache_stats(tauri::State::from(&cache_manager)).await.unwrap();
        assert_eq!(stats.total_entries, 1);
        assert_eq!(stats.hit_count, 1);
    }
    
    #[tokio::test]
    async fn test_cache_config_update() {
        let cache_manager = create_test_cache_manager().await;
        
        let config_update = CacheConfigUpdate {
            max_size_mb: Some(1000),
            max_entries: Some(50000),
            enable_http_cache: Some(false),
            enable_file_cache: Some(true),
            cleanup_interval_seconds: Some(600),
        };
        
        update_cache_config(
            tauri::State::from(&cache_manager),
            config_update,
        ).await.unwrap();
        
        let updated_config = get_cache_config(tauri::State::from(&cache_manager)).await.unwrap();
        assert_eq!(updated_config.max_size_mb, 1000);
        assert_eq!(updated_config.max_entries, 50000);
        assert_eq!(updated_config.enable_http_cache, false);
        assert_eq!(updated_config.enable_file_cache, true);
    }
    
    #[tokio::test]
    async fn test_cache_recommendations() {
        let cache_manager = create_test_cache_manager().await;
        
        let recommendations = get_cache_recommendations(
            tauri::State::from(&cache_manager)
        ).await.unwrap();
        
        assert!(!recommendations.is_empty());
        assert!(recommendations[0].contains("optimal") || recommendations[0].contains("performance"));
    }
}
