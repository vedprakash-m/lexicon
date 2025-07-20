import { TestEnvironmentManager } from './setup/TestEnvironmentManager';
import { beforeAll, afterEach } from 'vitest';
import '@testing-library/jest-dom';

// Set up global test environment before all tests
beforeAll(() => {
  TestEnvironmentManager.getInstance();
});

// Clean up after each test
afterEach(() => {
  TestEnvironmentManager.getInstance().cleanup();
});

// Configure Jest/Vitest globals
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

global.IntersectionObserver = class IntersectionObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords() { return []; }
  root = null;
  rootMargin = '';
  thresholds = [];
} as any;