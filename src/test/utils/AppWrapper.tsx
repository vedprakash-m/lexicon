import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { 
  ThemeProvider, 
  ToastProvider, 
  KeyboardShortcutsProvider,
  TooltipProvider 
} from '../../components/ui';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      staleTime: Infinity,
    },
  },
});

interface AppWrapperProps {
  children: React.ReactNode;
  initialEntries?: string[];
}

/**
 * Test wrapper that provides all the necessary providers for testing components
 * This avoids the router nesting issue by providing its own MemoryRouter
 */
export function AppWrapper({ children, initialEntries = ['/'] }: AppWrapperProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <ThemeProvider defaultTheme="system" storageKey="lexicon-theme">
          <TooltipProvider>
            <ToastProvider>
              <KeyboardShortcutsProvider>
                {children}
              </KeyboardShortcutsProvider>
            </ToastProvider>
          </TooltipProvider>
        </ThemeProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

/**
 * Test wrapper for testing App component specifically
 * This renders the App content without the BrowserRouter
 */
export function AppContentWrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="system" storageKey="lexicon-theme">
        <TooltipProvider>
          <ToastProvider>
            <KeyboardShortcutsProvider>
              {children}
            </KeyboardShortcutsProvider>
          </ToastProvider>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
