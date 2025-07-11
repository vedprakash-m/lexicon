import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Tabs, TabList, Tab, TabPanels, TabPanel } from '../ui/tabs';
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Cpu,
  HardDrive,
  MemoryStick,
  Activity,
  Play,
  Square,
  RefreshCw,
  TrendingUp,
  AlertCircle,
} from 'lucide-react';
import { usePerformanceMonitor } from '../../hooks/usePerformanceMonitor';

interface PerformanceDashboardProps {
  className?: string;
}

export function PerformanceDashboard({ className }: PerformanceDashboardProps) {
  const {
    metrics,
    tasks,
    loading,
    error,
    submitTask,
    cancelTask,
    optimizeSystem,
    refreshAll,
    getActiveTasks,
  } = usePerformanceMonitor();

  const [newTaskType, setNewTaskType] = useState('web_scraping');
  const [newTaskConfig, setNewTaskConfig] = useState('{}');

  // Load initial data
  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  const handleStartTask = async () => {
    try {
      const config = JSON.parse(newTaskConfig);
      await submitTask({
        task_type: newTaskType,
        metadata: config,
        priority: 'normal'
      });
      setNewTaskConfig('{}');
    } catch (error) {
      console.error('Failed to start task:', error);
    }
  };

  const handleOptimizeSystem = async () => {
    await optimizeSystem({
      optimization_type: 'low_memory'
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Activity className="h-4 w-4 text-blue-500" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'cancelled':
        return <XCircle className="h-4 w-4 text-gray-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'running':
        return 'default';
      case 'completed':
        return 'secondary';
      case 'failed':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2" />
          <p className="text-muted-foreground">Loading performance data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
          <p className="text-red-600">Error: {error}</p>
          <Button onClick={refreshAll} className="mt-2">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const activeTasks = getActiveTasks();

  return (
    <div className={className}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Performance Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor system performance and manage background tasks
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            onClick={refreshAll}
            disabled={loading}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      <Tabs defaultIndex={0}>
        <TabList className="mb-6 flex space-x-1 rounded-lg bg-muted p-1">
          <Tab className="flex-1">Overview</Tab>
          <Tab className="flex-1">Background Tasks</Tab>
          <Tab className="flex-1">System Optimization</Tab>
        </TabList>

        <TabPanels>
          <TabPanel className="space-y-6">
            {/* System Metrics Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
                  <Cpu className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {metrics?.cpu_usage?.toFixed(1) || '0.0'}%
                  </div>
                  <Progress value={metrics?.cpu_usage || 0} className="mt-2" />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
                  <MemoryStick className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {metrics?.memory_usage?.toFixed(1) || '0.0'}%
                  </div>
                  <Progress value={metrics?.memory_usage || 0} className="mt-2" />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Disk Usage</CardTitle>
                  <HardDrive className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {metrics?.disk_usage?.toFixed(1) || '0.0'}%
                  </div>
                  <Progress value={metrics?.disk_usage || 0} className="mt-2" />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Active Tasks</CardTitle>
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {activeTasks.length}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    of {tasks.length} total
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>
                  Latest background tasks and system events
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {tasks.slice(0, 5).map((task) => (
                    <div key={task.id} className="flex items-center space-x-3">
                      {getStatusIcon(task.status)}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">
                          {task.task_type}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Started {new Date(Number(task.created_at) * 1000).toLocaleTimeString()}
                        </p>
                      </div>
                      <Badge variant={getStatusBadgeVariant(task.status)}>
                        {task.status}
                      </Badge>
                    </div>
                  ))}
                  {tasks.length === 0 && (
                    <p className="text-muted-foreground text-center py-4">
                      No recent activity
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabPanel>

          <TabPanel className="space-y-6">
            {/* Task Creation */}
            <Card>
              <CardHeader>
                <CardTitle>Create New Task</CardTitle>
                <CardDescription>
                  Start a new background task
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Task Type</label>
                    <select
                      value={newTaskType}
                      onChange={(e) => setNewTaskType(e.target.value)}
                      className="w-full p-2 border rounded-md"
                    >
                      <option value="web_scraping">Web Scraping</option>
                      <option value="text_processing">Text Processing</option>
                      <option value="chunk_generation">Content Chunking</option>
                      <option value="metadata_enrichment">Metadata Enrichment</option>
                      <option value="export">Data Export</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Configuration (JSON)</label>
                    <textarea
                      value={newTaskConfig}
                      onChange={(e) => setNewTaskConfig(e.target.value)}
                      placeholder='{"url": "example.com", "depth": 2}'
                      className="w-full p-2 border rounded-md h-20 resize-none text-sm font-mono"
                    />
                  </div>
                </div>
                <Button onClick={handleStartTask} className="w-full">
                  <Play className="h-4 w-4 mr-2" />
                  Start Task
                </Button>
              </CardContent>
            </Card>

            {/* Task List */}
            <Card>
              <CardHeader>
                <CardTitle>Background Tasks</CardTitle>
                <CardDescription>
                  Manage running and completed tasks
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {tasks.map((task) => (
                    <div key={task.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-3">
                          {getStatusIcon(task.status)}
                          <div>
                            <h4 className="font-medium">{task.task_type}</h4>
                            <p className="text-sm text-muted-foreground">
                              Task ID: {task.id}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge variant={getStatusBadgeVariant(task.status)}>
                            {task.status}
                          </Badge>
                          {task.status === 'running' && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => cancelTask(task.id)}
                            >
                              <Square className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                      
                      {task.progress !== undefined && (
                        <div className="space-y-1">
                          <div className="flex justify-between text-sm">
                            <span>Progress</span>
                            <span>{task.progress}%</span>
                          </div>
                          <Progress value={task.progress} />
                        </div>
                      )}
                      
                      <div className="mt-2 text-xs text-muted-foreground">
                        Created: {new Date(Number(task.created_at) * 1000).toLocaleString()}
                        {task.completed_at && (
                          <> • Completed: {new Date(Number(task.completed_at) * 1000).toLocaleString()}</>
                        )}
                      </div>
                    </div>
                  ))}
                  {tasks.length === 0 && (
                    <div className="text-center py-8">
                      <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                      <h3 className="font-medium mb-2">No Background Tasks</h3>
                      <p className="text-muted-foreground mb-4">
                        Create a new task to get started
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabPanel>

          <TabPanel className="space-y-6">
            {/* System Optimization */}
            <Card>
              <CardHeader>
                <CardTitle>System Optimization</CardTitle>
                <CardDescription>
                  Optimize system performance and resource usage
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Button
                    onClick={handleOptimizeSystem}
                    className="h-20 flex-col space-y-2"
                  >
                    <MemoryStick className="h-6 w-6" />
                    <span>Optimize Memory</span>
                  </Button>
                  <Button
                    variant="outline"
                    className="h-20 flex-col space-y-2"
                    onClick={() => optimizeSystem({
                      optimization_type: 'performance'
                    })}
                  >
                    <Cpu className="h-6 w-6" />
                    <span>Optimize Performance</span>
                  </Button>
                  <Button
                    variant="outline"
                    className="h-20 flex-col space-y-2"
                    onClick={() => optimizeSystem({
                      optimization_type: 'balanced'
                    })}
                  >
                    <HardDrive className="h-6 w-6" />
                    <span>Balanced Optimization</span>
                  </Button>
                  <Button
                    variant="outline"
                    className="h-20 flex-col space-y-2"
                    onClick={() => optimizeSystem({
                      optimization_type: 'performance'
                    })}
                  >
                    <TrendingUp className="h-6 w-6" />
                    <span>Aggressive Optimization</span>
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Performance Tips */}
            <Card>
              <CardHeader>
                <CardTitle>Performance Tips</CardTitle>
                <CardDescription>
                  Recommendations to improve system performance
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {metrics?.cpu_usage && metrics.cpu_usage > 80 && (
                    <div className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
                      <AlertTriangle className="h-5 w-5 text-yellow-500 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-yellow-800">High CPU Usage</h4>
                        <p className="text-sm text-yellow-700">
                          Consider reducing concurrent tasks or optimizing CPU-intensive operations.
                        </p>
                      </div>
                    </div>
                  )}
                  
                  {metrics?.memory_usage && metrics.memory_usage > 85 && (
                    <div className="flex items-start space-x-3 p-3 bg-red-50 rounded-lg">
                      <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-red-800">High Memory Usage</h4>
                        <p className="text-sm text-red-700">
                          Free up memory by closing unused applications or optimizing data structures.
                        </p>
                      </div>
                    </div>
                  )}
                  
                  {metrics?.disk_usage && metrics.disk_usage > 90 && (
                    <div className="flex items-start space-x-3 p-3 bg-red-50 rounded-lg">
                      <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-red-800">Low Disk Space</h4>
                        <p className="text-sm text-red-700">
                          Free up disk space by removing unnecessary files or archiving old data.
                        </p>
                      </div>
                    </div>
                  )}
                  
                  {(!metrics?.cpu_usage || metrics.cpu_usage < 80) &&
                   (!metrics?.memory_usage || metrics.memory_usage < 85) &&
                   (!metrics?.disk_usage || metrics.disk_usage < 90) && (
                    <div className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg">
                      <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-green-800">System Running Optimally</h4>
                        <p className="text-sm text-green-700">
                          Your system is performing well. Continue monitoring for optimal performance.
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </div>
  );
}
