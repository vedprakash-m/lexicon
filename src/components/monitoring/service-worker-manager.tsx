import React, { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle, Download, Wifi, WifiOff, RefreshCw } from 'lucide-react';
import { Button } from '../ui';
import { cn } from '@/lib/utils';

interface ServiceWorkerManagerProps {
  className?: string;
}

interface ServiceWorkerState {
  registration: ServiceWorkerRegistration | null;
  isOnline: boolean;
  updateAvailable: boolean;
  isInstalling: boolean;
  cacheSize: string;
  lastSync: string;
}

export const ServiceWorkerManager: React.FC<ServiceWorkerManagerProps> = ({ 
  className 
}) => {
  const [state, setState] = useState<ServiceWorkerState>({
    registration: null,
    isOnline: navigator.onLine,
    updateAvailable: false,
    isInstalling: false,
    cacheSize: '0 MB',
    lastSync: 'Never'
  });

  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    initializeServiceWorker();
    setupEventListeners();
    updateCacheInfo();

    return () => {
      cleanupEventListeners();
    };
  }, []);

  const initializeServiceWorker = async () => {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js');
        
        setState(prev => ({ ...prev, registration }));

        // Check for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          
          if (newWorker) {
            setState(prev => ({ ...prev, isInstalling: true }));
            
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                setState(prev => ({ 
                  ...prev, 
                  updateAvailable: true,
                  isInstalling: false 
                }));
              } else if (newWorker.state === 'activated') {
                setState(prev => ({ ...prev, isInstalling: false }));
              }
            });
          }
        });

        // Listen for messages from service worker
        navigator.serviceWorker.addEventListener('message', handleServiceWorkerMessage);

        console.log('✅ Service Worker registered successfully');
      } catch (error) {
        console.error('❌ Service Worker registration failed:', error);
      }
    }
  };

  const setupEventListeners = () => {
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
  };

  const cleanupEventListeners = () => {
    window.removeEventListener('online', handleOnline);
    window.removeEventListener('offline', handleOffline);
    
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.removeEventListener('message', handleServiceWorkerMessage);
    }
  };

  const handleOnline = () => {
    setState(prev => ({ ...prev, isOnline: true }));
    
    // Trigger background sync when coming online
    if (state.registration && 'serviceWorker' in navigator) {
      // Use service worker messaging for background sync
      state.registration.active?.postMessage({ type: 'TRIGGER_SYNC' });
    }
    
    updateLastSync();
  };

  const handleOffline = () => {
    setState(prev => ({ ...prev, isOnline: false }));
  };

  const handleServiceWorkerMessage = (event: MessageEvent) => {
    const { data } = event;
    
    if (data?.type === 'CACHE_UPDATED') {
      updateCacheInfo();
    }
    
    if (data?.type === 'BACKGROUND_SYNC_COMPLETE') {
      updateLastSync();
    }
  };

  const updateCacheInfo = async () => {
    if ('caches' in window) {
      try {
        const cacheNames = await caches.keys();
        let totalSize = 0;
        
        for (const cacheName of cacheNames) {
          const cache = await caches.open(cacheName);
          const requests = await cache.keys();
          
          for (const request of requests) {
            const response = await cache.match(request);
            if (response && response.headers.get('content-length')) {
              totalSize += parseInt(response.headers.get('content-length') || '0');
            }
          }
        }
        
        const sizeInMB = (totalSize / 1024 / 1024).toFixed(1);
        setState(prev => ({ ...prev, cacheSize: `${sizeInMB} MB` }));
      } catch (error) {
        console.error('Failed to calculate cache size:', error);
      }
    }
  };

  const updateLastSync = () => {
    const now = new Date().toLocaleTimeString();
    setState(prev => ({ ...prev, lastSync: now }));
  };

  const handleUpdateApp = () => {
    if (state.registration?.waiting) {
      // Tell the waiting service worker to take over
      state.registration.waiting.postMessage({ type: 'SKIP_WAITING' });
      
      // Reload the page after a brief delay
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    }
  };

  const handleRefreshCache = async () => {
    if (state.registration?.active) {
      // Request cache update from service worker
      state.registration.active.postMessage({
        type: 'CACHE_UPDATE',
        urls: [
          '/',
          '/api/catalog',
          '/api/stats',
          '/api/status'
        ]
      });
      
      // Update local cache info after a delay
      setTimeout(updateCacheInfo, 2000);
    }
  };

  const handleClearCache = async () => {
    if ('caches' in window) {
      try {
        const cacheNames = await caches.keys();
        await Promise.all(cacheNames.map(name => caches.delete(name)));
        
        setState(prev => ({ ...prev, cacheSize: '0 MB' }));
        console.log('✅ Cache cleared successfully');
      } catch (error) {
        console.error('❌ Failed to clear cache:', error);
      }
    }
  };

  if (!('serviceWorker' in navigator)) {
    return (
      <div className={cn("p-4 bg-muted rounded-lg", className)}>
        <div className="flex items-center space-x-2 text-muted-foreground">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm">Service Worker not supported</span>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Connection Status */}
      <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
        <div className="flex items-center space-x-2">
          {state.isOnline ? (
            <Wifi className="h-4 w-4 text-green-500" />
          ) : (
            <WifiOff className="h-4 w-4 text-red-500" />
          )}
          <span className="text-sm font-medium">
            {state.isOnline ? 'Online' : 'Offline'}
          </span>
        </div>
        
        {state.isInstalling && (
          <div className="flex items-center space-x-2 text-blue-500">
            <Download className="h-4 w-4 animate-bounce" />
            <span className="text-sm">Installing update...</span>
          </div>
        )}
      </div>

      {/* Update Available Banner */}
      {state.updateAvailable && (
        <div className="p-3 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Download className="h-4 w-4 text-blue-500" />
              <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                App update available
              </span>
            </div>
            <Button size="sm" onClick={handleUpdateApp}>
              Update Now
            </Button>
          </div>
        </div>
      )}

      {/* Service Worker Details */}
      <div className="space-y-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowDetails(!showDetails)}
          className="w-full justify-between"
        >
          <span>Service Worker Details</span>
          <RefreshCw className={cn(
            "h-4 w-4 transition-transform",
            showDetails && "rotate-180"
          )} />
        </Button>

        {showDetails && (
          <div className="space-y-3 p-3 bg-muted rounded-lg">
            {/* Cache Information */}
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Cache Size:</span>
              <span className="text-sm font-mono">{state.cacheSize}</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Last Sync:</span>
              <span className="text-sm font-mono">{state.lastSync}</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Status:</span>
              <div className="flex items-center space-x-1">
                {state.registration ? (
                  <>
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    <span className="text-sm text-green-600 dark:text-green-400">
                      Active
                    </span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-3 w-3 text-yellow-500" />
                    <span className="text-sm text-yellow-600 dark:text-yellow-400">
                      Loading
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex space-x-2 pt-2">
              <Button
                size="sm"
                variant="outline"
                onClick={handleRefreshCache}
                disabled={!state.isOnline}
              >
                <RefreshCw className="h-3 w-3 mr-1" />
                Refresh Cache
              </Button>
              
              <Button
                size="sm"
                variant="outline"
                onClick={handleClearCache}
              >
                Clear Cache
              </Button>
            </div>

            {/* Offline Features */}
            <div className="pt-2 border-t border-border">
              <p className="text-xs text-muted-foreground mb-2">
                Available offline:
              </p>
              <ul className="text-xs space-y-1 text-muted-foreground">
                <li>• Browse cached library catalog</li>
                <li>• View book details and metadata</li>
                <li>• Access processing history</li>
                <li>• Queue processing jobs for sync</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
