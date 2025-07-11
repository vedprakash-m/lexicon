import { useState, useEffect, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

export interface SyncStatus {
  enabled: boolean;
  last_sync: string | null;
  provider: string | null;
  conflicts: number;
  pending_uploads: number;
  pending_downloads: number;
}

export interface BackupInfo {
  id: string;
  name: string;
  timestamp: string;
  size: number;
  location: string;
  verified: boolean;
  file_count: number;
}

export interface SyncConfig {
  provider: string;
  credentials: Record<string, string>;
  sync_interval: number;
  auto_sync: boolean;
  encryption_enabled: boolean;
}

export interface BackupConfig {
  auto_backup: boolean;
  backup_interval: number;
  max_backups: number;
  backup_location: string;
  compress: boolean;
  encrypt: boolean;
}

export const useSyncManager = () => {
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOperationInProgress, setIsOperationInProgress] = useState(false);

  // Fetch sync status
  const fetchSyncStatus = useCallback(async () => {
    try {
      setError(null);
      const status = await invoke<SyncStatus>('get_sync_status');
      setSyncStatus(status);
    } catch (err) {
      setError(err as string);
      console.error('Failed to fetch sync status:', err);
    }
  }, []);

  // Fetch backups list
  const fetchBackups = useCallback(async () => {
    try {
      setError(null);
      const backupsList = await invoke<BackupInfo[]>('list_backup_archives');
      setBackups(backupsList);
    } catch (err) {
      setError(err as string);
      console.error('Failed to fetch backups:', err);
    }
  }, []);

  // Initialize data
  const loadData = useCallback(async () => {
    setIsLoading(true);
    await Promise.all([fetchSyncStatus(), fetchBackups()]);
    setIsLoading(false);
  }, [fetchSyncStatus, fetchBackups]);

  // Configure sync
  const configureSync = useCallback(async (config: SyncConfig): Promise<boolean> => {
    try {
      setIsOperationInProgress(true);
      setError(null);
      const success = await invoke<boolean>('configure_sync', { config });
      if (success) {
        await fetchSyncStatus();
      }
      return success;
    } catch (err) {
      setError(err as string);
      console.error('Failed to configure sync:', err);
      return false;
    } finally {
      setIsOperationInProgress(false);
    }
  }, [fetchSyncStatus]);

  // Start sync
  const startSync = useCallback(async (): Promise<boolean> => {
    try {
      setIsOperationInProgress(true);
      setError(null);
      const success = await invoke<boolean>('start_sync');
      if (success) {
        await fetchSyncStatus();
      }
      return success;
    } catch (err) {
      setError(err as string);
      console.error('Failed to start sync:', err);
      return false;
    } finally {
      setIsOperationInProgress(false);
    }
  }, [fetchSyncStatus]);

  // Stop sync
  const stopSync = useCallback(async (): Promise<boolean> => {
    try {
      setIsOperationInProgress(true);
      setError(null);
      const success = await invoke<boolean>('stop_sync');
      if (success) {
        await fetchSyncStatus();
      }
      return success;
    } catch (err) {
      setError(err as string);
      console.error('Failed to stop sync:', err);
      return false;
    } finally {
      setIsOperationInProgress(false);
    }
  }, [fetchSyncStatus]);

  // Create backup
  const createBackup = useCallback(async (name: string): Promise<BackupInfo | null> => {
    try {
      setIsOperationInProgress(true);
      setError(null);
      const backupInfo = await invoke<BackupInfo>('create_backup', { name });
      await fetchBackups();
      return backupInfo;
    } catch (err) {
      setError(err as string);
      console.error('Failed to create backup:', err);
      return null;
    } finally {
      setIsOperationInProgress(false);
    }
  }, [fetchBackups]);

  // Restore backup
  const restoreBackup = useCallback(async (backupId: string): Promise<boolean> => {
    try {
      setIsOperationInProgress(true);
      setError(null);
      const success = await invoke<boolean>('restore_backup', { backupId });
      if (success) {
        await loadData(); // Refresh all data after restore
      }
      return success;
    } catch (err) {
      setError(err as string);
      console.error('Failed to restore backup:', err);
      return false;
    } finally {
      setIsOperationInProgress(false);
    }
  }, [loadData]);

  // Delete backup
  const deleteBackup = useCallback(async (backupId: string): Promise<boolean> => {
    try {
      setIsOperationInProgress(true);
      setError(null);
      const success = await invoke<boolean>('delete_backup', { backupId });
      if (success) {
        await fetchBackups();
      }
      return success;
    } catch (err) {
      setError(err as string);
      console.error('Failed to delete backup:', err);
      return false;
    } finally {
      setIsOperationInProgress(false);
    }
  }, [fetchBackups]);

  // Verify backup
  const verifyBackup = useCallback(async (backupId: string): Promise<boolean> => {
    try {
      setIsOperationInProgress(true);
      setError(null);
      const isValid = await invoke<boolean>('verify_backup', { backupId });
      await fetchBackups(); // Refresh to get updated verification status
      return isValid;
    } catch (err) {
      setError(err as string);
      console.error('Failed to verify backup:', err);
      return false;
    } finally {
      setIsOperationInProgress(false);
    }
  }, [fetchBackups]);

  // Configure backup
  const configureBackup = useCallback(async (config: BackupConfig): Promise<boolean> => {
    try {
      setIsOperationInProgress(true);
      setError(null);
      const success = await invoke<boolean>('configure_backup', { config });
      return success;
    } catch (err) {
      setError(err as string);
      console.error('Failed to configure backup:', err);
      return false;
    } finally {
      setIsOperationInProgress(false);
    }
  }, []);

  // Refresh data periodically
  const refreshData = useCallback(() => {
    loadData();
  }, [loadData]);

  // Auto-refresh every 30 seconds if sync is enabled
  useEffect(() => {
    if (syncStatus?.enabled) {
      const interval = setInterval(refreshData, 30000);
      return () => clearInterval(interval);
    }
  }, [syncStatus?.enabled, refreshData]);

  // Initial load
  useEffect(() => {
    loadData();
  }, [loadData]);

  return {
    // State
    syncStatus,
    backups,
    isLoading,
    error,
    isOperationInProgress,
    
    // Actions
    configureSync,
    startSync,
    stopSync,
    createBackup,
    restoreBackup,
    deleteBackup,
    verifyBackup,
    configureBackup,
    refreshData,
    
    // Utilities
    clearError: () => setError(null),
  };
};
