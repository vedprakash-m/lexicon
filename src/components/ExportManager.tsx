import React, { useState, useEffect } from 'react';
import { FileText, Database, Settings, Play, Check, X, AlertCircle, Loader } from 'lucide-react';

interface ExportConfig {
  format: string;
  outputPath: string;
  compression: string;
  includeMetadata: boolean;
  flattenNested: boolean;
  customFields?: string[];
  excludeFields?: string[];
}

interface ExportJob {
  id: string;
  config: ExportConfig;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  recordsExported: number;
  fileSizeBytes: number;
  exportTimeSeconds: number;
  errors?: string[];
  startTime: Date;
  endTime?: Date;
}

interface ExportManagerProps {
  chunks: any[];
  onExportComplete?: (result: any) => void;
}

const EXPORT_FORMATS = [
  { value: 'jsonl', label: 'JSON Lines (.jsonl)', description: 'Line-delimited JSON for streaming' },
  { value: 'json', label: 'JSON (.json)', description: 'Standard JSON array format' },
  { value: 'csv', label: 'CSV (.csv)', description: 'Comma-separated values' },
  { value: 'tsv', label: 'TSV (.tsv)', description: 'Tab-separated values' },
  { value: 'parquet', label: 'Parquet (.parquet)', description: 'Columnar storage format' },
  { value: 'xml', label: 'XML (.xml)', description: 'Extensible markup language' },
  { value: 'markdown', label: 'Markdown (.md)', description: 'Markdown format' },
  { value: 'custom', label: 'Custom Format', description: 'User-defined template' }
];

const COMPRESSION_TYPES = [
  { value: 'none', label: 'No Compression' },
  { value: 'gzip', label: 'GZIP' },
  { value: 'zip', label: 'ZIP' },
  { value: 'bzip2', label: 'BZIP2' },
  { value: 'xz', label: 'XZ' }
];

export const ExportManager: React.FC<ExportManagerProps> = ({ chunks, onExportComplete }) => {
  const [activeTab, setActiveTab] = useState<'single' | 'batch' | 'history'>('single');
  const [exportConfigs, setExportConfigs] = useState<ExportConfig[]>([{
    format: 'jsonl',
    outputPath: '',
    compression: 'none',
    includeMetadata: true,
    flattenNested: false
  }]);
  const [exportJobs, setExportJobs] = useState<ExportJob[]>([]);
  const [customTemplate, setCustomTemplate] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Mock data for demonstration
  useEffect(() => {
    setExportJobs([
      {
        id: 'job_001',
        config: {
          format: 'jsonl',
          outputPath: '/Users/Documents/Lexicon/exports/bhagavad_gita.jsonl',
          compression: 'gzip',
          includeMetadata: true,
          flattenNested: false
        },
        status: 'completed',
        progress: 100,
        recordsExported: 324,
        fileSizeBytes: 125400,
        exportTimeSeconds: 2.3,
        startTime: new Date(Date.now() - 300000),
        endTime: new Date(Date.now() - 295000)
      },
      {
        id: 'job_002',
        config: {
          format: 'csv',
          outputPath: '/Users/Documents/Lexicon/exports/bhagavad_gita.csv',
          compression: 'none',
          includeMetadata: true,
          flattenNested: true
        },
        status: 'running',
        progress: 67,
        recordsExported: 217,
        fileSizeBytes: 45200,
        exportTimeSeconds: 1.8,
        startTime: new Date(Date.now() - 120000)
      },
      {
        id: 'job_003',
        config: {
          format: 'parquet',
          outputPath: '/Users/Documents/Lexicon/exports/bhagavad_gita.parquet',
          compression: 'none',
          includeMetadata: true,
          flattenNested: true
        },
        status: 'failed',
        progress: 45,
        recordsExported: 0,
        fileSizeBytes: 0,
        exportTimeSeconds: 0.8,
        errors: ['PyArrow dependency not found. Please install: pip install pyarrow'],
        startTime: new Date(Date.now() - 600000),
        endTime: new Date(Date.now() - 595000)
      }
    ]);
  }, []);

  const updateExportConfig = (index: number, updates: Partial<ExportConfig>) => {
    setExportConfigs(configs => 
      configs.map((config, i) => i === index ? { ...config, ...updates } : config)
    );
  };

  const addExportConfig = () => {
    setExportConfigs(configs => [...configs, {
      format: 'jsonl',
      outputPath: '',
      compression: 'none',
      includeMetadata: true,
      flattenNested: false
    }]);
  };

  const removeExportConfig = (index: number) => {
    if (exportConfigs.length > 1) {
      setExportConfigs(configs => configs.filter((_, i) => i !== index));
    }
  };

  const startExport = async (configIndex?: number) => {
    const configs = configIndex !== undefined ? [exportConfigs[configIndex]] : exportConfigs;
    
    for (const config of configs) {
      const job: ExportJob = {
        id: `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        config,
        status: 'pending',
        progress: 0,
        recordsExported: 0,
        fileSizeBytes: 0,
        exportTimeSeconds: 0,
        startTime: new Date()
      };
      
      setExportJobs(jobs => [job, ...jobs]);
      
      // Simulate export process
      simulateExport(job);
    }
  };

  const simulateExport = async (job: ExportJob) => {
    // Update to running
    setExportJobs(jobs => 
      jobs.map(j => j.id === job.id ? { ...j, status: 'running' as const } : j)
    );

    // Simulate progress
    for (let progress = 0; progress <= 100; progress += 10) {
      await new Promise(resolve => setTimeout(resolve, 200));
      
      setExportJobs(jobs => 
        jobs.map(j => j.id === job.id ? { 
          ...j, 
          progress,
          recordsExported: Math.floor((chunks.length * progress) / 100),
          exportTimeSeconds: (Date.now() - j.startTime.getTime()) / 1000
        } : j)
      );
    }

    // Complete the job
    setExportJobs(jobs => 
      jobs.map(j => j.id === job.id ? { 
        ...j, 
        status: 'completed' as const,
        progress: 100,
        recordsExported: chunks.length,
        fileSizeBytes: Math.floor(Math.random() * 100000) + 50000,
        endTime: new Date()
      } : j)
    );

    onExportComplete?.({ success: true, format: job.config.format });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  };

  const getStatusIcon = (status: ExportJob['status']) => {
    switch (status) {
      case 'pending':
        return <Loader className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'running':
        return <Loader className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'completed':
        return <Check className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <X className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  const SingleExportTab = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Export Configuration</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Export Format
            </label>
            <select
              value={exportConfigs[0].format}
              onChange={(e) => updateExportConfig(0, { format: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {EXPORT_FORMATS.map(format => (
                <option key={format.value} value={format.value}>
                  {format.label}
                </option>
              ))}
            </select>
            <p className="text-sm text-gray-500 mt-1">
              {EXPORT_FORMATS.find(f => f.value === exportConfigs[0].format)?.description}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Output Path
            </label>
            <input
              type="text"
              value={exportConfigs[0].outputPath}
              onChange={(e) => updateExportConfig(0, { outputPath: e.target.value })}
              placeholder="/path/to/output/file"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Compression
            </label>
            <select
              value={exportConfigs[0].compression}
              onChange={(e) => updateExportConfig(0, { compression: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {COMPRESSION_TYPES.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col space-y-3">
            <label className="block text-sm font-medium text-gray-700">
              Options
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={exportConfigs[0].includeMetadata}
                onChange={(e) => updateExportConfig(0, { includeMetadata: e.target.checked })}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">Include metadata</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={exportConfigs[0].flattenNested}
                onChange={(e) => updateExportConfig(0, { flattenNested: e.target.checked })}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">Flatten nested fields</span>
            </label>
          </div>
        </div>

        {exportConfigs[0].format === 'custom' && (
          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Custom Template
            </label>
            <textarea
              value={customTemplate}
              onChange={(e) => setCustomTemplate(e.target.value)}
              placeholder="ID: {id} | Text: {text} | Chapter: {metadata.chapter}"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-sm text-gray-500 mt-1">
              Use {"{field_name}"} to reference chunk fields
            </p>
          </div>
        )}

        <div className="mt-6 flex items-center justify-between">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            {showAdvanced ? 'Hide' : 'Show'} Advanced Options
          </button>
          
          <button
            onClick={() => startExport(0)}
            disabled={!exportConfigs[0].outputPath}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play className="w-4 h-4" />
            <span>Start Export</span>
          </button>
        </div>

        {showAdvanced && (
          <div className="mt-6 p-4 bg-gray-50 rounded-md">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Advanced Options</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Include Only Fields (comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="id,text,metadata"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Exclude Fields (comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="internal_id,debug_info"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <FileText className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-blue-900">Export Preview</h4>
            <p className="text-sm text-blue-700 mt-1">
              Ready to export {chunks.length} chunks in {exportConfigs[0].format.toUpperCase()} format
              {exportConfigs[0].compression !== 'none' && ` with ${exportConfigs[0].compression.toUpperCase()} compression`}
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  const BatchExportTab = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Batch Export Configurations</h3>
          <button
            onClick={addExportConfig}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Add Format
          </button>
        </div>

        <div className="space-y-4">
          {exportConfigs.map((config, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-medium text-gray-900">Export #{index + 1}</h4>
                {exportConfigs.length > 1 && (
                  <button
                    onClick={() => removeExportConfig(index)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Format</label>
                  <select
                    value={config.format}
                    onChange={(e) => updateExportConfig(index, { format: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {EXPORT_FORMATS.map(format => (
                      <option key={format.value} value={format.value}>
                        {format.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Compression</label>
                  <select
                    value={config.compression}
                    onChange={(e) => updateExportConfig(index, { compression: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {COMPRESSION_TYPES.map(type => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Output Path</label>
                  <input
                    type="text"
                    value={config.outputPath}
                    onChange={(e) => updateExportConfig(index, { outputPath: e.target.value })}
                    placeholder="/path/to/output"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={() => startExport()}
            disabled={exportConfigs.some(config => !config.outputPath)}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play className="w-4 h-4" />
            <span>Start Batch Export</span>
          </button>
        </div>
      </div>
    </div>
  );

  const HistoryTab = () => (
    <div className="space-y-4">
      {exportJobs.map((job) => (
        <div key={job.id} className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              {getStatusIcon(job.status)}
              <div>
                <h3 className="text-sm font-medium text-gray-900">
                  {job.config.format.toUpperCase()} Export
                </h3>
                <p className="text-sm text-gray-500">
                  {job.startTime.toLocaleString()}
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm font-medium text-gray-900">
                {job.status === 'running' ? `${job.progress}%` : job.status}
              </div>
              {job.endTime && (
                <div className="text-sm text-gray-500">
                  {formatDuration(job.exportTimeSeconds)}
                </div>
              )}
            </div>
          </div>

          {job.status === 'running' && (
            <div className="mb-4">
              <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                <span>Progress</span>
                <span>{job.recordsExported} / {chunks.length} records</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${job.progress}%` }}
                />
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Output:</span>
              <p className="font-medium text-gray-900 truncate" title={job.config.outputPath}>
                {job.config.outputPath.split('/').pop() || job.config.outputPath}
              </p>
            </div>
            <div>
              <span className="text-gray-500">Records:</span>
              <p className="font-medium text-gray-900">{job.recordsExported.toLocaleString()}</p>
            </div>
            <div>
              <span className="text-gray-500">Size:</span>
              <p className="font-medium text-gray-900">{formatFileSize(job.fileSizeBytes)}</p>
            </div>
            <div>
              <span className="text-gray-500">Compression:</span>
              <p className="font-medium text-gray-900">{job.config.compression}</p>
            </div>
          </div>

          {job.errors && job.errors.length > 0 && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <div className="flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-red-600 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-red-900">Export Failed</h4>
                  <ul className="text-sm text-red-700 mt-1 space-y-1">
                    {job.errors.map((error, index) => (
                      <li key={index}>• {error}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      ))}

      {exportJobs.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <Database className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p>No export history yet</p>
          <p className="text-sm">Start an export to see it here</p>
        </div>
      )}
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Export Manager</h1>
        <p className="text-gray-600 mt-1">
          Export your processed chunks to various formats for use with RAG systems and other applications
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'single', label: 'Single Export', icon: FileText },
            { id: 'batch', label: 'Batch Export', icon: Database },
            { id: 'history', label: 'Export History', icon: Settings }
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id as any)}
              className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'single' && <SingleExportTab />}
      {activeTab === 'batch' && <BatchExportTab />}
      {activeTab === 'history' && <HistoryTab />}
    </div>
  );
};

export default ExportManager;
