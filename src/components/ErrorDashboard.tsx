import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { 
  AlertTriangle, 
  TrendingUp, 
  Users, 
  Clock, 
  Download, 
  Trash2, 
  RefreshCw,
  BarChart3,
  AlertCircle,
  Info,
  XCircle
} from 'lucide-react';
import { errorTracker, ErrorMetrics } from '../lib/errorTracking';

interface ErrorDashboardProps {
  className?: string;
}

interface ErrorReport {
  id: string;
  level: 'error' | 'warning' | 'info';
  message: string;
  stack?: string;
  context: {
    userId?: string;
    sessionId: string;
    timestamp: string;
    component?: string;
    action?: string;
  };
  fingerprint: string;
  tags: string[];
}

export default function ErrorDashboard({ className = '' }: ErrorDashboardProps) {
  const [metrics, setMetrics] = useState<ErrorMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('24h');
  const [recentErrors, setRecentErrors] = useState<ErrorReport[]>([]);
  const [selectedError, setSelectedError] = useState<ErrorReport | null>(null);

  useEffect(() => {
    loadErrorMetrics();
    loadRecentErrors();
  }, [timeRange]);

  const loadErrorMetrics = async () => {
    try {
      setLoading(true);
      const errorMetrics = await errorTracker.getErrorMetrics(timeRange);
      setMetrics(errorMetrics);

      // Also try to get metrics from backend
      try {
        const backendMetrics = await invoke<ErrorMetrics>('get_error_metrics', { 
          timeRange 
        });
        // Combine frontend and backend metrics
        if (backendMetrics && errorMetrics) {
          setMetrics({
            ...errorMetrics,
            errorCount: errorMetrics.errorCount + backendMetrics.errorCount,
            affectedUsers: Math.max(errorMetrics.affectedUsers, backendMetrics.affectedUsers),
            errorRate: (errorMetrics.errorRate + backendMetrics.errorRate) / 2
          });
        }
      } catch (backendError) {
        console.warn('Backend error metrics not available:', backendError);
      }
    } catch (error) {
      console.error('Failed to load error metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRecentErrors = async () => {
    try {
      // Get recent errors from localStorage
      const storedErrors = localStorage.getItem('lexicon_error_log');
      if (storedErrors) {
        const errors = JSON.parse(storedErrors);
        const cutoffTime = getTimeRangeCutoff(timeRange);
        const filteredErrors = errors.filter((error: ErrorReport) => 
          new Date(error.context.timestamp) > cutoffTime
        );
        setRecentErrors(filteredErrors.slice(-50)); // Last 50 errors
      }
    } catch (error) {
      console.error('Failed to load recent errors:', error);
    }
  };

  const getTimeRangeCutoff = (range: string): Date => {
    const now = new Date();
    const hours = range.includes('h') ? parseInt(range) : 
                  range.includes('d') ? parseInt(range) * 24 : 24;
    return new Date(now.getTime() - hours * 60 * 60 * 1000);
  };

  const clearErrors = async () => {
    try {
      await errorTracker.clearErrorLog();
      await invoke('clear_error_log');
      setMetrics(null);
      setRecentErrors([]);
      setSelectedError(null);
      await loadErrorMetrics();
    } catch (error) {
      console.error('Failed to clear errors:', error);
    }
  };

  const exportErrors = async () => {
    try {
      const errorData = errorTracker.exportErrorLog();
      const blob = new Blob([errorData], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `lexicon_errors_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export errors:', error);
    }
  };

  const getErrorIcon = (level: string) => {
    switch (level) {
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'info':
        return <Info className="w-4 h-4 text-blue-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const truncateMessage = (message: string, maxLength: number = 100) => {
    return message.length > maxLength ? message.substring(0, maxLength) + '...' : message;
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">Loading error metrics...</span>
      </div>
    );
  }

  return (
    <div className={`space-y-6 p-6 bg-white rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="w-6 h-6 text-red-500" />
          <h2 className="text-xl font-semibold text-gray-900">Error Dashboard</h2>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          <button
            onClick={loadErrorMetrics}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Metrics Cards */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <AlertCircle className="w-8 h-8 text-red-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-red-800">Total Errors</p>
                <p className="text-2xl font-bold text-red-900">{metrics.errorCount}</p>
              </div>
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center">
              <TrendingUp className="w-8 h-8 text-yellow-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-yellow-800">Error Rate</p>
                <p className="text-2xl font-bold text-yellow-900">
                  {metrics.errorRate.toFixed(1)}/hr
                </p>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center">
              <Users className="w-8 h-8 text-blue-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-blue-800">Affected Users</p>
                <p className="text-2xl font-bold text-blue-900">{metrics.affectedUsers}</p>
              </div>
            </div>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center">
              <Clock className="w-8 h-8 text-green-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-green-800">Time Range</p>
                <p className="text-2xl font-bold text-green-900">{metrics.timeRange}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top Errors */}
      {metrics && metrics.topErrors.length > 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" />
            Top Errors
          </h3>
          <div className="space-y-2">
            {metrics.topErrors.map((error, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-white rounded-lg shadow-sm"
              >
                <div className="flex-1">
                  <p className="font-medium text-gray-900">
                    {truncateMessage(error.message, 80)}
                  </p>
                  <p className="text-sm text-gray-500">
                    Last seen: {formatTimestamp(error.lastSeen)}
                  </p>
                </div>
                <div className="ml-4 text-right">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                    {error.count} times
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Errors List */}
      {recentErrors.length > 0 && (
        <div className="border border-gray-200 rounded-lg">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Recent Errors</h3>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {recentErrors.slice().reverse().map((error) => (
              <div
                key={error.id}
                className={`p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer ${
                  selectedError?.id === error.id ? 'bg-blue-50 border-blue-200' : ''
                }`}
                onClick={() => setSelectedError(selectedError?.id === error.id ? null : error)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    {getErrorIcon(error.level)}
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900">
                        {truncateMessage(error.message)}
                      </p>
                      <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
                        <span>{formatTimestamp(error.context.timestamp)}</span>
                        {error.context.component && (
                          <span>Component: {error.context.component}</span>
                        )}
                        {error.context.action && (
                          <span>Action: {error.context.action}</span>
                        )}
                      </div>
                      {error.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {error.tags.slice(0, 3).map((tag, index) => (
                            <span
                              key={index}
                              className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                            >
                              {tag}
                            </span>
                          ))}
                          {error.tags.length > 3 && (
                            <span className="text-xs text-gray-500">+{error.tags.length - 3} more</span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Error Details (Expanded) */}
                {selectedError?.id === error.id && (
                  <div className="mt-4 p-4 bg-gray-100 rounded-lg">
                    <h4 className="font-medium text-gray-900 mb-2">Error Details</h4>
                    <div className="space-y-2 text-sm">
                      <div>
                        <span className="font-medium">Message:</span> {error.message}
                      </div>
                      <div>
                        <span className="font-medium">Session ID:</span> {error.context.sessionId}
                      </div>
                      {error.context.userId && (
                        <div>
                          <span className="font-medium">User ID:</span> {error.context.userId}
                        </div>
                      )}
                      <div>
                        <span className="font-medium">Fingerprint:</span> {error.fingerprint}
                      </div>
                      {error.stack && (
                        <div>
                          <span className="font-medium">Stack Trace:</span>
                          <pre className="mt-1 p-2 bg-gray-50 rounded text-xs overflow-x-auto">
                            {error.stack}
                          </pre>
                        </div>
                      )}
                      <div>
                        <span className="font-medium">Tags:</span> {error.tags.join(', ')}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <div className="text-sm text-gray-500">
          Showing {recentErrors.length} recent errors
        </div>
        <div className="flex space-x-2">
          <button
            onClick={exportErrors}
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <Download className="w-4 h-4 mr-2" />
            Export
          </button>
          <button
            onClick={clearErrors}
            className="inline-flex items-center px-3 py-2 border border-red-300 rounded-lg text-sm font-medium text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Clear All
          </button>
        </div>
      </div>

      {/* No Errors State */}
      {!loading && (!metrics || metrics.errorCount === 0) && (
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto bg-green-100 rounded-full flex items-center justify-center">
            <TrendingUp className="w-8 h-8 text-green-500" />
          </div>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No errors found</h3>
          <p className="mt-2 text-gray-500">
            Great! No errors have been recorded in the selected time range.
          </p>
        </div>
      )}
    </div>
  );
}
