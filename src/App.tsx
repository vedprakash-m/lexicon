import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, ToastProvider } from './components/ui';
import { StateManager } from './components/StateManager';
import { AppLayout } from './components/layout';
import { Dashboard } from './components/Dashboard';
import { ComponentShowcase } from './components/ComponentShowcase';
import { ProjectManagement } from './components/project';
import { SourceConfiguration } from './components/source';
import { ScrapingExecution } from './components/scraping';
import { BatchProcessing } from './components/batch';
import { AdvancedChunking } from './components/chunking';
import './App.css';

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="lexicon-theme">
      <ToastProvider>
        <StateManager>
          <Router>
            <AppLayout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/projects" element={<ProjectManagement />} />
                <Route path="/sources" element={<SourceConfiguration />} />
                <Route path="/scraping" element={<ScrapingExecution />} />
                <Route path="/batch" element={<BatchProcessing />} />
                <Route path="/chunking" element={<AdvancedChunking />} />
                <Route path="/showcase" element={<ComponentShowcase />} />
              </Routes>
            </AppLayout>
          </Router>
        </StateManager>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;
