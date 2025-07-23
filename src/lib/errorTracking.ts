/**
 * Production Error Tracking and Monitoring System
 * Provides comprehensive error logging, user feedback, and diagnostic information
 */

import React from 'react';

export interface ErrorContext {
  userId?: string;
  sessionId: string;
  userAgent: string;
  timestamp: string;
  url: string;
  component?: string;
  action?: string;
  metadata?: Record<string, any>;
}

export interface ErrorReport {
  id: string;
  level: 'error' | 'warning' | 'info';
  message: string;
  stack?: string;
  context: ErrorContext;
  fingerprint: string;
  tags: string[];
}

export interface ErrorMetrics {
  errorCount: number;
  errorRate: number;
  topErrors: Array<{ message: string; count: number; lastSeen: string }>;
  affectedUsers: number;
  timeRange: string;
}

class ProductionErrorTracker {
  private sessionId: string;
  private errorQueue: ErrorReport[] = [];
  private isOnline: boolean = navigator.onLine;
  private maxQueueSize: number = 100;
  private flushInterval: number = 30000; // 30 seconds
  private userId?: string;

  constructor() {
    this.sessionId = this.generateSessionId();
    this.setupEventListeners();
    this.startPeriodicFlush();
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private setupEventListeners(): void {
    // Global error handler
    window.addEventListener('error', (event) => {
      this.captureError(event.error || new Error(event.message), {
        component: 'window',
        action: 'javascript_error',
        metadata: {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno
        }
      });
    });

    // Unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.captureError(new Error(`Unhandled Promise Rejection: ${event.reason}`), {
        component: 'promise',
        action: 'unhandled_rejection',
        metadata: { reason: event.reason }
      });
    });

    // Network status changes
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.flushErrors();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
    });

    // Page visibility changes (for cleanup)
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        this.flushErrors();
      }
    });
  }

  private startPeriodicFlush(): void {
    setInterval(() => {
      this.flushErrors();
    }, this.flushInterval);
  }

  public setUserId(userId: string): void {
    this.userId = userId;
  }

  public captureError(
    error: Error | string,
    additionalContext: Partial<ErrorContext> = {},
    level: ErrorReport['level'] = 'error'
  ): string {
    const errorMessage = typeof error === 'string' ? error : error.message;
    const stack = typeof error === 'object' && error.stack ? error.stack : undefined;

    const context: ErrorContext = {
      userId: this.userId,
      sessionId: this.sessionId,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      ...additionalContext
    };

    const fingerprint = this.generateFingerprint(errorMessage, stack, context.component);
    const errorId = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const errorReport: ErrorReport = {
      id: errorId,
      level,
      message: errorMessage,
      stack,
      context,
      fingerprint,
      tags: this.generateTags(context)
    };

    this.errorQueue.push(errorReport);

    // Trim queue if it gets too large
    if (this.errorQueue.length > this.maxQueueSize) {
      this.errorQueue = this.errorQueue.slice(-this.maxQueueSize);
    }

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('[ErrorTracker]', errorReport);
    }

    // Immediate flush for critical errors
    if (level === 'error') {
      this.flushErrors();
    }

    return errorId;
  }

  private generateFingerprint(message: string, stack?: string, component?: string): string {
    const content = [message, component, stack?.split('\n')[0]].filter(Boolean).join('|');
    return this.simpleHash(content);
  }

  private simpleHash(str: string): string {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(36);
  }

  private generateTags(context: ErrorContext): string[] {
    const tags: string[] = [];
    
    if (context.component) tags.push(`component:${context.component}`);
    if (context.action) tags.push(`action:${context.action}`);
    if (context.userId) tags.push(`user:${context.userId}`);
    
    // Browser tags
    tags.push(`browser:${this.getBrowserName()}`);
    tags.push(`platform:${navigator.platform}`);
    
    // Environment tags
    tags.push(`env:${process.env.NODE_ENV || 'production'}`);
    tags.push(`online:${this.isOnline}`);

    return tags;
  }

  private getBrowserName(): string {
    const userAgent = navigator.userAgent.toLowerCase();
    if (userAgent.includes('chrome')) return 'chrome';
    if (userAgent.includes('firefox')) return 'firefox';
    if (userAgent.includes('safari')) return 'safari';
    if (userAgent.includes('edge')) return 'edge';
    return 'unknown';
  }

  private async flushErrors(): Promise<void> {
    if (this.errorQueue.length === 0 || !this.isOnline) {
      return;
    }

    const errorsToFlush = [...this.errorQueue];
    this.errorQueue = [];

    try {
      // Try to send to external service first (Sentry, LogRocket, etc.)
      await this.sendToExternalService(errorsToFlush);
    } catch (externalError) {
      // Fallback to local storage
      this.saveToLocalStorage(errorsToFlush);
      
      // Re-queue errors for retry
      this.errorQueue.unshift(...errorsToFlush);
      
      console.warn('[ErrorTracker] Failed to send errors to external service, saved locally:', externalError);
    }
  }

  private async sendToExternalService(errors: ErrorReport[]): Promise<void> {
    // In a real implementation, this would send to Sentry, LogRocket, or custom endpoint
    // For now, we'll simulate with local logging
    
    try {
      // Simulate API call
      const response = await fetch('/api/errors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ errors })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (networkError) {
      // If the API doesn't exist, save to Tauri backend
      await this.sendToTauriBackend(errors);
    }
  }

  private async sendToTauriBackend(errors: ErrorReport[]): Promise<void> {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      await invoke('log_errors', { errors });
    } catch (tauriError) {
      // If Tauri isn't available, throw to trigger local storage fallback
      throw new Error(`Tauri backend not available: ${tauriError}`);
    }
  }

  private saveToLocalStorage(errors: ErrorReport[]): void {
    try {
      const existingErrors = this.getLocalStorageErrors();
      const allErrors = [...existingErrors, ...errors];
      
      // Keep only the last 1000 errors to prevent storage bloat
      const trimmedErrors = allErrors.slice(-1000);
      
      localStorage.setItem('lexicon_error_log', JSON.stringify(trimmedErrors));
    } catch (storageError) {
      console.error('[ErrorTracker] Failed to save errors to localStorage:', storageError);
    }
  }

  private getLocalStorageErrors(): ErrorReport[] {
    try {
      const stored = localStorage.getItem('lexicon_error_log');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  }

  public async getErrorMetrics(timeRange: string = '24h'): Promise<ErrorMetrics> {
    const allErrors = [
      ...this.errorQueue,
      ...this.getLocalStorageErrors()
    ];

    const cutoffTime = this.getTimeRangeCutoff(timeRange);
    const recentErrors = allErrors.filter(error => 
      new Date(error.context.timestamp) > cutoffTime
    );

    const errorCounts = new Map<string, number>();
    const lastSeen = new Map<string, string>();
    const affectedUsers = new Set<string>();

    recentErrors.forEach(error => {
      const key = error.fingerprint;
      errorCounts.set(key, (errorCounts.get(key) || 0) + 1);
      lastSeen.set(key, error.context.timestamp);
      
      if (error.context.userId) {
        affectedUsers.add(error.context.userId);
      }
    });

    const topErrors = Array.from(errorCounts.entries())
      .map(([fingerprint, count]) => {
        const error = recentErrors.find(e => e.fingerprint === fingerprint);
        return {
          message: error?.message || 'Unknown error',
          count,
          lastSeen: lastSeen.get(fingerprint) || new Date().toISOString()
        };
      })
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    return {
      errorCount: recentErrors.length,
      errorRate: this.calculateErrorRate(recentErrors, timeRange),
      topErrors,
      affectedUsers: affectedUsers.size,
      timeRange
    };
  }

  private getTimeRangeCutoff(timeRange: string): Date {
    const now = new Date();
    const hours = timeRange.includes('h') ? parseInt(timeRange) : 
                  timeRange.includes('d') ? parseInt(timeRange) * 24 : 24;
    
    return new Date(now.getTime() - hours * 60 * 60 * 1000);
  }

  private calculateErrorRate(errors: ErrorReport[], timeRange: string): number {
    if (errors.length === 0) return 0;
    
    const hours = timeRange.includes('h') ? parseInt(timeRange) : 
                  timeRange.includes('d') ? parseInt(timeRange) * 24 : 24;
    
    return errors.length / hours; // Errors per hour
  }

  public clearErrorLog(): void {
    this.errorQueue = [];
    localStorage.removeItem('lexicon_error_log');
  }

  public exportErrorLog(): string {
    const allErrors = [
      ...this.errorQueue,
      ...this.getLocalStorageErrors()
    ];
    
    return JSON.stringify(allErrors, null, 2);
  }
}

// Global error tracker instance
export const errorTracker = new ProductionErrorTracker();

// React Error Boundary HOC
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  fallbackComponent?: React.ComponentType<{ error: Error; resetError: () => void }>
) {
  return class ErrorBoundaryWrapper extends React.Component<
    P,
    { hasError: boolean; error?: Error }
  > {
    constructor(props: P) {
      super(props);
      this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error) {
      return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
      errorTracker.captureError(error, {
        component: Component.name,
        action: 'react_error_boundary',
        metadata: {
          componentStack: errorInfo.componentStack,
          errorBoundary: true
        }
      });
    }

    resetError = () => {
      this.setState({ hasError: false, error: undefined });
    };

    render() {
      if (this.state.hasError) {
        if (fallbackComponent) {
          const FallbackComponent = fallbackComponent;
          return React.createElement(FallbackComponent, {
            error: this.state.error!,
            resetError: this.resetError
          });
        }
        
        return React.createElement('div', {
          className: "error-boundary p-4 bg-red-50 border border-red-200 rounded-lg"
        }, [
          React.createElement('h2', {
            key: 'title',
            className: "text-lg font-semibold text-red-800 mb-2"
          }, "Something went wrong"),
          React.createElement('p', {
            key: 'message',
            className: "text-red-600 mb-4"
          }, "An error occurred in this component. The error has been logged."),
          React.createElement('button', {
            key: 'button',
            onClick: this.resetError,
            className: "px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          }, "Try Again")
        ]);
      }

      return React.createElement(Component, this.props);
    }
  };
}

// Utility functions for manual error reporting
export const captureException = (error: Error | string, context?: Partial<ErrorContext>) => {
  return errorTracker.captureError(error, context, 'error');
};

export const captureMessage = (message: string, level: ErrorReport['level'] = 'info', context?: Partial<ErrorContext>) => {
  return errorTracker.captureError(message, context, level);
};

export const setUser = (userId: string) => {
  errorTracker.setUserId(userId);
};

export const getErrorMetrics = (timeRange?: string) => {
  return errorTracker.getErrorMetrics(timeRange);
};

export const clearErrors = () => {
  errorTracker.clearErrorLog();
};

export const exportErrors = () => {
  return errorTracker.exportErrorLog();
};
