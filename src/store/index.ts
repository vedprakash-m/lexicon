import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { persist } from 'zustand/middleware';
import { LexiconStore, AppState, SourceText, Dataset, AppSettings, ChunkingStrategy, ExportConfig } from './types';
import { v4 as uuidv4 } from 'uuid';
import { invoke } from '@tauri-apps/api/core';

// API Response type to match backend
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// Default settings
const defaultChunkingStrategy: ChunkingStrategy = {
  type: 'paragraph',
  maxTokens: 512,
  overlap: 50,
  preserveStructure: true,
};

const defaultExportConfig: ExportConfig = {
  format: 'jsonl',
  includeMetadata: true,
  weightingStrategy: 'balanced',
};

const defaultSettings: AppSettings = {
  theme: 'system',
  language: 'en',
  autoSave: true,
  backupFrequency: 'weekly',
  defaultChunkingStrategy,
  defaultExportConfig,
  cloudSync: {
    enabled: false,
    provider: 'none',
    autoSync: true,
    syncInterval: 5, // 5 minutes
    encryption: true,
    compression: true,
    syncPatterns: ['*.db', '*.json', 'enrichment_*.json', 'catalog_*.json'],
    excludePatterns: ['*.tmp', '*.log', 'cache_*', 'temp_*'],
  },
  notifications: {
    processingComplete: true,
    errors: true,
    updates: false,
    cloudSync: true,
  },
};

// Initial state
const initialState: AppState = {
  sourceTexts: {},
  datasets: {},
  settings: defaultSettings,
  activeDatasetId: null,
  activeSourceTextId: null,
  isLoading: false,
  error: null,
  history: [],
  historyIndex: -1,
  maxHistorySize: 50,
};

// Helper function to create a snapshot for undo/redo
const createSnapshot = (state: AppState): AppState => ({
  sourceTexts: { ...state.sourceTexts },
  datasets: { ...state.datasets },
  settings: { ...state.settings },
  activeDatasetId: state.activeDatasetId,
  activeSourceTextId: state.activeSourceTextId,
  isLoading: state.isLoading,
  error: state.error,
  history: [], // Don't include history in snapshots
  historyIndex: -1,
  maxHistorySize: state.maxHistorySize,
});

// Helper function to add a state to history
const addToHistory = (state: AppState) => {
  const snapshot = createSnapshot(state);
  
  // Remove any redo states
  const newHistory = state.history.slice(0, state.historyIndex + 1);
  newHistory.push(snapshot);
  
  // Limit history size
  if (newHistory.length > state.maxHistorySize) {
    newHistory.shift();
  } else {
    state.historyIndex++;
  }
  
  state.history = newHistory;
};

export const useLexiconStore = create<LexiconStore>()(
  persist(
    immer((set, get) => ({
      ...initialState,

      // Source Text actions
      addSourceText: (sourceTextData) => {
        const id = uuidv4();
        const now = new Date().toISOString();
        const sourceText: SourceText = {
          ...sourceTextData,
          id,
          createdAt: now,
          updatedAt: now,
        };

        set((state) => {
          addToHistory(state);
          state.sourceTexts[id] = sourceText;
        });

        return id;
      },

      updateSourceText: (id, updates) => {
        set((state) => {
          if (state.sourceTexts[id]) {
            addToHistory(state);
            state.sourceTexts[id] = {
              ...state.sourceTexts[id],
              ...updates,
              updatedAt: new Date().toISOString(),
            };
          }
        });
      },

      deleteSourceText: (id) => {
        set((state) => {
          if (state.sourceTexts[id]) {
            addToHistory(state);
            delete state.sourceTexts[id];
            
            // Remove from all datasets
            Object.values(state.datasets).forEach(dataset => {
              const index = dataset.sourceTexts.indexOf(id);
              if (index > -1) {
                dataset.sourceTexts.splice(index, 1);
                dataset.updatedAt = new Date().toISOString();
              }
            });

            // Clear active selection if deleted
            if (state.activeSourceTextId === id) {
              state.activeSourceTextId = null;
            }
          }
        });
      },

      setSourceTextStatus: (id, status) => {
        set((state) => {
          if (state.sourceTexts[id]) {
            state.sourceTexts[id].processingStatus = status;
            state.sourceTexts[id].updatedAt = new Date().toISOString();
          }
        });
      },

      // Dataset actions
      createDataset: (datasetData) => {
        const id = uuidv4();
        const now = new Date().toISOString();
        const dataset: Dataset = {
          ...datasetData,
          id,
          createdAt: now,
          updatedAt: now,
        };

        set((state) => {
          addToHistory(state);
          state.datasets[id] = dataset;
        });

        return id;
      },

      updateDataset: (id, updates) => {
        set((state) => {
          if (state.datasets[id]) {
            addToHistory(state);
            state.datasets[id] = {
              ...state.datasets[id],
              ...updates,
              updatedAt: new Date().toISOString(),
            };
          }
        });
      },

      deleteDataset: (id) => {
        set((state) => {
          if (state.datasets[id]) {
            addToHistory(state);
            delete state.datasets[id];
            
            // Clear active selection if deleted
            if (state.activeDatasetId === id) {
              state.activeDatasetId = null;
            }
          }
        });
      },

      addSourceToDataset: (datasetId, sourceTextId) => {
        set((state) => {
          const dataset = state.datasets[datasetId];
          const sourceText = state.sourceTexts[sourceTextId];
          
          if (dataset && sourceText && !dataset.sourceTexts.includes(sourceTextId)) {
            addToHistory(state);
            dataset.sourceTexts.push(sourceTextId);
            dataset.updatedAt = new Date().toISOString();
          }
        });
      },

      removeSourceFromDataset: (datasetId, sourceTextId) => {
        set((state) => {
          const dataset = state.datasets[datasetId];
          if (dataset) {
            const index = dataset.sourceTexts.indexOf(sourceTextId);
            if (index > -1) {
              addToHistory(state);
              dataset.sourceTexts.splice(index, 1);
              dataset.updatedAt = new Date().toISOString();
            }
          }
        });
      },

      updateDatasetChunks: (datasetId, chunks) => {
        set((state) => {
          const dataset = state.datasets[datasetId];
          if (dataset) {
            addToHistory(state);
            dataset.chunks = chunks;
            dataset.metadata.totalChunks = chunks.length;
            dataset.metadata.totalWords = chunks.reduce((sum, chunk) => sum + chunk.metadata.wordCount, 0);
            dataset.updatedAt = new Date().toISOString();
          }
        });
      },

      // Settings actions
      updateSettings: async (updates) => {
        // Validate settings before updating
        const currentSettings = get().settings;
        const newSettings = { ...currentSettings, ...updates };
        
        // Basic validation
        if (newSettings.cloudSync.syncInterval < 1) {
          throw new Error('Sync interval must be at least 1 minute');
        }
        
        if (newSettings.backupFrequency && !['none', 'daily', 'weekly', 'monthly'].includes(newSettings.backupFrequency)) {
          throw new Error('Invalid backup frequency');
        }
        
        if (newSettings.theme && !['light', 'dark', 'system'].includes(newSettings.theme)) {
          throw new Error('Invalid theme');
        }

        try {
          // Save to backend first
          const response = await invoke('save_app_settings', { settings: newSettings }) as ApiResponse<boolean>;
          
          if (response.success) {
            // Only update local state if backend save succeeded
            set((state) => {
              addToHistory(state);
              state.settings = newSettings;
            });
          } else {
            throw new Error(response.error || 'Failed to save settings');
          }
        } catch (error) {
          console.error('Failed to save settings:', error);
          throw error;
        }
      },

      loadSettings: async () => {
        try {
          const response = await invoke('get_app_settings') as ApiResponse<AppSettings>;
          
          if (response.success && response.data) {
            set((state) => {
              state.settings = { ...defaultSettings, ...response.data };
            });
          }
        } catch (error) {
          console.error('Failed to load settings from backend:', error);
          // Fall back to default settings
          set((state) => {
            state.settings = defaultSettings;
          });
        }
      },

      resetSettings: async () => {
        try {
          // Save default settings to backend
          const response = await invoke('save_app_settings', { settings: defaultSettings }) as ApiResponse<boolean>;
          
          if (response.success) {
            set((state) => {
              addToHistory(state);
              state.settings = { ...defaultSettings };
            });
          } else {
            throw new Error(response.error || 'Failed to reset settings');
          }
        } catch (error) {
          console.error('Failed to reset settings:', error);
          throw error;
        }
      },

      // Reset entire store to initial state
      reset: () => {
        set(() => ({ ...initialState }));
      },

      // Undo/Redo actions
      undo: () => {
        set((state) => {
          if (state.historyIndex >= 0) {
            const previousState = state.history[state.historyIndex];
            state.historyIndex--;
            
            // Restore state (excluding history)
            state.sourceTexts = previousState.sourceTexts;
            state.datasets = previousState.datasets;
            state.settings = previousState.settings;
            state.activeDatasetId = previousState.activeDatasetId;
            state.activeSourceTextId = previousState.activeSourceTextId;
            state.isLoading = previousState.isLoading;
            state.error = previousState.error;
          }
        });
      },

      redo: () => {
        set((state) => {
          if (state.historyIndex < state.history.length - 1) {
            state.historyIndex++;
            const nextState = state.history[state.historyIndex];
            
            // Restore state (excluding history)
            state.sourceTexts = nextState.sourceTexts;
            state.datasets = nextState.datasets;
            state.settings = nextState.settings;
            state.activeDatasetId = nextState.activeDatasetId;
            state.activeSourceTextId = nextState.activeSourceTextId;
            state.isLoading = nextState.isLoading;
            state.error = nextState.error;
          }
        });
      },

      get canUndo() {
        return get().historyIndex >= 0;
      },

      get canRedo() {
        const state = get();
        return state.historyIndex < state.history.length - 1;
      },

      // Persistence actions
      saveState: async () => {
        const state = get();
        try {
          // Use Tauri's fs plugin to save state
          const { writeTextFile } = await import('@tauri-apps/plugin-fs');
          const { appDataDir } = await import('@tauri-apps/api/path');
          
          const appDir = await appDataDir();
          const statePath = `${appDir}/lexicon-state.json`;
          
          const stateToSave = {
            sourceTexts: state.sourceTexts,
            datasets: state.datasets,
            settings: state.settings,
            activeDatasetId: state.activeDatasetId,
            activeSourceTextId: state.activeSourceTextId,
          };
          
          await writeTextFile(statePath, JSON.stringify(stateToSave, null, 2));
        } catch (error) {
          console.error('Failed to save state:', error);
          set((state) => {
            state.error = 'Failed to save application state';
          });
        }
      },

      loadState: async () => {
        try {
          const { readTextFile } = await import('@tauri-apps/plugin-fs');
          const { appDataDir } = await import('@tauri-apps/api/path');
          
          const appDir = await appDataDir();
          const statePath = `${appDir}/lexicon-state.json`;
          
          const stateData = await readTextFile(statePath);
          const loadedState = JSON.parse(stateData);
          
          set((state) => {
            state.sourceTexts = loadedState.sourceTexts || {};
            state.datasets = loadedState.datasets || {};
            state.settings = { ...defaultSettings, ...loadedState.settings };
            state.activeDatasetId = loadedState.activeDatasetId || null;
            state.activeSourceTextId = loadedState.activeSourceTextId || null;
            state.error = null;
          });
        } catch (error) {
          console.error('Failed to load state:', error);
          // Don't set error here as it might be expected (first run)
        }
      },

      exportState: async () => {
        const state = get();
        const exportData = {
          sourceTexts: state.sourceTexts,
          datasets: state.datasets,
          settings: state.settings,
          exportedAt: new Date().toISOString(),
          version: '1.0.0',
        };
        return JSON.stringify(exportData, null, 2);
      },

      importState: async (data) => {
        try {
          const importedData = JSON.parse(data);
          set((state) => {
            addToHistory(state);
            if (importedData.sourceTexts) {
              state.sourceTexts = { ...state.sourceTexts, ...importedData.sourceTexts };
            }
            if (importedData.datasets) {
              state.datasets = { ...state.datasets, ...importedData.datasets };
            }
            if (importedData.settings) {
              state.settings = { ...state.settings, ...importedData.settings };
            }
            state.error = null;
          });
        } catch (error) {
          set((state) => {
            state.error = 'Failed to import state: Invalid data format';
          });
          throw error;
        }
      },

      // UI state actions
      setActiveDataset: (id) => {
        set((state) => {
          state.activeDatasetId = id;
        });
      },

      setActiveSourceText: (id) => {
        set((state) => {
          state.activeSourceTextId = id;
        });
      },

      setLoading: (loading) => {
        set((state) => {
          state.isLoading = loading;
        });
      },

      setError: (error) => {
        set((state) => {
          state.error = error;
        });
      },

      clearError: () => {
        set((state) => {
          state.error = null;
        });
      },

      // Getter methods for active items
      getActiveSourceText: () => {
        const state = get();
        return state.activeSourceTextId ? state.sourceTexts[state.activeSourceTextId] : null;
      },

      getActiveDataset: () => {
        const state = get();
        return state.activeDatasetId ? state.datasets[state.activeDatasetId] : null;
      },
    })),
    {
      name: 'lexicon-store',
      partialize: (state) => ({
        sourceTexts: state.sourceTexts,
        datasets: state.datasets,
        settings: state.settings,
        activeDatasetId: state.activeDatasetId,
        activeSourceTextId: state.activeSourceTextId,
      }),
    }
  )
);

// Selectors for easy access to computed state
export const useSourceTexts = () => useLexiconStore((state) => state.sourceTexts);
export const useDatasets = () => useLexiconStore((state) => state.datasets);
export const useSettings = () => useLexiconStore((state) => state.settings);
export const useActiveDataset = () => {
  const datasets = useDatasets();
  const activeId = useLexiconStore((state) => state.activeDatasetId);
  return activeId ? datasets[activeId] : null;
};
export const useActiveSourceText = () => {
  const sourceTexts = useSourceTexts();
  const activeId = useLexiconStore((state) => state.activeSourceTextId);
  return activeId ? sourceTexts[activeId] : null;
};
export const useUIState = () => useLexiconStore((state) => ({
  isLoading: state.isLoading,
  error: state.error,
  canUndo: state.canUndo,
  canRedo: state.canRedo,
}));
