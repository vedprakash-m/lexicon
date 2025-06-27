mod python_manager;
mod environment_manager;
mod state_manager;
mod file_system;
mod file_system_commands;
mod database;
mod repository;
mod database_commands;
mod web_scraper;
mod web_scraper_commands;
mod processing_commands;
pub mod models;
pub mod validation;
pub mod schema;
pub mod migration;

#[cfg(test)]
mod tests;

use python_manager::{
    PythonManager, PythonManagerState,
    discover_python_environment, create_python_environment,
    execute_python_script, execute_python_code,
    python_health_check, get_python_environment_info
};
use environment_manager::{
    EnvironmentManager, EnvironmentManagerState,
    create_python_virtual_environment, install_python_dependencies,
    check_environment_health, validate_python_environment,
    get_environment_config
};
use state_manager::{
    StateStorage,
    get_all_source_texts, get_source_text, save_source_text, delete_source_text,
    get_all_datasets, get_dataset, save_dataset, delete_dataset,
    process_source_text, generate_dataset, clear_all_data, get_state_stats
};
use file_system::{FileSystem, FileSystemConfig};
use file_system_commands::{
    init_file_system, write_file, read_file, delete_file, move_file,
    restore_from_backup, get_backup_info, list_backups, get_data_path,
    check_disk_space, ensure_directory_structure, get_file_system_config,
    update_file_system_config
};
use database::{Database, DatabaseConfig};
use database_commands::{
    DatabaseState,
    init_database, database_health_check, get_database_statistics,
    create_source_text, get_source_text_by_id, db_get_all_source_texts,
    update_source_text, db_delete_source_text, search_source_texts,
    get_source_texts_by_status, create_dataset, get_dataset_by_id,
    get_datasets_by_source_text, update_dataset, db_delete_dataset,
    create_text_chunks_batch, search_text_chunks,
    get_app_settings, save_app_settings,
    create_database_backup, restore_database_from_backup
};
use web_scraper::WebScraperManager;
use web_scraper_commands::{
    WebScraperState,
    init_web_scraper, start_scraping_job, get_scraping_job_status,
    get_active_scraping_jobs, cancel_scraping_job, scrape_single_url,
    cleanup_scraping_jobs, get_scraping_progress, get_default_scraping_config,
    validate_urls, test_scraper_connectivity
};
use processing_commands::{
    process_advanced_chunking, validate_chunking_config,
    get_chunking_strategies, test_chunking_config
};
use tokio::sync::Mutex;
use std::path::PathBuf;
use std::sync::Arc;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub async fn run() {
  // Initialize app data directory
  let app_data_dir = dirs::data_dir()
    .unwrap_or_else(|| PathBuf::from("."))
    .join("com.lexicon.dataset-tool");
  
  // Initialize managers
  let python_manager = PythonManager::new(app_data_dir.clone());
  let environment_manager = EnvironmentManager::new(app_data_dir.clone());
  let state_storage = StateStorage::new();
  let file_system = FileSystem::with_defaults()
    .expect("Failed to initialize file system");
  
  // Initialize database with default config
  let db_config = DatabaseConfig {
    db_path: app_data_dir.join("lexicon.db").to_string_lossy().to_string(),
    ..Default::default()
  };
  let database = Database::new(db_config).await
    .expect("Failed to initialize database");
  let database_state: DatabaseState = Arc::new(Mutex::new(database));
  
  // Initialize web scraper
  let web_scraper_manager = WebScraperManager::new(app_data_dir.clone());
  let web_scraper_state: WebScraperState = Arc::new(Mutex::new(web_scraper_manager));
  
  tauri::Builder::default()
    .manage(Mutex::new(python_manager) as PythonManagerState)
    .manage(Mutex::new(environment_manager) as EnvironmentManagerState)
    .manage(state_storage)
    .manage(Mutex::new(file_system))
    .manage(database_state)
    .manage(web_scraper_state)
    .invoke_handler(tauri::generate_handler![
      // Python Manager commands
      discover_python_environment,
      create_python_environment,
      execute_python_script,
      execute_python_code,
      python_health_check,
      get_python_environment_info,
      // Environment Manager commands
      create_python_virtual_environment,
      install_python_dependencies,
      check_environment_health,
      validate_python_environment,
      get_environment_config,
      // State Manager commands
      get_all_source_texts,
      get_source_text,
      save_source_text,
      delete_source_text,
      get_all_datasets,
      get_dataset,
      save_dataset,
      delete_dataset,
      process_source_text,
      generate_dataset,
      clear_all_data,
      get_state_stats,
      // File System commands
      init_file_system,
      write_file,
      read_file,
      delete_file,
      move_file,
      restore_from_backup,
      get_backup_info,
      list_backups,
      get_data_path,
      check_disk_space,
      ensure_directory_structure,
      get_file_system_config,
      update_file_system_config,
      // Database commands
      init_database,
      database_health_check,
      get_database_statistics,
      create_source_text,
      get_source_text_by_id,
      db_get_all_source_texts,
      update_source_text,
      db_delete_source_text,
      search_source_texts,
      get_source_texts_by_status,
      create_dataset,
      get_dataset_by_id,
      get_datasets_by_source_text,
      update_dataset,
      db_delete_dataset,
      create_text_chunks_batch,
      search_text_chunks,
      get_app_settings,
      save_app_settings,
      create_database_backup,
      restore_database_from_backup,
      // Web Scraper commands
      init_web_scraper,
      start_scraping_job,
      get_scraping_job_status,
      get_active_scraping_jobs,
      cancel_scraping_job,
      scrape_single_url,
      cleanup_scraping_jobs,
      get_scraping_progress,
      get_default_scraping_config,
      validate_urls,
      test_scraper_connectivity,
      // Processing commands
      process_advanced_chunking,
      validate_chunking_config,
      get_chunking_strategies,
      test_chunking_config
    ])
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }
      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
