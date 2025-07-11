/**
 * Keyboard Shortcuts System
 * 
 * Provides global keyboard shortcuts with visual indicators and help.
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  Badge, 
  Button 
} from '../ui';
import { cn } from '../../lib/utils';

// Enhanced keyboard shortcut definition
export interface KeyboardShortcut {
  id: string;
  keys: string[];
  description: string;
  action: () => void;
  category: 'navigation' | 'actions' | 'search' | 'general';
  global?: boolean;
  enabled?: boolean;
}

interface KeyboardShortcutsContextType {
  shortcuts: KeyboardShortcut[];
  registerShortcut: (shortcut: KeyboardShortcut) => void;
  unregisterShortcut: (id: string) => void;
  enableShortcut: (id: string, enabled: boolean) => void;
  showHelp: boolean;
  toggleHelp: () => void;
}

const KeyboardShortcutsContext = createContext<KeyboardShortcutsContextType | undefined>(undefined);

export function useKeyboardShortcuts() {
  const context = useContext(KeyboardShortcutsContext);
  if (!context) {
    throw new Error('useKeyboardShortcuts must be used within a KeyboardShortcutsProvider');
  }
  return context;
}

// Default shortcuts for the Lexicon app
export const createDefaultShortcuts = (navigate: (path: string) => void): KeyboardShortcut[] => [
  // Navigation shortcuts
  {
    id: 'nav-dashboard',
    keys: ['Cmd', 'Shift', 'D'],
    description: 'Go to Dashboard',
    action: () => navigate('/'),
    category: 'navigation',
    global: true,
  },
  {
    id: 'nav-projects',
    keys: ['Cmd', 'Shift', 'P'],
    description: 'Go to Projects',
    action: () => navigate('/projects'),
    category: 'navigation',
    global: true,
  },
  {
    id: 'nav-scraping',
    keys: ['Cmd', 'Shift', 'S'],
    description: 'Go to Scraping',
    action: () => navigate('/scraping'),
    category: 'navigation',
    global: true,
  },
  {
    id: 'nav-batch',
    keys: ['Cmd', 'Shift', 'B'],
    description: 'Go to Batch Processing',
    action: () => navigate('/batch'),
    category: 'navigation',
    global: true,
  },
  // Action shortcuts
  {
    id: 'action-new-book',
    keys: ['Cmd', 'N'],
    description: 'Add New Book',
    action: () => {
      // Will be connected to add book action
      console.log('Add new book');
    },
    category: 'actions',
    global: true,
  },
  {
    id: 'action-search',
    keys: ['Cmd', 'K'],
    description: 'Open Search/Command Palette',
    action: () => {
      // Will trigger command palette
      window.dispatchEvent(new CustomEvent('lexicon:open-command-palette'));
    },
    category: 'search',
    global: true,
  },
  // General shortcuts
  {
    id: 'general-help',
    keys: ['?'],
    description: 'Show Keyboard Shortcuts',
    action: () => {
      // Will be handled by the provider
    },
    category: 'general',
    global: true,
  },
  {
    id: 'general-settings',
    keys: ['Cmd', ','],
    description: 'Open Settings',
    action: () => navigate('/settings'),
    category: 'navigation',
    global: true,
  },
  {
    id: 'general-help-f1',
    keys: ['F1'],
    description: 'Open Help System',
    action: () => {
      window.dispatchEvent(new CustomEvent('lexicon:open-help'));
    },
    category: 'general',
    global: true,
  },
];

// Format key combination for display
const formatKeys = (keys: string[]): string => {
  return keys
    .map(key => {
      // Convert to macOS style symbols
      switch (key.toLowerCase()) {
        case 'cmd':
        case 'command':
          return '⌘';
        case 'shift':
          return '⇧';
        case 'alt':
        case 'option':
          return '⌥';
        case 'ctrl':
        case 'control':
          return '⌃';
        case 'enter':
        case 'return':
          return '↵';
        case 'space':
          return '⎵';
        case 'tab':
          return '⇥';
        case 'delete':
        case 'backspace':
          return '⌫';
        case 'escape':
        case 'esc':
          return '⎋';
        default:
          return key.toUpperCase();
      }
    })
    .join('');
};

// Check if key combination matches
const matchesKeys = (event: KeyboardEvent, keys: string[]): boolean => {
  const pressedKeys: string[] = [];
  
  if (event.metaKey || event.ctrlKey) pressedKeys.push('cmd');
  if (event.shiftKey) pressedKeys.push('shift');
  if (event.altKey) pressedKeys.push('alt');
  
  // Add the main key
  const mainKey = event.key.toLowerCase();
  if (!['meta', 'ctrl', 'shift', 'alt'].includes(mainKey)) {
    pressedKeys.push(mainKey);
  }
  
  // Normalize the target keys
  const targetKeys = keys.map(k => k.toLowerCase());
  
  // Check if arrays match
  return pressedKeys.length === targetKeys.length &&
    pressedKeys.every(key => targetKeys.includes(key));
};

// Keyboard shortcuts help dialog
export const KeyboardShortcutsHelp: React.FC<{
  shortcuts: KeyboardShortcut[];
  open: boolean;
  onClose: () => void;
}> = ({ shortcuts, open, onClose }) => {
  const groupedShortcuts = shortcuts.reduce((acc, shortcut) => {
    if (!acc[shortcut.category]) {
      acc[shortcut.category] = [];
    }
    acc[shortcut.category].push(shortcut);
    return acc;
  }, {} as Record<string, KeyboardShortcut[]>);

  const categoryLabels = {
    navigation: 'Navigation',
    actions: 'Actions',
    search: 'Search',
    general: 'General',
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span>Keyboard Shortcuts</span>
            <Badge variant="secondary" className="text-xs">
              {shortcuts.length} shortcuts
            </Badge>
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-6">
          {Object.entries(groupedShortcuts).map(([category, categoryShortcuts]) => (
            <div key={category}>
              <h3 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wider">
                {categoryLabels[category as keyof typeof categoryLabels] || category}
              </h3>
              
              <div className="space-y-2">
                {categoryShortcuts.map((shortcut) => (
                  <div 
                    key={shortcut.id}
                    className="flex items-center justify-between py-2 px-3 rounded-md hover:bg-muted/50"
                  >
                    <span className="text-sm">{shortcut.description}</span>
                    <div className="flex items-center gap-1">
                      {shortcut.keys.map((key, index) => (
                        <React.Fragment key={index}>
                          <kbd className="px-2 py-1 text-xs bg-muted border border-border rounded">
                            {formatKeys([key])}
                          </kbd>
                          {index < shortcut.keys.length - 1 && (
                            <span className="text-xs text-muted-foreground">+</span>
                          )}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        
        <div className="flex justify-end pt-4 border-t">
          <Button onClick={onClose}>Close</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export function KeyboardShortcutsProvider({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const [shortcuts, setShortcuts] = useState<KeyboardShortcut[]>(createDefaultShortcuts(navigate));
  const [showHelp, setShowHelp] = useState(false);

  const registerShortcut = useCallback((shortcut: KeyboardShortcut) => {
    setShortcuts(prev => {
      // Remove existing shortcut with same ID
      const filtered = prev.filter(s => s.id !== shortcut.id);
      return [...filtered, { ...shortcut, enabled: shortcut.enabled ?? true }];
    });
  }, []);

  const unregisterShortcut = useCallback((id: string) => {
    setShortcuts(prev => prev.filter(s => s.id !== id));
  }, []);

  const enableShortcut = useCallback((id: string, enabled: boolean) => {
    setShortcuts(prev => prev.map(s => s.id === id ? { ...s, enabled } : s));
  }, []);

  const toggleHelp = useCallback(() => {
    setShowHelp(prev => !prev);
  }, []);

  // Handle keyboard events
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Check for help shortcut first
      if (event.key === '?' && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey) {
        // Only if not in an input field
        const target = event.target as HTMLElement;
        if (target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA' && !target.isContentEditable) {
          event.preventDefault();
          setShowHelp(true);
          return;
        }
      }

      // Check other shortcuts
      for (const shortcut of shortcuts) {
        if (shortcut.enabled !== false && shortcut.global && matchesKeys(event, shortcut.keys)) {
          // Special handling for help shortcut
          if (shortcut.id === 'general-help') {
            event.preventDefault();
            setShowHelp(true);
            return;
          }
          
          // Special handling for command palette
          if (shortcut.id === 'action-search') {
            event.preventDefault();
            // This will be handled by command palette component
            window.dispatchEvent(new CustomEvent('lexicon:open-command-palette'));
            return;
          }
          
          event.preventDefault();
          shortcut.action();
          return;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);

  const contextValue = {
    shortcuts,
    registerShortcut,
    unregisterShortcut,
    enableShortcut,
    showHelp,
    toggleHelp,
  };

  return (
    <KeyboardShortcutsContext.Provider value={contextValue}>
      {children}
      <KeyboardShortcutsHelp 
        shortcuts={shortcuts}
        open={showHelp}
        onClose={() => setShowHelp(false)}
      />
    </KeyboardShortcutsContext.Provider>
  );
}

// Hook for registering shortcuts with automatic cleanup
export function useShortcut(shortcut: Omit<KeyboardShortcut, 'enabled'>) {
  const { registerShortcut, unregisterShortcut } = useKeyboardShortcuts();

  useEffect(() => {
    registerShortcut(shortcut as KeyboardShortcut);
    return () => unregisterShortcut(shortcut.id);
  }, [shortcut.id, shortcut.keys, shortcut.description, registerShortcut, unregisterShortcut]);
}

// Component to display a single keyboard shortcut
export const KeyboardShortcut: React.FC<{
  keys: string[];
  className?: string;
}> = ({ keys, className }) => {
  return (
    <div className={cn("flex items-center gap-1", className)}>
      {keys.map((key, index) => (
        <React.Fragment key={index}>
          <kbd className="px-1.5 py-0.5 text-xs bg-muted border border-border rounded font-mono">
            {formatKeys([key])}
          </kbd>
          {index < keys.length - 1 && (
            <span className="text-xs text-muted-foreground">+</span>
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

// Format shortcut display string for the new interface
export function formatShortcut(shortcut: KeyboardShortcut): string {
  return shortcut.keys
    .map(key => {
      const isMac = navigator.platform.toLowerCase().includes('mac');
      
      // Convert to macOS style symbols
      switch (key.toLowerCase()) {
        case 'cmd':
        case 'command':
          return isMac ? '⌘' : 'Ctrl';
        case 'shift':
          return isMac ? '⇧' : 'Shift';
        case 'alt':
        case 'option':
          return isMac ? '⌥' : 'Alt';
        case 'ctrl':
        case 'control':
          return '⌃';
        case 'enter':
        case 'return':
          return '↵';
        case 'space':
          return '⎵';
        case 'tab':
          return '⇥';
        case 'delete':
        case 'backspace':
          return '⌫';
        case 'escape':
        case 'esc':
          return '⎋';
        case 'arrowup':
          return '↑';
        case 'arrowdown':
          return '↓';
        case 'arrowleft':
          return '←';
        case 'arrowright':
          return '→';
        default:
          return key.charAt(0).toUpperCase() + key.slice(1);
      }
    })
    .join(navigator.platform.toLowerCase().includes('mac') ? '' : '+');
}
