import { useCallback, useEffect } from 'react';
import { useKeyboardShortcuts } from '../components/ui/keyboard-shortcuts';
import { useNavigate } from 'react-router-dom';

/**
 * Enhanced keyboard navigation hook with focus management
 */
export function useEnhancedKeyboardNavigation() {
  const { registerShortcut, unregisterShortcut } = useKeyboardShortcuts();
  const navigate = useNavigate();

  // Focus management for accessibility
  const focusFirstInteractiveElement = useCallback(() => {
    const firstInteractive = document.querySelector(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    ) as HTMLElement;
    
    if (firstInteractive) {
      firstInteractive.focus();
    }
  }, []);

  const focusLastInteractiveElement = useCallback(() => {
    const interactiveElements = document.querySelectorAll(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );
    
    const lastInteractive = interactiveElements[interactiveElements.length - 1] as HTMLElement;
    if (lastInteractive) {
      lastInteractive.focus();
    }
  }, []);

  const skipToMainContent = useCallback(() => {
    const mainContent = document.querySelector('main, [role="main"], #main-content') as HTMLElement;
    if (mainContent) {
      mainContent.focus();
      mainContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, []);

  const skipToNavigation = useCallback(() => {
    const navigation = document.querySelector('nav, [role="navigation"]') as HTMLElement;
    if (navigation) {
      const firstLink = navigation.querySelector('a, button') as HTMLElement;
      if (firstLink) {
        firstLink.focus();
      }
    }
  }, []);

  const cycleThroughSections = useCallback(() => {
    const sections = document.querySelectorAll('section, [role="region"], main, aside, nav');
    const currentFocus = document.activeElement;
    
    let currentSectionIndex = -1;
    sections.forEach((section, index) => {
      if (section.contains(currentFocus)) {
        currentSectionIndex = index;
      }
    });
    
    const nextIndex = (currentSectionIndex + 1) % sections.length;
    const nextSection = sections[nextIndex] as HTMLElement;
    
    if (nextSection) {
      const firstInteractive = nextSection.querySelector(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled])'
      ) as HTMLElement;
      
      if (firstInteractive) {
        firstInteractive.focus();
      } else {
        nextSection.focus();
      }
    }
  }, []);

  // Enhanced navigation shortcuts
  useEffect(() => {
    const shortcuts = [
      {
        id: 'accessibility-skip-main',
        keys: ['Alt', 'M'],
        description: 'Skip to Main Content',
        action: skipToMainContent,
        category: 'navigation' as const,
        global: true,
      },
      {
        id: 'accessibility-skip-nav',
        keys: ['Alt', 'N'],
        description: 'Skip to Navigation',
        action: skipToNavigation,
        category: 'navigation' as const,
        global: true,
      },
      {
        id: 'accessibility-focus-first',
        keys: ['Alt', 'F'],
        description: 'Focus First Interactive Element',
        action: focusFirstInteractiveElement,
        category: 'navigation' as const,
        global: true,
      },
      {
        id: 'accessibility-focus-last',
        keys: ['Alt', 'L'],
        description: 'Focus Last Interactive Element',
        action: focusLastInteractiveElement,
        category: 'navigation' as const,
        global: true,
      },
      {
        id: 'accessibility-cycle-sections',
        keys: ['Alt', 'S'],
        description: 'Cycle Through Page Sections',
        action: cycleThroughSections,
        category: 'navigation' as const,
        global: true,
      },
      {
        id: 'nav-library-quick',
        keys: ['G', 'L'],
        description: 'Go to Library (Quick)',
        action: () => navigate('/library'),
        category: 'navigation' as const,
        global: true,
      },
      {
        id: 'nav-processing-quick',
        keys: ['G', 'P'],
        description: 'Go to Processing (Quick)',
        action: () => navigate('/processing'),
        category: 'navigation' as const,
        global: true,
      },
      {
        id: 'nav-batch-quick',
        keys: ['G', 'B'],
        description: 'Go to Batch Processing (Quick)',
        action: () => navigate('/batch'),
        category: 'navigation' as const,
        global: true,
      },
      {
        id: 'nav-performance-quick',
        keys: ['G', 'M'],
        description: 'Go to Performance Monitoring (Quick)',
        action: () => navigate('/performance'),
        category: 'navigation' as const,
        global: true,
      },
    ];

    shortcuts.forEach(shortcut => registerShortcut(shortcut));

    return () => {
      shortcuts.forEach(shortcut => unregisterShortcut(shortcut.id));
    };
  }, [
    registerShortcut, 
    unregisterShortcut, 
    navigate, 
    skipToMainContent, 
    skipToNavigation, 
    focusFirstInteractiveElement, 
    focusLastInteractiveElement,
    cycleThroughSections
  ]);

  // Focus trap management for modal dialogs
  const createFocusTrap = useCallback((element: HTMLElement) => {
    const focusableElements = element.querySelectorAll(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );
    
    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

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
    };

    element.addEventListener('keydown', handleTabKey);
    firstElement?.focus();

    return () => {
      element.removeEventListener('keydown', handleTabKey);
    };
  }, []);

  // Toast navigation for screen readers
  const announceToScreenReader = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  }, []);

  return {
    focusFirstInteractiveElement,
    focusLastInteractiveElement,
    skipToMainContent,
    skipToNavigation,
    cycleThroughSections,
    createFocusTrap,
    announceToScreenReader,
  };
}
