import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Settings, 
  Upload, 
  Download, 
  BarChart3, 
  FileText, 
  Users, 
  Calendar,
  Book,
  FolderOpen,
  Plus,
  Edit,
  Trash2
} from 'lucide-react';
import { Button, Card, Badge } from '../ui';

interface Project {
  id: string;
  name: string;
  description: string;
  type: 'processing' | 'collection' | 'export';
  status: 'active' | 'completed' | 'paused';
  booksCount: number;
  createdAt: Date;
  lastModified: Date;
}

interface Book {
  id: string;
  title: string;
  author: string;
  status: 'processing' | 'completed' | 'error';
  addedAt: Date;
  fileSize: number;
  pages?: number;
}

export function ProjectWorkspace() {
  console.log('ProjectWorkspace: Component is being rendered');
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  console.log('ProjectWorkspace: useParams result:', { projectId });
  console.log('ProjectWorkspace: Current URL:', window.location.href);
  
  const [project, setProject] = useState<Project | null>(null);
  const [books, setBooks] = useState<Book[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'books' | 'settings'>('overview');
  const [loading, setLoading] = useState(true);

  console.log('ProjectWorkspace: Loaded with projectId:', projectId);

  useEffect(() => {
    console.log('ProjectWorkspace: useEffect running with projectId:', projectId);
    
    // Add a small delay to ensure localStorage is accessible
    const loadProject = () => {
      if (!projectId) {
        console.error('ProjectWorkspace: No projectId provided');
        setLoading(false);
        navigate('/projects');
        return;
      }
      
      // Load project from localStorage
      const savedProjects = localStorage.getItem('lexicon-user-projects');
      console.log('ProjectWorkspace: savedProjects from localStorage:', savedProjects);
      
      if (!savedProjects) {
        console.error('ProjectWorkspace: No saved projects found in localStorage');
        setLoading(false);
        navigate('/projects');
        return;
      }
      
      try {
        const projects = JSON.parse(savedProjects);
        console.log('ProjectWorkspace: parsed projects:', projects);
        console.log('ProjectWorkspace: looking for project with ID:', projectId);
        
        const foundProject = projects.find((p: any) => {
          console.log('ProjectWorkspace: comparing', p.id, 'with', projectId, '- match:', p.id === projectId);
          return p.id === projectId;
        });
        console.log('ProjectWorkspace: found project:', foundProject);
        
        if (foundProject) {
          // Convert date strings back to Date objects
          const processedProject = {
            ...foundProject,
            createdAt: new Date(foundProject.createdAt),
            lastModified: new Date(foundProject.lastModified)
          };
          console.log('ProjectWorkspace: setting processed project:', processedProject);
          setProject(processedProject);
          
          // Load books for this project (for now, empty array)
          setBooks([]);
        } else {
          console.error('Project not found:', projectId);
          console.error('Available project IDs:', projects.map((p: any) => p.id));
          navigate('/projects');
        }
      } catch (error) {
        console.error('Error parsing projects from localStorage:', error);
        navigate('/projects');
      } finally {
        setLoading(false);
      }
    };
    
    // Small delay to ensure localStorage is ready
    setTimeout(loadProject, 10);
  }, [projectId, navigate]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'completed': return 'bg-blue-500';
      case 'paused': return 'bg-yellow-500';
      case 'processing': return 'bg-blue-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  if (loading) {
    console.log('ProjectWorkspace: Showing loading state');
    return (
      <div className="p-6">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" onClick={() => navigate('/projects')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Projects
          </Button>
        </div>
        <div className="mt-8 text-center">
          <p className="text-muted-foreground">Loading project...</p>
          <p className="text-xs text-muted-foreground mt-2">Project ID: {projectId}</p>
        </div>
      </div>
    );
  }

  if (!project) {
    console.log('ProjectWorkspace: Project is null, showing loading state');
    return (
      <div className="p-6">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" onClick={() => navigate('/projects')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Projects
          </Button>
        </div>
        <div className="mt-8 text-center">
          {projectId ? (
            <div>
              <p className="text-red-600">Project not found</p>
              <p className="text-xs text-muted-foreground mt-2">Project ID: {projectId}</p>
              <p className="text-xs text-red-500 mt-2">Debug: Component loaded but project not found</p>
              <Button onClick={() => navigate('/projects')} className="mt-4">
                Go to Projects
              </Button>
            </div>
          ) : (
            <div>
              <p className="text-red-600">No project ID provided</p>
              <Button onClick={() => navigate('/projects')} className="mt-4">
                Go to Projects
              </Button>
            </div>
          )}
        </div>
      </div>
    );
  }

  console.log('ProjectWorkspace: Rendering project workspace for:', project.name);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" onClick={() => navigate('/projects')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Projects
          </Button>
          <div>
            <h1 className="text-3xl font-bold">{project.name}</h1>
            <p className="text-muted-foreground mt-1">{project.description}</p>
            <div className="flex items-center space-x-4 mt-2">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${getStatusColor(project.status)}`} />
                <span className="text-sm text-muted-foreground capitalize">{project.status}</span>
              </div>
              <Badge variant="secondary" className="text-xs">
                {project.type}
              </Badge>
              <span className="text-sm text-muted-foreground">
                {project.booksCount} books
              </span>
            </div>
          </div>
        </div>
        
        <div className="flex space-x-2">
          <Button variant="outline" onClick={() => navigate('/library')}>
            <Plus className="h-4 w-4 mr-2" />
            Add Books
          </Button>
          <Button variant="outline">
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-border">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground'
            }`}
          >
            <BarChart3 className="h-4 w-4 inline mr-2" />
            Overview
          </button>
          <button
            onClick={() => setActiveTab('books')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'books'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground'
            }`}
          >
            <Book className="h-4 w-4 inline mr-2" />
            Books ({books.length})
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'settings'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground'
            }`}
          >
            <Settings className="h-4 w-4 inline mr-2" />
            Settings
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Books</p>
                  <p className="text-2xl font-bold">{books.length}</p>
                </div>
                <Book className="h-8 w-8 text-primary" />
              </div>
            </Card>
            
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Processing</p>
                  <p className="text-2xl font-bold">
                    {books.filter(b => b.status === 'processing').length}
                  </p>
                </div>
                <div className="w-3 h-3 bg-blue-500 rounded-full" />
              </div>
            </Card>
            
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Completed</p>
                  <p className="text-2xl font-bold">
                    {books.filter(b => b.status === 'completed').length}
                  </p>
                </div>
                <div className="w-3 h-3 bg-green-500 rounded-full" />
              </div>
            </Card>
            
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Errors</p>
                  <p className="text-2xl font-bold">
                    {books.filter(b => b.status === 'error').length}
                  </p>
                </div>
                <div className="w-3 h-3 bg-red-500 rounded-full" />
              </div>
            </Card>
          </div>

          {/* Recent Activity */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
            <div className="space-y-3">
              <div className="flex items-center space-x-3 text-sm">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <span>Project created on {project.createdAt.toLocaleDateString()}</span>
              </div>
              <div className="flex items-center space-x-3 text-sm">
                <Edit className="h-4 w-4 text-muted-foreground" />
                <span>Last modified on {project.lastModified.toLocaleDateString()}</span>
              </div>
            </div>
          </Card>

          {/* Quick Actions */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Button variant="outline" className="h-20 flex-col" onClick={() => navigate('/library')}>
                <Plus className="h-6 w-6 mb-2" />
                Add Books
              </Button>
              <Button variant="outline" className="h-20 flex-col">
                <Upload className="h-6 w-6 mb-2" />
                Import Data
              </Button>
              <Button variant="outline" className="h-20 flex-col">
                <Download className="h-6 w-6 mb-2" />
                Export Results
              </Button>
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'books' && (
        <div className="space-y-4">
          {books.length === 0 ? (
            <Card className="p-12 text-center">
              <Book className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Books in Project</h3>
              <p className="text-muted-foreground mb-6">
                Add books to this project to start processing and organizing your content.
              </p>
              <Button onClick={() => navigate('/library')}>
                <Plus className="h-4 w-4 mr-2" />
                Add Books to Project
              </Button>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {books.map((book) => (
                <Card key={book.id} className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <FileText className="h-5 w-5 text-primary" />
                      <div>
                        <h3 className="font-semibold">{book.title}</h3>
                        <p className="text-sm text-muted-foreground">{book.author}</p>
                        <div className="flex items-center space-x-2 mt-1">
                          <div className={`w-2 h-2 rounded-full ${getStatusColor(book.status)}`} />
                          <span className="text-xs text-muted-foreground capitalize">
                            {book.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Added:</span>
                      <span>{book.addedAt.toLocaleDateString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Size:</span>
                      <span>{(book.fileSize / 1024 / 1024).toFixed(1)} MB</span>
                    </div>
                    {book.pages && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Pages:</span>
                        <span>{book.pages}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex space-x-2 mt-4">
                    <Button variant="outline" size="sm" className="flex-1">
                      <Edit className="h-3 w-3 mr-1" />
                      Process
                    </Button>
                    <Button variant="outline" size="sm">
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'settings' && (
        <div className="space-y-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Project Settings</h3>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Project Name</label>
                <input 
                  type="text" 
                  className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background" 
                  defaultValue={project.name}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Description</label>
                <textarea 
                  className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background" 
                  rows={3}
                  defaultValue={project.description}
                />
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline">Cancel</Button>
                <Button>Save Changes</Button>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4 text-red-600">Danger Zone</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 border border-red-200 rounded-lg">
                <div>
                  <h4 className="font-medium text-red-600">Delete Project</h4>
                  <p className="text-sm text-muted-foreground">
                    Permanently delete this project and all its data. This action cannot be undone.
                  </p>
                </div>
                <Button variant="outline" className="text-red-600 border-red-200 hover:bg-red-50">
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Project
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
