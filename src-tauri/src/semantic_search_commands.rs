use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use tauri::State;
use uuid::Uuid;
use crate::python_manager::{PythonManager, PythonManagerState, PythonManagerError};
use log::{info, warn, error};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SemanticSearchConfig {
    pub semantic_model: String,
    pub use_semantic_similarity: bool,
    pub similarity_threshold: f64,
    pub use_fuzzy_matching: bool,
    pub fuzzy_threshold: f64,
    pub max_results: u32,
    pub boost_exact_matches: bool,
    pub boost_title_matches: f64,
    pub boost_author_matches: f64,
    pub enable_cache: bool,
}

impl Default for SemanticSearchConfig {
    fn default() -> Self {
        Self {
            semantic_model: "all-MiniLM-L6-v2".to_string(),
            use_semantic_similarity: true,
            similarity_threshold: 0.7,
            use_fuzzy_matching: true,
            fuzzy_threshold: 0.8,
            max_results: 50,
            boost_exact_matches: true,
            boost_title_matches: 2.0,
            boost_author_matches: 1.5,
            enable_cache: true,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchQuery {
    pub text: String,
    pub filters: HashMap<String, serde_json::Value>,
    pub facets: Vec<String>,
    pub sort_by: String,
    pub sort_order: String,
    pub limit: u32,
    pub offset: u32,
}

impl Default for SearchQuery {
    fn default() -> Self {
        Self {
            text: String::new(),
            filters: HashMap::new(),
            facets: Vec::new(),
            sort_by: "relevance".to_string(),
            sort_order: "desc".to_string(),
            limit: 20,
            offset: 0,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResult {
    pub id: String,
    pub title: String,
    pub author: String,
    pub content: String,
    pub metadata: HashMap<String, serde_json::Value>,
    pub relevance_score: f64,
    pub match_type: String,
    pub highlighted_fields: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchFacet {
    pub name: String,
    pub values: Vec<(String, u32)>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResponse {
    pub results: Vec<SearchResult>,
    pub total_count: u32,
    pub facets: Vec<SearchFacet>,
    pub query_time_ms: u32,
    pub suggestions: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DocumentIndex {
    pub id: String,
    pub title: String,
    pub author: String,
    pub description: String,
    pub content: String,
    pub categories: Vec<String>,
    pub subjects: Vec<String>,
    pub keywords: Vec<String>,
    pub metadata: HashMap<String, serde_json::Value>,
}

pub struct SemanticSearchEngine {
    config: SemanticSearchConfig,
    python_manager: std::sync::Arc<tokio::sync::Mutex<PythonManager>>,
    is_initialized: bool,
}

impl SemanticSearchEngine {
    pub fn new(
        config: SemanticSearchConfig,
        python_manager: std::sync::Arc<tokio::sync::Mutex<PythonManager>>,
    ) -> Self {
        Self {
            config,
            python_manager,
            is_initialized: false,
        }
    }

    /// Initialize the search engine with Python backend
    pub async fn initialize(&mut self) -> Result<(), PythonManagerError> {
        info!("Initializing semantic search engine...");

        let python_code = format!(
            r#"
import sys
import json
from pathlib import Path

# Add processors path
processors_path = Path("processors")
if processors_path.exists():
    sys.path.insert(0, str(processors_path.absolute()))

try:
    from semantic_search import SemanticSearchEngine, SearchConfig
    
    # Initialize search engine with config
    config = SearchConfig(
        semantic_model="{}",
        use_semantic_similarity={},
        similarity_threshold={},
        use_fuzzy_matching={},
        fuzzy_threshold={},
        max_results={},
        boost_exact_matches={},
        boost_title_matches={},
        boost_author_matches={},
        enable_cache={}
    )
    
    # Create global search engine instance
    search_engine = SemanticSearchEngine(config)
    
    print(json.dumps({{"status": "success", "message": "Search engine initialized"}}))
    
except ImportError as e:
    print(json.dumps({{"status": "error", "message": f"Import error: {{str(e)}}"}}))
except Exception as e:
    print(json.dumps({{"status": "error", "message": f"Initialization error: {{str(e)}}"}}))
"#,
            self.config.semantic_model,
            self.config.use_semantic_similarity,
            self.config.similarity_threshold,
            self.config.use_fuzzy_matching,
            self.config.fuzzy_threshold,
            self.config.max_results,
            self.config.boost_exact_matches,
            self.config.boost_title_matches,
            self.config.boost_author_matches,
            self.config.enable_cache
        );

        let python_manager = self.python_manager.lock().await;
        let result = python_manager.execute_code(&python_code).await?;

        if !result.success {
            error!("Failed to initialize search engine: {}", result.stderr);
            return Err(PythonManagerError::ProcessExecutionFailed(result.stderr));
        }

        // Parse result
        let response: serde_json::Value = serde_json::from_str(&result.stdout)
            .map_err(|e| PythonManagerError::ProcessExecutionFailed(format!("Failed to parse response: {}", e)))?;

        if response.get("status").and_then(|s| s.as_str()) != Some("success") {
            let error_msg = response.get("message").and_then(|m| m.as_str()).unwrap_or("Unknown error");
            return Err(PythonManagerError::ProcessExecutionFailed(error_msg.to_string()));
        }

        self.is_initialized = true;
        info!("Semantic search engine initialized successfully");
        Ok(())
    }

    /// Index documents for searching
    pub async fn index_documents(&self, documents: Vec<DocumentIndex>) -> Result<(), PythonManagerError> {
        if !self.is_initialized {
            return Err(PythonManagerError::ProcessExecutionFailed("Search engine not initialized".to_string()));
        }

        info!("Indexing {} documents...", documents.len());

        let documents_json = serde_json::to_string(&documents)
            .map_err(|e| PythonManagerError::ProcessExecutionFailed(format!("Failed to serialize documents: {}", e)))?;

        let python_code = format!(
            r#"
import sys
import json
from pathlib import Path

# Add processors path
processors_path = Path("processors")
if processors_path.exists():
    sys.path.insert(0, str(processors_path.absolute()))

try:
    from semantic_search import SemanticSearchEngine, SearchConfig
    
    # Initialize search engine (should reuse existing one in production)
    config = SearchConfig()
    search_engine = SemanticSearchEngine(config)
    
    # Load documents
    documents = {}
    
    # Index documents
    search_engine.index_documents(documents)
    
    print(json.dumps({{"status": "success", "indexed_count": len(documents)}}))
    
except Exception as e:
    print(json.dumps({{"status": "error", "message": f"Indexing error: {{str(e)}}"}}))
"#,
            documents_json.replace("\"", "\\\"")
        );

        let python_manager = self.python_manager.lock().await;
        let result = python_manager.execute_code(&python_code).await?;

        if !result.success {
            error!("Failed to index documents: {}", result.stderr);
            return Err(PythonManagerError::ProcessExecutionFailed(result.stderr));
        }

        // Parse result
        let response: serde_json::Value = serde_json::from_str(&result.stdout)
            .map_err(|e| PythonManagerError::ProcessExecutionFailed(format!("Failed to parse response: {}", e)))?;

        if response.get("status").and_then(|s| s.as_str()) != Some("success") {
            let error_msg = response.get("message").and_then(|m| m.as_str()).unwrap_or("Unknown error");
            return Err(PythonManagerError::ProcessExecutionFailed(error_msg.to_string()));
        }

        let indexed_count = response.get("indexed_count").and_then(|c| c.as_u64()).unwrap_or(0);
        info!("Successfully indexed {} documents", indexed_count);
        Ok(())
    }

    /// Perform semantic search
    pub async fn search(&self, query: SearchQuery) -> Result<SearchResponse, PythonManagerError> {
        if !self.is_initialized {
            return Err(PythonManagerError::ProcessExecutionFailed("Search engine not initialized".to_string()));
        }

        let query_json = serde_json::to_string(&query)
            .map_err(|e| PythonManagerError::ProcessExecutionFailed(format!("Failed to serialize query: {}", e)))?;

        let python_code = format!(
            r#"
import sys
import json
from pathlib import Path

# Add processors path
processors_path = Path("processors")
if processors_path.exists():
    sys.path.insert(0, str(processors_path.absolute()))

try:
    from semantic_search import SemanticSearchEngine, SearchConfig, SearchQuery
    
    # Initialize search engine (should reuse existing one in production)
    config = SearchConfig()
    search_engine = SemanticSearchEngine(config)
    
    # Parse query
    query_data = {}
    
    # Create search query object
    search_query = SearchQuery(
        text=query_data.get("text", ""),
        filters=query_data.get("filters", {{}}),
        facets=query_data.get("facets", []),
        sort_by=query_data.get("sort_by", "relevance"),
        sort_order=query_data.get("sort_order", "desc"),
        limit=query_data.get("limit", 20),
        offset=query_data.get("offset", 0)
    )
    
    # Perform search
    search_response = search_engine.search(search_query)
    
    # Convert response to dict for JSON serialization
    response_dict = {{
        "results": [
            {{
                "id": result.id,
                "title": result.title,
                "author": result.author,
                "content": result.content,
                "metadata": result.metadata,
                "relevance_score": result.relevance_score,
                "match_type": result.match_type,
                "highlighted_fields": result.highlighted_fields
            }}
            for result in search_response.results
        ],
        "total_count": search_response.total_count,
        "facets": [
            {{
                "name": facet.name,
                "values": facet.values
            }}
            for facet in search_response.facets
        ],
        "query_time_ms": search_response.query_time_ms,
        "suggestions": search_response.suggestions
    }}
    
    print(json.dumps(response_dict))
    
except Exception as e:
    print(json.dumps({{"status": "error", "message": f"Search error: {{str(e)}}"}}))
"#,
            query_json.replace("\"", "\\\"")
        );

        let python_manager = self.python_manager.lock().await;
        let result = python_manager.execute_code(&python_code).await?;

        if !result.success {
            error!("Search failed: {}", result.stderr);
            return Err(PythonManagerError::ProcessExecutionFailed(result.stderr));
        }

        // Parse result
        let response: serde_json::Value = serde_json::from_str(&result.stdout)
            .map_err(|e| PythonManagerError::ProcessExecutionFailed(format!("Failed to parse search response: {}", e)))?;

        // Check for error in response
        if let Some(error_msg) = response.get("message").and_then(|m| m.as_str()) {
            if response.get("status").and_then(|s| s.as_str()) == Some("error") {
                return Err(PythonManagerError::ProcessExecutionFailed(error_msg.to_string()));
            }
        }

        // Convert to SearchResponse
        let search_response: SearchResponse = serde_json::from_value(response)
            .map_err(|e| PythonManagerError::ProcessExecutionFailed(format!("Failed to deserialize search response: {}", e)))?;

        Ok(search_response)
    }

    /// Get search engine statistics
    pub async fn get_statistics(&self) -> Result<HashMap<String, serde_json::Value>, PythonManagerError> {
        if !self.is_initialized {
            return Err(PythonManagerError::ProcessExecutionFailed("Search engine not initialized".to_string()));
        }

        let python_code = r#"
import sys
import json
from pathlib import Path

# Add processors path
processors_path = Path("processors")
if processors_path.exists():
    sys.path.insert(0, str(processors_path.absolute()))

try:
    from semantic_search import SemanticSearchEngine, SearchConfig
    
    # Initialize search engine (should reuse existing one in production)
    config = SearchConfig()
    search_engine = SemanticSearchEngine(config)
    
    # Get statistics
    stats = search_engine.get_statistics()
    
    print(json.dumps(stats))
    
except Exception as e:
    print(json.dumps({"status": "error", "message": f"Statistics error: {str(e)}"}))
"#;

        let python_manager = self.python_manager.lock().await;
        let result = python_manager.execute_code(python_code).await?;

        if !result.success {
            error!("Failed to get statistics: {}", result.stderr);
            return Err(PythonManagerError::ProcessExecutionFailed(result.stderr));
        }

        // Parse result
        let response: HashMap<String, serde_json::Value> = serde_json::from_str(&result.stdout)
            .map_err(|e| PythonManagerError::ProcessExecutionFailed(format!("Failed to parse statistics: {}", e)))?;

        Ok(response)
    }
}

// Global search engine state
pub type SemanticSearchState = std::sync::Arc<tokio::sync::Mutex<SemanticSearchEngine>>;

/// Tauri commands for semantic search

#[tauri::command]
pub async fn initialize_semantic_search(
    config: Option<SemanticSearchConfig>,
    search_state: State<'_, SemanticSearchState>,
) -> Result<(), String> {
    let mut search_engine = search_state.lock().await;
    search_engine.initialize().await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn index_documents_for_search(
    documents: Vec<DocumentIndex>,
    search_state: State<'_, SemanticSearchState>,
) -> Result<(), String> {
    let search_engine = search_state.lock().await;
    search_engine.index_documents(documents).await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn semantic_search(
    query: SearchQuery,
    search_state: State<'_, SemanticSearchState>,
) -> Result<SearchResponse, String> {
    let search_engine = search_state.lock().await;
    search_engine.search(query).await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_search_statistics(
    search_state: State<'_, SemanticSearchState>,
) -> Result<HashMap<String, serde_json::Value>, String> {
    let search_engine = search_state.lock().await;
    search_engine.get_statistics().await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn quick_search(
    query_text: String,
    limit: Option<u32>,
    search_state: State<'_, SemanticSearchState>,
) -> Result<SearchResponse, String> {
    let search_query = SearchQuery {
        text: query_text,
        limit: limit.unwrap_or(10),
        ..Default::default()
    };

    let search_engine = search_state.lock().await;
    search_engine.search(search_query).await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn faceted_search(
    query_text: String,
    filters: HashMap<String, serde_json::Value>,
    facets: Vec<String>,
    search_state: State<'_, SemanticSearchState>,
) -> Result<SearchResponse, String> {
    let search_query = SearchQuery {
        text: query_text,
        filters,
        facets,
        ..Default::default()
    };

    let search_engine = search_state.lock().await;
    search_engine.search(search_query).await.map_err(|e| e.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tokio_test;

    #[tokio::test]
    async fn test_search_config_default() {
        let config = SemanticSearchConfig::default();
        assert_eq!(config.semantic_model, "all-MiniLM-L6-v2");
        assert!(config.use_semantic_similarity);
        assert_eq!(config.similarity_threshold, 0.7);
    }

    #[tokio::test]
    async fn test_search_query_default() {
        let query = SearchQuery::default();
        assert_eq!(query.sort_by, "relevance");
        assert_eq!(query.sort_order, "desc");
        assert_eq!(query.limit, 20);
        assert_eq!(query.offset, 0);
    }
}
