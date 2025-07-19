import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import CloudSyncSettings from '../CloudSyncSettings';
import { useLexiconStore } from '../../store';

// Mock Tauri API
vi.mock('@tauri-apps/api/tauri', () => ({
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
  });

  it('renders all cloud provider options', () => {
    render(<CloudSyncSettings />);
    
    expect(screen.getByText('Disabled')).toBeInTheDocument();
    expect(screen.getByText('iCloud Drive')).toBeInTheDocument();
    expect(screen.getByText('Google Drive')).toBeInTheDocument();
    expect(screen.getByText('Dropbox')).toBeInTheDocument();
    expect(screen.getByText('Microsoft OneDrive')).toBeInTheDocument();
  });

  it('shows correct provider as selected', () => {
    render(<CloudSyncSettings />);
    
    // 'none' should be selected by default
    const disabledCard = screen.getByText('Disabled').closest('div');
    expect(disabledCard).toHaveClass('border-blue-500');
  });

  it('updates provider when clicking on a different option', async () => {
    const { invoke } = await import('@tauri-apps/api/tauri');
    (invoke as any).mockResolvedValue({
      enabled: false,
      lastSync: null,
      provider: null,
      conflicts: 0,
      pendingUploads: 0,
      pendingDownloads: 0,
    });

    render(<CloudSyncSettings />);
    
    // Click on iCloud Drive
    const icloudCard = screen.getByText('iCloud Drive').closest('div');
    fireEvent.click(icloudCard!);
    
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

  it('shows sync settings when provider is not none', () => {
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
    
    expect(screen.getByText('Sync Settings')).toBeInTheDocument();
    expect(screen.getByText('Automatic synchronization')).toBeInTheDocument();
    expect(screen.getByText('Encrypt data before upload')).toBeInTheDocument();
    expect(screen.getByText('Compress data to save bandwidth')).toBeInTheDocument();
  });

  it('toggles auto-sync setting', () => {
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
    
    const autoSyncCheckbox = screen.getByLabelText('Automatic synchronization');
    fireEvent.click(autoSyncCheckbox);
    
    expect(mockStore.updateSettings).toHaveBeenCalled();
  });

  it('updates sync interval', () => {
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
    
    const intervalSelect = screen.getByDisplayValue('5 minutes');
    fireEvent.change(intervalSelect, { target: { value: '15' } });
    
    expect(mockStore.updateSettings).toHaveBeenCalled();
  });

  it('shows sync status when available', async () => {
    const { invoke } = await import('@tauri-apps/api/tauri');
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
    const { invoke } = await import('@tauri-apps/api/tauri');
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

    render(<CloudSyncSettings />);
    
    await waitFor(() => {
      expect(screen.getByText('Stop Sync')).toBeInTheDocument();
    });

    const stopButton = screen.getByText('Stop Sync');
    fireEvent.click(stopButton);
    
    expect(invoke).toHaveBeenCalledWith('stop_sync');
  });

  it('updates sync patterns', () => {
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
    
    const syncPatternsTextarea = screen.getByDisplayValue('*.db\n*.json\nenrichment_*.json\ncatalog_*.json');
    fireEvent.change(syncPatternsTextarea, { 
      target: { value: '*.db\n*.json\nnew_pattern_*.json' } 
    });
    
    expect(mockStore.updateSettings).toHaveBeenCalled();
  });

  it('displays provider features correctly', () => {
    render(<CloudSyncSettings />);
    
    // Check iCloud features
    expect(screen.getByText(/Native integration/)).toBeInTheDocument();
    expect(screen.getByText(/Cross-device sync/)).toBeInTheDocument();
    
    // Check Google Drive features
    expect(screen.getByText(/15GB free storage/)).toBeInTheDocument();
    expect(screen.getByText(/Cross-platform/)).toBeInTheDocument();
    
    // Check Dropbox features
    expect(screen.getByText(/Smart sync/)).toBeInTheDocument();
    expect(screen.getByText(/Team collaboration/)).toBeInTheDocument();
  });

  it('shows loading state during connection test', async () => {
    const { invoke } = await import('@tauri-apps/api/tauri');
    (invoke as any).mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<CloudSyncSettings />);
    
    const icloudCard = screen.getByText('iCloud Drive').closest('div');
    fireEvent.click(icloudCard!);
    
    await waitFor(() => {
      expect(screen.getByText('Testing connection...')).toBeInTheDocument();
    });
  });
});
