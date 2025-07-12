import { useState, useEffect } from 'react';
import { Plus, FolderOpen, Settings, Download, Book, ArrowRight } from 'lucide-react';
import { Button, Card, Badge, Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui';
import { ProjectCreationWizard } from './ProjectCreationWizard';
import { useNavigate } from 'react-router-dom';

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

interface ProjectData {
  name: string;
  description: string;
  type: 'processing' | 'collection' | 'export';
  status: 'active' | 'completed' | 'paused';
  booksCount: number;
  createdAt: Date;
  lastModified: Date;
}

const mockProjects: Project[] = [];

export function ProjectManagement() {
  const [projects, setProjects] = useState<Project[]>(() => {
    // Load projects from localStorage on initialization
    const savedProjects = localStorage.getItem('lexicon-user-projects');
    if (savedProjects) {
      try {
        const parsed = JSON.parse(savedProjects);
        // Convert date strings back to Date objects
        return parsed.map((project: any) => ({
          ...project,
          createdAt: new Date(project.createdAt),
          lastModified: new Date(project.lastModified)
        }));
      } catch (error) {
        console.error('Error parsing projects from localStorage:', error);
        return [];
      }
    }
    return [];
  });
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);

  // Save projects to localStorage whenever projects change
  useEffect(() => {
    localStorage.setItem('lexicon-user-projects', JSON.stringify(projects));
  }, [projects]);

  // Clear any localStorage that might have legacy data
  useEffect(() => {
    // Clear any legacy project data on component mount
    const keysToCheck = [
      'lexicon-projects', 
      'projects', 
      'collections',
      'lexicon-collections',
      'lexicon-state',
      'lexicon-app-state'
    ];
    
    let hasCleared = false;
    keysToCheck.forEach(key => {
      if (localStorage.getItem(key)) {
        localStorage.removeItem(key);
        hasCleared = true;
      }
    });
    
    // Also clear any keys that contain project or collection data
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && (key.includes('project') || key.includes('collection') || key.includes('Śrimad') || key.includes('Bhāgavatam'))) {
        localStorage.removeItem(key);
        hasCleared = true;
      }
    }
    
    if (hasCleared) {
      console.log('Cleared legacy project data from localStorage');
    }
  }, []);

  const navigate = useNavigate();

  const handleViewDetails = (project: Project) => {
    setSelectedProject(project);
    setShowDetailsDialog(true);
  };

  const handleOpenProject = (projectId: string) => {
    navigate(`/projects/${projectId}`);
  };

  const getStatusColor = (status: Project['status']) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'completed': return 'bg-blue-500';
      case 'paused': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  const getTypeIcon = (type: Project['type']) => {
    switch (type) {
      case 'collection': return FolderOpen;
      case 'processing': return Settings;
      case 'export': return Download;
      default: return Book;
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Project Management</h1>
          <p className="text-muted-foreground mt-1">
            Organize your books into collections and configure processing workflows
          </p>
        </div>
        
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Project
        </Button>
        
        <Dialog open={showCreateDialog} onClose={() => setShowCreateDialog(false)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Project</DialogTitle>
            </DialogHeader>
            <ProjectCreationWizard 
              onComplete={(projectData: ProjectData) => {
                const newProject: Project = {
                  ...projectData,
                  id: Date.now().toString()
                };
                setProjects(prev => [...prev, newProject]);
                setShowCreateDialog(false);
              }}
              onCancel={() => setShowCreateDialog(false)}
            />
          </DialogContent>
        </Dialog>

        {/* Project Details Dialog */}
        <Dialog open={showDetailsDialog} onClose={() => setShowDetailsDialog(false)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {selectedProject?.name || 'Project Details'}
              </DialogTitle>
            </DialogHeader>
            {selectedProject && (
              <div className="space-y-6">
                <div>
                  <h3 className="font-semibold mb-2">Description</h3>
                  <p className="text-muted-foreground">{selectedProject.description}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium mb-1">Type</h4>
                    <p className="text-sm text-muted-foreground capitalize">{selectedProject.type}</p>
                  </div>
                  <div>
                    <h4 className="font-medium mb-1">Status</h4>
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${getStatusColor(selectedProject.status)}`} />
                      <span className="text-sm text-muted-foreground capitalize">{selectedProject.status}</span>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-1">Books</h4>
                    <p className="text-sm text-muted-foreground">{selectedProject.booksCount}</p>
                  </div>
                  <div>
                    <h4 className="font-medium mb-1">Created</h4>
                    <p className="text-sm text-muted-foreground">{selectedProject.createdAt.toLocaleDateString()}</p>
                  </div>
                </div>

                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setShowDetailsDialog(false)}>
                    Close
                  </Button>
                  <Button onClick={() => {
                    handleOpenProject(selectedProject.id);
                    setShowDetailsDialog(false);
                  }}>
                    Open Project
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Projects</p>
              <p className="text-2xl font-bold">{projects.length}</p>
            </div>
            <FolderOpen className="h-8 w-8 text-primary" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Active Projects</p>
              <p className="text-2xl font-bold">
                {projects.filter(p => p.status === 'active').length}
              </p>
            </div>
            <div className="w-3 h-3 bg-green-500 rounded-full" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Books</p>
              <p className="text-2xl font-bold">
                {projects.reduce((sum, p) => sum + p.booksCount, 0)}
              </p>
            </div>
            <Book className="h-8 w-8 text-primary" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Completed</p>
              <p className="text-2xl font-bold">
                {projects.filter(p => p.status === 'completed').length}
              </p>
            </div>
            <div className="w-3 h-3 bg-blue-500 rounded-full" />
          </div>
        </Card>
      </div>

      {/* Project Grid */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Your Projects</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => {
            const TypeIcon = getTypeIcon(project.type);
            return (
              <Card 
                key={project.id} 
                className="p-6 hover:shadow-md transition-shadow cursor-pointer"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <TypeIcon className="h-5 w-5 text-primary" />
                    <div>
                      <h3 className="font-semibold">{project.name}</h3>
                      <div className="flex items-center space-x-2 mt-1">
                        <div className={`w-2 h-2 rounded-full ${getStatusColor(project.status)}`} />
                        <span className="text-xs text-muted-foreground capitalize">
                          {project.status}
                        </span>
                      </div>
                    </div>
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {project.type}
                  </Badge>
                </div>
                
                <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                  {project.description}
                </p>
                
                <div className="flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    {project.booksCount} books
                  </div>
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={() => handleViewDetails(project)}
                  >
                    View Details
                    <ArrowRight className="h-3 w-3 ml-1" />
                  </Button>
                </div>
                
                <div className="mt-4 pt-4 border-t text-xs text-muted-foreground">
                  Modified {project.lastModified.toLocaleDateString()}
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Empty State for New Users */}
      {projects.length === 0 && (
        <Card className="p-12 text-center">
          <FolderOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Projects Yet</h3>
          <p className="text-muted-foreground mb-6">
            Create your first project to start organizing your books and processing workflows.
          </p>
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Your First Project
          </Button>
        </Card>
      )}
    </div>
  );
}
