import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { ErrorHandler, useStandardizedError, LOG_LEVELS, type ErrorContext } from '../../utils/errorHandler';

// Mock the store hooks
vi.mock('@/store/hooks', () => ({
  useErrorHandling: vi.fn(() => {
    throw new Error('Hook called outside component');
  })
}));

describe('ErrorHandler', () => {
  let consoleErrorSpy: any;
  let consoleWarnSpy: any;
  let consoleInfoSpy: any;
  let consoleDebugSpy: any;
  let consoleGroupSpy: any;
  let consoleGroupEndSpy: any;

  beforeEach(() => {
    // Mock console methods
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    consoleInfoSpy = vi.spyOn(console, 'info').mockImplementation(() => {});
    consoleDebugSpy = vi.spyOn(console, 'debug').mockImplementation(() => {});
    consoleGroupSpy = vi.spyOn(console, 'group').mockImplementation(() => {});
    consoleGroupEndSpy = vi.spyOn(console, 'groupEnd').mockImplementation(() => {});

    // Clear sessionStorage
    sessionStorage.clear();

    // Mock process.env - make sure to set development mode first
    vi.stubEnv('NODE_ENV', 'development');
    
    // Reset the ErrorHandler static property by accessing it
    (ErrorHandler as any).isDevelopment = true;
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.unstubAllEnvs();
    sessionStorage.clear();
  });

  describe('LOG_LEVELS', () => {
    it('should define all log levels correctly', () => {
      expect(LOG_LEVELS.INFO).toBe('info');
      expect(LOG_LEVELS.WARN).toBe('warn');
      expect(LOG_LEVELS.ERROR).toBe('error');
      expect(LOG_LEVELS.DEBUG).toBe('debug');
    });
  });

  describe('logError', () => {
    it('should log error with message string in development', () => {
      const errorMessage = 'Test error message';
      const context: ErrorContext = {
        component: 'TestComponent',
        operation: 'testOperation',
        details: { key: 'value' }
      };

      ErrorHandler.logError(errorMessage, context);

      expect(consoleGroupSpy).toHaveBeenCalledWith('🚨 Error: TestComponent');
      expect(consoleErrorSpy).toHaveBeenCalledWith('Message:', errorMessage);
      expect(consoleInfoSpy).toHaveBeenCalledWith('Operation:', 'testOperation');
      expect(consoleInfoSpy).toHaveBeenCalledWith('Details:', { key: 'value' });
      expect(consoleGroupEndSpy).toHaveBeenCalled();
    });

    it('should log error with Error object in development', () => {
      const error = new Error('Test error');
      const context: ErrorContext = { component: 'TestComponent' };

      ErrorHandler.logError(error, context);

      expect(consoleGroupSpy).toHaveBeenCalledWith('🚨 Error: TestComponent');
      expect(consoleErrorSpy).toHaveBeenCalledWith('Message:', 'Test error');
      expect(consoleErrorSpy).toHaveBeenCalledWith('Stack:', error.stack);
      expect(consoleGroupEndSpy).toHaveBeenCalled();
    });

    it('should handle missing context gracefully', () => {
      ErrorHandler.logError('Test error');

      expect(consoleGroupSpy).toHaveBeenCalledWith('🚨 Error: Unknown');
      expect(consoleErrorSpy).toHaveBeenCalledWith('Message:', 'Test error');
    });

    it('should log structured format in production', () => {
      vi.stubEnv('NODE_ENV', 'production');
      (ErrorHandler as any).isDevelopment = false;

      const error = new Error('Production error');
      const context: ErrorContext = { component: 'ProdComponent' };

      ErrorHandler.logError(error, context);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Application Error:',
        expect.objectContaining({
          timestamp: expect.any(String),
          level: 'error',
          message: 'Production error',
          stack: error.stack,
          context,
          userAgent: navigator.userAgent,
          url: window.location.href
        })
      );
    });

    it('should store errors in sessionStorage in production', () => {
      vi.stubEnv('NODE_ENV', 'production');
      (ErrorHandler as any).isDevelopment = false;

      ErrorHandler.logError('Production error', { component: 'Test' });

      const storedErrors = JSON.parse(sessionStorage.getItem('lexicon_errors') || '[]');
      expect(storedErrors).toHaveLength(1);
      expect(storedErrors[0]).toMatchObject({
        level: 'error',
        message: 'Production error'
      });
    });

    it('should limit stored errors to 100', () => {
      vi.stubEnv('NODE_ENV', 'production');
      (ErrorHandler as any).isDevelopment = false;

      // Pre-populate with 100 errors
      const existingErrors = Array.from({ length: 100 }, (_, i) => ({
        message: `Error ${i}`,
        timestamp: new Date().toISOString()
      }));
      sessionStorage.setItem('lexicon_errors', JSON.stringify(existingErrors));

      // Add one more error
      ErrorHandler.logError('New error');

      const storedErrors = JSON.parse(sessionStorage.getItem('lexicon_errors') || '[]');
      expect(storedErrors).toHaveLength(100);
      expect(storedErrors[99].message).toBe('New error');
    });

    it('should handle sessionStorage errors gracefully', () => {
      vi.stubEnv('NODE_ENV', 'production');
      (ErrorHandler as any).isDevelopment = false;

      // Mock sessionStorage to throw
      const originalSetItem = sessionStorage.setItem;
      sessionStorage.setItem = vi.fn().mockImplementation(() => {
        throw new Error('Storage error');
      });

      expect(() => {
        ErrorHandler.logError('Test error');
      }).not.toThrow();

      sessionStorage.setItem = originalSetItem;
    });
  });

  describe('logWarning', () => {
    it('should log warning in development', () => {
      const message = 'Test warning';
      const context: ErrorContext = {
        component: 'TestComponent',
        operation: 'testOp'
      };

      ErrorHandler.logWarning(message, context);

      expect(consoleGroupSpy).toHaveBeenCalledWith('⚠️ Warning: TestComponent');
      expect(consoleWarnSpy).toHaveBeenCalledWith('Message:', message);
      expect(consoleInfoSpy).toHaveBeenCalledWith('Operation:', 'testOp');
      expect(consoleGroupEndSpy).toHaveBeenCalled();
    });

    it('should log structured warning in production', () => {
      vi.stubEnv('NODE_ENV', 'production');
      (ErrorHandler as any).isDevelopment = false;

      ErrorHandler.logWarning('Production warning', { component: 'Test' });

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'Application Warning:',
        expect.objectContaining({
          level: 'warn',
          message: 'Production warning'
        })
      );
    });
  });

  describe('logInfo', () => {
    it('should log info in development', () => {
      const message = 'Test info';
      const context: ErrorContext = { component: 'TestComponent' };

      ErrorHandler.logInfo(message, context);

      expect(consoleGroupSpy).toHaveBeenCalledWith('ℹ️ Info: TestComponent');
      expect(consoleInfoSpy).toHaveBeenCalledWith('Message:', message);
      expect(consoleGroupEndSpy).toHaveBeenCalled();
    });

    it('should not log info in production', () => {
      vi.stubEnv('NODE_ENV', 'production');
      (ErrorHandler as any).isDevelopment = false;

      ErrorHandler.logInfo('Production info');

      expect(consoleGroupSpy).not.toHaveBeenCalled();
      expect(consoleInfoSpy).not.toHaveBeenCalled();
    });
  });

  describe('logDebug', () => {
    it('should log debug in development', () => {
      const message = 'Debug message';
      const data = { debug: true };

      ErrorHandler.logDebug(message, data);

      expect(consoleDebugSpy).toHaveBeenCalledWith('🐛 Debug:', message, data);
    });

    it('should handle missing data parameter', () => {
      ErrorHandler.logDebug('Debug message');

      expect(consoleDebugSpy).toHaveBeenCalledWith('🐛 Debug:', 'Debug message', '');
    });

    it('should not log debug in production', () => {
      vi.stubEnv('NODE_ENV', 'production');
      (ErrorHandler as any).isDevelopment = false;

      ErrorHandler.logDebug('Production debug');

      expect(consoleDebugSpy).not.toHaveBeenCalled();
    });
  });

  describe('handleAsync', () => {
    it('should return result on successful operation', async () => {
      const operation = vi.fn().mockResolvedValue('success');
      const context: ErrorContext = { component: 'TestComponent' };

      const result = await ErrorHandler.handleAsync(operation, context);

      expect(result).toBe('success');
      expect(operation).toHaveBeenCalledTimes(1);
    });

    it('should handle async errors and return null', async () => {
      const error = new Error('Async error');
      const operation = vi.fn().mockRejectedValue(error);
      const context: ErrorContext = { component: 'TestComponent' };

      const result = await ErrorHandler.handleAsync(operation, context);

      expect(result).toBeNull();
      expect(consoleGroupSpy).toHaveBeenCalledWith('🚨 Error: TestComponent');
    });

    it('should show user error when requested', async () => {
      const error = new Error('User error');
      const operation = vi.fn().mockRejectedValue(error);
      const context: ErrorContext = { component: 'TestComponent' };

      await ErrorHandler.handleAsync(operation, context, true);

      // Should attempt to show user error (will log warning due to mock)
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'Could not show error to user:',
        'User error'
      );
    });
  });

  describe('handleSync', () => {
    it('should return result on successful operation', () => {
      const operation = vi.fn().mockReturnValue('success');
      const context: ErrorContext = { component: 'TestComponent' };

      const result = ErrorHandler.handleSync(operation, context);

      expect(result).toBe('success');
      expect(operation).toHaveBeenCalledTimes(1);
    });

    it('should handle sync errors and return null', () => {
      const error = new Error('Sync error');
      const operation = vi.fn().mockImplementation(() => {
        throw error;
      });
      const context: ErrorContext = { component: 'TestComponent' };

      const result = ErrorHandler.handleSync(operation, context);

      expect(result).toBeNull();
      expect(consoleGroupSpy).toHaveBeenCalledWith('🚨 Error: TestComponent');
    });

    it('should show user error when requested', () => {
      const error = new Error('User error');
      const operation = vi.fn().mockImplementation(() => {
        throw error;
      });
      const context: ErrorContext = { component: 'TestComponent' };

      ErrorHandler.handleSync(operation, context, true);

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'Could not show error to user:',
        'User error'
      );
    });
  });

  describe('getStoredErrors', () => {
    it('should return stored errors', () => {
      const errors = [{ message: 'Test error', timestamp: '2023-01-01' }];
      sessionStorage.setItem('lexicon_errors', JSON.stringify(errors));

      const result = ErrorHandler.getStoredErrors();

      expect(result).toEqual(errors);
    });

    it('should return empty array when no errors stored', () => {
      const result = ErrorHandler.getStoredErrors();

      expect(result).toEqual([]);
    });

    it('should handle sessionStorage parse errors', () => {
      sessionStorage.setItem('lexicon_errors', 'invalid json');

      const result = ErrorHandler.getStoredErrors();

      expect(result).toEqual([]);
    });

    it('should handle sessionStorage access errors', () => {
      const originalGetItem = sessionStorage.getItem;
      sessionStorage.getItem = vi.fn().mockImplementation(() => {
        throw new Error('Storage error');
      });

      const result = ErrorHandler.getStoredErrors();

      expect(result).toEqual([]);

      sessionStorage.getItem = originalGetItem;
    });
  });

  describe('clearStoredErrors', () => {
    it('should clear stored errors', () => {
      sessionStorage.setItem('lexicon_errors', JSON.stringify([{ message: 'test' }]));

      ErrorHandler.clearStoredErrors();

      expect(sessionStorage.getItem('lexicon_errors')).toBeNull();
    });

    it('should handle sessionStorage errors gracefully', () => {
      const originalRemoveItem = sessionStorage.removeItem;
      sessionStorage.removeItem = vi.fn().mockImplementation(() => {
        throw new Error('Storage error');
      });

      expect(() => {
        ErrorHandler.clearStoredErrors();
      }).not.toThrow();

      sessionStorage.removeItem = originalRemoveItem;
    });
  });
});

describe('useStandardizedError', () => {
  it('should return all ErrorHandler methods', () => {
    const { result } = renderHook(() => useStandardizedError());

    expect(result.current).toHaveProperty('logError');
    expect(result.current).toHaveProperty('logWarning');
    expect(result.current).toHaveProperty('logInfo');
    expect(result.current).toHaveProperty('logDebug');
    expect(result.current).toHaveProperty('handleAsync');
    expect(result.current).toHaveProperty('handleSync');
    expect(result.current).toHaveProperty('getStoredErrors');
    expect(result.current).toHaveProperty('clearStoredErrors');

    expect(typeof result.current.logError).toBe('function');
    expect(typeof result.current.logWarning).toBe('function');
    expect(typeof result.current.logInfo).toBe('function');
    expect(typeof result.current.logDebug).toBe('function');
    expect(typeof result.current.handleAsync).toBe('function');
    expect(typeof result.current.handleSync).toBe('function');
    expect(typeof result.current.getStoredErrors).toBe('function');
    expect(typeof result.current.clearStoredErrors).toBe('function');
  });

  it('should provide working references to ErrorHandler methods', () => {
    const { result } = renderHook(() => useStandardizedError());
    
    // Create fresh spies for this test  
    const localConsoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    
    result.current.logWarning('Test warning', { component: 'Hook' });

    // Verify the method was called (the format depends on the environment)
    expect(localConsoleWarnSpy).toHaveBeenCalled();
    const [firstArg, secondArg] = localConsoleWarnSpy.mock.calls[0];
    
    // In development mode: expect('Message:', 'Test warning')
    // In production mode: expect('Application Warning:', {object})
    if (firstArg === 'Message:') {
      expect(firstArg).toBe('Message:');
      expect(secondArg).toBe('Test warning');
    } else {
      expect(firstArg).toBe('Application Warning:');
      expect(secondArg).toMatchObject({
        level: 'warn',
        message: 'Test warning',
        context: { component: 'Hook' }
      });
    }
    
    // Clean up local spy
    localConsoleWarnSpy.mockRestore();
  });
});
