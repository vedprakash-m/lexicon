/**
 * Header Component
 * 
 * The main application header with navigation, search, and user controls.
 */

import React from 'react';
import { Search, Bell, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './button';
import { Input } from './input';
import { ThemeToggle } from './theme-toggle';

export interface HeaderProps {
  title?: string;
  showSearch?: boolean;
  onSearchChange?: (value: string) => void;
  className?: string;
  actions?: React.ReactNode;
}

export function Header({ 
  title = 'Dashboard', 
  showSearch = true, 
  onSearchChange,
  className,
  actions
}: HeaderProps) {
  return (
    <header
      className={cn(
        'flex items-center justify-between h-16 px-6 bg-card border-b border-border',
        className
      )}
    >
      {/* Left section */}
      <div className="flex items-center space-x-4">
        <h1 className="text-xl font-semibold text-card-foreground">
          {title}
        </h1>
        
        {showSearch && (
          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search..."
              className="pl-10"
              onChange={(e) => onSearchChange?.(e.target.value)}
            />
          </div>
        )}
      </div>

      {/* Right section */}
      <div className="flex items-center space-x-2">
        {actions}
        
        <Button variant="ghost" size="icon">
          <Bell className="h-4 w-4" />
        </Button>
        
        <ThemeToggle />
        
        <Button variant="ghost" size="icon">
          <User className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}
