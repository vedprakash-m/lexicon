import { Routes, Route } from 'react-router-dom';
import { StateManager } from '../../components/StateManager';
import { AppLayout } from '../../components/layout';
import { Dashboard } from '../../components/Dashboard';

/**
 * Simplified App content for testing - only includes essential routes
 */
function AppContent() {
  return (
    <StateManager>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/library" element={<div>Library</div>} />
          <Route path="/projects" element={<div>Projects</div>} />
          <Route path="/sources" element={<div>Sources</div>} />
          <Route path="/scraping" element={<div>Scraping</div>} />
          <Route path="/batch" element={<div>Batch</div>} />
          <Route path="/chunking" element={<div>Chunking</div>} />
          <Route path="/export" element={<div>Export</div>} />
          <Route path="/sync" element={<div>Sync</div>} />
          <Route path="/performance" element={<div>Performance</div>} />
          <Route path="/showcase" element={<div>Showcase</div>} />
        </Routes>
      </AppLayout>
    </StateManager>
  );
}

export default AppContent;
