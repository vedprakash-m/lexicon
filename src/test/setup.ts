import '@testing-library/jest-dom/vitest'
import { beforeAll, afterEach, afterAll, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import { server } from './mocks/server'

// Shared mock dashboard data for all tests
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
  // Add all keys expected by dashboard code to avoid undefined errors
  books: [],
  collections: [],
  rules: [],
  errors: [],
};

// Start server before all tests
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))

// Reset handlers and cleanup after each test
afterEach(() => {
  server.resetHandlers()
  cleanup()
  vi.clearAllMocks()
})

// Clean up after all tests are done
afterAll(() => server.close())

// Mock Tauri APIs globally
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn().mockImplementation((cmd) => {
    if (cmd === 'get_dashboard_data') {
      // Return all keys, always defined
      return Promise.resolve({
        stats: mockDashboardData.stats,
        recent_activities: mockDashboardData.recent_activities,
        processing_tasks: mockDashboardData.processing_tasks,
        sourceTexts: mockDashboardData.sourceTexts,
        datasets: mockDashboardData.datasets,
        performance: mockDashboardData.performance,
        last_updated: mockDashboardData.last_updated,
        books: mockDashboardData.books,
        collections: mockDashboardData.collections,
        rules: mockDashboardData.rules,
        errors: mockDashboardData.errors,
      });
    }
    if (cmd === 'get_all_source_texts') {
      return Promise.resolve(mockDashboardData.sourceTexts);
    }
    if (cmd === 'get_all_datasets') {
      return Promise.resolve(mockDashboardData.datasets);
    }
    if (cmd === 'get_performance_metrics') {
      return Promise.resolve(mockDashboardData.performance);
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
  message: vi.fn(),
  ask: vi.fn(),
  confirm: vi.fn(),
}));

vi.mock('@tauri-apps/plugin-fs', () => ({
  readTextFile: vi.fn(),
  writeTextFile: vi.fn(),
  readBinaryFile: vi.fn(),
  writeBinaryFile: vi.fn(),
  exists: vi.fn(),
  mkdir: vi.fn(),
  remove: vi.fn(),
  copyFile: vi.fn(),
  rename: vi.fn(),
  readDir: vi.fn(),
  metadata: vi.fn(),
}));

vi.mock('@tauri-apps/plugin-notification', () => ({
  sendNotification: vi.fn(),
  isPermissionGranted: vi.fn(() => Promise.resolve(true)),
  requestPermission: vi.fn(() => Promise.resolve('granted')),
}));

vi.mock('@tauri-apps/plugin-shell', () => ({
  Command: vi.fn(() => ({
    execute: vi.fn(),
    spawn: vi.fn(),
  })),
  open: vi.fn(),
}));

// Mock ResizeObserver for components that use it
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock IntersectionObserver for components that use it
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock matchMedia for responsive components
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock crypto for UUID generation in tests
Object.defineProperty(global, 'crypto', {
  value: {
    randomUUID: vi.fn(() => 'test-uuid-123'),
    getRandomValues: vi.fn((arr) => {
      for (let i = 0; i < arr.length; i++) {
        arr[i] = Math.floor(Math.random() * 256);
      }
      return arr;
    }),
  },
});

// Mock Tauri APIs
declare global {
  var __TAURI__: any
}

global.__TAURI__ = {
  tauri: {
    invoke: vi.fn(),
  },
  fs: {
    readTextFile: vi.fn(),
    writeTextFile: vi.fn(),
    exists: vi.fn(),
    createDir: vi.fn(),
    removeFile: vi.fn(),
  },
  dialog: {
    open: vi.fn(),
    save: vi.fn(),
    message: vi.fn(),
    ask: vi.fn(),
    confirm: vi.fn(),
  },
  notification: {
    sendNotification: vi.fn(),
  },
  shell: {
    open: vi.fn(),
  },
}

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))
