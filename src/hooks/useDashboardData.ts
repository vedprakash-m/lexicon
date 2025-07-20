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
      
      // **FIX**: Use get_all_books instead of get_all_source_texts to match catalog data
      const books = await invoke<any[]>('get_all_books');
      
      // Fetch datasets for chunk count
      const datasets = await invoke<any[]>('get_all_datasets');
      
      // Calculate quality score (average of all books with quality scores)
      const booksWithQuality = books && Array.isArray(books) ? 
        books.filter(book => book.quality_score && book.quality_score > 0) : [];
      
      const qualityScore = booksWithQuality.length > 0 ? 
        Math.round(booksWithQuality.reduce((sum, book) => sum + (book.quality_score || 0), 0) / booksWithQuality.length) : null;

      // Calculate total chunks across all datasets with null checks
      const totalChunks = datasets && Array.isArray(datasets) ? 
        datasets.reduce((total, dataset) => {
          return total + (dataset.chunks ? dataset.chunks.length : 0);
        }, 0) : 0;

      // Generate recent activities from books (simplified for BookMetadata)
      const recentActivities: RecentActivity[] = [];
      
      // Add recent book additions (with null check)
      if (books && Array.isArray(books)) {
        books
          .slice(0, 5)
          .forEach(book => {
            recentActivities.push({
              id: book.id,
              type: 'book_added',
              title: `Added "${book.title}"`,
              description: `Book by ${book.authors?.[0]?.name || 'Unknown Author'} added to library`,
              timestamp: new Date().toISOString(), // Default to current time since BookMetadata doesn't have created_at
              status: 'success'
            });
          });
      }

      // For BookMetadata, we don't have processing status, so no processing tasks
      const processingTasks: ProcessingTask[] = [];

      // Count active processing tasks (none for BookMetadata)
      const activeProcessing = 0;

      const dashboardData: DashboardData = {
        stats: {
          total_books: books && Array.isArray(books) ? books.length : 0,
          active_processing: activeProcessing,
          chunks_created: totalChunks,
          quality_score: qualityScore,
        },
        recent_activities: recentActivities.slice(0, 5),
        processing_tasks: processingTasks,
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
