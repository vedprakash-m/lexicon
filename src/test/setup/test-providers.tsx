import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { render } from '@testing-library/react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { KeyboardShortcutsProvider } from '@/components/ui/keyboard-shortcuts';

// Create a test query client with error retries disabled
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      gcTime: Infinity,
    },
    mutations: {
      retry: false,
    },
  },
});

interface TestProvidersProps {
  children: React.ReactNode;
  initialEntries?: string[];
  queryClient?: QueryClient;
}

export const TestProviders: React.FC<TestProvidersProps> = ({ 
  children, 
  initialEntries = ['/'],
  queryClient
}) => {
  const testQueryClient = queryClient || createTestQueryClient();

  return (
    <QueryClientProvider client={testQueryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <TooltipProvider delayDuration={0} skipDelayDuration={0}>
          <KeyboardShortcutsProvider>
            {children}
          </KeyboardShortcutsProvider>
        </TooltipProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

export const renderWithProviders = (
  ui: React.ReactElement,
  options: {
    initialEntries?: string[];
    queryClient?: QueryClient;
  } = {}
) => {
  const { initialEntries, queryClient } = options;
  
  return {
    ...render(ui, {
      wrapper: ({ children }: { children: React.ReactNode }) => (
        <TestProviders 
          initialEntries={initialEntries} 
          queryClient={queryClient}
        >
          {children}
        </TestProviders>
      ),
    }),
    queryClient: queryClient || createTestQueryClient(),
  };
};

// Re-export for convenience
export { createTestQueryClient };
