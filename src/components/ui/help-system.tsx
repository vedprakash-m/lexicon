import React, { useState, useEffect } from 'react';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  Button, 
  Input,
  Tabs,
  TabPanels,
  TabPanel,
  TabList,
  Tab,
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
import { useKeyboardShortcuts, formatShortcut } from './keyboard-shortcuts';
import { QuickTooltip } from './tooltip';

interface HelpSection {
  id: string;
  title: string;
  content: React.ReactNode;
  category: 'getting-started' | 'features' | 'troubleshooting' | 'reference';
  keywords: string[];
}

const helpSections: HelpSection[] = [
  {
    id: 'first-steps',
    title: 'Getting Started with Lexicon',
    category: 'getting-started',
    keywords: ['start', 'begin', 'first', 'setup', 'new'],
    content: (
      <div className="space-y-4">
        <p>Welcome to Lexicon! Here's how to get started:</p>
        <ol className="list-decimal list-inside space-y-2">
          <li>Add your first book using the "Add Book" button or drag and drop a file</li>
          <li>Configure processing settings or use smart defaults</li>
          <li>Monitor processing progress in the dashboard</li>
          <li>Export your processed datasets in various formats</li>
        </ol>
        <div className="bg-muted p-4 rounded-lg">
          <p className="font-medium">💡 Pro Tip:</p>
          <p>Start with a shorter book to familiarize yourself with the processing workflow.</p>
        </div>
      </div>
    )
  },
  {
    id: 'adding-books',
    title: 'Adding and Managing Books',
    category: 'features',
    keywords: ['add', 'book', 'upload', 'import', 'file', 'pdf', 'epub'],
    content: (
      <div className="space-y-4">
        <p>Lexicon supports multiple ways to add books to your library:</p>
        <ul className="list-disc list-inside space-y-2">
          <li><strong>Drag & Drop:</strong> Simply drag files onto the library interface</li>
          <li><strong>File Browser:</strong> Click "Add Book" and select files</li>
          <li><strong>URL Import:</strong> Import books directly from web URLs</li>
          <li><strong>Batch Import:</strong> Process multiple files at once</li>
        </ul>
        <p><strong>Supported formats:</strong> PDF, EPUB, MOBI, TXT, and web scraping</p>
      </div>
    )
  },
  {
    id: 'processing-options',
    title: 'Understanding Processing Options',
    category: 'features',
    keywords: ['process', 'chunk', 'settings', 'quality', 'export'],
    content: (
      <div className="space-y-4">
        <p>Lexicon offers flexible processing options for different use cases:</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-muted p-4 rounded-lg">
            <h4 className="font-medium mb-2">Smart Processing</h4>
            <p className="text-sm">Automatically detects content type and applies optimal settings</p>
          </div>
          <div className="bg-muted p-4 rounded-lg">
            <h4 className="font-medium mb-2">Custom Processing</h4>
            <p className="text-sm">Fine-tune chunk size, overlap, and export formats</p>
          </div>
        </div>
        <p>Most users should start with Smart Processing and only customize when needed.</p>
      </div>
    )
  },
  {
    id: 'export-formats',
    title: 'Export Formats and Integration',
    category: 'features',
    keywords: ['export', 'format', 'json', 'csv', 'langchain', 'llamaindex'],
    content: (
      <div className="space-y-4">
        <p>Export your processed datasets in formats optimized for different use cases:</p>
        <ul className="list-disc list-inside space-y-2">
          <li><strong>JSON/JSONL:</strong> Perfect for LangChain and LlamaIndex</li>
          <li><strong>CSV:</strong> Great for spreadsheet analysis</li>
          <li><strong>Parquet:</strong> Efficient for large datasets</li>
          <li><strong>Markdown:</strong> Compatible with note-taking apps</li>
        </ul>
      </div>
    )
  },
  {
    id: 'performance-issues',
    title: 'Performance and Memory Issues',
    category: 'troubleshooting',
    keywords: ['slow', 'memory', 'performance', 'crash', 'freeze'],
    content: (
      <div className="space-y-4">
        <p>If you're experiencing performance issues:</p>
        <ul className="list-disc list-inside space-y-2">
          <li>Check available disk space (need at least 2GB free)</li>
          <li>Close other memory-intensive applications</li>
          <li>Process books sequentially rather than in parallel</li>
          <li>Use smaller chunk sizes for very large books</li>
        </ul>
        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
          <p className="font-medium text-yellow-800">⚠️ Memory Recommendation:</p>
          <p className="text-yellow-700">For best performance, ensure at least 4GB RAM available.</p>
        </div>
      </div>
    )
  },
  {
    id: 'processing-failed',
    title: 'Processing Failed or Incomplete',
    category: 'troubleshooting',
    keywords: ['failed', 'error', 'incomplete', 'stuck', 'broken'],
    content: (
      <div className="space-y-4">
        <p>If processing fails or gets stuck:</p>
        <ol className="list-decimal list-inside space-y-2">
          <li>Check the file format is supported</li>
          <li>Ensure the file isn't corrupted or password-protected</li>
          <li>Try processing a smaller test file first</li>
          <li>Check the processing logs in the Performance dashboard</li>
          <li>Restart the application if needed</li>
        </ol>
      </div>
    )
  }
];

interface HelpSystemProps {
  isOpen: boolean;
  onClose: () => void;
}

export function HelpSystem({ isOpen, onClose }: HelpSystemProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredSections, setFilteredSections] = useState(helpSections);
  const [activeCategory, setActiveCategory] = useState<string>('getting-started');
  const { shortcuts } = useKeyboardShortcuts();

  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredSections(helpSections);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = helpSections.filter(section =>
      section.title.toLowerCase().includes(query) ||
      section.keywords.some(keyword => keyword.toLowerCase().includes(query))
    );
    setFilteredSections(filtered);
  }, [searchQuery]);

  const categorySections = filteredSections.filter(s => s.category === activeCategory);

  return (
    <Dialog open={isOpen} onClose={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <HelpCircle className="h-5 w-5" />
            <span>Help & Documentation</span>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search help topics..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          <Tabs>
            <TabList className="grid w-full grid-cols-4 p-1 bg-muted rounded-lg">
              <Tab className="px-3 py-2 text-sm font-medium">Getting Started</Tab>
              <Tab className="px-3 py-2 text-sm font-medium">Features</Tab>
              <Tab className="px-3 py-2 text-sm font-medium">Troubleshooting</Tab>
              <Tab className="px-3 py-2 text-sm font-medium">Reference</Tab>
            </TabList>

            <TabPanels className="mt-6">
              <TabPanel className="space-y-4">
              <div className="grid gap-4">
                {categorySections.map(section => (
                  <Card key={section.id} className="p-6">
                    <h3 className="text-lg font-semibold mb-3">{section.title}</h3>
                    {section.content}
                  </Card>
                ))}
              </div>
              </TabPanel>

              <TabPanel className="space-y-4">
              <div className="grid gap-4">
                {categorySections.map(section => (
                  <Card key={section.id} className="p-6">
                    <h3 className="text-lg font-semibold mb-3">{section.title}</h3>
                    {section.content}
                  </Card>
                ))}
              </div>
              </TabPanel>

              <TabPanel className="space-y-4">
              <div className="grid gap-4">
                {categorySections.map(section => (
                  <Card key={section.id} className="p-6">
                    <h3 className="text-lg font-semibold mb-3">{section.title}</h3>
                    {section.content}
                  </Card>
                ))}
              </div>
              </TabPanel>

              <TabPanel className="space-y-4">
              {/* Keyboard Shortcuts */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
                  <Keyboard className="h-5 w-5" />
                  <span>Keyboard Shortcuts</span>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {shortcuts.map(shortcut => (
                    <div key={shortcut.id} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                      <span className="text-sm">{shortcut.description}</span>
                      <Badge variant="outline" className="font-mono text-xs">
                        {formatShortcut(shortcut)}
                      </Badge>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Support Resources */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
                  <MessageCircle className="h-5 w-5" />
                  <span>Support & Resources</span>
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Book className="h-4 w-4" />
                      <div className="flex-1">
                        <div className="font-medium">User Guide</div>
                        <div className="text-sm text-muted-foreground">Complete guide to using Lexicon</div>
                      </div>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => {
                        // Open user guide in new tab or modal
                        window.open('/docs/user-guide', '_blank');
                      }}
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Keyboard className="h-4 w-4" />
                      <div className="flex-1">
                        <div className="font-medium">Keyboard Shortcuts</div>
                        <div className="text-sm text-muted-foreground">Full list of keyboard shortcuts</div>
                      </div>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => {
                        // Show keyboard shortcuts overlay - this would scroll to shortcuts tab
                        const shortcutsElement = document.getElementById('shortcuts-tab');
                        if (shortcutsElement) {
                          shortcutsElement.click();
                        }
                      }}
                    >
                      <span className="text-xs">View</span>
                    </Button>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <div className="flex items-center space-x-3">
                      <MessageCircle className="h-4 w-4" />
                      <div className="flex-1">
                        <div className="font-medium">Community Support</div>
                        <div className="text-sm text-muted-foreground">Get help from the community</div>
                      </div>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => {
                        window.open('https://github.com/lexicon/discussions', '_blank');
                      }}
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <div className="flex items-center space-x-3">
                      <HelpCircle className="h-4 w-4" />
                      <div className="flex-1">
                        <div className="font-medium">API Documentation</div>
                        <div className="text-sm text-muted-foreground">Technical reference and examples</div>
                      </div>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => {
                        window.open('/docs/api', '_blank');
                      }}
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </Card>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Help button component
interface HelpButtonProps {
  className?: string;
  variant?: 'icon' | 'button';
}

export function HelpButton({ className, variant = 'icon' }: HelpButtonProps) {
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
        <HelpSystem isOpen={isOpen} onClose={() => setIsOpen(false)} />
      </>
    );
  }

  return (
    <>
      <QuickTooltip content="Open Help">
        <Button 
          variant="ghost" 
          size="sm"
          onClick={() => setIsOpen(true)}
          className={className}
        >
          <HelpCircle className="h-4 w-4" />
        </Button>
      </QuickTooltip>
      <HelpSystem isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  );
}
