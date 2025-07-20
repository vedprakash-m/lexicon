import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import { useEffect, Suspense, lazy, useState } from 'react';
import { 
  ThemeProvider, 
  ToastProvider, 
  KeyboardShortcutsProvider,
  TooltipProvider 
} from './components/ui';
import { StateManager } from './components/StateManager';
import { AppLayout } from './components/layout';
import { Dashboard } from './components/Dashboard';
import { ComponentShowcase } from './components/ComponentShowcase';
import { TestComponent } from './components/debug/TestComponent';
import { OnboardingProvider, OnboardingManager } from './components/onboarding';
import { 
  CatalogLoading, 
  ProjectLoading, 
  ProcessingLoading, 
  PerformanceLoading,
  RouteLoadingSpinner 
} from './components/ui/loading-states';
import { useRoutePreloader, preloadCriticalRoutes } from './components/ui/route-preloader';
import { usePerformanceMonitor, initializePerformanceMonitoring, PerformanceDebugger } from './components/ui/performance-monitor';
import { ServiceWorkerManager } from './components/monitoring/service-worker-manager';
import { AccessibilityProvider, SkipNavigation, LandmarkNavigation } from './components/accessibility/accessibility-provider';
import { SecurityProvider, SessionLock, useSecurity } from './components/security/security-provider';
import { useLexiconStore } from './store';
import './App.css';

// Lazy load heavy route components for better code splitting
const ProjectManagement = lazy(() => import('./components/project').then(m => ({ default: m.ProjectManagement })));
const ProjectWorkspace = lazy(() => import('./components/project').then(m => ({ default: m.ProjectWorkspace })));
const SourceConfiguration = lazy(() => import('./components/source').then(m => ({ default: m.SourceConfiguration })));
const ScrapingExecution = lazy(() => import('./components/scraping').then(m => ({ default: m.ScrapingExecution })));
const BatchProcessing = lazy(() => import('./components/batch').then(m => ({ default: m.BatchProcessing })));
const AdvancedChunking = lazy(() => import('./components/chunking').then(m => ({ default: m.AdvancedChunking })));
const ExportManager = lazy(() => import('./components/ExportManager').then(m => ({ default: m.ExportManager })));
const IntegratedCatalogInterface = lazy(() => import('./components/catalog/IntegratedCatalogInterface'));
const SimpleSyncBackupManager = lazy(() => import('./components/sync/SimpleSyncBackupManager').then(m => ({ default: m.SimpleSyncBackupManager })));
const PerformanceDashboard = lazy(() => import('./components/performance/PerformanceDashboard').then(m => ({ default: m.PerformanceDashboard })));

// Session Lock Wrapper Component
const SessionLockWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { state } = useSecurity();
  const [showUnlock, setShowUnlock] = useState(false);

  useEffect(() => {
    setShowUnlock(!state.sessionActive);
  }, [state.sessionActive]);

  if (showUnlock) {
    return <SessionLock onUnlock={() => setShowUnlock(false)} />;
  }

  return <>{children}</>;
};

// Main App Content Component
const AppContent: React.FC = () => {
  // Initialize route preloading and performance monitoring within the app context
  useRoutePreloader();
  usePerformanceMonitor();

  return (
    <AppLayout>
      <OnboardingManager>
        <main id="main-content" role="main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/library" element={
              <Suspense fallback={<CatalogLoading />}>
                <IntegratedCatalogInterface />
              </Suspense>
            } />
            <Route path="/projects" element={
              <Suspense fallback={<ProjectLoading />}>
                <ProjectManagement />
              </Suspense>
            } />
            <Route path="/projects/:projectId" element={
              <Suspense fallback={<ProjectLoading />}>
                <ProjectWorkspace />
              </Suspense>
            } />
            <Route path="/sources" element={
              <Suspense fallback={<ProcessingLoading />}>
                <SourceConfiguration />
              </Suspense>
            } />
            <Route path="/scraping" element={
              <Suspense fallback={<ProcessingLoading />}>
                <ScrapingExecution />
              </Suspense>
            } />
            <Route path="/batch" element={
              <Suspense fallback={<ProcessingLoading />}>
                <BatchProcessing />
              </Suspense>
            } />
            <Route path="/chunking" element={
              <Suspense fallback={<ProcessingLoading />}>
                <AdvancedChunking />
              </Suspense>
            } />
            <Route path="/export" element={
              <Suspense fallback={<ProcessingLoading />}>
                <ExportManager chunks={[]} />
              </Suspense>
            } />
            <Route path="/sync" element={
              <Suspense fallback={<ProcessingLoading />}>
                <SimpleSyncBackupManager />
              </Suspense>
            } />
            <Route path="/backups" element={
              <Suspense fallback={<ProcessingLoading />}>
                <SimpleSyncBackupManager />
              </Suspense>
            } />
            <Route path="/monitoring" element={
              <Suspense fallback={<PerformanceLoading />}>
                <PerformanceDashboard />
              </Suspense>
            } />
            <Route path="/performance" element={
              <Suspense fallback={<PerformanceLoading />}>
                <PerformanceDashboard />
              </Suspense>
            } />
            <Route path="/showcase" element={<ComponentShowcase />} />
            <Route path="/test" element={<TestComponent />} />
            <Route path="*" element={
              <div className="p-6">
                <h1>Route not found: {window.location.pathname}</h1>
                <p>Available routes:</p>
                <ul className="mt-4 space-y-1">
                  <li><a href="#/" className="text-blue-500 hover:underline">/</a> - Dashboard</li>
                  <li><a href="#/library" className="text-blue-500 hover:underline">/library</a> - Enhanced Catalog</li>
                  <li><a href="#/projects" className="text-blue-500 hover:underline">/projects</a> - Collections</li>
                  <li><a href="#/sources" className="text-blue-500 hover:underline">/sources</a> - Source Configuration</li>
                  <li><a href="#/scraping" className="text-blue-500 hover:underline">/scraping</a> - Scraping Jobs</li>
                  <li><a href="#/batch" className="text-blue-500 hover:underline">/batch</a> - Batch Processing</li>
                  <li><a href="#/chunking" className="text-blue-500 hover:underline">/chunking</a> - Advanced Chunking</li>
                  <li><a href="#/export" className="text-blue-500 hover:underline">/export</a> - Export Manager</li>
                  <li><a href="#/sync" className="text-blue-500 hover:underline">/sync</a> - Sync & Backup</li>
                  <li><a href="#/monitoring" className="text-blue-500 hover:underline">/monitoring</a> - Performance Monitor</li>
                  <li><a href="#/showcase" className="text-blue-500 hover:underline">/showcase</a> - Component Showcase</li>
                </ul>
              </div>
            } />
          </Routes>
        </main>
      </OnboardingManager>
      
      {/* Development Tools */}
      {process.env.NODE_ENV === 'development' && <PerformanceDebugger />}
      
      {/* Service Worker Manager in Settings */}
      <div className="hidden">
        <ServiceWorkerManager />
      </div>
    </AppLayout>
  );
};

function App() {
  console.log('App.tsx: Rendering full Lexicon App');
  
  const { loadSettings } = useLexiconStore();

  // Load settings from backend on app startup
  useEffect(() => {
    loadSettings().catch(console.error);
    
    // Initialize performance monitoring
    initializePerformanceMonitoring();
    
    // Preload critical routes after initial load
    setTimeout(() => {
      preloadCriticalRoutes();
    }, 1000);
  }, [loadSettings]);
  
  return (
    <AccessibilityProvider>
      <SecurityProvider>
        <ThemeProvider defaultTheme="system" storageKey="lexicon-theme">
          <TooltipProvider>
            <ToastProvider>
              <Router>
                <KeyboardShortcutsProvider>
                  <OnboardingProvider>
                    <StateManager>
                      {/* Accessibility Navigation Aids */}
                      <SkipNavigation />
                      <LandmarkNavigation />
                      
                      {/* Session Security Check */}
                      <SessionLockWrapper>
                        <AppContent />
                      </SessionLockWrapper>
                    </StateManager>
                  </OnboardingProvider>
                </KeyboardShortcutsProvider>
              </Router>
            </ToastProvider>
          </TooltipProvider>
        </ThemeProvider>
      </SecurityProvider>
    </AccessibilityProvider>
  );
}

export default App;
