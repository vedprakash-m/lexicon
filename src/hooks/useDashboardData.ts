import { useState, useEffect, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { PerformanceMetrics } from './usePerformanceMonitor';

export interface DashboardStats {
  total_books: number;
  active_processing: number;
  chunks_created: number;
  quality_score: number | null;
}

export interface RecentActivity {
  id: string;
  type: 'book_added' | 'processing_completed' | 'dataset_generated' | 'error_occurred';
  title: string;
  description: string;
  timestamp: string;
  status?: 'success' | 'warning' | 'error';
}

export interface ProcessingTask {
  id: string;
  title: string;
  progress: number;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  estimated_completion?: string;
  current_step?: string;
}

export interface DashboardData {
  stats: DashboardStats;
  recent_activities: RecentActivity[];
  processing_tasks: ProcessingTask[];
  performance: PerformanceMetrics | null;
  last_updated: string;
}

export function useDashboardData() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch basic state statistics
      const stateStats = await invoke<any>('get_state_stats');
      
      // Fetch performance metrics
      const performance = await invoke<PerformanceMetrics>('get_performance_metrics');
      
      // Fetch source texts to calculate quality score
      const sourceTexts = await invoke<any[]>('get_all_source_texts');
      
      // Fetch datasets for chunk count
      const datasets = await invoke<any[]>('get_all_datasets');
      
      // Calculate quality score (average of all completed processing)
      const completedTexts = sourceTexts.filter(text => 
        text.processing_status && typeof text.processing_status === 'object' && 'Completed' in text.processing_status
      );
      
      const qualityScore = completedTexts.length > 0 ? 
        Math.round((completedTexts.length / sourceTexts.length) * 100) : null;

      // Calculate total chunks across all datasets
      const totalChunks = datasets.reduce((total, dataset) => {
        return total + (dataset.chunks ? dataset.chunks.length : 0);
      }, 0);

      // Generate recent activities from source texts and datasets
      const recentActivities: RecentActivity[] = [];
      
      // Add recent book additions
      sourceTexts
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, 3)
        .forEach(text => {
          recentActivities.push({
            id: text.id,
            type: 'book_added',
            title: `Added "${text.title}"`,
            description: `New ${text.source_type.toLowerCase()} added to library`,
            timestamp: text.created_at,
            status: 'success'
          });
        });

      // Add recent processing completions
      completedTexts
        .sort((a, b) => {
          const aTime = a.processing_status?.Completed?.completed_at || a.updated_at;
          const bTime = b.processing_status?.Completed?.completed_at || b.updated_at;
          return new Date(bTime).getTime() - new Date(aTime).getTime();
        })
        .slice(0, 2)
        .forEach(text => {
          recentActivities.push({
            id: `${text.id}_processed`,
            type: 'processing_completed',
            title: `Processed "${text.title}"`,
            description: `Text processing completed successfully`,
            timestamp: text.processing_status?.Completed?.completed_at || text.updated_at,
            status: 'success'
          });
        });

      // Generate processing tasks from in-progress items
      const processingTasks: ProcessingTask[] = sourceTexts
        .filter(text => 
          text.processing_status && 
          typeof text.processing_status === 'object' && 
          'InProgress' in text.processing_status
        )
        .map(text => ({
          id: text.id,
          title: text.title,
          progress: text.processing_status.InProgress?.progress_percent || 0,
          status: 'in_progress' as const,
          current_step: text.processing_status.InProgress?.current_step || 'Processing',
        }));

      // Count active processing tasks
      const activeProcessing = processingTasks.length + 
        sourceTexts.filter(text => 
          text.processing_status && 
          typeof text.processing_status === 'object' && 
          'Pending' in text.processing_status
        ).length;

      const dashboardData: DashboardData = {
        stats: {
          total_books: sourceTexts.length,
          active_processing: activeProcessing,
          chunks_created: totalChunks,
          quality_score: qualityScore,
        },
        recent_activities: recentActivities.slice(0, 5),
        processing_tasks,
        performance,
        last_updated: new Date().toISOString(),
      };

      setData(dashboardData);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
    
    // Set up polling for real-time updates
    const interval = setInterval(fetchDashboardData, 30000); // Update every 30 seconds
    
    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  const refresh = useCallback(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  return {
    data,
    loading,
    error,
    refresh,
  };
}
