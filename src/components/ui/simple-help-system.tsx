import React, { useState } from 'react';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  Button, 
  Input,
  Badge,
  Card
} from '../ui';
import { 
  HelpCircle, 
  Search, 
  Keyboard, 
  Book, 
  MessageCircle, 
  ExternalLink
} from 'lucide-react';
import { useKeyboardShortcuts } from './keyboard-shortcuts';
import { TooltipWithShortcut } from './tooltip';

interface SimpleHelpSystemProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SimpleHelpSystem({ isOpen, onClose }: SimpleHelpSystemProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const { shortcuts } = useKeyboardShortcuts();

  const quickTips = [
    {
      title: "Getting Started",
      icon: Book,
      content: "Add your first book using drag & drop or the 'Add Book' button. Configure processing settings or use smart defaults."
    },
    {
      title: "Keyboard Navigation",
      icon: Keyboard,
      content: "Use keyboard shortcuts to navigate quickly. Press '?' to see all shortcuts, ⌘K for command palette."
    },
    {
      title: "Processing Tips",
      icon: MessageCircle,
      content: "Smart processing works for most books. Use custom settings for specialized content like spiritual texts."
    }
  ];

  return (
    <Dialog open={isOpen} onClose={onClose}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <HelpCircle className="h-5 w-5" />
            <span>Help & Quick Start</span>
            <Badge variant="secondary" className="ml-auto">
              Lexicon Guide
            </Badge>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search help topics..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Quick Tips */}
          <div className="grid gap-4">
            <h3 className="text-lg font-semibold">Quick Tips</h3>
            {quickTips.map((tip, index) => (
              <Card key={index} className="p-4">
                <div className="flex items-start gap-3">
                  <tip.icon className="h-5 w-5 mt-0.5 text-primary" />
                  <div>
                    <h4 className="font-medium mb-2">{tip.title}</h4>
                    <p className="text-sm text-muted-foreground">{tip.content}</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Keyboard Shortcuts */}
          <Card className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <Keyboard className="h-5 w-5" />
              <h3 className="text-lg font-semibold">Essential Shortcuts</h3>
              <Badge variant="outline" className="text-xs">
                {shortcuts.length} total
              </Badge>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {shortcuts.slice(0, 6).map((shortcut) => (
                <div 
                  key={shortcut.id}
                  className="flex items-center justify-between p-3 bg-muted/50 rounded-md"
                >
                  <span className="text-sm">{shortcut.description}</span>
                  <div className="flex items-center gap-1">
                    {shortcut.keys.map((key, index) => (
                      <React.Fragment key={index}>
                        <kbd className="px-2 py-1 text-xs bg-background border border-border rounded">
                          {key === 'Cmd' ? '⌘' : key === 'Shift' ? '⇧' : key}
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
            
            <div className="mt-4 pt-4 border-t">
              <p className="text-sm text-muted-foreground">
                Press <kbd className="px-2 py-1 text-xs bg-background border border-border rounded">?</kbd> 
                {' '}to see all keyboard shortcuts
              </p>
            </div>
          </Card>

          {/* Support */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Need More Help?</h3>
            <div className="flex gap-3">
              <Button variant="outline" size="sm">
                <Book className="h-4 w-4 mr-2" />
                User Guide
              </Button>
              <Button variant="outline" size="sm">
                <MessageCircle className="h-4 w-4 mr-2" />
                Support
              </Button>
              <Button variant="outline" size="sm">
                <ExternalLink className="h-4 w-4 mr-2" />
                Documentation
              </Button>
            </div>
          </Card>
        </div>

        <div className="flex justify-end pt-4 border-t">
          <Button onClick={onClose}>Close</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Simple help button component
interface SimpleHelpButtonProps {
  className?: string;
  variant?: 'icon' | 'button';
}

export function SimpleHelpButton({ className, variant = 'icon' }: SimpleHelpButtonProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (variant === 'button') {
    return (
      <>
        <Button 
          variant="outline" 
          onClick={() => setIsOpen(true)}
          className={className}
        >
          <HelpCircle className="h-4 w-4 mr-2" />
          Help
        </Button>
        <SimpleHelpSystem isOpen={isOpen} onClose={() => setIsOpen(false)} />
      </>
    );
  }

  return (
    <>
      <TooltipWithShortcut content="Open Help & Quick Start Guide" shortcut="F1">
        <Button 
          variant="ghost" 
          size="sm"
          onClick={() => setIsOpen(true)}
          className={className}
        >
          <HelpCircle className="h-4 w-4" />
        </Button>
      </TooltipWithShortcut>
      <SimpleHelpSystem isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  );
}
