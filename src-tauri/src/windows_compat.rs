// Windows platform compatibility utilities for Lexicon
use std::path::PathBuf;
use std::env;

/// Get platform-specific Python executable name
pub fn get_python_executable() -> &'static str {
    if cfg!(target_os = "windows") {
        "python"
    } else {
        "python3"
    }
}

/// Get platform-specific shell command
pub fn get_shell_command() -> (&'static str, Vec<&'static str>) {
    if cfg!(target_os = "windows") {
        ("cmd", vec!["/C"])
    } else {
        ("sh", vec!["-c"])
    }
}

/// Get platform-specific app data directory
pub fn get_app_data_dir() -> PathBuf {
    if cfg!(target_os = "windows") {
        // Windows: %APPDATA%\Lexicon
        dirs::data_dir()
            .unwrap_or_else(|| PathBuf::from("C:\\Users\\Default\\AppData\\Roaming"))
            .join("Lexicon")
    } else if cfg!(target_os = "macos") {
        // macOS: ~/Library/Application Support/Lexicon
        dirs::data_dir()
            .unwrap_or_else(|| dirs::home_dir().unwrap_or_default().join("Library/Application Support"))
            .join("Lexicon")
    } else {
        // Linux: ~/.local/share/lexicon
        dirs::data_dir()
            .unwrap_or_else(|| dirs::home_dir().unwrap_or_default().join(".local/share"))
            .join("lexicon")
    }
}

/// Get platform-specific documents directory
pub fn get_documents_dir() -> PathBuf {
    dirs::document_dir()
        .unwrap_or_else(|| {
            if cfg!(target_os = "windows") {
                PathBuf::from("C:\\Users\\Default\\Documents")
            } else {
                dirs::home_dir().unwrap_or_default().join("Documents")
            }
        })
}

/// Get platform-specific downloads directory
pub fn get_downloads_dir() -> PathBuf {
    dirs::download_dir()
        .unwrap_or_else(|| {
            if cfg!(target_os = "windows") {
                PathBuf::from("C:\\Users\\Default\\Downloads")
            } else {
                dirs::home_dir().unwrap_or_default().join("Downloads")
            }
        })
}

/// Get platform-specific desktop directory
pub fn get_desktop_dir() -> PathBuf {
    dirs::desktop_dir()
        .unwrap_or_else(|| {
            if cfg!(target_os = "windows") {
                PathBuf::from("C:\\Users\\Default\\Desktop")
            } else {
                dirs::home_dir().unwrap_or_default().join("Desktop")
            }
        })
}

/// Check if running on Windows
pub fn is_windows() -> bool {
    cfg!(target_os = "windows")
}

/// Check if running on macOS
pub fn is_macos() -> bool {
    cfg!(target_os = "macos")
}

/// Check if running on Linux
pub fn is_linux() -> bool {
    cfg!(target_os = "linux")
}

/// Get platform-specific path separator
pub fn get_path_separator() -> char {
    std::path::MAIN_SEPARATOR
}

/// Convert path to platform-specific format
pub fn normalize_path(path: &str) -> String {
    if cfg!(target_os = "windows") {
        path.replace('/', "\\")
    } else {
        path.replace('\\', "/")
    }
}

/// Get platform-specific environment variable
pub fn get_env_var(key: &str) -> Option<String> {
    env::var(key).ok()
}

/// Get platform-specific temporary directory
pub fn get_temp_dir() -> PathBuf {
    env::temp_dir()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_python_executable() {
        let python = get_python_executable();
        assert!(!python.is_empty());
    }

    #[test]
    fn test_app_data_dir() {
        let app_dir = get_app_data_dir();
        assert!(app_dir.to_string_lossy().contains("Lexicon") || 
                app_dir.to_string_lossy().contains("lexicon"));
    }

    #[test]
    fn test_path_separator() {
        let sep = get_path_separator();
        if cfg!(target_os = "windows") {
            assert_eq!(sep, '\\');
        } else {
            assert_eq!(sep, '/');
        }
    }

    #[test]
    fn test_normalize_path() {
        if cfg!(target_os = "windows") {
            assert_eq!(normalize_path("path/to/file"), "path\\to\\file");
        } else {
            assert_eq!(normalize_path("path\\to\\file"), "path/to/file");
        }
    }
}
