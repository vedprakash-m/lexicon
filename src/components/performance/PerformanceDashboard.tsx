import React, { useState, useEffect } from 'react';
import { Activity, Cpu, HardDrive, Zap, AlertTriangle, CheckCircle, TrendingUp, TrendingDown } from 'lucide-react';
import { PerformanceMonitor } from '../../utils/PerformanceMonitor';

interface PerformanceDashboardProps {
  className?: string;
}

export const PerformanceDashboard: React.FC<PerformanceDashboardProps> = ({ className = '' }) => {
  const [performanceData, setPerformanceData] = useState<any>(null);
  const [isMonitoring, setIsMonitoring] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);

  useEffect(() => {
    const monitor = PerformanceMonitor.getInstance();
    
    const updateData = () => {
      const data = monitor.exportData();
      setPerformanceData(data);
    };

    // Initial load
    updateData();

    // Set up interval
    const interval = setInterval(updateData, refreshInterval);

    return () => {
      clearInterval(interval);
    };
  }, [refreshInterval]);

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatTime = (ms: number): string => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getStatusColor = (value: number, thresholds: { good: number; warning: number }): string => {
    if (value <= thresholds.good) return 'text-green-600 bg-green-100';
    if (value <= thresholds.warning) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getStatusIcon = (value: number, thresholds: { good: number; warning: number }) => {
    if (value <= thresholds.good) return <CheckCircle className="w-4 h-4 text-green-600" />;
    if (value <= thresholds.warning) return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
    return <AlertTriangle className="w-4 h-4 text-red-600" />;
  };

  if (!performanceData) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  const { summary, thresholds, recommendations } = performanceData;

  return (
    <div className={`bg-white rounded-lg shadow ${className}`}>
      {/* Header */}
      <div className="border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Activity className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">Performance Dashboard</h2>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Refresh:</span>
              <select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value={1000}>1s</option>
                <option value={5000}>5s</option>
                <option value={10000}>10s</option>
                <option value={30000}>30s</option>
              </select>
            </div>
            
            <button
              onClick={() => setIsMonitoring(!isMonitoring)}
              className={`px-3 py-1 rounded text-sm font-medium ${
                isMonitoring
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              {isMonitoring ? 'Monitoring' : 'Paused'}
            </button>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Overall Status */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Overall Status</p>
                <p className={`text-lg font-semibold ${thresholds.passed ? 'text-green-600' : 'text-red-600'}`}>
                  {thresholds.passed ? 'Good' : 'Issues'}
                </p>
              </div>
              {thresholds.passed ? (
                <CheckCircle className="w-8 h-8 text-green-600" />
              ) : (
                <AlertTriangle className="w-8 h-8 text-red-600" />
              )}
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Memory Usage</p>
                <p className="text-lg font-semibold text-gray-900">
                  {formatBytes(summary.memoryUsage.current)}
                </p>
              </div>
              <HardDrive className="w-8 h-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Page Load</p>
                <p className="text-lg font-semibold text-gray-900">
                  {formatTime(summary.bundleMetrics.totalLoadTime)}
                </p>
              </div>
              <Zap className="w-8 h-8 text-yellow-600" />
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Components</p>
                <p className="text-lg font-semibold text-gray-900">
                  {summary.renderPerformance.slowestComponents.length}
                </p>
              </div>
              <Cpu className="w-8 h-8 text-purple-600" />
            </div>
          </div>
        </div>

        {/* Web Vitals */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Web Vitals</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {[
              { 
                name: 'FCP', 
                label: 'First Contentful Paint',
                value: summary.webVitals.fcp,
                thresholds: { good: 1800, warning: 3000 },
                unit: 'ms'
              },
              { 
                name: 'LCP', 
                label: 'Largest Contentful Paint',
                value: summary.webVitals.lcp,
                thresholds: { good: 2500, warning: 4000 },
                unit: 'ms'
              },
              { 
                name: 'FID', 
                label: 'First Input Delay',
                value: summary.webVitals.fid,
                thresholds: { good: 100, warning: 300 },
                unit: 'ms'
              },
              { 
                name: 'CLS', 
                label: 'Cumulative Layout Shift',
                value: summary.webVitals.cls,
                thresholds: { good: 0.1, warning: 0.25 },
                unit: ''
              },
              { 
                name: 'TTFB', 
                label: 'Time to First Byte',
                value: summary.webVitals.ttfb,
                thresholds: { good: 800, warning: 1800 },
                unit: 'ms'
              },
            ].map((vital) => (
              <div key={vital.name} className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-600">{vital.name}</span>
                  {vital.value !== null && getStatusIcon(vital.value, vital.thresholds)}
                </div>
                <div className="mb-1">
                  <span className="text-lg font-semibold text-gray-900">
                    {vital.value !== null ? `${vital.value.toFixed(vital.unit === 'ms' ? 0 : 3)}${vital.unit}` : 'N/A'}
                  </span>
                </div>
                <p className="text-xs text-gray-500">{vital.label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Memory Usage Chart */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Memory Usage</h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center">
                <p className="text-sm text-gray-600">Current</p>
                <p className="text-lg font-semibold text-gray-900">
                  {formatBytes(summary.memoryUsage.current)}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600">Average</p>
                <p className="text-lg font-semibold text-gray-900">
                  {formatBytes(summary.memoryUsage.average)}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600">Peak</p>
                <p className="text-lg font-semibold text-gray-900">
                  {formatBytes(summary.memoryUsage.peak)}
                </p>
              </div>
            </div>
            
            {/* Memory usage bar */}
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                style={{
                  width: `${Math.min((summary.memoryUsage.current / (500 * 1024 * 1024)) * 100, 100)}%`
                }}
              />
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0 MB</span>
              <span>500 MB (Target)</span>
            </div>
          </div>
        </div>

        {/* Component Performance */}
        {summary.renderPerformance.slowestComponents.length > 0 && (
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Slowest Components</h3>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="space-y-3">
                {summary.renderPerformance.slowestComponents.slice(0, 5).map((component, index) => (
                  <div key={component.name} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className="text-sm font-medium text-gray-900">
                        {component.name}
                      </span>
                      {component.averageTime > 16 && (
                        <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                          Slow
                        </span>
                      )}
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">
                        {formatTime(component.averageTime)} avg
                      </div>
                      <div className="text-xs text-gray-500">
                        {formatTime(component.maxTime)} max
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Issues and Warnings */}
        {(thresholds.issues.length > 0 || thresholds.warnings.length > 0) && (
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Issues & Warnings</h3>
            <div className="space-y-3">
              {thresholds.issues.map((issue, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-red-50 rounded-lg">
                  <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-red-800">Issue</p>
                    <p className="text-sm text-red-700">{issue}</p>
                  </div>
                </div>
              ))}
              
              {thresholds.warnings.map((warning, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
                  <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-yellow-800">Warning</p>
                    <p className="text-sm text-yellow-700">{warning}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Optimization Recommendations</h3>
            <div className="bg-blue-50 rounded-lg p-4">
              <ul className="space-y-2">
                {recommendations.map((recommendation, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <TrendingUp className="w-4 h-4 text-blue-600 mt-0.5" />
                    <span className="text-sm text-blue-800">{recommendation}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-between items-center pt-4 border-t border-gray-200">
          <div className="text-sm text-gray-500">
            Last updated: {new Date(performanceData.timestamp).toLocaleTimeString()}
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={() => {
                const monitor = PerformanceMonitor.getInstance();
                monitor.clearMetrics();
                setPerformanceData(monitor.exportData());
              }}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Clear Metrics
            </button>
            
            <button
              onClick={() => {
                const dataStr = JSON.stringify(performanceData, null, 2);
                const dataBlob = new Blob([dataStr], { type: 'application/json' });
                const url = URL.createObjectURL(dataBlob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `performance-report-${new Date().toISOString().split('T')[0]}.json`;
                link.click();
                URL.revokeObjectURL(url);
              }}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              Export Report
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};