import { ReactNode, useState, useEffect } from 'react';
import { AppSidebar } from './AppSidebar';
import { AppHeader } from './AppHeader';
import { StatusBar } from './StatusBar';
import { CommandPalette } from '../ui/command-palette';
import { SimpleHelpSystem } from '../ui/simple-help-system';
import { SkipNavigation } from '../accessibility/SkipNavigation';
import { LiveRegion, useScreenReaderAnnouncement } from '../../lib/accessibility';

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [showHelpSystem, setShowHelpSystem] = useState(false);
  const { announcement } = useScreenReaderAnnouncement();

  // Listen for global events to open command palette and help
  useEffect(() => {
    const handleOpenCommandPalette = () => setShowCommandPalette(true);
    const handleOpenHelp = () => setShowHelpSystem(true);

    window.addEventListener('lexicon:open-command-palette', handleOpenCommandPalette);
    window.addEventListener('lexicon:open-help', handleOpenHelp);

    return () => {
      window.removeEventListener('lexicon:open-command-palette', handleOpenCommandPalette);
      window.removeEventListener('lexicon:open-help', handleOpenHelp);
    };
  }, []);

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Skip navigation for keyboard users */}
      <SkipNavigation />
      
      {/* Live region for screen reader announcements */}
      <LiveRegion priority="polite" className="sr-only">
        {announcement}
      </LiveRegion>
      
      {/* Header */}
      <AppHeader />
      
      {/* Main content area with sidebar */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <AppSidebar data-tour="sidebar" />
        
        {/* Main content */}
        <main 
          id="main-content"
          className="flex-1 overflow-auto"
          role="main"
          aria-label="Main content"
          tabIndex={-1}
          data-tour="workspace"
        >
          {children}
        </main>
      </div>
      
      {/* Status bar */}
      <StatusBar />

      {/* Global UI Components */}
      <CommandPalette 
        isOpen={showCommandPalette} 
        onClose={() => setShowCommandPalette(false)}
        data-tour="command-palette"
      />
      
      <SimpleHelpSystem 
        isOpen={showHelpSystem} 
        onClose={() => setShowHelpSystem(false)} 
      />
    </div>
  );
}
