import { Card, Badge, Button, Progress } from './ui';
import { 
  BookOpen, 
  Download, 
  TrendingUp, 
  Clock,
  FileText,
  BarChart3,
  Plus,
  ArrowRight
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function Dashboard() {
  const navigate = useNavigate();

  const handleAddBook = () => {
    navigate('/library');
  };

  return (
    <div className="p-6 space-y-6">
      {/* Welcome Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Welcome back!</h1>
          <p className="text-muted-foreground mt-1">
            Here's what's happening with your lexicon today.
          </p>
        </div>
        <Button onClick={handleAddBook}>
          <Plus className="h-4 w-4 mr-2" />
          Add New Book
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Books</p>
              <p className="text-3xl font-bold">0</p>
              <p className="text-sm text-muted-foreground mt-1">Ready to start</p>
            </div>
            <BookOpen className="h-8 w-8 text-primary" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Processing</p>
              <p className="text-3xl font-bold">0</p>
              <p className="text-sm text-muted-foreground mt-1">No active tasks</p>
            </div>
            <Download className="h-8 w-8 text-blue-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Chunks Created</p>
              <p className="text-3xl font-bold">0</p>
              <p className="text-sm text-muted-foreground mt-1">Import content to begin</p>
            </div>
            <FileText className="h-8 w-8 text-purple-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Quality Score</p>
              <p className="text-3xl font-bold">--</p>
              <p className="text-sm text-muted-foreground mt-1">Awaiting data</p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-500" />
          </div>
        </Card>
      </div>

      {/* Recent Activity and Quick Actions */}
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
            <div className="text-center py-8 text-muted-foreground">
              <BookOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium mb-2">Welcome to Lexicon!</p>
              <p className="text-sm">Start by adding your first book or document to begin organizing your knowledge base.</p>
            </div>
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
            <div className="text-center py-8 text-muted-foreground">
              <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium mb-2">No Active Processing</p>
              <p className="text-sm">Upload documents to see processing status here.</p>
            </div>
          </div>
        </Card>
      </div>

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
