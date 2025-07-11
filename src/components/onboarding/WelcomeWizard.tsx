import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Check, BookOpen, Search, Zap, Users, ArrowRight, ArrowLeft, Star } from 'lucide-react';
import { useScreenReaderAnnouncement } from '@/lib/accessibility';

interface WelcomeWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (preferences: UserPreferences) => void;
}

interface UserPreferences {
  primaryUse: string;
  experience: string;
  interests: string[];
  enableTutorials: boolean;
  createSampleProject: boolean;
}

const STEPS = [
  { id: 'welcome', title: 'Welcome to Lexicon', description: 'Your intelligent knowledge management system' },
  { id: 'purpose', title: 'What brings you here?', description: 'Help us personalize your experience' },
  { id: 'experience', title: 'Experience Level', description: 'Tell us about your background' },
  { id: 'interests', title: 'Areas of Interest', description: 'Choose topics that interest you' },
  { id: 'setup', title: 'Setup Preferences', description: 'Configure your initial experience' },
  { id: 'complete', title: 'All Set!', description: 'Ready to explore Lexicon' }
];

const PRIMARY_USES = [
  { id: 'research', title: 'Academic Research', description: 'Organize papers, citations, and research notes', icon: BookOpen },
  { id: 'knowledge', title: 'Knowledge Management', description: 'Build a personal knowledge base', icon: Search },
  { id: 'collaboration', title: 'Team Collaboration', description: 'Share and collaborate on projects', icon: Users },
  { id: 'analysis', title: 'Content Analysis', description: 'Analyze and extract insights from texts', icon: Zap }
];

const EXPERIENCE_LEVELS = [
  { id: 'beginner', title: 'New to Knowledge Management', description: 'First time using tools like this' },
  { id: 'intermediate', title: 'Some Experience', description: 'Used note-taking or research tools before' },
  { id: 'advanced', title: 'Power User', description: 'Experienced with knowledge management systems' }
];

const INTEREST_AREAS = [
  'Literature & Philosophy',
  'Scientific Research',
  'Historical Studies',
  'Religious & Classical Texts',
  'Technical Documentation',
  'Educational Content',
  'Business & Strategy',
  'Creative Writing'
];

export function WelcomeWizard({ isOpen, onClose, onComplete }: WelcomeWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [preferences, setPreferences] = useState<UserPreferences>({
    primaryUse: '',
    experience: '',
    interests: [],
    enableTutorials: true,
    createSampleProject: true
  });

  const { announce } = useScreenReaderAnnouncement();
  const progress = ((currentStep + 1) / STEPS.length) * 100;

  useEffect(() => {
    if (isOpen && currentStep === 0) {
      announce('Welcome wizard opened. Step 1 of 6: Welcome to Lexicon');
    }
  }, [isOpen, announce]);

  useEffect(() => {
    if (isOpen) {
      const stepInfo = STEPS[currentStep];
      announce(`Step ${currentStep + 1} of ${STEPS.length}: ${stepInfo.title}`);
    }
  }, [currentStep, isOpen, announce]);

  const handleNext = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    onComplete(preferences);
    onClose();
  };

  const updatePreference = <K extends keyof UserPreferences>(
    key: K,
    value: UserPreferences[K]
  ) => {
    setPreferences(prev => ({ ...prev, [key]: value }));
  };

  const toggleInterest = (interest: string) => {
    setPreferences(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }));
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1: return preferences.primaryUse !== '';
      case 2: return preferences.experience !== '';
      default: return true;
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="text-center space-y-6">
            <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
              <BookOpen className="w-8 h-8 text-primary" />
            </div>
            <div>
              <h2 className="text-2xl font-bold mb-2">Welcome to Lexicon</h2>
              <p className="text-muted-foreground text-lg">
                Your intelligent knowledge management system for organizing, analyzing, and discovering insights from your content.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-500" />
                <span>Smart content organization</span>
              </div>
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-500" />
                <span>Powerful search capabilities</span>
              </div>
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-500" />
                <span>Collaborative workspaces</span>
              </div>
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-500" />
                <span>AI-powered insights</span>
              </div>
            </div>
          </div>
        );

      case 1:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-xl font-semibold mb-2">What brings you to Lexicon?</h2>
              <p className="text-muted-foreground">
                Select your primary use case to help us customize your experience
              </p>
            </div>
            <div className="grid gap-3">
              {PRIMARY_USES.map((use) => {
                const Icon = use.icon;
                return (
                  <Card
                    key={use.id}
                    className={`cursor-pointer transition-all hover:shadow-md ${
                      preferences.primaryUse === use.id ? 'ring-2 ring-primary bg-primary/5' : ''
                    }`}
                    onClick={() => updatePreference('primaryUse', use.id)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        updatePreference('primaryUse', use.id);
                      }
                    }}
                    aria-pressed={preferences.primaryUse === use.id}
                  >
                    <CardContent className="flex items-start gap-3 p-4">
                      <Icon className="w-5 h-5 text-primary mt-0.5" />
                      <div className="flex-1">
                        <h3 className="font-medium">{use.title}</h3>
                        <p className="text-sm text-muted-foreground">{use.description}</p>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-xl font-semibold mb-2">What's your experience level?</h2>
              <p className="text-muted-foreground">
                This helps us provide the right level of guidance
              </p>
            </div>
            <div className="space-y-3">
              {EXPERIENCE_LEVELS.map((level) => (
                <Card
                  key={level.id}
                  className={`cursor-pointer transition-all hover:shadow-md ${
                    preferences.experience === level.id ? 'ring-2 ring-primary bg-primary/5' : ''
                  }`}
                  onClick={() => updatePreference('experience', level.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      updatePreference('experience', level.id);
                    }
                  }}
                  aria-pressed={preferences.experience === level.id}
                >
                  <CardContent className="p-4">
                    <h3 className="font-medium">{level.title}</h3>
                    <p className="text-sm text-muted-foreground">{level.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-xl font-semibold mb-2">Areas of Interest</h2>
              <p className="text-muted-foreground">
                Select topics that interest you (optional)
              </p>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {INTEREST_AREAS.map((interest) => (
                <Badge
                  key={interest}
                  variant={preferences.interests.includes(interest) ? "default" : "outline"}
                  className="cursor-pointer justify-center p-2 h-auto text-center hover:bg-primary/10"
                  onClick={() => toggleInterest(interest)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      toggleInterest(interest);
                    }
                  }}
                  aria-pressed={preferences.interests.includes(interest)}
                >
                  {interest}
                </Badge>
              ))}
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-xl font-semibold mb-2">Setup Preferences</h2>
              <p className="text-muted-foreground">
                Configure your initial experience
              </p>
            </div>
            <div className="space-y-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">Enable Feature Tutorials</h3>
                      <p className="text-sm text-muted-foreground">
                        Show guided tours for key features
                      </p>
                    </div>
                    <Button
                      variant={preferences.enableTutorials ? "default" : "outline"}
                      size="sm"
                      onClick={() => updatePreference('enableTutorials', !preferences.enableTutorials)}
                    >
                      {preferences.enableTutorials ? 'Enabled' : 'Disabled'}
                    </Button>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">Create Sample Project</h3>
                      <p className="text-sm text-muted-foreground">
                        Set up a demo project to explore features
                      </p>
                    </div>
                    <Button
                      variant={preferences.createSampleProject ? "default" : "outline"}
                      size="sm"
                      onClick={() => updatePreference('createSampleProject', !preferences.createSampleProject)}
                    >
                      {preferences.createSampleProject ? 'Yes' : 'No'}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="text-center space-y-6">
            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <Check className="w-8 h-8 text-green-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold mb-2">You're all set!</h2>
              <p className="text-muted-foreground text-lg">
                Lexicon is configured and ready for you to explore.
              </p>
            </div>
            <div className="bg-muted/50 rounded-lg p-4 space-y-2">
              <h3 className="font-medium">What's next?</h3>
              <div className="text-sm text-muted-foreground space-y-1">
                {preferences.createSampleProject && (
                  <div className="flex items-center gap-2 justify-center">
                    <Star className="w-4 h-4" />
                    <span>Sample project will be created</span>
                  </div>
                )}
                {preferences.enableTutorials && (
                  <div className="flex items-center gap-2 justify-center">
                    <Zap className="w-4 h-4" />
                    <span>Feature tutorials are enabled</span>
                  </div>
                )}
                <div className="flex items-center gap-2 justify-center">
                  <BookOpen className="w-4 h-4" />
                  <span>Ready to start organizing your knowledge</span>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={isOpen} onClose={onClose}>
      <DialogContent 
        className="max-w-2xl max-h-[90vh] overflow-y-auto"
      >
        <DialogHeader className="space-y-3">
          <div className="flex items-center justify-between">
            <DialogTitle>{STEPS[currentStep].title}</DialogTitle>
            <Badge variant="outline" className="text-xs">
              Step {currentStep + 1} of {STEPS.length}
            </Badge>
          </div>
          <DialogDescription>
            {STEPS[currentStep].description}
          </DialogDescription>
          <Progress value={progress} className="w-full" aria-label={`Progress: ${Math.round(progress)}%`} />
        </DialogHeader>

        <div className="py-6">
          {renderStepContent()}
        </div>

        <div className="flex justify-between items-center pt-4 border-t">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentStep === 0}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Previous
          </Button>

          <div className="flex gap-2">
            {currentStep < STEPS.length - 1 ? (
              <Button
                onClick={handleNext}
                disabled={!canProceed()}
                className="flex items-center gap-2"
              >
                Next
                <ArrowRight className="w-4 h-4" />
              </Button>
            ) : (
              <Button
                onClick={handleComplete}
                className="flex items-center gap-2"
              >
                Get Started
                <Check className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
