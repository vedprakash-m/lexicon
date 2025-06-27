use std::path::PathBuf;
use serde::{Deserialize, Serialize};
use tauri::State;
use tokio::sync::Mutex;

use crate::python_manager::{PythonManager, PythonManagerError};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnvironmentConfig {
    pub name: String,
    pub python_version: String,
    pub requirements: Vec<String>,
    pub isolated: bool,
    pub created_at: chrono::DateTime<chrono::Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnvironmentHealth {
    pub overall_status: String, // "healthy", "warning", "critical"
    pub python_version: Option<String>,
    pub pip_available: bool,
    pub required_packages: std::collections::HashMap<String, bool>,
    pub disk_space_mb: Option<u64>,
    pub last_checked: chrono::DateTime<chrono::Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DependencyInstallProgress {
    pub package_name: String,
    pub status: String, // "pending", "installing", "completed", "failed"
    pub progress_percent: u8,
    pub error_message: Option<String>,
}

pub struct EnvironmentManager {
    app_data_dir: PathBuf,
    config: Option<EnvironmentConfig>,
    python_manager: Option<PythonManager>,
}

impl EnvironmentManager {
    pub fn new(app_data_dir: PathBuf) -> Self {
        Self {
            app_data_dir,
            config: None,
            python_manager: None,
        }
    }

    /// Create a new isolated Python virtual environment
    pub async fn create_virtual_environment(&mut self, name: &str) -> Result<EnvironmentConfig, PythonManagerError> {
        // Initialize Python manager if not already done
        if self.python_manager.is_none() {
            self.python_manager = Some(PythonManager::new(self.app_data_dir.clone()));
        }

        let python_manager = self.python_manager.as_mut().unwrap();
        
        // Create isolated environment
        let env = python_manager.create_isolated_environment().await?;
        
        let config = EnvironmentConfig {
            name: name.to_string(),
            python_version: env.version.clone(),
            requirements: self.get_core_requirements(),
            isolated: true,
            created_at: chrono::Utc::now(),
        };

        self.config = Some(config.clone());
        self.save_config().await?;

        Ok(config)
    }

    /// Get core requirements for Lexicon
    fn get_core_requirements(&self) -> Vec<String> {
        vec![
            "requests==2.32.3".to_string(),
            "beautifulsoup4==4.12.3".to_string(),
            "lxml==5.2.2".to_string(),
            "nltk==3.8.1".to_string(),
            "chardet==5.2.0".to_string(),
            "tqdm==4.66.4".to_string(),
            "click==8.1.7".to_string(),
            "pydantic==2.8.2".to_string(),
            "loguru==0.7.2".to_string(),
            "PyMuPDF==1.24.5".to_string(),
            "pdfplumber==0.11.1".to_string(),
            "python-dateutil==2.9.0".to_string(),
            "ftfy==6.2.0".to_string(),
            "langdetect==1.0.9".to_string(),
        ]
    }

    /// Install dependencies automatically with progress tracking
    pub async fn install_dependencies(&self, progress_callback: Option<fn(DependencyInstallProgress)>) -> Result<Vec<DependencyInstallProgress>, PythonManagerError> {
        let python_manager = self.python_manager.as_ref()
            .ok_or_else(|| PythonManagerError::IsolationError("Python manager not initialized".to_string()))?;

        let mut results = Vec::new();

        // Install core dependencies using the embedded installer script
        let install_result = python_manager.execute_script("dependency_installer", vec![
            "--install-core".to_string()
        ]).await?;

        if install_result.success {
            // Parse installation results and create progress updates
            for requirement in &self.get_core_requirements() {
                let package_name = requirement.split("==").next().unwrap_or(requirement).to_string();
                let progress = DependencyInstallProgress {
                    package_name: package_name.clone(),
                    status: "completed".to_string(),
                    progress_percent: 100,
                    error_message: None,
                };

                if let Some(callback) = progress_callback {
                    callback(progress.clone());
                }
                results.push(progress);
            }
        } else {
            return Err(PythonManagerError::ProcessExecutionFailed(install_result.stderr));
        }

        Ok(results)
    }

    /// Check version compatibility for all requirements
    pub async fn check_version_compatibility(&self) -> Result<std::collections::HashMap<String, bool>, PythonManagerError> {
        let python_manager = self.python_manager.as_ref()
            .ok_or_else(|| PythonManagerError::IsolationError("Python manager not initialized".to_string()))?;

        let check_result = python_manager.execute_script("dependency_installer", vec![
            "--check-only".to_string()
        ]).await?;

        if check_result.success {
            // Parse the JSON output to get package status
            let package_status: std::collections::HashMap<String, serde_json::Value> = 
                serde_json::from_str(&check_result.stdout)
                    .map_err(|e| PythonManagerError::ProcessExecutionFailed(format!("Failed to parse check results: {}", e)))?;

            let mut compatibility = std::collections::HashMap::new();

            if let Some(packages) = package_status.get("packages").and_then(|p| p.as_object()) {
                for (package_name, info) in packages {
                    let is_installed = info.get("installed").and_then(|v| v.as_bool()).unwrap_or(false);
                    compatibility.insert(package_name.clone(), is_installed);
                }
            }

            Ok(compatibility)
        } else {
            Err(PythonManagerError::ProcessExecutionFailed(check_result.stderr))
        }
    }

    /// Monitor environment health
    pub async fn monitor_health(&self) -> Result<EnvironmentHealth, PythonManagerError> {
        let python_manager = self.python_manager.as_ref()
            .ok_or_else(|| PythonManagerError::IsolationError("Python manager not initialized".to_string()))?;

        let health_data = python_manager.health_check().await?;
        
        let python_version = health_data.get("python")
            .and_then(|p| serde_json::from_str::<serde_json::Value>(p).ok())
            .and_then(|parsed| parsed.get("version").and_then(|v| v.as_str().map(|s| s.to_string())));

        let pip_available = health_data.get("pip")
            .and_then(|p| serde_json::from_str::<serde_json::Value>(p).ok())
            .and_then(|parsed| parsed.get("available").and_then(|v| v.as_bool()))
            .unwrap_or(false);

        let overall_status = health_data.get("status")
            .map(|s| s.clone())
            .unwrap_or_else(|| "unknown".to_string());

        // Check package availability
        let package_compatibility = self.check_version_compatibility().await.unwrap_or_default();

        // Estimate disk space (simplified)
        let disk_space_mb = self.estimate_disk_space().await;

        Ok(EnvironmentHealth {
            overall_status,
            python_version,
            pip_available,
            required_packages: package_compatibility,
            disk_space_mb,
            last_checked: chrono::Utc::now(),
        })
    }

    /// Estimate disk space usage (simplified implementation)
    async fn estimate_disk_space(&self) -> Option<u64> {
        // Simple estimation - in a real implementation, you'd calculate actual directory sizes
        if let Some(_venv_path) = self.python_manager.as_ref()
            .and_then(|pm| pm.get_current_environment())
            .and_then(|env| env.venv_path.as_ref()) 
        {
            // Rough estimate: typical venv with our dependencies is ~200-500MB
            Some(300) // MB
        } else {
            None
        }
    }

    /// Validate environment configuration
    pub async fn validate_environment(&self) -> Result<Vec<String>, PythonManagerError> {
        let mut issues = Vec::new();

        // Check if Python environment exists
        if self.python_manager.is_none() {
            issues.push("Python manager not initialized".to_string());
            return Ok(issues);
        }

        let python_manager = self.python_manager.as_ref().unwrap();
        
        // Check Python version
        if let Some(env) = python_manager.get_current_environment() {
            if !self.is_python_version_compatible(&env.version) {
                issues.push(format!("Python version {} is not compatible (requires 3.8+)", env.version));
            }
        } else {
            issues.push("No Python environment configured".to_string());
        }

        // Check package availability
        match self.check_version_compatibility().await {
            Ok(packages) => {
                for (package, available) in packages {
                    if !available {
                        issues.push(format!("Required package '{}' is not installed", package));
                    }
                }
            }
            Err(e) => {
                issues.push(format!("Could not check package compatibility: {}", e));
            }
        }

        Ok(issues)
    }

    /// Check if Python version is compatible
    fn is_python_version_compatible(&self, version: &str) -> bool {
        let parts: Vec<&str> = version.split('.').collect();
        if parts.len() >= 2 {
            if let (Ok(major), Ok(minor)) = (parts[0].parse::<i32>(), parts[1].parse::<i32>()) {
                return major > 3 || (major == 3 && minor >= 8);
            }
        }
        false
    }

    /// Save environment configuration
    async fn save_config(&self) -> Result<(), PythonManagerError> {
        if let Some(config) = &self.config {
            let config_path = self.app_data_dir.join("environment_config.json");
            
            // Ensure directory exists
            if let Some(parent) = config_path.parent() {
                tokio::fs::create_dir_all(parent).await
                    .map_err(|e| PythonManagerError::IsolationError(format!("Failed to create config directory: {}", e)))?;
            }

            let config_json = serde_json::to_string_pretty(config)
                .map_err(|e| PythonManagerError::IsolationError(format!("Failed to serialize config: {}", e)))?;

            tokio::fs::write(&config_path, config_json).await
                .map_err(|e| PythonManagerError::IsolationError(format!("Failed to save config: {}", e)))?;
        }
        Ok(())
    }

    /// Load environment configuration
    pub async fn load_config(&mut self) -> Result<Option<EnvironmentConfig>, PythonManagerError> {
        let config_path = self.app_data_dir.join("environment_config.json");
        
        if config_path.exists() {
            let config_content = tokio::fs::read_to_string(&config_path).await
                .map_err(|e| PythonManagerError::IsolationError(format!("Failed to read config: {}", e)))?;

            let config: EnvironmentConfig = serde_json::from_str(&config_content)
                .map_err(|e| PythonManagerError::IsolationError(format!("Failed to parse config: {}", e)))?;

            self.config = Some(config.clone());
            Ok(Some(config))
        } else {
            Ok(None)
        }
    }

    /// Get current configuration
    pub fn get_config(&self) -> Option<&EnvironmentConfig> {
        self.config.as_ref()
    }
}

/// Global environment manager state for Tauri
pub type EnvironmentManagerState = Mutex<EnvironmentManager>;

/// Tauri commands for environment management
#[tauri::command]
pub async fn create_python_virtual_environment(
    env_manager: State<'_, EnvironmentManagerState>,
    name: String,
) -> Result<EnvironmentConfig, String> {
    let mut manager = env_manager.lock().await;
    manager.create_virtual_environment(&name).await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn install_python_dependencies(
    env_manager: State<'_, EnvironmentManagerState>,
) -> Result<Vec<DependencyInstallProgress>, String> {
    let manager = env_manager.lock().await;
    manager.install_dependencies(None).await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn check_environment_health(
    env_manager: State<'_, EnvironmentManagerState>,
) -> Result<EnvironmentHealth, String> {
    let manager = env_manager.lock().await;
    manager.monitor_health().await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn validate_python_environment(
    env_manager: State<'_, EnvironmentManagerState>,
) -> Result<Vec<String>, String> {
    let manager = env_manager.lock().await;
    manager.validate_environment().await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_environment_config(
    env_manager: State<'_, EnvironmentManagerState>,
) -> Result<Option<EnvironmentConfig>, String> {
    let mut manager = env_manager.lock().await;
    manager.load_config().await.map_err(|e| e.to_string())
}
