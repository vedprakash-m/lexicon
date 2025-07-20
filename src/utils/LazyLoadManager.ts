import React, { ComponentType, lazy, LazyExoticComponent } from 'react';

export type LoadingState = 'idle' | 'loading' | 'loaded' | 'error';

interface LazyComponentConfig {
  loader: () => Promise<{ default: ComponentType<any> }>;
  loadingState: LoadingState;
  component: LazyExoticComponent<ComponentType<any>> | null;
  preloadTrigger?: 'hover' | 'viewport' | 'manual';
}

export class LazyLoadManager {
  private static instance: LazyLoadManager;
  private components: Map<string, LazyComponentConfig> = new Map();
  private preloadObserver: IntersectionObserver | null = null;
  
  private constructor() {
    this.initializePreloadObserver();
  }
  
  static getInstance(): LazyLoadManager {
    if (!LazyLoadManager.instance) {
      LazyLoadManager.instance = new LazyLoadManager();
    }
    return LazyLoadManager.instance;
  }

  registerLazyComponent(
    name: string, 
    loader: () => Promise<{ default: ComponentType<any> }>,
    preloadTrigger: 'hover' | 'viewport' | 'manual' = 'manual'
  ): LazyExoticComponent<ComponentType<any>> {
    if (this.components.has(name)) {
      const config = this.components.get(name)!;
      if (config.component) {
        return config.component;
      }
    }
    
    const component = lazy(loader);
    
    this.components.set(name, {
      loader,
      loadingState: 'idle',
      component,
      preloadTrigger
    });
    
    return component;
  }

  async preloadComponent(name: string): Promise<void> {
    if (!this.components.has(name)) {
      throw new Error(`Component ${name} not registered for lazy loading`);
    }
    
    const config = this.components.get(name)!;
    if (config.loadingState === 'loaded' || config.loadingState === 'loading') {
      return;
    }
    
    try {
      this.components.set(name, {
        ...config,
        loadingState: 'loading'
      });
      
      await config.loader();
      
      this.components.set(name, {
        ...config,
        loadingState: 'loaded'
      });
    } catch (error) {
      this.components.set(name, {
        ...config,
        loadingState: 'error'
      });
      console.error(`Failed to preload component ${name}:`, error);
      throw error;
    }
  }

  private initializePreloadObserver(): void {
    if (typeof window === 'undefined' || !('IntersectionObserver' in window)) {
      return;
    }

    this.preloadObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const componentName = entry.target.getAttribute('data-preload-component');
            if (componentName) {
              this.preloadComponent(componentName).catch(console.error);
              this.preloadObserver?.unobserve(entry.target);
            }
          }
        });
      },
      {
        rootMargin: '50px'
      }
    );
  }

  getLoadingState(name: string): LoadingState {
    if (!this.components.has(name)) {
      return 'idle';
    }
    
    return this.components.get(name)!.loadingState;
  }
}