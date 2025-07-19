use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use scraper::{Html, Selector};
use tauri::State;
use tokio::sync::Mutex;

#[derive(Debug, Serialize, Deserialize)]
pub struct SelectorTestResult {
    pub success: bool,
    pub element: Option<ElementInfo>,
    pub content: Option<String>,
    pub error: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ElementInfo {
    pub tag_name: String,
    pub text_content: Option<String>,
    pub attributes: HashMap<String, String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ExtractionRule {
    pub name: String,
    pub selectors: HashMap<String, SelectorInfo>,
    pub wait_conditions: Option<Vec<String>>,
    pub transformations: Option<HashMap<String, String>>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SelectorInfo {
    pub name: String,
    pub selector: String,
    pub fallback_selectors: Option<Vec<String>>,
    pub transform: Option<String>,
    pub required: bool,
    pub description: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ValidationResult {
    pub success: bool,
    pub extracted: Option<HashMap<String, String>>,
    pub error: Option<String>,
}

// Scraping state management
pub struct ScrapingState {
    pub cached_pages: Mutex<HashMap<String, String>>,
}

impl Default for ScrapingState {
    fn default() -> Self {
        Self {
            cached_pages: Mutex::new(HashMap::new()),
        }
    }
}

#[tauri::command]
pub async fn validate_selector_urls(urls: Vec<String>) -> Result<bool, String> {
    for url in urls {
        if url::Url::parse(&url).is_err() {
            return Ok(false);
        }
    }
    Ok(true)
}

#[tauri::command]
pub async fn scrape_url_for_selector_testing(
    url: String,
    config: Option<HashMap<String, String>>,
) -> Result<serde_json::Value, String> {
    let client = reqwest::Client::builder()
        .user_agent(
            config
                .as_ref()
                .and_then(|c| c.get("userAgent"))
                .map_or("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36", |v| v.as_str())
        )
        .timeout(std::time::Duration::from_secs(30))
        .build()
        .map_err(|e| format!("Failed to create HTTP client: {}", e))?;

    let response = client
        .get(&url)
        .send()
        .await
        .map_err(|e| format!("Failed to fetch URL: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("HTTP error: {}", response.status()));
    }

    let content = response
        .text()
        .await
        .map_err(|e| format!("Failed to get response text: {}", e))?;

    Ok(serde_json::json!({
        "success": true,
        "content": content,
        "url": url
    }))
}

#[tauri::command]
pub async fn test_css_selector(
    url: String,
    selector: String,
    field: String,
    state: State<'_, ScrapingState>,
) -> Result<SelectorTestResult, String> {
    // Check if we have cached content for this URL
    let cached_content = {
        let cache = state.cached_pages.lock().await;
        cache.get(&url).cloned()
    };

    let html_content = match cached_content {
        Some(content) => content,
        None => {
            // Scrape the URL
            let scrape_result = scrape_url_for_selector_testing(url.clone(), None).await?;
            let content = scrape_result["content"]
                .as_str()
                .ok_or("Failed to get content from scrape result")?
                .to_string();

            // Cache the content
            {
                let mut cache = state.cached_pages.lock().await;
                cache.insert(url, content.clone());
            }
            content
        }
    };

    // Parse the HTML
    let document = Html::parse_document(&html_content);
    
    // Try to parse the CSS selector
    let css_selector = match Selector::parse(&selector) {
        Ok(sel) => sel,
        Err(e) => {
            return Ok(SelectorTestResult {
                success: false,
                element: None,
                content: None,
                error: Some(format!("Invalid CSS selector: {}", e)),
            });
        }
    };

    // Find the first matching element
    if let Some(element) = document.select(&css_selector).next() {
        let tag_name = element.value().name().to_string();
        let text_content = element.text().collect::<Vec<_>>().join(" ");
        
        // Get attributes
        let mut attributes = HashMap::new();
        for (attr_name, attr_value) in element.value().attrs() {
            attributes.insert(attr_name.to_string(), attr_value.to_string());
        }

        let content = match field.as_str() {
            "image" => {
                // For images, try to get the src attribute
                attributes.get("src").cloned().unwrap_or(text_content.clone())
            }
            "date" => {
                // For dates, try datetime attribute first, then text
                attributes.get("datetime").cloned().unwrap_or(text_content.clone())
            }
            _ => text_content.clone()
        };

        Ok(SelectorTestResult {
            success: true,
            element: Some(ElementInfo {
                tag_name,
                text_content: Some(text_content),
                attributes,
            }),
            content: Some(content),
            error: None,
        })
    } else {
        Ok(SelectorTestResult {
            success: false,
            element: None,
            content: None,
            error: Some("No element found matching the selector".to_string()),
        })
    }
}

#[tauri::command]
pub async fn validate_extraction_rule(
    url: String,
    rule: ExtractionRule,
    state: State<'_, ScrapingState>,
) -> Result<ValidationResult, String> {
    let mut extracted = HashMap::new();
    let mut errors = Vec::new();

    for (field_name, selector_info) in rule.selectors {
        // Test the primary selector
        let test_result = test_css_selector(
            url.clone(),
            selector_info.selector.clone(),
            field_name.clone(),
            state.clone(),
        ).await?;

        if test_result.success {
            if let Some(content) = test_result.content {
                extracted.insert(field_name, content);
            }
        } else {
            // Try fallback selectors if available
            let mut found_with_fallback = false;
            if let Some(fallbacks) = selector_info.fallback_selectors {
                for fallback in fallbacks {
                    let fallback_result = test_css_selector(
                        url.clone(),
                        fallback,
                        field_name.clone(),
                        state.clone(),
                    ).await?;

                    if fallback_result.success {
                        if let Some(content) = fallback_result.content {
                            extracted.insert(field_name.clone(), content);
                            found_with_fallback = true;
                            break;
                        }
                    }
                }
            }

            if !found_with_fallback && selector_info.required {
                errors.push(format!(
                    "Required field '{}' not found with selector '{}'",
                    field_name, selector_info.selector
                ));
            }
        }
    }

    if errors.is_empty() {
        Ok(ValidationResult {
            success: true,
            extracted: Some(extracted),
            error: None,
        })
    } else {
        Ok(ValidationResult {
            success: false,
            extracted: None,
            error: Some(errors.join("; ")),
        })
    }
}
