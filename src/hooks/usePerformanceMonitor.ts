import { useState, useEffect, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

export interface PerformanceMetrics {
  cpu_usage: number;
  memory_usage: number;
  memory_total: number;
  disk_usage: number;
  disk_total: number;
  active_tasks: number;
  completed_tasks: number;
  average_task_duration: {
    secs: number;
    nanos: number;
  };
  uptime: {
    secs: number;
    nanos: number;
  };
}

export interface BackgroundTask {
  id: string;
  task_type: string;
  priority: string;
  status: string;
  progress: number;
  message: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  metadata: any;
}

export interface TaskSubmissionRequest {
  task_type: string;
  priority: string;
  metadata: any;
}

export interface SystemOptimizationRequest {
  optimization_type: 'low_memory' | 'performance' | 'balanced';
}

export interface SystemHealthSummary {
  health_status: 'healthy' | 'warning' | 'critical';
  performance: {
    cpu_usage: number;
    memory_usage_mb: number;
    memory_total_mb: number;
    memory_usage_percent: number;
    uptime_seconds: number;
    average_task_duration_seconds: number;
  };
  tasks: {
    active_count: number;
    queue_length: number;
    statistics: any;
  };
  recommendation: string;
  timestamp: string;
}

export const usePerformanceMonitor = () => {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [tasks, setTasks] = useState<BackgroundTask[]>([]);
  const [queueLength, setQueueLength] = useState<number>(0);
  const [recommendation, setRecommendation] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [healthSummary, setHealthSummary] = useState<SystemHealthSummary | null>(null);

  // Get current performance metrics
  const getMetrics = useCallback(async () => {
    try {
      setError(null);
      const result = await invoke<PerformanceMetrics>('get_performance_metrics');
      setMetrics(result);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get performance metrics';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  // Get resource usage recommendation
  const getRecommendation = useCallback(async () => {
    try {
      setError(null);
      const result = await invoke<string>('get_resource_recommendation');
      setRecommendation(result);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get recommendation';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  // Optimize system performance
  const optimizeSystem = useCallback(async (request: SystemOptimizationRequest) => {
    try {
      setError(null);
      setLoading(true);
      const result = await invoke<string>('optimize_system_performance', { request });
      
      // Refresh metrics after optimization
      await getMetrics();
      await getRecommendation();
      
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to optimize system';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [getMetrics, getRecommendation]);

  // Submit background task
  const submitTask = useCallback(async (request: TaskSubmissionRequest) => {
    try {
      setError(null);
      setLoading(true);
      const taskId = await invoke<string>('submit_background_task', { request });
      
      // Refresh task list
      await getAllTasks();
      
      return taskId;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to submit task';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  // Cancel background task
  const cancelTask = useCallback(async (taskId: string) => {
    try {
      setError(null);
      setLoading(true);
      const result = await invoke<string>('cancel_background_task', { taskId });
      
      // Refresh task list
      await getAllTasks();
      
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to cancel task';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  // Get all background tasks
  const getAllTasks = useCallback(async () => {
    try {
      setError(null);
      const result = await invoke<BackgroundTask[]>('get_all_background_tasks');
      setTasks(result);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get tasks';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  // Get task queue length
  const getQueueLength = useCallback(async () => {
    try {
      setError(null);
      const result = await invoke<number>('get_task_queue_length');
      setQueueLength(result);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get queue length';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  // Get task status
  const getTaskStatus = useCallback(async (taskId: string) => {
    try {
      setError(null);
      const result = await invoke<BackgroundTask | null>('get_task_status', { taskId });
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get task status';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  // Get system statistics
  const getSystemStats = useCallback(async () => {
    try {
      setError(null);
      const result = await invoke<any>('get_background_system_stats');
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get system stats';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  // Export performance metrics
  const exportMetrics = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const result = await invoke<string>('export_performance_metrics');
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to export metrics';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  // Cleanup old data
  const cleanupData = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const result = await invoke<string>('cleanup_performance_data');
      
      // Refresh metrics after cleanup
      await getMetrics();
      await getAllTasks();
      
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to cleanup data';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [getMetrics, getAllTasks]);

  // Refresh all data
  const refreshAll = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      
      await Promise.all([
        getMetrics(),
        getAllTasks(),
        getQueueLength(),
        getRecommendation(),
      ]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to refresh data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [getMetrics, getAllTasks, getQueueLength, getRecommendation]);

  // Auto-refresh data periodically
  useEffect(() => {
    refreshAll();
    
    const interval = setInterval(() => {
      refreshAll();
    }, 5000); // Refresh every 5 seconds
    
    return () => clearInterval(interval);
  }, [refreshAll]);

  // Utility functions for display
  const getMemoryUsagePercent = useCallback(() => {
    if (!metrics) return 0;
    return (metrics.memory_usage / metrics.memory_total) * 100;
  }, [metrics]);

  const getDiskUsagePercent = useCallback(() => {
    if (!metrics) return 0;
    return (metrics.disk_usage / metrics.disk_total) * 100;
  }, [metrics]);

  const getAverageTaskDurationSeconds = useCallback(() => {
    if (!metrics) return 0;
    return metrics.average_task_duration.secs + (metrics.average_task_duration.nanos / 1_000_000_000);
  }, [metrics]);

  const getUptimeSeconds = useCallback(() => {
    if (!metrics) return 0;
    return metrics.uptime.secs + (metrics.uptime.nanos / 1_000_000_000);
  }, [metrics]);

  const getHealthStatus = useCallback(() => {
    if (!metrics) return 'unknown';
    
    const memoryPercent = getMemoryUsagePercent();
    
    if (metrics.cpu_usage > 90 || memoryPercent > 90) {
      return 'critical';
    } else if (metrics.cpu_usage > 70 || memoryPercent > 75) {
      return 'warning';
    } else {
      return 'healthy';
    }
  }, [metrics, getMemoryUsagePercent]);

  const getActiveTasks = useCallback(() => {
    return tasks.filter(task => task.status === 'Running' || task.status === 'Queued');
  }, [tasks]);

  const getCompletedTasks = useCallback(() => {
    return tasks.filter(task => task.status === 'Completed');
  }, [tasks]);

  const getFailedTasks = useCallback(() => {
    return tasks.filter(task => task.status === 'Failed');
  }, [tasks]);

  return {
    // State
    metrics,
    tasks,
    queueLength,
    recommendation,
    loading,
    error,
    healthSummary,
    
    // Actions
    getMetrics,
    getRecommendation,
    optimizeSystem,
    submitTask,
    cancelTask,
    getAllTasks,
    getQueueLength,
    getTaskStatus,
    getSystemStats,
    exportMetrics,
    cleanupData,
    refreshAll,
    
    // Utilities
    getMemoryUsagePercent,
    getDiskUsagePercent,
    getAverageTaskDurationSeconds,
    getUptimeSeconds,
    getHealthStatus,
    getActiveTasks,
    getCompletedTasks,
    getFailedTasks,
  };
};

export default usePerformanceMonitor;
