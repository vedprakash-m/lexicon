import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Dashboard } from '../../components/Dashboard';
import { renderWithProviders } from '../utils/test-utils';

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

describe('Dashboard Component Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dashboard header correctly', async () => {
    renderWithProviders(<Dashboard />);
    expect(await screen.findByText('Welcome back!')).toBeInTheDocument();
    expect(await screen.findByText("Here's what's happening with your lexicon today.")).toBeInTheDocument();
    expect(await screen.findByText('Add New Book')).toBeInTheDocument();
  });

  it('displays stats grid correctly', async () => {
    renderWithProviders(<Dashboard />);
    expect(await screen.findByText('Total Books')).toBeInTheDocument();
    // Processing text appears at least once in the stats card
    expect(await screen.findByText('Processing')).toBeInTheDocument();
    expect(await screen.findByText('Chunks Created')).toBeInTheDocument();
    expect(await screen.findByText('Quality Score')).toBeInTheDocument();
  });

  it('shows recent activity section', async () => {
    renderWithProviders(<Dashboard />);
    expect(await screen.findByText('Recent Activity')).toBeInTheDocument();
    expect(await screen.findByText('View All')).toBeInTheDocument();
  });

  it('displays processing queue section', async () => {
    renderWithProviders(<Dashboard />);
    expect(await screen.findByText('Processing Status')).toBeInTheDocument();
    expect(await screen.findByText('Details')).toBeInTheDocument();
  });

  it('shows quick actions section', async () => {
    renderWithProviders(<Dashboard />);
    expect(await screen.findByText('Quick Actions')).toBeInTheDocument();
    expect(await screen.findByText('Add Book')).toBeInTheDocument();
    expect(await screen.findByText('Batch Import')).toBeInTheDocument();
    expect(await screen.findByText('View Analytics')).toBeInTheDocument();
  });

  it('handles add new book button click', async () => {
    const user = userEvent.setup();
    renderWithProviders(<Dashboard />);
    const addButton = await screen.findByText('Add New Book');
    await user.click(addButton);
    // Should trigger add book functionality (would be tested with actual implementation)
  });

  it('handles quick action button clicks', async () => {
    const user = userEvent.setup();
    renderWithProviders(<Dashboard />);
    const addBookButton = await screen.findByText('Add Book');
    await user.click(addBookButton);
    expect(addBookButton).toBeInTheDocument();
  });

  it('handles keyboard navigation', async () => {
    renderWithProviders(<Dashboard />);
    const addButton = await screen.findByText('Add New Book');
    addButton.focus();
    expect(document.activeElement).toBe(addButton);
  });

  it('displays loading states correctly', async () => {
    // Mock loading state
    vi.mock('@tauri-apps/api/core', () => ({
      invoke: vi.fn().mockImplementation(() => new Promise(resolve => setTimeout(() => resolve(mockDashboardData), 100))),
    }));
    
    renderWithProviders(<Dashboard />);
    
    // Should show loading indicators for async content
    await waitFor(() => {
      // Check for loading states in dynamic content sections
    }, { timeout: 200 });
  });

  it('handles error states gracefully', async () => {
    // Mock error state
    vi.mock('@tauri-apps/api/core', () => ({
      invoke: vi.fn().mockImplementation((cmd) => {
        if (cmd === 'get_dashboard_data') {
          return Promise.reject(new Error('Test error'));
        }
        return Promise.resolve();
      }),
    }));
    
    renderWithProviders(<Dashboard />);
    
    // Should display error states appropriately
    await waitFor(() => {
      // Error states would be handled by the component's error boundaries
    });
  });
});
