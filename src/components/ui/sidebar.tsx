/**
 * Sidebar Component
 * 
 * A responsive sidebar navigation component for the main application layout.
 */

import React, { useState } from 'react';
import { cn } from '../../lib/utils';
import { Button } from './button';
import { 
  ChevronLeft, 
  ChevronRight, 
  Home, 
  FileText, 
  Settings, 
  Database,
  BarChart3,
  Plus,
  Folder
} from 'lucide-react';

export interface SidebarItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  href?: string;
  onClick?: () => void;
  badge?: string | number;
  children?: SidebarItem[];
}

export interface SidebarProps {
  items: SidebarItem[];
  activeItem?: string;
  onItemClick?: (item: SidebarItem) => void;
  collapsed?: boolean;
  onCollapsedChange?: (collapsed: boolean) => void;
  className?: string;
}

const defaultItems: SidebarItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: <Home className="h-4 w-4" />,
    href: '/',
  },
  {
    id: 'projects',
    label: 'Projects',
    icon: <Folder className="h-4 w-4" />,
    href: '/projects',
    children: [
      {
        id: 'create-project',
        label: 'Create New',
        icon: <Plus className="h-4 w-4" />,
        href: '/projects/new',
      },
    ],
  },
  {
    id: 'scraping',
    label: 'Web Scraping',
    icon: <FileText className="h-4 w-4" />,
    href: '/scraping',
  },
  {
    id: 'datasets',
    label: 'Datasets',
    icon: <Database className="h-4 w-4" />,
    href: '/datasets',
  },
  {
    id: 'analytics',
    label: 'Quality Analytics',
    icon: <BarChart3 className="h-4 w-4" />,
    href: '/analytics',
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: <Settings className="h-4 w-4" />,
    href: '/settings',
  },
];

export function Sidebar({ 
  items = defaultItems, 
  activeItem, 
  onItemClick, 
  collapsed = false, 
  onCollapsedChange,
  className 
}: SidebarProps) {
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  const toggleExpanded = (itemId: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId);
    } else {
      newExpanded.add(itemId);
    }
    setExpandedItems(newExpanded);
  };

  const handleItemClick = (item: SidebarItem) => {
    if (item.children && !collapsed) {
      toggleExpanded(item.id);
    }
    onItemClick?.(item);
  };

  const renderItem = (item: SidebarItem, level = 0) => {
    const isActive = activeItem === item.id;
    const isExpanded = expandedItems.has(item.id);
    const hasChildren = item.children && item.children.length > 0;

    return (
      <div key={item.id}>
        <button
          onClick={() => handleItemClick(item)}
          className={cn(
            'w-full flex items-center justify-between px-3 py-2 text-sm font-medium rounded-md transition-colors',
            'hover:bg-accent hover:text-accent-foreground',
            'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
            isActive && 'bg-accent text-accent-foreground',
            level > 0 && 'ml-4 w-[calc(100%-1rem)]',
            collapsed && 'justify-center px-2'
          )}
          title={collapsed ? item.label : undefined}
        >
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              {item.icon}
            </div>
            {!collapsed && (
              <span className="truncate">
                {item.label}
              </span>
            )}
          </div>
          
          {!collapsed && (
            <div className="flex items-center space-x-1">
              {item.badge && (
                <span className="bg-primary text-primary-foreground text-xs px-1.5 py-0.5 rounded-full">
                  {item.badge}
                </span>
              )}
              {hasChildren && (
                <ChevronRight 
                  className={cn(
                    'h-4 w-4 transition-transform',
                    isExpanded && 'rotate-90'
                  )} 
                />
              )}
            </div>
          )}
        </button>

        {hasChildren && !collapsed && isExpanded && (
          <div className="mt-1 space-y-1">
            {item.children!.map(child => renderItem(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div
      className={cn(
        'flex flex-col h-full bg-card border-r border-border transition-all duration-200',
        collapsed ? 'w-16' : 'w-64',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        {!collapsed && (
          <div>
            <h2 className="text-lg font-semibold text-card-foreground">Lexicon</h2>
            <p className="text-xs text-muted-foreground">RAG Dataset Tool</p>
          </div>
        )}
        {onCollapsedChange && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onCollapsedChange(!collapsed)}
            className="h-8 w-8"
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        )}
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 overflow-y-auto p-2">
        <div className="space-y-1">
          {items.map(item => renderItem(item))}
        </div>
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="p-4 border-t border-border">
          <div className="text-xs text-muted-foreground">
            Version 1.0.0
          </div>
        </div>
      )}
    </div>
  );
}
