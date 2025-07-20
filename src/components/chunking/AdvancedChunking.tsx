import React, { useState, useEffect } from 'react';
import { 
  Button, 
  Card, 
  Input, 
  Label, 
  Select, 
  Tabs, 
  TabList, 
  Tab, 
  TabPanels, 
  TabPanel,
  Badge,
  Progress,
  Textarea
} from '../ui';
import { 
  Brain, 
  FileText, 
  Layers, 
  Settings, 
  Play, 
  Eye, 
  Save,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Target
} from 'lucide-react';
import { invoke } from '@tauri-apps/api/core';
import { useToastActions } from '../ui/toast';

interface ChunkingStrategy {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  params: ChunkingParam[];
}

interface ChunkingParam {
  key: string;
  label: string;
  type: 'number' | 'boolean' | 'select' | 'text';
  default: any;
  min?: number;
  max?: number;
  options?: { value: string; label: string }[];
  description?: string;
}

interface ChunkingJob {
  id: string;
  name: string;
  strategy: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  inputFiles: number;
  outputChunks: number;
  createdAt: Date;
}

interface AdvancedChunkingProps {
  onChunkingComplete?: (jobId: string, chunks: any[]) => void;
}

const CHUNKING_STRATEGIES: ChunkingStrategy[] = [
  {
    id: 'fixed-size',
    name: 'Fixed Size',
    description: 'Split text into chunks of fixed character or token count',
    icon: Layers,
    params: [
      { key: 'chunk_size', label: 'Chunk Size', type: 'number', default: 1000, min: 100, max: 8000, description: 'Number of characters per chunk' },
      { key: 'overlap', label: 'Overlap', type: 'number', default: 200, min: 0, max: 1000, description: 'Character overlap between chunks' },
      { key: 'preserve_sentences', label: 'Preserve Sentences', type: 'boolean', default: true, description: 'Avoid splitting sentences' }
    ]
  },
  {
    id: 'semantic',
    name: 'Semantic',
    description: 'Split text based on semantic boundaries and meaning',
    icon: Brain,
    params: [
      { key: 'min_chunk_size', label: 'Minimum Size', type: 'number', default: 500, min: 100, max: 2000 },
      { key: 'max_chunk_size', label: 'Maximum Size', type: 'number', default: 2000, min: 1000, max: 8000 },
      { key: 'similarity_threshold', label: 'Similarity Threshold', type: 'number', default: 0.7, min: 0.1, max: 1.0, description: 'Semantic similarity threshold' }
    ]
  },
  {
    id: 'hierarchical',
    name: 'Hierarchical',
    description: 'Respect document structure (headings, paragraphs, sections)',
    icon: FileText,
    params: [
      { key: 'max_chunk_size', label: 'Maximum Size', type: 'number', default: 1500, min: 500, max: 5000 },
      { key: 'respect_headers', label: 'Respect Headers', type: 'boolean', default: true },
      { key: 'include_context', label: 'Include Context', type: 'boolean', default: true, description: 'Include parent section context' }
    ]
  },
  {
    id: 'adaptive',
    name: 'Adaptive',
    description: 'Dynamically adjust chunk size based on content complexity',
    icon: Target,
    params: [
      { key: 'target_size', label: 'Target Size', type: 'number', default: 1200, min: 500, max: 3000 },
      { key: 'complexity_factor', label: 'Complexity Factor', type: 'number', default: 1.2, min: 0.5, max: 2.0 },
      { key: 'adapt_to_content', label: 'Adapt to Content Type', type: 'boolean', default: true }
    ]
  }
];

export default function AdvancedChunking({ onChunkingComplete }: AdvancedChunkingProps) {
  const [selectedStrategy, setSelectedStrategy] = useState<string>('fixed-size');
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [previewText, setPreviewText] = useState('');
  const [previewChunks, setPreviewChunks] = useState<any[]>([]);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [chunkingJobs, setChunkingJobs] = useState<ChunkingJob[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [jobName, setJobName] = useState('');
  const [activeTab, setActiveTab] = useState(0);
  const toast = useToastActions();

  // Initialize parameters when strategy changes
  useEffect(() => {
    const strategy = CHUNKING_STRATEGIES.find(s => s.id === selectedStrategy);
    if (strategy) {
      const defaultParams: Record<string, any> = {};
      strategy.params.forEach(param => {
        defaultParams[param.key] = param.default;
      });
      setParameters(defaultParams);
    }
  }, [selectedStrategy]);

  // Load chunking jobs on mount
  useEffect(() => {
    loadChunkingJobs();
  }, []);

  const loadChunkingJobs = async () => {
    try {
      const jobs = await invoke('get_chunking_jobs') as ChunkingJob[];
      setChunkingJobs(jobs);
    } catch (error) {
      console.error('Failed to load chunking jobs:', error);
    }
  };

  const handleParameterChange = (key: string, value: any) => {
    setParameters(prev => ({ ...prev, [key]: value }));
  };

  const generatePreview = async () => {
    if (!previewText.trim()) {
      toast.warning('Preview Text Required', 'Please enter some text to preview chunking.');
      return;
    }

    setIsPreviewLoading(true);
    try {
      const chunks = await invoke('preview_chunking', {
        text: previewText,
        strategy: selectedStrategy,
        parameters
      }) as any[];
      
      setPreviewChunks(chunks);
      toast.success('Preview Generated', `Generated ${chunks.length} chunks for preview.`);
    } catch (error) {
      console.error('Failed to generate preview:', error);
      toast.error('Preview Failed', 'Could not generate chunking preview.');
    } finally {
      setIsPreviewLoading(false);
    }
  };

  const startChunkingJob = async () => {
    if (!jobName.trim()) {
      toast.warning('Job Name Required', 'Please enter a name for this chunking job.');
      return;
    }

    if (selectedFiles.length === 0) {
      toast.warning('Files Required', 'Please select files to chunk.');
      return;
    }

    try {
      const jobId = await invoke('start_chunking_job', {
        name: jobName,
        strategy: selectedStrategy,
        parameters,
        files: selectedFiles
      }) as string;

      toast.success('Job Started', `Chunking job "${jobName}" has been started.`);
      setJobName('');
      setSelectedFiles([]);
      await loadChunkingJobs();
      
      if (onChunkingComplete) {
        // Monitor job completion
        const checkJob = setInterval(async () => {
          try {
            const job = await invoke('get_chunking_job', { jobId }) as ChunkingJob;
            if (job.status === 'completed') {
              clearInterval(checkJob);
              const chunks = await invoke('get_job_chunks', { jobId });
              onChunkingComplete(jobId, chunks);
            }
          } catch (error) {
            clearInterval(checkJob);
          }
        }, 2000);
      }

    } catch (error) {
      console.error('Failed to start chunking job:', error);
      toast.error('Job Failed', 'Could not start chunking job.');
    }
  };

  const currentStrategy = CHUNKING_STRATEGIES.find(s => s.id === selectedStrategy);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Brain className="h-8 w-8 text-primary" />
            Advanced Chunking
          </h1>
          <p className="text-muted-foreground mt-1">
            Configure intelligent text chunking strategies for optimal RAG performance
          </p>
        </div>
        
        <Button onClick={loadChunkingJobs} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      <Tabs defaultIndex={activeTab} onIndexChange={setActiveTab}>
        <TabList>
          <Tab>Strategy Configuration</Tab>
          <Tab>Preview & Test</Tab>
          <Tab>Chunking Jobs</Tab>
        </TabList>

        <TabPanels>
          {/* Strategy Configuration Tab */}
          <TabPanel className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Choose Chunking Strategy</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                {CHUNKING_STRATEGIES.map((strategy) => {
                  const Icon = strategy.icon;
                  return (
                    <div
                      key={strategy.id}
                      className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                        selectedStrategy === strategy.id
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:bg-accent/50'
                      }`}
                      onClick={() => setSelectedStrategy(strategy.id)}
                    >
                      <div className="flex items-start gap-3">
                        <Icon className={`h-6 w-6 mt-1 ${
                          selectedStrategy === strategy.id ? 'text-primary' : 'text-muted-foreground'
                        }`} />
                        <div>
                          <h4 className="font-medium">{strategy.name}</h4>
                          <p className="text-sm text-muted-foreground mt-1">
                            {strategy.description}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Strategy Parameters */}
              {currentStrategy && (
                <div className="space-y-4">
                  <h4 className="font-medium flex items-center gap-2">
                    <Settings className="h-4 w-4" />
                    {currentStrategy.name} Parameters
                  </h4>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {currentStrategy.params.map((param) => (
                      <div key={param.key} className="space-y-2">
                        <Label htmlFor={param.key}>
                          {param.label}
                          {param.description && (
                            <span className="text-xs text-muted-foreground block">
                              {param.description}
                            </span>
                          )}
                        </Label>
                        
                        {param.type === 'number' && (
                          <Input
                            id={param.key}
                            type="number"
                            value={parameters[param.key] || param.default}
                            onChange={(e) => handleParameterChange(param.key, Number(e.target.value))}
                            min={param.min}
                            max={param.max}
                          />
                        )}
                        
                        {param.type === 'boolean' && (
                          <div className="flex items-center space-x-2">
                            <input
                              id={param.key}
                              type="checkbox"
                              checked={parameters[param.key] || param.default}
                              onChange={(e) => handleParameterChange(param.key, e.target.checked)}
                              className="rounded border-input"
                            />
                            <Label htmlFor={param.key}>Enable</Label>
                          </div>
                        )}
                        
                        {param.type === 'select' && param.options && (
                          <Select
                            value={parameters[param.key] || param.default}
                            onValueChange={(value) => handleParameterChange(param.key, value)}
                            options={param.options}
                          />
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          </TabPanel>

          {/* Preview & Test Tab */}
          <TabPanel className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Input */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Preview Input</h3>
                <div className="space-y-4">
                  <Textarea
                    placeholder="Paste text here to preview how it will be chunked..."
                    value={previewText}
                    onChange={(e) => setPreviewText(e.target.value)}
                    rows={12}
                    className="resize-none"
                  />
                  <Button
                    onClick={generatePreview}
                    disabled={isPreviewLoading || !previewText.trim()}
                    className="w-full"
                  >
                    {isPreviewLoading ? (
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Eye className="h-4 w-4 mr-2" />
                    )}
                    Generate Preview
                  </Button>
                </div>
              </Card>

              {/* Preview Results */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">
                  Preview Results {previewChunks.length > 0 && (
                    <Badge variant="secondary" className="ml-2">
                      {previewChunks.length} chunks
                    </Badge>
                  )}
                </h3>
                
                {previewChunks.length > 0 ? (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {previewChunks.map((chunk, index) => (
                      <div key={index} className="p-3 border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium">Chunk {index + 1}</span>
                          <Badge variant="outline" className="text-xs">
                            {chunk.text.length} chars
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-3">
                          {chunk.text}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-64 text-muted-foreground">
                    <div className="text-center">
                      <Eye className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p>Enter text and click "Generate Preview" to see chunks</p>
                    </div>
                  </div>
                )}
              </Card>
            </div>
          </TabPanel>

          {/* Chunking Jobs Tab */}
          <TabPanel className="space-y-6">
            {/* Create New Job */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Create Chunking Job</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="job-name">Job Name</Label>
                  <Input
                    id="job-name"
                    placeholder="Enter job name..."
                    value={jobName}
                    onChange={(e) => setJobName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Strategy</Label>
                  <p className="text-sm text-muted-foreground">
                    {currentStrategy?.name} - {currentStrategy?.description}
                  </p>
                </div>
              </div>
              
              <div className="mt-4">
                <Button 
                  onClick={startChunkingJob}
                  disabled={!jobName.trim()}
                >
                  <Play className="h-4 w-4 mr-2" />
                  Start Chunking Job
                </Button>
              </div>
            </Card>

            {/* Job List */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Recent Jobs</h3>
              
              {chunkingJobs.length > 0 ? (
                <div className="space-y-4">
                  {chunkingJobs.map((job) => (
                    <div key={job.id} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          {job.status === 'completed' && <CheckCircle className="h-5 w-5 text-green-500" />}
                          {job.status === 'failed' && <AlertCircle className="h-5 w-5 text-red-500" />}
                          {job.status === 'running' && <RefreshCw className="h-5 w-5 text-blue-500 animate-spin" />}
                          {job.status === 'pending' && <FileText className="h-5 w-5 text-gray-500" />}
                          
                          <div>
                            <h4 className="font-medium">{job.name}</h4>
                            <p className="text-sm text-muted-foreground">
                              {job.strategy} • {job.inputFiles} files → {job.outputChunks} chunks
                            </p>
                          </div>
                        </div>
                        
                        <Badge variant={job.status === 'completed' ? 'default' : 'secondary'}>
                          {job.status}
                        </Badge>
                      </div>
                      
                      {job.status === 'running' && (
                        <Progress value={job.progress} className="h-2" />
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No chunking jobs yet</p>
                  <p className="text-sm">Create your first job to get started</p>
                </div>
              )}
            </Card>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </div>
  );
}
