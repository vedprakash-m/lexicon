import { useState, useRef } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { Button, Input, Label, Textarea, Card, Badge } from '../ui';
import { 
  Plus, 
  Trash2, 
  Eye, 
  Save, 
  ArrowLeft, 
  Globe, 
  MousePointer, 
  Target,
  Code,
  Wand2,
  CheckCircle,
  AlertCircle,
  FileText
} from 'lucide-react';

interface Selector {
  name: string;
  selector: string;
  fallback_selectors?: string[];
  transform?: string;
  required: boolean;
  description: string;
}

interface RuleData {
  name: string;
  description: string;
  domain_patterns: string[];
  selectors: Record<string, Selector>;
  status: 'active' | 'inactive' | 'testing';
  type: 'built-in' | 'custom';
  lastTested: Date;
  successRate: number;
}

interface VisualRuleEditorProps {
  onComplete: (rule: RuleData) => void;
  onCancel: () => void;
}

export function VisualRuleEditor({ onComplete, onCancel }: VisualRuleEditorProps) {
  const [currentStep, setCurrentStep] = useState<'basic' | 'url' | 'selectors' | 'test'>('basic');
  const [testUrl, setTestUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    domain_patterns: [''],
    selectors: {} as Record<string, Selector>,
    waitConditions: [] as string[],
    transformations: {} as Record<string, string>
  });

  const iframeRef = useRef<HTMLIFrameElement>(null);

  const [suggestedSelectors, setSuggestedSelectors] = useState<{
    title: string[];
    content: string[];
    author: string[];
    date: string[];
    image: string[];
  }>({
    title: [],
    content: [],
    author: [],
    date: [],
    image: []
  });

  const [selectedElements, setSelectedElements] = useState<Record<string, string>>({});
  const [testResults, setTestResults] = useState<Record<string, any>>({});
  const [isValidating, setIsValidating] = useState(false);

  const loadTestPage = async () => {
    if (!testUrl) return;
    
    setIsLoading(true);
    try {
      // Validate URL first
      const isValid = await invoke<boolean>('validate_selector_urls', { urls: [testUrl] });
      if (!isValid) {
        throw new Error('Invalid URL provided');
      }

      // Scrape the page to analyze its structure
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

      // Analyze the HTML structure to suggest selectors
      const suggestedSelectors = analyzeHtmlStructure(scrapingResult.content);
      setSuggestedSelectors(suggestedSelectors);
      
      setIsLoading(false);
    } catch (error) {
      console.error('Error loading test page:', error);
      setIsLoading(false);
    }
  };

  const analyzeHtmlStructure = (htmlContent: string) => {
    // Create a DOM parser to analyze the HTML
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlContent, 'text/html');
    
    const suggestions = {
      title: [] as string[],
      content: [] as string[],
      author: [] as string[],
      date: [] as string[],
      image: [] as string[]
    };

    // Title selectors - look for common title patterns
    const titleSelectors = [
      'h1', 'h2', '.title', '.headline', '.post-title', 
      '.entry-title', '.article-title', '[role="heading"]'
    ];
    titleSelectors.forEach(selector => {
      if (doc.querySelector(selector)) {
        suggestions.title.push(selector);
      }
    });

    // Content selectors - look for main content areas
    const contentSelectors = [
      'article', '.content', '.post-content', '.entry-content',
      '.article-body', '.main-content', '[role="main"]', 'main'
    ];
    contentSelectors.forEach(selector => {
      if (doc.querySelector(selector)) {
        suggestions.content.push(selector);
      }
    });

    // Author selectors
    const authorSelectors = [
      '.author', '.byline', '.post-author', '.author-name',
      '.written-by', '[rel="author"]'
    ];
    authorSelectors.forEach(selector => {
      if (doc.querySelector(selector)) {
        suggestions.author.push(selector);
      }
    });

    // Date selectors
    const dateSelectors = [
      'time', '.date', '.published', '.post-date', '.publish-date',
      '.article-date', '[datetime]'
    ];
    dateSelectors.forEach(selector => {
      if (doc.querySelector(selector)) {
        suggestions.date.push(selector);
      }
    });

    // Image selectors
    const imageSelectors = [
      '.featured-image img', '.post-image img', 'article img',
      '.hero-image img', '.header-image img'
    ];
    imageSelectors.forEach(selector => {
      if (doc.querySelector(selector)) {
        suggestions.image.push(selector);
      }
    });

    return suggestions;
  };

  const testSelector = async (field: string, selector: string) => {
    if (!testUrl) {
      alert('Please load a test page first');
      return;
    }

    try {
      // Use the backend to test the CSS selector against the scraped content
      const testResult = await invoke<any>('test_css_selector', {
        url: testUrl,
        selector: selector,
        field: field
      });

      if (testResult.success) {
        const element = testResult.element;
        const preview = testResult.content ? testResult.content.substring(0, 100) : 'No content found';
        
        setTestResults(prev => ({
          ...prev,
          [field]: {
            selector,
            found: true,
            preview: preview,
            elementTag: element.tagName,
            elementText: element.textContent?.substring(0, 50) || '',
            attributes: element.attributes || {}
          }
        }));
      } else {
        setTestResults(prev => ({
          ...prev,
          [field]: {
            selector,
            found: false,
            error: testResult.error || 'Selector not found'
          }
        }));
      }
    } catch (error) {
      console.error('Error testing selector:', error);
      setTestResults(prev => ({
        ...prev,
        [field]: {
          selector,
          found: false,
          error: 'Failed to test selector'
        }
      }));
    }
  };

  const validateRule = async () => {
    if (!testUrl) {
      alert('Please load a test page to validate the rule');
      return;
    }

    setIsValidating(true);
    try {
      // Test all selectors at once
      const validationResult = await invoke<any>('validate_extraction_rule', {
        url: testUrl,
        rule: {
          name: formData.name,
          selectors: formData.selectors,
          waitConditions: formData.waitConditions,
          transformations: formData.transformations
        }
      });

      if (validationResult.success) {
        const extracted = validationResult.extracted;
        alert(`Validation successful!\n\nExtracted data:\n${JSON.stringify(extracted, null, 2)}`);
      } else {
        alert(`Validation failed: ${validationResult.error}`);
      }
    } catch (error) {
      console.error('Error validating rule:', error);
      alert('Error validating rule: ' + error);
    } finally {
      setIsValidating(false);
    }
  };

  const selectElement = (type: string, selector: string) => {
    setSelectedElements(prev => ({
      ...prev,
      [type]: selector
    }));
    
    // Update form data
    setFormData(prev => ({
      ...prev,
      selectors: {
        ...prev.selectors,
        [type]: {
          name: type,
          selector: selector,
          fallback_selectors: suggestedSelectors[type as keyof typeof suggestedSelectors].filter(s => s !== selector),
          transform: 'clean_whitespace',
          required: type === 'title' || type === 'content',
          description: `Extract ${type} from the page`
        }
      }
    }));
  };

  const handleComplete = () => {
    const rule: RuleData = {
      ...formData,
      status: 'testing',
      type: 'custom',
      lastTested: new Date(),
      successRate: 0
    };
    onComplete(rule);
  };

  const renderBasicStep = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Basic Information</h3>
        <div className="space-y-4">
          <div>
            <Label htmlFor="name">Rule Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="e.g., News Article Extractor"
            />
          </div>
          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Describe what this rule extracts and from which types of pages"
              rows={3}
            />
          </div>
        </div>
      </div>
    </div>
  );

  const renderUrlStep = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Domain Patterns</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Specify which websites this rule should apply to. You can use wildcards (*) to match multiple domains.
        </p>
        <div className="space-y-3">
          {formData.domain_patterns.map((pattern, index) => (
            <div key={index} className="flex space-x-2">
              <Input
                value={pattern}
                onChange={(e) => {
                  const newPatterns = [...formData.domain_patterns];
                  newPatterns[index] = e.target.value;
                  setFormData(prev => ({ ...prev, domain_patterns: newPatterns }));
                }}
                placeholder="e.g., *.example.com, news.site.com"
              />
              {formData.domain_patterns.length > 1 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const newPatterns = formData.domain_patterns.filter((_, i) => i !== index);
                    setFormData(prev => ({ ...prev, domain_patterns: newPatterns }));
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              )}
            </div>
          ))}
          <Button
            variant="outline"
            onClick={() => setFormData(prev => ({ 
              ...prev, 
              domain_patterns: [...prev.domain_patterns, ''] 
            }))}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Pattern
          </Button>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Test with a Real Page</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Enter a URL to test your rule and automatically detect selectors.
        </p>
        <div className="flex space-x-2">
          <Input
            value={testUrl}
            onChange={(e) => setTestUrl(e.target.value)}
            placeholder="https://example.com/article"
          />
          <Button onClick={loadTestPage} disabled={!testUrl || isLoading}>
            <Globe className="h-4 w-4 mr-2" />
            {isLoading ? 'Loading...' : 'Load Page'}
          </Button>
        </div>
      </div>
    </div>
  );

  const renderSelectorsStep = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Content Selectors</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Select the CSS selectors for extracting different types of content. We've suggested some based on common patterns.
        </p>
      </div>

      {/* Visual selector interface */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left side - Selector configuration */}
        <div className="space-y-4">
          {Object.entries(suggestedSelectors).map(([type, selectors]) => (
            <Card key={type} className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium capitalize">{type}</h4>
                {selectedElements[type] && (
                  <Badge variant="default" className="text-xs">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Selected
                  </Badge>
                )}
              </div>
              
              <div className="space-y-2">
                {selectors.map((selector, index) => (
                  <div key={index} className="flex items-center justify-between p-2 border rounded">
                    <code className="text-xs font-mono flex-1 mr-2">{selector}</code>
                    <div className="flex space-x-1">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => testSelector(type, selector)}
                        disabled={!testUrl}
                        title="Test this selector"
                      >
                        <Eye className="h-3 w-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant={selectedElements[type] === selector ? "default" : "outline"}
                        onClick={() => selectElement(type, selector)}
                      >
                        {selectedElements[type] === selector ? (
                          <CheckCircle className="h-3 w-3" />
                        ) : (
                          <Target className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                  </div>
                ))}

                {/* Show test results */}
                {testResults[type] && (
                  <div className={`mt-2 p-2 rounded text-xs ${
                    testResults[type].found 
                      ? 'bg-green-50 border border-green-200 text-green-700' 
                      : 'bg-red-50 border border-red-200 text-red-700'
                  }`}>
                    {testResults[type].found ? (
                      <div>
                        <div className="font-medium flex items-center">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Found: {testResults[type].elementTag}
                        </div>
                        <div className="mt-1">
                          <strong>Content:</strong> {testResults[type].preview}
                        </div>
                      </div>
                    ) : (
                      <div className="font-medium flex items-center">
                        <AlertCircle className="h-3 w-3 mr-1" />
                        {testResults[type].error || 'Element not found'}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Custom selector input */}
              <div className="mt-3 pt-3 border-t">
                <div className="flex space-x-2">
                  <Input
                    placeholder="Custom CSS selector"
                    className="text-xs font-mono"
                  />
                  <Button size="sm" variant="outline">
                    <Plus className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* Right side - Preview iframe */}
        <div className="space-y-4">
          <Card className="p-4">
            <h4 className="font-medium mb-3">Page Preview</h4>
            {testUrl ? (
              <div className="border rounded-lg overflow-hidden" style={{ height: '400px' }}>
                {isLoading ? (
                  <div className="flex items-center justify-center h-full bg-muted">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
                      <p className="text-sm text-muted-foreground">Loading page...</p>
                    </div>
                  </div>
                ) : (
                  <iframe
                    ref={iframeRef}
                    src={testUrl}
                    className="w-full h-full"
                    sandbox="allow-same-origin allow-scripts"
                    title="Test page preview"
                  />
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center h-64 bg-muted rounded-lg">
                <div className="text-center">
                  <Globe className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">Load a test URL to preview</p>
                </div>
              </div>
            )}
          </Card>

          <Card className="p-4">
            <h4 className="font-medium mb-3">Selector Tools</h4>
            <div className="space-y-2">
              <Button variant="outline" className="w-full justify-start">
                <MousePointer className="h-4 w-4 mr-2" />
                Click to Select Element
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <Wand2 className="h-4 w-4 mr-2" />
                Auto-Detect Content
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <Code className="h-4 w-4 mr-2" />
                View Page Source
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );

  const renderTestStep = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Test Your Rule</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Review your rule configuration and test it against the sample page.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-4">
          <h4 className="font-medium mb-3">Rule Summary</h4>
          <div className="space-y-3">
            <div>
              <Label className="text-xs text-muted-foreground">Name</Label>
              <p className="font-medium">{formData.name}</p>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Domain Patterns</Label>
              <div className="space-y-1">
                {formData.domain_patterns.filter(p => p).map((pattern, index) => (
                  <code key={index} className="block text-xs bg-muted p-2 rounded">
                    {pattern}
                  </code>
                ))}
              </div>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Selected Selectors</Label>
              <div className="space-y-1">
                {Object.entries(selectedElements).map(([type, selector]) => (
                  <div key={type} className="flex items-center justify-between text-xs">
                    <span className="capitalize">{type}:</span>
                    <code className="bg-muted px-2 py-1 rounded">{selector}</code>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <h4 className="font-medium mb-3">Test Results</h4>
          <div className="space-y-3">
            {Object.entries(selectedElements).map(([type, selector]) => {
              const testResult = testResults[type];
              const hasResult = testResult && typeof testResult.found !== 'undefined';
              
              return (
                <div key={type} className="flex items-center justify-between p-2 border rounded">
                  <span className="capitalize text-sm">{type}</span>
                  <div className="flex items-center space-x-2">
                    {hasResult ? (
                      testResult.found ? (
                        <>
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          <span className="text-xs text-green-600">Found</span>
                        </>
                      ) : (
                        <>
                          <AlertCircle className="h-4 w-4 text-red-500" />
                          <span className="text-xs text-red-600">Not Found</span>
                        </>
                      )
                    ) : (
                      <>
                        <Eye className="h-4 w-4 text-gray-400" />
                        <span className="text-xs text-muted-foreground">Not Tested</span>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          
          <Button 
            className="w-full mt-4" 
            variant="outline"
            onClick={validateRule}
            disabled={isValidating || !testUrl || Object.keys(selectedElements).length === 0}
          >
            {isValidating ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                Validating...
              </>
            ) : (
              <>
                <Eye className="h-4 w-4 mr-2" />
                Run Test Extraction
              </>
            )}
          </Button>
        </Card>
      </div>
    </div>
  );

  const steps = [
    { id: 'basic', title: 'Basic Info', icon: FileText },
    { id: 'url', title: 'Domains', icon: Globe },
    { id: 'selectors', title: 'Selectors', icon: Target },
    { id: 'test', title: 'Test', icon: Eye }
  ];

  const currentStepIndex = steps.findIndex(step => step.id === currentStep);

  return (
    <div className="max-w-6xl mx-auto">
      {/* Step indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-center space-x-4">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isActive = step.id === currentStep;
            const isCompleted = index < currentStepIndex;
            
            return (
              <div key={step.id} className="flex items-center">
                <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                  isActive 
                    ? 'border-primary bg-primary text-primary-foreground' 
                    : isCompleted 
                      ? 'border-green-500 bg-green-500 text-white'
                      : 'border-muted-foreground text-muted-foreground'
                }`}>
                  {isCompleted ? (
                    <CheckCircle className="h-5 w-5" />
                  ) : (
                    <Icon className="h-5 w-5" />
                  )}
                </div>
                <span className={`ml-2 text-sm font-medium ${
                  isActive ? 'text-primary' : isCompleted ? 'text-green-600' : 'text-muted-foreground'
                }`}>
                  {step.title}
                </span>
                {index < steps.length - 1 && (
                  <div className={`w-8 h-px mx-4 ${
                    isCompleted ? 'bg-green-500' : 'bg-muted-foreground'
                  }`} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Step content */}
      <Card className="p-6">
        {currentStep === 'basic' && renderBasicStep()}
        {currentStep === 'url' && renderUrlStep()}
        {currentStep === 'selectors' && renderSelectorsStep()}
        {currentStep === 'test' && renderTestStep()}
      </Card>

      {/* Navigation */}
      <div className="flex justify-between mt-6">
        <Button variant="outline" onClick={onCancel}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Cancel
        </Button>
        
        <div className="flex space-x-2">
          {currentStepIndex > 0 && (
            <Button 
              variant="outline" 
              onClick={() => setCurrentStep(steps[currentStepIndex - 1].id as any)}
            >
              Previous
            </Button>
          )}
          
          {currentStepIndex < steps.length - 1 ? (
            <Button 
              onClick={() => setCurrentStep(steps[currentStepIndex + 1].id as any)}
              disabled={currentStep === 'basic' && (!formData.name || !formData.description)}
            >
              Next
            </Button>
          ) : (
            <Button 
              onClick={handleComplete}
              disabled={!formData.name || !formData.description || Object.keys(selectedElements).length === 0}
            >
              <Save className="h-4 w-4 mr-2" />
              Create Rule
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
