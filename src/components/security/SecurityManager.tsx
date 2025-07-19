import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Shield, Key, Lock, Eye, AlertTriangle, Clock, FileText, Hash } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface SecurityStats {
  total_audit_events: number;
  recent_events_24h: number;
  active_encryption_keys: number;
  active_sessions: number;
  last_key_rotation?: string;
}

interface AuditLogEntry {
  id: string;
  timestamp: string;
  event: any;
  ip_address?: string;
  user_agent?: string;
  session_id?: string;
}

interface EncryptionKeyRequest {
  key_id: string;
}

interface EncryptDataRequest {
  data: number[];
  key_id: string;
}

interface CheckPermissionRequest {
  user_id: string;
  resource: string;
  permission: string;
}

interface CreateSessionRequest {
  user_id: string;
}

interface HashDataRequest {
  data: number[];
}

interface VerifyIntegrityRequest {
  data: number[];
  expected_hash: string;
}

export const SecurityManager: React.FC = () => {
  const [stats, setStats] = useState<SecurityStats | null>(null);
  const [auditLog, setAuditLog] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [keyId, setKeyId] = useState('');
  const [encryptionText, setEncryptionText] = useState('');
  const [encryptedData, setEncryptedData] = useState<number[]>([]);
  const [userId, setUserId] = useState('');
  const [resource, setResource] = useState('');
  const [permission, setPermission] = useState('read');
  const [hashText, setHashText] = useState('');
  const [expectedHash, setExpectedHash] = useState('');
  const [verificationResult, setVerificationResult] = useState<boolean | null>(null);
  
  const { toast } = useToast();

  useEffect(() => {
    loadSecurityStats();
    loadAuditLog();
  }, []);

  const loadSecurityStats = async () => {
    try {
      const stats = await invoke<SecurityStats>('get_security_statistics');
      setStats(stats);
    } catch (error) {
      console.error('Failed to load security stats:', error);
      toast({
        title: "Error",
        description: "Failed to load security statistics",
        variant: "destructive"
      });
    }
  };

  const loadAuditLog = async () => {
    try {
      const response = await invoke<{ entries: AuditLogEntry[]; success: boolean; message: string }>('get_security_audit_log', {
        request: { limit: 50 }
      });
      if (response.success) {
        setAuditLog(response.entries);
      } else {
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('Failed to load audit log:', error);
      toast({
        title: "Error",
        description: "Failed to load audit log",
        variant: "destructive"
      });
    }
  };

  const generateEncryptionKey = async () => {
    if (!keyId.trim()) {
      toast({
        title: "Error",
        description: "Please enter a key ID",
        variant: "destructive"
      });
      return;
    }

    try {
      setLoading(true);
      const response = await invoke<{ key_id: string; success: boolean; message: string }>('generate_encryption_key', {
        request: { key_id: keyId } as EncryptionKeyRequest
      });
      
      if (response.success) {
        toast({
          title: "Success",
          description: `Encryption key '${response.key_id}' generated successfully`
        });
        setKeyId('');
        loadSecurityStats();
      } else {
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('Failed to generate key:', error);
      toast({
        title: "Error",
        description: "Failed to generate encryption key",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const rotateEncryptionKey = async () => {
    if (!keyId.trim()) {
      toast({
        title: "Error",
        description: "Please enter a key ID to rotate",
        variant: "destructive"
      });
      return;
    }

    try {
      setLoading(true);
      const response = await invoke<{ key_id: string; success: boolean; message: string }>('rotate_encryption_key', {
        request: { key_id: keyId } as EncryptionKeyRequest
      });
      
      if (response.success) {
        toast({
          title: "Success",
          description: `Key rotated successfully. New key ID: ${response.key_id}`
        });
        setKeyId('');
        loadSecurityStats();
      } else {
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('Failed to rotate key:', error);
      toast({
        title: "Error",
        description: "Failed to rotate encryption key",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const encryptData = async () => {
    if (!encryptionText.trim() || !keyId.trim()) {
      toast({
        title: "Error",
        description: "Please enter both text to encrypt and key ID",
        variant: "destructive"
      });
      return;
    }

    try {
      setLoading(true);
      const textBytes = Array.from(new TextEncoder().encode(encryptionText));
      const response = await invoke<{ encrypted_data: number[]; success: boolean; message: string }>('encrypt_data', {
        request: { data: textBytes, key_id: keyId } as EncryptDataRequest
      });
      
      if (response.success) {
        setEncryptedData(response.encrypted_data);
        toast({
          title: "Success",
          description: "Data encrypted successfully"
        });
      } else {
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('Failed to encrypt data:', error);
      toast({
        title: "Error",
        description: "Failed to encrypt data",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const decryptData = async () => {
    if (encryptedData.length === 0 || !keyId.trim()) {
      toast({
        title: "Error",
        description: "Please encrypt some data first and ensure key ID is provided",
        variant: "destructive"
      });
      return;
    }

    try {
      setLoading(true);
      const response = await invoke<{ decrypted_data: number[]; success: boolean; message: string }>('decrypt_data', {
        request: { encrypted_data: encryptedData, key_id: keyId }
      });
      
      if (response.success) {
        const decryptedText = new TextDecoder().decode(new Uint8Array(response.decrypted_data));
        toast({
          title: "Success",
          description: `Decrypted text: ${decryptedText}`
        });
      } else {
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('Failed to decrypt data:', error);
      toast({
        title: "Error",
        description: "Failed to decrypt data",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const checkPermission = async () => {
    if (!userId.trim() || !resource.trim()) {
      toast({
        title: "Error",
        description: "Please enter both user ID and resource",
        variant: "destructive"
      });
      return;
    }

    try {
      setLoading(true);
      const response = await invoke<{ has_permission: boolean; success: boolean; message: string }>('check_user_permission', {
        request: { user_id: userId, resource, permission } as CheckPermissionRequest
      });
      
      if (response.success) {
        toast({
          title: "Permission Check",
          description: `User ${userId} ${response.has_permission ? 'has' : 'does not have'} ${permission} permission for ${resource}`,
          variant: response.has_permission ? "default" : "destructive"
        });
      } else {
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('Failed to check permission:', error);
      toast({
        title: "Error",
        description: "Failed to check permission",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const createSession = async () => {
    if (!userId.trim()) {
      toast({
        title: "Error",
        description: "Please enter a user ID",
        variant: "destructive"
      });
      return;
    }

    try {
      setLoading(true);
      const response = await invoke<{ session_id: string; success: boolean; message: string }>('create_user_session', {
        request: { user_id: userId } as CreateSessionRequest
      });
      
      if (response.success) {
        toast({
          title: "Success",
          description: `Session created: ${response.session_id}`
        });
        loadSecurityStats();
      } else {
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('Failed to create session:', error);
      toast({
        title: "Error",
        description: "Failed to create session",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const hashData = async () => {
    if (!hashText.trim()) {
      toast({
        title: "Error",
        description: "Please enter text to hash",
        variant: "destructive"
      });
      return;
    }

    try {
      setLoading(true);
      const textBytes = Array.from(new TextEncoder().encode(hashText));
      const response = await invoke<{ hash: string; success: boolean; message: string }>('hash_data', {
        request: { data: textBytes } as HashDataRequest
      });
      
      if (response.success) {
        setExpectedHash(response.hash);
        toast({
          title: "Success",
          description: `Hash: ${response.hash}`
        });
      } else {
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('Failed to hash data:', error);
      toast({
        title: "Error",
        description: "Failed to hash data",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const verifyIntegrity = async () => {
    if (!hashText.trim() || !expectedHash.trim()) {
      toast({
        title: "Error",
        description: "Please enter both text and expected hash",
        variant: "destructive"
      });
      return;
    }

    try {
      setLoading(true);
      const textBytes = Array.from(new TextEncoder().encode(hashText));
      const response = await invoke<{ is_valid: boolean; success: boolean; message: string }>('verify_data_integrity', {
        request: { data: textBytes, expected_hash: expectedHash } as VerifyIntegrityRequest
      });
      
      if (response.success) {
        setVerificationResult(response.is_valid);
        toast({
          title: "Verification Result",
          description: response.is_valid ? "Data integrity verified" : "Data integrity check failed",
          variant: response.is_valid ? "default" : "destructive"
        });
      } else {
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('Failed to verify integrity:', error);
      toast({
        title: "Error",
        description: "Failed to verify data integrity",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const formatEventType = (event: any) => {
    if (event.DataAccess) {
      return `Data Access: ${event.DataAccess.action} on ${event.DataAccess.resource}`;
    }
    if (event.EncryptionOperation) {
      return `Encryption: ${event.EncryptionOperation.operation} on ${event.EncryptionOperation.resource}`;
    }
    if (event.AuthenticationAttempt) {
      return `Auth: ${event.AuthenticationAttempt.success ? 'Success' : 'Failed'} for ${event.AuthenticationAttempt.user}`;
    }
    if (event.AccessDenied) {
      return `Access Denied: ${event.AccessDenied.resource} - ${event.AccessDenied.reason}`;
    }
    if (event.KeyRotation) {
      return `Key Rotation: ${event.KeyRotation.key_id}`;
    }
    if (event.SecurityViolation) {
      return `Security Violation: ${event.SecurityViolation.violation_type}`;
    }
    return 'Unknown Event';
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center gap-2 mb-6">
        <Shield className="h-8 w-8 text-blue-600" />
        <h1 className="text-3xl font-bold">Security Management</h1>
      </div>

      {/* Security Statistics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5" />
            Security Overview
          </CardTitle>
          <CardDescription>
            Current security status and statistics
          </CardDescription>
        </CardHeader>
        <CardContent>
          {stats ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold">{stats.total_audit_events}</div>
                <div className="text-sm text-gray-600">Total Events</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{stats.recent_events_24h}</div>
                <div className="text-sm text-gray-600">Recent Events</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{stats.active_encryption_keys}</div>
                <div className="text-sm text-gray-600">Active Keys</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{stats.active_sessions}</div>
                <div className="text-sm text-gray-600">Active Sessions</div>
              </div>
            </div>
          ) : (
            <div className="text-center py-4">Loading security statistics...</div>
          )}
        </CardContent>
      </Card>

      {/* Security Management Tabs */}
      <Tabs defaultValue="encryption" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="encryption">Encryption</TabsTrigger>
          <TabsTrigger value="access">Access Control</TabsTrigger>
          <TabsTrigger value="integrity">Data Integrity</TabsTrigger>
          <TabsTrigger value="audit">Audit Log</TabsTrigger>
        </TabsList>

        <TabsContent value="encryption" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                Encryption Key Management
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="keyId">Key ID</Label>
                  <Input
                    id="keyId"
                    value={keyId}
                    onChange={(e) => setKeyId(e.target.value)}
                    placeholder="Enter key identifier"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Actions</Label>
                  <div className="flex gap-2">
                    <Button onClick={generateEncryptionKey} disabled={loading}>
                      Generate Key
                    </Button>
                    <Button onClick={rotateEncryptionKey} disabled={loading} variant="outline">
                      Rotate Key
                    </Button>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="encryptionText">Text to Encrypt</Label>
                <Input
                  id="encryptionText"
                  value={encryptionText}
                  onChange={(e) => setEncryptionText(e.target.value)}
                  placeholder="Enter text to encrypt"
                />
              </div>

              <div className="flex gap-2">
                <Button onClick={encryptData} disabled={loading}>
                  <Lock className="h-4 w-4 mr-2" />
                  Encrypt
                </Button>
                <Button onClick={decryptData} disabled={loading} variant="outline">
                  Decrypt
                </Button>
              </div>

              {encryptedData.length > 0 && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    Encrypted data: {encryptedData.slice(0, 20).join(', ')}...
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="access" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Access Control
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="userId">User ID</Label>
                  <Input
                    id="userId"
                    value={userId}
                    onChange={(e) => setUserId(e.target.value)}
                    placeholder="Enter user identifier"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="resource">Resource</Label>
                  <Input
                    id="resource"
                    value={resource}
                    onChange={(e) => setResource(e.target.value)}
                    placeholder="Enter resource name"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="permission">Permission</Label>
                <select
                  id="permission"
                  value={permission}
                  onChange={(e) => setPermission(e.target.value)}
                  className="w-full p-2 border rounded"
                >
                  <option value="read">Read</option>
                  <option value="write">Write</option>
                  <option value="delete">Delete</option>
                  <option value="execute">Execute</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              <div className="flex gap-2">
                <Button onClick={checkPermission} disabled={loading}>
                  Check Permission
                </Button>
                <Button onClick={createSession} disabled={loading} variant="outline">
                  Create Session
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="integrity" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Hash className="h-5 w-5" />
                Data Integrity
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="hashText">Text to Hash</Label>
                <Input
                  id="hashText"
                  value={hashText}
                  onChange={(e) => setHashText(e.target.value)}
                  placeholder="Enter text to hash"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="expectedHash">Expected Hash</Label>
                <Input
                  id="expectedHash"
                  value={expectedHash}
                  onChange={(e) => setExpectedHash(e.target.value)}
                  placeholder="Hash will appear here"
                  readOnly
                />
              </div>

              <div className="flex gap-2">
                <Button onClick={hashData} disabled={loading}>
                  Generate Hash
                </Button>
                <Button onClick={verifyIntegrity} disabled={loading} variant="outline">
                  Verify Integrity
                </Button>
              </div>

              {verificationResult !== null && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    Verification: {verificationResult ? 'VALID' : 'INVALID'}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="audit" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Security Audit Log
              </CardTitle>
              <CardDescription>
                Recent security events and activities
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96">
                <div className="space-y-2">
                  {auditLog.length > 0 ? (
                    auditLog.map((entry) => (
                      <div key={entry.id} className="border rounded p-3 bg-gray-50">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="font-medium">{formatEventType(entry.event)}</div>
                            <div className="text-sm text-gray-600 flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {new Date(entry.timestamp).toLocaleString()}
                            </div>
                          </div>
                          <Badge variant="outline">{entry.id.substring(0, 8)}</Badge>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      No audit log entries found
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
