import { invoke } from '@tauri-apps/api/core';

export interface EnhancedTestResult {
  success: boolean;
  element_count: number;
  elements: Array<{
    tag: string;
    text: string;
    attributes: Record<string, string>;
    position: { x: number; y: number; width: number; height: number };
    xpath: string;
    css_path: string;
  }>;
  performance: {
    execution_time_ms: number;
    selector_complexity: 'low' | 'medium' | 'high';
    suggestions?: string[];
  };
  accessibility: {
    has_aria_labels: boolean;
    has_alt_text: boolean;
    color_contrast_ratio?: number;
    tab_index?: number;
  };
  validation: {
    is_unique: boolean;
    is_stable: boolean;
    cross_browser_compatible: boolean;
    warnings: string[];
    errors: string[];
  };
}

export interface BulkTestResult {
  selector: string;
  test_results: EnhancedTestResult[];
  consensus: {
    average_element_count: number;
    stability_score: number;
    performance_score: number;
    reliability_rating: 'excellent' | 'good' | 'fair' | 'poor';
  };
}

/**
 * Enhanced testing utilities for the visual rule editor
 */
export class EnhancedSelectorTester {
  
  /**
   * Test a CSS selector with enhanced analysis
   */
  async testSelectorEnhanced(
    selector: string, 
    html: string, 
    options: {
      performanceTest?: boolean;
      accessibilityTest?: boolean;
      validationTest?: boolean;
    } = {}
  ): Promise<EnhancedTestResult> {
    try {
      const result = await invoke<EnhancedTestResult>('test_css_selector_enhanced', {
        selector,
        html,
        options
      });
      
      return result;
    } catch (error) {
      console.error('Enhanced selector test failed:', error);
      return {
        success: false,
        element_count: 0,
        elements: [],
        performance: {
          execution_time_ms: 0,
          selector_complexity: 'high',
          suggestions: [`Error testing selector: ${error}`]
        },
        accessibility: {
          has_aria_labels: false,
          has_alt_text: false
        },
        validation: {
          is_unique: false,
          is_stable: false,
          cross_browser_compatible: false,
          warnings: [],
          errors: [String(error)]
        }
      };
    }
  }

  /**
   * Test selector across multiple HTML samples for stability
   */
  async testSelectorStability(
    selector: string,
    htmlSamples: string[]
  ): Promise<BulkTestResult> {
    try {
      const testPromises = htmlSamples.map(html => 
        this.testSelectorEnhanced(selector, html, {
          performanceTest: true,
          validationTest: true
        })
      );

      const results = await Promise.all(testPromises);
      
      const elementCounts = results.map(r => r.element_count);
      const averageElementCount = elementCounts.reduce((a, b) => a + b, 0) / elementCounts.length;
      
      // Calculate stability score based on consistency
      const countVariance = elementCounts.reduce((variance, count) => {
        return variance + Math.pow(count - averageElementCount, 2);
      }, 0) / elementCounts.length;
      
      const stabilityScore = Math.max(0, 100 - (countVariance * 10));
      
      // Calculate performance score
      const avgExecutionTime = results.reduce((sum, r) => sum + r.performance.execution_time_ms, 0) / results.length;
      const performanceScore = Math.max(0, 100 - (avgExecutionTime / 10));
      
      // Determine reliability rating
      let reliabilityRating: 'excellent' | 'good' | 'fair' | 'poor';
      const overallScore = (stabilityScore + performanceScore) / 2;
      
      if (overallScore >= 90) reliabilityRating = 'excellent';
      else if (overallScore >= 75) reliabilityRating = 'good';
      else if (overallScore >= 50) reliabilityRating = 'fair';
      else reliabilityRating = 'poor';

      return {
        selector,
        test_results: results,
        consensus: {
          average_element_count: averageElementCount,
          stability_score: stabilityScore,
          performance_score: performanceScore,
          reliability_rating: reliabilityRating
        }
      };
    } catch (error) {
      console.error('Stability test failed:', error);
      throw error;
    }
  }

  /**
   * Generate alternative selectors for robustness
   */
  async generateAlternativeSelectors(
    targetElement: string,
    html: string
  ): Promise<Array<{
    selector: string;
    type: 'id' | 'class' | 'attribute' | 'xpath' | 'css_path' | 'text_content';
    reliability_score: number;
    description: string;
  }>> {
    try {
      return await invoke('generate_alternative_selectors', {
        targetElement,
        html
      });
    } catch (error) {
      console.error('Alternative selector generation failed:', error);
      return [];
    }
  }

  /**
   * Validate selector against real-world scenarios
   */
  async validateSelectorRobustness(
    selector: string,
    scenarios: Array<{
      name: string;
      html: string;
      expected_count: number;
    }>
  ): Promise<{
    overall_score: number;
    scenario_results: Array<{
      name: string;
      passed: boolean;
      actual_count: number;
      expected_count: number;
      issues: string[];
    }>;
    recommendations: string[];
  }> {
    try {
      return await invoke('validate_selector_robustness', {
        selector,
        scenarios
      });
    } catch (error) {
      console.error('Robustness validation failed:', error);
      return {
        overall_score: 0,
        scenario_results: scenarios.map(scenario => ({
          name: scenario.name,
          passed: false,
          actual_count: 0,
          expected_count: scenario.expected_count,
          issues: [String(error)]
        })),
        recommendations: ['Fix selector syntax errors before proceeding']
      };
    }
  }

  /**
   * Test selector performance with timing analysis
   */
  async benchmarkSelector(
    selector: string,
    html: string,
    iterations: number = 100
  ): Promise<{
    average_time_ms: number;
    min_time_ms: number;
    max_time_ms: number;
    median_time_ms: number;
    percentile_95_ms: number;
    complexity_analysis: {
      selector_complexity: 'low' | 'medium' | 'high';
      dom_traversal_depth: number;
      optimization_suggestions: string[];
    };
  }> {
    try {
      return await invoke('benchmark_selector_performance', {
        selector,
        html,
        iterations
      });
    } catch (error) {
      console.error('Selector benchmark failed:', error);
      return {
        average_time_ms: 0,
        min_time_ms: 0,
        max_time_ms: 0,
        median_time_ms: 0,
        percentile_95_ms: 0,
        complexity_analysis: {
          selector_complexity: 'high',
          dom_traversal_depth: 0,
          optimization_suggestions: [`Benchmark failed: ${error}`]
        }
      };
    }
  }

  /**
   * Analyze CSS selector for accessibility compliance
   */
  async analyzeAccessibility(
    selector: string,
    html: string
  ): Promise<{
    accessibility_score: number;
    wcag_compliance: {
      level_a: boolean;
      level_aa: boolean;
      level_aaa: boolean;
    };
    issues: Array<{
      severity: 'error' | 'warning' | 'info';
      message: string;
      recommendation: string;
    }>;
    improvements: string[];
  }> {
    try {
      return await invoke('analyze_selector_accessibility', {
        selector,
        html
      });
    } catch (error) {
      console.error('Accessibility analysis failed:', error);
      return {
        accessibility_score: 0,
        wcag_compliance: {
          level_a: false,
          level_aa: false,
          level_aaa: false
        },
        issues: [{
          severity: 'error',
          message: String(error),
          recommendation: 'Fix selector syntax before accessibility analysis'
        }],
        improvements: []
      };
    }
  }

  /**
   * Test selector across different viewport sizes (responsive testing)
   */
  async testResponsiveCompatibility(
    selector: string,
    html: string,
    viewports: Array<{ width: number; height: number; name: string }>
  ): Promise<{
    compatible_viewports: string[];
    incompatible_viewports: Array<{
      name: string;
      issues: string[];
      element_visibility: boolean;
    }>;
    responsive_score: number;
    recommendations: string[];
  }> {
    try {
      return await invoke('test_responsive_compatibility', {
        selector,
        html,
        viewports
      });
    } catch (error) {
      console.error('Responsive compatibility test failed:', error);
      return {
        compatible_viewports: [],
        incompatible_viewports: viewports.map(vp => ({
          name: vp.name,
          issues: [String(error)],
          element_visibility: false
        })),
        responsive_score: 0,
        recommendations: ['Fix selector issues before responsive testing']
      };
    }
  }

  /**
   * Export test results in various formats
   */
  async exportTestResults(
    results: any,
    format: 'json' | 'csv' | 'html' | 'pdf'
  ): Promise<string> {
    try {
      return await invoke('export_test_results', {
        results,
        format
      });
    } catch (error) {
      console.error('Export failed:', error);
      throw error;
    }
  }
}

// Singleton instance for global use
export const enhancedSelectorTester = new EnhancedSelectorTester();
