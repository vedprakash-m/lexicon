import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Library, 
  FolderOpen, 
  Download, 
  Settings, 
  BarChart3, 
  BookOpen, 
  Plus,
  ChevronRight,
  ChevronDown,
  Brain,
  Search,
  Cloud,
  Shield,
  Activity,
  Cpu,
  HardDrive,
  Database
} from 'lucide-react';
import { Button } from '../ui';
import { cn } from '../../lib/utils';

interface SidebarItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  count?: number;
  route?: string;
  children?: SidebarItem[];
}

const sidebarItems: SidebarItem[] = [
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
    count: 247,
    route: '/library',
    children: [
      { id: 'all-books', label: 'All Books', icon: BookOpen, count: 247, route: '/library' },
      { id: 'in-progress', label: 'In Progress', icon: Download, count: 3, route: '/library?status=processing' },
      { id: 'completed', label: 'Completed', icon: Library, count: 244, route: '/library?status=completed' },
    ]
  },
  {
    id: 'collections',
    label: 'Collections',
    icon: FolderOpen,
    count: 12,
    route: '/projects',
    children: [
      { id: 'scripture', label: 'Structured Scriptures', icon: FolderOpen, count: 156, route: '/projects?type=scripture' },
      { id: 'philosophy', label: 'Philosophy', icon: FolderOpen, count: 45, route: '/projects?type=philosophy' },
      { id: 'literature', label: 'Literature', icon: FolderOpen, count: 32, route: '/projects?type=literature' },
      { id: 'reference', label: 'Reference', icon: FolderOpen, count: 14, route: '/projects?type=reference' },
    ]
  },
  {
    id: 'processing',
    label: 'Processing',
    icon: Settings,
    children: [
      { id: 'sources', label: 'Sources & Rules', icon: Download, count: 5, route: '/sources' },
      { id: 'scraping', label: 'Scraping Jobs', icon: Download, count: 3, route: '/scraping' },
      { id: 'batch', label: 'Batch Processing', icon: Download, count: 1, route: '/batch' },
      { id: 'chunking', label: 'Advanced Chunking', icon: Brain, route: '/chunking' },
      { id: 'export', label: 'Export Manager', icon: Download, route: '/export' },
      { id: 'queue', label: 'Processing Queue', icon: Download, count: 2, route: '/processing' },
      { id: 'profiles', label: 'Processing Profiles', icon: Settings, count: 4, route: '/processing/profiles' },
    ]
  },
  {
    id: 'sync',
    label: 'Sync & Backup',
    icon: Cloud,
    route: '/sync',
    children: [
      { id: 'cloud-sync', label: 'Cloud Sync', icon: Cloud, route: '/sync' },
      { id: 'backups', label: 'Backups', icon: Shield, route: '/sync' },
    ]
  },
  {
    id: 'performance',
    label: 'Performance',
    icon: Activity,
    route: '/performance',
    children: [
      { id: 'system-metrics', label: 'System Metrics', icon: Cpu, route: '/performance' },
      { id: 'background-tasks', label: 'Background Tasks', icon: HardDrive, route: '/performance' },
      { id: 'cache-management', label: 'Cache Management', icon: Database, route: '/cache' },
    ]
  },
];

export function AppSidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set(['library', 'collections']));
  
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
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId);
    } else {
      newExpanded.add(itemId);
    }
    setExpandedItems(newExpanded);
  };

  const renderSidebarItem = (item: SidebarItem, level = 0) => {
    const isExpanded = expandedItems.has(item.id);
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
      className="w-64 border-r border-border bg-background/50 backdrop-blur supports-[backdrop-filter]:bg-background/80"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="p-4">
        {/* Quick Actions */}
        <div className="mb-6">
          <Button 
            className="w-full justify-start" 
            size="sm"
            ariaLabel="Add new book to library"
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
              <span>2.4 GB</span>
            </div>
            <div className="flex justify-between">
              <span>Processing</span>
              <span className="text-blue-500">2 active</span>
            </div>
            <div className="flex justify-between">
              <span>Last Sync</span>
              <span>2 min ago</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
