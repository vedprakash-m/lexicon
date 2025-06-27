import { useState } from 'react';
import { Button, Input, Label, Textarea, Card, Badge } from '../ui';
import { Plus, Trash2, Eye, Save, ArrowLeft } from 'lucide-react';

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

interface RuleEditorProps {
  onComplete: (rule: RuleData) => void;
  onCancel: () => void;
}

export function RuleEditor({ onComplete, onCancel }: RuleEditorProps) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    domain_patterns: [''],
    selectors: {} as Record<string, Selector>
  });

  const [currentSelector, setCurrentSelector] = useState<Selector>({
    name: '',
    selector: '',
    fallback_selectors: [],
    transform: 'clean_whitespace',
    required: false,
    description: ''
  });

  const [showSelectorForm, setShowSelectorForm] = useState(false);
  const [testHtml, setTestHtml] = useState('');

  const addDomainPattern = () => {
    setFormData(prev => ({
      ...prev,
      domain_patterns: [...prev.domain_patterns, '']
    }));
  };

  const updateDomainPattern = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      domain_patterns: prev.domain_patterns.map((pattern, i) => 
        i === index ? value : pattern
      )
    }));
  };

  const removeDomainPattern = (index: number) => {
    setFormData(prev => ({
      ...prev,
      domain_patterns: prev.domain_patterns.filter((_, i) => i !== index)
    }));
  };

  const addSelector = () => {
    if (!currentSelector.name || !currentSelector.selector) return;
    
    setFormData(prev => ({
      ...prev,
      selectors: {
        ...prev.selectors,
        [currentSelector.name]: { ...currentSelector }
      }
    }));

    setCurrentSelector({
      name: '',
      selector: '',
      fallback_selectors: [],
      transform: 'clean_whitespace',
      required: false,
      description: ''
    });
    setShowSelectorForm(false);
  };

  const removeSelector = (name: string) => {
    setFormData(prev => ({
      ...prev,
      selectors: Object.fromEntries(
        Object.entries(prev.selectors).filter(([key]) => key !== name)
      )
    }));
  };

  const handleComplete = () => {
    const rule: RuleData = {
      name: formData.name,
      description: formData.description,
      domain_patterns: formData.domain_patterns.filter(p => p.trim() !== ''),
      selectors: formData.selectors,
      status: 'inactive',
      type: 'custom',
      lastTested: new Date(),
      successRate: 0
    };
    onComplete(rule);
  };

  const isValid = () => {
    return formData.name.trim() !== '' && 
           formData.description.trim() !== '' &&
           formData.domain_patterns.some(p => p.trim() !== '') &&
           Object.keys(formData.selectors).length > 0;
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-semibold">Create Custom Extraction Rule</h3>
        <p className="text-sm text-muted-foreground">
          Define how to extract content from specific websites
        </p>
      </div>

      {/* Basic Information */}
      <Card className="p-4">
        <h4 className="font-medium mb-3">Basic Information</h4>
        <div className="space-y-4">
          <div>
            <Label htmlFor="name">Rule Name</Label>
            <Input
              id="name"
              placeholder="e.g., my_website_rule"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            />
          </div>

          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Describe what this rule extracts..."
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              rows={2}
            />
          </div>
        </div>
      </Card>

      {/* Domain Patterns */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium">Domain Patterns</h4>
          <Button variant="outline" size="sm" onClick={addDomainPattern}>
            <Plus className="h-3 w-3 mr-1" />
            Add Pattern
          </Button>
        </div>
        <div className="space-y-2">
          {formData.domain_patterns.map((pattern, index) => (
            <div key={index} className="flex space-x-2">
              <Input
                placeholder="e.g., example\\.com/articles/.*"
                value={pattern}
                onChange={(e) => updateDomainPattern(index, e.target.value)}
                className="flex-1"
              />
              {formData.domain_patterns.length > 1 && (
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => removeDomainPattern(index)}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              )}
            </div>
          ))}
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Use regex patterns to match website URLs. Use \\.  to escape dots.
        </p>
      </Card>

      {/* Selectors */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium">Content Selectors</h4>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => setShowSelectorForm(true)}
          >
            <Plus className="h-3 w-3 mr-1" />
            Add Selector
          </Button>
        </div>

        {/* Existing Selectors */}
        <div className="space-y-2 mb-4">
          {Object.entries(formData.selectors).map(([name, selector]) => (
            <div key={name} className="flex items-center justify-between p-3 border rounded">
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <span className="font-medium">{name}</span>
                  {selector.required && (
                    <Badge variant="destructive" className="text-xs">Required</Badge>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">{selector.description}</p>
                <code className="text-xs bg-muted px-1 rounded">{selector.selector}</code>
              </div>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => removeSelector(name)}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          ))}
        </div>

        {/* Selector Form */}
        {showSelectorForm && (
          <Card className="p-4 bg-muted/50">
            <h5 className="font-medium mb-3">Add New Selector</h5>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label htmlFor="selector-name">Selector Name</Label>
                  <Input
                    id="selector-name"
                    placeholder="e.g., title"
                    value={currentSelector.name}
                    onChange={(e) => setCurrentSelector(prev => ({ ...prev, name: e.target.value }))}
                  />
                </div>
                <div>
                  <Label htmlFor="selector-css">CSS Selector</Label>
                  <Input
                    id="selector-css"
                    placeholder="e.g., h1.title"
                    value={currentSelector.selector}
                    onChange={(e) => setCurrentSelector(prev => ({ ...prev, selector: e.target.value }))}
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="selector-desc">Description</Label>
                <Input
                  id="selector-desc"
                  placeholder="What this selector extracts..."
                  value={currentSelector.description}
                  onChange={(e) => setCurrentSelector(prev => ({ ...prev, description: e.target.value }))}
                />
              </div>

              <div className="flex items-center space-x-4">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={currentSelector.required}
                    onChange={(e) => setCurrentSelector(prev => ({ ...prev, required: e.target.checked }))}
                  />
                  <span className="text-sm">Required</span>
                </label>
              </div>

              <div className="flex space-x-2">
                <Button variant="outline" size="sm" onClick={addSelector}>
                  <Save className="h-3 w-3 mr-1" />
                  Add Selector
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setShowSelectorForm(false)}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </Card>
        )}
      </Card>

      {/* Test Section */}
      <Card className="p-4">
        <h4 className="font-medium mb-3">Test Rule</h4>
        <div className="space-y-3">
          <div>
            <Label htmlFor="test-html">Test HTML (Optional)</Label>
            <Textarea
              id="test-html"
              placeholder="Paste HTML content to test your selectors..."
              value={testHtml}
              onChange={(e) => setTestHtml(e.target.value)}
              rows={4}
            />
          </div>
          <Button variant="outline" size="sm">
            <Eye className="h-3 w-3 mr-1" />
            Test Selectors
          </Button>
        </div>
      </Card>

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t">
        <Button variant="outline" onClick={onCancel}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Cancel
        </Button>

        <Button onClick={handleComplete} disabled={!isValid()}>
          <Save className="h-4 w-4 mr-2" />
          Create Rule
        </Button>
      </div>
    </div>
  );
}
