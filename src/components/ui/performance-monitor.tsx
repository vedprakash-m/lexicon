/**
 * Performance Monitor
 * 
 * Tracks and reports application performance metrics including:
 * - Route load times
 * - Bundle loading performance
 * - User interaction metrics
 * - Core Web Vitals
 */

import { useEffect, useCallback, useRef } from 'react';
import { useLocation } from 'react-router-dom';

interface PerformanceMetrics {
  routeLoadTime: number;
  bundleLoadTime: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  cumulativeLayoutShift: number;
  firstInputDelay: number;
  timestamp: number;
  route: string;
  userAgent: string;
}

interface NavigationTiming {
  route: string;
  startTime: number;
  endTime: number;
  duration: number;
  fromRoute: string;
}

// Performance data storage
class PerformanceTracker {
  private metrics: PerformanceMetrics[] = [];
  private navigationTimings: NavigationTiming[] = [];
  private currentRouteStart: number = 0;
  private lastRoute: string = '';

  // Track route navigation performance
  startRouteTimer(route: string, fromRoute: string = '') {
    this.currentRouteStart = performance.now();
    this.lastRoute = fromRoute;
  }

  endRouteTimer(route: string) {
    if (this.currentRouteStart > 0) {
      const endTime = performance.now();
      const duration = endTime - this.currentRouteStart;
      
      this.navigationTimings.push({
        route,
        startTime: this.currentRouteStart,
        endTime,
        duration,
        fromRoute: this.lastRoute,
      });

      // Reset for next navigation
      this.currentRouteStart = 0;
    }
  }

  // Collect Web Vitals and performance metrics
  async collectMetrics(route: string): Promise<PerformanceMetrics | null> {
    try {
      // Check if performance APIs are available (not in test environment)
      if (typeof window === 'undefined' || !window.performance || !window.performance.getEntriesByType) {
        return null;
      }

      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const paint = performance.getEntriesByType('paint');
      
      const fcp = paint.find(entry => entry.name === 'first-contentful-paint')?.startTime || 0;
      
      // Get current metrics with safe fallbacks
      const metrics: PerformanceMetrics = {
        routeLoadTime: this.getLastNavigationDuration(),
        bundleLoadTime: navigation?.loadEventEnd && navigation?.loadEventStart 
          ? navigation.loadEventEnd - navigation.loadEventStart 
          : 0,
        firstContentfulPaint: fcp,
        largestContentfulPaint: 0, // Will be updated by observer
        cumulativeLayoutShift: 0, // Will be updated by observer
        firstInputDelay: 0, // Will be updated by observer
        timestamp: Date.now(),
        route,
        userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'test-environment',
      };

      this.metrics.push(metrics);
      return metrics;
    } catch (error) {
      console.warn('Failed to collect performance metrics:', error);
      return null;
    }
  }

  getLastNavigationDuration(): number {
    return this.navigationTimings.length > 0 
      ? this.navigationTimings[this.navigationTimings.length - 1].duration 
      : 0;
  }

  // Get performance analytics
  getAnalytics() {
    const routeMetrics = this.navigationTimings.reduce((acc, timing) => {
      if (!acc[timing.route]) {
        acc[timing.route] = {
          count: 0,
          totalTime: 0,
          avgTime: 0,
          minTime: Infinity,
          maxTime: 0,
        };
      }
      
      const metric = acc[timing.route];
      metric.count++;
      metric.totalTime += timing.duration;
      metric.avgTime = metric.totalTime / metric.count;
      metric.minTime = Math.min(metric.minTime, timing.duration);
      metric.maxTime = Math.max(metric.maxTime, timing.duration);
      
      return acc;
    }, {} as Record<string, any>);

    return {
      navigationCount: this.navigationTimings.length,
      uniqueRoutes: Object.keys(routeMetrics).length,
      routeMetrics,
      recentNavigations: this.navigationTimings.slice(-10),
      averageNavigationTime: this.navigationTimings.reduce((sum, nav) => sum + nav.duration, 0) / this.navigationTimings.length || 0,
    };
  }

  // Export metrics for analysis
  exportMetrics() {
    return {
      performanceMetrics: this.metrics,
      navigationTimings: this.navigationTimings,
      analytics: this.getAnalytics(),
      exportedAt: new Date().toISOString(),
    };
  }

  // Clear old data to prevent memory bloat
  cleanup() {
    const oneHourAgo = Date.now() - (60 * 60 * 1000);
    this.metrics = this.metrics.filter(m => m.timestamp > oneHourAgo);
    this.navigationTimings = this.navigationTimings.slice(-50); // Keep last 50 navigations
  }
}

// Global performance tracker instance
const performanceTracker = new PerformanceTracker();

// React hook for performance monitoring
export const usePerformanceMonitor = () => {
  const location = useLocation();
  const previousRoute = useRef(location.pathname);

  // Track route changes
  useEffect(() => {
    const currentRoute = location.pathname;
    const fromRoute = previousRoute.current;

    // End previous route timer and start new one
    if (fromRoute !== currentRoute) {
      performanceTracker.endRouteTimer(fromRoute);
      performanceTracker.startRouteTimer(currentRoute, fromRoute);
    }

    // Collect metrics after a short delay to allow content to load
    const timeoutId = setTimeout(() => {
      performanceTracker.collectMetrics(currentRoute);
    }, 100);

    previousRoute.current = currentRoute;

    return () => clearTimeout(timeoutId);
  }, [location.pathname]);

  // Cleanup on unmount
  useEffect(() => {
    const interval = setInterval(() => {
      performanceTracker.cleanup();
    }, 5 * 60 * 1000); // Clean up every 5 minutes

    return () => clearInterval(interval);
  }, []);

  return {
    getAnalytics: () => performanceTracker.getAnalytics(),
    exportMetrics: () => performanceTracker.exportMetrics(),
  };
};

// Web Vitals observer setup
const setupWebVitalsObserver = () => {
  // Skip in test environments or if PerformanceObserver is not available
  if (typeof window === 'undefined' || !('PerformanceObserver' in window) || process.env.NODE_ENV === 'test') {
    return;
  }

  try {
    // Largest Contentful Paint (LCP)
    const lcpObserver = new PerformanceObserver((entryList) => {
      const entries = entryList.getEntries();
      const lastEntry = entries[entries.length - 1];
      console.log('LCP:', lastEntry.startTime);
    });
    lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });

    // Cumulative Layout Shift (CLS)
    const clsObserver = new PerformanceObserver((entryList) => {
      const entries = entryList.getEntries();
      let cls = 0;
      entries.forEach((entry: any) => {
        if (!entry.hadRecentInput) {
          cls += entry.value;
        }
      });
      console.log('CLS:', cls);
    });
    clsObserver.observe({ entryTypes: ['layout-shift'] });

    // First Input Delay (FID)
    const fidObserver = new PerformanceObserver((entryList) => {
      const entries = entryList.getEntries();
      entries.forEach((entry: any) => {
        console.log('FID:', entry.processingStart - entry.startTime);
      });
    });
    fidObserver.observe({ entryTypes: ['first-input'] });

  } catch (error) {
    console.warn('Performance observers not fully supported:', error);
  }
};

// Initialize performance monitoring
export const initializePerformanceMonitoring = () => {
  // Skip performance monitoring in test environments
  if (typeof window === 'undefined' || typeof document === 'undefined' || process.env.NODE_ENV === 'test') {
    return;
  }

  // Set up Web Vitals observers
  setupWebVitalsObserver();

  // Track initial page load
  if (document.readyState === 'complete') {
    performanceTracker.collectMetrics(window.location.pathname);
  } else {
    window.addEventListener('load', () => {
      performanceTracker.collectMetrics(window.location.pathname);
    });
  }

  console.log('🚀 Performance monitoring initialized');
};

// Performance analytics component for debugging
export const PerformanceDebugger = () => {
  const { getAnalytics, exportMetrics } = usePerformanceMonitor();

  const handleExportMetrics = () => {
    const metrics = exportMetrics();
    const blob = new Blob([JSON.stringify(metrics, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `lexicon-performance-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const analytics = getAnalytics();

  if (process.env.NODE_ENV !== 'development') {
    return null; // Only show in development
  }

  return (
    <div className="fixed bottom-4 right-4 bg-white border border-gray-300 rounded-lg p-4 shadow-lg z-50 max-w-sm">
      <h3 className="font-semibold text-sm mb-2">Performance Monitor</h3>
      <div className="text-xs space-y-1">
        <div>Routes: {analytics.uniqueRoutes}</div>
        <div>Navigations: {analytics.navigationCount}</div>
        <div>Avg Time: {analytics.averageNavigationTime.toFixed(2)}ms</div>
        <button
          onClick={handleExportMetrics}
          className="mt-2 px-2 py-1 bg-blue-500 text-white rounded text-xs"
        >
          Export Metrics
        </button>
      </div>
    </div>
  );
};

export default performanceTracker;
