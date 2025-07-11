import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
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
  return (
    <ThemeProvider defaultTheme="system" storageKey="lexicon-theme">
      <TooltipProvider>
        <ToastProvider>
          <KeyboardShortcutsProvider>
            <OnboardingProvider>
              <StateManager>
                <Router>
                  <AppLayout>
                    <OnboardingManager>
                      <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/library" element={<IntegratedCatalogInterface />} />
                        <Route path="/projects" element={<ProjectManagement />} />
                        <Route path="/sources" element={<SourceConfiguration />} />
                        <Route path="/scraping" element={<ScrapingExecution />} />
                        <Route path="/batch" element={<BatchProcessing />} />
                        <Route path="/chunking" element={<AdvancedChunking />} />
                        <Route path="/export" element={<ExportManager chunks={[]} />} />
                        <Route path="/sync" element={<SimpleSyncBackupManager />} />                <Route path="/performance" element={<PerformanceDashboard />} />
                    {/* <Route path="/cache" element={<CacheManager />} /> */}
                    <Route path="/showcase" element={<ComponentShowcase />} />
                      </Routes>
                    </OnboardingManager>
                  </AppLayout>
                </Router>
              </StateManager>
            </OnboardingProvider>
          </KeyboardShortcutsProvider>
        </ToastProvider>
      </TooltipProvider>
    </ThemeProvider>
  );
}

export default App;
