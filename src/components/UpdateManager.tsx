import React, { useState, useEffect } from 'react';
import { 
  Download, 
  RefreshCw, 
  CheckCircle, 
  AlertCircle, 
  Settings, 
  X, 
  Clock,
  Info,
  Zap
} from 'lucide-react';
import { 
  autoUpdater, 
  UpdateInfo, 
  UpdateConfig, 
  checkForUpdates,
  downloadAndInstall,
  getUpdateConfig,
  updateConfig,
  addUpdateListener,
  getUpdateStatus,
  forceUpdateCheck,
  skipVersion,
  restartApp
} from '../lib/autoUpdater';

interface UpdateManagerProps {
  className?: string;
}

export default function UpdateManager({ className = '' }: UpdateManagerProps) {
  const [updateInfo, setUpdateInfo] = useState<UpdateInfo | null>(null);
  const [config, setConfig] = useState<UpdateConfig | null>(null);
  const [status, setStatus] = useState({
    checking: false,
    downloading: false,
    installing: false,
    lastCheck: null as Date | null
  });
  const [showSettings, setShowSettings] = useState(false);
  const [updateProgress, setUpdateProgress] = useState<number>(0);
  const [notification, setNotification] = useState<{
    type: 'info' | 'success' | 'warning' | 'error';
    message: string;
  } | null>(null);

  useEffect(() => {
    initializeUpdateManager();
    
    // Set up event listeners
    const unsubscribe = addUpdateListener((event) => {
      handleUpdateEvent(event);
    });

    return () => {
      unsubscribe();
    };
  }, []);

  useEffect(() => {
    // Update status periodically
    const interval = setInterval(() => {
      setStatus(getUpdateStatus());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const initializeUpdateManager = async () => {
    try {
      const currentConfig = getUpdateConfig();
      setConfig(currentConfig);
      setStatus(getUpdateStatus());
    } catch (error) {
      console.error('Failed to initialize update manager:', error);
      showNotification('error', 'Failed to initialize update manager');
    }
  };

  const handleUpdateEvent = (event: { type: string; data?: any }) => {
    switch (event.type) {
      case 'checking':
        showNotification('info', 'Checking for updates...');
        break;
      case 'available':
        setUpdateInfo(event.data);
        showNotification('info', `Update ${event.data.version} is available!`);
        break;
      case 'downloaded':
        showNotification('success', 'Update downloaded successfully');
        break;
      case 'installed':
        showNotification('success', 'Update installed! Restart to apply changes.');
        break;
      case 'error':
        showNotification('error', `Update error: ${event.data || 'Unknown error'}`);
        break;
    }
  };

  const showNotification = (type: 'info' | 'success' | 'warning' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  };

  const handleCheckForUpdates = async () => {
    try {
      const update = await forceUpdateCheck();
      if (update && !update.available) {
        showNotification('success', 'You are running the latest version!');
      }
    } catch (error) {
      showNotification('error', 'Failed to check for updates');
    }
  };

  const handleDownloadUpdate = async () => {
    if (updateInfo) {
      try {
        await downloadAndInstall(updateInfo);
      } catch (error) {
        showNotification('error', 'Failed to download update');
      }
    }
  };

  const handleSkipVersion = async () => {
    if (updateInfo) {
      await skipVersion(updateInfo.version);
      setUpdateInfo(null);
      showNotification('info', `Version ${updateInfo.version} will be skipped`);
    }
  };

  const handleRestartApp = async () => {
    try {
      await restartApp();
    } catch (error) {
      showNotification('error', 'Failed to restart application');
    }
  };

  const handleConfigChange = async (newConfig: Partial<UpdateConfig>) => {
    if (config) {
      const updatedConfig = { ...config, ...newConfig };
      await updateConfig(newConfig);
      setConfig(updatedConfig);
      showNotification('success', 'Update settings saved');
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'warning':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      default:
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const formatLastCheckTime = (lastCheck: Date | null) => {
    if (!lastCheck) return 'Never';
    
    const now = new Date();
    const diffMs = now.getTime() - lastCheck.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (diffHours > 0) {
      return `${diffHours}h ${diffMinutes}m ago`;
    } else if (diffMinutes > 0) {
      return `${diffMinutes}m ago`;
    } else {
      return 'Just now';
    }
  };

  return (
    <div className={`space-y-4 p-6 bg-white rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Download className="w-6 h-6 text-blue-500" />
          <h2 className="text-xl font-semibold text-gray-900">Updates</h2>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
            title="Update Settings"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Notification */}
      {notification && (
        <div className={`flex items-center justify-between p-4 rounded-lg ${
          notification.type === 'error' ? 'bg-red-50 border border-red-200' :
          notification.type === 'success' ? 'bg-green-50 border border-green-200' :
          notification.type === 'warning' ? 'bg-yellow-50 border border-yellow-200' :
          'bg-blue-50 border border-blue-200'
        }`}>
          <div className="flex items-center">
            {getNotificationIcon(notification.type)}
            <span className={`ml-2 text-sm font-medium ${
              notification.type === 'error' ? 'text-red-800' :
              notification.type === 'success' ? 'text-green-800' :
              notification.type === 'warning' ? 'text-yellow-800' :
              'text-blue-800'
            }`}>
              {notification.message}
            </span>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Update Available */}
      {updateInfo && updateInfo.available && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <Zap className="w-6 h-6 text-blue-500 mt-0.5" />
              <div>
                <h3 className="text-lg font-semibold text-blue-900">
                  Update Available: v{updateInfo.version}
                </h3>
                <p className="text-blue-700 mt-1">
                  A new version of Lexicon is available.
                </p>
                {updateInfo.body && (
                  <div className="mt-3 p-3 bg-white rounded border">
                    <h4 className="font-medium text-gray-900 mb-2">Release Notes:</h4>
                    <div className="text-sm text-gray-700 whitespace-pre-wrap">
                      {updateInfo.body}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 mt-4">
            <button
              onClick={handleDownloadUpdate}
              disabled={status.downloading || status.installing}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {status.downloading ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Downloading...
                </>
              ) : status.installing ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Installing...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  Download & Install
                </>
              )}
            </button>
            
            <button
              onClick={handleSkipVersion}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg"
            >
              Skip This Version
            </button>
          </div>
          
          {updateProgress > 0 && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Download Progress</span>
                <span>{updateProgress.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${updateProgress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Status Card */}
      <div className="border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">Update Status</h3>
          <button
            onClick={handleCheckForUpdates}
            disabled={status.checking}
            className="inline-flex items-center px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${status.checking ? 'animate-spin' : ''}`} />
            Check Now
          </button>
        </div>
        
        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex justify-between">
            <span>Current Version:</span>
            <span className="font-medium">v{updateInfo?.currentVersion || '1.0.0'}</span>
          </div>
          <div className="flex justify-between">
            <span>Last Check:</span>
            <span className="font-medium">
              {formatLastCheckTime(status.lastCheck)}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Auto-check:</span>
            <span className="font-medium">
              {config?.autoCheck ? 'Enabled' : 'Disabled'}
            </span>
          </div>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && config && (
        <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
          <h3 className="font-semibold text-gray-900 mb-4">Update Settings</h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Automatic Updates
              </label>
              <input
                type="checkbox"
                checked={config.autoCheck}
                onChange={(e) => handleConfigChange({ autoCheck: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
            </div>
            
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Auto Install Updates
              </label>
              <input
                type="checkbox"
                checked={config.autoInstall}
                onChange={(e) => handleConfigChange({ autoInstall: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
            </div>
            
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Show Notifications
              </label>
              <input
                type="checkbox"
                checked={config.notifyUser}
                onChange={(e) => handleConfigChange({ notifyUser: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Check Interval
              </label>
              <select
                value={config.checkInterval}
                onChange={(e) => handleConfigChange({ checkInterval: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={60 * 60 * 1000}>Every Hour</option>
                <option value={6 * 60 * 60 * 1000}>Every 6 Hours</option>
                <option value={24 * 60 * 60 * 1000}>Daily</option>
                <option value={7 * 24 * 60 * 60 * 1000}>Weekly</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Update Channel
              </label>
              <select
                value={config.updateChannel}
                onChange={(e) => handleConfigChange({ updateChannel: e.target.value as any })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="stable">Stable</option>
                <option value="beta">Beta</option>
                <option value="alpha">Alpha</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* No Updates Available */}
      {!updateInfo?.available && !status.checking && (
        <div className="text-center py-8">
          <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">You're up to date!</h3>
          <p className="text-gray-500 mt-2">
            Lexicon will automatically check for updates in the background.
          </p>
        </div>
      )}
    </div>
  );
}
