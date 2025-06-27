import { useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

export interface EnvironmentConfig {
  name: string;
  python_version: string;
  requirements: string[];
  isolated: boolean;
  created_at: string;
}

export interface EnvironmentHealth {
  overall_status: 'healthy' | 'warning' | 'critical' | 'unknown';
  python_version?: string;
  pip_available: boolean;
  required_packages: Record<string, boolean>;
  disk_space_mb?: number;
  last_checked: string;
}

export interface DependencyInstallProgress {
  package_name: string;
  status: 'pending' | 'installing' | 'completed' | 'failed';
  progress_percent: number;
  error_message?: string;
}

export interface UseEnvironmentManagerReturn {
  config: EnvironmentConfig | null;
  health: EnvironmentHealth | null;
  isLoading: boolean;
  error: string | null;
  createEnvironment: (name: string) => Promise<EnvironmentConfig>;
  installDependencies: () => Promise<DependencyInstallProgress[]>;
  checkHealth: () => Promise<EnvironmentHealth>;
  validateEnvironment: () => Promise<string[]>;
  loadConfig: () => Promise<EnvironmentConfig | null>;
  getConfig: () => Promise<EnvironmentConfig | null>;
}

export const useEnvironmentManager = (): UseEnvironmentManagerReturn => {
  const [config, setConfig] = useState<EnvironmentConfig | null>(null);
  const [health, setHealth] = useState<EnvironmentHealth | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleError = useCallback((error: unknown, context: string) => {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error(`Environment Manager Error (${context}):`, errorMessage);
    setError(`${context}: ${errorMessage}`);
  }, []);

  const createEnvironment = useCallback(async (name: string): Promise<EnvironmentConfig> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const newConfig = await invoke<EnvironmentConfig>('create_python_virtual_environment', { name });
      setConfig(newConfig);
      console.log('Python virtual environment created:', newConfig);
      return newConfig;
    } catch (error) {
      handleError(error, 'Environment creation failed');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [handleError]);

  const installDependencies = useCallback(async (): Promise<DependencyInstallProgress[]> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const progress = await invoke<DependencyInstallProgress[]>('install_python_dependencies');
      console.log('Dependencies installation completed:', progress);
      
      // Refresh health after installation
      await checkHealth();
      return progress;
    } catch (error) {
      handleError(error, 'Dependency installation failed');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [handleError]);

  const checkHealth = useCallback(async (): Promise<EnvironmentHealth> => {
    setError(null);
    
    try {
      const healthStatus = await invoke<EnvironmentHealth>('check_environment_health');
      setHealth(healthStatus);
      console.log('Environment health checked:', healthStatus);
      return healthStatus;
    } catch (error) {
      handleError(error, 'Health check failed');
      throw error;
    }
  }, [handleError]);

  const validateEnvironment = useCallback(async (): Promise<string[]> => {
    setError(null);
    
    try {
      const issues = await invoke<string[]>('validate_python_environment');
      console.log('Environment validation completed:', issues);
      return issues;
    } catch (error) {
      handleError(error, 'Environment validation failed');
      return [error instanceof Error ? error.message : String(error)];
    }
  }, [handleError]);

  const loadConfig = useCallback(async (): Promise<EnvironmentConfig | null> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const loadedConfig = await invoke<EnvironmentConfig | null>('get_environment_config');
      setConfig(loadedConfig);
      console.log('Environment config loaded:', loadedConfig);
      return loadedConfig;
    } catch (error) {
      handleError(error, 'Config loading failed');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [handleError]);

  const getConfig = useCallback(async (): Promise<EnvironmentConfig | null> => {
    return loadConfig();
  }, [loadConfig]);

  return {
    config,
    health,
    isLoading,
    error,
    createEnvironment,
    installDependencies,
    checkHealth,
    validateEnvironment,
    loadConfig,
    getConfig,
  };
};

// Composite hook for complete environment setup workflow
export const useEnvironmentSetup = () => {
  const envManager = useEnvironmentManager();
  const [setupPhase, setSetupPhase] = useState<
    'idle' | 'configuring' | 'creating' | 'installing' | 'validating' | 'complete' | 'error'
  >('idle');
  const [setupProgress, setSetupProgress] = useState(0);

  const runCompleteSetup = useCallback(async (environmentName: string = 'lexicon-env') => {
    setSetupPhase('configuring');
    setSetupProgress(10);

    try {
      // Load existing config first
      setSetupPhase('configuring');
      setSetupProgress(20);
      await envManager.loadConfig();

      // Create environment if needed
      if (!envManager.config) {
        setSetupPhase('creating');
        setSetupProgress(40);
        await envManager.createEnvironment(environmentName);
      }

      // Install dependencies
      setSetupPhase('installing');
      setSetupProgress(60);
      await envManager.installDependencies();

      // Validate setup
      setSetupPhase('validating');
      setSetupProgress(80);
      const issues = await envManager.validateEnvironment();
      
      if (issues.length > 0) {
        console.warn('Environment setup completed with issues:', issues);
      }

      // Final health check
      await envManager.checkHealth();

      setSetupPhase('complete');
      setSetupProgress(100);

    } catch (error) {
      console.error('Complete environment setup failed:', error);
      setSetupPhase('error');
    }
  }, [envManager]);

  return {
    ...envManager,
    setupPhase,
    setupProgress,
    runCompleteSetup,
  };
};
