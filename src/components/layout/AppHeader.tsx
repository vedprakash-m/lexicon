import { Search, Plus, Settings, Bell } from 'lucide-react';
import { Button, Input, TooltipWithShortcut, Badge } from '../ui';
import { ThemeToggle } from '../ui/theme-toggle';
import { SimpleHelpButton } from '../ui/simple-help-system';
import { NotificationsDialog, useNotifications } from '../notifications';
import { SettingsDialog as SettingsModalDialog } from '../settings/SettingsDialog';
import { NewProjectDialog } from '../project/NewProjectDialog';
import { useState, useEffect } from 'react';
import { useKeyboardShortcuts } from '../ui/keyboard-shortcuts';

export function AppHeader() {
  const [showNotifications, setShowNotifications] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showNewProject, setShowNewProject] = useState(false);
  const { unreadCount } = useNotifications();
  const { registerShortcut, unregisterShortcut } = useKeyboardShortcuts();

  // Register keyboard shortcuts and global event listeners
  useEffect(() => {
    const newProjectShortcut = {
      id: 'header-new-project',
      keys: ['Cmd', 'N'],
      description: 'Open New Project Dialog',
      action: () => setShowNewProject(true),
      category: 'actions' as const,
      global: true,
    };

    const settingsShortcut = {
      id: 'header-settings',
      keys: ['Cmd', ','],
      description: 'Open Settings',
      action: () => setShowSettings(true),
      category: 'navigation' as const,
      global: true,
    };

    registerShortcut(newProjectShortcut);
    registerShortcut(settingsShortcut);

    // Global event listeners for command palette actions
    const handleOpenNewProject = () => setShowNewProject(true);
    const handleOpenSettings = () => setShowSettings(true);
    const handleOpenNotifications = () => setShowNotifications(true);

    window.addEventListener('lexicon:open-new-project', handleOpenNewProject);
    window.addEventListener('lexicon:open-settings', handleOpenSettings);
    window.addEventListener('lexicon:open-notifications', handleOpenNotifications);

    return () => {
      unregisterShortcut('header-new-project');
      unregisterShortcut('header-settings');
      window.removeEventListener('lexicon:open-new-project', handleOpenNewProject);
      window.removeEventListener('lexicon:open-settings', handleOpenSettings);
      window.removeEventListener('lexicon:open-notifications', handleOpenNotifications);
    };
  }, [registerShortcut, unregisterShortcut]);
  return (
    <header className="h-14 border-b border-border flex items-center justify-between px-6 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      {/* Left section - Logo and title */}
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
          <span className="text-primary-foreground font-bold text-sm">L</span>
        </div>
        <h1 className="text-lg font-semibold">Lexicon</h1>
      </div>

      {/* Center section - Search */}
      <div className="flex-1 max-w-md mx-8" data-tour="search">
        <TooltipWithShortcut 
          content="Search your library or press ⌘K for quick commands" 
          shortcut="⌘K"
        >
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search books, collections..."
              className="pl-10 h-9"
              data-tour="command-trigger"
              onFocus={() => {
                // Trigger command palette instead of regular search
                window.dispatchEvent(new CustomEvent('lexicon:open-command-palette'));
              }}
              readOnly
            />
          </div>
        </TooltipWithShortcut>
      </div>

      {/* Right section - Actions */}
      <div className="flex items-center space-x-2">
        <TooltipWithShortcut 
          content="Add new book or start a new project" 
          shortcut="⌘N"
        >
          <Button 
            variant="ghost" 
            size="sm" 
            data-tour="new-project"
            onClick={() => setShowNewProject(true)}
          >
            <Plus className="h-4 w-4" />
            <span className="ml-2 hidden sm:inline">New</span>
          </Button>
        </TooltipWithShortcut>
        
        <TooltipWithShortcut 
          content="View notifications and processing updates"
        >
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => setShowNotifications(true)}
            className="relative"
          >
            <Bell className="h-4 w-4" />
            {unreadCount > 0 && (
              <Badge 
                variant="destructive" 
                className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center text-xs p-0"
              >
                {unreadCount}
              </Badge>
            )}
          </Button>
        </TooltipWithShortcut>
        
        <TooltipWithShortcut 
          content="Open application settings" 
          shortcut="⌘,"
        >
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => setShowSettings(true)}
          >
            <Settings className="h-4 w-4" />
          </Button>
        </TooltipWithShortcut>
        
        <SimpleHelpButton />
        
        <ThemeToggle />
      </div>

      {/* Dialogs */}
      <NotificationsDialog 
        isOpen={showNotifications} 
        onClose={() => setShowNotifications(false)} 
      />
      <SettingsModalDialog 
        isOpen={showSettings} 
        onClose={() => setShowSettings(false)} 
      />
      <NewProjectDialog 
        isOpen={showNewProject} 
        onClose={() => setShowNewProject(false)} 
      />
    </header>
  );
}
