import { useState, useEffect, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { useSyncManager } from './useSyncManager';
import { useBatchProcessing } from './useBatchProcessing';
import { usePerformanceMonitor } from './usePerformanceMonitor';

export interface SidebarStatus {
  storageUsed: string;
  processingCount: number;
  lastSync: string;
}

export function useSidebarStatus() {
  const [status, setStatus] = useState<SidebarStatus>({
    storageUsed: '0 MB',
    processingCount: 0,
    lastSync: 'Never'
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Use existing hooks for data
  const { syncStatus } = useSyncManager();
  const { jobs } = useBatchProcessing();
  const { metrics } = usePerformanceMonitor();

  // Calculate storage usage from disk metrics
  const getStorageUsed = useCallback(() => {
    if (!metrics) return '0 MB';
    
    const usageMB = metrics.disk_usage / (1024 * 1024);
    if (usageMB >= 1024) {
      return `${(usageMB / 1024).toFixed(1)} GB`;
    }
    return `${usageMB.toFixed(0)} MB`;
  }, [metrics]);

  // Count active processing jobs
  const getProcessingCount = useCallback(() => {
    if (!jobs) return 0;
    return jobs.filter(job => 
      job.status === 'running' || 
      job.status === 'queued' || 
      job.status === 'pending'
    ).length;
  }, [jobs]);

  // Format last sync time
  const getLastSync = useCallback(() => {
    if (!syncStatus?.last_sync) return 'Never';
    
    try {
      const lastSyncDate = new Date(syncStatus.last_sync);
      const now = new Date();
      const diffMs = now.getTime() - lastSyncDate.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMins / 60);
      const diffDays = Math.floor(diffHours / 24);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      
      return lastSyncDate.toLocaleDateString();
    } catch {
      return 'Never';
    }
  }, [syncStatus]);

  // Update status when data changes
  useEffect(() => {
    setStatus({
      storageUsed: getStorageUsed(),
      processingCount: getProcessingCount(),
      lastSync: getLastSync()
    });
    setLoading(false);
  }, [getStorageUsed, getProcessingCount, getLastSync]);

  // Get additional system info via Tauri commands
  const fetchAdditionalData = useCallback(async () => {
    try {
      setError(null);
      
      // Try to get more precise storage info from file system
      const diskSpaceAvailable = await invoke<boolean>('check_disk_space', { 
        requiredBytes: 0 
      }).catch(() => null);
      
      // Additional status could be fetched here if needed
      
    } catch (err) {
      console.warn('Failed to fetch additional sidebar status:', err);
      setError(err as string);
    }
  }, []);

  // Refresh status periodically
  useEffect(() => {
    fetchAdditionalData();
    
    const interval = setInterval(() => {
      fetchAdditionalData();
    }, 30000); // Refresh every 30 seconds
    
    return () => clearInterval(interval);
  }, [fetchAdditionalData]);

  return {
    status,
    loading,
    error,
    refresh: fetchAdditionalData
  };
}
