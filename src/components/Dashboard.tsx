import { Card, Badge, Button, Progress } from './ui';
import { 
  BookOpen, 
  Download, 
  TrendingUp, 
  Clock,
  FileText,
  BarChart3,
  Plus,
  ArrowRight,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Activity
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useDashboardData } from '../hooks/useDashboardData';
import { formatDistanceToNow } from 'date-fns';

export function Dashboard() {
  const navigate = useNavigate();
  const { data, loading, error, refresh } = useDashboardData();

  const handleAddBook = () => {
    navigate('/library');
  };

  const formatMemoryUsage = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  const formatPercentage = (value: number, total: number) => {
    return total > 0 ? Math.round((value / total) * 100) : 0;
  };

  if (loading && !data) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Welcome back!</h1>
            <p className="text-muted-foreground mt-1">Loading your dashboard...</p>
          </div>
          <Button disabled>
            <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            Loading...
          </Button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="p-6 animate-pulse">
              <div className="h-20 bg-muted rounded"></div>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Welcome back!</h1>
            <p className="text-muted-foreground mt-1 text-red-600">
              Error loading dashboard: {error}
            </p>
          </div>
          <Button onClick={refresh} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Welcome Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Welcome back!</h1>
          <p className="text-muted-foreground mt-1">
            Here's what's happening with your lexicon today.
          </p>
          {data?.last_updated && (
            <p className="text-xs text-muted-foreground mt-1">
              Last updated {formatDistanceToNow(new Date(data.last_updated), { addSuffix: true })}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <Button onClick={refresh} variant="outline" size="sm">
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={handleAddBook}>
            <Plus className="h-4 w-4 mr-2" />
            Add New Book
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Books</p>
              <p className="text-3xl font-bold">{data?.stats.total_books || 0}</p>
              <p className="text-sm text-muted-foreground mt-1">
                {data?.stats.total_books === 0 ? 'Ready to start' : 'In your library'}
              </p>
            </div>
            <BookOpen className="h-8 w-8 text-primary" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Processing</p>
              <p className="text-3xl font-bold">{data?.stats.active_processing || 0}</p>
              <p className="text-sm text-muted-foreground mt-1">
                {data?.stats.active_processing === 0 ? 'No active tasks' : 'Active tasks'}
              </p>
            </div>
            <Download className="h-8 w-8 text-blue-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Chunks Created</p>
              <p className="text-3xl font-bold">{data?.stats.chunks_created || 0}</p>
              <p className="text-sm text-muted-foreground mt-1">
                {data?.stats.chunks_created === 0 ? 'Import content to begin' : 'Ready for RAG'}
              </p>
            </div>
            <FileText className="h-8 w-8 text-purple-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Quality Score</p>
              <p className="text-3xl font-bold">
                {data?.stats.quality_score !== null ? `${data.stats.quality_score}%` : '--'}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {data?.stats.quality_score !== null ? 'Processing success rate' : 'Awaiting data'}
              </p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-500" />
          </div>
        </Card>
      </div>

      {/* Recent Activity and Processing Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Recent Activity</h2>
            <Button variant="ghost" size="sm">
              View All
              <ArrowRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
          <div className="space-y-4">
            {data?.recent_activities && data.recent_activities.length > 0 ? (
              data.recent_activities.map((activity) => (
                <div key={activity.id} className="flex items-start space-x-3 p-3 rounded-lg border">
                  <div className="flex-shrink-0">
                    {activity.status === 'success' && <CheckCircle className="h-5 w-5 text-green-500" />}
                    {activity.status === 'warning' && <AlertCircle className="h-5 w-5 text-yellow-500" />}
                    {activity.status === 'error' && <AlertCircle className="h-5 w-5 text-red-500" />}
                    {!activity.status && <Activity className="h-5 w-5 text-blue-500" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground">{activity.title}</p>
                    <p className="text-sm text-muted-foreground">{activity.description}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <BookOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium mb-2">Welcome to Lexicon!</p>
                <p className="text-sm">Start by adding your first book or document to begin organizing your knowledge base.</p>
              </div>
            )}
          </div>
        </Card>

        {/* Processing Status */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Processing Status</h2>
            <Button variant="ghost" size="sm">
              <BarChart3 className="h-4 w-4 mr-1" />
              Details
            </Button>
          </div>
          <div className="space-y-4">
            {data?.processing_tasks && data.processing_tasks.length > 0 ? (
              data.processing_tasks.map((task) => (
                <div key={task.id} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium truncate">{task.title}</p>
                    <Badge variant={task.status === 'completed' ? 'default' : 'secondary'}>
                      {task.status === 'in_progress' ? 'Processing' : task.status}
                    </Badge>
                  </div>
                  <div className="space-y-1">
                    <Progress value={task.progress} className="h-2" />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>{task.current_step || 'Processing...'}</span>
                      <span>{task.progress}%</span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium mb-2">No Active Processing</p>
                <p className="text-sm">Upload documents to see processing status here.</p>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Performance Overview */}
      {data?.performance && (
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">System Performance</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-sm text-muted-foreground">CPU Usage</p>
              <p className="text-2xl font-bold">{data.performance.cpu_usage.toFixed(1)}%</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-muted-foreground">Memory Usage</p>
              <p className="text-2xl font-bold">
                {formatMemoryUsage(data.performance.memory_usage)} / {formatMemoryUsage(data.performance.memory_total)}
              </p>
              <p className="text-xs text-muted-foreground">
                {formatPercentage(data.performance.memory_usage, data.performance.memory_total)}%
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-muted-foreground">Active Tasks</p>
              <p className="text-2xl font-bold">{data.performance.active_tasks}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-muted-foreground">Completed Tasks</p>
              <p className="text-2xl font-bold">{data.performance.completed_tasks}</p>
            </div>
          </div>
        </Card>
      )}

      {/* Quick Actions */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Button variant="outline" className="h-16 flex-col" onClick={handleAddBook}>
            <Plus className="h-5 w-5 mb-1" />
            <span>Add Book</span>
          </Button>
          <Button variant="outline" className="h-16 flex-col" onClick={() => navigate('/batch')}>
            <Download className="h-5 w-5 mb-1" />
            <span>Batch Import</span>
          </Button>
          <Button variant="outline" className="h-16 flex-col" onClick={() => navigate('/performance')}>
            <BarChart3 className="h-5 w-5 mb-1" />
            <span>View Analytics</span>
          </Button>
        </div>
      </Card>
    </div>
  );
}
