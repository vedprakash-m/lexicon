import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { useEnhancedKeyboardNavigation } from '../hooks/useEnhancedKeyboardNavigation';
import { enhancedSelectorTester, type EnhancedTestResult } from '../utils/enhanced-selector-testing';
import { CheckCircle, XCircle, AlertTriangle, Zap, Eye, Gauge } from 'lucide-react';

export function Phase4TestingDashboard() {
  const [testResults, setTestResults] = useState<EnhancedTestResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [testSelector, setTestSelector] = useState('button.primary');
  const [testHtml, setTestHtml] = useState(`
    <div class="container">
      <button class="primary" aria-label="Submit form">Submit</button>
      <button class="secondary">Cancel</button>
      <input type="text" placeholder="Enter text" />
    </div>
  `);

  const {
    focusFirstInteractiveElement,
    skipToMainContent,
    announceToScreenReader,
    createFocusTrap
  } = useEnhancedKeyboardNavigation();

  const handleEnhancedTest = async () => {
    setIsLoading(true);
    announceToScreenReader('Starting enhanced selector test', 'polite');
    
    try {
      const result = await enhancedSelectorTester.testSelectorEnhanced(
        testSelector,
        testHtml,
        {
          performanceTest: true,
          accessibilityTest: true,
          validationTest: true
        }
      );
      
      setTestResults(result);
      announceToScreenReader(
        `Test completed. Found ${result.element_count} elements with ${result.validation.errors.length} errors`,
        'assertive'
      );
    } catch (error) {
      announceToScreenReader('Test failed', 'assertive');
      console.error('Enhanced test failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyboardNavTest = () => {
    announceToScreenReader('Testing keyboard navigation features', 'polite');
    
    // Demonstrate focus management
    setTimeout(() => focusFirstInteractiveElement(), 500);
    setTimeout(() => skipToMainContent(), 2000);
  };

  // Performance score color coding
  const getPerformanceColor = (timeMs: number): string => {
    if (timeMs < 10) return 'text-green-600';
    if (timeMs < 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Accessibility score display
  const getAccessibilityScore = (accessibility: any): number => {
    let score = 0;
    if (accessibility.has_aria_labels) score += 25;
    if (accessibility.has_alt_text) score += 25;
    if (accessibility.tab_index !== undefined) score += 25;
    if (accessibility.color_contrast_ratio && accessibility.color_contrast_ratio > 4.5) score += 25;
    return score;
  };

  return (
    <div 
      className="w-full max-w-6xl mx-auto p-6 space-y-6"
      role="main"
      aria-label="Phase 4 Testing Dashboard"
    >
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Phase 4: Enhanced Accessibility & Performance Testing
          </CardTitle>
          <CardDescription>
            Complete testing dashboard with enhanced keyboard navigation and visual rule editor test functions
          </CardDescription>
        </CardHeader>
      </Card>

      <Tabs defaultValue="selector-testing" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="selector-testing">Enhanced Selector Testing</TabsTrigger>
          <TabsTrigger value="keyboard-nav">Keyboard Navigation</TabsTrigger>
        </TabsList>

        <TabsContent value="selector-testing" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Eye className="h-5 w-5" />
                Enhanced Visual Rule Editor Testing
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label htmlFor="test-selector" className="text-sm font-medium">
                    CSS Selector to Test
                  </label>
                  <input
                    id="test-selector"
                    type="text"
                    value={testSelector}
                    onChange={(e) => setTestSelector(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter CSS selector..."
                  />
                </div>
                <div className="space-y-2">
                  <label htmlFor="test-html" className="text-sm font-medium">
                    HTML to Test Against
                  </label>
                  <textarea
                    id="test-html"
                    value={testHtml}
                    onChange={(e) => setTestHtml(e.target.value)}
                    rows={4}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter HTML content..."
                  />
                </div>
              </div>

              <Button 
                onClick={handleEnhancedTest}
                disabled={isLoading}
                className="w-full"
              >
                {isLoading ? 'Running Enhanced Test...' : 'Run Enhanced Selector Test'}
              </Button>

              {testResults && (
                <div className="space-y-6 mt-6">
                  {/* Performance Results */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Gauge className="h-4 w-4" />
                        Performance Analysis
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center">
                          <div className={`text-2xl font-bold ${getPerformanceColor(testResults.performance.execution_time_ms)}`}>
                            {testResults.performance.execution_time_ms}ms
                          </div>
                          <div className="text-sm text-gray-500">Execution Time</div>
                        </div>
                        <div className="text-center">
                          <Badge variant={testResults.performance.selector_complexity === 'low' ? 'default' : 'destructive'}>
                            {testResults.performance.selector_complexity}
                          </Badge>
                          <div className="text-sm text-gray-500 mt-1">Complexity</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold">
                            {testResults.element_count}
                          </div>
                          <div className="text-sm text-gray-500">Elements Found</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-blue-600">
                            {getAccessibilityScore(testResults.accessibility)}%
                          </div>
                          <div className="text-sm text-gray-500">Accessibility</div>
                        </div>
                      </div>

                      {testResults.performance.suggestions && (
                        <div className="mt-4">
                          <h4 className="font-medium mb-2">Performance Suggestions:</h4>
                          <ul className="space-y-1">
                            {testResults.performance.suggestions.map((suggestion, index) => (
                              <li key={index} className="text-sm text-blue-600 flex items-center gap-2">
                                <AlertTriangle className="h-3 w-3" />
                                {suggestion}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* Accessibility Results */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Accessibility Analysis</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="flex items-center gap-2">
                          {testResults.accessibility.has_aria_labels ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <XCircle className="h-4 w-4 text-red-600" />
                          )}
                          <span className="text-sm">ARIA Labels</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {testResults.accessibility.has_alt_text ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <XCircle className="h-4 w-4 text-red-600" />
                          )}
                          <span className="text-sm">Alt Text</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {testResults.accessibility.tab_index !== undefined ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <XCircle className="h-4 w-4 text-gray-400" />
                          )}
                          <span className="text-sm">Tab Index</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {testResults.accessibility.color_contrast_ratio ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <XCircle className="h-4 w-4 text-gray-400" />
                          )}
                          <span className="text-sm">Contrast</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Validation Results */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Validation Results</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span>Unique Selector</span>
                          {testResults.validation.is_unique ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <XCircle className="h-4 w-4 text-red-600" />
                          )}
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Stable Selector</span>
                          {testResults.validation.is_stable ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <XCircle className="h-4 w-4 text-yellow-600" />
                          )}
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Cross-Browser Compatible</span>
                          {testResults.validation.cross_browser_compatible ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <XCircle className="h-4 w-4 text-red-600" />
                          )}
                        </div>
                      </div>

                      {(testResults.validation.warnings.length > 0 || testResults.validation.errors.length > 0) && (
                        <div className="mt-4 space-y-2">
                          {testResults.validation.warnings.map((warning, index) => (
                            <Alert key={`warning-${index}`}>
                              <AlertTriangle className="h-4 w-4" />
                              <AlertDescription>{warning}</AlertDescription>
                            </Alert>
                          ))}
                          {testResults.validation.errors.map((error, index) => (
                            <Alert key={`error-${index}`} variant="destructive">
                              <XCircle className="h-4 w-4" />
                              <AlertDescription>{error}</AlertDescription>
                            </Alert>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="keyboard-nav" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Enhanced Keyboard Navigation Testing</CardTitle>
              <CardDescription>
                Test the enhanced keyboard navigation features and accessibility shortcuts
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Button onClick={handleKeyboardNavTest}>
                  Test Navigation Features
                </Button>
                <Button onClick={() => focusFirstInteractiveElement()}>
                  Focus First Element
                </Button>
                <Button onClick={() => skipToMainContent()}>
                  Skip to Main Content
                </Button>
                <Button onClick={() => announceToScreenReader('Test announcement', 'assertive')}>
                  Test Screen Reader
                </Button>
              </div>

              <Card className="mt-6">
                <CardHeader>
                  <CardTitle className="text-lg">Available Keyboard Shortcuts</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <h4 className="font-medium mb-2">Navigation:</h4>
                      <ul className="space-y-1 text-gray-600">
                        <li><kbd>Alt + M</kbd> - Skip to Main Content</li>
                        <li><kbd>Alt + N</kbd> - Skip to Navigation</li>
                        <li><kbd>Alt + F</kbd> - Focus First Element</li>
                        <li><kbd>Alt + L</kbd> - Focus Last Element</li>
                        <li><kbd>Alt + S</kbd> - Cycle Through Sections</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium mb-2">Quick Navigation:</h4>
                      <ul className="space-y-1 text-gray-600">
                        <li><kbd>G + L</kbd> - Go to Library</li>
                        <li><kbd>G + P</kbd> - Go to Processing</li>
                        <li><kbd>G + B</kbd> - Go to Batch</li>
                        <li><kbd>G + M</kbd> - Go to Performance</li>
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
