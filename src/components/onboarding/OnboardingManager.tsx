import { useState, useEffect, createContext, useContext, ReactNode } from 'react';
import { WelcomeWizard } from './WelcomeWizard';
import { SampleProjects } from './SampleProjects';
import { InteractiveHelp, QuickHelp } from './InteractiveHelp';
import { FeatureTour, useTourManager } from './FeatureTour';

interface UserPreferences {
  primaryUse: string;
  experience: string;
  interests: string[];
  enableTutorials: boolean;
  createSampleProject: boolean;
}

interface OnboardingState {
  isFirstTime: boolean;
  hasCompletedWelcome: boolean;
  currentStep: 'welcome' | 'sample-projects' | 'complete' | null;
  userPreferences: UserPreferences | null;
  showHelp: boolean;
  helpQuery: string;
}

interface OnboardingContextType {
  state: OnboardingState;
  actions: {
    startOnboarding: () => void;
    completeWelcome: (preferences: UserPreferences) => void;
    skipSampleProjects: () => void;
    selectSampleProject: (project: any) => void;
    openHelp: (query?: string) => void;
    closeHelp: () => void;
    completeOnboarding: () => void;
  };
  tourManager: ReturnType<typeof useTourManager>;
}

const OnboardingContext = createContext<OnboardingContextType | null>(null);

interface OnboardingProviderProps {
  children: ReactNode;
}

export function OnboardingProvider({ children }: OnboardingProviderProps) {
  const [state, setState] = useState<OnboardingState>(() => {
    const saved = localStorage.getItem('lexicon-onboarding');
    const defaultState = {
      isFirstTime: true,
      hasCompletedWelcome: false,
      currentStep: null as OnboardingState['currentStep'],
      userPreferences: null,
      showHelp: false,
      helpQuery: ''
    };

    if (!saved) return defaultState;

    try {
      const parsed = JSON.parse(saved);
      return { ...defaultState, ...parsed };
    } catch {
      return defaultState;
    }
  });

  const tourManager = useTourManager();

  // Save state to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('lexicon-onboarding', JSON.stringify(state));
  }, [state]);

  // Auto-start onboarding for first-time users
  useEffect(() => {
    if (state.isFirstTime && !state.hasCompletedWelcome && state.currentStep === null) {
      setState(prev => ({ ...prev, currentStep: 'welcome' }));
    }
  }, [state.isFirstTime, state.hasCompletedWelcome, state.currentStep]);

  const actions = {
    startOnboarding: () => {
      setState(prev => ({ 
        ...prev, 
        currentStep: 'welcome',
        isFirstTime: true 
      }));
    },

    completeWelcome: (preferences: UserPreferences) => {
      setState(prev => ({
        ...prev,
        hasCompletedWelcome: true,
        userPreferences: preferences,
        currentStep: preferences.createSampleProject ? 'sample-projects' : 'complete'
      }));

      // Start appropriate tours based on experience level
      if (preferences.enableTutorials) {
        setTimeout(() => {
          if (preferences.experience === 'beginner') {
            tourManager.startTour('main-navigation');
          }
        }, 1000);
      }
    },

    skipSampleProjects: () => {
      setState(prev => ({ ...prev, currentStep: 'complete' }));
    },

    selectSampleProject: (project: any) => {
      setState(prev => ({ ...prev, currentStep: 'complete' }));
      
      // Start project-specific tour if tutorials are enabled
      if (state.userPreferences?.enableTutorials) {
        setTimeout(() => {
          if (project.category === 'research') {
            tourManager.startTour('project-creation');
          } else if (project.category === 'analysis') {
            tourManager.startTour('document-analysis');
          }
        }, 2000);
      }
    },

    openHelp: (query = '') => {
      setState(prev => ({ 
        ...prev, 
        showHelp: true, 
        helpQuery: query 
      }));
    },

    closeHelp: () => {
      setState(prev => ({ 
        ...prev, 
        showHelp: false, 
        helpQuery: '' 
      }));
    },

    completeOnboarding: () => {
      setState(prev => ({
        ...prev,
        isFirstTime: false,
        currentStep: null
      }));
    }
  };

  return (
    <OnboardingContext.Provider value={{ state, actions, tourManager }}>
      {children}
    </OnboardingContext.Provider>
  );
}

export function useOnboarding() {
  const context = useContext(OnboardingContext);
  if (!context) {
    throw new Error('useOnboarding must be used within an OnboardingProvider');
  }
  return context;
}

interface OnboardingManagerProps {
  children: ReactNode;
}

export function OnboardingManager({ children }: OnboardingManagerProps) {
  const { state, actions, tourManager } = useOnboarding();

  return (
    <>
      {children}

      {/* Welcome Wizard */}
      <WelcomeWizard
        isOpen={state.currentStep === 'welcome'}
        onClose={() => actions.completeOnboarding()}
        onComplete={actions.completeWelcome}
      />

      {/* Sample Projects */}
      {state.currentStep === 'sample-projects' && (
        <SampleProjects
          onProjectSelect={actions.selectSampleProject}
          onSkip={actions.skipSampleProjects}
        />
      )}

      {/* Interactive Help */}
      <InteractiveHelp
        isOpen={state.showHelp}
        onClose={actions.closeHelp}
        initialQuery={state.helpQuery}
      />

      {/* Quick Help Button */}
      <QuickHelp onOpenHelp={actions.openHelp} />

      {/* Active Tours */}
      {tourManager.activeTour && (
        <FeatureTour
          isActive={!!tourManager.activeTour}
          tourId={tourManager.activeTour}
          steps={[]}
          onComplete={() => tourManager.completeTour(tourManager.activeTour!)}
          onSkip={tourManager.skipTour}
          autoStart={true}
        />
      )}
    </>
  );
}

// Utility hook for checking onboarding status
export function useOnboardingStatus() {
  const { state } = useOnboarding();
  
  return {
    isFirstTime: state.isFirstTime,
    hasCompletedWelcome: state.hasCompletedWelcome,
    isOnboarding: state.currentStep !== null,
    currentStep: state.currentStep,
    userPreferences: state.userPreferences
  };
}

// Progressive disclosure hook
export function useProgressiveDisclosure() {
  const { tourManager } = useOnboarding();
  const [discoveredFeatures, setDiscoveredFeatures] = useState<string[]>(() => {
    const saved = localStorage.getItem('lexicon-discovered-features');
    return saved ? JSON.parse(saved) : [];
  });

  const discoverFeature = (featureId: string) => {
    if (!discoveredFeatures.includes(featureId)) {
      const updated = [...discoveredFeatures, featureId];
      setDiscoveredFeatures(updated);
      localStorage.setItem('lexicon-discovered-features', JSON.stringify(updated));
    }
  };

  const isFeatureDiscovered = (featureId: string) => {
    return discoveredFeatures.includes(featureId);
  };

  const suggestTour = (tourId: string) => {
    if (!tourManager.isTourCompleted(tourId) && !tourManager.activeTour) {
      // Could trigger a gentle suggestion here
      return true;
    }
    return false;
  };

  return {
    discoveredFeatures,
    discoverFeature,
    isFeatureDiscovered,
    suggestTour
  };
}
