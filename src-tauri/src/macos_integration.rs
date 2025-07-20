use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::process::Command;
use tauri::{command, AppHandle, Manager};
use tokio::fs;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DragDropEvent {
    pub files: Vec<String>,
    pub position: (f64, f64),
    pub event_type: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResult {
    pub id: String,
    pub title: String,
    pub content: String,
    pub score: f64,
    pub metadata: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NotificationConfig {
    pub title: String,
    pub body: String,
    pub sound: Option<String>,
    pub badge_count: Option<u32>,
}

pub struct MacOSIntegration {
    app_handle: AppHandle,
}

impl MacOSIntegration {
    pub fn new(app_handle: AppHandle) -> Self {
        Self { app_handle }
    }

    pub async fn setup_drag_drop(&self) -> Result<(), Box<dyn std::error::Error>> {
        // Configure drag and drop handlers
        // This would integrate with Tauri's drag-drop APIs
        Ok(())
    }

    pub async fn send_notification(&self, config: NotificationConfig) -> Result<(), Box<dyn std::error::Error>> {
        // Use macOS native notifications
        let mut cmd = Command::new("osascript");
        cmd.arg("-e");
        
        let script = format!(
            r#"display notification "{}" with title "{}""#,
            config.body, config.title
        );
        
        if let Some(sound) = config.sound {
            let script_with_sound = format!(r#"{} sound name "{}""#, script, sound);
            cmd.arg(script_with_sound);
        } else {
            cmd.arg(script);
        }
        
        cmd.output()?;
        Ok(())
    }

    pub async fn create_shortcuts_integration(&self) -> Result<(), Box<dyn std::error::Error>> {
        // Create Shortcuts app integration
        let shortcuts_dir = dirs::home_dir()
            .ok_or("Could not find home directory")?
            .join("Library")
            .join("Shortcuts");

        fs::create_dir_all(&shortcuts_dir).await?;

        // Create shortcut files for common operations
        let shortcuts = vec![
            ("Process Document", "process_document"),
            ("Batch Process", "batch_process"),
            ("Export Data", "export_data"),
            ("Sync to Cloud", "sync_cloud"),
        ];

        for (name, action) in shortcuts {
            let shortcut_content = self.create_shortcut_content(name, action);
            let shortcut_path = shortcuts_dir.join(format!("{}.shortcut", name));
            fs::write(shortcut_path, shortcut_content).await?;
        }

        Ok(())
    }

    fn create_shortcut_content(&self, name: &str, action: &str) -> String {
        // Create Shortcuts app compatible content
        format!(
            r#"{{
                "WFWorkflowName": "{}",
                "WFWorkflowActions": [
                    {{
                        "WFWorkflowActionIdentifier": "is.workflow.actions.shell",
                        "WFWorkflowActionParameters": {{
                            "WFShellActionCommand": "open -a Lexicon --args --action {}"
                        }}
                    }}
                ]
            }}"#,
            name, action
        )
    }

    pub async fn setup_applescript_support(&self) -> Result<(), Box<dyn std::error::Error>> {
        // Create AppleScript handlers
        let applescript_dir = dirs::home_dir()
            .ok_or("Could not find home directory")?
            .join("Library")
            .join("Application Scripts")
            .join("com.lexicon.app");

        fs::create_dir_all(&applescript_dir).await?;

        // Create main AppleScript handler
        let applescript_content = r#"
on run argv
    set action to item 1 of argv
    
    if action is "process" then
        set filePath to item 2 of argv
        tell application "Lexicon"
            process document at filePath
        end tell
    else if action is "export" then
        set format to item 2 of argv
        tell application "Lexicon"
            export data with format format
        end tell
    end if
end run
"#;

        let script_path = applescript_dir.join("main.scpt");
        fs::write(script_path, applescript_content).await?;

        Ok(())
    }

    pub async fn integrate_with_finder(&self) -> Result<(), Box<dyn std::error::Error>> {
        // Create Finder integration
        let services_dir = dirs::home_dir()
            .ok_or("Could not find home directory")?
            .join("Library")
            .join("Services");

        fs::create_dir_all(&services_dir).await?;

        // Create service for "Process with Lexicon"
        let service_content = r#"<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NSMenuItem</key>
    <dict>
        <key>default</key>
        <string>Process with Lexicon</string>
    </dict>
    <key>NSMessage</key>
    <string>runWorkflowAsService</string>
    <key>NSPortName</key>
    <string>Lexicon</string>
    <key>NSRequiredContext</key>
    <dict>
        <key>NSApplicationIdentifier</key>
        <string>com.apple.finder</string>
    </dict>
    <key>NSReturnTypes</key>
    <array>
        <string>NSStringPboardType</string>
    </array>
    <key>NSSendFileTypes</key>
    <array>
        <string>public.data</string>
    </array>
</dict>
</plist>"#;

        let service_path = services_dir.join("Process with Lexicon.workflow");
        fs::create_dir_all(&service_path).await?;
        
        let info_plist_path = service_path.join("Contents").join("Info.plist");
        fs::create_dir_all(info_plist_path.parent().unwrap()).await?;
        fs::write(info_plist_path, service_content).await?;

        Ok(())
    }

    pub fn setup_dock_progress(&self, progress: f64) -> Result<(), Box<dyn std::error::Error>> {
        // Update dock icon with progress
        let script = format!(
            r#"tell application "System Events"
                set progress of dock item "Lexicon" to {}
            end tell"#,
            progress
        );

        Command::new("osascript")
            .arg("-e")
            .arg(script)
            .output()?;

        Ok(())
    }

    pub fn setup_menu_bar_indicator(&self, status: &str) -> Result<(), Box<dyn std::error::Error>> {
        // This would integrate with macOS menu bar
        // For now, we'll use a simple approach
        self.app_handle.emit_all("menu_bar_update", status)?;
        Ok(())
    }
}

// Tauri commands for macOS integration
#[command]
pub async fn handle_drag_drop(files: Vec<String>) -> Result<Vec<String>, String> {
    // Process dropped files
    let mut processed_files = Vec::new();
    
    for file_path in files {
        let path = PathBuf::from(&file_path);
        if path.exists() {
            processed_files.push(file_path);
        }
    }
    
    Ok(processed_files)
}

#[command]
pub async fn spotlight_search(query: String, limit: Option<usize>) -> Result<Vec<SearchResult>, String> {
    // Implement Spotlight-style search
    let limit = limit.unwrap_or(10);
    let mut results = Vec::new();
    
    // This would integrate with the actual search index
    // For now, return mock results
    for i in 0..limit.min(5) {
        results.push(SearchResult {
            id: format!("result_{}", i),
            title: format!("Search Result {}", i + 1),
            content: format!("Content matching '{}'", query),
            score: 1.0 - (i as f64 * 0.1),
            metadata: serde_json::json!({
                "type": "document",
                "path": format!("/path/to/document_{}.pdf", i)
            }),
        });
    }
    
    Ok(results)
}

#[command]
pub async fn send_macos_notification(config: NotificationConfig) -> Result<(), String> {
    let integration = MacOSIntegration::new(tauri::AppHandle::default());
    integration.send_notification(config).await.map_err(|e| e.to_string())
}

#[command]
pub async fn update_dock_progress(progress: f64) -> Result<(), String> {
    let integration = MacOSIntegration::new(tauri::AppHandle::default());
    integration.setup_dock_progress(progress).map_err(|e| e.to_string())
}

#[command]
pub async fn organize_output_folders(base_path: String) -> Result<Vec<String>, String> {
    // Organize output folders
    let base = PathBuf::from(base_path);
    let folders = vec!["exports", "processed", "metadata", "assets"];
    let mut created_folders = Vec::new();
    
    for folder in folders {
        let folder_path = base.join(folder);
        fs::create_dir_all(&folder_path).await.map_err(|e| e.to_string())?;
        created_folders.push(folder_path.to_string_lossy().to_string());
    }
    
    Ok(created_folders)
}

#[command]
pub async fn create_workflow_template(name: String, steps: Vec<String>) -> Result<String, String> {
    // Create workflow template
    let template = serde_json::json!({
        "name": name,
        "steps": steps,
        "created_at": chrono::Utc::now().to_rfc3339(),
        "version": "1.0"
    });
    
    let templates_dir = dirs::home_dir()
        .ok_or("Could not find home directory")?
        .join(".lexicon")
        .join("templates");
    
    fs::create_dir_all(&templates_dir).await.map_err(|e| e.to_string())?;
    
    let template_path = templates_dir.join(format!("{}.json", name));
    fs::write(&template_path, serde_json::to_string_pretty(&template)?).await.map_err(|e| e.to_string())?;
    
    Ok(template_path.to_string_lossy().to_string())
}