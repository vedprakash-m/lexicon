import React, { useState, useEffect } from 'react';
import {
  Activity,
  Cpu,
  HardDrive,
  Memory,
  Network,
  AlertTriangle,
  TrendingUp,
  Settings,
  Zap,
  RefreshCw,
  CheckCircle,
  XCircle,
  Play,
  Pause
} from 'lucide-react';
import {
  performanceMonitor,
  PerformanceMetrics,
  PerformanceAlert,
  PerformanceConfig,
  PerformanceRecommendation,
  addPerformanceListener,
  addAlertListener,
  getPerformanceRecommendations,
  updatePerformanceConfig,
  startPerformanceMonitoring,
  stopPerformanceMonitoring
} from '../lib/performanceMonitor';

interface RealTimePerformanceDashboardProps {
  className?: string;
}

export default function RealTimePerformanceDashboard({ className = '' }: RealTimePerformanceDashboardProps) {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [alerts, setAlerts] = useState<PerformanceAlert[]>([]);
  const [config, setConfig] = useState<PerformanceConfig | null>(null);
  const [recommendations, setRecommendations] = useState<PerformanceRecommendation[]>([]);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [timeRange, setTimeRange] = useState('1h');

  useEffect(() => {
    initializeDashboard();

    // Set up event listeners
    const unsubscribeMetrics = addPerformanceListener((newMetrics) => {
      setMetrics(newMetrics);
      updateRecommendations();
    });

    const unsubscribeAlerts = addAlertListener((alert) => {
      setAlerts(prev => [alert, ...prev].slice(0, 10)); // Keep last 10 alerts
    });

    return () => {
      unsubscribeMetrics();
      unsubscribeAlerts();
    };
  }, []);

  const initializeDashboard = async () => {
    try {
      const currentConfig = performanceMonitor.getConfig();
      const currentMetrics = performanceMonitor.getCurrentMetrics();
      const activeAlerts = performanceMonitor.getActiveAlerts();
      
      setConfig(currentConfig);
      setMetrics(currentMetrics);
      setAlerts(activeAlerts);
      setIsMonitoring(currentConfig.monitoringEnabled);
      
      await updateRecommendations();
    } catch (error) {
      console.error('Failed to initialize performance dashboard:', error);
    }
  };

  const updateRecommendations = async () => {
    try {
      const recs = await getPerformanceRecommendations();
      setRecommendations(recs);
    } catch (error) {
      console.error('Failed to get recommendations:', error);
    }
  };

  const handleToggleMonitoring = async () => {
    try {
      if (isMonitoring) {
        stopPerformanceMonitoring();
        setIsMonitoring(false);
      } else {
        await startPerformanceMonitoring();
        setIsMonitoring(true);
      }
    } catch (error) {
      console.error('Failed to toggle monitoring:', error);
    }
  };

  const handleConfigChange = async (newConfig: Partial<PerformanceConfig>) => {
    if (config) {
      const updatedConfig = { ...config, ...newConfig };
      await updatePerformanceConfig(newConfig);
      setConfig(updatedConfig);
    }
  };

  const resolveAlert = (alertId: string) => {
    performanceMonitor.resolveAlert(alertId);
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId ? { ...alert, resolved: true } : alert
    ));
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatUptime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const getUsageColor = (usage: number, threshold: number = 80): string => {
    if (usage >= threshold) return 'text-red-600';
    if (usage >= threshold * 0.7) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getUsageBarColor = (usage: number, threshold: number = 80): string => {
    if (usage >= threshold) return 'bg-red-500';
    if (usage >= threshold * 0.7) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-blue-600 bg-blue-50 border-blue-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  if (!metrics && isMonitoring) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">Loading performance metrics...</span>
      </div>
    );
  }

  return (
    <div className={`space-y-6 p-6 bg-white rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Activity className="w-6 h-6 text-blue-500" />
          <h2 className="text-xl font-semibold text-gray-900">Real-time Performance</h2>
          {isMonitoring && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              <div className="w-2 h-2 bg-green-400 rounded-full mr-1 animate-pulse"></div>
              Monitoring
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleToggleMonitoring}
            className={`inline-flex items-center px-3 py-2 rounded-lg text-sm font-medium ${
              isMonitoring 
                ? 'bg-red-100 text-red-700 hover:bg-red-200'
                : 'bg-green-100 text-green-700 hover:bg-green-200'
            }`}
          >
            {isMonitoring ? (
              <>
                <Pause className="w-4 h-4 mr-2" />
                Stop
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Start
              </>
            )}
          </button>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Alerts */}
      {alerts.filter(alert => !alert.resolved).length > 0 && (
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2 text-red-500" />
            Active Alerts ({alerts.filter(alert => !alert.resolved).length})
          </h3>
          {alerts.filter(alert => !alert.resolved).slice(0, 3).map((alert) => (
            <div
              key={alert.id}
              className={`p-3 rounded-lg border ${getSeverityColor(alert.severity)}`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{alert.message}</p>
                  <p className="text-sm opacity-75">
                    {alert.timestamp.toLocaleTimeString()}
                  </p>
                </div>
                <button
                  onClick={() => resolveAlert(alert.id)}
                  className="p-1 hover:bg-white hover:bg-opacity-50 rounded"
                >
                  <XCircle className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* System Metrics Cards */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* CPU */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <Cpu className="w-5 h-5 text-blue-500 mr-2" />
                <span className="font-medium text-gray-900">CPU</span>
              </div>
              <span className={`text-sm font-medium ${getUsageColor(metrics.cpu.usage)}`}>
                {metrics.cpu.usage.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${getUsageBarColor(metrics.cpu.usage)}`}
                style={{ width: `${Math.min(metrics.cpu.usage, 100)}%` }}
              />
            </div>
            <p className="text-xs text-gray-600">{metrics.cpu.cores} cores</p>
          </div>

          {/* Memory */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <Memory className="w-5 h-5 text-green-500 mr-2" />
                <span className="font-medium text-gray-900">Memory</span>
              </div>
              <span className={`text-sm font-medium ${getUsageColor(metrics.memory.usage)}`}>
                {metrics.memory.usage.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${getUsageBarColor(metrics.memory.usage)}`}
                style={{ width: `${Math.min(metrics.memory.usage, 100)}%` }}
              />
            </div>
            <p className="text-xs text-gray-600">
              {formatBytes(metrics.memory.used)} / {formatBytes(metrics.memory.total)}
            </p>
          </div>

          {/* Disk */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <HardDrive className="w-5 h-5 text-purple-500 mr-2" />
                <span className="font-medium text-gray-900">Disk</span>
              </div>
              <span className={`text-sm font-medium ${getUsageColor(metrics.disk.usage, 90)}`}>
                {metrics.disk.usage.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${getUsageBarColor(metrics.disk.usage, 90)}`}
                style={{ width: `${Math.min(metrics.disk.usage, 100)}%` }}
              />
            </div>
            <p className="text-xs text-gray-600">
              {formatBytes(metrics.disk.available)} available
            </p>
          </div>

          {/* Application */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <Zap className="w-5 h-5 text-yellow-500 mr-2" />
                <span className="font-medium text-gray-900">Application</span>
              </div>
              <span className="text-sm font-medium text-gray-700">
                {metrics.application.tasksActive} active
              </span>
            </div>
            <div className="space-y-1 text-xs text-gray-600">
              <div className="flex justify-between">
                <span>Uptime:</span>
                <span>{formatUptime(metrics.application.uptime)}</span>
              </div>
              <div className="flex justify-between">
                <span>Tasks:</span>
                <span>{metrics.application.tasksCompleted} completed</span>
              </div>
              <div className="flex justify-between">
                <span>Errors:</span>
                <span className={metrics.application.errorCount > 0 ? 'text-red-600' : 'text-green-600'}>
                  {metrics.application.errorCount}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Performance Recommendations */}
      {recommendations.length > 0 && (
        <div className="border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-blue-500" />
            Performance Recommendations
          </h3>
          <div className="space-y-3">
            {recommendations.slice(0, 3).map((rec) => (
              <div key={rec.id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className={`p-1 rounded ${
                  rec.impact === 'high' ? 'bg-red-100 text-red-600' :
                  rec.impact === 'medium' ? 'bg-yellow-100 text-yellow-600' :
                  'bg-blue-100 text-blue-600'
                }`}>
                  <TrendingUp className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-gray-900">{rec.title}</h4>
                  <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
                  <div className="flex items-center justify-between mt-2">
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      rec.impact === 'high' ? 'bg-red-100 text-red-700' :
                      rec.impact === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-blue-100 text-blue-700'
                    }`}>
                      {rec.impact} impact
                    </span>
                    {rec.automated && (
                      <span className="text-xs text-green-600 flex items-center">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        Auto-fixable
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Settings Panel */}
      {showSettings && config && (
        <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
          <h3 className="font-semibold text-gray-900 mb-4">Performance Settings</h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Enable Monitoring
              </label>
              <input
                type="checkbox"
                checked={config.monitoringEnabled}
                onChange={(e) => handleConfigChange({ monitoringEnabled: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
            </div>
            
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Auto-optimize
              </label>
              <input
                type="checkbox"
                checked={config.autoOptimize}
                onChange={(e) => handleConfigChange({ autoOptimize: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Collection Interval
              </label>
              <select
                value={config.collectInterval}
                onChange={(e) => handleConfigChange({ collectInterval: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={1000}>1 second</option>
                <option value={5000}>5 seconds</option>
                <option value={10000}>10 seconds</option>
                <option value={30000}>30 seconds</option>
                <option value={60000}>1 minute</option>
              </select>
            </div>
            
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-gray-700">Alert Thresholds</h4>
              
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">CPU (%)</label>
                  <input
                    type="number"
                    value={config.alerts.cpuThreshold}
                    onChange={(e) => handleConfigChange({ 
                      alerts: { ...config.alerts, cpuThreshold: parseInt(e.target.value) }
                    })}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                    min="0" max="100"
                  />
                </div>
                
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Memory (%)</label>
                  <input
                    type="number"
                    value={config.alerts.memoryThreshold}
                    onChange={(e) => handleConfigChange({ 
                      alerts: { ...config.alerts, memoryThreshold: parseInt(e.target.value) }
                    })}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                    min="0" max="100"
                  />
                </div>
                
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Disk (%)</label>
                  <input
                    type="number"
                    value={config.alerts.diskThreshold}
                    onChange={(e) => handleConfigChange({ 
                      alerts: { ...config.alerts, diskThreshold: parseInt(e.target.value) }
                    })}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                    min="0" max="100"
                  />
                </div>
                
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Response (ms)</label>
                  <input
                    type="number"
                    value={config.alerts.responseTimeThreshold}
                    onChange={(e) => handleConfigChange({ 
                      alerts: { ...config.alerts, responseTimeThreshold: parseInt(e.target.value) }
                    })}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                    min="0"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* No Monitoring State */}
      {!isMonitoring && (
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto bg-blue-100 rounded-full flex items-center justify-center">
            <Activity className="w-8 h-8 text-blue-500" />
          </div>
          <h3 className="mt-4 text-lg font-medium text-gray-900">Performance Monitoring Disabled</h3>
          <p className="mt-2 text-gray-500 mb-4">
            Enable monitoring to track real-time performance metrics and receive alerts.
          </p>
          <button
            onClick={handleToggleMonitoring}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Play className="w-4 h-4 mr-2" />
            Start Monitoring
          </button>
        </div>
      )}
    </div>
  );
}
