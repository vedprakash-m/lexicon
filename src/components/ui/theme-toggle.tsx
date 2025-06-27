/**
 * Theme Toggle Component
 * 
 * Provides a toggle button for switching between light, dark, and system theme modes.
 */

import { Moon, Sun, Monitor } from 'lucide-react';
import { Button } from './button';
import { useTheme } from './theme-provider';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  const cycleTheme = () => {
    if (theme === 'light') {
      setTheme('dark');
    } else if (theme === 'dark') {
      setTheme('system');
    } else {
      setTheme('light');
    }
  };

  const getIcon = () => {
    switch (theme) {
      case 'light':
        return <Sun className="h-4 w-4" />;
      case 'dark':
        return <Moon className="h-4 w-4" />;
      case 'system':
        return <Monitor className="h-4 w-4" />;
      default:
        return <Sun className="h-4 w-4" />;
    }
  };

  const getLabel = () => {
    switch (theme) {
      case 'light':
        return 'Switch to dark mode';
      case 'dark':
        return 'Switch to system mode';
      case 'system':
        return 'Switch to light mode';
      default:
        return 'Toggle theme';
    }
  };

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={cycleTheme}
      aria-label={getLabel()}
      title={getLabel()}
    >
      {getIcon()}
    </Button>
  );
}
