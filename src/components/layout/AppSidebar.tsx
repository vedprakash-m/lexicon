import React, { useState, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Library, 
  FolderOpen,
  Settings,
  BarChart3,
  Plus,
  ChevronRight,
  ChevronDown,
  Cloud,
  Activity,
  FileText,
  Download,
  Zap,
  Database,
  Users,
  HelpCircle,
  Search,
  BookOpen,
  Brain,
  Shield,
  Cpu,
  HardDrive
} from 'lucide-react';
import { Button } from '../ui';
import { useSidebarStatus } from '@/hooks/useSidebarStatus';
import { useCatalogManager } from '@/hooks/useCatalogManager';
import { cn } from '../../lib/utils';

interface SidebarItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  count?: number;
  route?: string;
  children?: SidebarItem[];
}

export const AppSidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [expandedSections, setExpandedSections] = useState<string[]>(['library']);
  
  const { status: sidebarStatus, loading: statusLoading } = useSidebarStatus();
  const { books, stats, isLoading } = useCatalogManager();

  // Calculate book counts from catalog data
  const bookCounts = useMemo(() => {
    if (!books || books.length === 0) {
      return {
        total: 0,
        inProgress: 0,
        completed: 0,
        collections: 0
      };
    }

    const total = books.length;
    // For now, use simple categorization based on available data
    // We'll update this once we know the actual status fields in BookMetadata
    const inProgress = 0; // Placeholder - need to check actual status field
    const completed = total; // Assuming all cataloged books are processed
    
    // Count unique categories as collections for now
    const collections = new Set(books.flatMap(book => book.categories)).size;

    return {
      total,
      inProgress,
      completed,
      collections
    };
  }, [books]);

  // Dynamic sidebar items with real counts
  const sidebarItems: SidebarItem[] = useMemo(() => [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: BarChart3,
      route: '/',
    },
    {
      id: 'library',
      label: 'Enhanced Catalog',
      icon: Search,
      count: bookCounts.total,
      route: '/library',
      children: [
        { id: 'all-books', label: 'All Books', icon: BookOpen, count: bookCounts.total, route: '/library' },
        { id: 'in-progress', label: 'In Progress', icon: Download, count: bookCounts.inProgress, route: '/library?status=processing' },
        { id: 'completed', label: 'Completed', icon: Library, count: bookCounts.completed, route: '/library?status=completed' },
      ]
    },
    {
      id: 'collections',
      label: 'Collections',
      icon: FolderOpen,
      count: bookCounts.collections,
      route: '/projects',
      children: [
        { id: 'scripture', label: 'Structured Scriptures', icon: FolderOpen, count: 0, route: '/projects?type=scripture' },
        { id: 'philosophy', label: 'Philosophy', icon: FolderOpen, count: 0, route: '/projects?type=philosophy' },
        { id: 'literature', label: 'Literature', icon: FolderOpen, count: 0, route: '/projects?type=literature' },
        { id: 'reference', label: 'Reference', icon: FolderOpen, count: 0, route: '/projects?type=reference' },
      ]
    },
    {
      id: 'processing',
      label: 'Processing',
      icon: Settings,
      children: [
        { id: 'sources', label: 'Sources & Rules', icon: Download, count: 0, route: '/sources' },
        { id: 'scraping', label: 'Scraping Jobs', icon: Download, count: 0, route: '/scraping' },
        { id: 'batch', label: 'Batch Processing', icon: Download, count: 0, route: '/batch' },
        { id: 'chunking', label: 'Advanced Chunking', icon: Brain, route: '/chunking' },
        { id: 'export', label: 'Export Manager', icon: Download, route: '/export' },
        { id: 'queue', label: 'Processing Queue', icon: Download, count: sidebarStatus.processingCount, route: '/processing' },
        { id: 'profiles', label: 'Processing Profiles', icon: Settings, count: 0, route: '/processing/profiles' },
      ]
    },
    {
      id: 'sync',
      label: 'Sync & Backup',
      icon: Cloud,
      children: [
        { id: 'sync-manager', label: 'Sync Manager', icon: Cloud, route: '/sync' },
        { id: 'backups', label: 'Backup Manager', icon: HardDrive, route: '/backups' },
        { id: 'data-manager', label: 'Data Manager', icon: Database, route: '/data' },
      ]
    },
    {
      id: 'monitoring',
      label: 'Monitoring',
      icon: Activity,
      children: [
        { id: 'performance', label: 'Performance Monitor', icon: Cpu, route: '/monitoring' },
        { id: 'audit', label: 'Audit Logs', icon: FileText, route: '/audit' },
        { id: 'security', label: 'Security Dashboard', icon: Shield, route: '/security' },
      ]
    },
    {
      id: 'help',
      label: 'Help & Resources',
      icon: HelpCircle,
      children: [
        { id: 'docs', label: 'Documentation', icon: FileText, route: '/docs' },
        { id: 'api', label: 'API Reference', icon: FileText, route: '/api' },
        { id: 'community', label: 'Community', icon: Users, route: '/community' },
      ]
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: Settings,
      route: '/settings',
    },
  ], [bookCounts, sidebarStatus.processingCount]);
  
  const handleAddBook = () => {
    navigate('/library');
  };
  
  // Determine active item based on current path
  const getActiveItem = () => {
    const path = location.pathname;
    if (path === '/') return 'dashboard';
    if (path.startsWith('/projects')) return 'collections';
    if (path.startsWith('/library')) return 'library';
    if (path.startsWith('/sources') || path.startsWith('/scraping') || path.startsWith('/processing') || path.startsWith('/batch') || path.startsWith('/chunking') || path.startsWith('/export')) return 'processing';
    if (path.startsWith('/sync')) return 'sync';
    if (path.startsWith('/performance')) return 'performance';
    return 'dashboard';
  };
  
  const activeItem = getActiveItem();

  const toggleExpanded = (itemId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId);
    } else {
      newExpanded.add(itemId);
    }
    setExpandedSections(Array.from(newExpanded));
  };

  const renderSidebarItem = (item: SidebarItem, level = 0) => {
    const isExpanded = expandedSections.includes(item.id);
    const isActive = activeItem === item.id;
    const hasChildren = item.children && item.children.length > 0;

    return (
      <div key={item.id}>
        <Button
          variant={isActive ? "secondary" : "ghost"}
          className={cn(
            "w-full justify-start h-9 px-3",
            level > 0 && "ml-4 w-[calc(100%-1rem)]",
            isActive && "bg-secondary"
          )}
          onClick={() => {
            if (item.route) {
              navigate(item.route);
            }
            if (hasChildren) {
              toggleExpanded(item.id);
            }
          }}
          role={hasChildren ? "treeitem" : "link"}
          aria-expanded={hasChildren ? isExpanded : undefined}
          aria-current={isActive ? "page" : undefined}
          ariaLabel={`${item.label}${item.count ? `, ${item.count} items` : ''}`}
        >
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center space-x-3">
              <item.icon className="h-4 w-4" aria-hidden="true" />
              <span className="text-sm">{item.label}</span>
            </div>
            <div className="flex items-center space-x-1">
              {item.count && (
                <span 
                  className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded"
                  aria-label={`${item.count} items`}
                >
                  {item.count}
                </span>
              )}
              {hasChildren && (
                isExpanded ? 
                  <ChevronDown className="h-3 w-3" aria-hidden="true" /> : 
                  <ChevronRight className="h-3 w-3" aria-hidden="true" />
              )}
            </div>
          </div>
        </Button>

        {hasChildren && isExpanded && (
          <div className="mt-1 space-y-1" role="group" aria-label={`${item.label} submenu`}>
            {item.children!.map(child => renderSidebarItem(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <aside 
      className="w-64 border-r border-border bg-background/50 backdrop-blur supports-[backdrop-filter]:bg-background/80 flex flex-col"
      role="navigation"
      aria-label="Main navigation"
    >
      {/* Scrollable content area */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4">
          {/* Quick Actions */}
          <div className="mb-6">
            <Button 
              className="w-full justify-start" 
              size="sm"
              ariaLabel="Add new book to library"
              onClick={handleAddBook}
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Book
            </Button>
          </div>

          {/* Navigation */}
          <nav className="space-y-2" role="tree" aria-label="Main navigation tree">
            <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">
              Navigation
            </h2>
            <ul className="space-y-1" role="none">
              {sidebarItems.map(item => (
                <li key={item.id} role="none">
                  {renderSidebarItem(item)}
                </li>
              ))}
            </ul>
          </nav>

          {/* Status Section */}
          <div className="mt-8 pt-4 border-t border-border">
            <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">
              Status
            </h2>
            <div 
              className="space-y-2 text-sm text-muted-foreground"
              role="status"
              aria-label="System status information"
            >
              <div className="flex justify-between">
                <span>Storage Used</span>
                <span className={statusLoading ? 'text-muted-foreground' : 'text-foreground'}>
                  {statusLoading ? 'Loading...' : sidebarStatus.storageUsed}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Processing</span>
                <span className={`${statusLoading ? 'text-muted-foreground' : 
                  sidebarStatus.processingCount > 0 ? 'text-green-500' : 'text-muted-foreground'}`}>
                  {statusLoading ? 'Loading...' : 
                    sidebarStatus.processingCount > 0 
                      ? `${sidebarStatus.processingCount} active`
                      : '0 active'
                  }
                </span>
              </div>
              <div className="flex justify-between">
                <span>Last Sync</span>
                <span className={statusLoading ? 'text-muted-foreground' : 'text-foreground'}>
                  {statusLoading ? 'Loading...' : sidebarStatus.lastSync}
                </span>
              </div>
            </div>
          </div>
          
          {/* Bottom padding to ensure help button doesn't overlap */}
          <div className="h-16" />
        </div>
      </div>
    </aside>
  );
}
