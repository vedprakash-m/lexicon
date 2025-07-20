import React, { useState } from 'react';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle,
  Button, 
  Input, 
  Label, 
  Textarea,
  Select,
  Card,
  Badge
} from '../ui';
import { 
  Plus, 
  X, 
  Upload, 
  FolderOpen,
  FileText,
  Settings,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { useFormValidation, ValidationRules } from '../../utils/formValidation';
import type { BatchJobCreate } from '../../hooks/useBatchProcessing';

interface BatchJobCreationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (jobData: BatchJobCreate) => Promise<void>;
}

export function BatchJobCreationDialog({ isOpen, onClose, onSubmit }: BatchJobCreationDialogProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [sources, setSources] = useState<string[]>([]);
  const [newSource, setNewSource] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [parallelSources, setParallelSources] = useState(true);
  const [parallelPages, setParallelPages] = useState(false);

  const {
    validation,
    values,
    setValue,
    validateForm,
    validateField,
    getFieldError,
    hasFieldError
  } = useFormValidation({
    name: [ValidationRules.required(), ValidationRules.minLength(3), ValidationRules.maxLength(100)],
    description: [ValidationRules.required(), ValidationRules.minLength(10), ValidationRules.maxLength(500)],
    priority: [ValidationRules.required()],
    sources: [ValidationRules.custom((value: string[]) => Array.isArray(value) && value.length > 0, 'At least one source is required')]
  });

  const steps = [
    {
      title: 'Job Details',
      description: 'Basic information about your batch job'
    },
    {
      title: 'Sources',
      description: 'Select files or URLs to process'
    },
    {
      title: 'Processing Options',
      description: 'Configure processing parameters'
    },
    {
      title: 'Review & Create',
      description: 'Review your configuration'
    }
  ];

  const addSource = () => {
    if (newSource.trim()) {
      const updatedSources = [...sources, newSource.trim()];
      setSources(updatedSources);
      setValue('sources', updatedSources);
      setNewSource('');
    }
  };

  const removeSource = (index: number) => {
    const updatedSources = sources.filter((_, i) => i !== index);
    setSources(updatedSources);
    setValue('sources', updatedSources);
  };

  const handleFileUpload = async () => {
    try {
      // This would open a file dialog and handle file selection
      // For now, we'll simulate adding a file path
      const mockFilePath = '/path/to/selected/file.pdf';
      const updatedSources = [...sources, mockFilePath];
      setSources(updatedSources);
      setValue('sources', updatedSources);
    } catch (error) {
      console.error('File upload failed:', error);
    }
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    const validation = validateForm();
    if (!validation.isValid) {
      return;
    }

    setSubmitting(true);
    try {
      await onSubmit({
        name: values.name || '',
        description: values.description || '',
        priority: values.priority || 'normal',
        sources,
        parallelSources,
        parallelPages
      });
      
      // Reset form and close dialog
      setSources([]);
      setCurrentStep(0);
      setParallelSources(true);
      setParallelPages(false);
      onClose();
    } catch (error) {
      console.error('Failed to create batch job:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    setSources([]);
    setCurrentStep(0);
    setParallelSources(true);
    setParallelPages(false);
    onClose();
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Job Name *</Label>
              <Input
                id="name"
                value={values.name || ''}
                onChange={(e) => setValue('name', e.target.value)}
                onBlur={() => validateField('name')}
                placeholder="e.g., Complete Vedabase Collection"
                className={hasFieldError('name') ? 'border-red-500' : ''}
              />
              {hasFieldError('name') && (
                <p className="text-sm text-red-600 mt-1">{getFieldError('name')}</p>
              )}
            </div>

            <div>
              <Label htmlFor="description">Description *</Label>
              <Textarea
                id="description"
                value={values.description || ''}
                onChange={(e) => setValue('description', e.target.value)}
                onBlur={() => validateField('description')}
                placeholder="Describe what this batch job will accomplish..."
                rows={3}
                className={hasFieldError('description') ? 'border-red-500' : ''}
              />
              {hasFieldError('description') && (
                <p className="text-sm text-red-600 mt-1">{getFieldError('description')}</p>
              )}
            </div>

            <div>
              <Label htmlFor="priority">Priority</Label>
              <Select
                value={values.priority || 'normal'}
                onValueChange={(value) => setValue('priority', value)}
                options={[
                  { value: 'low', label: 'Low - Background processing' },
                  { value: 'normal', label: 'Normal - Standard priority' },
                  { value: 'high', label: 'High - Expedited processing' },
                  { value: 'urgent', label: 'Urgent - Immediate processing' }
                ]}
              />
            </div>
          </div>
        );

      case 1:
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label>Sources ({sources.length})</Label>
              <div className="flex space-x-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleFileUpload}
                >
                  <Upload className="h-4 w-4 mr-2" />
                  Upload Files
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    // This would open a folder selection dialog
                    const mockFolderPath = '/path/to/selected/folder';
                    const updatedSources = [...sources, `${mockFolderPath}/*`];
                    setSources(updatedSources);
                    setValue('sources', updatedSources);
                  }}
                >
                  <FolderOpen className="h-4 w-4 mr-2" />
                  Add Folder
                </Button>
              </div>
            </div>

            <div className="flex space-x-2">
              <Input
                value={newSource}
                onChange={(e) => setNewSource(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addSource()}
                placeholder="Add file path or URL..."
                className="flex-1"
              />
              <Button
                type="button"
                onClick={addSource}
                disabled={!newSource.trim()}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>

            {hasFieldError('sources') && (
              <p className="text-sm text-red-600">{getFieldError('sources')}</p>
            )}

            <div className="space-y-2 max-h-48 overflow-y-auto">
              {sources.map((source, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                  <div className="flex items-center space-x-3">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">{source}</span>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => removeSource(index)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <Card className="p-4">
              <h3 className="font-medium mb-4 flex items-center">
                <Settings className="h-4 w-4 mr-2" />
                Processing Configuration
              </h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Parallel Sources</Label>
                    <p className="text-sm text-muted-foreground">
                      Process multiple sources simultaneously for faster completion
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={parallelSources}
                    onChange={(e) => setParallelSources(e.target.checked)}
                    className="h-4 w-4"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Parallel Pages</Label>
                    <p className="text-sm text-muted-foreground">
                      Process pages within each source in parallel (higher memory usage)
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={parallelPages}
                    onChange={(e) => setParallelPages(e.target.checked)}
                    className="h-4 w-4"
                  />
                </div>
              </div>
            </Card>

            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="flex items-start space-x-3">
                <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-blue-900">Performance Tips</h4>
                  <ul className="text-sm text-blue-800 mt-2 space-y-1">
                    <li>• Enable parallel sources for large batch jobs</li>
                    <li>• Parallel pages work best with adequate RAM (8GB+)</li>
                    <li>• Higher priority jobs may slow down other processes</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <Card className="p-4">
              <h3 className="font-medium mb-4">Job Summary</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <Label>Name</Label>
                  <p className="font-medium">{values.name}</p>
                </div>
                <div>
                  <Label>Priority</Label>
                  <Badge variant={
                    values.priority === 'urgent' ? 'destructive' :
                    values.priority === 'high' ? 'default' :
                    'secondary'
                  }>
                    {values.priority}
                  </Badge>
                </div>
                <div className="col-span-2">
                  <Label>Description</Label>
                  <p className="text-muted-foreground">{values.description}</p>
                </div>
              </div>
            </Card>

            <Card className="p-4">
              <h3 className="font-medium mb-4">Sources ({sources.length})</h3>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {sources.slice(0, 3).map((source, index) => (
                  <div key={index} className="text-sm text-muted-foreground">
                    {source}
                  </div>
                ))}
                {sources.length > 3 && (
                  <p className="text-sm text-muted-foreground">
                    ...and {sources.length - 3} more sources
                  </p>
                )}
              </div>
            </Card>

            <Card className="p-4">
              <h3 className="font-medium mb-4">Processing Options</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Parallel Sources:</span>
                  <span className={parallelSources ? 'text-green-600' : 'text-muted-foreground'}>
                    {parallelSources ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Parallel Pages:</span>
                  <span className={parallelPages ? 'text-green-600' : 'text-muted-foreground'}>
                    {parallelPages ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
              </div>
            </Card>

            <div className="p-4 bg-green-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <div>
                  <h4 className="font-medium text-green-900">Ready to Create</h4>
                  <p className="text-sm text-green-800">
                    Your batch job configuration is complete and ready to submit.
                  </p>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={isOpen} onClose={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle>Create New Batch Job</DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex flex-col">
          {/* Progress Steps */}
          <div className="flex items-center justify-between mb-6 px-1">
            {steps.map((step, index) => (
              <div
                key={index}
                className={`flex items-center ${index < steps.length - 1 ? 'flex-1' : ''}`}
              >
                <div className={`
                  w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                  ${index <= currentStep 
                    ? 'bg-primary text-primary-foreground' 
                    : 'bg-muted text-muted-foreground'
                  }
                `}>
                  {index + 1}
                </div>
                <div className="ml-3 min-w-0">
                  <p className={`text-sm font-medium ${
                    index <= currentStep ? 'text-foreground' : 'text-muted-foreground'
                  }`}>
                    {step.title}
                  </p>
                  <p className="text-xs text-muted-foreground hidden sm:block">
                    {step.description}
                  </p>
                </div>
                {index < steps.length - 1 && (
                  <div className={`flex-1 h-px mx-4 ${
                    index < currentStep ? 'bg-primary' : 'bg-muted'
                  }`} />
                )}
              </div>
            ))}
          </div>

          {/* Step Content */}
          <div className="flex-1 overflow-y-auto">
            {renderStepContent()}
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between pt-6 border-t border-border">
            <Button
              variant="outline"
              onClick={currentStep === 0 ? handleClose : handlePrevious}
            >
              {currentStep === 0 ? 'Cancel' : 'Previous'}
            </Button>

            <div className="flex space-x-3">
              {currentStep < steps.length - 1 ? (
                <Button onClick={handleNext}>
                  Next
                </Button>
              ) : (
                <Button
                  onClick={handleSubmit}
                  disabled={submitting || !validateForm().isValid}
                >
                  {submitting ? 'Creating...' : 'Create Job'}
                </Button>
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
