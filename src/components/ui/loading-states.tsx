/**
 * Enhanced Loading States
 * 
 * Provides contextual loading experiences for different parts of the application
 * with skeleton placeholders and smooth transitions.
 */

import { Skeleton, SkeletonCard, SkeletonTable, SkeletonList } from '@/components/ui/skeleton';
import { Loader2, BookOpen, Settings, Database, Zap } from 'lucide-react';

// Generic route loading spinner (existing)
export const RouteLoadingSpinner = () => (
  <div className="flex items-center justify-center h-64">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    <span className="ml-2 text-sm text-gray-600">Loading...</span>
  </div>
);

// Enhanced route-specific loading states
export const DashboardLoading = () => (
  <div className="p-6 space-y-6">
    <div className="flex items-center space-x-2 mb-6">
      <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
      <span className="text-lg font-semibold">Loading Dashboard...</span>
    </div>
    
    {/* Stats cards */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <SkeletonCard key={i} className="h-24" />
      ))}
    </div>
    
    {/* Recent activity */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="space-y-3">
        <Skeleton className="h-6 w-32" />
        <SkeletonList items={3} />
      </div>
      <div className="space-y-3">
        <Skeleton className="h-6 w-40" />
        <SkeletonTable rows={3} columns={3} />
      </div>
    </div>
  </div>
);

export const CatalogLoading = () => (
  <div className="p-6 space-y-6">
    <div className="flex items-center space-x-2 mb-6">
      <BookOpen className="h-5 w-5 animate-pulse text-green-600" />
      <span className="text-lg font-semibold">Loading Library...</span>
    </div>
    
    {/* Search and filters */}
    <div className="flex space-x-4 mb-6">
      <Skeleton className="h-10 flex-1" />
      <Skeleton className="h-10 w-32" />
      <Skeleton className="h-10 w-24" />
    </div>
    
    {/* Book grid */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="space-y-3">
          <Skeleton variant="card" className="h-48" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      ))}
    </div>
  </div>
);

export const ProjectLoading = () => (
  <div className="p-6 space-y-6">
    <div className="flex items-center space-x-2 mb-6">
      <Settings className="h-5 w-5 animate-pulse text-purple-600" />
      <span className="text-lg font-semibold">Loading Projects...</span>
    </div>
    
    {/* Project header */}
    <div className="flex justify-between items-center">
      <Skeleton className="h-8 w-48" />
      <Skeleton variant="button" className="h-10 w-32" />
    </div>
    
    {/* Project cards */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Array.from({ length: 6 }).map((_, i) => (
        <SkeletonCard key={i} className="h-40" />
      ))}
    </div>
  </div>
);

export const ProcessingLoading = () => (
  <div className="p-6 space-y-6">
    <div className="flex items-center space-x-2 mb-6">
      <Database className="h-5 w-5 animate-pulse text-orange-600" />
      <span className="text-lg font-semibold">Loading Processing...</span>
    </div>
    
    {/* Processing queue */}
    <div className="space-y-4">
      <Skeleton className="h-6 w-40" />
      <SkeletonTable rows={5} columns={5} />
    </div>
    
    {/* Processing options */}
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <SkeletonCard className="h-32" />
      <SkeletonCard className="h-32" />
    </div>
  </div>
);

export const PerformanceLoading = () => (
  <div className="p-6 space-y-6">
    <div className="flex items-center space-x-2 mb-6">
      <Zap className="h-5 w-5 animate-pulse text-yellow-600" />
      <span className="text-lg font-semibold">Loading Performance Dashboard...</span>
    </div>
    
    {/* Performance metrics */}
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {Array.from({ length: 3 }).map((_, i) => (
        <SkeletonCard key={i} className="h-24" />
      ))}
    </div>
    
    {/* Charts placeholder */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Skeleton variant="card" className="h-64" />
      <Skeleton variant="card" className="h-64" />
    </div>
  </div>
);

// Loading state router - returns appropriate loading component based on route
export const getRouteLoadingComponent = (route: string) => {
  switch (route) {
    case '/':
    case '/dashboard':
      return DashboardLoading;
    case '/library':
      return CatalogLoading;
    case '/projects':
      return ProjectLoading;
    case '/batch':
    case '/chunking':
    case '/scraping':
      return ProcessingLoading;
    case '/performance':
      return PerformanceLoading;
    default:
      return RouteLoadingSpinner;
  }
};

export default {
  RouteLoadingSpinner,
  DashboardLoading,
  CatalogLoading,
  ProjectLoading,
  ProcessingLoading,
  PerformanceLoading,
  getRouteLoadingComponent,
};
