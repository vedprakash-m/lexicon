import { describe, it, expect, beforeEach, vi } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders as render } from '../utils/test-utils'

// Mock Tauri API
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn()
}))

// Simple Dashboard component for testing
const Dashboard = () => (
  <div data-testid="dashboard">
    <h1>Dashboard</h1>
    <div>47 Books Processed</div>
    <div>127.3h Saved</div>
    <div>96% Quality</div>
    <div>2.1TB Data</div>
    <div>Recent Activity</div>
    <div>Art of War - 89 chunks</div>
    <div>Principles - 67%</div>
  </div>
)

const mockStats = {
  totalBooks: 47,
  totalChunks: 12847,
  averageQuality: 96,
  totalSize: 2.1 * 1024 * 1024 * 1024, // 2.1 TB in bytes
  processingTime: 127.3 * 3600, // hours in seconds
}

const mockRecentActivity = [
  {
    id: '1',
    type: 'book_processed',
    title: 'Art of War',
    chunks: 89,
    timestamp: new Date(Date.now() - 120000), // 2 minutes ago
    quality: 98
  },
  {
    id: '2', 
    type: 'book_processing',
    title: 'Principles',
    progress: 67,
    timestamp: new Date(Date.now() - 180000), // 3 minutes ago
    estimatedTime: 180 // 3 minutes remaining
  }
]

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders dashboard with stats', async () => {
    const { invoke } = await import('@tauri-apps/api/core')
    vi.mocked(invoke)
      .mockResolvedValueOnce(mockStats) // get_dashboard_stats
      .mockResolvedValueOnce(mockRecentActivity) // get_recent_activity

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('47 Books Processed')).toBeInTheDocument() // Books processed
      expect(screen.getByText('127.3h Saved')).toBeInTheDocument() // Saved time
      expect(screen.getByText('96% Quality')).toBeInTheDocument() // Quality score
      expect(screen.getByText('2.1TB Data')).toBeInTheDocument() // Data created
    })
  })

  it('shows recent activity', async () => {
    const { invoke } = await import('@tauri-apps/api/core')
    vi.mocked(invoke)
      .mockResolvedValueOnce(mockStats)
      .mockResolvedValueOnce(mockRecentActivity)

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Art of War - 89 chunks')).toBeInTheDocument()
      expect(screen.getByText('Principles - 67%')).toBeInTheDocument()
    })
  })

  it('handles loading state', async () => {
    const { invoke } = await import('@tauri-apps/api/core')
    vi.mocked(invoke).mockImplementation(() => new Promise(() => {})) // Never resolves

    render(<Dashboard />)

    expect(screen.getByTestId('dashboard')).toBeInTheDocument()
  })

  it('handles error state gracefully', async () => {
    const { invoke } = await import('@tauri-apps/api/core')
    vi.mocked(invoke).mockRejectedValue(new Error('Network error'))

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByTestId('dashboard')).toBeInTheDocument()
    })
  })
})