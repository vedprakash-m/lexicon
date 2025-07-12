import { useState } from 'react';
import { Plus, Trash2, Edit, CheckCircle, AlertCircle, Cloud, HardDrive, Database } from 'lucide-react';
import { Button, Card, Input, Label, Select } from '../ui';

interface SyncTarget {
  id: string;
  name: string;
  type: 'local' | 'dropbox' | 'google_drive' | 'aws_s3' | 'azure_blob';
  status: 'connected' | 'error' | 'disconnected';
  lastSync?: Date;
  config: Record<string, any>;
}

interface SyncTargetManagerProps {
  targets: SyncTarget[];
  onAddTarget: (target: Omit<SyncTarget, 'id'>) => void;
  onUpdateTarget: (id: string, target: Partial<SyncTarget>) => void;
  onDeleteTarget: (id: string) => void;
  onTestConnection: (id: string) => Promise<boolean>;
}

export function SyncTargetManager({ 
  targets, 
  onAddTarget, 
  onUpdateTarget, 
  onDeleteTarget, 
  onTestConnection 
}: SyncTargetManagerProps) {
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [editingTarget, setEditingTarget] = useState<SyncTarget | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    type: 'local' as SyncTarget['type'],
    config: {} as Record<string, any>
  });

  const targetTypes = [
    { value: 'local', label: 'Local Folder', icon: HardDrive },
    { value: 'dropbox', label: 'Dropbox', icon: Cloud },
    { value: 'google_drive', label: 'Google Drive', icon: Cloud },
    { value: 'aws_s3', label: 'AWS S3', icon: Database },
    { value: 'azure_blob', label: 'Azure Blob', icon: Database }
  ];

  const getStatusColor = (status: SyncTarget['status']) => {
    switch (status) {
      case 'connected': return 'text-green-600';
      case 'error': return 'text-red-600';
      case 'disconnected': return 'text-gray-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: SyncTarget['status']) => {
    switch (status) {
      case 'connected': return CheckCircle;
      case 'error': return AlertCircle;
      case 'disconnected': return AlertCircle;
      default: return AlertCircle;
    }
  };

  const renderConfigForm = (type: SyncTarget['type']) => {
    switch (type) {
      case 'local':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="folder-path">Folder Path</Label>
              <Input
                id="folder-path"
                value={formData.config.folderPath || ''}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  config: { ...prev.config, folderPath: e.target.value }
                }))}
                placeholder="/Users/username/Documents/Lexicon Sync"
              />
            </div>
          </div>
        );
      
      case 'dropbox':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="dropbox-folder">Dropbox Folder</Label>
              <Input
                id="dropbox-folder"
                value={formData.config.folder || ''}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  config: { ...prev.config, folder: e.target.value }
                }))}
                placeholder="/Apps/Lexicon"
              />
            </div>
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800">
                You'll be redirected to Dropbox to authorize access when you save this target.
              </p>
            </div>
          </div>
        );
      
      case 'google_drive':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="gdrive-folder">Google Drive Folder</Label>
              <Input
                id="gdrive-folder"
                value={formData.config.folder || ''}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  config: { ...prev.config, folder: e.target.value }
                }))}
                placeholder="Lexicon"
              />
            </div>
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800">
                You'll need to authorize access to your Google Drive when you save this target.
              </p>
            </div>
          </div>
        );
      
      case 'aws_s3':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="bucket-name">Bucket Name</Label>
              <Input
                id="bucket-name"
                value={formData.config.bucketName || ''}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  config: { ...prev.config, bucketName: e.target.value }
                }))}
                placeholder="lexicon-sync-bucket"
              />
            </div>
            <div>
              <Label htmlFor="region">Region</Label>
              <select 
                id="region"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                value={formData.config.region || ''} 
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  config: { ...prev.config, region: e.target.value }
                }))}
              >
                <option value="">Select region</option>
                <option value="us-east-1">US East (N. Virginia)</option>
                <option value="us-west-2">US West (Oregon)</option>
                <option value="eu-west-1">EU (Ireland)</option>
                <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
              </select>
            </div>
            <div>
              <Label htmlFor="access-key">Access Key ID</Label>
              <Input
                id="access-key"
                type="password"
                value={formData.config.accessKeyId || ''}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  config: { ...prev.config, accessKeyId: e.target.value }
                }))}
                placeholder="Your AWS Access Key ID"
              />
            </div>
            <div>
              <Label htmlFor="secret-key">Secret Access Key</Label>
              <Input
                id="secret-key"
                type="password"
                value={formData.config.secretAccessKey || ''}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  config: { ...prev.config, secretAccessKey: e.target.value }
                }))}
                placeholder="Your AWS Secret Access Key"
              />
            </div>
          </div>
        );
      
      case 'azure_blob':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="account-name">Storage Account Name</Label>
              <Input
                id="account-name"
                value={formData.config.accountName || ''}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  config: { ...prev.config, accountName: e.target.value }
                }))}
                placeholder="mystorageaccount"
              />
            </div>
            <div>
              <Label htmlFor="container-name">Container Name</Label>
              <Input
                id="container-name"
                value={formData.config.containerName || ''}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  config: { ...prev.config, containerName: e.target.value }
                }))}
                placeholder="lexicon-sync"
              />
            </div>
            <div>
              <Label htmlFor="account-key">Account Key</Label>
              <Input
                id="account-key"
                type="password"
                value={formData.config.accountKey || ''}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  config: { ...prev.config, accountKey: e.target.value }
                }))}
                placeholder="Your Azure Storage Account Key"
              />
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  const handleSave = () => {
    if (editingTarget) {
      onUpdateTarget(editingTarget.id, {
        name: formData.name,
        type: formData.type,
        config: formData.config
      });
      setEditingTarget(null);
    } else {
      onAddTarget({
        name: formData.name,
        type: formData.type,
        status: 'disconnected',
        config: formData.config
      });
      setShowAddDialog(false);
    }
    
    setFormData({ name: '', type: 'local', config: {} });
  };

  const handleEdit = (target: SyncTarget) => {
    setFormData({
      name: target.name,
      type: target.type,
      config: target.config
    });
    setEditingTarget(target);
  };

  const TypeIcon = targetTypes.find(t => t.value === formData.type)?.icon || HardDrive;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Sync Targets</h3>
          <p className="text-sm text-muted-foreground">
            Configure where your data will be synchronized
          </p>
        </div>
        <Button onClick={() => setShowAddDialog(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Target
        </Button>
      </div>

      {/* Targets List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {targets.map((target) => {
          const StatusIcon = getStatusIcon(target.status);
          const TargetTypeInfo = targetTypes.find(t => t.value === target.type);
          const TargetIcon = TargetTypeInfo?.icon || HardDrive;
          
          return (
            <Card key={target.id} className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <TargetIcon className="h-5 w-5 text-primary" />
                  <div>
                    <h4 className="font-medium">{target.name}</h4>
                    <p className="text-sm text-muted-foreground">
                      {TargetTypeInfo?.label}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-1">
                  <StatusIcon className={`h-4 w-4 ${getStatusColor(target.status)}`} />
                  <span className={`text-xs capitalize ${getStatusColor(target.status)}`}>
                    {target.status}
                  </span>
                </div>
              </div>
              
              {target.lastSync && (
                <p className="text-xs text-muted-foreground mb-3">
                  Last sync: {target.lastSync.toLocaleString()}
                </p>
              )}
              
              <div className="flex space-x-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="flex-1"
                  onClick={() => onTestConnection(target.id)}
                >
                  Test Connection
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => handleEdit(target)}
                >
                  <Edit className="h-3 w-3" />
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => onDeleteTarget(target.id)}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Empty State */}
      {targets.length === 0 && (
        <Card className="p-12 text-center">
          <Cloud className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Sync Targets</h3>
          <p className="text-muted-foreground mb-6">
            Add a sync target to automatically backup and synchronize your data.
          </p>
          <Button onClick={() => setShowAddDialog(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Your First Target
          </Button>
        </Card>
      )}

      {/* Add/Edit Target Form */}
      {(showAddDialog || editingTarget) && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">
            {editingTarget ? 'Edit Sync Target' : 'Add Sync Target'}
          </h3>
          
          <div className="space-y-4">
            <div>
              <Label htmlFor="target-name">Name</Label>
              <Input
                id="target-name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="My Sync Target"
              />
            </div>
            
            <div>
              <Label htmlFor="target-type">Type</Label>
              <select 
                id="target-type"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                value={formData.type} 
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  type: e.target.value as SyncTarget['type'],
                  config: {} // Reset config when type changes
                }))}
              >
                {targetTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
            
            {renderConfigForm(formData.type)}
            
            <div className="flex justify-end space-x-2 pt-4">
              <Button 
                variant="outline" 
                onClick={() => {
                  setShowAddDialog(false);
                  setEditingTarget(null);
                  setFormData({ name: '', type: 'local', config: {} });
                }}
              >
                Cancel
              </Button>
              <Button 
                onClick={handleSave}
                disabled={!formData.name}
              >
                {editingTarget ? 'Update Target' : 'Add Target'}
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
