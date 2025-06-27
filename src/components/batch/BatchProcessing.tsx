import { useState, useEffect } from 'react';
import { 
  Play, 
  Pause, 
  Square, 
  Settings, 
  Clock, 
  Cpu, 
  HardDrive, 
  Activity,
  CheckCircle,
  AlertCircle,
  Users,
  Zap
} from 'lucide-react';
import { 
  Button, 
  Card, 
  Badge, 
  Progress, 
  Tabs, 
  TabList, 
  Tab, 
  TabPanels, 
  TabPanel,
  Dialog
} from '../ui';

interface BatchJob {
  id: string;
  name: string;
  description: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  status: 'pending' | 'queued' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  sourceCount: number;
  completedSources: number;
  totalPages: number;
  processedPages: number;
  startTime?: Date;
  endTime?: Date;
  estimatedDuration?: number; // minutes
  parallelSources: boolean;
  parallelPages: boolean;
}

interface ResourceUsage {
  cpuPercent: number;
  memoryPercent: number;
  memoryMb: number;
  activeProcesses: number;
}

interface SystemStatus {
  processorRunning: boolean;
  resourceUsage: ResourceUsage;
  resourceLimits: {
    maxCpuCores: number;
    maxMemoryMb: number;
    maxConcurrentJobs: number;
  };
  queueStatus: {
    queuedJobs: number;
    activeJobs: number;
    completedJobs: number;
  };
  shouldThrottle: boolean;
}

// Mock data for development
const mockJobs: BatchJob[] = [
  {
    id: '1',
    name: 'Complete Vedabase Collection',
    description: 'Process all Vedabase.io texts including Bhagavad Gita, Srimad Bhagavatam, and Upanishads',
    priority: 'high',
    status: 'running',
    sourceCount: 12,
    completedSources: 8,
    totalPages: 2847,
    processedPages: 1923,
    startTime: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
    parallelSources: true,
    parallelPages: false,
    estimatedDuration: 45
  },
  {
    id: '2',
    name: 'Philosophy Collection Batch',
    description: 'Process modern philosophy texts from various sources',
    priority: 'normal',
    status: 'queued',
    sourceCount: 6,
    completedSources: 0,
    totalPages: 1450,
    processedPages: 0,
    parallelSources: false,
    parallelPages: true,
    estimatedDuration: 120
  },
  {
    id: '3',
    name: 'Classical Literature Archive',
    description: 'Historical and classical literature processing',
    priority: 'low',
    status: 'completed',
    sourceCount: 8,
    completedSources: 8,
    totalPages: 1200,
    processedPages: 1200,
    startTime: new Date(Date.now() - 4 * 60 * 60 * 1000),
    endTime: new Date(Date.now() - 1 * 60 * 60 * 1000),
    parallelSources: true,
    parallelPages: true
  }
];

const mockSystemStatus: SystemStatus = {
  processorRunning: true,
  resourceUsage: {
    cpuPercent: 68.5,
    memoryPercent: 72.3,
    memoryMb: 5832,
    activeProcesses: 847
  },
  resourceLimits: {
    maxCpuCores: 8,
    maxMemoryMb: 8192,
    maxConcurrentJobs: 4
  },
  queueStatus: {
    queuedJobs: 3,
    activeJobs: 1,
    completedJobs: 12
  },
  shouldThrottle: false
};

export function BatchProcessing() {
  const [jobs, setJobs] = useState<BatchJob[]>(mockJobs);
  const [systemStatus, setSystemStatus] = useState<SystemStatus>(mockSystemStatus);
  const [showJobDialog, setShowJobDialog] = useState(false);
  const [selectedTab, setSelectedTab] = useState(0);

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setJobs(currentJobs => 
        currentJobs.map(job => {
          if (job.status === 'running') {
            const progress = Math.min(job.processedPages + Math.floor(Math.random() * 10), job.totalPages);
            const sourceProgress = Math.min(
              job.completedSources + (progress === job.totalPages ? 1 : 0), 
              job.sourceCount
            );
            return {
              ...job,
              processedPages: progress,
              completedSources: sourceProgress,
              status: progress === job.totalPages ? 'completed' : 'running'
            };
          }
          return job;
        })
      );

      // Update system status
      setSystemStatus(current => ({
        ...current,
        resourceUsage: {
          ...current.resourceUsage,
          cpuPercent: Math.max(30, Math.min(90, current.resourceUsage.cpuPercent + (Math.random() - 0.5) * 10)),
          memoryPercent: Math.max(40, Math.min(85, current.resourceUsage.memoryPercent + (Math.random() - 0.5) * 5))
        }
      }));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'normal': return 'bg-blue-500';
      case 'low': return 'bg-gray-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <Activity className="h-4 w-4 text-blue-500 animate-pulse" />;
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed': return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'paused': return <Pause className="h-4 w-4 text-yellow-500" />;
      case 'queued': return <Clock className="h-4 w-4 text-gray-500" />;
      default: return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const activeJobs = jobs.filter(job => ['running', 'queued', 'pending'].includes(job.status));
  const completedJobs = jobs.filter(job => ['completed', 'failed', 'cancelled'].includes(job.status));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Batch Processing</h1>
          <p className="text-muted-foreground">
            Manage and monitor large-scale processing operations
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4 mr-2" />
            Configure
          </Button>
          <Button onClick={() => setShowJobDialog(true)}>
            <Play className="h-4 w-4 mr-2" />
            New Batch Job
          </Button>
        </div>
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">CPU Usage</p>
              <p className="text-2xl font-bold">{systemStatus.resourceUsage.cpuPercent.toFixed(1)}%</p>
            </div>
            <Cpu className={`h-8 w-8 ${systemStatus.resourceUsage.cpuPercent > 80 ? 'text-red-500' : 'text-blue-500'}`} />
          </div>
          <Progress 
            value={systemStatus.resourceUsage.cpuPercent} 
            className="mt-2"
          />
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Memory Usage</p>
              <p className="text-2xl font-bold">{systemStatus.resourceUsage.memoryPercent.toFixed(1)}%</p>
            </div>
            <HardDrive className={`h-8 w-8 ${systemStatus.resourceUsage.memoryPercent > 80 ? 'text-red-500' : 'text-green-500'}`} />
          </div>
          <Progress 
            value={systemStatus.resourceUsage.memoryPercent} 
            className="mt-2"
          />
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Active Jobs</p>
              <p className="text-2xl font-bold">{systemStatus.queueStatus.activeJobs}</p>
            </div>
            <Users className="h-8 w-8 text-purple-500" />
          </div>
          <div className="text-xs text-muted-foreground mt-2">
            {systemStatus.queueStatus.queuedJobs} queued
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">System Status</p>
              <p className="text-lg font-semibold text-green-600">
                {systemStatus.processorRunning ? 'Running' : 'Stopped'}
              </p>
            </div>
            <Zap className={`h-8 w-8 ${systemStatus.processorRunning ? 'text-green-500' : 'text-red-500'}`} />
          </div>
          {systemStatus.shouldThrottle && (
            <Badge variant="destructive" className="mt-2 text-xs">
              Throttled
            </Badge>
          )}
        </Card>
      </div>

      {/* Job Management Tabs */}
      <Tabs defaultIndex={selectedTab} onChange={setSelectedTab} className="space-y-4">
        <TabList>
          <Tab>Active Jobs ({activeJobs.length})</Tab>
          <Tab>Completed ({completedJobs.length})</Tab>
          <Tab>Queue Management</Tab>
          <Tab>Resource Settings</Tab>
        </TabList>

        <TabPanels>
          {/* Active Jobs Tab */}
          <TabPanel className="space-y-4">
            {activeJobs.length === 0 ? (
              <Card className="p-8 text-center">
                <Clock className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Active Jobs</h3>
                <p className="text-muted-foreground mb-4">
                  Start a new batch job to see it here.
                </p>
                <Button onClick={() => setShowJobDialog(true)}>
                  <Play className="h-4 w-4 mr-2" />
                  Create Batch Job
                </Button>
              </Card>
            ) : (
              activeJobs.map((job) => (
                <Card key={job.id} className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(job.status)}
                      <div>
                        <h3 className="font-semibold">{job.name}</h3>
                        <p className="text-sm text-muted-foreground">{job.description}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Badge 
                        variant="secondary" 
                        className={`${getPriorityColor(job.priority)} text-white`}
                      >
                        {job.priority}
                      </Badge>
                      <Badge variant={job.status === 'running' ? 'default' : 'secondary'}>
                        {job.status}
                      </Badge>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <p className="text-sm font-medium mb-1">Sources Progress</p>
                      <Progress 
                        value={(job.completedSources / job.sourceCount) * 100} 
                        className="mb-1"
                      />
                      <p className="text-xs text-muted-foreground">
                        {job.completedSources} of {job.sourceCount} sources
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium mb-1">Pages Progress</p>
                      <Progress 
                        value={(job.processedPages / job.totalPages) * 100} 
                        className="mb-1"
                      />
                      <p className="text-xs text-muted-foreground">
                        {job.processedPages.toLocaleString()} of {job.totalPages.toLocaleString()} pages
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                      {job.startTime && (
                        <span>Started: {job.startTime.toLocaleTimeString()}</span>
                      )}
                      {job.estimatedDuration && job.status === 'running' && (
                        <span>ETA: {job.estimatedDuration} min remaining</span>
                      )}
                      <span>
                        {job.parallelSources ? 'Parallel sources' : 'Sequential sources'}
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {job.status === 'running' && (
                        <Button variant="outline" size="sm">
                          <Pause className="h-4 w-4 mr-2" />
                          Pause
                        </Button>
                      )}
                      {job.status === 'paused' && (
                        <Button variant="outline" size="sm">
                          <Play className="h-4 w-4 mr-2" />
                          Resume
                        </Button>
                      )}
                      <Button variant="outline" size="sm">
                        <Square className="h-4 w-4 mr-2" />
                        Stop
                      </Button>
                    </div>
                  </div>
                </Card>
              ))
            )}
          </TabPanel>

          {/* Completed Jobs Tab */}
          <TabPanel className="space-y-4">
            {completedJobs.map((job) => (
              <Card key={job.id} className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(job.status)}
                    <div>
                      <h3 className="font-semibold">{job.name}</h3>
                      <p className="text-sm text-muted-foreground">{job.description}</p>
                    </div>
                  </div>
                  
                  <Badge variant={job.status === 'completed' ? 'default' : 'destructive'}>
                    {job.status}
                  </Badge>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm font-medium">Success Rate</p>
                    <p className="text-2xl font-bold text-green-600">
                      {((job.processedPages / job.totalPages) * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Duration</p>
                    <p className="text-lg">
                      {job.startTime && job.endTime ? 
                        `${Math.round((job.endTime.getTime() - job.startTime.getTime()) / (1000 * 60))} min` :
                        'N/A'
                      }
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Pages Processed</p>
                    <p className="text-lg">{job.processedPages.toLocaleString()}</p>
                  </div>
                </div>
              </Card>
            ))}
          </TabPanel>

          {/* Queue Management Tab */}
          <TabPanel className="space-y-4">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Queue Configuration</h3>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-2">Processing Limits</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Max Concurrent Jobs:</span>
                      <span className="font-medium">{systemStatus.resourceLimits.maxConcurrentJobs}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Max CPU Cores:</span>
                      <span className="font-medium">{systemStatus.resourceLimits.maxCpuCores}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Max Memory:</span>
                      <span className="font-medium">{systemStatus.resourceLimits.maxMemoryMb} MB</span>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Current Queue</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Queued Jobs:</span>
                      <span className="font-medium">{systemStatus.queueStatus.queuedJobs}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Active Jobs:</span>
                      <span className="font-medium">{systemStatus.queueStatus.activeJobs}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Completed Jobs:</span>
                      <span className="font-medium">{systemStatus.queueStatus.completedJobs}</span>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </TabPanel>

          {/* Resource Settings Tab */}
          <TabPanel className="space-y-4">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Resource Management</h3>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">CPU Usage</h4>
                  <Progress value={systemStatus.resourceUsage.cpuPercent} className="mb-1" />
                  <p className="text-sm text-muted-foreground">
                    {systemStatus.resourceUsage.cpuPercent.toFixed(1)}% of {systemStatus.resourceLimits.maxCpuCores} cores
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Memory Usage</h4>
                  <Progress value={systemStatus.resourceUsage.memoryPercent} className="mb-1" />
                  <p className="text-sm text-muted-foreground">
                    {systemStatus.resourceUsage.memoryMb.toFixed(0)} MB of {systemStatus.resourceLimits.maxMemoryMb} MB
                  </p>
                </div>
                <div className="pt-4">
                  <Button variant="outline">
                    <Settings className="h-4 w-4 mr-2" />
                    Configure Resource Limits
                  </Button>
                </div>
              </div>
            </Card>
          </TabPanel>
        </TabPanels>
      </Tabs>

      {/* New Job Dialog (placeholder) */}
      <Dialog open={showJobDialog} onClose={() => setShowJobDialog(false)}>
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">Create New Batch Job</h2>
          <p className="text-muted-foreground mb-6">
            Batch job creation wizard will be implemented in the next iteration.
          </p>
          <div className="flex justify-end space-x-3">
            <Button variant="outline" onClick={() => setShowJobDialog(false)}>
              Cancel
            </Button>
            <Button onClick={() => setShowJobDialog(false)}>
              Create Job
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
