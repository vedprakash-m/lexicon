import { useState, useEffect } from 'react';
import { Play, Pause, Square, RefreshCw, Clock, CheckCircle, AlertCircle, XCircle } from 'lucide-react';
import { Button, Card, Badge, Progress, Tabs, TabList, Tab, TabPanels, TabPanel } from '../ui';

interface ScrapingJob {
  id: string;
  name: string;
  sourceId: string;
  sourceName: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  startTime?: Date;
  endTime?: Date;
  progress: number;
  totalPages: number;
  processedPages: number;
  failedPages: number;
  errors: string[];
  estimatedTimeRemaining?: number;
  currentUrl?: string;
  rateLimit: number; // requests per second
}

interface JobHistory {
  id: string;
  jobId: string;
  timestamp: Date;
  event: 'started' | 'paused' | 'resumed' | 'completed' | 'failed' | 'cancelled';
  message: string;
  metadata?: Record<string, any>;
}

const mockJobs: ScrapingJob[] = [
  {
    id: '1',
    name: 'Bhagavad Gita Complete Scrape',
    sourceId: '1',
    sourceName: 'Bhagavad Gita Complete',
    status: 'running',
    startTime: new Date(Date.now() - 2 * 60 * 1000), // 2 minutes ago
    progress: 65,
    totalPages: 18,
    processedPages: 12,
    failedPages: 0,
    errors: [],
    estimatedTimeRemaining: 180, // 3 minutes
    currentUrl: 'https://vedabase.io/en/library/bg/13',
    rateLimit: 1
  },
  {
    id: '2',
    name: 'Srimad Bhagavatam Canto 1',
    sourceId: '2',
    sourceName: 'Srimad Bhagavatam Canto 1',
    status: 'pending',
    progress: 0,
    totalPages: 19,
    processedPages: 0,
    failedPages: 0,
    errors: [],
    rateLimit: 1
  },
  {
    id: '3',
    name: 'Philosophy Articles Collection',
    sourceId: '3',
    sourceName: 'Philosophy Blog',
    status: 'completed',
    startTime: new Date(Date.now() - 30 * 60 * 1000), // 30 minutes ago
    endTime: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
    progress: 100,
    totalPages: 25,
    processedPages: 24,
    failedPages: 1,
    errors: ['Failed to extract content from page: /article-23'],
    rateLimit: 0.5
  }
];

const mockHistory: JobHistory[] = [
  {
    id: '1',
    jobId: '1',
    timestamp: new Date(Date.now() - 2 * 60 * 1000),
    event: 'started',
    message: 'Job started with 18 pages to process'
  },
  {
    id: '2',
    jobId: '3',
    timestamp: new Date(Date.now() - 5 * 60 * 1000),
    event: 'completed',
    message: 'Job completed successfully with 1 failed page'
  },
  {
    id: '3',
    jobId: '3',
    timestamp: new Date(Date.now() - 30 * 60 * 1000),
    event: 'started',
    message: 'Job started with 25 pages to process'
  }
];

export function ScrapingExecution() {
  const [jobs, setJobs] = useState<ScrapingJob[]>(mockJobs);
  const [history, setHistory] = useState<JobHistory[]>(mockHistory);

  // Simulate real-time updates for running jobs
  useEffect(() => {
    const interval = setInterval(() => {
      setJobs(prevJobs => 
        prevJobs.map(job => {
          if (job.status === 'running' && job.progress < 100) {
            const newProgress = Math.min(100, job.progress + Math.random() * 5);
            const newProcessedPages = Math.floor((newProgress / 100) * job.totalPages);
            return {
              ...job,
              progress: newProgress,
              processedPages: newProcessedPages,
              estimatedTimeRemaining: Math.max(0, job.estimatedTimeRemaining! - 5)
            };
          }
          return job;
        })
      );
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: ScrapingJob['status']) => {
    switch (status) {
      case 'running': return <RefreshCw className="h-4 w-4 animate-spin text-blue-500" />;
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'paused': return <Pause className="h-4 w-4 text-yellow-500" />;
      case 'pending': return <Clock className="h-4 w-4 text-gray-500" />;
      case 'cancelled': return <Square className="h-4 w-4 text-gray-500" />;
      default: return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: ScrapingJob['status']) => {
    switch (status) {
      case 'running': return 'bg-blue-500';
      case 'completed': return 'bg-green-500';
      case 'failed': return 'bg-red-500';
      case 'paused': return 'bg-yellow-500';
      case 'pending': return 'bg-gray-500';
      case 'cancelled': return 'bg-gray-400';
      default: return 'bg-gray-500';
    }
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const handleJobAction = (jobId: string, action: 'start' | 'pause' | 'resume' | 'cancel') => {
    setJobs(prevJobs =>
      prevJobs.map(job => {
        if (job.id === jobId) {
          switch (action) {
            case 'start':
              return { ...job, status: 'running', startTime: new Date() };
            case 'pause':
              return { ...job, status: 'paused' };
            case 'resume':
              return { ...job, status: 'running' };
            case 'cancel':
              return { ...job, status: 'cancelled', endTime: new Date() };
            default:
              return job;
          }
        }
        return job;
      })
    );

    // Add to history
    const newHistoryEntry: JobHistory = {
      id: Date.now().toString(),
      jobId,
      timestamp: new Date(),
      event: action === 'resume' ? 'resumed' : action as any,
      message: `Job ${action}${action === 'start' ? 'ed' : action === 'pause' ? 'd' : action === 'resume' ? 'd' : 'led'}`
    };
    setHistory(prev => [newHistoryEntry, ...prev]);
  };

  const runningJobs = jobs.filter(job => job.status === 'running');
  const pendingJobs = jobs.filter(job => job.status === 'pending');
  const completedJobs = jobs.filter(job => ['completed', 'failed', 'cancelled'].includes(job.status));

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Scraping Execution</h1>
          <p className="text-muted-foreground mt-1">
            Monitor and manage your scraping jobs
          </p>
        </div>
        
        <div className="flex space-x-2">
          <Button variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button>
            <Play className="h-4 w-4 mr-2" />
            New Job
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Running</p>
              <p className="text-2xl font-bold">{runningJobs.length}</p>
            </div>
            <RefreshCw className="h-8 w-8 text-blue-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Pending</p>
              <p className="text-2xl font-bold">{pendingJobs.length}</p>
            </div>
            <Clock className="h-8 w-8 text-gray-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Completed</p>
              <p className="text-2xl font-bold">
                {jobs.filter(j => j.status === 'completed').length}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Pages</p>
              <p className="text-2xl font-bold">
                {jobs.reduce((sum, job) => sum + job.processedPages, 0)}
              </p>
            </div>
            <div className="text-xs text-muted-foreground">
              {jobs.reduce((sum, job) => sum + job.totalPages, 0)} total
            </div>
          </div>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultIndex={0} className="space-y-4">
        <TabList>
          <Tab>Active Jobs ({runningJobs.length + pendingJobs.length})</Tab>
          <Tab>Completed ({completedJobs.length})</Tab>
          <Tab>History</Tab>
        </TabList>

        <TabPanels>
          {/* Active Jobs Tab */}
          <TabPanel className="space-y-4">{[...runningJobs, ...pendingJobs].map((job) => (
            <Card key={job.id} className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(job.status)}
                  <div>
                    <h3 className="font-semibold">{job.name}</h3>
                    <p className="text-sm text-muted-foreground">{job.sourceName}</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Badge variant={job.status === 'running' ? 'default' : 'secondary'}>
                    {job.status}
                  </Badge>
                  
                  {job.status === 'pending' && (
                    <Button 
                      size="sm" 
                      onClick={() => handleJobAction(job.id, 'start')}
                    >
                      <Play className="h-3 w-3 mr-1" />
                      Start
                    </Button>
                  )}
                  
                  {job.status === 'running' && (
                    <>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => handleJobAction(job.id, 'pause')}
                      >
                        <Pause className="h-3 w-3 mr-1" />
                        Pause
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => handleJobAction(job.id, 'cancel')}
                      >
                        <Square className="h-3 w-3 mr-1" />
                        Cancel
                      </Button>
                    </>
                  )}
                  
                  {job.status === 'paused' && (
                    <Button 
                      size="sm"
                      onClick={() => handleJobAction(job.id, 'resume')}
                    >
                      <Play className="h-3 w-3 mr-1" />
                      Resume
                    </Button>
                  )}
                </div>
              </div>

              {/* Progress */}
              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span>Progress: {job.processedPages}/{job.totalPages} pages</span>
                  <span>{Math.round(job.progress)}%</span>
                </div>
                <Progress value={job.progress} className="h-2" />
              </div>

              {/* Details */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Rate Limit:</span>
                  <div>{job.rateLimit} req/sec</div>
                </div>
                <div>
                  <span className="text-muted-foreground">Failed Pages:</span>
                  <div className={job.failedPages > 0 ? 'text-red-600' : ''}>
                    {job.failedPages}
                  </div>
                </div>
                {job.estimatedTimeRemaining && (
                  <div>
                    <span className="text-muted-foreground">ETA:</span>
                    <div>{formatDuration(job.estimatedTimeRemaining)}</div>
                  </div>
                )}
                {job.startTime && (
                  <div>
                    <span className="text-muted-foreground">Started:</span>
                    <div>{job.startTime.toLocaleTimeString()}</div>
                  </div>
                )}
              </div>

              {/* Current URL for running jobs */}
              {job.status === 'running' && job.currentUrl && (
                <div className="mt-4 p-3 bg-muted rounded">
                  <div className="text-xs text-muted-foreground mb-1">Currently processing:</div>
                  <code className="text-xs">{job.currentUrl}</code>
                </div>
              )}

              {/* Errors */}
              {job.errors.length > 0 && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
                  <div className="text-sm font-medium text-red-800 mb-2">
                    <AlertCircle className="h-4 w-4 inline mr-1" />
                    Errors ({job.errors.length})
                  </div>
                  <div className="space-y-1">
                    {job.errors.slice(0, 3).map((error, idx) => (
                      <div key={idx} className="text-xs text-red-700">{error}</div>
                    ))}
                    {job.errors.length > 3 && (
                      <div className="text-xs text-red-600">
                        ...and {job.errors.length - 3} more errors
                      </div>
                    )}
                  </div>
                </div>
              )}
            </Card>
          ))}

          {[...runningJobs, ...pendingJobs].length === 0 && (
            <Card className="p-12 text-center">
              <Clock className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Active Jobs</h3>
              <p className="text-muted-foreground mb-6">
                Start a new scraping job to see it here.
              </p>
              <Button>
                <Play className="h-4 w-4 mr-2" />
                Start New Job
              </Button>
            </Card>
          )}
          </TabPanel>

          {/* Completed Jobs Tab */}
          <TabPanel className="space-y-4">{completedJobs.map((job) => (
            <Card key={job.id} className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(job.status)}
                  <div>
                    <h3 className="font-semibold">{job.name}</h3>
                    <p className="text-sm text-muted-foreground">{job.sourceName}</p>
                  </div>
                </div>
                
                <Badge 
                  variant={job.status === 'completed' ? 'default' : 'destructive'}
                  className={job.status === 'completed' ? 'bg-green-500' : ''}
                >
                  {job.status}
                </Badge>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Processed:</span>
                  <div>{job.processedPages}/{job.totalPages} pages</div>
                </div>
                <div>
                  <span className="text-muted-foreground">Failed:</span>
                  <div className={job.failedPages > 0 ? 'text-red-600' : ''}>
                    {job.failedPages} pages
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground">Duration:</span>
                  <div>
                    {job.startTime && job.endTime && 
                      formatDuration((job.endTime.getTime() - job.startTime.getTime()) / 1000)
                    }
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground">Completed:</span>
                  <div>{job.endTime?.toLocaleString()}</div>
                </div>
              </div>

              {job.errors.length > 0 && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
                  <div className="text-sm font-medium text-red-800 mb-2">
                    <AlertCircle className="h-4 w-4 inline mr-1" />
                    {job.errors.length} Error{job.errors.length > 1 ? 's' : ''}
                  </div>
                  <Button variant="outline" size="sm">
                    View Details
                  </Button>
                </div>
              )}
            </Card>
          ))}
          </TabPanel>

          {/* History Tab */}
          <TabPanel className="space-y-4"><Card className="p-6">
            <h3 className="font-semibold mb-4">Job History</h3>
            <div className="space-y-3">
              {history.map((entry) => {
                const job = jobs.find(j => j.id === entry.jobId);
                return (
                  <div key={entry.id} className="flex items-center space-x-3 py-2 border-b last:border-b-0">
                    <div className={`w-2 h-2 rounded-full ${getStatusColor(entry.event as any)}`} />
                    <div className="flex-1">
                      <div className="text-sm font-medium">
                        {job?.name || `Job ${entry.jobId}`}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {entry.message}
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {entry.timestamp.toLocaleString()}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </div>
  );
}
