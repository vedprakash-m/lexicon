/**
 * Comprehensive Security System for Lexicon
 * Handles data encryption, authentication, authorization, and security auditing
 */

import { invoke } from '@tauri-apps/api/core';
import { errorTracker } from './errorTracking';

export interface SecurityConfig {
  encryptionEnabled: boolean;
  encryptionAlgorithm: 'AES-256-GCM' | 'ChaCha20-Poly1305';
  keyRotationInterval: number; // hours
  sessionTimeout: number; // minutes
  maxLoginAttempts: number;
  lockoutDuration: number; // minutes
  auditLogging: boolean;
  dataIntegrityChecks: boolean;
  secureTransport: boolean;
}

export interface UserSession {
  id: string;
  userId: string;
  username: string;
  email?: string;
  role: 'admin' | 'user' | 'readonly';
  permissions: string[];
  createdAt: Date;
  expiresAt: Date;
  lastActivity: Date;
  ipAddress?: string;
  userAgent?: string;
}

export interface SecurityAuditEvent {
  id: string;
  type: 'authentication' | 'authorization' | 'data_access' | 'configuration' | 'security_violation';
  severity: 'low' | 'medium' | 'high' | 'critical';
  userId?: string;
  username?: string;
  action: string;
  resource?: string;
  outcome: 'success' | 'failure' | 'warning';
  details: Record<string, any>;
  timestamp: Date;
  ipAddress?: string;
  userAgent?: string;
}

export interface EncryptionKey {
  id: string;
  algorithm: string;
  keyData: string; // Base64 encoded
  createdAt: Date;
  expiresAt?: Date;
  active: boolean;
}

export interface DataIntegrityCheck {
  resource: string;
  hash: string;
  algorithm: 'SHA-256' | 'SHA-512';
  timestamp: Date;
  verified: boolean;
}

class ComprehensiveSecurityManager {
  private config: SecurityConfig;
  private currentSession: UserSession | null = null;
  private encryptionKeys: Map<string, EncryptionKey> = new Map();
  private auditLog: SecurityAuditEvent[] = [];
  private loginAttempts: Map<string, { count: number; lastAttempt: Date }> = new Map();
  private keyRotationInterval: NodeJS.Timeout | null = null;

  constructor() {
    this.config = this.getDefaultConfig();
    this.loadConfig();
    this.initialize();
  }

  private getDefaultConfig(): SecurityConfig {
    return {
      encryptionEnabled: true,
      encryptionAlgorithm: 'AES-256-GCM',
      keyRotationInterval: 24, // 24 hours
      sessionTimeout: 60, // 60 minutes
      maxLoginAttempts: 5,
      lockoutDuration: 30, // 30 minutes
      auditLogging: true,
      dataIntegrityChecks: true,
      secureTransport: true
    };
  }

  private async loadConfig(): Promise<void> {
    try {
      const stored = localStorage.getItem('lexicon_security_config');
      if (stored) {
        this.config = { ...this.config, ...JSON.parse(stored) };
      }
    } catch (error) {
      console.warn('Failed to load security config:', error);
      this.logSecurityEvent('configuration', 'medium', 'config_load_failed', '', 'warning', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }

  private async saveConfig(): Promise<void> {
    try {
      localStorage.setItem('lexicon_security_config', JSON.stringify(this.config));
    } catch (error) {
      console.warn('Failed to save security config:', error);
    }
  }

  private async initialize(): Promise<void> {
    console.log('Initializing comprehensive security manager...');
    
    try {
      // Initialize encryption keys
      await this.initializeEncryptionKeys();
      
      // Start key rotation if enabled
      if (this.config.encryptionEnabled) {
        this.startKeyRotation();
      }
      
      // Load existing session if available
      await this.loadStoredSession();
      
      // Set up session timeout monitoring
      this.setupSessionMonitoring();
      
      this.logSecurityEvent('configuration', 'low', 'security_manager_initialized', '', 'success', {
        encryptionEnabled: this.config.encryptionEnabled,
        auditLogging: this.config.auditLogging
      });
    } catch (error) {
      console.error('Failed to initialize security manager:', error);
      this.logSecurityEvent('configuration', 'high', 'security_manager_init_failed', '', 'failure', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }

  private async initializeEncryptionKeys(): Promise<void> {
    try {
      // Try to get keys from secure backend
      const keys = await invoke<EncryptionKey[]>('get_encryption_keys');
      keys.forEach(key => this.encryptionKeys.set(key.id, key));
      
      // If no keys exist, generate initial key
      if (this.encryptionKeys.size === 0) {
        await this.generateNewEncryptionKey();
      }
    } catch (error) {
      // Fallback: generate key locally
      console.warn('Backend encryption keys not available, using local key generation');
      await this.generateLocalEncryptionKey();
    }
  }

  private async generateNewEncryptionKey(): Promise<string> {
    try {
      const keyId = await invoke<string>('generate_encryption_key', {
        algorithm: this.config.encryptionAlgorithm
      });
      
      const key: EncryptionKey = {
        id: keyId,
        algorithm: this.config.encryptionAlgorithm,
        keyData: '', // Backend handles the actual key data
        createdAt: new Date(),
        active: true
      };
      
      this.encryptionKeys.set(keyId, key);
      
      this.logSecurityEvent('configuration', 'medium', 'encryption_key_generated', '', 'success', {
        keyId,
        algorithm: this.config.encryptionAlgorithm
      });
      
      return keyId;
    } catch (error) {
      console.error('Failed to generate encryption key:', error);
      throw error;
    }
  }

  private async generateLocalEncryptionKey(): Promise<string> {
    // Fallback local key generation for development/testing
    const keyId = `local_key_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const key: EncryptionKey = {
      id: keyId,
      algorithm: this.config.encryptionAlgorithm,
      keyData: btoa(crypto.getRandomValues(new Uint8Array(32)).join(',')), // Dummy key for demo
      createdAt: new Date(),
      active: true
    };
    
    this.encryptionKeys.set(keyId, key);
    
    this.logSecurityEvent('configuration', 'low', 'local_encryption_key_generated', '', 'success', {
      keyId,
      note: 'Development/demo key - not for production use'
    });
    
    return keyId;
  }

  private startKeyRotation(): void {
    if (this.keyRotationInterval) {
      clearInterval(this.keyRotationInterval);
    }
    
    const intervalMs = this.config.keyRotationInterval * 60 * 60 * 1000;
    this.keyRotationInterval = setInterval(async () => {
      try {
        await this.rotateEncryptionKeys();
      } catch (error) {
        console.error('Key rotation failed:', error);
        this.logSecurityEvent('configuration', 'high', 'key_rotation_failed', '', 'failure', {
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }, intervalMs);
  }

  private async rotateEncryptionKeys(): Promise<void> {
    console.log('Rotating encryption keys...');
    
    try {
      // Generate new key
      const newKeyId = await this.generateNewEncryptionKey();
      
      // Mark old keys as inactive
      this.encryptionKeys.forEach(key => {
        if (key.id !== newKeyId) {
          key.active = false;
        }
      });
      
      // Notify backend about key rotation
      await invoke('rotate_encryption_key');
      
      this.logSecurityEvent('configuration', 'medium', 'encryption_keys_rotated', '', 'success', {
        newKeyId,
        totalKeys: this.encryptionKeys.size
      });
    } catch (error) {
      console.error('Failed to rotate encryption keys:', error);
      throw error;
    }
  }

  public async authenticateUser(username: string, password: string): Promise<UserSession> {
    const startTime = Date.now();
    
    try {
      // Check for account lockout
      const attemptKey = username.toLowerCase();
      const attempts = this.loginAttempts.get(attemptKey);
      
      if (attempts && attempts.count >= this.config.maxLoginAttempts) {
        const lockoutEnd = new Date(attempts.lastAttempt.getTime() + this.config.lockoutDuration * 60 * 1000);
        if (new Date() < lockoutEnd) {
          this.logSecurityEvent('authentication', 'medium', 'login_attempt_blocked', username, 'failure', {
            reason: 'account_locked',
            lockoutEnd: lockoutEnd.toISOString(),
            attemptCount: attempts.count
          });
          throw new Error('Account temporarily locked due to too many failed attempts');
        } else {
          // Reset attempts after lockout period
          this.loginAttempts.delete(attemptKey);
        }
      }
      
      // Attempt authentication with backend
      const authResult = await invoke<{
        success: boolean;
        session?: any;
        user?: any;
        error?: string;
      }>('authenticate_user', { username, password });
      
      if (!authResult.success) {
        // Record failed attempt
        const currentAttempts = this.loginAttempts.get(attemptKey) || { count: 0, lastAttempt: new Date() };
        currentAttempts.count += 1;
        currentAttempts.lastAttempt = new Date();
        this.loginAttempts.set(attemptKey, currentAttempts);
        
        this.logSecurityEvent('authentication', 'medium', 'login_failed', username, 'failure', {
          reason: authResult.error || 'invalid_credentials',
          attemptCount: currentAttempts.count,
          responseTime: Date.now() - startTime
        });
        
        throw new Error(authResult.error || 'Authentication failed');
      }
      
      // Clear failed attempts on successful login
      this.loginAttempts.delete(attemptKey);
      
      // Create session
      const session: UserSession = {
        id: authResult.session?.id || this.generateSessionId(),
        userId: authResult.user?.id || username,
        username: authResult.user?.username || username,
        email: authResult.user?.email,
        role: authResult.user?.role || 'user',
        permissions: authResult.user?.permissions || ['read', 'write'],
        createdAt: new Date(),
        expiresAt: new Date(Date.now() + this.config.sessionTimeout * 60 * 1000),
        lastActivity: new Date(),
        ipAddress: await this.getClientIPAddress(),
        userAgent: navigator.userAgent
      };
      
      this.currentSession = session;
      await this.storeSession(session);
      
      this.logSecurityEvent('authentication', 'low', 'login_successful', username, 'success', {
        sessionId: session.id,
        role: session.role,
        responseTime: Date.now() - startTime
      });
      
      return session;
    } catch (error) {
      errorTracker.captureError(error, {
        component: 'SecurityManager',
        action: 'authenticateUser',
        metadata: { username }
      });
      throw error;
    }
  }

  public async logout(): Promise<void> {
    if (!this.currentSession) {
      return;
    }
    
    const sessionId = this.currentSession.id;
    const username = this.currentSession.username;
    
    try {
      // Invalidate session on backend
      await invoke('invalidate_session', { sessionId });
      
      // Clear local session
      this.currentSession = null;
      localStorage.removeItem('lexicon_user_session');
      
      this.logSecurityEvent('authentication', 'low', 'logout_successful', username, 'success', {
        sessionId
      });
    } catch (error) {
      console.error('Failed to logout properly:', error);
      this.logSecurityEvent('authentication', 'medium', 'logout_error', username, 'warning', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }

  public async encryptData(data: string): Promise<string> {
    if (!this.config.encryptionEnabled) {
      return data;
    }
    
    try {
      const activeKey = Array.from(this.encryptionKeys.values()).find(key => key.active);
      if (!activeKey) {
        throw new Error('No active encryption key available');
      }
      
      const encrypted = await invoke<string>('encrypt_data', {
        data,
        keyId: activeKey.id
      });
      
      this.logSecurityEvent('data_access', 'low', 'data_encrypted', this.currentSession?.username, 'success', {
        keyId: activeKey.id,
        dataSize: data.length
      });
      
      return encrypted;
    } catch (error) {
      this.logSecurityEvent('data_access', 'high', 'encryption_failed', this.currentSession?.username, 'failure', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  }

  public async decryptData(encryptedData: string): Promise<string> {
    if (!this.config.encryptionEnabled) {
      return encryptedData;
    }
    
    try {
      const decrypted = await invoke<string>('decrypt_data', {
        encryptedData
      });
      
      this.logSecurityEvent('data_access', 'low', 'data_decrypted', this.currentSession?.username, 'success', {
        dataSize: encryptedData.length
      });
      
      return decrypted;
    } catch (error) {
      this.logSecurityEvent('data_access', 'high', 'decryption_failed', this.currentSession?.username, 'failure', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  }

  public checkPermission(permission: string): boolean {
    if (!this.currentSession) {
      this.logSecurityEvent('authorization', 'medium', 'permission_check_no_session', '', 'failure', {
        requestedPermission: permission
      });
      return false;
    }
    
    const hasPermission = this.currentSession.permissions.includes(permission) || 
                         this.currentSession.role === 'admin';
    
    this.logSecurityEvent('authorization', 'low', 'permission_checked', this.currentSession.username, 
      hasPermission ? 'success' : 'failure', {
        requestedPermission: permission,
        userPermissions: this.currentSession.permissions,
        role: this.currentSession.role
      });
    
    return hasPermission;
  }

  public async verifyDataIntegrity(resource: string, data: string): Promise<boolean> {
    if (!this.config.dataIntegrityChecks) {
      return true;
    }
    
    try {
      const hash = await this.calculateHash(data, 'SHA-256');
      const result = await invoke<boolean>('verify_data_integrity', {
        resource,
        hash
      });
      
      this.logSecurityEvent('data_access', 'low', 'integrity_check', this.currentSession?.username, 
        result ? 'success' : 'failure', {
          resource,
          hash: hash.substring(0, 16) + '...' // Log only partial hash for security
        });
      
      return result;
    } catch (error) {
      this.logSecurityEvent('data_access', 'high', 'integrity_check_failed', this.currentSession?.username, 'failure', {
        resource,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return false;
    }
  }

  private async calculateHash(data: string, algorithm: 'SHA-256' | 'SHA-512'): Promise<string> {
    const encoder = new TextEncoder();
    const dataBuffer = encoder.encode(data);
    
    const hashAlgorithm = algorithm === 'SHA-256' ? 'SHA-256' : 'SHA-512';
    const hashBuffer = await crypto.subtle.digest(hashAlgorithm, dataBuffer);
    
    return Array.from(new Uint8Array(hashBuffer))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 16)}`;
  }

  private async getClientIPAddress(): Promise<string | undefined> {
    // In a Tauri app, we can't get the real IP, so return undefined
    return undefined;
  }

  private async storeSession(session: UserSession): Promise<void> {
    try {
      const sessionData = {
        ...session,
        createdAt: session.createdAt.toISOString(),
        expiresAt: session.expiresAt.toISOString(),
        lastActivity: session.lastActivity.toISOString()
      };
      
      const encryptedSession = await this.encryptData(JSON.stringify(sessionData));
      localStorage.setItem('lexicon_user_session', encryptedSession);
    } catch (error) {
      console.warn('Failed to store session:', error);
    }
  }

  private async loadStoredSession(): Promise<void> {
    try {
      const stored = localStorage.getItem('lexicon_user_session');
      if (!stored) return;
      
      const decryptedSession = await this.decryptData(stored);
      const sessionData = JSON.parse(decryptedSession);
      
      const session: UserSession = {
        ...sessionData,
        createdAt: new Date(sessionData.createdAt),
        expiresAt: new Date(sessionData.expiresAt),
        lastActivity: new Date(sessionData.lastActivity)
      };
      
      // Check if session is still valid
      if (session.expiresAt > new Date()) {
        this.currentSession = session;
        this.logSecurityEvent('authentication', 'low', 'session_restored', session.username, 'success', {
          sessionId: session.id
        });
      } else {
        localStorage.removeItem('lexicon_user_session');
        this.logSecurityEvent('authentication', 'low', 'session_expired', session.username, 'warning', {
          sessionId: session.id
        });
      }
    } catch (error) {
      console.warn('Failed to load stored session:', error);
      localStorage.removeItem('lexicon_user_session');
    }
  }

  private setupSessionMonitoring(): void {
    setInterval(() => {
      if (this.currentSession) {
        // Update last activity
        this.currentSession.lastActivity = new Date();
        this.storeSession(this.currentSession);
        
        // Check for session expiration
        if (this.currentSession.expiresAt <= new Date()) {
          this.logSecurityEvent('authentication', 'low', 'session_expired', this.currentSession.username, 'warning', {
            sessionId: this.currentSession.id
          });
          this.logout();
        }
      }
    }, 60000); // Check every minute
  }

  private logSecurityEvent(
    type: SecurityAuditEvent['type'],
    severity: SecurityAuditEvent['severity'],
    action: string,
    username: string,
    outcome: SecurityAuditEvent['outcome'],
    details: Record<string, any>
  ): void {
    if (!this.config.auditLogging) return;
    
    const event: SecurityAuditEvent = {
      id: `audit_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      severity,
      userId: this.currentSession?.userId,
      username: username || this.currentSession?.username,
      action,
      outcome,
      details,
      timestamp: new Date(),
      ipAddress: this.currentSession?.ipAddress,
      userAgent: this.currentSession?.userAgent
    };
    
    this.auditLog.push(event);
    
    // Keep only last 1000 events in memory
    if (this.auditLog.length > 1000) {
      this.auditLog = this.auditLog.slice(-1000);
    }
    
    // Try to send to backend for persistent storage
    this.sendAuditEventToBackend(event).catch(error => {
      console.warn('Failed to send audit event to backend:', error);
    });
  }

  private async sendAuditEventToBackend(event: SecurityAuditEvent): Promise<void> {
    try {
      await invoke('log_security_event', { event });
    } catch (error) {
      // Store locally if backend is unavailable
      const localAuditLog = JSON.parse(localStorage.getItem('lexicon_security_audit') || '[]');
      localAuditLog.push(event);
      
      // Keep only last 100 events in localStorage
      if (localAuditLog.length > 100) {
        localAuditLog.splice(0, localAuditLog.length - 100);
      }
      
      localStorage.setItem('lexicon_security_audit', JSON.stringify(localAuditLog));
    }
  }

  // Public API methods
  public getCurrentSession(): UserSession | null {
    return this.currentSession;
  }

  public getSecurityAuditLog(): SecurityAuditEvent[] {
    return [...this.auditLog];
  }

  public getConfig(): SecurityConfig {
    return { ...this.config };
  }

  public async updateConfig(newConfig: Partial<SecurityConfig>): Promise<void> {
    const oldConfig = { ...this.config };
    this.config = { ...this.config, ...newConfig };
    await this.saveConfig();
    
    // Handle configuration changes
    if (newConfig.encryptionEnabled !== oldConfig.encryptionEnabled) {
      if (newConfig.encryptionEnabled) {
        await this.initializeEncryptionKeys();
        this.startKeyRotation();
      } else if (this.keyRotationInterval) {
        clearInterval(this.keyRotationInterval);
        this.keyRotationInterval = null;
      }
    }
    
    if (newConfig.keyRotationInterval !== oldConfig.keyRotationInterval && this.config.encryptionEnabled) {
      this.startKeyRotation();
    }
    
    this.logSecurityEvent('configuration', 'medium', 'security_config_updated', '', 'success', {
      changes: Object.keys(newConfig)
    });
  }

  public isAuthenticated(): boolean {
    return this.currentSession !== null && this.currentSession.expiresAt > new Date();
  }

  public destroy(): void {
    if (this.keyRotationInterval) {
      clearInterval(this.keyRotationInterval);
      this.keyRotationInterval = null;
    }
    
    this.logout();
    this.encryptionKeys.clear();
    this.auditLog = [];
    this.loginAttempts.clear();
  }
}

// Global security manager instance
export const securityManager = new ComprehensiveSecurityManager();

// Convenience functions
export const authenticate = (username: string, password: string) => 
  securityManager.authenticateUser(username, password);
export const logout = () => securityManager.logout();
export const encryptData = (data: string) => securityManager.encryptData(data);
export const decryptData = (data: string) => securityManager.decryptData(data);
export const checkPermission = (permission: string) => securityManager.checkPermission(permission);
export const verifyDataIntegrity = (resource: string, data: string) => 
  securityManager.verifyDataIntegrity(resource, data);
export const getCurrentSession = () => securityManager.getCurrentSession();
export const getSecurityAuditLog = () => securityManager.getSecurityAuditLog();
export const updateSecurityConfig = (config: Partial<SecurityConfig>) => 
  securityManager.updateConfig(config);
export const isAuthenticated = () => securityManager.isAuthenticated();
