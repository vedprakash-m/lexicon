use std::path::PathBuf;
use std::process::Stdio;
use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use tauri::State;
use tokio::sync::Mutex;
use tokio::process::Command as AsyncCommand;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PythonEnvironment {
    pub python_path: PathBuf,
    pub venv_path: Option<PathBuf>,
    pub version: String,
    pub isolated: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PythonProcessResult {
    pub success: bool,
    pub stdout: String,
    pub stderr: String,
    pub exit_code: Option<i32>,
}

#[derive(Debug, thiserror::Error)]
pub enum PythonManagerError {
    #[error("Python executable not found. Please install Python 3.8+ and ensure it's in your PATH")]
    PythonNotFound,
    #[error("Python version {found} is not supported. Minimum required: {required}")]
    UnsupportedVersion { found: String, required: String },
    #[error("Virtual environment creation failed: {0}")]
    VenvCreationFailed(String),
    #[error("Python process execution failed: {0}")]
    ProcessExecutionFailed(String),
    #[error("Environment isolation error: {0}")]
    IsolationError(String),
}

pub struct PythonManager {
    app_data_dir: PathBuf,
    current_env: Option<PythonEnvironment>,
    embedded_scripts: HashMap<String, &'static str>,
}

impl PythonManager {
    pub fn new(app_data_dir: PathBuf) -> Self {
        let mut embedded_scripts = HashMap::new();
        
        // Embed core Python scripts directly in the binary
        embedded_scripts.insert(
            "environment_health_check".to_string(),
            include_str!("../scripts/environment_health_check.py")
        );
        embedded_scripts.insert(
            "dependency_installer".to_string(),
            include_str!("../scripts/dependency_installer.py")
        );
        embedded_scripts.insert(
            "version_check".to_string(),
            include_str!("../scripts/version_check.py")
        );
        embedded_scripts.insert(
            "quality_assessment".to_string(),
            include_str!("../scripts/quality_assessment.py")
        );

        Self {
            app_data_dir,
            current_env: None,
            embedded_scripts,
        }
    }

    /// Discover and validate Python installation
    pub async fn discover_python(&self) -> Result<PythonEnvironment, PythonManagerError> {
        // Try common Python executables in order of preference
        let python_candidates = vec!["python3", "python3.9", "python3.10", "python3.11", "python3.12", "python"];
        
        for candidate in python_candidates {
            if let Ok(python_path) = which::which(candidate) {
                if let Ok(env) = self.validate_python_executable(&python_path).await {
                    return Ok(env);
                }
            }
        }

        Err(PythonManagerError::PythonNotFound)
    }

    /// Validate Python executable and get version info
    async fn validate_python_executable(&self, python_path: &PathBuf) -> Result<PythonEnvironment, PythonManagerError> {
        let output = AsyncCommand::new(python_path)
            .args(&["--version"])
            .output()
            .await
            .map_err(|e| PythonManagerError::ProcessExecutionFailed(e.to_string()))?;

        let version_str = String::from_utf8_lossy(&output.stdout);
        let version = version_str.trim().replace("Python ", "");

        // Check minimum version requirement (3.8+)
        if !self.is_version_compatible(&version) {
            return Err(PythonManagerError::UnsupportedVersion {
                found: version,
                required: "3.8+".to_string(),
            });
        }

        Ok(PythonEnvironment {
            python_path: python_path.clone(),
            venv_path: None,
            version,
            isolated: false,
        })
    }

    /// Check if Python version meets minimum requirements
    fn is_version_compatible(&self, version: &str) -> bool {
        // Simple version check - parse major.minor
        let parts: Vec<&str> = version.split('.').collect();
        if parts.len() >= 2 {
            if let (Ok(major), Ok(minor)) = (parts[0].parse::<i32>(), parts[1].parse::<i32>()) {
                return major > 3 || (major == 3 && minor >= 8);
            }
        }
        false
    }

    /// Create isolated virtual environment for Lexicon
    pub async fn create_isolated_environment(&mut self) -> Result<PythonEnvironment, PythonManagerError> {
        let base_python = self.discover_python().await?;
        let venv_dir = self.app_data_dir.join("python_env");

        // Create virtual environment
        let output = AsyncCommand::new(&base_python.python_path)
            .args(&["-m", "venv", venv_dir.to_string_lossy().as_ref()])
            .output()
            .await
            .map_err(|e| PythonManagerError::VenvCreationFailed(e.to_string()))?;

        if !output.status.success() {
            return Err(PythonManagerError::VenvCreationFailed(
                String::from_utf8_lossy(&output.stderr).to_string()
            ));
        }

        // Determine venv Python path
        let venv_python = if cfg!(target_os = "windows") {
            venv_dir.join("Scripts").join("python.exe")
        } else {
            venv_dir.join("bin").join("python")
        };

        let isolated_env = PythonEnvironment {
            python_path: venv_python,
            venv_path: Some(venv_dir),
            version: base_python.version,
            isolated: true,
        };

        self.current_env = Some(isolated_env.clone());
        Ok(isolated_env)
    }

    /// Execute Python script with proper environment isolation
    pub async fn execute_script(&self, script_name: &str, args: Vec<String>) -> Result<PythonProcessResult, PythonManagerError> {
        let env = self.current_env.as_ref()
            .ok_or_else(|| PythonManagerError::IsolationError("No Python environment configured".to_string()))?;

        let script_content = self.embedded_scripts.get(script_name)
            .ok_or_else(|| PythonManagerError::ProcessExecutionFailed(format!("Script '{}' not found", script_name)))?;

        // Write script to temporary file
        let temp_script = self.app_data_dir.join(format!("temp_{}.py", script_name));
        tokio::fs::write(&temp_script, script_content).await
            .map_err(|e| PythonManagerError::ProcessExecutionFailed(e.to_string()))?;

        // Execute script
        let mut cmd = AsyncCommand::new(&env.python_path);
        cmd.arg(&temp_script);
        cmd.args(&args);
        cmd.stdout(Stdio::piped());
        cmd.stderr(Stdio::piped());

        let output = cmd.output().await
            .map_err(|e| PythonManagerError::ProcessExecutionFailed(e.to_string()))?;

        // Clean up temporary file
        let _ = tokio::fs::remove_file(&temp_script).await;

        Ok(PythonProcessResult {
            success: output.status.success(),
            stdout: String::from_utf8_lossy(&output.stdout).to_string(),
            stderr: String::from_utf8_lossy(&output.stderr).to_string(),
            exit_code: output.status.code(),
        })
    }

    /// Execute Python code directly (for simple operations)
    pub async fn execute_code(&self, code: &str) -> Result<PythonProcessResult, PythonManagerError> {
        let env = self.current_env.as_ref()
            .ok_or_else(|| PythonManagerError::IsolationError("No Python environment configured".to_string()))?;

        let output = AsyncCommand::new(&env.python_path)
            .args(&["-c", code])
            .output()
            .await
            .map_err(|e| PythonManagerError::ProcessExecutionFailed(e.to_string()))?;

        Ok(PythonProcessResult {
            success: output.status.success(),
            stdout: String::from_utf8_lossy(&output.stdout).to_string(),
            stderr: String::from_utf8_lossy(&output.stderr).to_string(),
            exit_code: output.status.code(),
        })
    }

    /// Get current environment information
    pub fn get_current_environment(&self) -> Option<&PythonEnvironment> {
        self.current_env.as_ref()
    }

    /// Health check for Python environment
    pub async fn health_check(&self) -> Result<HashMap<String, String>, PythonManagerError> {
        let result = self.execute_script("environment_health_check", vec![]).await?;
        
        if result.success {
            let health_data: HashMap<String, String> = serde_json::from_str(&result.stdout)
                .unwrap_or_else(|_| {
                    let mut map = HashMap::new();
                    map.insert("status".to_string(), "unknown".to_string());
                    map.insert("output".to_string(), result.stdout);
                    map
                });
            Ok(health_data)
        } else {
            Err(PythonManagerError::ProcessExecutionFailed(result.stderr))
        }
    }

    /// Install Python packages using the dependency installer
    pub async fn install_packages(&self, packages: Vec<String>, upgrade: bool) -> Result<PythonProcessResult, PythonManagerError> {
        let mut args = vec!["--packages".to_string()];
        args.extend(packages);
        
        if upgrade {
            args.push("--upgrade".to_string());
        }
        
        self.execute_script("dependency_installer", args).await
    }

    /// Install core Lexicon dependencies
    pub async fn install_core_dependencies(&self, upgrade: bool) -> Result<PythonProcessResult, PythonManagerError> {
        let mut args = vec!["--install-core".to_string()];
        
        if upgrade {
            args.push("--upgrade".to_string());
        }
        
        self.execute_script("dependency_installer", args).await
    }

    /// Check package installation status
    pub async fn check_package_installation(&self, packages: Vec<String>) -> Result<HashMap<String, serde_json::Value>, PythonManagerError> {
        let mut args = vec!["--check-only".to_string(), "--packages".to_string()];
        args.extend(packages);
        
        let result = self.execute_script("dependency_installer", args).await?;
        
        if result.success {
            let check_data: HashMap<String, serde_json::Value> = serde_json::from_str(&result.stdout)
                .unwrap_or_else(|_| HashMap::new());
            Ok(check_data)
        } else {
            Err(PythonManagerError::ProcessExecutionFailed(result.stderr))
        }
    }

    /// Assess quality of text chunks using ML models
    pub async fn assess_chunk_quality(&self, text: String) -> Result<serde_json::Value, PythonManagerError> {
        let args = vec!["--text".to_string(), text];
        
        let result = self.execute_script("quality_assessment", args).await?;
        
        if result.success {
            let assessment: serde_json::Value = serde_json::from_str(&result.stdout)
                .map_err(|e| PythonManagerError::ProcessExecutionFailed(format!("Failed to parse quality assessment: {}", e)))?;
            Ok(assessment)
        } else {
            Err(PythonManagerError::ProcessExecutionFailed(result.stderr))
        }
    }

    /// Assess relationships between chunks
    pub async fn assess_chunk_relationships(&self, chunks: Vec<serde_json::Value>) -> Result<serde_json::Value, PythonManagerError> {
        let chunks_json = serde_json::to_string(&chunks)
            .map_err(|e| PythonManagerError::ProcessExecutionFailed(format!("Failed to serialize chunks: {}", e)))?;
        
        let args = vec!["--chunks".to_string(), chunks_json, "--assess-relationships".to_string()];
        
        let result = self.execute_script("quality_assessment", args).await?;
        
        if result.success {
            let relationships: serde_json::Value = serde_json::from_str(&result.stdout)
                .map_err(|e| PythonManagerError::ProcessExecutionFailed(format!("Failed to parse relationships: {}", e)))?;
            Ok(relationships)
        } else {
            Err(PythonManagerError::ProcessExecutionFailed(result.stderr))
        }
    }
}

/// Global Python manager state for Tauri
pub type PythonManagerState = Mutex<PythonManager>;

/// Tauri commands for Python integration
#[tauri::command]
pub async fn discover_python_environment(
    manager: State<'_, PythonManagerState>,
) -> Result<PythonEnvironment, String> {
    let manager = manager.lock().await;
    manager.discover_python().await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn create_python_environment(
    manager: State<'_, PythonManagerState>,
) -> Result<PythonEnvironment, String> {
    let mut manager = manager.lock().await;
    manager.create_isolated_environment().await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn execute_python_script(
    manager: State<'_, PythonManagerState>,
    script_name: String,
    args: Vec<String>,
) -> Result<PythonProcessResult, String> {
    let manager = manager.lock().await;
    manager.execute_script(&script_name, args).await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn execute_python_code(
    manager: State<'_, PythonManagerState>,
    code: String,
) -> Result<PythonProcessResult, String> {
    let manager = manager.lock().await;
    manager.execute_code(&code).await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn python_health_check(
    manager: State<'_, PythonManagerState>,
) -> Result<HashMap<String, String>, String> {
    let manager = manager.lock().await;
    manager.health_check().await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_python_environment_info(
    manager: State<'_, PythonManagerState>,
) -> Result<Option<PythonEnvironment>, String> {
    let manager = manager.lock().await;
    Ok(manager.get_current_environment().cloned())
}

#[tauri::command]
pub async fn install_python_packages(
    manager: State<'_, PythonManagerState>,
    packages: Vec<String>,
    upgrade: Option<bool>,
) -> Result<PythonProcessResult, String> {
    let manager = manager.lock().await;
    manager.install_packages(packages, upgrade.unwrap_or(false)).await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn install_core_python_dependencies(
    manager: State<'_, PythonManagerState>,
    upgrade: Option<bool>,
) -> Result<PythonProcessResult, String> {
    let manager = manager.lock().await;
    manager.install_core_dependencies(upgrade.unwrap_or(false)).await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn check_python_packages(
    manager: State<'_, PythonManagerState>,
    packages: Vec<String>,
) -> Result<HashMap<String, serde_json::Value>, String> {
    let manager = manager.lock().await;
    manager.check_package_installation(packages).await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn assess_text_quality(
    manager: State<'_, PythonManagerState>,
    text: String,
) -> Result<serde_json::Value, String> {
    let manager = manager.lock().await;
    manager.assess_chunk_quality(text).await.map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn assess_chunk_relationships(
    manager: State<'_, PythonManagerState>,
    chunks: Vec<serde_json::Value>,
) -> Result<serde_json::Value, String> {
    let manager = manager.lock().await;
    manager.assess_chunk_relationships(chunks).await.map_err(|e| e.to_string())
}
