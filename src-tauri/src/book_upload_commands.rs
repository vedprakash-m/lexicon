use tauri::{command, State};
use tokio::sync::Mutex;
use serde::{Serialize, Deserialize};
use uuid::Uuid;
use chrono::Utc;
use std::path::Path;

use crate::models::{SourceText, TextMetadata, SourceType, ProcessingStatus};
use crate::database_commands::{DatabaseState, create_source_text};

#[derive(Debug, Serialize, Deserialize)]
pub struct UploadBookRequest {
    pub file_name: String,
    pub file_path: String,
    pub file_size: u64,
    pub title: Option<String>,
    pub author: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct UploadBookResponse {
    pub success: bool,
    pub source_text_id: Option<String>,
    pub message: String,
}

#[command]
pub async fn upload_book_from_file(
    upload_request: UploadBookRequest,
    database: State<'_, DatabaseState>
) -> Result<UploadBookResponse, String> {
    // Extract metadata from file
    let file_extension = Path::new(&upload_request.file_name)
        .extension()
        .and_then(|ext| ext.to_str())
        .unwrap_or("")
        .to_lowercase();

    let source_type = match file_extension.as_str() {
        "pdf" => SourceType::PDF,
        "epub" => SourceType::Epub,
        "mobi" => SourceType::Book,
        "txt" => SourceType::PlainText,
        _ => SourceType::Book,
    };

    // Create source text
    let source_text = SourceText {
        id: Uuid::new_v4(),
        title: upload_request.title.unwrap_or_else(|| {
            // Remove extension from file name for title
            Path::new(&upload_request.file_name)
                .file_stem()
                .and_then(|stem| stem.to_str())
                .unwrap_or(&upload_request.file_name)
                .to_string()
        }),
        author: upload_request.author,
        language: "en".to_string(), // Default to English
        source_type,
        file_path: Some(upload_request.file_path.clone()),
        url: None,
        metadata: TextMetadata {
            word_count: None,
            character_count: None,
            page_count: None,
            isbn: None,
            publisher: None,
            publication_date: None,
            genre: None,
            tags: Vec::new(),
            description: None,
            encoding: Some("UTF-8".to_string()),
            file_size_bytes: Some(upload_request.file_size),
            checksum: None,
            custom_fields: std::collections::HashMap::new(),
        },
        processing_status: ProcessingStatus::Pending,
        created_at: Utc::now(),
        updated_at: Utc::now(),
    };

    // Save to database
    match create_source_text(source_text.clone(), database).await {
        Ok(_) => Ok(UploadBookResponse {
            success: true,
            source_text_id: Some(source_text.id.to_string()),
            message: format!("Successfully added book: {}", source_text.title),
        }),
        Err(e) => Ok(UploadBookResponse {
            success: false,
            source_text_id: None,
            message: format!("Failed to add book: {}", e),
        }),
    }
}

#[command]
pub async fn upload_multiple_books(
    upload_requests: Vec<UploadBookRequest>,
    database: State<'_, DatabaseState>
) -> Result<Vec<UploadBookResponse>, String> {
    let mut responses = Vec::new();
    
    for request in upload_requests {
        match upload_book_from_file(request, database.clone()).await {
            Ok(response) => responses.push(response),
            Err(e) => responses.push(UploadBookResponse {
                success: false,
                source_text_id: None,
                message: e,
            }),
        }
    }
    
    Ok(responses)
}
