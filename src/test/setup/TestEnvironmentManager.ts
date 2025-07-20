import { AsyncTestUtils } from '../utils/AsyncTestUtils';
import { vi } from 'vitest';

export class TestEnvironmentManager {
  private static instance: TestEnvironmentManager;
  private mocks: Array<{ restore: () => void }> = [];
  
  private constructor() {
    this.setupGlobalMocks();
  }
  
  static getInstance(): TestEnvironmentManager {
    if (!TestEnvironmentManager.instance) {
      TestEnvironmentManager.instance = new TestEnvironmentManager();
    }
    return TestEnvironmentManager.instance;
  }

  /**
   * Set up global mocks needed for all tests
   */
  private setupGlobalMocks(): void {
    // Mock ResizeObserver
    if (!window.ResizeObserver) {
      window.ResizeObserver = class ResizeObserver {
        observe() {}
        unobserve() {}
        disconnect() {}
      };
    }

    // Mock IntersectionObserver
    if (!window.IntersectionObserver) {
      window.IntersectionObserver = class IntersectionObserver {
        observe() {}
        unobserve() {}
        disconnect() {}
        takeRecords() { return []; }
        root = null;
        rootMargin = '';
        thresholds = [];
      } as any;
    }

    // Mock matchMedia
    if (!window.matchMedia) {
      window.matchMedia = (query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: () => {},
        removeListener: () => {},
        addEventListener: () => {},
        removeEventListener: () => {},
        dispatchEvent: () => true,
      });
    }

    // Mock Tauri API if needed
    if (!(window as any).__TAURI__) {
      (window as any).__TAURI__ = {
        invoke: vi.fn().mockResolvedValue({}),
        fs: {
          readTextFile: vi.fn().mockResolvedValue(''),
          writeTextFile: vi.fn().mockResolvedValue(undefined),
          readDir: vi.fn().mockResolvedValue([]),
          createDir: vi.fn().mockResolvedValue(undefined),
        },
        dialog: {
          open: vi.fn().mockResolvedValue(null),
          save: vi.fn().mockResolvedValue(null),
        },
        notification: {
          sendNotification: vi.fn().mockResolvedValue(undefined),
        },
        shell: {
          open: vi.fn().mockResolvedValue(undefined),
        }
      };
    }
  }

  /**
   * Mock a Tauri command for the duration of a test
   */
  mockTauriCommand<T>(
    commandName: string,
    mockImplementation: (...args: any[]) => Promise<T>
  ): void {
    const mock = AsyncTestUtils.mockTauriCommand(commandName, mockImplementation);
    this.mocks.push(mock);
  }

  /**
   * Clean up all mocks created during testing
   */
  cleanup(): void {
    this.mocks.forEach(mock => mock.restore());
    this.mocks = [];
  }

  /**
   * Create an isolated test environment
   */
  createIsolatedEnvironment(): { cleanup: () => void } {
    // Store original document body
    const originalBody = document.body.innerHTML;
    
    // Create isolated container
    const container = document.createElement('div');
    container.id = 'test-container';
    document.body.appendChild(container);
    
    return {
      cleanup: () => {
        // Restore original body
        document.body.innerHTML = originalBody;
        // Clean up mocks
        this.cleanup();
      }
    };
  }
}