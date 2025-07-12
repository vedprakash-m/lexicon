use tauri::{command, State};
use tokio::sync::Mutex;
use serde::{Serialize, Deserialize};
use std::process::Command;
use std::path::PathBuf;
use std::fs;
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Author {
    name: String,
    role: Option<String>,
    photo: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Publisher {
    name: String,
    logo: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Relationship {
    #[serde(rename = "type")]
    relationship_type: String,
    book_id: String,
    confidence: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BookMetadata {
    id: String,
    title: String,
    subtitle: Option<String>,
    authors: Vec<Author>,
    publisher: Option<Publisher>,
    publication_year: i32,
    language: String,
    original_language: Option<String>,
    pages: Option<i32>,
    isbn: Option<String>,
    categories: Vec<String>,
    subjects: Vec<String>,
    description: String,
    cover_image: Option<String>,
    rating: Option<f64>,
    quality_score: Option<f64>,
    translations: Option<Vec<String>>,
    related_books: Option<Vec<String>>,
    series: Option<String>,
    series_number: Option<i32>,
    enrichment_sources: Option<Vec<String>>,
    relationships: Option<Vec<Relationship>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CatalogFilters {
    category: Option<String>,
    author: Option<String>,
    language: Option<String>,
    year_range: Option<[i32; 2]>,
    has_translations: Option<bool>,
    has_cover: Option<bool>,
    min_quality: Option<f64>,
    min_rating: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CatalogStats {
    total_books: i32,
    total_authors: i32,
    categories_count: i32,
    languages_count: i32,
    average_quality: f64,
    books_with_covers: i32,
    books_with_translations: i32,
    recently_added: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnrichmentResult {
    book_id: String,
    success: bool,
    added_fields: Vec<String>,
    errors: Option<Vec<String>>,
}

pub struct CatalogManager {
    python_engine_path: PathBuf,
    cache: HashMap<String, BookMetadata>,
    last_updated: Option<std::time::SystemTime>,
}

impl CatalogManager {
    pub fn new(app_data_dir: PathBuf) -> Self {
        Self {
            python_engine_path: app_data_dir.join("python-engine"),
            cache: HashMap::new(),
            last_updated: None,
        }
    }

    fn execute_python_script(&self, script_name: &str, args: &[&str]) -> Result<String, String> {
        let script_path = self.python_engine_path.join(script_name);
        
        if !script_path.exists() {
            return Err(format!("Script not found: {:?}", script_path));
        }

        let output = Command::new("python3")
            .arg(&script_path)
            .args(args)
            .current_dir(&self.python_engine_path)
            .output()
            .map_err(|e| format!("Failed to execute script: {}", e))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(format!("Script execution failed: {}", stderr));
        }

        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    }

    pub fn get_all_books(&self) -> Result<Vec<BookMetadata>, String> {
        // Return empty catalog for new installations
        Ok(vec![])
    }

    pub fn search_books(&self, _query: &str, _filters: &CatalogFilters, _sort_by: &str) -> Result<Vec<BookMetadata>, String> {
        // Return empty search results for new installations
        Ok(vec![])
    }

    pub fn get_book_by_id(&self, _book_id: &str) -> Result<Option<BookMetadata>, String> {
        // Return None for new installations (no books in catalog)
        Ok(None)
    }

    pub fn enrich_book(&self, book_id: &str, _sources: &[String]) -> Result<EnrichmentResult, String> {
        // Enrichment functionality disabled for new installations
        Ok(EnrichmentResult {
            book_id: book_id.to_string(),
            success: false,
            added_fields: vec![],
            errors: Some(vec!["Enrichment functionality not available".to_string()]),
        })
    }

    pub fn export_catalog(&self, format: &str, book_ids: &[String]) -> Result<String, String> {
        let books = if book_ids.is_empty() {
            self.get_all_books()?
        } else {
            book_ids.iter()
                .filter_map(|id| self.get_book_by_id(id).ok().flatten())
                .collect()
        };

        match format {
            "json" => serde_json::to_string_pretty(&books)
                .map_err(|e| format!("Failed to serialize to JSON: {}", e)),
            _ => Err(format!("Unsupported format: {}", format))
        }
    }

    pub fn get_catalog_stats(&self) -> Result<CatalogStats, String> {
        // Return empty stats for new installations
        Ok(CatalogStats {
            total_books: 0,
            total_authors: 0,
            categories_count: 0,
            languages_count: 0,
            average_quality: 0.0,
            books_with_covers: 0,
            books_with_translations: 0,
            recently_added: 0,
        })
    }

    pub fn get_related_books(&self, _book_id: &str) -> Result<Vec<BookMetadata>, String> {
        // Return empty related books list for new installations
        Ok(vec![])
    }
}

// Tauri Commands

#[command]
pub async fn get_all_books(
    catalog_manager: State<'_, Mutex<CatalogManager>>
) -> Result<Vec<BookMetadata>, String> {
    let manager = catalog_manager.lock().await;
    manager.get_all_books()
}

#[command]
pub async fn search_catalog(
    query: String,
    filters: CatalogFilters,
    sort_by: String,
    sort_order: String,
    page: i32,
    limit: i32,
    catalog_manager: State<'_, Mutex<CatalogManager>>
) -> Result<Vec<BookMetadata>, String> {
    let manager = catalog_manager.lock().await;
    let mut results = manager.search_books(&query, &filters, &sort_by)?;
    
    // Apply pagination
    let start = ((page - 1) * limit) as usize;
    let end = (start + limit as usize).min(results.len());
    
    if start < results.len() {
        results = results.into_iter().skip(start).take(end - start).collect();
    } else {
        results.clear();
    }
    
    Ok(results)
}

#[command]
pub async fn get_book_by_id(
    book_id: String,
    catalog_manager: State<'_, Mutex<CatalogManager>>
) -> Result<Option<BookMetadata>, String> {
    let manager = catalog_manager.lock().await;
    manager.get_book_by_id(&book_id)
}

#[command]
pub async fn enrich_book_metadata(
    book_id: String,
    sources: Vec<String>,
    catalog_manager: State<'_, Mutex<CatalogManager>>
) -> Result<EnrichmentResult, String> {
    let manager = catalog_manager.lock().await;
    manager.enrich_book(&book_id, &sources)
}

#[command]
pub async fn export_catalog(
    format: String,
    book_ids: Vec<String>,
    catalog_manager: State<'_, Mutex<CatalogManager>>
) -> Result<String, String> {
    let manager = catalog_manager.lock().await;
    manager.export_catalog(&format, &book_ids)
}

#[command]
pub async fn get_related_books(
    book_id: String,
    catalog_manager: State<'_, Mutex<CatalogManager>>
) -> Result<Vec<BookMetadata>, String> {
    let manager = catalog_manager.lock().await;
    manager.get_related_books(&book_id)
}

#[command]
pub async fn get_catalog_stats(
    catalog_manager: State<'_, Mutex<CatalogManager>>
) -> Result<CatalogStats, String> {
    let manager = catalog_manager.lock().await;
    manager.get_catalog_stats()
}

#[command]
pub async fn generate_catalog_report(
    catalog_manager: State<'_, Mutex<CatalogManager>>
) -> Result<String, String> {
    let manager = catalog_manager.lock().await;
    
    // Generate a comprehensive catalog report
    let stats = manager.get_catalog_stats()?;
    let books = manager.get_all_books()?;
    
    let report = format!(
        "# Lexicon Catalog Report\n\n\
        ## Statistics\n\
        - Total Books: {}\n\
        - Total Authors: {}\n\
        - Categories: {}\n\
        - Languages: {}\n\
        - Average Quality Score: {:.2}%\n\
        - Books with Cover Images: {}\n\
        - Books with Translations: {}\n\n\
        ## Books by Category\n",
        stats.total_books,
        stats.total_authors,
        stats.categories_count,
        stats.languages_count,
        stats.average_quality * 100.0,
        stats.books_with_covers,
        stats.books_with_translations
    );
    
    // Add category breakdown
    let mut category_counts = std::collections::HashMap::new();
    for book in &books {
        for category in &book.categories {
            *category_counts.entry(category.clone()).or_insert(0) += 1;
        }
    }
    
    let mut category_report = report;
    for (category, count) in category_counts {
        category_report.push_str(&format!("- {}: {} books\n", category, count));
    }
    
    Ok(category_report)
}
