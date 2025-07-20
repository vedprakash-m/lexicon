import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import { cn } from '@/lib/utils';

// Accessibility Context for global a11y settings
interface AccessibilityState {
  reducedMotion: boolean;
  highContrast: boolean;
  fontSize: 'small' | 'medium' | 'large' | 'extra-large';
  focusVisible: boolean;
  screenReader: boolean;
  keyboardNavigation: boolean;
}

interface AccessibilityContextType {
  state: AccessibilityState;
  updatePreference: (key: keyof AccessibilityState, value: any) => void;
  announceToScreenReader: (message: string, priority?: 'polite' | 'assertive') => void;
}

const AccessibilityContext = createContext<AccessibilityContextType | null>(null);

export const useAccessibility = () => {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within AccessibilityProvider');
  }
  return context;
};

// Provider component
export const AccessibilityProvider: React.FC<{ children: React.ReactNode }> = ({ 
  children 
}) => {
  const [state, setState] = useState<AccessibilityState>(() => {
    // Initialize from system preferences and localStorage
    const stored = localStorage.getItem('lexicon-accessibility');
    const preferences = stored ? JSON.parse(stored) : {};
    
    return {
      reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
      highContrast: window.matchMedia('(prefers-contrast: high)').matches,
      fontSize: preferences.fontSize || 'medium',
      focusVisible: true,
      screenReader: detectScreenReader(),
      keyboardNavigation: false,
      ...preferences
    };
  });

  const announcementRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Listen for system preference changes
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const contrastQuery = window.matchMedia('(prefers-contrast: high)');
    
    const handleMotionChange = (e: MediaQueryListEvent) => {
      setState(prev => ({ ...prev, reducedMotion: e.matches }));
    };
    
    const handleContrastChange = (e: MediaQueryListEvent) => {
      setState(prev => ({ ...prev, highContrast: e.matches }));
    };

    motionQuery.addEventListener('change', handleMotionChange);
    contrastQuery.addEventListener('change', handleContrastChange);

    // Detect keyboard navigation
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        setState(prev => ({ ...prev, keyboardNavigation: true }));
      }
    };

    const handleMouseDown = () => {
      setState(prev => ({ ...prev, keyboardNavigation: false }));
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleMouseDown);

    return () => {
      motionQuery.removeEventListener('change', handleMotionChange);
      contrastQuery.removeEventListener('change', handleContrastChange);
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleMouseDown);
    };
  }, []);

  // Persist accessibility preferences
  useEffect(() => {
    localStorage.setItem('lexicon-accessibility', JSON.stringify(state));
    
    // Apply global CSS classes
    const root = document.documentElement;
    
    root.classList.toggle('reduce-motion', state.reducedMotion);
    root.classList.toggle('high-contrast', state.highContrast);
    root.classList.toggle('focus-visible', state.focusVisible);
    root.classList.toggle('keyboard-navigation', state.keyboardNavigation);
    
    // Apply font size
    root.setAttribute('data-font-size', state.fontSize);
    
  }, [state]);

  const updatePreference = (key: keyof AccessibilityState, value: any) => {
    setState(prev => ({ ...prev, [key]: value }));
  };

  const announceToScreenReader = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (announcementRef.current) {
      announcementRef.current.setAttribute('aria-live', priority);
      announcementRef.current.textContent = message;
      
      // Clear after announcement
      setTimeout(() => {
        if (announcementRef.current) {
          announcementRef.current.textContent = '';
        }
      }, 1000);
    }
  };

  return (
    <AccessibilityContext.Provider value={{ state, updatePreference, announceToScreenReader }}>
      {children}
      {/* Screen reader announcements */}
      <div
        ref={announcementRef}
        className="sr-only"
        aria-live="polite"
        aria-atomic="true"
      />
    </AccessibilityContext.Provider>
  );
};

// Utility function to detect screen readers
function detectScreenReader(): boolean {
  // Basic screen reader detection
  if (typeof window === 'undefined') return false;
  
  // Check for common screen reader indicators
  const hasScreenReader = (
    window.speechSynthesis ||
    window.navigator.userAgent.includes('NVDA') ||
    window.navigator.userAgent.includes('JAWS') ||
    window.navigator.userAgent.includes('VoiceOver') ||
    window.navigator.userAgent.includes('TalkBack')
  );
  
  return Boolean(hasScreenReader);
}

// Focus Management Hook
export const useFocusManagement = () => {
  const { state } = useAccessibility();
  
  const focusFirstElement = (container: HTMLElement) => {
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstElement = focusableElements[0] as HTMLElement;
    if (firstElement) {
      firstElement.focus();
    }
  };

  const trapFocus = (container: HTMLElement) => {
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    ) as NodeListOf<HTMLElement>;
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
      
      if (e.key === 'Escape') {
        container.focus();
      }
    };

    container.addEventListener('keydown', handleKeyDown);
    
    return () => {
      container.removeEventListener('keydown', handleKeyDown);
    };
  };

  return {
    focusFirstElement,
    trapFocus,
    keyboardNavigation: state.keyboardNavigation
  };
};

// Skip Navigation Component
export const SkipNavigation: React.FC = () => {
  return (
    <a
      href="#main-content"
      className={cn(
        "absolute top-0 left-0 z-50 p-3 bg-primary text-primary-foreground",
        "translate-y-[-100%] focus:translate-y-0 transition-transform",
        "focus:outline-none focus:ring-2 focus:ring-ring"
      )}
    >
      Skip to main content
    </a>
  );
};

// Accessible Button Component
interface AccessibleButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  announcement?: string;
}

export const AccessibleButton: React.FC<AccessibleButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  announcement,
  className,
  onClick,
  ...props
}) => {
  const { announceToScreenReader } = useAccessibility();

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (announcement) {
      announceToScreenReader(announcement);
    }
    onClick?.(e);
  };

  const variantClasses = {
    primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
    secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
    outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
    ghost: 'hover:bg-accent hover:text-accent-foreground'
  };

  const sizeClasses = {
    sm: 'h-8 px-3 text-sm',
    md: 'h-10 px-4',
    lg: 'h-12 px-6 text-lg'
  };

  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded-md font-medium transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        'disabled:pointer-events-none disabled:opacity-50',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      onClick={handleClick}
      aria-busy={loading}
      {...props}
    >
      {loading && (
        <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      )}
      {children}
    </button>
  );
};

// Accessible Form Field Component
interface AccessibleFieldProps {
  label: string;
  children: React.ReactNode;
  error?: string;
  hint?: string;
  required?: boolean;
  className?: string;
}

export const AccessibleField: React.FC<AccessibleFieldProps> = ({
  label,
  children,
  error,
  hint,
  required = false,
  className
}) => {
  const fieldId = React.useId();
  const errorId = error ? `${fieldId}-error` : undefined;
  const hintId = hint ? `${fieldId}-hint` : undefined;

  return (
    <div className={cn('space-y-2', className)}>
      <label
        htmlFor={fieldId}
        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
      >
        {label}
        {required && (
          <span className="text-destructive ml-1" aria-label="required">
            *
          </span>
        )}
      </label>
      
      <div className="relative">
        {React.cloneElement(children as React.ReactElement, {
          id: fieldId,
          'aria-invalid': error ? 'true' : 'false',
          'aria-describedby': [hintId, errorId].filter(Boolean).join(' ') || undefined,
          'aria-required': required
        })}
      </div>
      
      {hint && (
        <p id={hintId} className="text-sm text-muted-foreground">
          {hint}
        </p>
      )}
      
      {error && (
        <p id={errorId} className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  );
};

// Landmark Navigation Component
export const LandmarkNavigation: React.FC = () => {
  const landmarks = [
    { id: 'main-content', label: 'Main Content' },
    { id: 'navigation', label: 'Navigation' },
    { id: 'search', label: 'Search' },
    { id: 'footer', label: 'Footer' }
  ];

  return (
    <nav
      className={cn(
        "fixed top-0 left-0 z-50 p-4 bg-background border-r border-border",
        "translate-x-[-100%] focus-within:translate-x-0 transition-transform",
        "sr-only focus-within:not-sr-only"
      )}
      aria-label="Landmark navigation"
    >
      <h2 className="text-lg font-semibold mb-4">Skip to:</h2>
      <ul className="space-y-2">
        {landmarks.map((landmark) => (
          <li key={landmark.id}>
            <a
              href={`#${landmark.id}`}
              className="block p-2 text-sm hover:bg-accent rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {landmark.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
};

// Accessibility Settings Panel
export const AccessibilitySettings: React.FC<{ className?: string }> = ({ 
  className 
}) => {
  const { state, updatePreference } = useAccessibility();

  return (
    <div className={cn("space-y-6 p-4", className)}>
      <h2 className="text-lg font-semibold">Accessibility Settings</h2>
      
      {/* Font Size */}
      <div className="space-y-3">
        <label className="text-sm font-medium">Font Size</label>
        <div className="flex space-x-2">
          {['small', 'medium', 'large', 'extra-large'].map((size) => (
            <AccessibleButton
              key={size}
              variant={state.fontSize === size ? 'primary' : 'outline'}
              size="sm"
              onClick={() => updatePreference('fontSize', size)}
              announcement={`Font size changed to ${size}`}
            >
              {size.charAt(0).toUpperCase() + size.slice(1)}
            </AccessibleButton>
          ))}
        </div>
      </div>

      {/* Motion Preferences */}
      <div className="flex items-center justify-between">
        <label htmlFor="reduced-motion" className="text-sm font-medium">
          Reduce Motion
        </label>
        <button
          id="reduced-motion"
          role="switch"
          aria-checked={state.reducedMotion}
          className={cn(
            "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
            "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
            state.reducedMotion ? "bg-primary" : "bg-input"
          )}
          onClick={() => updatePreference('reducedMotion', !state.reducedMotion)}
        >
          <span
            className={cn(
              "inline-block h-4 w-4 transform rounded-full bg-background transition-transform",
              state.reducedMotion ? "translate-x-6" : "translate-x-1"
            )}
          />
          <span className="sr-only">
            {state.reducedMotion ? 'Disable' : 'Enable'} reduced motion
          </span>
        </button>
      </div>

      {/* High Contrast */}
      <div className="flex items-center justify-between">
        <label htmlFor="high-contrast" className="text-sm font-medium">
          High Contrast
        </label>
        <button
          id="high-contrast"
          role="switch"
          aria-checked={state.highContrast}
          className={cn(
            "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
            "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
            state.highContrast ? "bg-primary" : "bg-input"
          )}
          onClick={() => updatePreference('highContrast', !state.highContrast)}
        >
          <span
            className={cn(
              "inline-block h-4 w-4 transform rounded-full bg-background transition-transform",
              state.highContrast ? "translate-x-6" : "translate-x-1"
            )}
          />
          <span className="sr-only">
            {state.highContrast ? 'Disable' : 'Enable'} high contrast
          </span>
        </button>
      </div>

      {/* Focus Indicators */}
      <div className="flex items-center justify-between">
        <label htmlFor="focus-visible" className="text-sm font-medium">
          Enhanced Focus Indicators
        </label>
        <button
          id="focus-visible"
          role="switch"
          aria-checked={state.focusVisible}
          className={cn(
            "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
            "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
            state.focusVisible ? "bg-primary" : "bg-input"
          )}
          onClick={() => updatePreference('focusVisible', !state.focusVisible)}
        >
          <span
            className={cn(
              "inline-block h-4 w-4 transform rounded-full bg-background transition-transform",
              state.focusVisible ? "translate-x-6" : "translate-x-1"
            )}
          />
          <span className="sr-only">
            {state.focusVisible ? 'Disable' : 'Enable'} enhanced focus indicators
          </span>
        </button>
      </div>

      <div className="pt-4 border-t border-border text-sm text-muted-foreground">
        <p>
          These settings are saved to your device and will persist across sessions.
          Some preferences may be automatically detected from your system settings.
        </p>
      </div>
    </div>
  );
};
