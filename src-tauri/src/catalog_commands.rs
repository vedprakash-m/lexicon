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
        // First try to load from enrichment demo results
        let demo_results_path = self.python_engine_path.join("enrichment/enrichment_demo_results.json");
        
        if demo_results_path.exists() {
            match fs::read_to_string(&demo_results_path) {
                Ok(content) => {
                    match serde_json::from_str::<Vec<BookMetadata>>(&content) {
                        Ok(books) => return Ok(books),
                        Err(e) => eprintln!("Failed to parse demo results: {}", e),
                    }
                }
                Err(e) => eprintln!("Failed to read demo results: {}", e),
            }
        }

        // Fallback to demo data generation
        self.execute_python_script("enrichment/demo_metadata_enrichment.py", &[])
            .and_then(|_| {
                match fs::read_to_string(&demo_results_path) {
                    Ok(content) => {
                        serde_json::from_str::<Vec<BookMetadata>>(&content)
                            .map_err(|e| format!("Failed to parse generated results: {}", e))
                    }
                    Err(e) => Err(format!("Failed to read generated results: {}", e))
                }
            })
    }

    pub fn search_books(&self, query: &str, filters: &CatalogFilters, sort_by: &str) -> Result<Vec<BookMetadata>, String> {
        let all_books = self.get_all_books()?;
        
        let mut filtered_books: Vec<BookMetadata> = all_books.into_iter()
            .filter(|book| {
                // Text search
                let query_lower = query.to_lowercase();
                let matches_query = query.is_empty() || 
                    book.title.to_lowercase().contains(&query_lower) ||
                    book.authors.iter().any(|a| a.name.to_lowercase().contains(&query_lower)) ||
                    book.description.to_lowercase().contains(&query_lower) ||
                    book.subjects.iter().any(|s| s.to_lowercase().contains(&query_lower));

                if !matches_query {
                    return false;
                }

                // Category filter
                if let Some(category) = &filters.category {
                    if !book.categories.contains(category) {
                        return false;
                    }
                }

                // Author filter
                if let Some(author) = &filters.author {
                    let author_lower = author.to_lowercase();
                    if !book.authors.iter().any(|a| a.name.to_lowercase().contains(&author_lower)) {
                        return false;
                    }
                }

                // Language filter
                if let Some(language) = &filters.language {
                    if &book.language != language {
                        return false;
                    }
                }

                // Year range filter
                if let Some(year_range) = &filters.year_range {
                    if book.publication_year < year_range[0] || book.publication_year > year_range[1] {
                        return false;
                    }
                }

                // Translations filter
                if let Some(has_translations) = filters.has_translations {
                    let book_has_translations = book.translations.as_ref().map_or(false, |t| !t.is_empty());
                    if has_translations && !book_has_translations {
                        return false;
                    }
                }

                // Cover filter
                if let Some(has_cover) = filters.has_cover {
                    let book_has_cover = book.cover_image.is_some();
                    if has_cover && !book_has_cover {
                        return false;
                    }
                }

                // Quality filter
                if let Some(min_quality) = filters.min_quality {
                    if book.quality_score.unwrap_or(0.0) < min_quality {
                        return false;
                    }
                }

                // Rating filter
                if let Some(min_rating) = filters.min_rating {
                    if book.rating.unwrap_or(0.0) < min_rating {
                        return false;
                    }
                }

                true
            })
            .collect();

        // Sort results
        match sort_by {
            "title" => filtered_books.sort_by(|a, b| a.title.cmp(&b.title)),
            "author" => filtered_books.sort_by(|a, b| {
                let a_author = a.authors.first().map(|a| a.name.as_str()).unwrap_or("");
                let b_author = b.authors.first().map(|a| a.name.as_str()).unwrap_or("");
                a_author.cmp(b_author)
            }),
            "year" => filtered_books.sort_by(|a, b| b.publication_year.cmp(&a.publication_year)),
            "rating" => filtered_books.sort_by(|a, b| {
                let a_rating = a.rating.unwrap_or(0.0);
                let b_rating = b.rating.unwrap_or(0.0);
                b_rating.partial_cmp(&a_rating).unwrap_or(std::cmp::Ordering::Equal)
            }),
            "quality" => filtered_books.sort_by(|a, b| {
                let a_quality = a.quality_score.unwrap_or(0.0);
                let b_quality = b.quality_score.unwrap_or(0.0);
                b_quality.partial_cmp(&a_quality).unwrap_or(std::cmp::Ordering::Equal)
            }),
            _ => {} // Default order
        }

        Ok(filtered_books)
    }

    pub fn get_book_by_id(&self, book_id: &str) -> Result<Option<BookMetadata>, String> {
        let all_books = self.get_all_books()?;
        Ok(all_books.into_iter().find(|book| book.id == book_id))
    }

    pub fn enrich_book(&self, book_id: &str, _sources: &[String]) -> Result<EnrichmentResult, String> {
        // Run metadata enrichment for specific book
        let args: Vec<&str> = vec!["--book-id", book_id];
        
        match self.execute_python_script("enrichment/metadata_enrichment.py", &args) {
            Ok(_) => Ok(EnrichmentResult {
                book_id: book_id.to_string(),
                success: true,
                added_fields: vec!["metadata".to_string(), "relationships".to_string()],
                errors: None,
            }),
            Err(e) => Ok(EnrichmentResult {
                book_id: book_id.to_string(),
                success: false,
                added_fields: vec![],
                errors: Some(vec![e]),
            })
        }
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
        let books = self.get_all_books()?;
        
        let total_books = books.len() as i32;
        let mut authors = std::collections::HashSet::new();
        let mut categories = std::collections::HashSet::new();
        let mut languages = std::collections::HashSet::new();
        let mut total_quality = 0.0;
        let mut quality_count = 0;
        let mut books_with_covers = 0;
        let mut books_with_translations = 0;

        for book in &books {
            for author in &book.authors {
                authors.insert(&author.name);
            }
            for category in &book.categories {
                categories.insert(category);
            }
            languages.insert(&book.language);

            if let Some(quality) = book.quality_score {
                total_quality += quality;
                quality_count += 1;
            }

            if book.cover_image.is_some() {
                books_with_covers += 1;
            }

            if book.translations.as_ref().map_or(false, |t| !t.is_empty()) {
                books_with_translations += 1;
            }
        }

        Ok(CatalogStats {
            total_books,
            total_authors: authors.len() as i32,
            categories_count: categories.len() as i32,
            languages_count: languages.len() as i32,
            average_quality: if quality_count > 0 { total_quality / quality_count as f64 } else { 0.0 },
            books_with_covers,
            books_with_translations,
            recently_added: 0, // Would need timestamp tracking
        })
    }

    pub fn get_related_books(&self, book_id: &str) -> Result<Vec<BookMetadata>, String> {
        let all_books = self.get_all_books()?;
        
        // Find relationships first without borrowing all_books
        let mut related_ids = Vec::new();
        if let Some(book) = all_books.iter().find(|b| b.id == book_id) {
            if let Some(relationships) = &book.relationships {
                related_ids = relationships.iter()
                    .map(|r| r.book_id.clone())
                    .collect();
            }
        }
        
        // Now filter the books
        let related_books: Vec<BookMetadata> = all_books.into_iter()
            .filter(|b| related_ids.contains(&b.id))
            .collect();
        
        Ok(related_books)
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
