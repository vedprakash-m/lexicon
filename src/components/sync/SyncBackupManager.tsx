import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import { 
  Cloud, 
  CloudOff, 
  Shield, 
  RefreshCw, 
  Download, 
  Upload, 
  AlertCircle, 
  CheckCircle, 
  Archive, 
  Trash2, 
  Settings, 
  Plus,
  Play,
  Square,
  RotateCcw,
  HardDrive,
  Clock,
  FileText,
  Zap
} from 'lucide-react';
import { useSyncManager, SyncConfig, BackupConfig } from '@/hooks/useSyncManager';
import { formatBytes, formatRelativeTime } from '@/lib/utils';

export const SyncBackupManager: React.FC = () => {
  const {
    syncStatus,
    backups,
    isLoading,
    error,
    isOperationInProgress,
    configureSync,
    startSync,
    stopSync,
    createBackup,
    restoreBackup,
    deleteBackup,
    verifyBackup,
    configureBackup,
    refreshData,
    clearError
  } = useSyncManager();

  const [showSyncConfig, setShowSyncConfig] = useState(false);
  const [showBackupConfig, setShowBackupConfig] = useState(false);
  const [newBackupName, setNewBackupName] = useState('');
  const [selectedProvider, setSelectedProvider] = useState('local');

  // Sync Configuration Form
  const [syncConfigForm, setSyncConfigForm] = useState<SyncConfig>({
    provider: 'local',
    credentials: {},
    sync_interval: 300, // 5 minutes
    auto_sync: true,
    encryption_enabled: true
  });

  // Backup Configuration Form
  const [backupConfigForm, setBackupConfigForm] = useState<BackupConfig>({
    auto_backup: true,
    backup_interval: 3600, // 1 hour
    max_backups: 10,
    backup_location: '/Users/vedprakashmishra/lexicon-backups',
    compress: true,
    encrypt: true
  });

  const handleSyncConfig = async () => {
    const success = await configureSync(syncConfigForm);
    if (success) {
      setShowSyncConfig(false);
    }
  };

  const handleBackupConfig = async () => {
    const success = await configureBackup(backupConfigForm);
    if (success) {
      setShowBackupConfig(false);
    }
  };

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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Sync & Backup</h1>
          <p className="text-muted-foreground">
            Manage cloud synchronization and data backup systems
          </p>
        </div>
        <Button onClick={refreshData} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription className="flex items-center justify-between">
            {error}
            <Button variant="ghost" size="sm" onClick={clearError}>
              Dismiss
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="sync" className="space-y-4">
        <TabsList>
          <TabsTrigger value="sync">Cloud Sync</TabsTrigger>
          <TabsTrigger value="backup">Backup & Restore</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        {/* Cloud Sync Tab */}
        <TabsContent value="sync" className="space-y-4">
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
                  <Label className="text-sm text-muted-foreground">Status</Label>
                  <Badge variant={syncStatus?.enabled ? "default" : "secondary"}>
                    {syncStatus?.enabled ? "Active" : "Inactive"}
                  </Badge>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm text-muted-foreground">Provider</Label>
                  <Badge variant="outline">
                    {syncStatus?.provider || "None"}
                  </Badge>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm text-muted-foreground">Last Sync</Label>
                  <p className="text-sm">
                    {syncStatus?.last_sync ? formatRelativeTime(new Date(syncStatus.last_sync)) : "Never"}
                  </p>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm text-muted-foreground">Conflicts</Label>
                  <Badge variant={syncStatus?.conflicts ? "destructive" : "default"}>
                    {syncStatus?.conflicts || 0}
                  </Badge>
                </div>
              </div>

              {syncStatus?.enabled && (
                <div className="space-y-2">
                  <Label className="text-sm text-muted-foreground">Sync Activity</Label>
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

              <Separator />

              <div className="flex gap-2">
                {syncStatus?.enabled ? (
                  <Button
                    onClick={stopSync}
                    disabled={isOperationInProgress}
                    variant="destructive"
                  >
                    <Square className="h-4 w-4 mr-2" />
                    Stop Sync
                  </Button>
                ) : (
                  <Button
                    onClick={startSync}
                    disabled={isOperationInProgress}
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Start Sync
                  </Button>
                )}
                
                <Dialog open={showSyncConfig} onOpenChange={setShowSyncConfig}>
                  <DialogTrigger asChild>
                    <Button variant="outline">
                      <Settings className="h-4 w-4 mr-2" />
                      Configure
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-md">
                    <DialogHeader>
                      <DialogTitle>Sync Configuration</DialogTitle>
                      <DialogDescription>
                        Configure cloud synchronization settings
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <Label>Provider</Label>
                        <Select 
                          value={syncConfigForm.provider} 
                          onValueChange={(value) => setSyncConfigForm(prev => ({ ...prev, provider: value }))}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="local">Local Storage</SelectItem>
                            <SelectItem value="icloud">iCloud</SelectItem>
                            <SelectItem value="google_drive">Google Drive</SelectItem>
                            <SelectItem value="dropbox">Dropbox</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label>Sync Interval (seconds)</Label>
                        <Input
                          type="number"
                          value={syncConfigForm.sync_interval}
                          onChange={(e) => setSyncConfigForm(prev => ({ 
                            ...prev, 
                            sync_interval: parseInt(e.target.value) || 300 
                          }))}
                        />
                      </div>

                      <div className="flex items-center space-x-2">
                        <Switch
                          checked={syncConfigForm.auto_sync}
                          onCheckedChange={(checked) => setSyncConfigForm(prev => ({ 
                            ...prev, 
                            auto_sync: checked 
                          }))}
                        />
                        <Label>Auto Sync</Label>
                      </div>

                      <div className="flex items-center space-x-2">
                        <Switch
                          checked={syncConfigForm.encryption_enabled}
                          onCheckedChange={(checked) => setSyncConfigForm(prev => ({ 
                            ...prev, 
                            encryption_enabled: checked 
                          }))}
                        />
                        <Label>Enable Encryption</Label>
                      </div>

                      <div className="flex gap-2">
                        <Button onClick={handleSyncConfig} disabled={isOperationInProgress}>
                          Save Configuration
                        </Button>
                        <Button variant="outline" onClick={() => setShowSyncConfig(false)}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Backup & Restore Tab */}
        <TabsContent value="backup" className="space-y-4">
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
                >
                  <Archive className="h-4 w-4 mr-2" />
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
                <div className="text-center py-8 text-muted-foreground">
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
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
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
                          >
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Verify
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => restoreBackup(backup.id)}
                            disabled={isOperationInProgress}
                          >
                            <RotateCcw className="h-3 w-3 mr-1" />
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
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Backup Configuration
              </CardTitle>
              <CardDescription>
                Configure automatic backup settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Backup Location</Label>
                  <Input
                    value={backupConfigForm.backup_location}
                    onChange={(e) => setBackupConfigForm(prev => ({ 
                      ...prev, 
                      backup_location: e.target.value 
                    }))}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Backup Interval (seconds)</Label>
                  <Input
                    type="number"
                    value={backupConfigForm.backup_interval}
                    onChange={(e) => setBackupConfigForm(prev => ({ 
                      ...prev, 
                      backup_interval: parseInt(e.target.value) || 3600 
                    }))}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Max Backups to Keep</Label>
                  <Input
                    type="number"
                    value={backupConfigForm.max_backups}
                    onChange={(e) => setBackupConfigForm(prev => ({ 
                      ...prev, 
                      max_backups: parseInt(e.target.value) || 10 
                    }))}
                  />
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Switch
                    checked={backupConfigForm.auto_backup}
                    onCheckedChange={(checked) => setBackupConfigForm(prev => ({ 
                      ...prev, 
                      auto_backup: checked 
                    }))}
                  />
                  <Label>Enable Automatic Backups</Label>
                </div>

                <div className="flex items-center space-x-2">
                  <Switch
                    checked={backupConfigForm.compress}
                    onCheckedChange={(checked) => setBackupConfigForm(prev => ({ 
                      ...prev, 
                      compress: checked 
                    }))}
                  />
                  <Label>Compress Backups</Label>
                </div>

                <div className="flex items-center space-x-2">
                  <Switch
                    checked={backupConfigForm.encrypt}
                    onCheckedChange={(checked) => setBackupConfigForm(prev => ({ 
                      ...prev, 
                      encrypt: checked 
                    }))}
                  />
                  <Label>Encrypt Backups</Label>
                </div>
              </div>

              <Button onClick={handleBackupConfig} disabled={isOperationInProgress}>
                <Settings className="h-4 w-4 mr-2" />
                Save Configuration
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
