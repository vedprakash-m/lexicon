import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Dialog, 
  DialogContent, 
  Input,
  Badge
} from '../ui';
import { 
  Search, 
  FileText, 
  Settings, 
  BarChart3, 
  Library,
  Download,
  Cloud,
  HelpCircle,
  Command as CommandIcon,
  ArrowRight
} from 'lucide-react';
import { useListNavigation, useScreenReaderAnnouncement } from '../../lib/accessibility';

interface Command {
  id: string;
  title: string;
  description?: string;
  icon: React.ComponentType<{ className?: string }>;
  action: () => void;
  category: 'navigation' | 'actions' | 'settings' | 'help';
  keywords: string[];
  shortcut?: string;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const navigate = useNavigate();

  // Define available commands
  const commands: Command[] = useMemo(() => [
    // Navigation commands
    {
      id: 'nav-dashboard',
      title: 'Go to Dashboard',
      description: 'View overview and recent activity',
      icon: BarChart3,
      category: 'navigation',
      keywords: ['dashboard', 'home', 'overview'],
      action: () => { navigate('/'); onClose(); }
    },
    {
      id: 'nav-library',
      title: 'Go to Library',
      description: 'Browse and manage your book collection',
      icon: Library,
      category: 'navigation',
      keywords: ['library', 'books', 'catalog', 'collection'],
      action: () => { navigate('/library'); onClose(); }
    },
    {
      id: 'nav-processing',
      title: 'Go to Processing',
      description: 'Configure and monitor text processing',
      icon: Settings,
      category: 'navigation',
      keywords: ['processing', 'chunking', 'configuration'],
      action: () => { navigate('/chunking'); onClose(); }
    },
    {
      id: 'nav-export',
      title: 'Go to Export Manager',
      description: 'Export processed datasets',
      icon: Download,
      category: 'navigation',
      keywords: ['export', 'download', 'format'],
      action: () => { navigate('/export'); onClose(); }
    },
    {
      id: 'nav-sync',
      title: 'Go to Sync & Backup',
      description: 'Manage cloud storage and backups',
      icon: Cloud,
      category: 'navigation',
      keywords: ['sync', 'backup', 'cloud', 'storage'],
      action: () => { navigate('/sync'); onClose(); }
    },
    {
      id: 'nav-performance',
      title: 'Go to Performance',
      description: 'Monitor system performance and background tasks',
      icon: BarChart3,
      category: 'navigation',
      keywords: ['performance', 'monitoring', 'system', 'tasks'],
      action: () => { navigate('/performance'); onClose(); }
    },
    {
      id: 'nav-cache',
      title: 'Go to Cache Management',
      description: 'Monitor and optimize caching performance',
      icon: CommandIcon,
      category: 'navigation',
      keywords: ['cache', 'memory', 'optimization'],
      action: () => { navigate('/cache'); onClose(); }
    },
    
    // Action commands
    {
      id: 'action-add-book',
      title: 'Add New Book',
      description: 'Upload and process a new book',
      icon: FileText,
      category: 'actions',
      keywords: ['add', 'new', 'book', 'upload', 'import'],
      action: () => { 
        navigate('/library');
        onClose();
        // Trigger file upload dialog
        setTimeout(() => {
          window.dispatchEvent(new CustomEvent('lexicon:open-file-upload'));
        }, 100);
      }
    },
    {
      id: 'action-new-project',
      title: 'Create New Project',
      description: 'Start a new project or collection',
      icon: Settings,
      category: 'actions',
      keywords: ['create', 'new', 'project', 'collection'],
      action: () => { 
        onClose();
        // Trigger new project dialog
        window.dispatchEvent(new CustomEvent('lexicon:open-new-project'));
      }
    },
    {
      id: 'action-batch-import',
      title: 'Batch Import',
      description: 'Import multiple files at once',
      icon: Download,
      category: 'actions', 
      keywords: ['batch', 'import', 'multiple', 'bulk'],
      action: () => { 
        navigate('/batch');
        onClose();
      }
    },
    {
      id: 'action-settings',
      title: 'Open Settings',
      description: 'Configure application preferences',
      icon: Settings,
      category: 'actions',
      keywords: ['settings', 'preferences', 'config'],
      shortcut: '⌘,',
      action: () => { 
        onClose();
        // Trigger settings dialog
        window.dispatchEvent(new CustomEvent('lexicon:open-settings'));
      }
    },
    {
      id: 'action-notifications',
      title: 'View Notifications',
      description: 'Check recent notifications and updates',
      icon: CommandIcon,
      category: 'actions',
      keywords: ['notifications', 'updates', 'alerts'],
      action: () => { 
        onClose();
        // Trigger notifications dialog
        window.dispatchEvent(new CustomEvent('lexicon:open-notifications'));
      }
    },
    
    // Help commands
    {
      id: 'help-open',
      title: 'Open Help',
      description: 'View documentation and keyboard shortcuts',
      icon: HelpCircle,
      category: 'help',
      keywords: ['help', 'documentation', 'support', 'guide'],
      shortcut: 'F1',
      action: () => { 
        onClose();
        // Trigger help system
        window.dispatchEvent(new CustomEvent('lexicon:open-help'));
      }
    },
    {
      id: 'help-shortcuts',
      title: 'Keyboard Shortcuts',
      description: 'View all available keyboard shortcuts',
      icon: CommandIcon,
      category: 'help', 
      keywords: ['keyboard', 'shortcuts', 'hotkeys'],
      shortcut: '?',
      action: () => { 
        onClose();
        // Trigger shortcuts help
        window.dispatchEvent(new CustomEvent('lexicon:show-shortcuts'));
      }
    },
  ], [navigate, onClose]);

  // Filter commands based on query
  const filteredCommands = useMemo(() => {
    if (!query.trim()) return commands;
    
    const lowercaseQuery = query.toLowerCase();
    return commands.filter(command => 
      command.title.toLowerCase().includes(lowercaseQuery) ||
      command.description?.toLowerCase().includes(lowercaseQuery) ||
      command.keywords.some(keyword => keyword.toLowerCase().includes(lowercaseQuery)) ||
      command.category.toLowerCase().includes(lowercaseQuery)
    );
  }, [commands, query]);

  // Group commands by category
  const groupedCommands = useMemo(() => {
    const groups: Record<string, Command[]> = {};
    filteredCommands.forEach(command => {
      if (!groups[command.category]) {
        groups[command.category] = [];
      }
      groups[command.category].push(command);
    });
    return groups;
  }, [filteredCommands]);

  // Handle keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev => 
            prev < filteredCommands.length - 1 ? prev + 1 : 0
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => 
            prev > 0 ? prev - 1 : filteredCommands.length - 1
          );
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredCommands[selectedIndex]) {
            filteredCommands[selectedIndex].action();
          }
          break;
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredCommands, selectedIndex, onClose]);

  // Reset selection when query changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Reset query when dialog opens
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  const categoryLabels = {
    navigation: 'Navigation',
    actions: 'Actions',
    settings: 'Settings',
    help: 'Help & Support'
  };

  return (
    <Dialog open={isOpen} onClose={onClose}>
      <DialogContent className="max-w-2xl p-0 overflow-hidden">
        <div className="border-b">
          <div className="flex items-center px-4 py-3">
            <Search className="h-4 w-4 text-muted-foreground mr-3" />
            <Input
              placeholder="Type a command or search..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0"
              autoFocus
            />
            <Badge variant="outline" className="ml-3 font-mono text-xs">
              ⌘K
            </Badge>
          </div>
        </div>

        <div className="max-h-96 overflow-auto">
          {filteredCommands.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <Search className="h-8 w-8 mx-auto mb-3 opacity-50" />
              <p>No commands found</p>
              <p className="text-sm">Try searching for "dashboard", "library", or "help"</p>
            </div>
          ) : (
            <div className="p-2">
              {Object.entries(groupedCommands).map(([category, categoryCommands]) => (
                <div key={category} className="mb-4">
                  <div className="px-3 py-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {categoryLabels[category as keyof typeof categoryLabels]}
                  </div>
                  <div className="space-y-1">
                    {categoryCommands.map((command) => {
                      const globalIndex = filteredCommands.indexOf(command);
                      const isSelected = globalIndex === selectedIndex;
                      
                      return (
                        <button
                          key={command.id}
                          onClick={command.action}
                          className={`w-full flex items-center px-3 py-2 text-left rounded-lg transition-colors ${
                            isSelected 
                              ? 'bg-accent text-accent-foreground' 
                              : 'hover:bg-accent/50'
                          }`}
                        >
                          <command.icon className="h-4 w-4 mr-3 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <div className="font-medium truncate">{command.title}</div>
                            {command.description && (
                              <div className="text-sm text-muted-foreground truncate">
                                {command.description}
                              </div>
                            )}
                          </div>
                          {command.shortcut && (
                            <Badge variant="outline" className="ml-3 font-mono text-xs">
                              {command.shortcut}
                            </Badge>
                          )}
                          <ArrowRight className="h-3 w-3 ml-3 text-muted-foreground" />
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="border-t px-4 py-3 text-xs text-muted-foreground">
          <div className="flex items-center justify-between">
            <span>Use ↑↓ to navigate, ↵ to select, ESC to close</span>
            <span>Type to search</span>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Hook for using command palette
export function useCommandPalette() {
  const [isOpen, setIsOpen] = useState(false);

  // Listen for global command palette events
  useEffect(() => {
    const handleOpenCommandPalette = () => setIsOpen(true);
    window.addEventListener('lexicon:open-command-palette', handleOpenCommandPalette);
    
    return () => {
      window.removeEventListener('lexicon:open-command-palette', handleOpenCommandPalette);
    };
  }, []);

  return {
    isOpen,
    open: () => setIsOpen(true),
    close: () => setIsOpen(false),
    toggle: () => setIsOpen(prev => !prev),
  };
}
