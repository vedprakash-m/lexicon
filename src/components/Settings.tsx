import React, { useState } from 'react';
import { useLexiconStore } from '../store';
import CloudSyncSettings from './CloudSyncSettings';
import { useToastActions } from './ui/toast';

const Settings: React.FC = () => {
  const { settings, updateSettings } = useLexiconStore();
  const [activeTab, setActiveTab] = useState<'general' | 'cloud' | 'advanced'>('general');
  const [isSaving, setIsSaving] = useState(false);
  const { success, error } = useToastActions();

  const handleSettingsUpdate = async (updates: any) => {
    setIsSaving(true);
    try {
      await updateSettings(updates);
      success('Settings saved successfully');
    } catch (err) {
      console.error('Failed to save settings:', err);
      error('Failed to save settings', err instanceof Error ? err.message : undefined);
    } finally {
      setIsSaving(false);
    }
  };

  const tabs = [
    { id: 'general', label: 'General', icon: '⚙️' },
    { id: 'cloud', label: 'Cloud Sync', icon: '☁️' },
    { id: 'advanced', label: 'Advanced', icon: '🔧' },
  ];

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Configure your Lexicon application preferences
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700 mb-8">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        {activeTab === 'general' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                General Settings
              </h3>
            </div>

            {/* Theme Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Theme
              </label>
              <select
                value={settings.theme}
                onChange={(e) => handleSettingsUpdate({ theme: e.target.value as any })}
                className="w-full rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700"
              >
                <option value="system">System</option>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
            </div>

            {/* Language Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Language
              </label>
              <select
                value={settings.language}
                onChange={(e) => handleSettingsUpdate({ language: e.target.value })}
                className="w-full rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700"
              >
                <option value="en">English</option>
                <option value="es">Español</option>
                <option value="fr">Français</option>
                <option value="de">Deutsch</option>
              </select>
            </div>

            {/* Auto Save */}
            <div>
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={settings.autoSave}
                  onChange={(e) => handleSettingsUpdate({ autoSave: e.target.checked })}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <div className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Auto-save changes
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Automatically save your work as you make changes
                  </div>
                </div>
              </label>
            </div>

            {/* Backup Frequency */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Local Backup Frequency
              </label>
              <select
                value={settings.backupFrequency}
                onChange={(e) => handleSettingsUpdate({ backupFrequency: e.target.value as any })}
                className="w-full rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700"
              >
                <option value="none">Never</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Note: Cloud sync provides real-time backup when enabled
              </p>
            </div>

            {/* Notifications */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Notifications
              </h4>
              <div className="space-y-3">
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={settings.notifications.processingComplete}
                    onChange={(e) => handleSettingsUpdate({
                      notifications: {
                        ...settings.notifications,
                        processingComplete: e.target.checked
                      }
                    })}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    Processing complete notifications
                  </span>
                </label>

                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={settings.notifications.errors}
                    onChange={(e) => handleSettingsUpdate({
                      notifications: {
                        ...settings.notifications,
                        errors: e.target.checked
                      }
                    })}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    Error notifications
                  </span>
                </label>

                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={settings.notifications.updates}
                    onChange={(e) => handleSettingsUpdate({
                      notifications: {
                        ...settings.notifications,
                        updates: e.target.checked
                      }
                    })}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    Update notifications
                  </span>
                </label>

                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={settings.notifications.cloudSync}
                    onChange={(e) => handleSettingsUpdate({
                      notifications: {
                        ...settings.notifications,
                        cloudSync: e.target.checked
                      }
                    })}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    Cloud sync notifications
                  </span>
                </label>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'cloud' && <CloudSyncSettings />}

        {activeTab === 'advanced' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Advanced Settings
              </h3>
            </div>

            {/* Python Path */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Python Path (Optional)
              </label>
              <input
                type="text"
                value={settings.pythonPath || ''}
                onChange={(e) => handleSettingsUpdate({ pythonPath: e.target.value || undefined })}
                placeholder="Auto-detect Python installation"
                className="w-full rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Leave empty to auto-detect Python. Specify a custom path if needed.
              </p>
            </div>

            {/* Default Chunking Strategy */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Default Chunking Strategy
              </label>
              <select
                value={settings.defaultChunkingStrategy.type}
                onChange={(e) => handleSettingsUpdate({
                  defaultChunkingStrategy: {
                    ...settings.defaultChunkingStrategy,
                    type: e.target.value as any
                  }
                })}
                disabled={isSaving}
                className="w-full rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700"
              >
                <option value="semantic">Semantic</option>
                <option value="fixed_size">Fixed Size</option>
                <option value="paragraph">Paragraph</option>
                <option value="sentence">Sentence</option>
              </select>
            </div>

            {/* Chunk Size */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Default Chunk Size
              </label>
              <input
                type="number"
                value={settings.defaultChunkingStrategy.maxTokens || 512}
                onChange={(e) => handleSettingsUpdate({
                  defaultChunkingStrategy: {
                    ...settings.defaultChunkingStrategy,
                    maxTokens: parseInt(e.target.value)
                  }
                })}
                disabled={isSaving}
                min="100"
                max="10000"
                className="w-full rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Maximum tokens per chunk
              </p>
            </div>

            {/* Export Format */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Default Export Format
              </label>
              <select
                value={settings.defaultExportConfig.format}
                onChange={(e) => handleSettingsUpdate({
                  defaultExportConfig: {
                    ...settings.defaultExportConfig,
                    format: e.target.value as any
                  }
                })}
                className="w-full rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700"
              >
                <option value="json">JSON</option>
                <option value="csv">CSV</option>
                <option value="parquet">Parquet</option>
                <option value="jsonl">JSONL</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Save Button */}
      <div className="mt-8 flex justify-end">
        <button
          onClick={() => {
            // Settings are saved automatically via the store
            // This could trigger a toast notification
            console.log('Settings saved');
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          Save Settings
        </button>
      </div>
    </div>
  );
};

export default Settings;
