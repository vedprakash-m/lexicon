import React, { useState } from 'react';
import { useLexiconStore } from '../store';
import { invoke } from '@tauri-apps/api/tauri';

interface CloudProvider {
  id: 'none' | 'icloud' | 'google_drive' | 'dropbox' | 'onedrive';
  name: string;
  description: string;
  icon: string;
  platforms: string[];
  features: string[];
  available: boolean;
}

interface SyncStatus {
  enabled: boolean;
  lastSync: string | null;
  provider: string | null;
  conflicts: number;
  pendingUploads: number;
  pendingDownloads: number;
}

const CloudSyncSettings: React.FC = () => {
  const { settings, updateSettings } = useLexiconStore();
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [providers, setProviders] = useState<CloudProvider[]>([
    {
      id: 'none',
      name: 'Disabled',
      description: 'No cloud synchronization',
      icon: '🚫',
      platforms: ['All'],
      features: ['Local storage only'],
      available: true,
    },
    {
      id: 'icloud',
      name: 'iCloud Drive',
      description: 'Apple iCloud Drive integration (macOS/iOS)',
      icon: '☁️',
      platforms: ['macOS', 'iOS'],
      features: ['Native integration', 'Cross-device sync', 'Version history', 'No setup required'],
      available: true,
    },
    {
      id: 'google_drive',
      name: 'Google Drive',
      description: 'Google Drive cloud storage',
      icon: '📁',
      platforms: ['All platforms'],
      features: ['15GB free storage', 'Version history', 'Sharing capabilities', 'Cross-platform'],
      available: true,
    },
    {
      id: 'dropbox',
      name: 'Dropbox',
      description: 'Dropbox cloud storage and sync',
      icon: '📦',
      platforms: ['All platforms'],
      features: ['Smart sync', 'Team collaboration', 'Advanced sharing', 'API integration'],
      available: true,
    },
    {
      id: 'onedrive',
      name: 'Microsoft OneDrive',
      description: 'Microsoft OneDrive cloud storage',
      icon: '🔵',
      platforms: ['Windows', 'macOS', 'iOS', 'Android'],
      features: ['Office integration', '5GB free storage', 'Version history', 'Enterprise features'],
      available: true,
    },
  ]);

  React.useEffect(() => {
    // Load sync status on component mount
    loadSyncStatus();
  }, []);

  const loadSyncStatus = async () => {
    try {
      const status = await invoke<SyncStatus>('get_sync_status');
      setSyncStatus(status);
    } catch (error) {
      console.error('Failed to load sync status:', error);
    }
  };

  const handleProviderChange = async (providerId: CloudProvider['id']) => {
    const newSettings = {
      ...settings,
      cloudSync: {
        ...settings.cloudSync,
        provider: providerId,
        enabled: providerId !== 'none',
      },
    };

    updateSettings(newSettings);

    // If enabling sync, test connection
    if (providerId !== 'none') {
      await testConnection(providerId);
    }
  };

  const testConnection = async (providerId: string) => {
    setIsTestingConnection(true);
    try {
      const config = {
        provider: providerId,
        credentials: {},
        sync_folders: settings.cloudSync.syncPatterns,
        auto_sync: settings.cloudSync.autoSync,
        sync_interval: settings.cloudSync.syncInterval * 60, // Convert to seconds
      };

      await invoke('configure_sync', { config });
      
      // Refresh sync status
      await loadSyncStatus();
    } catch (error) {
      console.error('Failed to test connection:', error);
      // Show error to user
    } finally {
      setIsTestingConnection(false);
    }
  };

  const handleSyncSettingChange = (key: string, value: any) => {
    const newSettings = {
      ...settings,
      cloudSync: {
        ...settings.cloudSync,
        [key]: value,
      },
    };
    updateSettings(newSettings);
  };

  const startSync = async () => {
    try {
      await invoke('start_sync');
      await loadSyncStatus();
    } catch (error) {
      console.error('Failed to start sync:', error);
    }
  };

  const stopSync = async () => {
    try {
      await invoke('stop_sync');
      await loadSyncStatus();
    } catch (error) {
      console.error('Failed to stop sync:', error);
    }
  };

  const forceSync = async () => {
    try {
      await invoke('force_sync');
      await loadSyncStatus();
    } catch (error) {
      console.error('Failed to force sync:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Cloud Synchronization
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
          Keep your Lexicon data synchronized across devices and backed up in the cloud.
        </p>
      </div>

      {/* Cloud Provider Selection */}
      <div className="space-y-4">
        <h4 className="font-medium text-gray-900 dark:text-white">Choose Cloud Provider</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {providers.map((provider) => (
            <div
              key={provider.id}
              className={`relative border rounded-lg p-4 cursor-pointer transition-all ${
                settings.cloudSync.provider === provider.id
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              } ${!provider.available ? 'opacity-50 cursor-not-allowed' : ''}`}
              onClick={() => provider.available && handleProviderChange(provider.id)}
            >
              <div className="flex items-start space-x-3">
                <span className="text-2xl">{provider.icon}</span>
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h5 className="font-medium text-gray-900 dark:text-white">
                      {provider.name}
                    </h5>
                    {settings.cloudSync.provider === provider.id && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                        Selected
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {provider.description}
                  </p>
                  <div className="mt-2">
                    <div className="text-xs text-gray-500 dark:text-gray-500">
                      <strong>Platforms:</strong> {provider.platforms.join(', ')}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                      <strong>Features:</strong> {provider.features.join(', ')}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Sync Settings */}
      {settings.cloudSync.provider !== 'none' && (
        <div className="space-y-4">
          <h4 className="font-medium text-gray-900 dark:text-white">Sync Settings</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={settings.cloudSync.autoSync}
                  onChange={(e) => handleSyncSettingChange('autoSync', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Automatic synchronization
                </span>
              </label>
            </div>

            <div>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={settings.cloudSync.encryption}
                  onChange={(e) => handleSyncSettingChange('encryption', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Encrypt data before upload
                </span>
              </label>
            </div>

            <div>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={settings.cloudSync.compression}
                  onChange={(e) => handleSyncSettingChange('compression', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Compress data to save bandwidth
                </span>
              </label>
            </div>

            <div>
              <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">
                Sync interval (minutes)
              </label>
              <select
                value={settings.cloudSync.syncInterval}
                onChange={(e) => handleSyncSettingChange('syncInterval', parseInt(e.target.value))}
                className="w-full rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700 text-sm"
              >
                <option value={1}>1 minute</option>
                <option value={5}>5 minutes</option>
                <option value={15}>15 minutes</option>
                <option value={30}>30 minutes</option>
                <option value={60}>1 hour</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Sync Status */}
      {syncStatus && settings.cloudSync.provider !== 'none' && (
        <div className="space-y-4">
          <h4 className="font-medium text-gray-900 dark:text-white">Sync Status</h4>
          
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-gray-500 dark:text-gray-400">Status</div>
                <div className={`font-medium ${syncStatus.enabled ? 'text-green-600' : 'text-gray-600'}`}>
                  {syncStatus.enabled ? 'Active' : 'Inactive'}
                </div>
              </div>
              <div>
                <div className="text-gray-500 dark:text-gray-400">Last Sync</div>
                <div className="font-medium text-gray-900 dark:text-white">
                  {syncStatus.lastSync || 'Never'}
                </div>
              </div>
              <div>
                <div className="text-gray-500 dark:text-gray-400">Pending Uploads</div>
                <div className="font-medium text-gray-900 dark:text-white">
                  {syncStatus.pendingUploads}
                </div>
              </div>
              <div>
                <div className="text-gray-500 dark:text-gray-400">Conflicts</div>
                <div className={`font-medium ${syncStatus.conflicts > 0 ? 'text-red-600' : 'text-gray-900 dark:text-white'}`}>
                  {syncStatus.conflicts}
                </div>
              </div>
            </div>
          </div>

          {/* Sync Controls */}
          <div className="flex space-x-3">
            {syncStatus.enabled ? (
              <button
                onClick={stopSync}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
              >
                Stop Sync
              </button>
            ) : (
              <button
                onClick={startSync}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
              >
                Start Sync
              </button>
            )}
            
            <button
              onClick={forceSync}
              disabled={!syncStatus.enabled}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 text-sm"
            >
              Force Sync Now
            </button>

            {isTestingConnection && (
              <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span>Testing connection...</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Sync Patterns */}
      {settings.cloudSync.provider !== 'none' && (
        <div className="space-y-4">
          <h4 className="font-medium text-gray-900 dark:text-white">File Sync Patterns</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-700 dark:text-gray-300 mb-2">
                Files to sync (patterns)
              </label>
              <textarea
                value={settings.cloudSync.syncPatterns.join('\n')}
                onChange={(e) => handleSyncSettingChange('syncPatterns', e.target.value.split('\n').filter(p => p.trim()))}
                rows={4}
                className="w-full rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700 text-sm"
                placeholder="*.db&#10;*.json&#10;enrichment_*.json"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                One pattern per line. Use * for wildcards.
              </p>
            </div>

            <div>
              <label className="block text-sm text-gray-700 dark:text-gray-300 mb-2">
                Files to exclude (patterns)
              </label>
              <textarea
                value={settings.cloudSync.excludePatterns.join('\n')}
                onChange={(e) => handleSyncSettingChange('excludePatterns', e.target.value.split('\n').filter(p => p.trim()))}
                rows={4}
                className="w-full rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700 text-sm"
                placeholder="*.tmp&#10;*.log&#10;cache_*"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                One pattern per line. Use * for wildcards.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CloudSyncSettings;
