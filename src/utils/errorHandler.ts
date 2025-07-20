import { useErrorHandling } from '@/store/hooks';

export interface ErrorContext {
  component?: string;
  operation?: string;
  details?: Record<string, any>;
}

export interface LogLevel {
  INFO: 'info';
  WARN: 'warn'; 
  ERROR: 'error';
  DEBUG: 'debug';
}

export const LOG_LEVELS: LogLevel = {
  INFO: 'info',
  WARN: 'warn',
  ERROR: 'error',
  DEBUG: 'debug'
};

/**
 * Standardized error logging and handling utility
 */
export class ErrorHandler {
  private static isDevelopment = process.env.NODE_ENV === 'development';

  /**
   * Log an error with context and optionally display to user
   */
  static logError(
    error: Error | string,
    context: ErrorContext = {},
    showToUser = false
  ): void {
    const errorMessage = typeof error === 'string' ? error : error.message;
    const errorStack = typeof error === 'string' ? undefined : error.stack;
    
    const logContext = {
      timestamp: new Date().toISOString(),
      level: LOG_LEVELS.ERROR,
      message: errorMessage,
      stack: errorStack,
      context,
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    // Always log to console in structured format
    if (this.isDevelopment) {
      console.group(`🚨 Error: ${context.component || 'Unknown'}`);
      console.error('Message:', errorMessage);
      if (context.operation) console.info('Operation:', context.operation);
      if (context.details) console.info('Details:', context.details);
      if (errorStack) console.error('Stack:', errorStack);
      console.groupEnd();
    } else {
      console.error('Application Error:', logContext);
    }

    // Send to error tracking service in production
    if (!this.isDevelopment) {
      this.sendToErrorTracking(logContext);
    }

    // Show to user if requested
    if (showToUser) {
      this.showUserError(errorMessage, context);
    }
  }

  /**
   * Log a warning with context
   */
  static logWarning(
    message: string,
    context: ErrorContext = {}
  ): void {
    const logContext = {
      timestamp: new Date().toISOString(),
      level: LOG_LEVELS.WARN,
      message,
      context
    };

    if (this.isDevelopment) {
      console.group(`⚠️ Warning: ${context.component || 'Unknown'}`);
      console.warn('Message:', message);
      if (context.operation) console.info('Operation:', context.operation);
      if (context.details) console.info('Details:', context.details);
      console.groupEnd();
    } else {
      console.warn('Application Warning:', logContext);
    }
  }

  /**
   * Log an info message with context (development only)
   */
  static logInfo(
    message: string,
    context: ErrorContext = {}
  ): void {
    if (!this.isDevelopment) return;

    console.group(`ℹ️ Info: ${context.component || 'Unknown'}`);
    console.info('Message:', message);
    if (context.operation) console.info('Operation:', context.operation);
    if (context.details) console.info('Details:', context.details);
    console.groupEnd();
  }

  /**
   * Log a debug message (development only)
   */
  static logDebug(
    message: string,
    data?: any
  ): void {
    if (!this.isDevelopment) return;
    console.debug('🐛 Debug:', message, data || '');
  }

  /**
   * Create an error handler for async operations
   */
  static async handleAsync<T>(
    operation: () => Promise<T>,
    context: ErrorContext,
    showUserError = false
  ): Promise<T | null> {
    try {
      return await operation();
    } catch (error) {
      this.logError(error as Error, context, showUserError);
      return null;
    }
  }

  /**
   * Create an error handler for sync operations
   */
  static handleSync<T>(
    operation: () => T,
    context: ErrorContext,
    showUserError = false
  ): T | null {
    try {
      return operation();
    } catch (error) {
      this.logError(error as Error, context, showUserError);
      return null;
    }
  }

  /**
   * Show error to user via the global error handling system
   */
  private static showUserError(message: string, context: ErrorContext): void {
    // This would integrate with the global error state
    // For now, we'll use the store directly
    try {
      const { handleError } = useErrorHandling();
      handleError(message);
    } catch {
      // Fallback if store is not available
      console.warn('Could not show error to user:', message);
    }
  }

  /**
   * Send error to external tracking service (production only)
   */
  private static sendToErrorTracking(logContext: any): void {
    // This would integrate with services like Sentry, LogRocket, etc.
    // For now, we'll just store in sessionStorage for debugging
    try {
      const existingErrors = JSON.parse(sessionStorage.getItem('lexicon_errors') || '[]');
      existingErrors.push(logContext);
      
      // Keep only last 100 errors
      if (existingErrors.length > 100) {
        existingErrors.splice(0, existingErrors.length - 100);
      }
      
      sessionStorage.setItem('lexicon_errors', JSON.stringify(existingErrors));
    } catch {
      // Ignore sessionStorage errors
    }
  }

  /**
   * Get stored errors for debugging
   */
  static getStoredErrors(): any[] {
    try {
      return JSON.parse(sessionStorage.getItem('lexicon_errors') || '[]');
    } catch {
      return [];
    }
  }

  /**
   * Clear stored errors
   */
  static clearStoredErrors(): void {
    try {
      sessionStorage.removeItem('lexicon_errors');
    } catch {
      // Ignore
    }
  }
}

/**
 * Hook-friendly error handler
 */
export function useStandardizedError() {
  return {
    logError: ErrorHandler.logError,
    logWarning: ErrorHandler.logWarning,
    logInfo: ErrorHandler.logInfo,
    logDebug: ErrorHandler.logDebug,
    handleAsync: ErrorHandler.handleAsync,
    handleSync: ErrorHandler.handleSync,
    getStoredErrors: ErrorHandler.getStoredErrors,
    clearStoredErrors: ErrorHandler.clearStoredErrors
  };
}
