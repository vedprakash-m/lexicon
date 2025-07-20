import { useState } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { Plus, Globe, FileText, Settings, Eye, Trash2, Edit, CheckCircle, AlertCircle } from 'lucide-react';
import { Button, Card, Badge, Dialog, DialogContent, DialogHeader, DialogTitle, Input, Label } from '../ui';
import { SourceCreationWizard } from './SourceCreationWizard';
import { VisualRuleEditor } from './VisualRuleEditor';

interface ScrapingRule {
  id: string;
  name: string;
  description: string;
  domain_patterns: string[];
  selectors: Record<string, any>;
  status: 'active' | 'inactive' | 'testing';
  type: 'built-in' | 'custom';
  lastTested: Date;
  successRate: number;
}

interface Source {
  id: string;
  name: string;
  description: string;
  url: string;
  type: 'website' | 'api' | 'file';
  ruleId: string;
  status: 'active' | 'inactive' | 'error';
  lastScraped: Date;
  totalPages: number;
  projectId?: string;
}

const mockRules: ScrapingRule[] = [];

const mockSources: Source[] = [];

export function SourceConfiguration() {
  const [activeTab, setActiveTab] = useState<'sources' | 'rules'>('sources');
  const [sources, setSources] = useState<Source[]>(mockSources);
  const [rules, setRules] = useState<ScrapingRule[]>(mockRules);
  const [showSourceDialog, setShowSourceDialog] = useState(false);
  const [showRuleDialog, setShowRuleDialog] = useState(false);
  const [selectedRule, setSelectedRule] = useState<ScrapingRule | null>(null);
  const [testUrl, setTestUrl] = useState('');
  const [isTestingUrl, setIsTestingUrl] = useState(false);
  const [testResults, setTestResults] = useState<any>(null);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'inactive': return 'bg-gray-500';
      case 'error': return 'bg-red-500';
      case 'testing': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  const getSuccessRateColor = (rate: number) => {
    if (rate >= 90) return 'text-green-600';
    if (rate >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const handleTestUrl = async () => {
    if (!testUrl.trim()) return;
    
    setIsTestingUrl(true);
    setTestResults(null);
    
    try {
      // First validate the URL
      const isValidUrl = await invoke<boolean>('validate_selector_urls', { 
        urls: [testUrl] 
      });
      
      if (!isValidUrl) {
        throw new Error('Invalid URL format');
      }

      // Scrape the URL to test connectivity and basic structure
      const scrapingResult = await invoke<any>('scrape_url_for_selector_testing', { 
        url: testUrl,
        config: {
          followRedirects: true,
          userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
      });

      if (!scrapingResult.success) {
        throw new Error(scrapingResult.error || 'Failed to scrape URL');
      }

      // Test which rules match this URL
      const matchingRules = rules.filter(rule => {
        return rule.domain_patterns.some(pattern => {
          try {
            const regex = new RegExp(pattern);
            return regex.test(testUrl);
          } catch {
            return testUrl.includes(pattern);
          }
        });
      });

      // If we have matching rules, test a basic selector from the first one
      let selectorTestResult = null;
      if (matchingRules.length > 0 && Object.keys(matchingRules[0].selectors).length > 0) {
        const firstRule = matchingRules[0];
        const firstSelectorKey = Object.keys(firstRule.selectors)[0];
        const firstSelector = firstRule.selectors[firstSelectorKey];
        
        if (firstSelector?.selector) {
          try {
            selectorTestResult = await invoke<any>('test_css_selector', {
              url: testUrl,
              selector: firstSelector.selector,
              field: firstSelectorKey
            });
          } catch (err) {
            console.warn('Selector test failed:', err);
          }
        }
      }

      setTestResults({
        url: testUrl,
        success: true,
        accessible: true,
        contentLength: scrapingResult.content?.length || 0,
        matchingRules: matchingRules.map(rule => rule.name),
        selectorTest: selectorTestResult
      });

    } catch (error) {
      console.error('URL test failed:', error);
      setTestResults({
        url: testUrl,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
        accessible: false,
        matchingRules: []
      });
    } finally {
      setIsTestingUrl(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Source Configuration</h1>
          <p className="text-muted-foreground mt-1">
            Configure scraping sources and rules for automated content extraction
          </p>
        </div>
        
        <div className="flex space-x-2">
          <Button 
            variant="outline"
            onClick={() => setShowRuleDialog(true)}
          >
            <Plus className="h-4 w-4 mr-2" />
            New Rule
          </Button>
          <Button onClick={() => setShowSourceDialog(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Source
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-border">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('sources')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'sources'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground'
            }`}
          >
            <Globe className="h-4 w-4 inline mr-2" />
            Sources ({sources.length})
          </button>
          <button
            onClick={() => setActiveTab('rules')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'rules'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground'
            }`}
          >
            <FileText className="h-4 w-4 inline mr-2" />
            Rules ({rules.length})
          </button>
        </nav>
      </div>

      {/* Sources Tab */}
      {activeTab === 'sources' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sources.map((source) => (
              <Card key={source.id} className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <Globe className="h-5 w-5 text-primary" />
                    <div>
                      <h3 className="font-semibold">{source.name}</h3>
                      <div className="flex items-center space-x-2 mt-1">
                        <div className={`w-2 h-2 rounded-full ${getStatusColor(source.status)}`} />
                        <span className="text-xs text-muted-foreground capitalize">
                          {source.status}
                        </span>
                      </div>
                    </div>
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {source.type}
                  </Badge>
                </div>
                
                <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                  {source.description}
                </p>
                
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">URL:</span>
                    <span className="truncate ml-2 max-w-[200px]">{source.url}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Pages:</span>
                    <span>{source.totalPages}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Last Scraped:</span>
                    <span>{source.lastScraped.toLocaleDateString()}</span>
                  </div>
                </div>
                
                <div className="flex space-x-2 mt-4">
                  <Button variant="outline" size="sm" className="flex-1">
                    <Eye className="h-3 w-3 mr-1" />
                    Test
                  </Button>
                  <Button variant="outline" size="sm" className="flex-1">
                    <Edit className="h-3 w-3 mr-1" />
                    Edit
                  </Button>
                  <Button variant="outline" size="sm">
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Rules Tab */}
      {activeTab === 'rules' && (
        <div className="space-y-4">
          {/* Rule Testing Section */}
          <Card className="p-4">
            <h3 className="font-semibold mb-3">Quick Rule Test</h3>
            <div className="flex space-x-2">
              <Input
                placeholder="Enter URL to test rules against..."
                value={testUrl}
                onChange={(e) => setTestUrl(e.target.value)}
                className="flex-1"
              />
              <Button variant="outline" onClick={handleTestUrl} disabled={!testUrl.trim() || isTestingUrl}>
                <Eye className="h-4 w-4 mr-2" />
                {isTestingUrl ? 'Testing...' : 'Test URL'}
              </Button>
            </div>
          </Card>

          {/* Test Results */}
          {testResults && (
            <Card className="p-4">
              <h3 className="font-semibold mb-3">Test Results</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">URL Accessibility:</span>
                  <div className="flex items-center space-x-2">
                    {testResults.success ? (
                      <>
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        <span className="text-sm text-green-600">Accessible</span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="h-4 w-4 text-red-500" />
                        <span className="text-sm text-red-600">Failed</span>
                      </>
                    )}
                  </div>
                </div>
                
                {testResults.success && (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Content Length:</span>
                      <span className="text-sm">{testResults.contentLength.toLocaleString()} characters</span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Matching Rules:</span>
                      <span className="text-sm">
                        {testResults.matchingRules.length > 0 
                          ? testResults.matchingRules.join(', ') 
                          : 'No matching rules'}
                      </span>
                    </div>
                    
                    {testResults.selectorTest && (
                      <div className="space-y-2">
                        <span className="text-sm text-muted-foreground">Sample Extraction:</span>
                        <div className="bg-muted p-3 rounded-lg">
                          {testResults.selectorTest.success ? (
                            <div className="space-y-1">
                              <div className="flex items-center space-x-2">
                                <CheckCircle className="h-3 w-3 text-green-500" />
                                <span className="text-xs text-green-600">Selector found content</span>
                              </div>
                              <code className="text-xs block mt-1">
                                {testResults.selectorTest.content?.substring(0, 100)}
                                {testResults.selectorTest.content?.length > 100 ? '...' : ''}
                              </code>
                            </div>
                          ) : (
                            <div className="flex items-center space-x-2">
                              <AlertCircle className="h-3 w-3 text-red-500" />
                              <span className="text-xs text-red-600">
                                {testResults.selectorTest.error || 'Selector did not find content'}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </>
                )}
                
                {!testResults.success && testResults.error && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="h-4 w-4 text-red-500" />
                      <span className="text-sm text-red-600">Error: {testResults.error}</span>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* Rules Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {rules.map((rule) => (
              <Card key={rule.id} className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <FileText className="h-5 w-5 text-primary" />
                    <div>
                      <h3 className="font-semibold">{rule.name}</h3>
                      <div className="flex items-center space-x-2 mt-1">
                        <div className={`w-2 h-2 rounded-full ${getStatusColor(rule.status)}`} />
                        <span className="text-xs text-muted-foreground capitalize">
                          {rule.status}
                        </span>
                      </div>
                    </div>
                  </div>
                  <Badge 
                    variant={rule.type === 'built-in' ? 'default' : 'secondary'} 
                    className="text-xs"
                  >
                    {rule.type}
                  </Badge>
                </div>
                
                <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                  {rule.description}
                </p>
                
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Domains:</span>
                    <span>{rule.domain_patterns.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Success Rate:</span>
                    <span className={getSuccessRateColor(rule.successRate)}>
                      {rule.successRate}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Last Tested:</span>
                    <span>{rule.lastTested.toLocaleDateString()}</span>
                  </div>
                </div>
                
                <div className="flex space-x-2 mt-4">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="flex-1"
                    onClick={() => setSelectedRule(rule)}
                  >
                    <Eye className="h-3 w-3 mr-1" />
                    View
                  </Button>
                  {rule.type === 'custom' && (
                    <Button variant="outline" size="sm" className="flex-1">
                      <Edit className="h-3 w-3 mr-1" />
                      Edit
                    </Button>
                  )}
                  <Button 
                    variant="outline" 
                    size="sm"
                    className={rule.status === 'active' ? 'text-yellow-600' : 'text-green-600'}
                  >
                    {rule.status === 'active' ? (
                      <AlertCircle className="h-3 w-3" />
                    ) : (
                      <CheckCircle className="h-3 w-3" />
                    )}
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Dialogs */}
      <Dialog open={showSourceDialog} onClose={() => setShowSourceDialog(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Source</DialogTitle>
          </DialogHeader>
          <SourceCreationWizard 
            rules={rules}
            onComplete={(source) => {
              setSources(prev => [...prev, { ...source, id: Date.now().toString() }]);
              setShowSourceDialog(false);
            }}
            onCancel={() => setShowSourceDialog(false)}
          />
        </DialogContent>
      </Dialog>

      <Dialog open={showRuleDialog} onClose={() => setShowRuleDialog(false)}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Create New Rule</DialogTitle>
          </DialogHeader>
          <VisualRuleEditor 
            onComplete={(rule) => {
              setRules(prev => [...prev, { ...rule, id: Date.now().toString() }]);
              setShowRuleDialog(false);
            }}
            onCancel={() => setShowRuleDialog(false)}
          />
        </DialogContent>
      </Dialog>

      <Dialog open={!!selectedRule} onClose={() => setSelectedRule(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rule Details: {selectedRule?.name}</DialogTitle>
          </DialogHeader>
          {selectedRule && (
            <div className="space-y-4">
              <div>
                <Label>Description</Label>
                <p className="text-sm text-muted-foreground">{selectedRule.description}</p>
              </div>
              <div>
                <Label>Domain Patterns</Label>
                <div className="space-y-1">
                  {selectedRule.domain_patterns.map((pattern, idx) => (
                    <code key={idx} className="block text-xs bg-muted p-2 rounded">
                      {pattern}
                    </code>
                  ))}
                </div>
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setSelectedRule(null)}>
                  Close
                </Button>
                <Button>
                  <Settings className="h-4 w-4 mr-2" />
                  Configure
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
