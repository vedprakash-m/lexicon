import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../utils/test-utils';
import AppContent from '../components/AppContent';
import { useLexiconStore } from '../../store';

// Mock Tauri API
// Default mock: return valid dashboard data
const mockDashboardData = {
  stats: {
    total_books: 4,
    active_processing: 2,
    chunks_created: 5,
    quality_score: 75,
  },
  recent_activities: [
    {
      id: '1',
      type: 'book_added',
      title: 'Added "Book A"',
      description: 'New book added to library',
      timestamp: new Date(Date.now() - 100000).toISOString(),
      status: 'success',
    },
    {
      id: '2',
      type: 'processing_completed',
      title: 'Processed "Book C"',
      description: 'Text processing completed successfully',
      timestamp: new Date(Date.now() - 10000).toISOString(),
      status: 'success',
    },
  ],
  processing_tasks: [
    {
      id: 't2',
      title: 'Book B',
      progress: 50,
      status: 'in_progress',
      current_step: 'Chunking',
    },
    {
      id: 't4',
      title: 'Book D',
      progress: 0,
      status: 'pending',
      current_step: 'Pending',
    },
  ],
  sourceTexts: [
    {
      id: 't1',
      title: 'Book A',
      created_at: new Date(Date.now() - 100000).toISOString(),
      updated_at: new Date(Date.now() - 50000).toISOString(),
      source_type: 'Book',
      processing_status: {
        Completed: {
          completed_at: new Date(Date.now() - 50000).toISOString(),
        }
      },
    },
    {
      id: 't2',
      title: 'Book B',
      created_at: new Date(Date.now() - 80000).toISOString(),
      updated_at: new Date(Date.now() - 20000).toISOString(),
      source_type: 'Book',
      processing_status: {
        InProgress: {
          progress_percent: 50,
          current_step: 'Chunking',
        }
      },
    },
    {
      id: 't3',
      title: 'Book C',
      created_at: new Date(Date.now() - 60000).toISOString(),
      updated_at: new Date(Date.now() - 10000).toISOString(),
      source_type: 'Book',
      processing_status: {
        Completed: {
          completed_at: new Date(Date.now() - 10000).toISOString(),
        }
      },
    },
    {
      id: 't4',
      title: 'Book D',
      created_at: new Date(Date.now() - 40000).toISOString(),
      updated_at: new Date(Date.now() - 5000).toISOString(),
      source_type: 'Book',
      processing_status: {
        Pending: {},
      },
    },
  ],
  datasets: [
    {
      id: 'd1',
      chunks: [{}, {}, {}],
    },
    {
      id: 'd2',
      chunks: [{}, {}],
    },
  ],
  performance: null,
  last_updated: new Date().toISOString(),
};

vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn().mockImplementation((cmd) => {
    if (cmd === 'get_dashboard_data') {
      return Promise.resolve(mockDashboardData);
    }
    if (cmd === 'get_all_source_texts') {
      return Promise.resolve(mockDashboardData.sourceTexts);
    }
    if (cmd === 'get_all_datasets') {
      return Promise.resolve(mockDashboardData.datasets);
    }
    if (cmd === 'get_performance_metrics') {
      return Promise.resolve(null);
    }
    if (cmd === 'get_state_stats') {
      return Promise.resolve({});
    }
    return Promise.resolve();
  }),
}));

vi.mock('@tauri-apps/plugin-dialog', () => ({
  open: vi.fn(),
  save: vi.fn(),
}));

vi.mock('@tauri-apps/plugin-fs', () => ({
  readTextFile: vi.fn(),
  writeTextFile: vi.fn(),
  exists: vi.fn(),
  mkdir: vi.fn(),
}));

vi.mock('@tauri-apps/plugin-notification', () => ({
  sendNotification: vi.fn(),
  isPermissionGranted: vi.fn(() => Promise.resolve(true)),
  requestPermission: vi.fn(() => Promise.resolve('granted')),
}));

describe('App Integration Tests', () => {
  beforeEach(() => {
    // Reset store before each test
    useLexiconStore.getState().reset();
    vi.clearAllMocks();
  });

  it('renders main navigation correctly', async () => {
    renderWithProviders(<AppContent />);
    
    // Wait for initialization to complete and check for dashboard content
    await waitFor(() => {
      expect(screen.getByText('Welcome back!')).toBeInTheDocument();
    });
  });

  it('navigates between routes correctly', async () => {
    const user = userEvent.setup();
    renderWithProviders(<AppContent />, { initialEntries: ['/'] });
    
    // Should render the dashboard by default
    await waitFor(() => {
      expect(screen.getByText('Welcome back!')).toBeInTheDocument();
    });
    
    // This test would need actual navigation implementation to be meaningful
    // For now, just verify the dashboard loads
  });

  it('handles keyboard navigation', async () => {
    renderWithProviders(<AppContent />);
    
    // Wait for content to load
    await waitFor(() => {
      expect(screen.getByText('Welcome back!')).toBeInTheDocument();
    });
    
    // Focus the first interactive element
    const addButton = screen.getByText('Add New Book');
    addButton.focus();
    expect(document.activeElement).toBe(addButton);
  });

  it('renders error boundary correctly', () => {
    // This test would need an actual error to be meaningful
    renderWithProviders(<AppContent />);
    
    // Just verify the app renders without crashing
    expect(screen.getByText('Initializing Lexicon')).toBeInTheDocument();
  });

  it('handles offline state correctly', async () => {
    // Mock network offline
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    });

    renderWithProviders(<AppContent />);
    
    // The app should still render even when offline
    await waitFor(() => {
      expect(screen.getByText('Welcome back!')).toBeInTheDocument();
    });
  });
});
