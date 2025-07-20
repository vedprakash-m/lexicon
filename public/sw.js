// Lexicon Service Worker
// Production-grade service worker for offline functionality and caching

const CACHE_NAME = 'lexicon-v1.0.0';
const OFFLINE_URL = '/offline.html';

// Core assets to cache on install
const CORE_ASSETS = [
  '/',
  '/offline.html',
  '/index.html',
  '/src/main.tsx',
  '/src/index.css',
  '/src/App.css'
];

// API endpoints that can work offline
const OFFLINE_FALLBACKS = {
  '/api/catalog': '/data/offline-catalog.json',
  '/api/stats': '/data/offline-stats.json',
  '/api/status': '/data/offline-status.json'
};

// Network-first strategy for API calls, cache-first for assets
const CACHE_STRATEGIES = {
  api: 'network-first',
  assets: 'cache-first',
  images: 'cache-first',
  fonts: 'cache-first'
};

// Install event - cache core assets
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Installing');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[ServiceWorker] Caching core assets');
        return cache.addAll(CORE_ASSETS);
      })
      .then(() => {
        // Force activation immediately
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[ServiceWorker] Install failed:', error);
      })
  );
});

// Activate event - cleanup old caches
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activating');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => cacheName !== CACHE_NAME)
            .map((cacheName) => {
              console.log('[ServiceWorker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => {
        // Take control of all clients immediately
        return self.clients.claim();
      })
  );
});

// Fetch event - handle requests with appropriate cache strategy
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip chrome-extension and other non-http protocols
  if (!url.protocol.startsWith('http')) {
    return;
  }
  
  // Determine cache strategy based on request type
  let strategy = 'network-first'; // default
  
  if (url.pathname.startsWith('/api/')) {
    strategy = CACHE_STRATEGIES.api;
  } else if (url.pathname.match(/\.(js|css|woff2?|png|jpg|jpeg|svg|ico)$/)) {
    strategy = CACHE_STRATEGIES.assets;
  }
  
  event.respondWith(
    handleRequest(request, strategy, url)
  );
});

// Handle request with specified strategy
async function handleRequest(request, strategy, url) {
  const cache = await caches.open(CACHE_NAME);
  
  try {
    switch (strategy) {
      case 'cache-first':
        return await cacheFirst(request, cache);
      case 'network-first':
        return await networkFirst(request, cache, url);
      default:
        return await networkFirst(request, cache, url);
    }
  } catch (error) {
    console.error('[ServiceWorker] Request failed:', error);
    return await handleOfflineFallback(request, cache, url);
  }
}

// Cache-first strategy
async function cacheFirst(request, cache) {
  const cachedResponse = await cache.match(request);
  
  if (cachedResponse) {
    // Update cache in background
    updateCacheInBackground(request, cache);
    return cachedResponse;
  }
  
  // Not in cache, fetch from network
  const networkResponse = await fetch(request);
  
  if (networkResponse.ok) {
    cache.put(request, networkResponse.clone());
  }
  
  return networkResponse;
}

// Network-first strategy
async function networkFirst(request, cache, url) {
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Cache successful responses
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    // Network failed, try cache
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // No cache available, handle offline fallback
    throw error;
  }
}

// Update cache in background
async function updateCacheInBackground(request, cache) {
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
  } catch (error) {
    // Silently fail background updates
    console.log('[ServiceWorker] Background update failed:', error.message);
  }
}

// Handle offline fallbacks
async function handleOfflineFallback(request, cache, url) {
  // Check for specific offline fallbacks
  const fallbackUrl = OFFLINE_FALLBACKS[url.pathname];
  
  if (fallbackUrl) {
    const fallbackResponse = await cache.match(fallbackUrl);
    if (fallbackResponse) {
      return fallbackResponse;
    }
  }
  
  // For navigation requests, return offline page
  if (request.mode === 'navigate') {
    const offlineResponse = await cache.match(OFFLINE_URL);
    if (offlineResponse) {
      return offlineResponse;
    }
  }
  
  // Return generic offline response
  return new Response(
    JSON.stringify({
      error: 'Offline',
      message: 'This content is not available offline',
      timestamp: new Date().toISOString()
    }),
    {
      status: 503,
      statusText: 'Service Unavailable',
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
      }
    }
  );
}

// Background sync for processing queue
self.addEventListener('sync', (event) => {
  console.log('[ServiceWorker] Background sync:', event.tag);
  
  if (event.tag === 'process-queue') {
    event.waitUntil(syncProcessingQueue());
  }
});

// Sync processing queue when online
async function syncProcessingQueue() {
  try {
    // Get queued processing jobs from IndexedDB
    const queuedJobs = await getQueuedJobs();
    
    if (queuedJobs.length > 0) {
      console.log(`[ServiceWorker] Syncing ${queuedJobs.length} queued jobs`);
      
      for (const job of queuedJobs) {
        try {
          await fetch('/api/processing/queue', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(job)
          });
          
          // Remove from queue on success
          await removeFromQueue(job.id);
        } catch (error) {
          console.error('[ServiceWorker] Failed to sync job:', job.id, error);
        }
      }
    }
  } catch (error) {
    console.error('[ServiceWorker] Background sync failed:', error);
  }
}

// IndexedDB helpers for offline queue
async function getQueuedJobs() {
  // Implement IndexedDB access for offline queue
  return [];
}

async function removeFromQueue(jobId) {
  // Implement IndexedDB removal
  console.log('[ServiceWorker] Removing job from queue:', jobId);
}

// Push notification handler
self.addEventListener('push', (event) => {
  console.log('[ServiceWorker] Push received');
  
  const options = {
    body: 'Processing job completed',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    tag: 'lexicon-notification',
    data: {
      url: '/processing'
    }
  };
  
  if (event.data) {
    const data = event.data.json();
    options.body = data.message || options.body;
    options.data = { ...options.data, ...data };
  }
  
  event.waitUntil(
    self.registration.showNotification('Lexicon', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  const url = event.notification.data?.url || '/';
  
  event.waitUntil(
    clients.matchAll({ type: 'window' })
      .then((clientList) => {
        // Check if app is already open
        for (const client of clientList) {
          if (client.url.includes(url) && 'focus' in client) {
            return client.focus();
          }
        }
        
        // Open new window if app not open
        if (clients.openWindow) {
          return clients.openWindow(url);
        }
      })
  );
});

// Message handler for communication with main app
self.addEventListener('message', (event) => {
  console.log('[ServiceWorker] Message received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CACHE_UPDATE') {
    // Force cache update for specific resources
    const urls = event.data.urls || [];
    event.waitUntil(updateSpecificCache(urls));
  }
});

// Update specific cache entries
async function updateSpecificCache(urls) {
  const cache = await caches.open(CACHE_NAME);
  
  for (const url of urls) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        await cache.put(url, response);
        console.log('[ServiceWorker] Updated cache for:', url);
      }
    } catch (error) {
      console.error('[ServiceWorker] Failed to update cache for:', url, error);
    }
  }
}

console.log('[ServiceWorker] Service Worker registered and ready');
