import { ReactNode } from 'react';
import { AppSidebar } from './AppSidebar';
import { AppHeader } from './AppHeader';
import { StatusBar } from './StatusBar';

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <AppHeader />
      
      {/* Main content area with sidebar */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <AppSidebar />
        
        {/* Main content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
      
      {/* Status bar */}
      <StatusBar />
    </div>
  );
}
