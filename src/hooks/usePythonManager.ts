import { useState, useEffect, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

export interface PythonEnvironment {
  python_path: string;
  venv_path?: string;
  version: string;
  isolated: boolean;
}

export interface PythonProcessResult {
  success: boolean;
  stdout: string;
  stderr: string;
  exit_code?: number;
}

export interface PythonHealthStatus {
  status: 'healthy' | 'warning' | 'critical' | 'error';
  issues?: string[];
  python?: {
    version: string;
    compatible: boolean;
  };
  modules?: Record<string, { available: boolean; version?: string }>;
  pip?: {
    available: boolean;
    version?: string;
  };
}

export interface UsePythonManagerReturn {
  environment: PythonEnvironment | null;
  healthStatus: PythonHealthStatus | null;
  isLoading: boolean;
  error: string | null;
  discoverEnvironment: () => Promise<void>;
  createEnvironment: () => Promise<void>;
  executeScript: (scriptName: string, args?: string[]) => Promise<PythonProcessResult>;
  executeCode: (code: string) => Promise<PythonProcessResult>;
  checkHealth: () => Promise<void>;
  refreshStatus: () => Promise<void>;
}

export const usePythonManager = (): UsePythonManagerReturn => {
  const [environment, setEnvironment] = useState<PythonEnvironment | null>(null);
  const [healthStatus, setHealthStatus] = useState<PythonHealthStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleError = useCallback((error: unknown, context: string) => {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error(`Python Manager Error (${context}):`, errorMessage);
    setError(`${context}: ${errorMessage}`);
  }, []);

  const discoverEnvironment = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const env = await invoke<PythonEnvironment>('discover_python_environment');
      setEnvironment(env);
      console.log('Python environment discovered:', env);
    } catch (error) {
      handleError(error, 'Discovery failed');
    } finally {
      setIsLoading(false);
    }
  }, [handleError]);

  const createEnvironment = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const env = await invoke<PythonEnvironment>('create_python_environment');
      setEnvironment(env);
      console.log('Python environment created:', env);
    } catch (error) {
      handleError(error, 'Environment creation failed');
    } finally {
      setIsLoading(false);
    }
  }, [handleError]);

  const executeScript = useCallback(async (
    scriptName: string, 
    args: string[] = []
  ): Promise<PythonProcessResult> => {
    setError(null);
    
    try {
      const result = await invoke<PythonProcessResult>('execute_python_script', {
        scriptName,
        args,
      });
      
      if (!result.success) {
        console.warn(`Script '${scriptName}' failed:`, result.stderr);
      }
      
      return result;
    } catch (error) {
      handleError(error, `Script execution failed (${scriptName})`);
      return {
        success: false,
        stdout: '',
        stderr: error instanceof Error ? error.message : String(error),
        exit_code: -1,
      };
    }
  }, [handleError]);

  const executeCode = useCallback(async (code: string): Promise<PythonProcessResult> => {
    setError(null);
    
    try {
      const result = await invoke<PythonProcessResult>('execute_python_code', { code });
      
      if (!result.success) {
        console.warn('Python code execution failed:', result.stderr);
      }
      
      return result;
    } catch (error) {
      handleError(error, 'Code execution failed');
      return {
        success: false,
        stdout: '',
        stderr: error instanceof Error ? error.message : String(error),
        exit_code: -1,
      };
    }
  }, [handleError]);

  const checkHealth = useCallback(async () => {
    setError(null);
    
    try {
      const health = await invoke<Record<string, any>>('python_health_check');
      setHealthStatus(health as PythonHealthStatus);
      console.log('Python health check completed:', health);
    } catch (error) {
      handleError(error, 'Health check failed');
      setHealthStatus({
        status: 'error',
        issues: [error instanceof Error ? error.message : String(error)],
      });
    }
  }, [handleError]);

  const refreshStatus = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Get current environment info
      const envInfo = await invoke<PythonEnvironment | null>('get_python_environment_info');
      setEnvironment(envInfo);
      
      // Run health check if environment exists
      if (envInfo) {
        await checkHealth();
      }
    } catch (error) {
      handleError(error, 'Status refresh failed');
    } finally {
      setIsLoading(false);
    }
  }, [handleError, checkHealth]);

  // Initialize on mount
  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  return {
    environment,
    healthStatus,
    isLoading,
    error,
    discoverEnvironment,
    createEnvironment,
    executeScript,
    executeCode,
    checkHealth,
    refreshStatus,
  };
};

// Utility hook for Python environment setup workflow
export const usePythonSetup = () => {
  const python = usePythonManager();
  const [setupPhase, setSetupPhase] = useState<
    'idle' | 'discovering' | 'creating' | 'installing' | 'complete' | 'error'
  >('idle');
  const [setupProgress, setSetupProgress] = useState(0);

  const runSetup = useCallback(async () => {
    setSetupPhase('discovering');
    setSetupProgress(25);

    try {
      // Try to discover existing environment first
      await python.discoverEnvironment();
      
      if (!python.environment?.isolated) {
        setSetupPhase('creating');
        setSetupProgress(50);
        
        // Create isolated environment
        await python.createEnvironment();
      }

      setSetupPhase('installing');
      setSetupProgress(75);

      // Install core dependencies
      const installResult = await python.executeScript('dependency_installer', [
        '--install-core'
      ]);

      if (!installResult.success) {
        throw new Error(`Dependency installation failed: ${installResult.stderr}`);
      }

      setSetupPhase('complete');
      setSetupProgress(100);

      // Final health check
      await python.checkHealth();

    } catch (error) {
      console.error('Python setup failed:', error);
      setSetupPhase('error');
    }
  }, [python]);

  return {
    ...python,
    setupPhase,
    setupProgress,
    runSetup,
  };
};
