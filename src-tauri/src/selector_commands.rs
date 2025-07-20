use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use scraper::{Html, Selector, ElementRef};
use tauri::State;
use tokio::sync::Mutex;
use std::time::Instant;

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

#[derive(Debug, Serialize, Deserialize)]
pub struct EnhancedElementInfo {
    pub tag: String,
    pub text: String,
    pub attributes: HashMap<String, String>,
    pub position: ElementPosition,
    pub xpath: String,
    pub css_path: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ElementPosition {
    pub x: f64,
    pub y: f64,
    pub width: f64,
    pub height: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PerformanceMetrics {
    pub execution_time_ms: u64,
    pub selector_complexity: String,
    pub suggestions: Option<Vec<String>>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AccessibilityMetrics {
    pub has_aria_labels: bool,
    pub has_alt_text: bool,
    pub color_contrast_ratio: Option<f64>,
    pub tab_index: Option<i32>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ValidationMetrics {
    pub is_unique: bool,
    pub is_stable: bool,
    pub cross_browser_compatible: bool,
    pub warnings: Vec<String>,
    pub errors: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EnhancedTestResult {
    pub success: bool,
    pub element_count: usize,
    pub elements: Vec<EnhancedElementInfo>,
    pub performance: PerformanceMetrics,
    pub accessibility: AccessibilityMetrics,
    pub validation: ValidationMetrics,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TestOptions {
    pub performance_test: Option<bool>,
    pub accessibility_test: Option<bool>,
    pub validation_test: Option<bool>,
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

#[tauri::command]
pub async fn test_css_selector_enhanced(
    selector: String,
    html: String,
    options: TestOptions,
) -> Result<EnhancedTestResult, String> {
    let start_time = Instant::now();
    
    // Parse the CSS selector
    let css_selector = match Selector::parse(&selector) {
        Ok(sel) => sel,
        Err(e) => {
            return Ok(EnhancedTestResult {
                success: false,
                element_count: 0,
                elements: vec![],
                performance: PerformanceMetrics {
                    execution_time_ms: start_time.elapsed().as_millis() as u64,
                    selector_complexity: "invalid".to_string(),
                    suggestions: Some(vec![format!("Invalid CSS selector: {}", e)]),
                },
                accessibility: AccessibilityMetrics {
                    has_aria_labels: false,
                    has_alt_text: false,
                    color_contrast_ratio: None,
                    tab_index: None,
                },
                validation: ValidationMetrics {
                    is_unique: false,
                    is_stable: false,
                    cross_browser_compatible: false,
                    warnings: vec![],
                    errors: vec![format!("Invalid CSS selector: {}", e)],
                },
            });
        }
    };

    // Parse the HTML
    let document = Html::parse_document(&html);
    
    // Find all matching elements
    let matching_elements: Vec<ElementRef> = document.select(&css_selector).collect();
    let element_count = matching_elements.len();
    
    // Create enhanced element info
    let mut enhanced_elements = Vec::new();
    
    for (index, element) in matching_elements.iter().enumerate() {
        let tag_name = element.value().name().to_string();
        let text_content = element.text().collect::<Vec<_>>().join(" ");
        
        // Get attributes
        let mut attributes = HashMap::new();
        for (attr_name, attr_value) in element.value().attrs() {
            attributes.insert(attr_name.to_string(), attr_value.to_string());
        }

        // Generate XPath (simplified)
        let xpath = generate_xpath(element, index);
        
        // Generate CSS path (simplified)
        let css_path = generate_css_path(element, index);
        
        enhanced_elements.push(EnhancedElementInfo {
            tag: tag_name,
            text: text_content.trim().to_string(),
            attributes,
            position: ElementPosition {
                x: 0.0, // Would need browser API for real positioning
                y: 0.0,
                width: 0.0,
                height: 0.0,
            },
            xpath,
            css_path,
        });
    }

    let execution_time = start_time.elapsed().as_millis() as u64;
    
    // Analyze selector complexity
    let complexity = analyze_selector_complexity(&selector);
    
    // Generate performance suggestions
    let suggestions = if options.performance_test.unwrap_or(false) {
        Some(generate_performance_suggestions(&selector, element_count))
    } else {
        None
    };

    // Analyze accessibility
    let accessibility = if options.accessibility_test.unwrap_or(false) {
        analyze_accessibility(&enhanced_elements)
    } else {
        AccessibilityMetrics {
            has_aria_labels: false,
            has_alt_text: false,
            color_contrast_ratio: None,
            tab_index: None,
        }
    };

    // Perform validation
    let validation = if options.validation_test.unwrap_or(false) {
        analyze_validation(&selector, element_count, &enhanced_elements)
    } else {
        ValidationMetrics {
            is_unique: element_count == 1,
            is_stable: true,
            cross_browser_compatible: true,
            warnings: vec![],
            errors: vec![],
        }
    };

    Ok(EnhancedTestResult {
        success: element_count > 0,
        element_count,
        elements: enhanced_elements,
        performance: PerformanceMetrics {
            execution_time_ms: execution_time,
            selector_complexity: complexity,
            suggestions,
        },
        accessibility,
        validation,
    })
}

fn generate_xpath(element: &ElementRef, index: usize) -> String {
    // Simplified XPath generation
    format!("//*[{}][{}]", element.value().name(), index + 1)
}

fn generate_css_path(element: &ElementRef, index: usize) -> String {
    // Simplified CSS path generation
    let tag = element.value().name();
    if let Some(id) = element.value().attr("id") {
        format!("{}#{}", tag, id)
    } else if let Some(class) = element.value().attr("class") {
        let first_class = class.split_whitespace().next().unwrap_or("");
        format!("{}.{}", tag, first_class)
    } else {
        format!("{}:nth-of-type({})", tag, index + 1)
    }
}

fn analyze_selector_complexity(selector: &str) -> String {
    let complexity_indicators = [
        (" ", 1),           // Descendant selectors
        (">", 2),           // Child selectors  
        ("+", 2),           // Adjacent sibling
        ("~", 2),           // General sibling
        ("[", 3),           // Attribute selectors
        (":nth-", 4),       // nth selectors
        ("::before", 3),    // Pseudo elements
        ("::after", 3),     // Pseudo elements
        (":hover", 2),      // Pseudo classes
    ];
    
    let mut score = 0;
    for (indicator, weight) in complexity_indicators.iter() {
        score += selector.matches(indicator).count() * weight;
    }
    
    match score {
        0..=2 => "low".to_string(),
        3..=6 => "medium".to_string(),
        _ => "high".to_string(),
    }
}

fn generate_performance_suggestions(selector: &str, element_count: usize) -> Vec<String> {
    let mut suggestions = Vec::new();
    
    if element_count == 0 {
        suggestions.push("No elements found. Consider using more general selectors.".to_string());
    } else if element_count > 100 {
        suggestions.push("Too many elements found. Consider making your selector more specific.".to_string());
    }
    
    if selector.contains("*") {
        suggestions.push("Universal selector (*) can be slow. Consider more specific selectors.".to_string());
    }
    
    if selector.matches(":nth-").count() > 0 {
        suggestions.push("nth-child selectors can be slow. Consider ID or class-based selectors.".to_string());
    }
    
    if selector.split_whitespace().count() > 4 {
        suggestions.push("Deep nesting can impact performance. Consider flattening the selector.".to_string());
    }
    
    suggestions
}

fn analyze_accessibility(elements: &[EnhancedElementInfo]) -> AccessibilityMetrics {
    let has_aria_labels = elements.iter().any(|e| {
        e.attributes.contains_key("aria-label") || 
        e.attributes.contains_key("aria-labelledby") ||
        e.attributes.contains_key("aria-describedby")
    });
    
    let has_alt_text = elements.iter().any(|e| {
        e.tag == "img" && e.attributes.contains_key("alt")
    });
    
    let tab_index = elements.iter()
        .filter_map(|e| e.attributes.get("tabindex"))
        .filter_map(|ti| ti.parse::<i32>().ok())
        .next();
    
    AccessibilityMetrics {
        has_aria_labels,
        has_alt_text,
        color_contrast_ratio: None, // Would need color analysis
        tab_index,
    }
}

fn analyze_validation(selector: &str, element_count: usize, elements: &[EnhancedElementInfo]) -> ValidationMetrics {
    let mut warnings = Vec::new();
    let mut errors = Vec::new();
    
    let is_unique = element_count == 1;
    if !is_unique && element_count > 1 {
        warnings.push("Selector matches multiple elements. Consider making it more specific.".to_string());
    }
    
    // Check for potentially unstable selectors
    let is_stable = !selector.contains(":nth-child") && 
                   !selector.contains(":first-child") && 
                   !selector.contains(":last-child");
    
    if !is_stable {
        warnings.push("Selector uses positional selectors which may be unstable.".to_string());
    }
    
    // Basic cross-browser compatibility check
    let cross_browser_compatible = !selector.contains("::") || 
                                 selector.contains("::before") || 
                                 selector.contains("::after");
    
    if !cross_browser_compatible {
        warnings.push("Selector may have cross-browser compatibility issues.".to_string());
    }
    
    ValidationMetrics {
        is_unique,
        is_stable,
        cross_browser_compatible,
        warnings,
        errors,
    }
}
