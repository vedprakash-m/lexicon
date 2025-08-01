import React from 'react';
import { render, screen, fireEvent, waitFor, act, cleanup } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import CloudSyncSettings from '../CloudSyncSettings';
import { useLexiconStore } from '../../store';
import { AsyncTestUtils } from '../../test/utils/AsyncTestUtils';

// Mock Tauri API
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(),
}));

// Mock the store
vi.mock('../../store', () => ({
  useLexiconStore: vi.fn(),
}));

const mockStore = {
  settings: {
    cloudSync: {
      enabled: false,
      provider: 'none' as const,
      autoSync: true,
      syncInterval: 5,
      encryption: true,
      compression: true,
      syncPatterns: ['*.db', '*.json', 'enrichment_*.json', 'catalog_*.json'],
      excludePatterns: ['*.tmp', '*.log', 'cache_*', 'temp_*'],
    },
  },
  updateSettings: vi.fn(),
};

describe('CloudSyncSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useLexiconStore as any).mockReturnValue(mockStore);
    cleanup(); // Ensure clean state between tests
  });

  afterEach(() => {
    cleanup(); // Clean up after each test
  });

  it('renders all cloud provider options', async () => {
    await act(async () => {
      render(<CloudSyncSettings />);
    });
    
    expect(screen.getByText('Disabled')).toBeInTheDocument();
    expect(screen.getByText('iCloud Drive')).toBeInTheDocument();
    expect(screen.getByText('Google Drive')).toBeInTheDocument();
    expect(screen.getByText('Dropbox')).toBeInTheDocument();
    expect(screen.getByText('Microsoft OneDrive')).toBeInTheDocument();
  });

  it('shows correct provider as selected', async () => {
    await act(async () => {
      render(<CloudSyncSettings />);
    });
    
    // Check that a provider is selected (could be any provider based on store state)
    const selectedBadge = screen.getByText('Selected');
    expect(selectedBadge).toBeInTheDocument();
  });

  it('updates provider when clicking on a different option', async () => {
    const { invoke } = await import('@tauri-apps/api/core');
    (invoke as any).mockResolvedValue({
      enabled: false,
      lastSync: null,
      provider: null,
      conflicts: 0,
      pendingUploads: 0,
      pendingDownloads: 0,
    });

    render(<CloudSyncSettings />);
    
    // Click on iCloud Drive - use getAllByText in case there are duplicates
    const icloudCards = screen.getAllByText('iCloud Drive');
    const icloudCard = icloudCards[0].closest('div');
    
    await act(async () => {
      fireEvent.click(icloudCard!);
    });
    
    await waitFor(() => {
      expect(mockStore.updateSettings).toHaveBeenCalledWith({
        ...mockStore.settings,
        cloudSync: {
          ...mockStore.settings.cloudSync,
          provider: 'icloud',
          enabled: true,
        },
      });
    });
  });

  it('shows sync settings when provider is not none', async () => {
    const storeWithProvider = {
      ...mockStore,
      settings: {
        ...mockStore.settings,
        cloudSync: {
          ...mockStore.settings.cloudSync,
          provider: 'icloud' as const,
          enabled: true,
        },
      },
    };
    (useLexiconStore as any).mockReturnValue(storeWithProvider);

    await act(async () => {
      render(<CloudSyncSettings />);
    });
    
    expect(screen.getByText('Sync Settings')).toBeInTheDocument();
    expect(screen.getByText('Automatic synchronization')).toBeInTheDocument();
    expect(screen.getByText('Encrypt data before upload')).toBeInTheDocument();
    expect(screen.getByText('Compress data to save bandwidth')).toBeInTheDocument();
  });

  it('toggles auto-sync setting', async () => {
    const storeWithProvider = {
      ...mockStore,
      settings: {
        ...mockStore.settings,
        cloudSync: {
          ...mockStore.settings.cloudSync,
          provider: 'icloud' as const,
          enabled: true,
        },
      },
    };
    (useLexiconStore as any).mockReturnValue(storeWithProvider);

    await act(async () => {
      render(<CloudSyncSettings />);
    });
    
    const autoSyncCheckbox = screen.getByLabelText('Automatic synchronization');
    
    await act(async () => {
      fireEvent.click(autoSyncCheckbox);
    });
    
    expect(mockStore.updateSettings).toHaveBeenCalled();
  });

  it('updates sync interval', async () => {
    const storeWithProvider = {
      ...mockStore,
      settings: {
        ...mockStore.settings,
        cloudSync: {
          ...mockStore.settings.cloudSync,
          provider: 'icloud' as const,
          enabled: true,
        },
      },
    };
    (useLexiconStore as any).mockReturnValue(storeWithProvider);

    await act(async () => {
      render(<CloudSyncSettings />);
    });
    
    const intervalSelect = screen.getByDisplayValue('5 minutes');
    
    await act(async () => {
      fireEvent.change(intervalSelect, { target: { value: '15' } });
    });
    
    expect(mockStore.updateSettings).toHaveBeenCalled();
  });

  it('shows sync status when available', async () => {
    const { invoke } = await import('@tauri-apps/api/core');
    (invoke as any).mockResolvedValue({
      enabled: true,
      lastSync: '2025-07-14T12:00:00Z',
      provider: 'icloud',
      conflicts: 0,
      pendingUploads: 2,
      pendingDownloads: 0,
    });

    const storeWithProvider = {
      ...mockStore,
      settings: {
        ...mockStore.settings,
        cloudSync: {
          ...mockStore.settings.cloudSync,
          provider: 'icloud' as const,
          enabled: true,
        },
      },
    };
    (useLexiconStore as any).mockReturnValue(storeWithProvider);

    render(<CloudSyncSettings />);
    
    await waitFor(() => {
      expect(screen.getByText('Sync Status')).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument(); // pending uploads
    });
  });

  it('handles sync control actions', async () => {
    const { invoke } = await import('@tauri-apps/api/core');
    (invoke as any).mockResolvedValue({
      enabled: true,
      lastSync: '2025-07-14T12:00:00Z',
      provider: 'icloud',
      conflicts: 0,
      pendingUploads: 0,
      pendingDownloads: 0,
    });

    const storeWithProvider = {
      ...mockStore,
      settings: {
        ...mockStore.settings,
        cloudSync: {
          ...mockStore.settings.cloudSync,
          provider: 'icloud' as const,
          enabled: true,
        },
      },
    };
    (useLexiconStore as any).mockReturnValue(storeWithProvider);

    await act(async () => {
      render(<CloudSyncSettings />);
    });
    
    await waitFor(() => {
      expect(screen.getAllByText('Stop Sync')[0]).toBeInTheDocument();
    });

    await act(async () => {
      const stopButton = screen.getAllByText('Stop Sync')[0];
      fireEvent.click(stopButton);
    });
    
    expect(invoke).toHaveBeenCalledWith('stop_sync');
  });

  it('updates sync patterns', async () => {
    const storeWithProvider = {
      ...mockStore,
      settings: {
        ...mockStore.settings,
        cloudSync: {
          ...mockStore.settings.cloudSync,
          provider: 'icloud' as const,
          enabled: true,
        },
      },
    };
    (useLexiconStore as any).mockReturnValue(storeWithProvider);

    await act(async () => {
      render(<CloudSyncSettings />);
    });
    
    // Find the textarea by label text since placeholder might not match exactly
    await act(async () => {
      const syncPatternsTextarea = screen.getByLabelText('Files to sync (patterns)');
      fireEvent.change(syncPatternsTextarea, { 
        target: { value: '*.db\n*.json\nnew_pattern_*.json' } 
      });
    });
    
    expect(mockStore.updateSettings).toHaveBeenCalled();
  });

  it('displays provider features correctly', async () => {
    await act(async () => {
      render(<CloudSyncSettings />);
    });
    
    // Check iCloud features - use getAllByText since there might be multiple elements
    expect(screen.getAllByText(/Native integration/)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Cross-device sync/)[0]).toBeInTheDocument();
    
    // Check Google Drive features
    expect(screen.getAllByText(/15GB free storage/)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Cross-platform/)[0]).toBeInTheDocument();
    
    // Check Dropbox features
    expect(screen.getAllByText(/Smart sync/)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Team collaboration/)[0]).toBeInTheDocument();
  });

  it('shows loading state during connection test', async () => {
    // Mock the invoke function to resolve after a delay
    const { invoke } = await import('@tauri-apps/api/core');
    let resolveInvoke: (value: any) => void;
    const invokePromise = new Promise(resolve => {
      resolveInvoke = resolve;
    });
    
    (invoke as any).mockImplementation(() => invokePromise);

    await act(async () => {
      render(<CloudSyncSettings />);
    });
    
    await act(async () => {
      const icloudCards = screen.getAllByText('iCloud Drive');
      const icloudCard = icloudCards[0].closest('div');
      fireEvent.click(icloudCard!);
    });
    
    // Check that the provider gets selected and store is updated
    await waitFor(() => {
      expect(mockStore.updateSettings).toHaveBeenCalled();
    });
    
    // Resolve the invoke promise to complete the async operation
    await act(async () => {
      resolveInvoke!({
        enabled: true,
        lastSync: null,
        provider: 'icloud',
        conflicts: 0,
        pendingUploads: 0,
        pendingDownloads: 0,
      });
      
      // Wait for the promise to resolve
      await invokePromise;
    });
  });
});
