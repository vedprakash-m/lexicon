/**
 * Real-time Performance Monitoring System
 * Tracks application performance metrics and provides insights
 */

import { invoke } from '@tauri-apps/api/core';

export interface PerformanceMetrics {
  cpu: {
    usage: number;
    cores: number;
    frequency?: number;
  };
  memory: {
    used: number;
    total: number;
    available: number;
    usage: number;
  };
  disk: {
    used: number;
    total: number;
    available: number;
    usage: number;
  };
  network: {
    bytesReceived: number;
    bytesSent: number;
    packetsReceived: number;
    packetsSent: number;
  };
  application: {
    uptime: number;
    tasksActive: number;
    tasksCompleted: number;
    errorCount: number;
    responseTime: number;
  };
  python: {
    memory: number;
    activeTasks: number;
    errorRate: number;
  };
}

export interface PerformanceAlert {
  id: string;
  type: 'cpu' | 'memory' | 'disk' | 'network' | 'application' | 'python';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  value: number;
  threshold: number;
  timestamp: Date;
  resolved: boolean;
}

export interface PerformanceConfig {
  monitoringEnabled: boolean;
  collectInterval: number; // milliseconds
  retentionPeriod: number; // hours
  alerts: {
    cpuThreshold: number;
    memoryThreshold: number;
    diskThreshold: number;
    responseTimeThreshold: number;
    errorRateThreshold: number;
  };
  autoOptimize: boolean;
}

export interface PerformanceRecommendation {
  id: string;
  category: 'memory' | 'cpu' | 'disk' | 'network' | 'application';
  title: string;
  description: string;
  impact: 'low' | 'medium' | 'high';
  action: string;
  automated: boolean;
}

type PerformanceEventCallback = (metrics: PerformanceMetrics) => void;
type AlertCallback = (alert: PerformanceAlert) => void;

class RealTimePerformanceMonitor {
  private metrics: PerformanceMetrics | null = null;
  private config: PerformanceConfig;
  private isMonitoring: boolean = false;
  private monitoringInterval: NodeJS.Timeout | null = null;
  private eventCallbacks: PerformanceEventCallback[] = [];
  private alertCallbacks: AlertCallback[] = [];
  private alerts: PerformanceAlert[] = [];
  private metricsHistory: Array<{ timestamp: Date; metrics: PerformanceMetrics }> = [];
  private startTime: Date = new Date();

  constructor() {
    this.config = this.getDefaultConfig();
    this.loadConfig();
  }

  private getDefaultConfig(): PerformanceConfig {
    return {
      monitoringEnabled: true,
      collectInterval: 5000, // 5 seconds
      retentionPeriod: 24, // 24 hours
      alerts: {
        cpuThreshold: 80,
        memoryThreshold: 85,
        diskThreshold: 90,
        responseTimeThreshold: 5000,
        errorRateThreshold: 5
      },
      autoOptimize: false
    };
  }

  private async loadConfig(): Promise<void> {
    try {
      const stored = localStorage.getItem('lexicon_performance_config');
      if (stored) {
        this.config = { ...this.config, ...JSON.parse(stored) };
      }
    } catch (error) {
      console.warn('Failed to load performance config:', error);
    }
  }

  private async saveConfig(): Promise<void> {
    try {
      localStorage.setItem('lexicon_performance_config', JSON.stringify(this.config));
    } catch (error) {
      console.warn('Failed to save performance config:', error);
    }
  }

  public async initialize(): Promise<void> {
    console.log('Initializing real-time performance monitor...');
    
    if (this.config.monitoringEnabled) {
      await this.startMonitoring();
    }

    // Clean up old metrics on startup
    this.cleanupOldMetrics();
  }

  public async startMonitoring(): Promise<void> {
    if (this.isMonitoring) {
      console.log('Performance monitoring already active');
      return;
    }

    console.log('Starting performance monitoring...');
    this.isMonitoring = true;
    this.startTime = new Date();

    // Initial metrics collection
    await this.collectMetrics();

    // Set up periodic collection
    this.monitoringInterval = setInterval(async () => {
      try {
        await this.collectMetrics();
      } catch (error) {
        console.error('Failed to collect performance metrics:', error);
      }
    }, this.config.collectInterval);
  }

  public stopMonitoring(): void {
    if (!this.isMonitoring) {
      return;
    }

    console.log('Stopping performance monitoring...');
    this.isMonitoring = false;

    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }
  }

  private async collectMetrics(): Promise<void> {
    try {
      // Get system metrics from Tauri backend
      const systemMetrics = await this.getSystemMetrics();
      
      // Get application metrics
      const appMetrics = await this.getApplicationMetrics();
      
      // Get Python-specific metrics
      const pythonMetrics = await this.getPythonMetrics();

      const metrics: PerformanceMetrics = {
        ...systemMetrics,
        application: appMetrics,
        python: pythonMetrics
      };

      this.metrics = metrics;
      
      // Store in history
      this.metricsHistory.push({
        timestamp: new Date(),
        metrics: { ...metrics }
      });

      // Clean up old history
      this.cleanupOldMetrics();

      // Check for alerts
      this.checkAlerts(metrics);

      // Notify listeners
      this.notifyEventCallbacks(metrics);

    } catch (error) {
      console.error('Failed to collect performance metrics:', error);
    }
  }

  private async getSystemMetrics(): Promise<Omit<PerformanceMetrics, 'application' | 'python'>> {
    try {
      // Try to get metrics from Tauri backend
      const backendMetrics = await invoke<any>('get_performance_metrics');
      return {
        cpu: {
          usage: backendMetrics.cpu_usage || 0,
          cores: backendMetrics.cpu_cores || navigator.hardwareConcurrency || 4,
          frequency: backendMetrics.cpu_frequency
        },
        memory: {
          used: backendMetrics.memory_used || 0,
          total: backendMetrics.memory_total || 8 * 1024 * 1024 * 1024, // 8GB default
          available: backendMetrics.memory_available || 0,
          usage: backendMetrics.memory_usage || 0
        },
        disk: {
          used: backendMetrics.disk_used || 0,
          total: backendMetrics.disk_total || 500 * 1024 * 1024 * 1024, // 500GB default
          available: backendMetrics.disk_available || 0,
          usage: backendMetrics.disk_usage || 0
        },
        network: {
          bytesReceived: backendMetrics.network_bytes_received || 0,
          bytesSent: backendMetrics.network_bytes_sent || 0,
          packetsReceived: backendMetrics.network_packets_received || 0,
          packetsSent: backendMetrics.network_packets_sent || 0
        }
      };
    } catch (error) {
      // Fallback to browser-based metrics
      return this.getBrowserMetrics();
    }
  }

  private getBrowserMetrics(): Omit<PerformanceMetrics, 'application' | 'python'> {
    const memory = (performance as any).memory || {};
    
    return {
      cpu: {
        usage: 0, // Not available in browser
        cores: navigator.hardwareConcurrency || 4
      },
      memory: {
        used: memory.usedJSHeapSize || 0,
        total: memory.totalJSHeapSize || 0,
        available: memory.jsHeapSizeLimit || 0,
        usage: memory.usedJSHeapSize && memory.totalJSHeapSize ? 
               (memory.usedJSHeapSize / memory.totalJSHeapSize) * 100 : 0
      },
      disk: {
        used: 0,
        total: 0,
        available: 0,
        usage: 0
      },
      network: {
        bytesReceived: 0,
        bytesSent: 0,
        packetsReceived: 0,
        packetsSent: 0
      }
    };
  }

  private async getApplicationMetrics(): Promise<PerformanceMetrics['application']> {
    const uptime = (new Date().getTime() - this.startTime.getTime()) / 1000;
    
    try {
      const backgroundStats = await invoke<any>('get_background_system_stats');
      const errorLog = localStorage.getItem('lexicon_error_log');
      const errors = errorLog ? JSON.parse(errorLog) : [];
      
      // Calculate recent error count (last hour)
      const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
      const recentErrors = errors.filter((error: any) => 
        new Date(error.context.timestamp) > oneHourAgo
      );

      return {
        uptime,
        tasksActive: backgroundStats?.active_tasks || 0,
        tasksCompleted: backgroundStats?.completed_tasks || 0,
        errorCount: recentErrors.length,
        responseTime: this.calculateAverageResponseTime()
      };
    } catch (error) {
      return {
        uptime,
        tasksActive: 0,
        tasksCompleted: 0,
        errorCount: 0,
        responseTime: 0
      };
    }
  }

  private async getPythonMetrics(): Promise<PerformanceMetrics['python']> {
    try {
      const pythonStats = await invoke<any>('get_python_environment_info');
      return {
        memory: pythonStats?.memory_usage || 0,
        activeTasks: pythonStats?.active_tasks || 0,
        errorRate: pythonStats?.error_rate || 0
      };
    } catch (error) {
      return {
        memory: 0,
        activeTasks: 0,
        errorRate: 0
      };
    }
  }

  private calculateAverageResponseTime(): number {
    // Use Navigation Timing API to calculate response time
    const perfEntries = performance.getEntriesByType('navigation');
    if (perfEntries.length > 0) {
      const navEntry = perfEntries[0] as PerformanceNavigationTiming;
      return navEntry.loadEventEnd - navEntry.fetchStart;
    }
    return 0;
  }

  private checkAlerts(metrics: PerformanceMetrics): void {
    const now = new Date();
    const newAlerts: PerformanceAlert[] = [];

    // CPU Alert
    if (metrics.cpu.usage > this.config.alerts.cpuThreshold) {
      newAlerts.push(this.createAlert('cpu', 'high', 
        `High CPU usage: ${metrics.cpu.usage.toFixed(1)}%`,
        metrics.cpu.usage, this.config.alerts.cpuThreshold, now
      ));
    }

    // Memory Alert
    if (metrics.memory.usage > this.config.alerts.memoryThreshold) {
      newAlerts.push(this.createAlert('memory', 'high',
        `High memory usage: ${metrics.memory.usage.toFixed(1)}%`,
        metrics.memory.usage, this.config.alerts.memoryThreshold, now
      ));
    }

    // Disk Alert
    if (metrics.disk.usage > this.config.alerts.diskThreshold) {
      newAlerts.push(this.createAlert('disk', 'high',
        `High disk usage: ${metrics.disk.usage.toFixed(1)}%`,
        metrics.disk.usage, this.config.alerts.diskThreshold, now
      ));
    }

    // Response Time Alert
    if (metrics.application.responseTime > this.config.alerts.responseTimeThreshold) {
      newAlerts.push(this.createAlert('application', 'medium',
        `Slow response time: ${metrics.application.responseTime.toFixed(0)}ms`,
        metrics.application.responseTime, this.config.alerts.responseTimeThreshold, now
      ));
    }

    // Error Rate Alert
    const errorRate = (metrics.application.errorCount / (metrics.application.uptime / 3600)) || 0;
    if (errorRate > this.config.alerts.errorRateThreshold) {
      newAlerts.push(this.createAlert('application', 'high',
        `High error rate: ${errorRate.toFixed(1)} errors/hour`,
        errorRate, this.config.alerts.errorRateThreshold, now
      ));
    }

    // Add new alerts and notify
    newAlerts.forEach(alert => {
      this.alerts.push(alert);
      this.notifyAlertCallbacks(alert);
    });

    // Auto-optimize if enabled
    if (this.config.autoOptimize && newAlerts.length > 0) {
      this.performAutoOptimization(newAlerts);
    }
  }

  private createAlert(
    type: PerformanceAlert['type'], 
    severity: PerformanceAlert['severity'],
    message: string, 
    value: number, 
    threshold: number, 
    timestamp: Date
  ): PerformanceAlert {
    return {
      id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      severity,
      message,
      value,
      threshold,
      timestamp,
      resolved: false
    };
  }

  private async performAutoOptimization(alerts: PerformanceAlert[]): Promise<void> {
    console.log('Performing auto-optimization for alerts:', alerts);
    
    for (const alert of alerts) {
      try {
        switch (alert.type) {
          case 'memory':
            await this.optimizeMemory();
            break;
          case 'cpu':
            await this.optimizeCPU();
            break;
          case 'disk':
            await this.optimizeDisk();
            break;
        }
      } catch (error) {
        console.error(`Failed to auto-optimize ${alert.type}:`, error);
      }
    }
  }

  private async optimizeMemory(): Promise<void> {
    try {
      // Clear caches
      await invoke('cleanup_cache');
      
      // Trigger garbage collection in browser
      if ('gc' in window && typeof (window as any).gc === 'function') {
        (window as any).gc();
      }
      
      console.log('Memory optimization completed');
    } catch (error) {
      console.error('Memory optimization failed:', error);
    }
  }

  private async optimizeCPU(): Promise<void> {
    try {
      // Reduce background task priority
      await invoke('optimize_system_performance');
      console.log('CPU optimization completed');
    } catch (error) {
      console.error('CPU optimization failed:', error);
    }
  }

  private async optimizeDisk(): Promise<void> {
    try {
      // Clean up old files and logs
      await invoke('cleanup_performance_data');
      console.log('Disk optimization completed');
    } catch (error) {
      console.error('Disk optimization failed:', error);
    }
  }

  private cleanupOldMetrics(): void {
    const cutoffTime = new Date(Date.now() - this.config.retentionPeriod * 60 * 60 * 1000);
    this.metricsHistory = this.metricsHistory.filter(entry => entry.timestamp > cutoffTime);
    
    // Clean up old alerts
    this.alerts = this.alerts.filter(alert => alert.timestamp > cutoffTime);
  }

  private notifyEventCallbacks(metrics: PerformanceMetrics): void {
    this.eventCallbacks.forEach(callback => {
      try {
        callback(metrics);
      } catch (error) {
        console.error('Error in performance event callback:', error);
      }
    });
  }

  private notifyAlertCallbacks(alert: PerformanceAlert): void {
    this.alertCallbacks.forEach(callback => {
      try {
        callback(alert);
      } catch (error) {
        console.error('Error in alert callback:', error);
      }
    });
  }

  // Public API methods
  public getCurrentMetrics(): PerformanceMetrics | null {
    return this.metrics;
  }

  public getMetricsHistory(): Array<{ timestamp: Date; metrics: PerformanceMetrics }> {
    return [...this.metricsHistory];
  }

  public getActiveAlerts(): PerformanceAlert[] {
    return this.alerts.filter(alert => !alert.resolved);
  }

  public getAllAlerts(): PerformanceAlert[] {
    return [...this.alerts];
  }

  public resolveAlert(alertId: string): void {
    const alert = this.alerts.find(a => a.id === alertId);
    if (alert) {
      alert.resolved = true;
    }
  }

  public getConfig(): PerformanceConfig {
    return { ...this.config };
  }

  public async updateConfig(newConfig: Partial<PerformanceConfig>): Promise<void> {
    this.config = { ...this.config, ...newConfig };
    await this.saveConfig();

    // Restart monitoring with new config
    if ('monitoringEnabled' in newConfig || 'collectInterval' in newConfig) {
      this.stopMonitoring();
      if (this.config.monitoringEnabled) {
        await this.startMonitoring();
      }
    }
  }

  public addEventListener(callback: PerformanceEventCallback): () => void {
    this.eventCallbacks.push(callback);
    return () => {
      const index = this.eventCallbacks.indexOf(callback);
      if (index > -1) {
        this.eventCallbacks.splice(index, 1);
      }
    };
  }

  public addAlertListener(callback: AlertCallback): () => void {
    this.alertCallbacks.push(callback);
    return () => {
      const index = this.alertCallbacks.indexOf(callback);
      if (index > -1) {
        this.alertCallbacks.splice(index, 1);
      }
    };
  }

  public async getRecommendations(): Promise<PerformanceRecommendation[]> {
    const recommendations: PerformanceRecommendation[] = [];
    
    if (!this.metrics) return recommendations;

    // Memory recommendations
    if (this.metrics.memory.usage > 70) {
      recommendations.push({
        id: 'mem_cleanup',
        category: 'memory',
        title: 'Clear Application Cache',
        description: 'High memory usage detected. Clearing cache can free up memory.',
        impact: 'medium',
        action: 'Clear cache and temporary files',
        automated: true
      });
    }

    // CPU recommendations
    if (this.metrics.cpu.usage > 60) {
      recommendations.push({
        id: 'cpu_optimize',
        category: 'cpu',
        title: 'Reduce Background Tasks',
        description: 'High CPU usage detected. Consider reducing background processing.',
        impact: 'high',
        action: 'Pause non-essential background tasks',
        automated: false
      });
    }

    // Application recommendations
    if (this.metrics.application.responseTime > 3000) {
      recommendations.push({
        id: 'app_optimize',
        category: 'application',
        title: 'Optimize Application Performance',
        description: 'Slow response times detected. Consider optimizing queries and processing.',
        impact: 'high',
        action: 'Review and optimize slow operations',
        automated: false
      });
    }

    return recommendations;
  }

  public destroy(): void {
    this.stopMonitoring();
    this.eventCallbacks = [];
    this.alertCallbacks = [];
    this.alerts = [];
    this.metricsHistory = [];
  }
}

// Global performance monitor instance
export const performanceMonitor = new RealTimePerformanceMonitor();

// Convenience functions
export const startPerformanceMonitoring = () => performanceMonitor.startMonitoring();
export const stopPerformanceMonitoring = () => performanceMonitor.stopMonitoring();
export const getCurrentMetrics = () => performanceMonitor.getCurrentMetrics();
export const getPerformanceHistory = () => performanceMonitor.getMetricsHistory();
export const getActiveAlerts = () => performanceMonitor.getActiveAlerts();
export const addPerformanceListener = (callback: PerformanceEventCallback) => 
  performanceMonitor.addEventListener(callback);
export const addAlertListener = (callback: AlertCallback) => 
  performanceMonitor.addAlertListener(callback);
export const getPerformanceRecommendations = () => performanceMonitor.getRecommendations();
export const updatePerformanceConfig = (config: Partial<PerformanceConfig>) => 
  performanceMonitor.updateConfig(config);

// Initialize on module load
if (typeof window !== 'undefined') {
  performanceMonitor.initialize();
}
