use tauri::command;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::fs;
use tokio::process::Command;
use sha2::{Sha256, Digest};
use std::io::Read;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AssetMetadata {
    pub asset_id: String,
    pub asset_type: String,
    pub source_url: Option<String>,
    pub local_path: Option<String>,
    pub width: Option<u32>,
    pub height: Option<u32>,
    pub file_size: Option<u64>,
    pub format: Option<String>,
    pub quality: Option<String>,
    pub checksum: Option<String>,
    pub download_date: Option<String>,
    pub last_accessed: Option<String>,
    pub cache_expires: Option<String>,
    pub fallback_used: bool,
    pub error_count: i32,
    pub last_error: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AssetCollection {
    pub entity_id: String,
    pub entity_type: String,
    pub assets: HashMap<String, Vec<AssetMetadata>>,
    pub primary_cover: Option<String>,
    pub primary_author_photo: Option<String>,
    pub created_date: String,
    pub updated_date: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CoverImageRequest {
    pub book_id: String,
    pub title: String,
    pub authors: Vec<String>,
    pub isbn: Option<String>,
    pub preferred_size: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CoverImageResponse {
    pub success: bool,
    pub asset_metadata: Option<AssetMetadata>,
    pub local_path: Option<String>,
    pub fallback_used: bool,
    pub error: Option<String>,
}

/// Get the visual assets directory path
fn get_assets_directory() -> Result<PathBuf, String> {
    let app_data_dir = dirs::document_dir()
        .ok_or_else(|| "Could not find documents directory".to_string())?
        .join("Lexicon")
        .join("assets");
    
    // Create directory if it doesn't exist
    if !app_data_dir.exists() {
        fs::create_dir_all(&app_data_dir)
            .map_err(|e| format!("Failed to create assets directory: {}", e))?;
    }
    
    Ok(app_data_dir)
}

/// Generate a fallback cover image for a book
fn generate_fallback_cover(book_id: &str, title: &str, authors: &[String]) -> Result<PathBuf, String> {
    let assets_dir = get_assets_directory()?;
    let fallback_path = assets_dir.join(format!("fallback_cover_{}.svg", book_id));
    
    // Create a simple SVG cover with title and author
    let author_text = if !authors.is_empty() {
        authors.join(", ")
    } else {
        "Unknown Author".to_string()
    };
    
    let svg_content = format!(r#"
<svg width="400" height="600" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="coverGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#4f46e5;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#7c3aed;stop-opacity:1" />
        </linearGradient>
    </defs>
    <rect width="100%" height="100%" fill="url(#coverGradient)"/>
    <rect x="20" y="20" width="360" height="560" fill="none" stroke="white" stroke-width="2" opacity="0.5"/>
    
    <!-- Book Title -->
    <foreignObject x="40" y="100" width="320" height="300">
        <div xmlns="http://www.w3.org/1999/xhtml" style="
            color: white; 
            font-family: 'Georgia', serif; 
            font-size: 24px; 
            font-weight: bold; 
            text-align: center; 
            line-height: 1.3;
            padding: 20px;
            word-wrap: break-word;
        ">
            {}
        </div>
    </foreignObject>
    
    <!-- Author -->
    <text x="200" y="480" text-anchor="middle" fill="white" 
          font-family="Arial, sans-serif" font-size="18" opacity="0.9">
        {}
    </text>
    
    <!-- Lexicon Branding -->
    <text x="200" y="550" text-anchor="middle" fill="white" 
          font-family="Arial, sans-serif" font-size="12" opacity="0.7">
        Processed with Lexicon
    </text>
</svg>
"#, title, author_text);
    
    fs::write(&fallback_path, svg_content)
        .map_err(|e| format!("Failed to create fallback cover: {}", e))?;
    
    Ok(fallback_path)
}

/// Calculate SHA256 checksum of a file
fn calculate_checksum(file_path: &Path) -> Result<String, String> {
    let mut file = fs::File::open(file_path)
        .map_err(|e| format!("Failed to open file: {}", e))?;
    
    let mut hasher = Sha256::new();
    let mut buffer = [0; 8192];
    
    loop {
        let bytes_read = file.read(&mut buffer)
            .map_err(|e| format!("Failed to read file: {}", e))?;
        
        if bytes_read == 0 {
            break;
        }
        
        hasher.update(&buffer[..bytes_read]);
    }
    
    Ok(format!("{:x}", hasher.finalize()))
}

#[command]
pub async fn get_book_cover(request: CoverImageRequest) -> Result<CoverImageResponse, String> {
    println!("Getting cover for book: {} - {}", request.book_id, request.title);
    
    let assets_dir = get_assets_directory()?;
    let covers_dir = assets_dir.join("covers");
    
    if !covers_dir.exists() {
        fs::create_dir_all(&covers_dir)
            .map_err(|e| format!("Failed to create covers directory: {}", e))?;
    }
    
    // Check if we already have a cover for this book
    let cover_pattern = format!("cover_{}.*", request.book_id);
    let existing_covers: Vec<_> = fs::read_dir(&covers_dir)
        .map_err(|e| format!("Failed to read covers directory: {}", e))?
        .filter_map(|entry| entry.ok())
        .filter(|entry| {
            entry.file_name().to_string_lossy().starts_with(&format!("cover_{}", request.book_id))
        })
        .collect();
    
    if let Some(existing_cover) = existing_covers.first() {
        let existing_path = existing_cover.path();
        let checksum = calculate_checksum(&existing_path).ok();
        
        let metadata = AssetMetadata {
            asset_id: format!("cover_{}", request.book_id),
            asset_type: "cover_image".to_string(),
            source_url: None,
            local_path: Some(existing_path.to_string_lossy().to_string()),
            width: None,
            height: None,
            file_size: existing_path.metadata().ok().map(|m| m.len()),
            format: existing_path.extension().and_then(|e| e.to_str()).map(|s| s.to_string()),
            quality: Some("original".to_string()),
            checksum,
            download_date: None,
            last_accessed: Some(chrono::Utc::now().to_rfc3339()),
            cache_expires: None,
            fallback_used: false,
            error_count: 0,
            last_error: None,
        };
        
        return Ok(CoverImageResponse {
            success: true,
            asset_metadata: Some(metadata),
            local_path: Some(existing_path.to_string_lossy().to_string()),
            fallback_used: false,
            error: None,
        });
    }
    
    // Try to download cover from external sources (Google Books, Open Library, etc.)
    let downloaded_cover = try_download_cover(&request).await;
    
    match downloaded_cover {
        Ok(Some((path, metadata))) => {
            Ok(CoverImageResponse {
                success: true,
                asset_metadata: Some(metadata),
                local_path: Some(path.to_string_lossy().to_string()),
                fallback_used: false,
                error: None,
            })
        },
        Ok(None) | Err(_) => {
            // Generate fallback cover
            let fallback_path = generate_fallback_cover(&request.book_id, &request.title, &request.authors)?;
            let checksum = calculate_checksum(&fallback_path).ok();
            
            let metadata = AssetMetadata {
                asset_id: format!("cover_{}_fallback", request.book_id),
                asset_type: "cover_image".to_string(),
                source_url: None,
                local_path: Some(fallback_path.to_string_lossy().to_string()),
                width: Some(400),
                height: Some(600),
                file_size: fallback_path.metadata().ok().map(|m| m.len()),
                format: Some("svg".to_string()),
                quality: Some("fallback".to_string()),
                checksum,
                download_date: Some(chrono::Utc::now().to_rfc3339()),
                last_accessed: Some(chrono::Utc::now().to_rfc3339()),
                cache_expires: None,
                fallback_used: true,
                error_count: 0,
                last_error: None,
            };
            
            Ok(CoverImageResponse {
                success: true,
                asset_metadata: Some(metadata),
                local_path: Some(fallback_path.to_string_lossy().to_string()),
                fallback_used: true,
                error: None,
            })
        }
    }
}

async fn try_download_cover(request: &CoverImageRequest) -> Result<Option<(PathBuf, AssetMetadata)>, String> {
    // Try Python visual asset manager integration
    let python_result = call_python_visual_manager(request).await;
    
    if let Ok(Some(result)) = python_result {
        return Ok(Some(result));
    }
    
    // Fallback to direct API calls if Python integration fails
    try_direct_api_download(request).await
}

async fn call_python_visual_manager(request: &CoverImageRequest) -> Result<Option<(PathBuf, AssetMetadata)>, String> {
    let python_script = r#"
import sys
import json
import asyncio
from pathlib import Path

# Add the python-engine directory to sys.path
import os
script_dir = Path(__file__).parent
python_engine_dir = script_dir / "../../python-engine"
sys.path.insert(0, str(python_engine_dir.resolve()))

try:
    from enrichment.visual_asset_manager import VisualAssetManager, AssetType, AssetQuality
    
    async def download_cover(book_data):
        manager = VisualAssetManager()
        
        # Try to download cover
        result = await manager.download_book_cover(
            book_id=book_data['book_id'],
            title=book_data['title'],
            authors=book_data['authors'],
            isbn=book_data.get('isbn'),
            preferred_quality=AssetQuality.MEDIUM
        )
        
        if result:
            return {
                'success': True,
                'local_path': str(result.local_path) if result.local_path else None,
                'asset_metadata': {
                    'asset_id': result.asset_id,
                    'asset_type': result.asset_type.value,
                    'source_url': result.source_url,
                    'local_path': str(result.local_path) if result.local_path else None,
                    'width': result.width,
                    'height': result.height,
                    'file_size': result.file_size,
                    'format': result.format,
                    'quality': result.quality.value if result.quality else None,
                    'checksum': result.checksum,
                    'fallback_used': result.fallback_used
                }
            }
        else:
            return {'success': False}
    
    if __name__ == "__main__":
        book_data = json.loads(sys.argv[1])
        result = asyncio.run(download_cover(book_data))
        print(json.dumps(result))
        
except Exception as e:
    print(json.dumps({'success': False, 'error': str(e)}))
"#;
    
    // Write temporary Python script
    let temp_dir = std::env::temp_dir();
    let script_path = temp_dir.join("download_cover.py");
    fs::write(&script_path, python_script)
        .map_err(|e| format!("Failed to write Python script: {}", e))?;
    
    // Prepare request data
    let request_json = serde_json::to_string(&serde_json::json!({
        "book_id": request.book_id,
        "title": request.title,
        "authors": request.authors,
        "isbn": request.isbn
    })).map_err(|e| format!("Failed to serialize request: {}", e))?;
    
    // Execute Python script
    let output = Command::new("python3")
        .arg(&script_path)
        .arg(&request_json)
        .output()
        .await
        .map_err(|e| format!("Failed to execute Python script: {}", e))?;
    
    // Clean up temporary script
    let _ = fs::remove_file(&script_path);
    
    if !output.status.success() {
        return Err(format!("Python script failed: {}", String::from_utf8_lossy(&output.stderr)));
    }
    
    let result_str = String::from_utf8_lossy(&output.stdout);
    let result: serde_json::Value = serde_json::from_str(&result_str)
        .map_err(|e| format!("Failed to parse Python result: {}", e))?;
    
    if result["success"].as_bool().unwrap_or(false) {
        if let Some(local_path_str) = result["local_path"].as_str() {
            let local_path = PathBuf::from(local_path_str);
            
            if local_path.exists() {
                let asset_data = &result["asset_metadata"];
                let metadata = AssetMetadata {
                    asset_id: asset_data["asset_id"].as_str().unwrap_or("").to_string(),
                    asset_type: asset_data["asset_type"].as_str().unwrap_or("cover_image").to_string(),
                    source_url: asset_data["source_url"].as_str().map(|s| s.to_string()),
                    local_path: Some(local_path_str.to_string()),
                    width: asset_data["width"].as_u64().map(|w| w as u32),
                    height: asset_data["height"].as_u64().map(|h| h as u32),
                    file_size: asset_data["file_size"].as_u64(),
                    format: asset_data["format"].as_str().map(|s| s.to_string()),
                    quality: asset_data["quality"].as_str().map(|s| s.to_string()),
                    checksum: asset_data["checksum"].as_str().map(|s| s.to_string()),
                    download_date: Some(chrono::Utc::now().to_rfc3339()),
                    last_accessed: Some(chrono::Utc::now().to_rfc3339()),
                    cache_expires: None,
                    fallback_used: asset_data["fallback_used"].as_bool().unwrap_or(false),
                    error_count: 0,
                    last_error: None,
                };
                
                return Ok(Some((local_path, metadata)));
            }
        }
    }
    
    Ok(None)
}

async fn try_direct_api_download(_request: &CoverImageRequest) -> Result<Option<(PathBuf, AssetMetadata)>, String> {
    // For now, return None to fall back to generated covers
    // In a full implementation, this would try Google Books API, Open Library, etc.
    Ok(None)
}

#[command]
pub async fn get_asset_collection(entity_id: String, entity_type: String) -> Result<Option<AssetCollection>, String> {
    let assets_dir = get_assets_directory()?;
    let collections_dir = assets_dir.join("collections");
    
    if !collections_dir.exists() {
        return Ok(None);
    }
    
    let collection_file = collections_dir.join(format!("{}_{}.json", entity_type, entity_id));
    
    if !collection_file.exists() {
        return Ok(None);
    }
    
    let content = fs::read_to_string(&collection_file)
        .map_err(|e| format!("Failed to read collection file: {}", e))?;
    
    let collection: AssetCollection = serde_json::from_str(&content)
        .map_err(|e| format!("Failed to parse collection: {}", e))?;
    
    Ok(Some(collection))
}

#[command]
pub async fn save_asset_collection(collection: AssetCollection) -> Result<bool, String> {
    let assets_dir = get_assets_directory()?;
    let collections_dir = assets_dir.join("collections");
    
    if !collections_dir.exists() {
        fs::create_dir_all(&collections_dir)
            .map_err(|e| format!("Failed to create collections directory: {}", e))?;
    }
    
    let collection_file = collections_dir.join(format!("{}_{}.json", collection.entity_type, collection.entity_id));
    
    let content = serde_json::to_string_pretty(&collection)
        .map_err(|e| format!("Failed to serialize collection: {}", e))?;
    
    fs::write(&collection_file, content)
        .map_err(|e| format!("Failed to write collection file: {}", e))?;
    
    Ok(true)
}

#[command]
pub async fn get_all_asset_collections() -> Result<Vec<AssetCollection>, String> {
    let assets_dir = get_assets_directory()?;
    let collections_dir = assets_dir.join("collections");
    
    if !collections_dir.exists() {
        return Ok(vec![]);
    }
    
    let mut collections = Vec::new();
    
    for entry in fs::read_dir(&collections_dir)
        .map_err(|e| format!("Failed to read collections directory: {}", e))? 
    {
        let entry = entry.map_err(|e| format!("Failed to read directory entry: {}", e))?;
        let path = entry.path();
        
        if path.is_file() && path.extension().map_or(false, |ext| ext == "json") {
            if let Ok(content) = fs::read_to_string(&path) {
                if let Ok(collection) = serde_json::from_str::<AssetCollection>(&content) {
                    collections.push(collection);
                }
            }
        }
    }
    
    Ok(collections)
}

#[command]
pub async fn cleanup_unused_assets() -> Result<i32, String> {
    let assets_dir = get_assets_directory()?;
    let mut cleaned_count = 0;
    
    // Get all asset collections to find referenced assets
    let collections = get_all_asset_collections().await?;
    let mut referenced_paths = std::collections::HashSet::new();
    
    for collection in collections {
        for asset_list in collection.assets.values() {
            for asset in asset_list {
                if let Some(path) = &asset.local_path {
                    referenced_paths.insert(PathBuf::from(path));
                }
            }
        }
    }
    
    // Check covers directory for orphaned files
    let covers_dir = assets_dir.join("covers");
    if covers_dir.exists() {
        for entry in fs::read_dir(&covers_dir)
            .map_err(|e| format!("Failed to read covers directory: {}", e))? 
        {
            let entry = entry.map_err(|e| format!("Failed to read directory entry: {}", e))?;
            let path = entry.path();
            
            if path.is_file() && !referenced_paths.contains(&path) {
                // Check if file is older than 7 days and unreferenced
                if let Ok(metadata) = path.metadata() {
                    if let Ok(modified) = metadata.modified() {
                        let age = std::time::SystemTime::now()
                            .duration_since(modified)
                            .unwrap_or(std::time::Duration::from_secs(0));
                        
                        if age > std::time::Duration::from_secs(7 * 24 * 60 * 60) {
                            if fs::remove_file(&path).is_ok() {
                                cleaned_count += 1;
                            }
                        }
                    }
                }
            }
        }
    }
    
    Ok(cleaned_count)
}
