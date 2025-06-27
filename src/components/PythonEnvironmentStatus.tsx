import React from 'react';
import { CheckCircle, AlertCircle, XCircle, RefreshCw, Settings } from 'lucide-react';
import { usePythonManager } from '../hooks/usePythonManager';

interface PythonEnvironmentStatusProps {
  showDetails?: boolean;
  onSetupClick?: () => void;
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'healthy':
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    case 'warning':
      return <AlertCircle className="h-5 w-5 text-yellow-500" />;
    case 'critical':
    case 'error':
      return <XCircle className="h-5 w-5 text-red-500" />;
    default:
      return <AlertCircle className="h-5 w-5 text-gray-400" />;
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'healthy':
      return 'text-green-700 bg-green-50 border-green-200';
    case 'warning':
      return 'text-yellow-700 bg-yellow-50 border-yellow-200';
    case 'critical':
    case 'error':
      return 'text-red-700 bg-red-50 border-red-200';
    default:
      return 'text-gray-700 bg-gray-50 border-gray-200';
  }
};

export const PythonEnvironmentStatus: React.FC<PythonEnvironmentStatusProps> = ({
  showDetails = false,
  onSetupClick,
}) => {
  const { environment, healthStatus, isLoading, error, refreshStatus, checkHealth } = usePythonManager();

  const handleRefresh = async () => {
    await refreshStatus();
    await checkHealth();
  };

  if (isLoading) {
    return (
      <div className="flex items-center space-x-2 text-gray-600">
        <RefreshCw className="h-4 w-4 animate-spin" />
        <span className="text-sm">Checking Python environment...</span>
      </div>
    );
  }

  if (error && !environment) {
    return (
      <div className={`p-3 rounded-lg border ${getStatusColor('error')}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {getStatusIcon('error')}
            <span className="font-medium">Python Environment Error</span>
          </div>
          <button
            onClick={handleRefresh}
            className="text-red-600 hover:text-red-800"
            title="Retry"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
        <p className="text-sm mt-1">{error}</p>
        {onSetupClick && (
          <button
            onClick={onSetupClick}
            className="mt-2 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
          >
            Setup Python Environment
          </button>
        )}
      </div>
    );
  }

  if (!environment) {
    return (
      <div className={`p-3 rounded-lg border ${getStatusColor('warning')}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {getStatusIcon('warning')}
            <span className="font-medium">Python Environment Not Found</span>
          </div>
          {onSetupClick && (
            <button
              onClick={onSetupClick}
              className="flex items-center space-x-1 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
            >
              <Settings className="h-3 w-3" />
              <span>Setup</span>
            </button>
          )}
        </div>
        <p className="text-sm mt-1">
          Python environment needs to be configured for text processing.
        </p>
      </div>
    );
  }

  const status = healthStatus?.status || 'unknown';

  return (
    <div className={`p-3 rounded-lg border ${getStatusColor(status)}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStatusIcon(status)}
          <div>
            <span className="font-medium">Python Environment</span>
            <div className="text-xs text-gray-600">
              {environment.version} • {environment.isolated ? 'Isolated' : 'System'}
            </div>
          </div>
        </div>
        <button
          onClick={handleRefresh}
          className="text-gray-500 hover:text-gray-700"
          title="Refresh status"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {healthStatus?.issues && healthStatus.issues.length > 0 && (
        <div className="mt-2">
          <p className="text-sm font-medium">Issues:</p>
          <ul className="text-xs space-y-1 mt-1">
            {healthStatus.issues.map((issue, index) => (
              <li key={index} className="flex items-start space-x-1">
                <span>•</span>
                <span>{issue}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {showDetails && healthStatus && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            {/* Python Info */}
            {healthStatus.python && (
              <div>
                <h4 className="font-medium mb-1">Python</h4>
                <p>Version: {healthStatus.python.version}</p>
                <p>Compatible: {healthStatus.python.compatible ? 'Yes' : 'No'}</p>
              </div>
            )}

            {/* Pip Info */}
            {healthStatus.pip && (
              <div>
                <h4 className="font-medium mb-1">Package Manager</h4>
                <p>pip: {healthStatus.pip.available ? 'Available' : 'Missing'}</p>
                {healthStatus.pip.version && <p>Version: {healthStatus.pip.version}</p>}
              </div>
            )}

            {/* Modules Info */}
            {healthStatus.modules && (
              <div className="md:col-span-2">
                <h4 className="font-medium mb-1">Dependencies</h4>
                <div className="grid grid-cols-2 gap-1">
                  {Object.entries(healthStatus.modules).map(([name, info]) => (
                    <div key={name} className="flex items-center justify-between">
                      <span>{name}</span>
                      <span className={info.available ? 'text-green-600' : 'text-red-600'}>
                        {info.available ? '✓' : '✗'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default PythonEnvironmentStatus;
