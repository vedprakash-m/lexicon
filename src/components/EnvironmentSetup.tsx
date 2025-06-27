import { useState, useEffect } from 'react';
import { useEnvironmentManager } from '../hooks/useEnvironmentManager';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';

interface EnvironmentSetupProps {
  onSetupComplete?: () => void;
}

export function EnvironmentSetup({ onSetupComplete }: EnvironmentSetupProps) {
  const {
    createEnvironment,
    installDependencies,
    checkHealth,
    validateEnvironment,
    getConfig,
    isLoading,
    error
  } = useEnvironmentManager();

  const [environment, setEnvironment] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [validationIssues, setValidationIssues] = useState<string[]>([]);
  const [installProgress, setInstallProgress] = useState<any[]>([]);
  const [setupStep, setSetupStep] = useState<'initial' | 'creating' | 'installing' | 'validating' | 'complete'>('initial');

  useEffect(() => {
    loadExistingConfig();
  }, []);

  const loadExistingConfig = async () => {
    try {
      const config = await getConfig();
      if (config) {
        setEnvironment(config);
        setSetupStep('complete');
        await checkEnvironmentHealth();
      }
    } catch (err) {
      console.log('No existing environment config found');
    }
  };

  const checkEnvironmentHealth = async () => {
    try {
      const healthData = await checkHealth();
      setHealth(healthData);
    } catch (err) {
      console.error('Failed to check environment health:', err);
    }
  };

  const handleCreateEnvironment = async () => {
    setSetupStep('creating');
    try {
      const env = await createEnvironment('lexicon_env');
      setEnvironment(env);
      setSetupStep('installing');
      await handleInstallDependencies();
    } catch (err) {
      console.error('Failed to create environment:', err);
      setSetupStep('initial');
    }
  };

  const handleInstallDependencies = async () => {
    try {
      const progress = await installDependencies();
      setInstallProgress(progress);
      setSetupStep('validating');
      await handleValidateEnvironment();
    } catch (err) {
      console.error('Failed to install dependencies:', err);
      setSetupStep('creating');
    }
  };

  const handleValidateEnvironment = async () => {
    try {
      const issues = await validateEnvironment();
      setValidationIssues(issues);
      
      if (issues.length === 0) {
        setSetupStep('complete');
        await checkEnvironmentHealth();
        onSetupComplete?.();
      } else {
        setSetupStep('installing');
      }
    } catch (err) {
      console.error('Failed to validate environment:', err);
      setSetupStep('installing');
    }
  };

  const getStepIcon = (step: string) => {
    switch (step) {
      case 'complete':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'current':
        return <Clock className="w-4 h-4 text-blue-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <div className="w-4 h-4 border-2 border-gray-300 rounded-full" />;
    }
  };

  const getOverallStatus = () => {
    if (setupStep === 'complete' && health?.overall_status === 'healthy') {
      return { status: 'healthy', color: 'green', text: 'Environment Ready' };
    } else if (validationIssues.length > 0) {
      return { status: 'warning', color: 'yellow', text: 'Issues Detected' };
    } else if (setupStep === 'initial') {
      return { status: 'not-setup', color: 'gray', text: 'Not Set Up' };
    } else {
      return { status: 'in-progress', color: 'blue', text: 'Setting Up...' };
    }
  };

  const overallStatus = getOverallStatus();

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Python Environment Setup
          <Badge 
            variant={overallStatus.color === 'green' ? 'default' : 
                    overallStatus.color === 'yellow' ? 'secondary' : 
                    overallStatus.color === 'blue' ? 'outline' : 'destructive'}
          >
            {overallStatus.text}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center gap-2 text-red-700">
              <AlertTriangle className="w-4 h-4" />
              <span className="font-medium">Error</span>
            </div>
            <p className="text-red-600 mt-1">{error}</p>
          </div>
        )}

        {/* Setup Steps */}
        <div className="space-y-4">
          <h3 className="font-medium">Setup Progress</h3>
          
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              {getStepIcon(setupStep === 'creating' ? 'current' : 
                          setupStep === 'initial' ? 'pending' : 'complete')}
              <span className={setupStep === 'creating' ? 'font-medium' : ''}>
                Create Virtual Environment
              </span>
            </div>
            
            <div className="flex items-center gap-3">
              {getStepIcon(setupStep === 'installing' ? 'current' : 
                          ['initial', 'creating'].includes(setupStep) ? 'pending' : 'complete')}
              <span className={setupStep === 'installing' ? 'font-medium' : ''}>
                Install Dependencies
              </span>
            </div>
            
            <div className="flex items-center gap-3">
              {getStepIcon(setupStep === 'validating' ? 'current' : 
                          ['initial', 'creating', 'installing'].includes(setupStep) ? 'pending' : 'complete')}
              <span className={setupStep === 'validating' ? 'font-medium' : ''}>
                Validate Environment
              </span>
            </div>
          </div>
        </div>

        {/* Environment Info */}
        {environment && (
          <div className="space-y-3">
            <h3 className="font-medium">Environment Details</h3>
            <div className="bg-gray-50 p-3 rounded-lg space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Name:</span>
                <span className="text-sm font-medium">{environment.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Python Version:</span>
                <span className="text-sm font-medium">{environment.python_version}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Created:</span>
                <span className="text-sm font-medium">
                  {new Date(environment.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Health Status */}
        {health && (
          <div className="space-y-3">
            <h3 className="font-medium">Health Status</h3>
            <div className="bg-gray-50 p-3 rounded-lg space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Overall Status:</span>
                <Badge 
                  variant={health.overall_status === 'healthy' ? 'default' : 
                          health.overall_status === 'warning' ? 'secondary' : 'destructive'}
                >
                  {health.overall_status}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Pip Available:</span>
                <span className="text-sm">
                  {health.pip_available ? '✅' : '❌'}
                </span>
              </div>
              {health.disk_space_mb && (
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Estimated Size:</span>
                  <span className="text-sm font-medium">{health.disk_space_mb} MB</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Installation Progress */}
        {installProgress.length > 0 && (
          <div className="space-y-3">
            <h3 className="font-medium">Package Installation</h3>
            <div className="space-y-2">
              {installProgress.map((pkg, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="text-sm">{pkg.package_name}</span>
                  <div className="flex items-center gap-2">
                    <Progress value={pkg.progress_percent} className="w-16" />
                    <Badge 
                      variant={pkg.status === 'completed' ? 'default' : 
                              pkg.status === 'failed' ? 'destructive' : 'outline'}
                    >
                      {pkg.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Validation Issues */}
        {validationIssues.length > 0 && (
          <div className="space-y-3">
            <h3 className="font-medium text-yellow-700">Validation Issues</h3>
            <div className="space-y-1">
              {validationIssues.map((issue, index) => (
                <div key={index} className="flex items-center gap-2 text-sm text-yellow-700">
                  <AlertTriangle className="w-4 h-4" />
                  {issue}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2">
          {setupStep === 'initial' && (
            <Button 
              onClick={handleCreateEnvironment}
              disabled={isLoading}
              className="flex-1"
            >
              {isLoading ? 'Creating...' : 'Set Up Environment'}
            </Button>
          )}
          
          {setupStep === 'complete' && (
            <Button 
              onClick={checkEnvironmentHealth}
              variant="outline"
              disabled={isLoading}
            >
              Refresh Status
            </Button>
          )}
          
          {validationIssues.length > 0 && setupStep === 'installing' && (
            <Button 
              onClick={handleInstallDependencies}
              disabled={isLoading}
            >
              Retry Installation
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
