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

export function Dashboard() {
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
        <Button>
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
              <p className="text-3xl font-bold">247</p>
              <p className="text-sm text-green-600 mt-1">+12 this week</p>
            </div>
            <BookOpen className="h-8 w-8 text-primary" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Processing</p>
              <p className="text-3xl font-bold">3</p>
              <p className="text-sm text-blue-600 mt-1">2 in queue</p>
            </div>
            <Download className="h-8 w-8 text-blue-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Chunks Created</p>
              <p className="text-3xl font-bold">15.2K</p>
              <p className="text-sm text-purple-600 mt-1">avg 62 per book</p>
            </div>
            <FileText className="h-8 w-8 text-purple-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Quality Score</p>
              <p className="text-3xl font-bold">94%</p>
              <p className="text-sm text-green-600 mt-1">+2% this month</p>
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
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-green-500 rounded-full" />
              <div className="flex-1">
                <p className="text-sm font-medium">Bhagavad Gita processing completed</p>
                <p className="text-xs text-muted-foreground">2 minutes ago</p>
              </div>
              <Badge variant="secondary">Complete</Badge>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-blue-500 rounded-full" />
              <div className="flex-1">
                <p className="text-sm font-medium">Srimad Bhagavatam Canto 1 started</p>
                <p className="text-xs text-muted-foreground">15 minutes ago</p>
              </div>
              <Badge variant="outline">Processing</Badge>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-purple-500 rounded-full" />
              <div className="flex-1">
                <p className="text-sm font-medium">Quality analysis updated for 5 books</p>
                <p className="text-xs text-muted-foreground">1 hour ago</p>
              </div>
              <Badge variant="secondary">Analysis</Badge>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-gray-500 rounded-full" />
              <div className="flex-1">
                <p className="text-sm font-medium">New collection "Philosophy" created</p>
                <p className="text-xs text-muted-foreground">3 hours ago</p>
              </div>
              <Badge variant="outline">Collection</Badge>
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
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Sri Isopanisad</span>
                <span className="text-xs text-muted-foreground">78%</span>
              </div>
              <Progress value={78} className="h-2" />
              <p className="text-xs text-muted-foreground mt-1">Chunking in progress...</p>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Nectar of Devotion</span>
                <span className="text-xs text-muted-foreground">45%</span>
              </div>
              <Progress value={45} className="h-2" />
              <p className="text-xs text-muted-foreground mt-1">Text extraction...</p>
            </div>
            <div className="pt-2 border-t">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">Queue Status</span>
                </div>
                <span className="text-sm font-medium">2 files waiting</span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Button variant="outline" className="h-16 flex-col">
            <Plus className="h-5 w-5 mb-1" />
            <span>Add Book</span>
          </Button>
          <Button variant="outline" className="h-16 flex-col">
            <Download className="h-5 w-5 mb-1" />
            <span>Batch Import</span>
          </Button>
          <Button variant="outline" className="h-16 flex-col">
            <BarChart3 className="h-5 w-5 mb-1" />
            <span>View Analytics</span>
          </Button>
        </div>
      </Card>
    </div>
  );
}
