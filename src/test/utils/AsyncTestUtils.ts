import { act } from '@testing-library/react';
import { vi } from 'vitest';

export class AsyncTestUtils {
  /**
   * Enhanced waitFor with better error messages and timeout handling
   */
  static async waitFor(
    callback: () => boolean | Promise<boolean>,
    options: { timeout?: number; interval?: number; errorMessage?: string } = {}
  ): Promise<void> {
    const { 
      timeout = 5000, 
      interval = 50,
      errorMessage = 'Timed out waiting for condition'
    } = options;
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      try {
        const result = await callback();
        if (result) return;
      } catch (e) {
        // Continue trying until timeout
      }
      await new Promise(resolve => setTimeout(resolve, interval));
    }
    throw new Error(`${errorMessage} (waited ${timeout}ms)`);
  }

  /**
   * Wait for a specific element to appear in the DOM
   */
  static async waitForElement(
    selector: string,
    options: { timeout?: number; errorMessage?: string } = {}
  ): Promise<HTMLElement> {
    const { 
      timeout = 5000,
      errorMessage = `Element not found: ${selector}`
    } = options;
    let element: HTMLElement | null = null;
    
    await this.waitFor(
      () => {
        element = document.querySelector(selector);
        return !!element;
      },
      { timeout, errorMessage }
    );
    return element as HTMLElement;
  }

  /**
   * Wait for a React state change to occur
   */
  static async waitForStateChange<T>(
    getValue: () => T,
    predicate: (value: T) => boolean,
    options: { timeout?: number; errorMessage?: string } = {}
  ): Promise<T> {
    const { 
      timeout = 5000,
      errorMessage = 'State did not change to expected value'
    } = options;
    let currentValue: T;
    
    await this.waitFor(
      () => {
        currentValue = getValue();
        return predicate(currentValue);
      },
      { timeout, errorMessage }
    );
    return currentValue!;
  }

  /**
   * Flush all pending promises in the JavaScript event queue
   */
  static async flushPromises(): Promise<void> {
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });
  }

  /**
   * Mock a Tauri command with automatic cleanup
   */
  static mockTauriCommand<T>(
    commandName: string,
    mockImplementation: (...args: any[]) => Promise<T>
  ): { restore: () => void } {
    const originalInvoke = (window as any).__TAURI__?.invoke;
    
    (window as any).__TAURI__ = {
      ...(window as any).__TAURI__,
      invoke: vi.fn().mockImplementation(async (cmd: string, ...args: any[]) => {
        if (cmd === commandName) {
          return mockImplementation(...args);
        }
        return originalInvoke ? originalInvoke(cmd, ...args) : Promise.reject(`Command ${cmd} not mocked`);
      })
    };
    
    return {
      restore: () => {
        if (originalInvoke) {
          (window as any).__TAURI__.invoke = originalInvoke;
        }
      }
    };
  }
}