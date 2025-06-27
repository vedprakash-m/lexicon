import React, { useEffect, useState } from 'react';
import { useLexiconStore, useUIState } from '../store';
import { StateSyncService } from '../store/sync';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';

interface StateManagerProps {
  children: React.ReactNode;
}

export const StateManager: React.FC<StateManagerProps> = ({ children }) => {
  const [isInitializing, setIsInitializing] = useState(true);
  const [initializationStep, setInitializationStep] = useState('');
  const [initializationProgress, setInitializationProgress] = useState(0);
  const [initializationError, setInitializationError] = useState<string | null>(null);
  
  const { error, isLoading } = useUIState();
  const { loadState, saveState } = useLexiconStore();

  useEffect(() => {
    let mounted = true;

    const initializeStateManagement = async () => {
      try {
        setInitializationStep('Loading persisted state...');
        setInitializationProgress(20);
        await loadState();

        if (!mounted) return;

        setInitializationStep('Initializing state synchronization...');
        setInitializationProgress(50);
        const syncService = StateSyncService.getInstance();
        await syncService.initialize();

        if (!mounted) return;

        setInitializationStep('Setting up auto-save...');
        setInitializationProgress(80);
        
        // Set up auto-save on window beforeunload
        const handleBeforeUnload = async () => {
          try {
            await saveState();
            await syncService.saveToBackend();
          } catch (error) {
            console.error('Failed to save state on exit:', error);
          }
        };

        window.addEventListener('beforeunload', handleBeforeUnload);

        setInitializationStep('Complete');
        setInitializationProgress(100);

        // Clean up function
        return () => {
          window.removeEventListener('beforeunload', handleBeforeUnload);
          syncService.destroy();
        };

      } catch (error) {
        console.error('State management initialization failed:', error);
        if (mounted) {
          setInitializationError(
            error instanceof Error ? error.message : 'Unknown initialization error'
          );
        }
      } finally {
        if (mounted) {
          setIsInitializing(false);
        }
      }
    };

    initializeStateManagement();

    return () => {
      mounted = false;
    };
  }, [loadState, saveState]);

  // Show initialization UI if still initializing
  if (isInitializing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="w-96">
          <CardHeader>
            <CardTitle>Initializing Lexicon</CardTitle>
            <CardDescription>
              Setting up state management and synchronization...
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{initializationStep}</span>
                <span>{initializationProgress}%</span>
              </div>
              <Progress value={initializationProgress} />
            </div>
            
            {initializationError && (
              <div className="space-y-2">
                <Badge variant="destructive">Initialization Failed</Badge>
                <p className="text-sm text-muted-foreground">
                  {initializationError}
                </p>
                <Button 
                  onClick={() => window.location.reload()} 
                  variant="outline" 
                  size="sm"
                >
                  Retry
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  // Show error state if there's a global error
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="w-96">
          <CardHeader>
            <CardTitle>Application Error</CardTitle>
            <CardDescription>
              An error occurred while running Lexicon
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Badge variant="destructive">Error</Badge>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
            <div className="flex gap-2">
              <Button 
                onClick={() => useLexiconStore.getState().setError(null)} 
                variant="outline" 
                size="sm"
              >
                Clear Error
              </Button>
              <Button 
                onClick={() => window.location.reload()} 
                variant="outline" 
                size="sm"
              >
                Reload App
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Show loading overlay if operations are in progress
  return (
    <div className="relative">
      {children}
      {isLoading && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center space-x-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <span>Processing...</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};
