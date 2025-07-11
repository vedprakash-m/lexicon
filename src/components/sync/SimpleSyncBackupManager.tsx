import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Cloud, 
  CloudOff, 
  RefreshCw, 
  Download, 
  Upload, 
  AlertCircle, 
  CheckCircle, 
  Archive, 
  Trash2, 
  Plus,
  Play,
  Square,
  RotateCcw,
  HardDrive,
  Clock,
  FileText
} from 'lucide-react';
import { useSyncManager } from '@/hooks/useSyncManager';
import { formatBytes, formatRelativeTime } from '@/lib/utils';

export const SimpleSyncBackupManager: React.FC = () => {
  const {
    syncStatus,
    backups,
    isLoading,
    error,
    isOperationInProgress,
    startSync,
    stopSync,
    createBackup,
    restoreBackup,
    deleteBackup,
    verifyBackup,
    refreshData,
    clearError
  } = useSyncManager();

  const [newBackupName, setNewBackupName] = useState('');
  const [selectedTab, setSelectedTab] = useState('sync');

  const handleCreateBackup = async () => {
    if (!newBackupName.trim()) return;
    await createBackup(newBackupName);
    setNewBackupName('');
  };

  const getSyncStatusColor = (status: boolean) => {
    return status ? 'text-green-600' : 'text-gray-400';
  };

  const getSyncStatusIcon = (status: boolean) => {
    return status ? <Cloud className="h-4 w-4" /> : <CloudOff className="h-4 w-4" />;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-6 w-6 animate-spin mr-2" />
        <span>Loading sync and backup status...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Sync & Backup</h1>
          <p className="text-gray-600">
            Manage cloud synchronization and data backup systems
          </p>
        </div>
        <Button onClick={refreshData} className="flex items-center gap-2">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <h3 className="font-medium text-red-800">Error</h3>
          </div>
          <p className="text-red-700 mt-1">{error}</p>
          <Button 
            onClick={clearError} 
            className="mt-2 bg-red-600 text-white hover:bg-red-700"
            size="sm"
          >
            Dismiss
          </Button>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setSelectedTab('sync')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'sync'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Cloud Sync
          </button>
          <button
            onClick={() => setSelectedTab('backup')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'backup'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Backup & Restore
          </button>
        </nav>
      </div>

      {/* Cloud Sync Tab */}
      {selectedTab === 'sync' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {getSyncStatusIcon(syncStatus?.enabled || false)}
              <span className={getSyncStatusColor(syncStatus?.enabled || false)}>
                Sync Status
              </span>
            </CardTitle>
            <CardDescription>
              Current cloud synchronization status and controls
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-2">
                <Label className="text-sm text-gray-600">Status</Label>
                <Badge variant={syncStatus?.enabled ? "default" : "secondary"}>
                  {syncStatus?.enabled ? "Active" : "Inactive"}
                </Badge>
              </div>
              <div className="space-y-2">
                <Label className="text-sm text-gray-600">Provider</Label>
                <Badge variant="outline">
                  {syncStatus?.provider || "None"}
                </Badge>
              </div>
              <div className="space-y-2">
                <Label className="text-sm text-gray-600">Last Sync</Label>
                <p className="text-sm">
                  {syncStatus?.last_sync ? formatRelativeTime(new Date(syncStatus.last_sync)) : "Never"}
                </p>
              </div>
              <div className="space-y-2">
                <Label className="text-sm text-gray-600">Conflicts</Label>
                <Badge variant={syncStatus?.conflicts ? "destructive" : "default"}>
                  {syncStatus?.conflicts || 0}
                </Badge>
              </div>
            </div>

            {syncStatus?.enabled && (
              <div className="space-y-2">
                <Label className="text-sm text-gray-600">Sync Activity</Label>
                <div className="flex items-center gap-4 text-sm">
                  <div className="flex items-center gap-1">
                    <Upload className="h-3 w-3" />
                    <span>{syncStatus.pending_uploads} uploads pending</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Download className="h-3 w-3" />
                    <span>{syncStatus.pending_downloads} downloads pending</span>
                  </div>
                </div>
              </div>
            )}

            <hr className="my-4" />

            <div className="flex gap-2">
              {syncStatus?.enabled ? (
                <Button
                  onClick={stopSync}
                  disabled={isOperationInProgress}
                  variant="destructive"
                  className="flex items-center gap-2"
                >
                  <Square className="h-4 w-4" />
                  Stop Sync
                </Button>
              ) : (
                <Button
                  onClick={startSync}
                  disabled={isOperationInProgress}
                  className="flex items-center gap-2"
                >
                  <Play className="h-4 w-4" />
                  Start Sync
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Backup & Restore Tab */}
      {selectedTab === 'backup' && (
        <div className="space-y-4">
          {/* Create Backup */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Plus className="h-4 w-4" />
                Create Backup
              </CardTitle>
              <CardDescription>
                Create a new backup of your Lexicon data
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Input
                  placeholder="Backup name (e.g., 'Before major update')"
                  value={newBackupName}
                  onChange={(e) => setNewBackupName(e.target.value)}
                />
                <Button 
                  onClick={handleCreateBackup}
                  disabled={!newBackupName.trim() || isOperationInProgress}
                  className="flex items-center gap-2"
                >
                  <Archive className="h-4 w-4" />
                  Create
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Backups List */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Archive className="h-4 w-4" />
                Available Backups
              </CardTitle>
              <CardDescription>
                Manage your backup archives
              </CardDescription>
            </CardHeader>
            <CardContent>
              {backups.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Archive className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No backups found</p>
                  <p className="text-sm">Create your first backup to get started</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {backups.map((backup) => (
                    <div key={backup.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <h4 className="font-medium">{backup.name}</h4>
                            <Badge variant={backup.verified ? "default" : "destructive"}>
                              {backup.verified ? "Verified" : "Unverified"}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-4 text-sm text-gray-600">
                            <div className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {formatRelativeTime(new Date(backup.timestamp))}
                            </div>
                            <div className="flex items-center gap-1">
                              <HardDrive className="h-3 w-3" />
                              {formatBytes(backup.size)}
                            </div>
                            <div className="flex items-center gap-1">
                              <FileText className="h-3 w-3" />
                              {backup.file_count} files
                            </div>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => verifyBackup(backup.id)}
                            disabled={isOperationInProgress}
                            className="flex items-center gap-1"
                          >
                            <CheckCircle className="h-3 w-3" />
                            Verify
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => restoreBackup(backup.id)}
                            disabled={isOperationInProgress}
                            className="flex items-center gap-1"
                          >
                            <RotateCcw className="h-3 w-3" />
                            Restore
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => deleteBackup(backup.id)}
                            disabled={isOperationInProgress}
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};
