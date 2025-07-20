/**
 * Route Preloader
 * 
 * Intelligent preloading of likely navigation routes to improve perceived performance.
 * Uses intersection observer and user interaction patterns to predict and preload routes.
 */

import { useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';

// Route preloading mappings - define likely next routes based on current route
const ROUTE_PRELOAD_MAP: Record<string, string[]> = {
  '/': ['/library', '/projects'], // From dashboard, users likely go to library or projects
  '/library': ['/projects', '/export'], // From library, users might manage projects or export
  '/projects': ['/library', '/batch', '/chunking'], // From projects, users might process content
  '/batch': ['/chunking', '/export'], // Processing workflow
  '/chunking': ['/export', '/performance'], // After chunking, export or check performance
  '/export': ['/library', '/performance'], // After export, back to library or check performance
  '/scraping': ['/batch', '/sources'], // Scraping leads to processing
  '/sources': ['/scraping', '/batch'], // Source config leads to scraping/processing
  '/performance': ['/library', '/projects'], // Performance review back to main features
  '/sync': ['/library', '/projects'], // Sync management back to content
};

// Preload functions for each lazy route
const ROUTE_PRELOADERS: Record<string, () => Promise<any>> = {
  '/library': () => import('../catalog/IntegratedCatalogInterface'),
  '/projects': () => import('../project').then(m => m.ProjectManagement),
  '/batch': () => import('../batch').then(m => m.BatchProcessing),
  '/chunking': () => import('../chunking').then(m => m.AdvancedChunking),
  '/export': () => import('../ExportManager'),
  '/scraping': () => import('../scraping').then(m => m.ScrapingExecution),
  '/sources': () => import('../source').then(m => m.SourceConfiguration),
  '/performance': () => import('../performance/PerformanceDashboard'),
  '/sync': () => import('../sync/SimpleSyncBackupManager'),
};

// Track preloaded routes to avoid duplicate requests
const preloadedRoutes = new Set<string>();

// Preload a specific route
const preloadRoute = async (route: string): Promise<void> => {
  if (preloadedRoutes.has(route) || !ROUTE_PRELOADERS[route]) {
    return;
  }

  try {
    preloadedRoutes.add(route);
    await ROUTE_PRELOADERS[route]();
    console.log(`🚀 Preloaded route: ${route}`);
  } catch (error) {
    console.warn(`Failed to preload route ${route}:`, error);
    preloadedRoutes.delete(route); // Allow retry
  }
};

// Main preloader hook
export const useRoutePreloader = () => {
  const location = useLocation();

  const preloadLikelyRoutes = useCallback(async () => {
    const currentPath = location.pathname;
    const likelyRoutes = ROUTE_PRELOAD_MAP[currentPath] || [];
    
    // Preload likely next routes with a small delay to not interfere with current route loading
    setTimeout(() => {
      likelyRoutes.forEach(route => {
        preloadRoute(route);
      });
    }, 100);
  }, [location.pathname]);

  useEffect(() => {
    preloadLikelyRoutes();
  }, [preloadLikelyRoutes]);
};

// Navigation hint preloader - preloads on hover/focus of navigation elements
export const useNavigationPreloader = () => {
  const preloadOnHover = useCallback((targetRoute: string) => {
    return {
      onMouseEnter: () => preloadRoute(targetRoute),
      onFocus: () => preloadRoute(targetRoute),
    };
  }, []);

  return { preloadOnHover };
};

// Intersection observer preloader for preloading routes when navigation becomes visible
export const useVisibilityPreloader = (routes: string[]) => {
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const route = entry.target.getAttribute('data-preload-route');
            if (route) {
              preloadRoute(route);
            }
          }
        });
      },
      { threshold: 0.1 }
    );

    // Observe navigation elements
    const navElements = document.querySelectorAll('[data-preload-route]');
    navElements.forEach(el => observer.observe(el));

    return () => observer.disconnect();
  }, [routes]);
};

// Priority preloader - immediately preloads critical routes
export const preloadCriticalRoutes = () => {
  const criticalRoutes = ['/library', '/projects']; // Most commonly accessed routes
  criticalRoutes.forEach(route => {
    // Preload after a short delay to allow the current page to finish loading
    setTimeout(() => preloadRoute(route), 500);
  });
};

export default {
  useRoutePreloader,
  useNavigationPreloader,
  useVisibilityPreloader,
  preloadCriticalRoutes,
  preloadRoute,
};
