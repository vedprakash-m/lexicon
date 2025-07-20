import { useState, useEffect, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { ErrorHandler } from '@/utils/errorHandler';

export interface BatchJob {
  id: string;
  name: string;
  description: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  status: 'pending' | 'queued' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  sourceCount: number;
  completedSources: number;
  totalPages: number;
  processedPages: number;
  startTime?: Date;
  endTime?: Date;
  estimatedDuration?: number; // minutes
  parallelSources: boolean;
  parallelPages: boolean;
}

export interface ResourceUsage {
  cpuPercent: number;
  memoryPercent: number;
  memoryMb: number;
  activeProcesses: number;
}

export interface SystemStatus {
  processorRunning: boolean;
  resourceUsage: ResourceUsage;
  resourceLimits: {
    maxCpuCores: number;
    maxMemoryMb: number;
    maxConcurrentJobs: number;
  };
  queueStatus: {
    queuedJobs: number;
    activeJobs: number;
    completedJobs: number;
  };
  shouldThrottle: boolean;
}

export interface BatchJobCreate {
  name: string;
  description: string;
  priority: BatchJob['priority'];
  sources: string[];
  parallelSources?: boolean;
  parallelPages?: boolean;
}

export interface UseBatchProcessingResult {
  // Data
  jobs: BatchJob[];
  systemStatus: SystemStatus | null;
  
  // Loading states
  loading: boolean;
  error: string | null;
  
  // Actions
  createJob: (jobData: BatchJobCreate) => Promise<void>;
  pauseJob: (jobId: string) => Promise<void>;
  resumeJob: (jobId: string) => Promise<void>;
  cancelJob: (jobId: string) => Promise<void>;
  deleteJob: (jobId: string) => Promise<void>;
  exportJobResults: (jobId: string, format: string) => Promise<void>;
  
  // System actions
  refreshJobs: () => Promise<void>;
  refreshSystemStatus: () => Promise<void>;
}

export function useBatchProcessing(): UseBatchProcessingResult {
  const [jobs, setJobs] = useState<BatchJob[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch all batch jobs
  const fetchJobs = useCallback(async () => {
    try {
      const jobsData = await invoke<BatchJob[]>('get_all_batch_jobs');
      setJobs(jobsData);
      setError(null);
    } catch (err) {
      const errorMessage = 'Failed to load batch jobs';
      setError(errorMessage);
      ErrorHandler.logError(err as Error, {
        component: 'BatchProcessing',
        operation: 'fetchJobs',
        details: { invokeCommand: 'get_all_batch_jobs' }
      });
    }
  }, []);

  // Fetch system status
  const fetchSystemStatus = useCallback(async () => {
    try {
      const status = await invoke<SystemStatus>('get_batch_system_status');
      setSystemStatus(status);
      setError(null);
    } catch (err) {
      const errorMessage = 'Failed to load system status';
      setError(errorMessage);
      ErrorHandler.logError(err as Error, {
        component: 'BatchProcessing',
        operation: 'fetchSystemStatus',
        details: { invokeCommand: 'get_batch_system_status' }
      });
    }
  }, []);

  // Initial data load
  useEffect(() => {
    const loadInitialData = async () => {
      setLoading(true);
      await Promise.all([
        fetchJobs(),
        fetchSystemStatus()
      ]);
      setLoading(false);
    };

    loadInitialData();
  }, [fetchJobs, fetchSystemStatus]);

  // Auto-refresh jobs and system status
  useEffect(() => {
    const interval = setInterval(() => {
      fetchJobs();
      fetchSystemStatus();
    }, 5000); // Refresh every 5 seconds

    return () => clearInterval(interval);
  }, [fetchJobs, fetchSystemStatus]);

  // Create new batch job
  const createJob = useCallback(async (jobData: BatchJobCreate) => {
    try {
      await invoke('create_batch_job', { jobData });
      await fetchJobs(); // Refresh jobs list
    } catch (err) {
      console.error('Failed to create batch job:', err);
      throw new Error('Failed to create batch job');
    }
  }, [fetchJobs]);

  // Pause a running job
  const pauseJob = useCallback(async (jobId: string) => {
    try {
      await invoke('pause_batch_job', { jobId });
      await fetchJobs(); // Refresh jobs list
    } catch (err) {
      console.error('Failed to pause job:', err);
      throw new Error('Failed to pause job');
    }
  }, [fetchJobs]);

  // Resume a paused job
  const resumeJob = useCallback(async (jobId: string) => {
    try {
      await invoke('resume_batch_job', { jobId });
      await fetchJobs(); // Refresh jobs list
    } catch (err) {
      console.error('Failed to resume job:', err);
      throw new Error('Failed to resume job');
    }
  }, [fetchJobs]);

  // Cancel a job
  const cancelJob = useCallback(async (jobId: string) => {
    try {
      await invoke('cancel_batch_job', { jobId });
      await fetchJobs(); // Refresh jobs list
    } catch (err) {
      console.error('Failed to cancel job:', err);
      throw new Error('Failed to cancel job');
    }
  }, [fetchJobs]);

  // Delete a job
  const deleteJob = useCallback(async (jobId: string) => {
    try {
      await invoke('delete_batch_job', { jobId });
      await fetchJobs(); // Refresh jobs list
    } catch (err) {
      console.error('Failed to delete job:', err);
      throw new Error('Failed to delete job');
    }
  }, [fetchJobs]);

  // Export job results
  const exportJobResults = useCallback(async (jobId: string, format: string) => {
    try {
      await invoke('export_batch_results', { jobId, format });
    } catch (err) {
      console.error('Failed to export job results:', err);
      throw new Error('Failed to export job results');
    }
  }, []);

  // Manual refresh actions
  const refreshJobs = useCallback(async () => {
    await fetchJobs();
  }, [fetchJobs]);

  const refreshSystemStatus = useCallback(async () => {
    await fetchSystemStatus();
  }, [fetchSystemStatus]);

  return {
    // Data
    jobs,
    systemStatus,
    
    // Loading states
    loading,
    error,
    
    // Actions
    createJob,
    pauseJob,
    resumeJob,
    cancelJob,
    deleteJob,
    exportJobResults,
    
    // System actions
    refreshJobs,
    refreshSystemStatus,
  };
}
