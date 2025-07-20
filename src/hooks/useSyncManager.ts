import { useState, useEffect, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { ErrorHandler } from '@/utils/errorHandler';

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

export interface SyncTarget {
  id: string;
  name: string;
  target_type: 'local' | 'dropbox' | 'google_drive' | 'aws_s3' | 'azure_blob';
  status: 'connected' | 'error' | 'disconnected';
  last_sync?: string;
  config: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export const useSyncManager = () => {
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [syncTargets, setSyncTargets] = useState<SyncTarget[]>([]);
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
      const errorMessage = err as string;
      setError(errorMessage);
      ErrorHandler.logError(err as Error, {
        component: 'SyncManager',
        operation: 'fetchSyncStatus',
        details: { invokeCommand: 'get_sync_status' }
      });
    }
  }, []);

  // Fetch backups list
  const fetchBackups = useCallback(async () => {
    try {
      setError(null);
      const backupsList = await invoke<BackupInfo[]>('list_backup_archives');
      setBackups(backupsList);
    } catch (err) {
      const errorMessage = err as string;
      setError(errorMessage);
      ErrorHandler.logError(err as Error, {
        component: 'SyncManager',
        operation: 'fetchBackups',
        details: { invokeCommand: 'list_backup_archives' }
      });
    }
  }, []);

  // Fetch sync targets list
  const fetchSyncTargets = useCallback(async () => {
    try {
      setError(null);
      const targetsList = await invoke<SyncTarget[]>('get_sync_targets');
      setSyncTargets(targetsList);
    } catch (err) {
      const errorMessage = err as string;
      setError(errorMessage);
      ErrorHandler.logError(err as Error, {
        component: 'SyncManager',
        operation: 'fetchSyncTargets',
        details: { invokeCommand: 'get_sync_targets' }
      });
    }
  }, []);

  // Initialize data
  const loadData = useCallback(async () => {
    setIsLoading(true);
    await Promise.all([fetchSyncStatus(), fetchBackups(), fetchSyncTargets()]);
    setIsLoading(false);
  }, [fetchSyncStatus, fetchBackups, fetchSyncTargets]);

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
  const restoreBackup = useCallback(async (archiveId: string): Promise<{ success: boolean; message: string }> => {
    try {
      setError(null);
      const result = await invoke<{ success: boolean; message: string }>('restore_backup', { archiveId });
      if (result.success) {
        await loadData(); // Refresh all data after restore
      }
      return result;
    } catch (err) {
      const errorMessage = err as string;
      setError(errorMessage);
      ErrorHandler.logError(err as Error, {
        component: 'SyncManager',
        operation: 'restoreBackup',
        details: { archiveId, invokeCommand: 'restore_backup' }
      });
      return { success: false, message: errorMessage };
    }
  }, [loadData]);

  // Add new sync target
  const addSyncTarget = useCallback(async (target: Omit<SyncTarget, 'id' | 'created_at' | 'updated_at'>): Promise<{ success: boolean; message: string }> => {
    try {
      setError(null);
      const result = await invoke<{ success: boolean; message: string }>('add_sync_target', { target });
      if (result.success) {
        await fetchSyncTargets(); // Refresh targets list
      }
      return result;
    } catch (err) {
      const errorMessage = err as string;
      setError(errorMessage);
      ErrorHandler.logError(err as Error, {
        component: 'SyncManager',
        operation: 'addSyncTarget',
        details: { target, invokeCommand: 'add_sync_target' }
      });
      return { success: false, message: errorMessage };
    }
  }, [fetchSyncTargets]);

  // Update existing sync target
  const updateSyncTarget = useCallback(async (target: SyncTarget): Promise<{ success: boolean; message: string }> => {
    try {
      setError(null);
      const result = await invoke<{ success: boolean; message: string }>('update_sync_target', { target });
      if (result.success) {
        await fetchSyncTargets(); // Refresh targets list
      }
      return result;
    } catch (err) {
      const errorMessage = err as string;
      setError(errorMessage);
      ErrorHandler.logError(err as Error, {
        component: 'SyncManager',
        operation: 'updateSyncTarget',
        details: { target, invokeCommand: 'update_sync_target' }
      });
      return { success: false, message: errorMessage };
    }
  }, [fetchSyncTargets]);

  // Delete sync target
  const deleteSyncTarget = useCallback(async (targetId: string): Promise<{ success: boolean; message: string }> => {
    try {
      setError(null);
      const result = await invoke<{ success: boolean; message: string }>('delete_sync_target', { targetId });
      if (result.success) {
        await fetchSyncTargets(); // Refresh targets list
      }
      return result;
    } catch (err) {
      const errorMessage = err as string;
      setError(errorMessage);
      ErrorHandler.logError(err as Error, {
        component: 'SyncManager',
        operation: 'deleteSyncTarget',
        details: { targetId, invokeCommand: 'delete_sync_target' }
      });
      return { success: false, message: errorMessage };
    }
  }, [fetchSyncTargets]);

  // Test sync target connection
  const testSyncTargetConnection = useCallback(async (targetId: string): Promise<{ success: boolean; message: string }> => {
    try {
      setError(null);
      const result = await invoke<{ success: boolean; message: string }>('test_sync_target_connection', { targetId });
      return result;
    } catch (err) {
      const errorMessage = err as string;
      setError(errorMessage);
      ErrorHandler.logError(err as Error, {
        component: 'SyncManager',
        operation: 'testSyncTargetConnection',
        details: { targetId, invokeCommand: 'test_sync_target_connection' }
      });
      return { success: false, message: errorMessage };
    }
  }, []);

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
    syncTargets,
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
    fetchSyncTargets,
    addSyncTarget,
    updateSyncTarget,
    deleteSyncTarget,
    testSyncTargetConnection,
    
    // Utilities
    clearError: () => setError(null),
  };
};
