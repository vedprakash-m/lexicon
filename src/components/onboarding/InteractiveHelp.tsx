import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { 
  Search, 
  HelpCircle, 
  BookOpen, 
  Video, 
  FileText, 
  MessageCircle, 
  ExternalLink,
  ChevronRight,
  Lightbulb,
  Keyboard,
  Settings,
  Users,
  Zap
} from 'lucide-react';

interface HelpItem {
  id: string;
  title: string;
  category: 'getting-started' | 'features' | 'troubleshooting' | 'shortcuts' | 'advanced';
  type: 'article' | 'video' | 'tutorial' | 'faq';
  content: string;
  duration?: string;
  tags: string[];
  popular?: boolean;
  related?: string[];
}

const HELP_ITEMS: HelpItem[] = [
  {
    id: 'first-steps',
    title: 'Getting Started with Lexicon',
    category: 'getting-started',
    type: 'tutorial',
    content: 'Learn the basics of creating projects, importing documents, and organizing your knowledge base.',
    duration: '5 min',
    tags: ['basics', 'tutorial', 'new-user'],
    popular: true,
    related: ['project-creation', 'document-import']
  },
  {
    id: 'project-creation',
    title: 'Creating Your First Project',
    category: 'getting-started',
    type: 'article',
    content: 'Step-by-step guide to creating and configuring a new project in Lexicon.',
    duration: '3 min',
    tags: ['project', 'setup', 'organization'],
    popular: true,
    related: ['document-import', 'workspace-setup']
  },
  {
    id: 'keyboard-shortcuts',
    title: 'Essential Keyboard Shortcuts',
    category: 'shortcuts',
    type: 'article',
    content: 'Master Lexicon with these time-saving keyboard shortcuts and hotkeys.',
    duration: '2 min',
    tags: ['shortcuts', 'productivity', 'keyboard'],
    popular: true,
    related: ['command-palette', 'navigation']
  },
  {
    id: 'document-analysis',
    title: 'AI-Powered Document Analysis',
    category: 'features',
    type: 'video',
    content: 'Discover how to use AI features for document insights, summaries, and pattern recognition.',
    duration: '8 min',
    tags: ['ai', 'analysis', 'insights'],
    related: ['annotations', 'search-features']
  },
  {
    id: 'collaboration',
    title: 'Team Collaboration Features',
    category: 'features',
    type: 'tutorial',
    content: 'Learn how to share projects, collaborate in real-time, and manage team permissions.',
    duration: '6 min',
    tags: ['collaboration', 'sharing', 'teams'],
    related: ['permissions', 'comments']
  },
  {
    id: 'search-tips',
    title: 'Advanced Search Techniques',
    category: 'features',
    type: 'article',
    content: 'Master semantic search, filters, and query operators to find exactly what you need.',
    duration: '4 min',
    tags: ['search', 'filters', 'operators'],
    popular: true,
    related: ['document-analysis', 'organization']
  },
  {
    id: 'troubleshooting-import',
    title: 'Fixing Document Import Issues',
    category: 'troubleshooting',
    type: 'faq',
    content: 'Common solutions for document import problems and file format compatibility.',
    duration: '2 min',
    tags: ['import', 'troubleshooting', 'files'],
    related: ['supported-formats', 'project-creation']
  },
  {
    id: 'performance-optimization',
    title: 'Optimizing Performance for Large Projects',
    category: 'advanced',
    type: 'article',
    content: 'Tips and techniques for maintaining optimal performance with large document collections.',
    duration: '5 min',
    tags: ['performance', 'optimization', 'large-projects'],
    related: ['organization', 'best-practices']
  }
];

const CATEGORIES = [
  { id: 'getting-started', label: 'Getting Started', icon: Lightbulb, color: 'text-green-600' },
  { id: 'features', label: 'Features', icon: Zap, color: 'text-blue-600' },
  { id: 'shortcuts', label: 'Shortcuts', icon: Keyboard, color: 'text-purple-600' },
  { id: 'troubleshooting', label: 'Troubleshooting', icon: Settings, color: 'text-orange-600' },
  { id: 'advanced', label: 'Advanced', icon: Users, color: 'text-red-600' }
] as const;

const TYPE_ICONS = {
  article: FileText,
  video: Video,
  tutorial: BookOpen,
  faq: MessageCircle
};

interface InteractiveHelpProps {
  isOpen: boolean;
  onClose: () => void;
  initialQuery?: string;
}

export function InteractiveHelp({ isOpen, onClose, initialQuery = '' }: InteractiveHelpProps) {
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<HelpItem | null>(null);
  const [filteredItems, setFilteredItems] = useState(HELP_ITEMS);

  useEffect(() => {
    let filtered = HELP_ITEMS;

    // Filter by category
    if (selectedCategory) {
      filtered = filtered.filter(item => item.category === selectedCategory);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(item =>
        item.title.toLowerCase().includes(query) ||
        item.content.toLowerCase().includes(query) ||
        item.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }

    setFilteredItems(filtered);
  }, [searchQuery, selectedCategory]);

  const popularItems = HELP_ITEMS.filter(item => item.popular);

  const handleItemClick = (item: HelpItem) => {
    setSelectedItem(item);
  };

  const handleCategoryClick = (categoryId: string) => {
    setSelectedCategory(selectedCategory === categoryId ? null : categoryId);
  };

  return (
    <Dialog open={isOpen} onClose={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <HelpCircle className="w-5 h-5" />
            Help & Documentation
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 flex overflow-hidden">
          {/* Sidebar */}
          <div className="w-80 border-r flex flex-col">
            {/* Search */}
            <div className="p-4 border-b">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search help articles..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Categories */}
            <div className="flex-1 overflow-y-auto">
              <div className="p-4 space-y-4">
                {/* Popular Items */}
                {!searchQuery && !selectedCategory && (
                  <div className="space-y-2">
                    <h3 className="font-medium text-sm text-muted-foreground">Popular</h3>
                    {popularItems.map((item) => {
                      const TypeIcon = TYPE_ICONS[item.type];
                      return (
                        <button
                          key={item.id}
                          onClick={() => handleItemClick(item)}
                          className="w-full text-left p-2 rounded-lg hover:bg-muted/50 transition-colors"
                        >
                          <div className="flex items-start gap-2">
                            <TypeIcon className="w-4 h-4 mt-0.5 text-muted-foreground" />
                            <div className="flex-1 min-w-0">
                              <div className="font-medium text-sm">{item.title}</div>
                              <div className="text-xs text-muted-foreground flex items-center gap-2 mt-1">
                                {item.duration && (
                                  <span>{item.duration}</span>
                                )}
                                <Badge variant="outline" className="text-xs px-1 py-0">
                                  {item.type}
                                </Badge>
                              </div>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}

                {/* Categories */}
                <div className="space-y-2">
                  <h3 className="font-medium text-sm text-muted-foreground">Categories</h3>
                  {CATEGORIES.map((category) => {
                    const Icon = category.icon;
                    const isSelected = selectedCategory === category.id;
                    const categoryItems = filteredItems.filter(item => item.category === category.id);
                    
                    return (
                      <div key={category.id}>
                        <button
                          onClick={() => handleCategoryClick(category.id)}
                          className={`w-full text-left p-2 rounded-lg transition-colors flex items-center justify-between ${
                            isSelected ? 'bg-primary/10 text-primary' : 'hover:bg-muted/50'
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <Icon className={`w-4 h-4 ${isSelected ? 'text-primary' : category.color}`} />
                            <span className="font-medium text-sm">{category.label}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Badge variant="outline" className="text-xs">
                              {categoryItems.length}
                            </Badge>
                            <ChevronRight className={`w-3 h-3 transition-transform ${
                              isSelected ? 'rotate-90' : ''
                            }`} />
                          </div>
                        </button>
                        
                        {/* Category Items */}
                        {isSelected && categoryItems.length > 0 && (
                          <div className="ml-6 mt-2 space-y-1">
                            {categoryItems.map((item) => {
                              const TypeIcon = TYPE_ICONS[item.type];
                              return (
                                <button
                                  key={item.id}
                                  onClick={() => handleItemClick(item)}
                                  className="w-full text-left p-2 rounded-lg hover:bg-muted/50 transition-colors"
                                >
                                  <div className="flex items-start gap-2">
                                    <TypeIcon className="w-3 h-3 mt-0.5 text-muted-foreground" />
                                    <div className="flex-1 min-w-0">
                                      <div className="font-medium text-sm">{item.title}</div>
                                      {item.duration && (
                                        <div className="text-xs text-muted-foreground mt-1">
                                          {item.duration}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                </button>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* All Items (when searching) */}
                {(searchQuery || (!selectedCategory && filteredItems.length > 0)) && (
                  <div className="space-y-2">
                    {searchQuery && (
                      <h3 className="font-medium text-sm text-muted-foreground">
                        Search Results ({filteredItems.length})
                      </h3>
                    )}
                    {filteredItems.map((item) => {
                      const TypeIcon = TYPE_ICONS[item.type];
                      return (
                        <button
                          key={item.id}
                          onClick={() => handleItemClick(item)}
                          className="w-full text-left p-2 rounded-lg hover:bg-muted/50 transition-colors"
                        >
                          <div className="flex items-start gap-2">
                            <TypeIcon className="w-4 h-4 mt-0.5 text-muted-foreground" />
                            <div className="flex-1 min-w-0">
                              <div className="font-medium text-sm">{item.title}</div>
                              <div className="text-xs text-muted-foreground flex items-center gap-2 mt-1">
                                {item.duration && (
                                  <span>{item.duration}</span>
                                )}
                                <Badge variant="outline" className="text-xs px-1 py-0">
                                  {item.type}
                                </Badge>
                              </div>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}

                {/* No Results */}
                {filteredItems.length === 0 && searchQuery && (
                  <div className="text-center py-8 text-muted-foreground">
                    <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No help articles found</p>
                    <p className="text-xs">Try different keywords or browse categories</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto">
            {selectedItem ? (
              <div className="p-6 space-y-6">
                {/* Header */}
                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      {(() => {
                        const TypeIcon = TYPE_ICONS[selectedItem.type];
                        return <TypeIcon className="w-5 h-5 text-muted-foreground" />;
                      })()}
                      <Badge variant="outline" className="capitalize">
                        {selectedItem.type}
                      </Badge>
                      {selectedItem.duration && (
                        <Badge variant="secondary">
                          {selectedItem.duration}
                        </Badge>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedItem(null)}
                    >
                      Back to List
                    </Button>
                  </div>
                  
                  <h2 className="text-2xl font-bold">{selectedItem.title}</h2>
                  
                  <div className="flex flex-wrap gap-1">
                    {selectedItem.tags.map((tag) => (
                      <Badge key={tag} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Content */}
                <Card>
                  <CardContent className="p-6">
                    <p className="text-muted-foreground leading-relaxed">
                      {selectedItem.content}
                    </p>
                    
                    {selectedItem.type === 'video' && (
                      <div className="mt-4">
                        <Button className="flex items-center gap-2">
                          <Video className="w-4 h-4" />
                          Watch Video
                          <ExternalLink className="w-3 h-3" />
                        </Button>
                      </div>
                    )}
                    
                    {selectedItem.type === 'tutorial' && (
                      <div className="mt-4">
                        <Button className="flex items-center gap-2">
                          <BookOpen className="w-4 h-4" />
                          Start Tutorial
                          <ChevronRight className="w-3 h-3" />
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Related Items */}
                {selectedItem.related && selectedItem.related.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="font-medium">Related Articles</h3>
                    <div className="grid gap-3">
                      {selectedItem.related.map((relatedId) => {
                        const relatedItem = HELP_ITEMS.find(item => item.id === relatedId);
                        if (!relatedItem) return null;
                        
                        const TypeIcon = TYPE_ICONS[relatedItem.type];
                        return (
                          <Card
                            key={relatedId}
                            className="cursor-pointer hover:shadow-md transition-shadow"
                            onClick={() => handleItemClick(relatedItem)}
                          >
                            <CardContent className="p-4">
                              <div className="flex items-start gap-3">
                                <TypeIcon className="w-4 h-4 mt-0.5 text-muted-foreground" />
                                <div className="flex-1">
                                  <h4 className="font-medium text-sm">{relatedItem.title}</h4>
                                  <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                                    {relatedItem.content}
                                  </p>
                                </div>
                                <ChevronRight className="w-4 h-4 text-muted-foreground" />
                              </div>
                            </CardContent>
                          </Card>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              /* Welcome State */
              <div className="flex items-center justify-center h-full p-6">
                <div className="text-center space-y-4 max-w-md">
                  <div className="w-16 h-16 mx-auto bg-primary/10 rounded-full flex items-center justify-center">
                    <HelpCircle className="w-8 h-8 text-primary" />
                  </div>
                  <h3 className="text-xl font-semibold">Welcome to Help</h3>
                  <p className="text-muted-foreground">
                    Search for specific topics or browse categories to find helpful articles, tutorials, and guides.
                  </p>
                  <div className="flex flex-wrap justify-center gap-2 pt-4">
                    {CATEGORIES.slice(0, 3).map((category) => (
                      <Button
                        key={category.id}
                        variant="outline"
                        size="sm"
                        onClick={() => handleCategoryClick(category.id)}
                        className="flex items-center gap-2"
                      >
                        <category.icon className={`w-4 h-4 ${category.color}`} />
                        {category.label}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Quick help trigger component
interface QuickHelpProps {
  onOpenHelp: (query?: string) => void;
}

export function QuickHelp({ onOpenHelp }: QuickHelpProps) {
  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => onOpenHelp()}
      className="fixed bottom-4 left-4 z-40 shadow-lg"
      title="Get Help"
    >
      <HelpCircle className="w-4 h-4 mr-2" />
      Help
    </Button>
  );
}
