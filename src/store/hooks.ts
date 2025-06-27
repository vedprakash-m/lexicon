import { useCallback } from 'react';
import { useLexiconStore } from './index';
import { SourceText, Dataset, ChunkingStrategy, ExportConfig } from './types';

// Hook for managing source texts
export const useSourceTextActions = () => {
  const {
    addSourceText,
    updateSourceText,
    deleteSourceText,
    setSourceTextStatus,
    setActiveSourceText,
  } = useLexiconStore();

  const createSourceText = useCallback((data: {
    title: string;
    author?: string;
    language: string;
    sourceType: SourceText['sourceType'];
    filePath?: string;
    url?: string;
    metadata?: Partial<SourceText['metadata']>;
  }) => {
    const sourceText = {
      ...data,
      metadata: {
        tags: [],
        customFields: {},
        ...data.metadata,
      },
      processingStatus: 'pending' as const,
    };
    
    return addSourceText(sourceText);
  }, [addSourceText]);

  const updateSourceTextMetadata = useCallback((
    id: string,
    metadata: Partial<SourceText['metadata']>
  ) => {
    const currentSourceText = useLexiconStore.getState().sourceTexts[id];
    if (currentSourceText) {
      const updatedMetadata = {
        ...currentSourceText.metadata,
        ...metadata,
      };
      updateSourceText(id, { metadata: updatedMetadata });
    }
  }, [updateSourceText]);

  return {
    createSourceText,
    updateSourceText,
    updateSourceTextMetadata,
    deleteSourceText,
    setSourceTextStatus,
    setActiveSourceText,
  };
};

// Hook for managing datasets
export const useDatasetActions = () => {
  const {
    createDataset,
    updateDataset,
    deleteDataset,
    addSourceToDataset,
    removeSourceFromDataset,
    updateDatasetChunks,
    setActiveDataset,
  } = useLexiconStore();

  const createNewDataset = useCallback((data: {
    name: string;
    description?: string;
    chunkingStrategy?: ChunkingStrategy;
    exportConfig?: ExportConfig;
  }) => {
    const dataset = {
      ...data,
      sourceTexts: [],
      chunks: [],
      metadata: {
        totalChunks: 0,
        totalWords: 0,
        languages: [],
        chunkingStrategy: data.chunkingStrategy || {
          type: 'paragraph' as const,
          maxTokens: 512,
          overlap: 50,
          preserveStructure: true,
        },
        exportConfig: data.exportConfig || {
          format: 'jsonl' as const,
          includeMetadata: true,
          weightingStrategy: 'balanced' as const,
        },
        customFields: {},
      },
      status: 'draft' as const,
    };
    
    return createDataset(dataset);
  }, [createDataset]);

  const updateDatasetMetadata = useCallback((
    id: string,
    metadata: Partial<Dataset['metadata']>
  ) => {
    const currentDataset = useLexiconStore.getState().datasets[id];
    if (currentDataset) {
      const updatedMetadata = {
        ...currentDataset.metadata,
        ...metadata,
      };
      updateDataset(id, { metadata: updatedMetadata });
    }
  }, [updateDataset]);

  return {
    createNewDataset,
    updateDataset,
    updateDatasetMetadata,
    deleteDataset,
    addSourceToDataset,
    removeSourceFromDataset,
    updateDatasetChunks,
    setActiveDataset,
  };
};

// Hook for undo/redo functionality
export const useHistory = () => {
  const { undo, redo, canUndo, canRedo } = useLexiconStore();

  const handleUndo = useCallback(() => {
    if (canUndo) {
      undo();
    }
  }, [undo, canUndo]);

  const handleRedo = useCallback(() => {
    if (canRedo) {
      redo();
    }
  }, [redo, canRedo]);

  return {
    undo: handleUndo,
    redo: handleRedo,
    canUndo,
    canRedo,
  };
};

// Hook for persistence operations
export const usePersistence = () => {
  const { saveState, loadState, exportState, importState } = useLexiconStore();

  const handleExport = useCallback(async (): Promise<string> => {
    return await exportState();
  }, [exportState]);

  const handleImport = useCallback(async (data: string): Promise<void> => {
    await importState(data);
  }, [importState]);

  return {
    saveState,
    loadState,
    exportState: handleExport,
    importState: handleImport,
  };
};

// Hook for application settings
export const useSettingsActions = () => {
  const { updateSettings, resetSettings } = useLexiconStore();

  const updateTheme = useCallback((theme: 'light' | 'dark' | 'system') => {
    updateSettings({ theme });
  }, [updateSettings]);

  const updateLanguage = useCallback((language: string) => {
    updateSettings({ language });
  }, [updateSettings]);

  const updateAutoSave = useCallback((autoSave: boolean) => {
    updateSettings({ autoSave });
  }, [updateSettings]);

  const updateBackupFrequency = useCallback((backupFrequency: 'none' | 'daily' | 'weekly' | 'monthly') => {
    updateSettings({ backupFrequency });
  }, [updateSettings]);

  const updateDefaultChunkingStrategy = useCallback((chunkingStrategy: ChunkingStrategy) => {
    updateSettings({ defaultChunkingStrategy: chunkingStrategy });
  }, [updateSettings]);

  const updateDefaultExportConfig = useCallback((exportConfig: ExportConfig) => {
    updateSettings({ defaultExportConfig: exportConfig });
  }, [updateSettings]);

  const updateNotificationSettings = useCallback((notifications: Partial<{
    processingComplete: boolean;
    errors: boolean;
    updates: boolean;
  }>) => {
    updateSettings({ 
      notifications: { 
        ...useLexiconStore.getState().settings.notifications, 
        ...notifications 
      } 
    });
  }, [updateSettings]);

  return {
    updateSettings,
    resetSettings,
    updateTheme,
    updateLanguage,
    updateAutoSave,
    updateBackupFrequency,
    updateDefaultChunkingStrategy,
    updateDefaultExportConfig,
    updateNotificationSettings,
  };
};

// Hook for error handling
export const useErrorHandling = () => {
  const { setError, error } = useLexiconStore();

  const clearError = useCallback(() => {
    setError(null);
  }, [setError]);

  const handleError = useCallback((error: Error | string) => {
    const errorMessage = typeof error === 'string' ? error : error.message;
    setError(errorMessage);
    console.error('Application error:', error);
  }, [setError]);

  return {
    error,
    setError,
    clearError,
    handleError,
  };
};

// Hook for loading states
export const useLoadingState = () => {
  const { setLoading, isLoading } = useLexiconStore();

  const withLoading = useCallback(async <T>(
    operation: () => Promise<T>
  ): Promise<T> => {
    setLoading(true);
    try {
      const result = await operation();
      return result;
    } finally {
      setLoading(false);
    }
  }, [setLoading]);

  return {
    isLoading,
    setLoading,
    withLoading,
  };
};
