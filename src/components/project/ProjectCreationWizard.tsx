import { useState } from 'react';
import { Button, Input, Label, Textarea, Card, Badge } from '../ui';
import { FolderOpen, Settings, Download, ArrowRight, ArrowLeft, Check } from 'lucide-react';

interface ProjectData {
  name: string;
  description: string;
  type: 'processing' | 'collection' | 'export';
  status: 'active' | 'completed' | 'paused';
  booksCount: number;
  createdAt: Date;
  lastModified: Date;
}

interface ProjectCreationWizardProps {
  onComplete: (project: ProjectData) => void;
  onCancel: () => void;
}

export function ProjectCreationWizard({ onComplete, onCancel }: ProjectCreationWizardProps) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    type: 'collection' as const,
    template: ''
  });

  const projectTypes = [
    {
      id: 'collection',
      title: 'Book Collection',
      description: 'Organize books by topic, genre, or purpose',
      icon: FolderOpen,
      examples: ['Spiritual Texts', 'Philosophy Books', 'Technical References']
    },
    {
      id: 'processing',
      title: 'Processing Workflow',
      description: 'Configure specific processing rules and formats',
      icon: Settings,
      examples: ['RAG Dataset', 'Research Notes', 'Study Materials']
    },
    {
      id: 'export',
      title: 'Export Configuration',
      description: 'Set up export formats and destinations',
      icon: Download,
      examples: ['LangChain Format', 'CSV Export', 'API Integration']
    }
  ];

  const templates = {
    collection: [
      { id: 'spiritual', name: 'Spiritual Texts', description: 'Vedic literature, Buddhism, Christianity, etc.' },
      { id: 'philosophy', name: 'Philosophy', description: 'Western and Eastern philosophical works' },
      { id: 'technical', name: 'Technical Books', description: 'Programming, AI/ML, science' },
      { id: 'literature', name: 'Literature', description: 'Fiction, poetry, classic works' },
      { id: 'custom', name: 'Custom Collection', description: 'Start from scratch' }
    ],
    processing: [
      { id: 'rag-optimal', name: 'RAG Optimized', description: 'Optimized chunks for RAG applications' },
      { id: 'research', name: 'Research Notes', description: 'Detailed chunks with citations' },
      { id: 'study', name: 'Study Materials', description: 'Educational content with summaries' },
      { id: 'custom', name: 'Custom Processing', description: 'Configure your own rules' }
    ],
    export: [
      { id: 'langchain', name: 'LangChain/LlamaIndex', description: 'JSON format for popular frameworks' },
      { id: 'openai', name: 'OpenAI Fine-tuning', description: 'JSONL format for model training' },
      { id: 'csv', name: 'CSV/Spreadsheet', description: 'Tabular format for analysis' },
      { id: 'custom', name: 'Custom Format', description: 'Define your own export format' }
    ]
  };

  const handleNext = () => {
    if (step < 3) setStep(step + 1);
  };

  const handleBack = () => {
    if (step > 1) setStep(step - 1);
  };

  const handleComplete = () => {
    const project: ProjectData = {
      name: formData.name,
      description: formData.description,
      type: formData.type,
      status: 'active',
      booksCount: 0,
      createdAt: new Date(),
      lastModified: new Date()
    };
    onComplete(project);
  };

  const isStepValid = () => {
    switch (step) {
      case 1: return true; // type is always set to 'collection' by default
      case 2: return formData.template !== '';
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

      {/* Step 1: Choose Project Type */}
      {step === 1 && (
        <div className="space-y-4">
          <div className="text-center">
            <h3 className="text-lg font-semibold">Choose Project Type</h3>
            <p className="text-sm text-muted-foreground">
              What kind of project would you like to create?
            </p>
          </div>

          <div className="grid gap-4">
            {projectTypes.map((type) => {
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
                      <div className="flex flex-wrap gap-1">
                        {type.examples.map((example, idx) => (
                          <Badge key={idx} variant="secondary" className="text-xs">
                            {example}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Step 2: Choose Template */}
      {step === 2 && (
        <div className="space-y-4">
          <div className="text-center">
            <h3 className="text-lg font-semibold">Choose Template</h3>
            <p className="text-sm text-muted-foreground">
              Select a template to get started quickly
            </p>
          </div>

          <div className="grid gap-3">
            {templates[formData.type].map((template) => (
              <Card 
                key={template.id}
                className={`p-4 cursor-pointer transition-all ${
                  formData.template === template.id 
                    ? 'border-primary bg-primary/5' 
                    : 'hover:border-muted-foreground/50'
                }`}
                onClick={() => setFormData(prev => ({ ...prev, template: template.id }))}
              >
                <div>
                  <h4 className="font-medium">{template.name}</h4>
                  <p className="text-sm text-muted-foreground">{template.description}</p>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Step 3: Project Details */}
      {step === 3 && (
        <div className="space-y-4">
          <div className="text-center">
            <h3 className="text-lg font-semibold">Project Details</h3>
            <p className="text-sm text-muted-foreground">
              Give your project a name and description
            </p>
          </div>

          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Project Name</Label>
              <Input
                id="name"
                placeholder="e.g., Spiritual Texts Collection"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              />
            </div>

            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Describe the purpose and scope of your project..."
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
              />
            </div>

            {/* Summary */}
            <Card className="p-4 bg-muted/50">
              <h4 className="font-medium mb-2">Project Summary</h4>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Type:</span>
                  <span className="capitalize">{formData.type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Template:</span>
                  <span>{templates[formData.type].find(t => t.id === formData.template)?.name}</span>
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
              Create Project
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
