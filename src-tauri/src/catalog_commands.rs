use tauri::{command, State};
use tokio::sync::Mutex;
use serde::{Serialize, Deserialize};
use std::process::Command;
use std::path::PathBuf;
use std::fs;
use std::io;
use std::collections::HashMap;
use uuid::Uuid;
use sha2::{Digest, Sha256};
use crate::database_commands::{DatabaseState, db_get_all_source_texts, PaginationParams};
use crate::models::{SourceText, SourceType};
use crate::file_system::{FileSystem, FileSystemConfig};

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
pub struct DuplicateCheckResult {
    is_duplicate: bool,
    existing_book_id: Option<String>,
    existing_book_title: Option<String>,
    similarity_score: Option<f64>,
    duplicate_type: Option<String>, // "checksum", "title_author", "isbn"
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeleteResult {
    success: bool,
    deleted_book_id: String,
    files_deleted: Vec<String>,
    message: String,
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

    pub async fn get_all_books(&self, database: &DatabaseState) -> Result<Vec<BookMetadata>, String> {
        // Get all source texts from database with no pagination limits
        let database_lock = database.lock().await;
        let repo = crate::repository::SourceTextRepository::new(database_lock.pool());
        
        match repo.get_all(None, None).await {
            Ok(source_texts) => {
                // Convert SourceText to BookMetadata
                let books: Vec<BookMetadata> = source_texts.into_iter().map(|source_text| {
                    BookMetadata {
                        id: source_text.id.to_string(),
                        title: source_text.title.clone(),
                        subtitle: None,
                        authors: vec![Author {
                            name: source_text.author.unwrap_or_else(|| "Unknown Author".to_string()),
                            role: None,
                            photo: None,
                        }],
                        publisher: None,
                        publication_year: 2024, // Default year for now
                        language: source_text.language.clone(),
                        original_language: None,
                        pages: source_text.metadata.page_count.map(|p| p as i32),
                        isbn: source_text.metadata.isbn.clone(),
                        categories: vec![],
                        subjects: vec![],
                        description: source_text.metadata.description.unwrap_or_else(|| "No description available".to_string()),
                        cover_image: None,
                        rating: None,
                        quality_score: None,
                        translations: None,
                        related_books: None,
                        series: None,
                        series_number: None,
                        enrichment_sources: None,
                        relationships: None,
                    }
                }).collect();
                
                Ok(books)
            }
            Err(e) => {
                eprintln!("Error fetching source texts: {}", e);
                Ok(vec![]) // Return empty vec on error to avoid breaking the UI
            }
        }
    }

    pub fn search_books(&self, _query: &str, _filters: &CatalogFilters, _sort_by: &str) -> Result<Vec<BookMetadata>, String> {
        // Return empty search results for new installations
        Ok(vec![])
    }

    pub async fn get_book_by_id(&self, book_id: &str, database: &DatabaseState) -> Result<Option<BookMetadata>, String> {
        let database_lock = database.lock().await;
        let repo = crate::repository::SourceTextRepository::new(database_lock.pool());
        
        let parsed_id = book_id.parse::<Uuid>().map_err(|_| "Invalid book ID format".to_string())?;
        
        match repo.get_by_id(parsed_id).await {
            Ok(source_text) => {
                let book_metadata = BookMetadata {
                    id: source_text.id.to_string(),
                    title: source_text.title.clone(),
                    subtitle: None,
                    authors: vec![Author {
                        name: source_text.author.unwrap_or_else(|| "Unknown Author".to_string()),
                        role: None,
                        photo: None,
                    }],
                    publisher: None,
                    publication_year: 2024, // Default year for now
                    language: source_text.language.clone(),
                    original_language: None,
                    pages: source_text.metadata.page_count.map(|p| p as i32),
                    isbn: source_text.metadata.isbn.clone(),
                    categories: vec![],
                    subjects: vec![],
                    description: source_text.metadata.description.unwrap_or_else(|| "No description available".to_string()),
                    cover_image: None,
                    rating: None,
                    quality_score: Some(75.0), // Default quality score
                    translations: None,
                    related_books: None,
                    series: None,
                    series_number: None,
                    enrichment_sources: None,
                    relationships: None,
                };
                Ok(Some(book_metadata))
            }
            Err(e) => Err(format!("Failed to get book: {}", e)),
        }
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

    pub async fn export_catalog(&self, format: &str, book_ids: &[String], database: &DatabaseState) -> Result<String, String> {
        let books = if book_ids.is_empty() {
            self.get_all_books(database).await?
        } else {
            // For specific book IDs, we'd need to implement individual lookups
            // For now, return empty list for specific IDs
            vec![]
        };

        // Basic export implementation
        match format {
            "json" => {
                serde_json::to_string_pretty(&books)
                    .map_err(|e| format!("JSON serialization error: {}", e))
            }
            "csv" => {
                let mut csv = "Title,Author,Language,Description\n".to_string();
                for book in books {
                    let author = book.authors.first()
                        .map(|a| a.name.clone())
                        .unwrap_or_else(|| "Unknown".to_string());
                    csv.push_str(&format!(
                        "\"{}\",\"{}\",\"{}\",\"{}\"\n",
                        book.title, author, book.language, book.description
                    ));
                }
                Ok(csv)
            }
            _ => Err(format!("Unsupported export format: {}", format))
        }
    }

    pub async fn get_catalog_stats(&self, database: &DatabaseState) -> Result<CatalogStats, String> {
        // Get real stats from database
        let database_lock = database.lock().await;
        let repo = crate::repository::SourceTextRepository::new(database_lock.pool());
        
        match repo.get_all(None, None).await {
            Ok(source_texts) => {
                let total_books = source_texts.len();
                let mut authors = std::collections::HashSet::new();
                let mut languages = std::collections::HashSet::new();
                
                for source_text in &source_texts {
                    if let Some(author) = &source_text.author {
                        authors.insert(author.clone());
                    }
                    languages.insert(source_text.language.clone());
                }
                
                Ok(CatalogStats {
                    total_books: total_books as i32,
                    total_authors: authors.len() as i32,
                    categories_count: 0,
                    languages_count: languages.len() as i32,
                    average_quality: 75.0, // Default quality score
                    books_with_covers: 0,
                    books_with_translations: 0,
                    recently_added: total_books as i32, // For now, all books are recently added
                })
            }
            Err(_) => {
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
        }
    }

    pub fn get_related_books(&self, _book_id: &str) -> Result<Vec<BookMetadata>, String> {
        // Return empty related books list for new installations
        Ok(vec![])
    }

    /// Calculate SHA256 checksum of a file
    fn calculate_file_checksum(&self, file_path: &str) -> Result<String, String> {
        let mut file = std::fs::File::open(file_path)
            .map_err(|e| format!("Failed to open file for checksum: {}", e))?;
        
        let mut hasher = Sha256::new();
        std::io::copy(&mut file, &mut hasher)
            .map_err(|e| format!("Failed to calculate checksum: {}", e))?;
        
        Ok(format!("{:x}", hasher.finalize()))
    }

    /// Check for duplicate books based on checksum, title+author, or ISBN
    pub async fn check_for_duplicates(&self, title: &str, author: Option<&str>, isbn: Option<&str>, file_path: Option<&str>, database: &DatabaseState) -> Result<DuplicateCheckResult, String> {
        let database_lock = database.lock().await;
        let repo = crate::repository::SourceTextRepository::new(database_lock.pool());
        
        // First check by file checksum if file provided
        if let Some(path) = file_path {
            if let Ok(checksum) = self.calculate_file_checksum(path) {
                if let Ok(existing_books) = repo.get_all(None, None).await {
                    for book in existing_books {
                        if let Some(existing_checksum) = &book.metadata.checksum {
                            if *existing_checksum == checksum {
                                return Ok(DuplicateCheckResult {
                                    is_duplicate: true,
                                    existing_book_id: Some(book.id.to_string()),
                                    existing_book_title: Some(book.title.clone()),
                                    similarity_score: Some(100.0),
                                    duplicate_type: Some("checksum".to_string()),
                                });
                            }
                        }
                    }
                }
            }
        }

        // Check by ISBN if provided
        if let Some(isbn_value) = isbn {
            if let Ok(existing_books) = repo.get_all(None, None).await {
                for book in existing_books {
                    if let Some(existing_isbn) = &book.metadata.isbn {
                        if *existing_isbn == isbn_value {
                            return Ok(DuplicateCheckResult {
                                is_duplicate: true,
                                existing_book_id: Some(book.id.to_string()),
                                existing_book_title: Some(book.title.clone()),
                                similarity_score: Some(95.0),
                                duplicate_type: Some("isbn".to_string()),
                            });
                        }
                    }
                }
            }
        }

        // Check by title and author combination
        if let Some(author_name) = author {
            if let Ok(existing_books) = repo.get_all(None, None).await {
                for book in existing_books {
                    let title_match = book.title.to_lowercase().trim() == title.to_lowercase().trim();
                    let author_match = book.author.as_ref()
                        .map(|a| a.to_lowercase().trim() == author_name.to_lowercase().trim())
                        .unwrap_or(false);
                    
                    if title_match && author_match {
                        return Ok(DuplicateCheckResult {
                            is_duplicate: true,
                            existing_book_id: Some(book.id.to_string()),
                            existing_book_title: Some(book.title.clone()),
                            similarity_score: Some(90.0),
                            duplicate_type: Some("title_author".to_string()),
                        });
                    }
                }
            }
        }

        Ok(DuplicateCheckResult {
            is_duplicate: false,
            existing_book_id: None,
            existing_book_title: None,
            similarity_score: None,
            duplicate_type: None,
        })
    }

    /// Delete a book and associated files
    pub async fn delete_book(&self, book_id: &str, app_data_dir: &str, database: &DatabaseState) -> Result<DeleteResult, String> {
        let database_lock = database.lock().await;
        let repo = crate::repository::SourceTextRepository::new(database_lock.pool());
        
        let parsed_id = book_id.parse::<Uuid>().map_err(|_| "Invalid book ID format".to_string())?;
        
        // Get the book first to retrieve file information
        let book = match repo.get_by_id(parsed_id).await {
            Ok(book) => book,
            Err(_) => return Err("Book not found".to_string()),
        };

        let mut deleted_files = Vec::new();
        
        // Delete associated files if they exist
        if let Some(file_path) = &book.file_path {
            let fs_config = FileSystemConfig::default();
            let mut file_system = FileSystem::new(fs_config)
                .map_err(|e| format!("Failed to initialize file system: {:?}", e))?;
            
            match file_system.delete_file(file_path) {
                Ok(_) => {
                    deleted_files.push(file_path.clone());
                }
                Err(e) => {
                    eprintln!("Failed to delete file {}: {:?}", file_path, e);
                    // Continue with database deletion even if file deletion fails
                }
            }
        }

        // Delete from database
        match repo.delete(parsed_id).await {
            Ok(_) => {
                Ok(DeleteResult {
                    success: true,
                    deleted_book_id: book_id.to_string(),
                    files_deleted: deleted_files.clone(),
                    message: format!("Successfully deleted book '{}' and {} associated files", book.title, deleted_files.len()),
                })
            }
            Err(e) => {
                Err(format!("Failed to delete book from database: {}", e))
            }
        }
    }
}

// Tauri Commands

#[command]
pub async fn get_all_books(
    catalog_manager: State<'_, Mutex<CatalogManager>>,
    database: State<'_, DatabaseState>
) -> Result<Vec<BookMetadata>, String> {
    let manager = catalog_manager.lock().await;
    manager.get_all_books(&database).await
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
    catalog_manager: State<'_, Mutex<CatalogManager>>,
    database: State<'_, DatabaseState>
) -> Result<Option<BookMetadata>, String> {
    let manager = catalog_manager.lock().await;
    manager.get_book_by_id(&book_id, &database).await
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
    catalog_manager: State<'_, Mutex<CatalogManager>>,
    database: State<'_, DatabaseState>
) -> Result<String, String> {
    let manager = catalog_manager.lock().await;
    manager.export_catalog(&format, &book_ids, &database).await
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
    catalog_manager: State<'_, Mutex<CatalogManager>>,
    database: State<'_, DatabaseState>
) -> Result<CatalogStats, String> {
    let manager = catalog_manager.lock().await;
    manager.get_catalog_stats(&database).await
}

#[command]
pub async fn generate_catalog_report(
    catalog_manager: State<'_, Mutex<CatalogManager>>,
    database: State<'_, DatabaseState>
) -> Result<String, String> {
    let manager = catalog_manager.lock().await;
    
    // Generate a comprehensive catalog report
    let stats = manager.get_catalog_stats(&database).await?;
    let books = manager.get_all_books(&database).await?;
    
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

#[command]
pub async fn check_for_duplicates(
    title: String,
    author: Option<String>,
    isbn: Option<String>,
    file_path: Option<String>,
    catalog_manager: State<'_, Mutex<CatalogManager>>,
    database: State<'_, DatabaseState>
) -> Result<DuplicateCheckResult, String> {
    let manager = catalog_manager.lock().await;
    manager.check_for_duplicates(
        &title,
        author.as_deref(),
        isbn.as_deref(),
        file_path.as_deref(),
        &database
    ).await
}

#[command]
pub async fn delete_book(
    book_id: String,
    app_data_dir: String,
    catalog_manager: State<'_, Mutex<CatalogManager>>,
    database: State<'_, DatabaseState>
) -> Result<DeleteResult, String> {
    let manager = catalog_manager.lock().await;
    manager.delete_book(&book_id, &app_data_dir, &database).await
}
