import { Search, Plus, Settings, Bell } from 'lucide-react';
import { Button, Input, TooltipWithShortcut } from '../ui';
import { ThemeToggle } from '../ui/theme-toggle';
import { SimpleHelpButton } from '../ui/simple-help-system';

export function AppHeader() {
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
          <Button variant="ghost" size="sm" data-tour="new-project">
            <Plus className="h-4 w-4" />
            <span className="ml-2 hidden sm:inline">New</span>
          </Button>
        </TooltipWithShortcut>
        
        <TooltipWithShortcut 
          content="View notifications and processing updates"
        >
          <Button variant="ghost" size="sm">
            <Bell className="h-4 w-4" />
          </Button>
        </TooltipWithShortcut>
        
        <TooltipWithShortcut 
          content="Open application settings" 
          shortcut="⌘,"
        >
          <Button variant="ghost" size="sm">
            <Settings className="h-4 w-4" />
          </Button>
        </TooltipWithShortcut>
        
        <SimpleHelpButton />
        
        <ThemeToggle />
      </div>
    </header>
  );
}
