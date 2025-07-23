/**
 * Auto-updater System for Lexicon
 * Handles automatic application updates with user consent and fallback mechanisms
 */

import { invoke } from '@tauri-apps/api/core';
import { check as checkUpdater } from '@tauri-apps/plugin-updater';
import { relaunch } from '@tauri-apps/plugin-process';

export interface UpdateInfo {
  version: string;
  currentVersion: string;
  date?: string;
  body?: string;
  signature?: string;
  url: string;
  available: boolean;
}

export interface UpdateConfig {
  autoCheck: boolean;
  autoInstall: boolean;
  checkInterval: number; // in milliseconds
  allowPrerelease: boolean;
  notifyUser: boolean;
  updateChannel: 'stable' | 'beta' | 'alpha';
}

export interface UpdateProgress {
  chunkLength: number;
  contentLength?: number;
  downloaded: number;
  percentage: number;
}

type UpdateEventCallback = (event: {
  type: 'checking' | 'available' | 'downloaded' | 'installed' | 'error';
  data?: any;
}) => void;

class AutoUpdater {
  private config: UpdateConfig;
  private isChecking: boolean = false;
  private isDownloading: boolean = false;
  private isInstalling: boolean = false;
  private lastCheckTime: Date | null = null;
  private checkInterval: NodeJS.Timeout | null = null;
  private eventCallbacks: UpdateEventCallback[] = [];
  private progressCallback: ((progress: UpdateProgress) => void) | null = null;

  constructor() {
    this.config = this.getDefaultConfig();
    this.loadConfig();
    this.setupEventListeners();
  }

  private getDefaultConfig(): UpdateConfig {
    return {
      autoCheck: true,
      autoInstall: false,
      checkInterval: 6 * 60 * 60 * 1000, // 6 hours
      allowPrerelease: false,
      notifyUser: true,
      updateChannel: 'stable'
    };
  }

  private async loadConfig(): Promise<void> {
    try {
      const stored = localStorage.getItem('lexicon_update_config');
      if (stored) {
        this.config = { ...this.config, ...JSON.parse(stored) };
      }
    } catch (error) {
      console.warn('Failed to load update config:', error);
    }
  }

  private async saveConfig(): Promise<void> {
    try {
      localStorage.setItem('lexicon_update_config', JSON.stringify(this.config));
    } catch (error) {
      console.warn('Failed to save update config:', error);
    }
  }

  private setupEventListeners(): void {
    // Listen for updater events
    // Note: onUpdaterEvent not available in current plugin version
    /*
    onUpdaterEvent(({ error, status }) => {
      if (error) {
        this.notifyCallbacks({ type: 'error', data: error });
        console.error('Updater error:', error);
        return;
      }

      switch (status) {
        case 'PENDING':
          this.notifyCallbacks({ type: 'checking' });
          break;
        case 'ERROR':
          this.notifyCallbacks({ type: 'error', data: 'Update check failed' });
          break;
        case 'DONE':
          this.notifyCallbacks({ type: 'downloaded' });
          break;
        case 'UPTODATE':
          console.log('Application is up to date');
          break;
      }
    });
    */
  }

  public async initialize(): Promise<void> {
    console.log('Initializing auto-updater...');
    
    if (this.config.autoCheck) {
      // Check for updates on startup (after a delay)
      setTimeout(() => {
        this.checkForUpdates();
      }, 10000); // 10 second delay on startup

      // Setup periodic checks
      this.startPeriodicChecks();
    }
  }

  public async checkForUpdates(manual: boolean = false): Promise<UpdateInfo | null> {
    if (this.isChecking) {
      console.log('Update check already in progress');
      return null;
    }

    try {
      this.isChecking = true;
      this.lastCheckTime = new Date();
      
      if (!manual) {
        this.notifyCallbacks({ type: 'checking' });
      }

      const update = await checkUpdater();
      
      if (update) {
        const updateInfo: UpdateInfo = {
          version: update.version,
          currentVersion: update.currentVersion,
          date: update.date,
          body: update.body,
          url: '', // Not directly available in Tauri updater
          available: true
        };

        this.notifyCallbacks({ type: 'available', data: updateInfo });

        if (this.config.autoInstall && !manual) {
          await this.downloadAndInstallUpdate(updateInfo);
        }

        return updateInfo;
      } else {
        console.log('No updates available');
        return {
          version: '',
          currentVersion: '',
          available: false,
          url: ''
        };
      }
    } catch (error) {
      console.error('Failed to check for updates:', error);
      this.notifyCallbacks({ type: 'error', data: error });
      return null;
    } finally {
      this.isChecking = false;
    }
  }

  public async downloadAndInstallUpdate(updateInfo: UpdateInfo): Promise<boolean> {
    if (this.isDownloading || this.isInstalling) {
      console.log('Update already in progress');
      return false;
    }

    try {
      this.isDownloading = true;
      
      // Start download and installation
      console.log(`Downloading update ${updateInfo.version}...`);
      
      // Note: installUpdate not available in current plugin version
      // await installUpdate();
      console.log('Update installation would happen here');
      return false;
      
      /*
      this.isDownloading = false;
      this.isInstalling = true;
      
      this.notifyCallbacks({ type: 'installed', data: updateInfo });
      
      // Prompt user for restart
      if (this.config.notifyUser) {
        const shouldRestart = confirm(
          `Update ${updateInfo.version} has been installed. Would you like to restart the application now?`
        );
        
        if (shouldRestart) {
          await this.restartApplication();
        }
      } else if (this.config.autoInstall) {
        // Auto-restart after a delay
        setTimeout(async () => {
          await this.restartApplication();
        }, 5000);
      }
      
      return true;
      */
    } catch (error) {
      console.error('Failed to download/install update:', error);
      this.notifyCallbacks({ type: 'error', data: error });
      return false;
    } finally {
      this.isDownloading = false;
      this.isInstalling = false;
    }
  }

  public async restartApplication(): Promise<void> {
    try {
      console.log('Restarting application...');
      await relaunch();
    } catch (error) {
      console.error('Failed to restart application:', error);
      // Fallback: show message to user
      alert('Please manually restart the application to complete the update.');
    }
  }

  public getConfig(): UpdateConfig {
    return { ...this.config };
  }

  public async updateConfig(newConfig: Partial<UpdateConfig>): Promise<void> {
    this.config = { ...this.config, ...newConfig };
    await this.saveConfig();

    // Restart periodic checks if interval changed
    if ('checkInterval' in newConfig || 'autoCheck' in newConfig) {
      this.stopPeriodicChecks();
      if (this.config.autoCheck) {
        this.startPeriodicChecks();
      }
    }
  }

  public addEventListener(callback: UpdateEventCallback): () => void {
    this.eventCallbacks.push(callback);
    
    // Return unsubscribe function
    return () => {
      const index = this.eventCallbacks.indexOf(callback);
      if (index > -1) {
        this.eventCallbacks.splice(index, 1);
      }
    };
  }

  public setProgressCallback(callback: (progress: UpdateProgress) => void): void {
    this.progressCallback = callback;
  }

  private notifyCallbacks(event: { type: 'checking' | 'available' | 'downloaded' | 'installed' | 'error'; data?: any }): void {
    this.eventCallbacks.forEach(callback => {
      try {
        callback(event);
      } catch (error) {
        console.error('Error in update event callback:', error);
      }
    });
  }

  private startPeriodicChecks(): void {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
    }

    this.checkInterval = setInterval(() => {
      this.checkForUpdates();
    }, this.config.checkInterval);
  }

  private stopPeriodicChecks(): void {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
  }

  public getLastCheckTime(): Date | null {
    return this.lastCheckTime;
  }

  public isUpdateInProgress(): boolean {
    return this.isChecking || this.isDownloading || this.isInstalling;
  }

  public getStatus(): {
    checking: boolean;
    downloading: boolean;
    installing: boolean;
    lastCheck: Date | null;
  } {
    return {
      checking: this.isChecking,
      downloading: this.isDownloading,
      installing: this.isInstalling,
      lastCheck: this.lastCheckTime
    };
  }

  // Manual update methods for testing
  public async forceCheck(): Promise<UpdateInfo | null> {
    return this.checkForUpdates(true);
  }

  public async skipVersion(version: string): Promise<void> {
    try {
      const skippedVersions = JSON.parse(
        localStorage.getItem('lexicon_skipped_versions') || '[]'
      );
      
      if (!skippedVersions.includes(version)) {
        skippedVersions.push(version);
        localStorage.setItem('lexicon_skipped_versions', JSON.stringify(skippedVersions));
      }
    } catch (error) {
      console.warn('Failed to skip version:', error);
    }
  }

  public async clearSkippedVersions(): Promise<void> {
    localStorage.removeItem('lexicon_skipped_versions');
  }

  private isVersionSkipped(version: string): boolean {
    try {
      const skippedVersions = JSON.parse(
        localStorage.getItem('lexicon_skipped_versions') || '[]'
      );
      return skippedVersions.includes(version);
    } catch {
      return false;
    }
  }

  // Cleanup method
  public destroy(): void {
    this.stopPeriodicChecks();
    this.eventCallbacks = [];
    this.progressCallback = null;
  }
}

// Create global instance
export const autoUpdater = new AutoUpdater();

// Convenience functions
export const checkForUpdates = (manual?: boolean) => autoUpdater.checkForUpdates(manual);
export const downloadAndInstall = (updateInfo: UpdateInfo) => autoUpdater.downloadAndInstallUpdate(updateInfo);
export const getUpdateConfig = () => autoUpdater.getConfig();
export const updateConfig = (config: Partial<UpdateConfig>) => autoUpdater.updateConfig(config);
export const addUpdateListener = (callback: UpdateEventCallback) => autoUpdater.addEventListener(callback);
export const getUpdateStatus = () => autoUpdater.getStatus();
export const forceUpdateCheck = () => autoUpdater.forceCheck();
export const skipVersion = (version: string) => autoUpdater.skipVersion(version);
export const restartApp = () => autoUpdater.restartApplication();

// Initialize on module load (in production)
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
  autoUpdater.initialize();
}
