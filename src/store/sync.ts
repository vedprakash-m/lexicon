import { invoke } from '@tauri-apps/api/core';
import { useLexiconStore } from './index';
import { SourceText, Dataset } from './types';

// Tauri command interfaces matching the Rust backend
interface TauriSourceText {
  id: string;
  title: string;
  author?: string;
  language: string;
  source_type: string;
  file_path?: string;
  url?: string;
  metadata: any;
  processing_status: string;
  created_at: string;
  updated_at: string;
}

interface TauriDataset {
  id: string;
  name: string;
  description?: string;
  source_texts: string[];
  chunks: any[];
  metadata: any;
  status: string;
  created_at: string;
  updated_at: string;
}

// Conversion utilities between frontend and backend types
const convertSourceTextToTauri = (sourceText: SourceText): TauriSourceText => ({
  id: sourceText.id,
  title: sourceText.title,
  author: sourceText.author,
  language: sourceText.language,
  source_type: sourceText.sourceType,
  file_path: sourceText.filePath,
  url: sourceText.url,
  metadata: sourceText.metadata,
  processing_status: sourceText.processingStatus,
  created_at: sourceText.createdAt,
  updated_at: sourceText.updatedAt,
});

const convertSourceTextFromTauri = (tauriSourceText: TauriSourceText): SourceText => ({
  id: tauriSourceText.id,
  title: tauriSourceText.title,
  author: tauriSourceText.author,
  language: tauriSourceText.language,
  sourceType: tauriSourceText.source_type as SourceText['sourceType'],
  filePath: tauriSourceText.file_path,
  url: tauriSourceText.url,
  metadata: tauriSourceText.metadata,
  processingStatus: tauriSourceText.processing_status as SourceText['processingStatus'],
  createdAt: tauriSourceText.created_at,
  updatedAt: tauriSourceText.updated_at,
});

const convertDatasetToTauri = (dataset: Dataset): TauriDataset => ({
  id: dataset.id,
  name: dataset.name,
  description: dataset.description,
  source_texts: dataset.sourceTexts,
  chunks: dataset.chunks,
  metadata: dataset.metadata,
  status: dataset.status,
  created_at: dataset.createdAt,
  updated_at: dataset.updatedAt,
});

const convertDatasetFromTauri = (tauriDataset: TauriDataset): Dataset => ({
  id: tauriDataset.id,
  name: tauriDataset.name,
  description: tauriDataset.description,
  sourceTexts: tauriDataset.source_texts,
  chunks: tauriDataset.chunks,
  metadata: tauriDataset.metadata,
  status: tauriDataset.status as Dataset['status'],
  createdAt: tauriDataset.created_at,
  updatedAt: tauriDataset.updated_at,
});

// State synchronization service
export class StateSyncService {
  private static instance: StateSyncService;
  private isAutoSyncEnabled = true;
  private syncIntervalMs = 5000; // 5 seconds
  private syncIntervalId?: number;

  static getInstance(): StateSyncService {
    if (!StateSyncService.instance) {
      StateSyncService.instance = new StateSyncService();
    }
    return StateSyncService.instance;
  }

  // Initialize the sync service
  async initialize() {
    try {
      // Load initial state from backend
      await this.loadFromBackend();
      
      // Start auto-sync if enabled
      if (this.isAutoSyncEnabled) {
        this.startAutoSync();
      }
    } catch (error) {
      console.error('Failed to initialize state sync:', error);
    }
  }

  // Load state from Rust backend
  async loadFromBackend() {
    try {
      const [sourceTexts, datasets] = await Promise.all([
        invoke<TauriSourceText[]>('get_all_source_texts'),
        invoke<TauriDataset[]>('get_all_datasets'),
      ]);

      // Convert and update source texts
      const convertedSourceTexts: Record<string, SourceText> = {};
      sourceTexts.forEach((tauriSourceText: TauriSourceText) => {
        const sourceText = convertSourceTextFromTauri(tauriSourceText);
        convertedSourceTexts[sourceText.id] = sourceText;
      });

      // Convert and update datasets
      const convertedDatasets: Record<string, Dataset> = {};
      datasets.forEach((tauriDataset: TauriDataset) => {
        const dataset = convertDatasetFromTauri(tauriDataset);
        convertedDatasets[dataset.id] = dataset;
      });

      // Update store without triggering history
      useLexiconStore.setState({
        sourceTexts: convertedSourceTexts,
        datasets: convertedDatasets,
      });

    } catch (error) {
      console.error('Failed to load state from backend:', error);
      throw error;
    }
  }

  // Save state to Rust backend
  async saveToBackend() {
    try {
      const { sourceTexts, datasets } = useLexiconStore.getState();

      // Save source texts
      const sourceTextPromises = Object.values(sourceTexts).map(sourceText =>
        invoke('save_source_text', { sourceText: convertSourceTextToTauri(sourceText) })
      );

      // Save datasets
      const datasetPromises = Object.values(datasets).map(dataset =>
        invoke('save_dataset', { dataset: convertDatasetToTauri(dataset) })
      );

      await Promise.all([...sourceTextPromises, ...datasetPromises]);

    } catch (error) {
      console.error('Failed to save state to backend:', error);
      throw error;
    }
  }

  // Sync specific source text
  async syncSourceText(id: string) {
    try {
      const sourceText = useLexiconStore.getState().sourceTexts[id];
      if (sourceText) {
        await invoke('save_source_text', { 
          sourceText: convertSourceTextToTauri(sourceText) 
        });
      }
    } catch (error) {
      console.error(`Failed to sync source text ${id}:`, error);
      throw error;
    }
  }

  // Sync specific dataset
  async syncDataset(id: string) {
    try {
      const dataset = useLexiconStore.getState().datasets[id];
      if (dataset) {
        await invoke('save_dataset', { 
          dataset: convertDatasetToTauri(dataset) 
        });
      }
    } catch (error) {
      console.error(`Failed to sync dataset ${id}:`, error);
      throw error;
    }
  }

  // Process source text through Python pipeline
  async processSourceText(id: string, chunkingStrategy?: any) {
    try {
      useLexiconStore.getState().setSourceTextStatus(id, 'processing');
      
      const result = await invoke<any>('process_source_text', {
        sourceTextId: id,
        chunkingStrategy,
      });

      useLexiconStore.getState().setSourceTextStatus(id, 'completed');
      return result;
    } catch (error) {
      console.error(`Failed to process source text ${id}:`, error);
      useLexiconStore.getState().setSourceTextStatus(id, 'failed');
      throw error;
    }
  }

  // Generate dataset from processed sources
  async generateDataset(datasetId: string) {
    try {
      const dataset = useLexiconStore.getState().datasets[datasetId];
      if (!dataset) {
        throw new Error('Dataset not found');
      }

      useLexiconStore.getState().updateDataset(datasetId, { status: 'processing' });

      const result = await invoke<any>('generate_dataset', {
        datasetId,
        exportConfig: dataset.metadata.exportConfig,
      });

      useLexiconStore.getState().updateDataset(datasetId, { status: 'ready' });
      return result;
    } catch (error) {
      console.error(`Failed to generate dataset ${datasetId}:`, error);
      useLexiconStore.getState().updateDataset(datasetId, { status: 'draft' });
      throw error;
    }
  }

  // Start automatic synchronization
  startAutoSync() {
    if (this.syncIntervalId) {
      clearInterval(this.syncIntervalId);
    }

    this.syncIntervalId = window.setInterval(async () => {
      try {
        if (useLexiconStore.getState().settings.autoSave) {
          await this.saveToBackend();
        }
      } catch (error) {
        console.error('Auto-sync failed:', error);
      }
    }, this.syncIntervalMs);
  }

  // Stop automatic synchronization
  stopAutoSync() {
    if (this.syncIntervalId) {
      clearInterval(this.syncIntervalId);
      this.syncIntervalId = undefined;
    }
  }

  // Configure sync settings
  configurSync(options: {
    enabled?: boolean;
    intervalMs?: number;
  }) {
    if (options.enabled !== undefined) {
      this.isAutoSyncEnabled = options.enabled;
      if (options.enabled) {
        this.startAutoSync();
      } else {
        this.stopAutoSync();
      }
    }

    if (options.intervalMs !== undefined) {
      this.syncIntervalMs = options.intervalMs;
      if (this.isAutoSyncEnabled) {
        this.startAutoSync(); // Restart with new interval
      }
    }
  }

  // Manual sync trigger
  async manualSync() {
    try {
      await this.saveToBackend();
      await this.loadFromBackend();
    } catch (error) {
      console.error('Manual sync failed:', error);
      throw error;
    }
  }

  // Cleanup
  destroy() {
    this.stopAutoSync();
  }
}

// Hook for using state sync service
export const useStateSync = () => {
  const syncService = StateSyncService.getInstance();

  return {
    loadFromBackend: () => syncService.loadFromBackend(),
    saveToBackend: () => syncService.saveToBackend(),
    syncSourceText: (id: string) => syncService.syncSourceText(id),
    syncDataset: (id: string) => syncService.syncDataset(id),
    processSourceText: (id: string, chunkingStrategy?: any) => 
      syncService.processSourceText(id, chunkingStrategy),
    generateDataset: (datasetId: string) => syncService.generateDataset(datasetId),
    manualSync: () => syncService.manualSync(),
    configureSync: (options: { enabled?: boolean; intervalMs?: number }) =>
      syncService.configurSync(options),
  };
};
