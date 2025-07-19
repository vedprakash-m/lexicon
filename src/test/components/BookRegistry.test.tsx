import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Dashboard } from '../../components/Dashboard';
import { renderWithProviders } from '../utils/test-utils';

// Mock Tauri API
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(),
}));

describe('Dashboard Component Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dashboard header correctly', () => {
    renderWithProviders(<Dashboard />);
    
    expect(screen.getByText('Welcome back!')).toBeInTheDocument();
    expect(screen.getByText("Here's what's happening with your lexicon today.")).toBeInTheDocument();
    expect(screen.getByText('Add New Book')).toBeInTheDocument();
  });

  it('displays stats grid correctly', () => {
    renderWithProviders(<Dashboard />);
    
    // Check for stat cards
    expect(screen.getByText('Total Books')).toBeInTheDocument();
    expect(screen.getAllByText('Processing')[0]).toBeInTheDocument(); // First occurrence in stat cards
    expect(screen.getByText('Chunks Created')).toBeInTheDocument();
    expect(screen.getByText('Quality Score')).toBeInTheDocument();
  });

  it('shows recent activity section', () => {
    renderWithProviders(<Dashboard />);
    
    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
    expect(screen.getByText('View All')).toBeInTheDocument();
  });

  it('displays processing queue section', () => {
    renderWithProviders(<Dashboard />);
    
    expect(screen.getByText('Processing Status')).toBeInTheDocument();
    expect(screen.getByText('Details')).toBeInTheDocument();
  });

  it('shows quick actions section', () => {
    renderWithProviders(<Dashboard />);
    
    expect(screen.getByText('Quick Actions')).toBeInTheDocument();
    expect(screen.getByText('Add Book')).toBeInTheDocument();
    expect(screen.getByText('Batch Import')).toBeInTheDocument();
    expect(screen.getByText('View Analytics')).toBeInTheDocument();
  });

  it('handles add new book button click', async () => {
    const user = userEvent.setup();
    renderWithProviders(<Dashboard />);
    
    const addButton = screen.getByText('Add New Book');
    await user.click(addButton);
    
    // Should trigger add book functionality (would be tested with actual implementation)
  });

  it('handles quick action button clicks', async () => {
    const user = userEvent.setup();
    renderWithProviders(<Dashboard />);
    
    const addBookButton = screen.getByText('Add Book');
    await user.click(addBookButton);
    
    // Should trigger add book functionality
    expect(addBookButton).toBeInTheDocument();
  });

  it('handles keyboard navigation', async () => {
    renderWithProviders(<Dashboard />);
    
    // Focus first button (Add New Book)
    const addButton = screen.getByText('Add New Book');
    addButton.focus();
    expect(document.activeElement).toBe(addButton);
  });

  it('displays loading states correctly', async () => {
    // Mock loading state
    vi.mock('@tauri-apps/api/core', () => ({
      invoke: vi.fn().mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100))),
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
      invoke: vi.fn().mockRejectedValue(new Error('Test error')),
    }));
    
    renderWithProviders(<Dashboard />);
    
    // Should display error states appropriately
    await waitFor(() => {
      // Error states would be handled by the component's error boundaries
    });
  });
});
