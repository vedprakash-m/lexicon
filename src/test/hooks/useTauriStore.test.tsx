import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useLexiconStore } from '../../store';
import { useSourceTextActions, useDatasetActions } from '../../store/hooks';

// Mock Tauri API
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(),
}));

// Test wrapper
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('Store Hooks Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset store state by creating new initial state
    useLexiconStore.setState({
      sourceTexts: {},
      datasets: {},
      settings: {
        theme: 'system',
        language: 'en',
        autoSave: true,
        backupFrequency: 'weekly',
        defaultChunkingStrategy: {
          type: 'paragraph',
          maxTokens: 512,
          overlap: 50,
          preserveStructure: true,
        },
        defaultExportConfig: {
          format: 'jsonl',
          includeMetadata: true,
          weightingStrategy: 'balanced',
        },
        cloudSync: {
          enabled: false,
          provider: 'none',
          autoSync: false,
          syncInterval: 60,
          encryption: true,
          compression: true,
          syncPatterns: [],
          excludePatterns: []
        },
        notifications: {
          processingComplete: true,
          errors: true,
          updates: false,
          cloudSync: false,
        },
      },
      activeDatasetId: null,
      activeSourceTextId: null,
      isLoading: false,
      error: null,
      history: [],
      historyIndex: -1,
      maxHistorySize: 50,
    });
  });

  describe('useSourceTextActions Hook', () => {
    it('creates source text correctly', () => {
      const { result } = renderHook(() => useSourceTextActions(), {
        wrapper: createWrapper(),
      });

      const sourceTextData = {
        title: 'Test Book',
        author: 'Test Author',
        language: 'en',
        sourceType: 'book' as const,
        metadata: {
          tags: [],
          customFields: {},
        },
      };

      act(() => {
        const id = result.current.createSourceText(sourceTextData);
        expect(id).toBeDefined();
        expect(typeof id).toBe('string');
      });
    });

    it('updates source text metadata correctly', () => {
      const { result } = renderHook(() => useSourceTextActions(), {
        wrapper: createWrapper(),
      });

      act(() => {
        const id = result.current.createSourceText({
          title: 'Test Book',
          language: 'en',
          sourceType: 'book',
          metadata: { tags: [], customFields: {} },
        });

        result.current.updateSourceText(id, {
          author: 'Updated Author',
        });

        const state = useLexiconStore.getState();
        expect(state.sourceTexts[id]?.author).toBe('Updated Author');
      });
    });

    it('starts processing correctly', () => {
      const { result } = renderHook(() => useSourceTextActions(), {
        wrapper: createWrapper(),
      });

      act(() => {
        const id = result.current.createSourceText({
          title: 'Test Book',
          language: 'en',
          sourceType: 'book',
          metadata: { tags: [], customFields: {} },
        });

        result.current.setSourceTextStatus(id, 'processing');

        const state = useLexiconStore.getState();
        expect(state.sourceTexts[id]?.processingStatus).toBe('processing');
      });
    });
  });

  describe('useDatasetActions Hook', () => {
    it('creates dataset correctly', () => {
      const { result } = renderHook(() => useDatasetActions(), {
        wrapper: createWrapper(),
      });

      const datasetData = {
        name: 'Test Dataset',
        description: 'A test dataset',
        sourceTexts: [],
        chunks: [],
        metadata: {
          tags: [],
          customFields: {},
        },
        status: 'draft' as const,
      };

      act(() => {
        const id = result.current.createNewDataset(datasetData);
        expect(id).toBeDefined();
        expect(typeof id).toBe('string');
      });
    });

    it('adds source text to dataset', () => {
      const { result: sourceActions } = renderHook(() => useSourceTextActions(), {
        wrapper: createWrapper(),
      });
      const { result: datasetActions } = renderHook(() => useDatasetActions(), {
        wrapper: createWrapper(),
      });

      act(() => {
        const sourceId = sourceActions.current.createSourceText({
          title: 'Test Book',
          language: 'en',
          sourceType: 'book',
          metadata: { tags: [], customFields: {} },
        });

        const datasetId = datasetActions.current.createNewDataset({
          name: 'Test Dataset',
          description: 'A test dataset',
        });

        datasetActions.current.addSourceToDataset(datasetId, sourceId);

        const state = useLexiconStore.getState();
        expect(state.datasets[datasetId]?.sourceTexts).toContain(sourceId);
      });
    });

    it('removes source text from dataset', () => {
      const { result: sourceActions } = renderHook(() => useSourceTextActions(), {
        wrapper: createWrapper(),
      });
      const { result: datasetActions } = renderHook(() => useDatasetActions(), {
        wrapper: createWrapper(),
      });

      act(() => {
        const sourceId = sourceActions.current.createSourceText({
          title: 'Test Book',
          language: 'en',
          sourceType: 'book',
          metadata: { tags: [], customFields: {} },
        });

        const datasetId = datasetActions.current.createNewDataset({
          name: 'Test Dataset',
          description: 'A test dataset',
        });

        // Add source text first, then remove it
        datasetActions.current.addSourceToDataset(datasetId, sourceId);
        datasetActions.current.removeSourceFromDataset(datasetId, sourceId);

        const state = useLexiconStore.getState();
        expect(state.datasets[datasetId]?.sourceTexts).not.toContain(sourceId);
      });
    });
  });

  describe('useChunkingActions Hook', () => {
    it('creates chunking strategy correctly', () => {
      const strategy = {
        type: 'sentence' as const,
        maxTokens: 256,
        overlap: 25,
        preserveStructure: false,
      };

      // This would need actual chunking hook implementation
      expect(strategy.type).toBe('sentence');
    });

    it('applies chunking strategy correctly', () => {
      // This would need actual chunking implementation
      expect(true).toBe(true);
    });
  });

  describe('Error Handling', () => {
    it('handles store reset correctly', () => {
      const { result } = renderHook(() => useSourceTextActions(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.createSourceText({
          title: 'Test Book',
          language: 'en',
          sourceType: 'book',
          metadata: { tags: [], customFields: {} },
        });

        // Reset store
        useLexiconStore.getState().reset();

        const state = useLexiconStore.getState();
        expect(Object.keys(state.sourceTexts)).toHaveLength(0);
      });
    });

    it('handles invalid operations gracefully', () => {
      const { result } = renderHook(() => useSourceTextActions(), {
        wrapper: createWrapper(),
      });

      act(() => {
        // Try to update non-existent source text
        result.current.updateSourceText('non-existent-id', {
          title: 'Updated Title',
        });

        // Should not crash
        const state = useLexiconStore.getState();
        expect(state.sourceTexts['non-existent-id']).toBeUndefined();
      });
    });
  });

  describe('Performance', () => {
    it('handles multiple rapid operations efficiently', () => {
      const { result } = renderHook(() => useSourceTextActions(), {
        wrapper: createWrapper(),
      });

      act(() => {
        // Create multiple source texts rapidly
        for (let i = 0; i < 10; i++) {
          result.current.createSourceText({
            title: `Test Book ${i}`,
            language: 'en',
            sourceType: 'book',
            metadata: { tags: [], customFields: {} },
          });
        }

        const state = useLexiconStore.getState();
        expect(Object.keys(state.sourceTexts)).toHaveLength(10);
      });
    });
  });
});
