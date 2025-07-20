import React, { ComponentType, useEffect } from 'react';

export interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  category: 'bundle' | 'runtime' | 'vitals' | 'custom';
}

export interface WebVitalsMetrics {
  fcp: number | null; // First Contentful Paint
  lcp: number | null; // Largest Contentful Paint
  cls: number | null; // Cumulative Layout Shift
  fid: number | null; // First Input Delay
  ttfb: number | null; // Time to First Byte
}

export class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics: PerformanceMetric[] = [];
  private customMetrics: Record<string, number> = {};
  private observers: PerformanceObserver[] = [];
  private memoryUsage: number[] = [];
  private renderTimes: Map<string, number[]> = new Map();
  
  private constructor() {
    this.initializeWebVitals();
    this.initializeBundleMetrics();
    this.initializeMemoryMonitoring();
  }
  
  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  /**
   * Initialize Web Vitals monitoring
   */
  private initializeWebVitals(): void {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) {
      return;
    }

    // First Contentful Paint (FCP)
    try {
      const fcpObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        if (entries.length > 0) {
          const fcp = entries[0];
          this.recordMetric('fcp', fcp.startTime, 'vitals');
        }
      });
      fcpObserver.observe({ type: 'paint', buffered: true });
      this.observers.push(fcpObserver);
    } catch (e) {
      console.warn('FCP monitoring not supported:', e);
    }

    // Largest Contentful Paint (LCP)
    try {
      const lcpObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        if (entries.length > 0) {
          const lcp = entries[entries.length - 1];
          this.recordMetric('lcp', lcp.startTime, 'vitals');
        }
      });
      lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
      this.observers.push(lcpObserver);
    } catch (e) {
      console.warn('LCP monitoring not supported:', e);
    }

    // Cumulative Layout Shift (CLS)
    try {
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((entryList) => {
        for (const entry of entryList.getEntries()) {
          if (!(entry as any).hadRecentInput) {
            clsValue += (entry as any).value;
            this.recordMetric('cls', clsValue, 'vitals');
          }
        }
      });
      clsObserver.observe({ type: 'layout-shift', buffered: true });
      this.observers.push(clsObserver);
    } catch (e) {
      console.warn('CLS monitoring not supported:', e);
    }

    // First Input Delay (FID)
    try {
      const fidObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        if (entries.length > 0) {
          const fid = entries[0];
          const delay = (fid as any).processingStart - (fid as any).startTime;
          this.recordMetric('fid', delay, 'vitals');
        }
      });
      fidObserver.observe({ type: 'first-input', buffered: true });
      this.observers.push(fidObserver);
    } catch (e) {
      console.warn('FID monitoring not supported:', e);
    }
  }

  /**
   * Initialize bundle and resource metrics
   */
  private initializeBundleMetrics(): void {
    if (typeof window === 'undefined') return;

    // Monitor resource loading
    try {
      const resourceObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        entries.forEach((entry) => {
          if (entry.name.includes('.js') || entry.name.includes('.css')) {
            this.recordMetric(
              `resource_${entry.name.split('/').pop()}`,
              entry.duration,
              'bundle'
            );
          }
        });
      });
      resourceObserver.observe({ type: 'resource', buffered: true });
      this.observers.push(resourceObserver);
    } catch (e) {
      console.warn('Resource monitoring not supported:', e);
    }

    // Monitor navigation timing
    if (performance.getEntriesByType) {
      const navEntries = performance.getEntriesByType('navigation');
      if (navEntries.length > 0) {
        const nav = navEntries[0] as PerformanceNavigationTiming;
        this.recordMetric('ttfb', nav.responseStart - nav.requestStart, 'vitals');
        this.recordMetric('dom_load', nav.domContentLoadedEventEnd - nav.navigationStart, 'runtime');
        this.recordMetric('page_load', nav.loadEventEnd - nav.navigationStart, 'runtime');
      }
    }
  }

  /**
   * Initialize memory monitoring
   */
  private initializeMemoryMonitoring(): void {
    if (typeof window === 'undefined') return;

    // Monitor memory usage
    const monitorMemory = () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        this.recordMetric('memory_used', memory.usedJSHeapSize, 'runtime');
        this.recordMetric('memory_total', memory.totalJSHeapSize, 'runtime');
        this.recordMetric('memory_limit', memory.jsHeapSizeLimit, 'runtime');
        
        this.memoryUsage.push(memory.usedJSHeapSize);
        if (this.memoryUsage.length > 100) {
          this.memoryUsage = this.memoryUsage.slice(-100);
        }
      }
    };

    // Monitor every 5 seconds
    setInterval(monitorMemory, 5000);
    monitorMemory(); // Initial measurement
  }

  /**
   * Record a performance metric
   */
  recordMetric(name: string, value: number, category: PerformanceMetric['category'] = 'custom'): void {
    const metric: PerformanceMetric = {
      name,
      value,
      timestamp: Date.now(),
      category
    };
    
    this.metrics.push(metric);
    this.customMetrics[name] = value;

    // Keep only last 1000 metrics to prevent memory leaks
    if (this.metrics.length > 1000) {
      this.metrics = this.metrics.slice(-1000);
    }
  }

  /**
   * Start timing an operation
   */
  startTimer(name: string): () => void {
    const startTime = performance.now();
    
    return () => {
      const endTime = performance.now();
      const duration = endTime - startTime;
      this.recordMetric(`timer_${name}`, duration, 'custom');
    };
  }

  /**
   * Measure React component render time
   */
  measureComponentRender<T extends ComponentType<any>>(
    Component: T,
    displayName?: string
  ): T {
    const componentName = displayName || Component.displayName || Component.name || 'Anonymous';
    
    return React.memo(React.forwardRef<any, any>((props, ref) => {
      const renderStart = performance.now();
      
      useEffect(() => {
        const renderEnd = performance.now();
        const renderTime = renderEnd - renderStart;
        this.recordMetric(`component_render_${componentName}`, renderTime, 'runtime');
        
        // Track render times for this component
        if (!this.renderTimes.has(componentName)) {
          this.renderTimes.set(componentName, []);
        }
        const times = this.renderTimes.get(componentName)!;
        times.push(renderTime);
        if (times.length > 50) {
          times.splice(0, times.length - 50);
        }
      });
      
      return React.createElement(Component, { ...props, ref });
    })) as T;
  }

  /**
   * Get Web Vitals metrics
   */
  getWebVitals(): WebVitalsMetrics {
    return {
      fcp: this.customMetrics['fcp'] || null,
      lcp: this.customMetrics['lcp'] || null,
      cls: this.customMetrics['cls'] || null,
      fid: this.customMetrics['fid'] || null,
      ttfb: this.customMetrics['ttfb'] || null,
    };
  }

  /**
   * Get performance summary
   */
  getPerformanceSummary(): {
    webVitals: WebVitalsMetrics;
    memoryUsage: {
      current: number;
      average: number;
      peak: number;
    };
    renderPerformance: {
      slowestComponents: Array<{ name: string; averageTime: number; maxTime: number }>;
    };
    bundleMetrics: {
      totalLoadTime: number;
      resourceCount: number;
    };
  } {
    const webVitals = this.getWebVitals();
    
    // Memory usage stats
    const currentMemory = this.customMetrics['memory_used'] || 0;
    const averageMemory = this.memoryUsage.length > 0 
      ? this.memoryUsage.reduce((a, b) => a + b, 0) / this.memoryUsage.length 
      : 0;
    const peakMemory = Math.max(...this.memoryUsage, 0);

    // Component render performance
    const slowestComponents = Array.from(this.renderTimes.entries())
      .map(([name, times]) => ({
        name,
        averageTime: times.reduce((a, b) => a + b, 0) / times.length,
        maxTime: Math.max(...times)
      }))
      .sort((a, b) => b.averageTime - a.averageTime)
      .slice(0, 10);

    // Bundle metrics
    const resourceMetrics = this.metrics.filter(m => m.category === 'bundle');
    const totalLoadTime = this.customMetrics['page_load'] || 0;
    const resourceCount = resourceMetrics.length;

    return {
      webVitals,
      memoryUsage: {
        current: currentMemory,
        average: averageMemory,
        peak: peakMemory
      },
      renderPerformance: {
        slowestComponents
      },
      bundleMetrics: {
        totalLoadTime,
        resourceCount
      }
    };
  }

  /**
   * Check if performance is within acceptable thresholds
   */
  checkPerformanceThresholds(): {
    passed: boolean;
    issues: string[];
    warnings: string[];
  } {
    const issues: string[] = [];
    const warnings: string[] = [];
    const vitals = this.getWebVitals();

    // Check Web Vitals thresholds
    if (vitals.fcp && vitals.fcp > 1800) {
      issues.push(`First Contentful Paint too slow: ${vitals.fcp.toFixed(0)}ms (should be < 1800ms)`);
    } else if (vitals.fcp && vitals.fcp > 1000) {
      warnings.push(`First Contentful Paint could be faster: ${vitals.fcp.toFixed(0)}ms`);
    }

    if (vitals.lcp && vitals.lcp > 2500) {
      issues.push(`Largest Contentful Paint too slow: ${vitals.lcp.toFixed(0)}ms (should be < 2500ms)`);
    } else if (vitals.lcp && vitals.lcp > 1500) {
      warnings.push(`Largest Contentful Paint could be faster: ${vitals.lcp.toFixed(0)}ms`);
    }

    if (vitals.cls && vitals.cls > 0.1) {
      issues.push(`Cumulative Layout Shift too high: ${vitals.cls.toFixed(3)} (should be < 0.1)`);
    } else if (vitals.cls && vitals.cls > 0.05) {
      warnings.push(`Cumulative Layout Shift could be lower: ${vitals.cls.toFixed(3)}`);
    }

    if (vitals.fid && vitals.fid > 100) {
      issues.push(`First Input Delay too high: ${vitals.fid.toFixed(0)}ms (should be < 100ms)`);
    } else if (vitals.fid && vitals.fid > 50) {
      warnings.push(`First Input Delay could be lower: ${vitals.fid.toFixed(0)}ms`);
    }

    // Check memory usage
    const currentMemory = this.customMetrics['memory_used'] || 0;
    const memoryMB = currentMemory / (1024 * 1024);
    
    if (memoryMB > 500) {
      issues.push(`Memory usage too high: ${memoryMB.toFixed(0)}MB (should be < 500MB)`);
    } else if (memoryMB > 300) {
      warnings.push(`Memory usage getting high: ${memoryMB.toFixed(0)}MB`);
    }

    // Check component render times
    const slowComponents = Array.from(this.renderTimes.entries())
      .filter(([_, times]) => {
        const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
        return avgTime > 16; // 60fps threshold
      });

    if (slowComponents.length > 0) {
      warnings.push(`${slowComponents.length} components rendering slowly (>16ms)`);
    }

    return {
      passed: issues.length === 0,
      issues,
      warnings
    };
  }

  /**
   * Get optimization recommendations
   */
  getOptimizationRecommendations(): string[] {
    const recommendations: string[] = [];
    const vitals = this.getWebVitals();
    const summary = this.getPerformanceSummary();

    // Bundle optimization
    if (vitals.fcp && vitals.fcp > 1500) {
      recommendations.push('Consider code splitting to reduce initial bundle size');
      recommendations.push('Implement lazy loading for non-critical components');
    }

    // Memory optimization
    if (summary.memoryUsage.current > 300 * 1024 * 1024) {
      recommendations.push('Implement memory cleanup in useEffect hooks');
      recommendations.push('Consider virtualizing large lists');
      recommendations.push('Review for memory leaks in event listeners');
    }

    // Render optimization
    if (summary.renderPerformance.slowestComponents.length > 0) {
      recommendations.push('Optimize slow-rendering components with React.memo');
      recommendations.push('Consider useMemo for expensive calculations');
      recommendations.push('Implement debouncing for frequent state updates');
    }

    // Layout optimization
    if (vitals.cls && vitals.cls > 0.05) {
      recommendations.push('Reserve space for dynamic content to reduce layout shifts');
      recommendations.push('Use CSS transforms instead of changing layout properties');
    }

    return recommendations;
  }

  /**
   * Export performance data
   */
  exportData(): {
    timestamp: number;
    metrics: PerformanceMetric[];
    summary: ReturnType<typeof this.getPerformanceSummary>;
    thresholds: ReturnType<typeof this.checkPerformanceThresholds>;
    recommendations: string[];
  } {
    return {
      timestamp: Date.now(),
      metrics: [...this.metrics],
      summary: this.getPerformanceSummary(),
      thresholds: this.checkPerformanceThresholds(),
      recommendations: this.getOptimizationRecommendations()
    };
  }

  /**
   * Clear all metrics
   */
  clearMetrics(): void {
    this.metrics = [];
    this.customMetrics = {};
    this.memoryUsage = [];
    this.renderTimes.clear();
  }

  /**
   * Cleanup observers
   */
  cleanup(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }
}