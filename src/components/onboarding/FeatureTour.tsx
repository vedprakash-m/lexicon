import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { X, ArrowLeft, ArrowRight, Target, MousePointer, Lightbulb } from 'lucide-react';
import { useScreenReaderAnnouncement } from '@/lib/accessibility';

interface TourStep {
  id: string;
  title: string;
  content: string;
  target: string; // CSS selector for the target element
  position: 'top' | 'bottom' | 'left' | 'right';
  action?: 'click' | 'hover' | 'type';
  required?: boolean;
  highlight?: boolean;
}

interface FeatureTourProps {
  isActive: boolean;
  tourId: string;
  steps: TourStep[];
  onComplete: () => void;
  onSkip: () => void;
  autoStart?: boolean;
}

const TOURS = {
  'main-navigation': [
    {
      id: 'sidebar',
      title: 'Navigation Sidebar',
      content: 'Access all your projects, recent documents, and main features from this sidebar.',
      target: '[data-tour="sidebar"]',
      position: 'right' as const,
      highlight: true
    },
    {
      id: 'search',
      title: 'Global Search',
      content: 'Use the search bar to quickly find documents, projects, or specific content across your entire knowledge base.',
      target: '[data-tour="search"]',
      position: 'bottom' as const,
      action: 'click' as const
    },
    {
      id: 'command-palette',
      title: 'Command Palette',
      content: 'Press Cmd/Ctrl + K to open the command palette for quick actions and navigation.',
      target: '[data-tour="command-trigger"]',
      position: 'bottom' as const,
      required: true
    },
    {
      id: 'workspace',
      title: 'Main Workspace',
      content: 'This is where your content appears. You can have multiple tabs open and work with different documents.',
      target: '[data-tour="workspace"]',
      position: 'top' as const
    }
  ],
  'project-creation': [
    {
      id: 'new-project',
      title: 'Create New Project',
      content: 'Start by creating a new project to organize your documents and sources.',
      target: '[data-tour="new-project"]',
      position: 'right' as const,
      action: 'click' as const,
      required: true
    },
    {
      id: 'project-type',
      title: 'Choose Project Type',
      content: 'Select a project type that matches your use case - research, knowledge base, or collaboration.',
      target: '[data-tour="project-type"]',
      position: 'bottom' as const
    },
    {
      id: 'add-sources',
      title: 'Add Sources',
      content: 'Upload documents, connect external sources, or start with sample content.',
      target: '[data-tour="add-sources"]',
      position: 'top' as const,
      highlight: true
    }
  ],
  'document-analysis': [
    {
      id: 'document-view',
      title: 'Document Viewer',
      content: 'View and annotate your documents with advanced reading tools.',
      target: '[data-tour="document-view"]',
      position: 'left' as const
    },
    {
      id: 'analysis-panel',
      title: 'Analysis Panel',
      content: 'Get AI-powered insights, summaries, and key themes from your documents.',
      target: '[data-tour="analysis-panel"]',
      position: 'left' as const,
      highlight: true
    },
    {
      id: 'annotations',
      title: 'Annotations',
      content: 'Highlight text and add notes. Your annotations are automatically organized and searchable.',
      target: '[data-tour="annotations"]',
      position: 'bottom' as const,
      action: 'click' as const
    }
  ]
};

export function FeatureTour({ isActive, tourId, steps: customSteps, onComplete, onSkip, autoStart = false }: FeatureTourProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const [highlightedElement, setHighlightedElement] = useState<Element | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });
  
  const { announce } = useScreenReaderAnnouncement();
  const overlayRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const steps = customSteps || TOURS[tourId as keyof typeof TOURS] || [];
  const currentStep = steps[currentStepIndex];
  const progress = ((currentStepIndex + 1) / steps.length) * 100;

  useEffect(() => {
    if (isActive && autoStart) {
      setIsVisible(true);
      announce(`Starting ${tourId} tour. Step 1 of ${steps.length}`);
    }
  }, [isActive, autoStart, tourId, steps.length, announce]);

  useEffect(() => {
    if (!isVisible || !currentStep) return;

    const targetElement = document.querySelector(currentStep.target);
    if (targetElement) {
      setHighlightedElement(targetElement);
      positionTooltip(targetElement);
      
      if (currentStep.highlight) {
        targetElement.classList.add('tour-highlight');
      }

      announce(`Step ${currentStepIndex + 1}: ${currentStep.title}`);
    }

    return () => {
      if (targetElement && currentStep.highlight) {
        targetElement.classList.remove('tour-highlight');
      }
    };
  }, [currentStepIndex, isVisible, currentStep, announce]);

  const positionTooltip = (targetElement: Element) => {
    const rect = targetElement.getBoundingClientRect();
    const tooltipRect = tooltipRef.current?.getBoundingClientRect();
    
    if (!tooltipRect) return;

    let top = 0;
    let left = 0;

    switch (currentStep.position) {
      case 'top':
        top = rect.top - tooltipRect.height - 16;
        left = rect.left + (rect.width - tooltipRect.width) / 2;
        break;
      case 'bottom':
        top = rect.bottom + 16;
        left = rect.left + (rect.width - tooltipRect.width) / 2;
        break;
      case 'left':
        top = rect.top + (rect.height - tooltipRect.height) / 2;
        left = rect.left - tooltipRect.width - 16;
        break;
      case 'right':
        top = rect.top + (rect.height - tooltipRect.height) / 2;
        left = rect.right + 16;
        break;
    }

    // Ensure tooltip stays within viewport
    const viewport = {
      width: window.innerWidth,
      height: window.innerHeight
    };

    top = Math.max(16, Math.min(top, viewport.height - tooltipRect.height - 16));
    left = Math.max(16, Math.min(left, viewport.width - tooltipRect.width - 16));

    setTooltipPosition({ top, left });
  };

  const handleNext = () => {
    if (currentStepIndex < steps.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrevious = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(currentStepIndex - 1);
    }
  };

  const handleComplete = () => {
    setIsVisible(false);
    if (highlightedElement) {
      highlightedElement.classList.remove('tour-highlight');
    }
    onComplete();
    announce('Tour completed');
  };

  const handleSkip = () => {
    setIsVisible(false);
    if (highlightedElement) {
      highlightedElement.classList.remove('tour-highlight');
    }
    onSkip();
    announce('Tour skipped');
  };

  const startTour = () => {
    setIsVisible(true);
    setCurrentStepIndex(0);
    announce(`Starting ${tourId} tour. Step 1 of ${steps.length}`);
  };

  if (!isActive || steps.length === 0) return null;

  return (
    <>
      {/* Tour overlay */}
      {isVisible && (
        <div
          ref={overlayRef}
          className="fixed inset-0 z-50 bg-black/20 pointer-events-none"
          style={{
            backgroundColor: 'rgba(0, 0, 0, 0.3)',
          }}
        />
      )}

      {/* Tour tooltip */}
      {isVisible && currentStep && (
        <div
          ref={tooltipRef}
          className="fixed z-50 w-80 pointer-events-auto"
          style={{
            top: tooltipPosition.top,
            left: tooltipPosition.left,
          }}
        >
          <Card className="shadow-2xl border-2 border-primary/20">
            <CardContent className="p-0">
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b bg-primary/5">
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-primary" />
                  <Badge variant="outline" className="text-xs">
                    {currentStepIndex + 1} of {steps.length}
                  </Badge>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleSkip}
                  className="h-6 w-6 p-0"
                  aria-label="Skip tour"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>

              {/* Progress */}
              <div className="px-4 pt-2">
                <Progress value={progress} className="h-1" aria-label={`Tour progress: ${Math.round(progress)}%`} />
              </div>

              {/* Content */}
              <div className="p-4 space-y-3">
                <div className="flex items-start gap-2">
                  {currentStep.action === 'click' && <MousePointer className="w-4 h-4 text-orange-500 mt-0.5" />}
                  {'required' in currentStep && currentStep.required && <Lightbulb className="w-4 h-4 text-yellow-500 mt-0.5" />}
                  <div className="flex-1">
                    <h3 className="font-semibold text-sm">{currentStep.title}</h3>
                    <p className="text-sm text-muted-foreground mt-1">{currentStep.content}</p>
                  </div>
                </div>

                {currentStep.action && (
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <MousePointer className="w-3 h-3" />
                    <span>
                      {currentStep.action === 'click' && 'Click to interact'}
                      {currentStep.action === 'hover' && 'Hover to see more'}
                      {currentStep.action === 'type' && 'Try typing here'}
                    </span>
                  </div>
                )}
              </div>

              {/* Navigation */}
              <div className="flex justify-between items-center p-4 border-t bg-muted/30">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handlePrevious}
                  disabled={currentStepIndex === 0}
                  className="flex items-center gap-1"
                >
                  <ArrowLeft className="w-3 h-3" />
                  Previous
                </Button>

                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleSkip}
                    className="text-muted-foreground"
                  >
                    Skip Tour
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleNext}
                    className="flex items-center gap-1"
                  >
                    {currentStepIndex === steps.length - 1 ? 'Finish' : 'Next'}
                    {currentStepIndex < steps.length - 1 && <ArrowRight className="w-3 h-3" />}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tour starter button (when not visible) */}
      {!isVisible && (
        <Button
          onClick={startTour}
          variant="outline"
          size="sm"
          className="fixed bottom-4 right-4 z-40 shadow-lg"
        >
          <Target className="w-4 h-4 mr-2" />
          Start Tour
        </Button>
      )}
    </>
  );
}

// Pre-configured tour components
export function MainNavigationTour(props: Omit<FeatureTourProps, 'tourId' | 'steps'>) {
  return <FeatureTour {...props} tourId="main-navigation" steps={TOURS['main-navigation']} />;
}

export function ProjectCreationTour(props: Omit<FeatureTourProps, 'tourId' | 'steps'>) {
  return <FeatureTour {...props} tourId="project-creation" steps={TOURS['project-creation']} />;
}

export function DocumentAnalysisTour(props: Omit<FeatureTourProps, 'tourId' | 'steps'>) {
  return <FeatureTour {...props} tourId="document-analysis" steps={TOURS['document-analysis']} />;
}

// Tour manager hook
export function useTourManager() {
  const [activeTour, setActiveTour] = useState<string | null>(null);
  const [completedTours, setCompletedTours] = useState<string[]>(() => {
    const saved = localStorage.getItem('lexicon-completed-tours');
    return saved ? JSON.parse(saved) : [];
  });

  const startTour = (tourId: string) => {
    setActiveTour(tourId);
  };

  const completeTour = (tourId: string) => {
    setActiveTour(null);
    const newCompleted = [...completedTours, tourId];
    setCompletedTours(newCompleted);
    localStorage.setItem('lexicon-completed-tours', JSON.stringify(newCompleted));
  };

  const skipTour = () => {
    setActiveTour(null);
  };

  const resetTours = () => {
    setCompletedTours([]);
    localStorage.removeItem('lexicon-completed-tours');
  };

  const isTourCompleted = (tourId: string) => completedTours.includes(tourId);

  return {
    activeTour,
    completedTours,
    startTour,
    completeTour,
    skipTour,
    resetTours,
    isTourCompleted,
  };
}
