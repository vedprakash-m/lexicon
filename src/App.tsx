import { HashRouter as Router, Routes, Route } from 'react-router-dom';
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
import { ProjectManagement } from './components/project';
import { ProjectWorkspace } from './components/project';
import { TestComponent } from './components/debug/TestComponent';
import { SourceConfiguration } from './components/source';
import { ScrapingExecution } from './components/scraping';
import { BatchProcessing } from './components/batch';
import { AdvancedChunking } from './components/chunking';
import { ExportManager } from './components/ExportManager';
import IntegratedCatalogInterface from './components/catalog/IntegratedCatalogInterface';
import { SimpleSyncBackupManager } from './components/sync/SimpleSyncBackupManager';
import { PerformanceDashboard } from './components/performance/PerformanceDashboard';
import { OnboardingProvider, OnboardingManager } from './components/onboarding';
// import { CacheManager } from './components/cache';
import './App.css';

function App() {
  console.log('App.tsx: Rendering full Lexicon App');
  
  try {
    return (
      <ThemeProvider defaultTheme="system" storageKey="lexicon-theme">
        <TooltipProvider>
        <ToastProvider>
          <Router>
            <KeyboardShortcutsProvider>
              <OnboardingProvider>
                <StateManager>
                  <AppLayout>
                    <OnboardingManager>
                      <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/library" element={<IntegratedCatalogInterface />} />
                        <Route path="/projects" element={<ProjectManagement />} />
                        <Route path="/projects/:projectId" element={<ProjectWorkspace />} />
                        <Route path="/sources" element={<SourceConfiguration />} />
                        <Route path="/scraping" element={<ScrapingExecution />} />
                        <Route path="/batch" element={<BatchProcessing />} />
                        <Route path="/chunking" element={<AdvancedChunking />} />
                        <Route path="/export" element={<ExportManager chunks={[]} />} />
                        <Route path="/sync" element={<SimpleSyncBackupManager />} />
                        <Route path="/performance" element={<PerformanceDashboard />} />
                        {/* <Route path="/cache" element={<CacheManager />} /> */}
                        <Route path="/showcase" element={<ComponentShowcase />} />
                        <Route path="*" element={<div className="p-6"><h1>Route not found: {window.location.pathname}</h1><p>Available routes:</p><ul><li>/</li><li>/projects</li><li>/projects/:projectId</li></ul></div>} />
                      </Routes>
                    </OnboardingManager>
                  </AppLayout>
                </StateManager>
              </OnboardingProvider>
            </KeyboardShortcutsProvider>
          </Router>
        </ToastProvider>
      </TooltipProvider>
    </ThemeProvider>
    );
  } catch (error) {
    console.error('App.tsx: Error rendering app:', error);
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <h1>Error Loading Lexicon</h1>
        <p>An error occurred while loading the application.</p>
        <pre>{String(error)}</pre>
      </div>
    );
  }
}

export default App;
