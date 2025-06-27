import { useState } from 'react';
import { Button, Input, Label, Textarea, Select, Card } from '../ui';
import { Globe, FileText, Database, ArrowRight, ArrowLeft, Check } from 'lucide-react';

interface ScrapingRule {
  id: string;
  name: string;
  description: string;
  domain_patterns: string[];
  selectors: Record<string, any>;
  status: 'active' | 'inactive' | 'testing';
  type: 'built-in' | 'custom';
}

interface SourceData {
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

interface SourceCreationWizardProps {
  rules: ScrapingRule[];
  onComplete: (source: SourceData) => void;
  onCancel: () => void;
}

export function SourceCreationWizard({ rules, onComplete, onCancel }: SourceCreationWizardProps) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    url: '',
    type: 'website' as const,
    ruleId: '',
    projectId: ''
  });

  const sourceTypes = [
    {
      id: 'website',
      title: 'Website',
      description: 'Scrape content from web pages',
      icon: Globe,
      examples: ['Academic papers', 'Blog posts', 'News articles']
    },
    {
      id: 'api',
      title: 'API Endpoint',
      description: 'Fetch data from REST APIs',
      icon: Database,
      examples: ['JSON APIs', 'RSS feeds', 'Academic databases']
    },
    {
      id: 'file',
      title: 'File Upload',
      description: 'Process uploaded documents',
      icon: FileText,
      examples: ['PDFs', 'EPUB files', 'Text documents']
    }
  ];

  const handleNext = () => {
    if (step < 3) setStep(step + 1);
  };

  const handleBack = () => {
    if (step > 1) setStep(step - 1);
  };

  const handleComplete = () => {
    const source: SourceData = {
      name: formData.name,
      description: formData.description,
      url: formData.url,
      type: formData.type,
      ruleId: formData.ruleId,
      status: 'inactive',
      lastScraped: new Date(),
      totalPages: 0,
      projectId: formData.projectId || undefined
    };
    onComplete(source);
  };

  const isStepValid = () => {
    switch (step) {
      case 1: return true; // type is always valid
      case 2: return formData.url.trim() !== '' && formData.ruleId !== '';
      case 3: return formData.name.trim() !== '' && formData.description.trim() !== '';
      default: return false;
    }
  };

  return (
    <div className="space-y-6">
      {/* Progress Indicator */}
      <div className="flex items-center justify-center space-x-2">
        {[1, 2, 3].map((stepNum) => (
          <div key={stepNum} className="flex items-center">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              stepNum <= step 
                ? 'bg-primary text-primary-foreground' 
                : 'bg-muted text-muted-foreground'
            }`}>
              {stepNum < step ? <Check className="h-4 w-4" /> : stepNum}
            </div>
            {stepNum < 3 && (
              <div className={`w-8 h-0.5 ${stepNum < step ? 'bg-primary' : 'bg-muted'}`} />
            )}
          </div>
        ))}
      </div>

      {/* Step 1: Choose Source Type */}
      {step === 1 && (
        <div className="space-y-4">
          <div className="text-center">
            <h3 className="text-lg font-semibold">Choose Source Type</h3>
            <p className="text-sm text-muted-foreground">
              What kind of content source would you like to configure?
            </p>
          </div>

          <div className="grid gap-4">
            {sourceTypes.map((type) => {
              const Icon = type.icon;
              return (
                <Card 
                  key={type.id}
                  className={`p-4 cursor-pointer transition-all ${
                    formData.type === type.id 
                      ? 'border-primary bg-primary/5' 
                      : 'hover:border-muted-foreground/50'
                  }`}
                  onClick={() => setFormData(prev => ({ ...prev, type: type.id as any }))}
                >
                  <div className="flex items-start space-x-3">
                    <Icon className="h-5 w-5 text-primary mt-0.5" />
                    <div className="flex-1">
                      <h4 className="font-medium">{type.title}</h4>
                      <p className="text-sm text-muted-foreground mb-2">{type.description}</p>
                      <div className="text-xs text-muted-foreground">
                        Examples: {type.examples.join(', ')}
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Step 2: Configure Source */}
      {step === 2 && (
        <div className="space-y-4">
          <div className="text-center">
            <h3 className="text-lg font-semibold">Configure Source</h3>
            <p className="text-sm text-muted-foreground">
              Provide the source details and select extraction rules
            </p>
          </div>

          <div className="space-y-4">
            <div>
              <Label htmlFor="url">Source URL</Label>
              <Input
                id="url"
                placeholder="https://example.com/content"
                value={formData.url}
                onChange={(e) => setFormData(prev => ({ ...prev, url: e.target.value }))}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Enter the base URL or starting point for content extraction
              </p>
            </div>

            <div>
              <Label htmlFor="rule">Extraction Rule</Label>
              <Select
                value={formData.ruleId}
                onValueChange={(value) => setFormData(prev => ({ ...prev, ruleId: value }))}
                placeholder="Select a rule..."
                options={rules.map(rule => ({
                  value: rule.id,
                  label: `${rule.name} - ${rule.description}`
                }))}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Choose the extraction rule that best matches your source
              </p>
            </div>

            {formData.ruleId && (
              <Card className="p-4 bg-muted/50">
                <h4 className="font-medium mb-2">Selected Rule Preview</h4>
                {(() => {
                  const rule = rules.find(r => r.id === formData.ruleId);
                  return rule ? (
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Name:</span>
                        <span>{rule.name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Type:</span>
                        <span className="capitalize">{rule.type}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Domain Patterns:</span>
                        <span>{rule.domain_patterns.length}</span>
                      </div>
                    </div>
                  ) : null;
                })()}
              </Card>
            )}
          </div>
        </div>
      )}

      {/* Step 3: Source Details */}
      {step === 3 && (
        <div className="space-y-4">
          <div className="text-center">
            <h3 className="text-lg font-semibold">Source Details</h3>
            <p className="text-sm text-muted-foreground">
              Give your source a name and description
            </p>
          </div>

          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Source Name</Label>
              <Input
                id="name"
                placeholder="e.g., Bhagavad Gita Complete"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              />
            </div>

            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Describe what content this source provides..."
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
              />
            </div>

            {/* Summary */}
            <Card className="p-4 bg-muted/50">
              <h4 className="font-medium mb-2">Source Summary</h4>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Type:</span>
                  <span className="capitalize">{formData.type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">URL:</span>
                  <span className="truncate max-w-[200px]">{formData.url}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Rule:</span>
                  <span>{rules.find(r => r.id === formData.ruleId)?.name}</span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between pt-4 border-t">
        <Button 
          variant="outline" 
          onClick={step === 1 ? onCancel : handleBack}
        >
          {step === 1 ? (
            'Cancel'
          ) : (
            <>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </>
          )}
        </Button>

        <Button 
          onClick={step === 3 ? handleComplete : handleNext}
          disabled={!isStepValid()}
        >
          {step === 3 ? (
            <>
              <Check className="h-4 w-4 mr-2" />
              Create Source
            </>
          ) : (
            <>
              Next
              <ArrowRight className="h-4 w-4 ml-2" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
