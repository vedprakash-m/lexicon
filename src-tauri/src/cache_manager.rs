use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::Arc;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::sync::RwLock;
use serde::{Deserialize, Serialize};
use anyhow::{Result, anyhow};
use reqwest::Response;
use sha2::{Sha256, Digest};

/// Cache entry with expiration and metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CacheEntry {
    pub key: String,
    pub data: Vec<u8>,
    pub content_type: Option<String>,
    pub created_at: u64,
    pub expires_at: Option<u64>,
    pub access_count: u64,
    pub last_accessed: u64,
    pub size_bytes: usize,
}

impl CacheEntry {
    pub fn new(key: String, data: Vec<u8>, ttl: Option<Duration>) -> Self {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        let expires_at = ttl.map(|duration| now + duration.as_secs());
        let size_bytes = data.len();
        
        Self {
            key,
            data,
            content_type: None,
            created_at: now,
            expires_at,
            access_count: 0,
            last_accessed: now,
            size_bytes,
        }
    }
    
    pub fn is_expired(&self) -> bool {
        if let Some(expires_at) = self.expires_at {
            let now = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_secs();
            now > expires_at
        } else {
            false
        }
    }
    
    pub fn mark_accessed(&mut self) {
        self.access_count += 1;
        self.last_accessed = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
    }
}

/// Cache configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CacheConfig {
    pub max_size_mb: u64,
    pub max_entries: u64,
    pub default_ttl: Option<Duration>,
    pub enable_http_cache: bool,
    pub enable_file_cache: bool,
    pub cache_directory: PathBuf,
    pub cleanup_interval: Duration,
}

impl Default for CacheConfig {
    fn default() -> Self {
        Self {
            max_size_mb: 500, // 500MB default
            max_entries: 10000,
            default_ttl: Some(Duration::from_secs(3600)), // 1 hour
            enable_http_cache: true,
            enable_file_cache: true,
            cache_directory: PathBuf::from("cache"),
            cleanup_interval: Duration::from_secs(300), // 5 minutes
        }
    }
}

/// Cache statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CacheStats {
    pub total_entries: u64,
    pub total_size_bytes: u64,
    pub hit_count: u64,
    pub miss_count: u64,
    pub eviction_count: u64,
    pub expired_count: u64,
    pub hit_ratio: f64,
    pub memory_usage_mb: f64,
}

/// Intelligent caching system with LRU eviction and size management
pub struct CacheManager {
    config: CacheConfig,
    entries: Arc<RwLock<HashMap<String, CacheEntry>>>,
    stats: Arc<RwLock<CacheStats>>,
    http_client: reqwest::Client,
}

impl CacheManager {
    pub fn new(config: CacheConfig) -> Result<Self> {
        // Ensure cache directory exists
        std::fs::create_dir_all(&config.cache_directory)?;
        
        let http_client = reqwest::Client::builder()
            .timeout(Duration::from_secs(30))
            .build()?;
        
        Ok(Self {
            config,
            entries: Arc::new(RwLock::new(HashMap::new())),
            stats: Arc::new(RwLock::new(CacheStats {
                total_entries: 0,
                total_size_bytes: 0,
                hit_count: 0,
                miss_count: 0,
                eviction_count: 0,
                expired_count: 0,
                hit_ratio: 0.0,
                memory_usage_mb: 0.0,
            })),
            http_client,
        })
    }
    
    /// Generate cache key from URL or content
    pub fn generate_key(input: &str) -> String {
        let mut hasher = Sha256::new();
        hasher.update(input.as_bytes());
        format!("{:x}", hasher.finalize())
    }
    
    /// Get cached data
    pub async fn get(&self, key: &str) -> Result<Option<Vec<u8>>> {
        let mut entries = self.entries.write().await;
        let mut stats = self.stats.write().await;
        
        if let Some(entry) = entries.get_mut(key) {
            if entry.is_expired() {
                entries.remove(key);
                stats.expired_count += 1;
                stats.miss_count += 1;
                Ok(None)
            } else {
                entry.mark_accessed();
                stats.hit_count += 1;
                self.update_hit_ratio(&mut stats).await;
                Ok(Some(entry.data.clone()))
            }
        } else {
            stats.miss_count += 1;
            self.update_hit_ratio(&mut stats).await;
            Ok(None)
        }
    }
    
    /// Store data in cache
    pub async fn put(&self, key: String, data: Vec<u8>, ttl: Option<Duration>) -> Result<()> {
        let mut entries = self.entries.write().await;
        let mut stats = self.stats.write().await;
        
        // Check if we need to evict entries
        self.maybe_evict(&mut entries, &mut stats, data.len()).await?;
        
        let entry = CacheEntry::new(key.clone(), data, ttl.or(self.config.default_ttl));
        let entry_size = entry.size_bytes;
        
        entries.insert(key, entry);
        stats.total_entries += 1;
        stats.total_size_bytes += entry_size as u64;
        stats.memory_usage_mb = stats.total_size_bytes as f64 / (1024.0 * 1024.0);
        
        Ok(())
    }
    
    /// Cache HTTP response
    pub async fn cache_http_response(&self, url: &str, response: Response) -> Result<Vec<u8>> {
        if !self.config.enable_http_cache {
            return Ok(response.bytes().await?.to_vec());
        }
        
        let cache_key = Self::generate_key(url);
        
        // Check if already cached
        if let Some(cached_data) = self.get(&cache_key).await? {
            return Ok(cached_data);
        }
        
        // Cache the response
        let data = response.bytes().await?.to_vec();
        self.put(cache_key, data.clone(), None).await?;
        
        Ok(data)
    }
    
    /// Cache file content
    pub async fn cache_file(&self, file_path: &PathBuf) -> Result<Vec<u8>> {
        if !self.config.enable_file_cache {
            return tokio::fs::read(file_path).await.map_err(Into::into);
        }
        
        let cache_key = Self::generate_key(&file_path.to_string_lossy());
        
        // Check if already cached
        if let Some(cached_data) = self.get(&cache_key).await? {
            return Ok(cached_data);
        }
        
        // Read and cache the file
        let data = tokio::fs::read(file_path).await?;
        self.put(cache_key, data.clone(), None).await?;
        
        Ok(data)
    }
    
    /// Remove expired entries
    pub async fn cleanup_expired(&self) -> Result<u64> {
        let mut entries = self.entries.write().await;
        let mut stats = self.stats.write().await;
        
        let mut removed_count = 0;
        let mut removed_size = 0;
        
        entries.retain(|_key, entry| {
            if entry.is_expired() {
                removed_count += 1;
                removed_size += entry.size_bytes;
                false
            } else {
                true
            }
        });
        
        stats.expired_count += removed_count;
        stats.total_entries -= removed_count;
        stats.total_size_bytes -= removed_size as u64;
        stats.memory_usage_mb = stats.total_size_bytes as f64 / (1024.0 * 1024.0);
        
        Ok(removed_count)
    }
    
    /// Clear all cache entries
    pub async fn clear_all(&self) -> Result<()> {
        let mut entries = self.entries.write().await;
        let mut stats = self.stats.write().await;
        
        entries.clear();
        *stats = CacheStats {
            total_entries: 0,
            total_size_bytes: 0,
            hit_count: stats.hit_count,
            miss_count: stats.miss_count,
            eviction_count: stats.eviction_count,
            expired_count: stats.expired_count,
            hit_ratio: stats.hit_ratio,
            memory_usage_mb: 0.0,
        };
        
        Ok(())
    }
    
    /// Get cache statistics
    pub async fn get_stats(&self) -> CacheStats {
        self.stats.read().await.clone()
    }
    
    /// Get current cache configuration
    pub fn get_config(&self) -> CacheConfig {
        self.config.clone()
    }
    
    /// Update cache configuration
    pub async fn update_config(&mut self, new_config: CacheConfig) -> Result<()> {
        self.config = new_config;
        
        // Ensure new cache directory exists
        std::fs::create_dir_all(&self.config.cache_directory)?;
        
        // If size limits changed, may need to evict
        let mut entries = self.entries.write().await;
        let mut stats = self.stats.write().await;
        self.maybe_evict(&mut entries, &mut stats, 0).await?;
        
        Ok(())
    }
    
    /// Evict entries using LRU strategy if necessary
    async fn maybe_evict(
        &self,
        entries: &mut HashMap<String, CacheEntry>,
        stats: &mut CacheStats,
        additional_size: usize,
    ) -> Result<()> {
        let max_size_bytes = self.config.max_size_mb * 1024 * 1024;
        let current_size = stats.total_size_bytes + additional_size as u64;
        
        if current_size <= max_size_bytes && entries.len() < self.config.max_entries as usize {
            return Ok(());
        }
        
        // Collect entries sorted by last accessed time (LRU)
        let mut entries_by_access: Vec<_> = entries.iter().map(|(k, v)| (k.clone(), v.clone())).collect();
        entries_by_access.sort_by_key(|(_, entry)| entry.last_accessed);
        
        let mut evicted_count = 0;
        let mut evicted_size = 0;
        let mut keys_to_remove = Vec::new();
        
        // Collect keys to evict until we're under limits
        for (key, entry) in entries_by_access {
            if stats.total_size_bytes <= max_size_bytes / 2 
                && entries.len() <= self.config.max_entries as usize / 2 {
                break;
            }
            
            evicted_size += entry.size_bytes;
            evicted_count += 1;
            keys_to_remove.push(key);
        }
        
        // Remove the keys
        for key in keys_to_remove {
            entries.remove(&key);
        }
        
        stats.eviction_count += evicted_count;
        stats.total_entries -= evicted_count;
        stats.total_size_bytes -= evicted_size as u64;
        stats.memory_usage_mb = stats.total_size_bytes as f64 / (1024.0 * 1024.0);
        
        Ok(())
    }
    
    /// Update hit ratio statistics
    async fn update_hit_ratio(&self, stats: &mut CacheStats) {
        let total_requests = stats.hit_count + stats.miss_count;
        if total_requests > 0 {
            stats.hit_ratio = stats.hit_count as f64 / total_requests as f64;
        }
    }
    
    /// Start background cleanup task
    pub async fn start_cleanup_task(cache: Arc<CacheManager>) {
        let cleanup_interval = cache.config.cleanup_interval;
        
        tokio::spawn(async move {
            let mut interval = tokio::time::interval(cleanup_interval);
            
            loop {
                interval.tick().await;
                
                if let Err(e) = cache.cleanup_expired().await {
                    log::error!("Cache cleanup failed: {}", e);
                }
            }
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tokio::time::{sleep, Duration};
    
    #[tokio::test]
    async fn test_cache_basic_operations() {
        let config = CacheConfig::default();
        let cache = CacheManager::new(config).unwrap();
        
        let key = "test_key".to_string();
        let data = b"test_data".to_vec();
        
        // Initially empty
        assert!(cache.get(&key).await.unwrap().is_none());
        
        // Store data
        cache.put(key.clone(), data.clone(), None).await.unwrap();
        
        // Retrieve data
        let retrieved = cache.get(&key).await.unwrap().unwrap();
        assert_eq!(retrieved, data);
        
        // Check stats
        let stats = cache.get_stats().await;
        assert_eq!(stats.total_entries, 1);
        assert_eq!(stats.hit_count, 1);
        assert_eq!(stats.miss_count, 1);
    }
    
    #[tokio::test]
    async fn test_cache_expiration() {
        let config = CacheConfig::default();
        let cache = CacheManager::new(config).unwrap();
        
        let key = "expiry_test".to_string();
        let data = b"expiry_data".to_vec();
        let ttl = Duration::from_millis(100);
        
        // Store with short TTL
        cache.put(key.clone(), data.clone(), Some(ttl)).await.unwrap();
        
        // Should be available immediately
        assert!(cache.get(&key).await.unwrap().is_some());
        
        // Wait for expiration
        sleep(Duration::from_millis(150)).await;
        
        // Should be expired
        assert!(cache.get(&key).await.unwrap().is_none());
    }
    
    #[tokio::test]
    async fn test_cache_size_limits() {
        let mut config = CacheConfig::default();
        config.max_size_mb = 1; // 1MB limit
        config.max_entries = 2;
        
        let cache = CacheManager::new(config).unwrap();
        
        // Add entries that exceed limits
        let large_data = vec![0u8; 1024 * 1024]; // 1MB
        
        cache.put("key1".to_string(), large_data.clone(), None).await.unwrap();
        cache.put("key2".to_string(), large_data.clone(), None).await.unwrap();
        
        // Should trigger eviction when adding third
        cache.put("key3".to_string(), large_data, None).await.unwrap();
        
        let stats = cache.get_stats().await;
        assert!(stats.eviction_count > 0);
    }
}
