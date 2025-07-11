import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { 
  BookOpen, 
  FileText, 
  Users, 
  Zap, 
  Download, 
  Play, 
  CheckCircle,
  Clock
} from 'lucide-react';

interface SampleProject {
  id: string;
  title: string;
  description: string;
  category: 'research' | 'literature' | 'collaboration' | 'analysis';
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  estimatedTime: string;
  features: string[];
  content: {
    documents: number;
    sources: number;
    annotations: number;
  };
  preview: string;
  setupSteps: string[];
}

const SAMPLE_PROJECTS: SampleProject[] = [
  {
    id: 'philosophy-intro',
    title: 'Introduction to Philosophy',
    description: 'Explore fundamental philosophical questions through classic texts and modern interpretations.',
    category: 'literature',
    difficulty: 'beginner',
    estimatedTime: '15-20 minutes',
    features: ['Document analysis', 'Concept mapping', 'Cross-references', 'Annotations'],
    content: {
      documents: 8,
      sources: 3,
      annotations: 25
    },
    preview: 'Sample texts from Plato, Aristotle, and contemporary philosophers with guided analysis.',
    setupSteps: [
      'Import philosophical texts',
      'Set up concept mapping',
      'Configure cross-reference system',
      'Add sample annotations'
    ]
  },
  {
    id: 'research-methodology',
    title: 'Academic Research Project',
    description: 'Learn research organization with papers, citations, and collaborative note-taking.',
    category: 'research',
    difficulty: 'intermediate',
    estimatedTime: '25-30 minutes',
    features: ['Citation management', 'Research timeline', 'Collaboration', 'Literature review'],
    content: {
      documents: 15,
      sources: 8,
      annotations: 45
    },
    preview: 'Complete research workflow from literature review to final paper organization.',
    setupSteps: [
      'Import research papers',
      'Set up citation system',
      'Create research timeline',
      'Configure collaboration features'
    ]
  },
  {
    id: 'content-analysis',
    title: 'Text Analysis Workshop',
    description: 'Advanced content analysis using AI-powered insights and pattern recognition.',
    category: 'analysis',
    difficulty: 'advanced',
    estimatedTime: '35-40 minutes',
    features: ['AI analysis', 'Pattern recognition', 'Sentiment analysis', 'Topic modeling'],
    content: {
      documents: 20,
      sources: 12,
      annotations: 60
    },
    preview: 'Comprehensive text analysis with machine learning insights and data visualization.',
    setupSteps: [
      'Import diverse text corpus',
      'Configure AI analysis tools',
      'Set up pattern recognition',
      'Create analysis dashboards'
    ]
  },
  {
    id: 'team-collaboration',
    title: 'Team Knowledge Base',
    description: 'Collaborative workspace for team research and knowledge sharing.',
    category: 'collaboration',
    difficulty: 'intermediate',
    estimatedTime: '20-25 minutes',
    features: ['Shared workspaces', 'Real-time editing', 'Comment system', 'Version control'],
    content: {
      documents: 12,
      sources: 6,
      annotations: 35
    },
    preview: 'Multi-user environment with shared documents and collaborative editing features.',
    setupSteps: [
      'Create shared workspace',
      'Set up user permissions',
      'Configure collaboration tools',
      'Enable real-time features'
    ]
  }
];

const CATEGORY_ICONS = {
  research: FileText,
  literature: BookOpen,
  collaboration: Users,
  analysis: Zap
};

const DIFFICULTY_COLORS = {
  beginner: 'bg-green-100 text-green-800 border-green-200',
  intermediate: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  advanced: 'bg-red-100 text-red-800 border-red-200'
};

interface SampleProjectsProps {
  onProjectSelect: (project: SampleProject) => void;
  onSkip: () => void;
}

export function SampleProjects({ onProjectSelect, onSkip }: SampleProjectsProps) {
  const [selectedProject, setSelectedProject] = useState<SampleProject | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [creationProgress, setCreationProgress] = useState(0);
  const [filter, setFilter] = useState<'all' | 'beginner' | 'intermediate' | 'advanced'>('all');

  const filteredProjects = SAMPLE_PROJECTS.filter(project => 
    filter === 'all' || project.difficulty === filter
  );

  const handleCreateProject = async (project: SampleProject) => {
    setSelectedProject(project);
    setIsCreating(true);
    setCreationProgress(0);

    // Simulate project creation steps
    for (let i = 0; i <= project.setupSteps.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      setCreationProgress((i / project.setupSteps.length) * 100);
    }

    setIsCreating(false);
    onProjectSelect(project);
  };

  const handlePreview = (project: SampleProject) => {
    setSelectedProject(project);
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold">Choose a Sample Project</h1>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Get started quickly with pre-configured projects that demonstrate Lexicon's key features.
          Each project includes sample content and guided tutorials.
        </p>
      </div>

      {/* Filters */}
      <div className="flex justify-center gap-2">
        {['all', 'beginner', 'intermediate', 'advanced'].map((level) => (
          <Button
            key={level}
            variant={filter === level ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter(level as typeof filter)}
            className="capitalize"
          >
            {level === 'all' ? 'All Levels' : level}
          </Button>
        ))}
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredProjects.map((project) => {
          const CategoryIcon = CATEGORY_ICONS[project.category];
          
          return (
            <Card key={project.id} className="group hover:shadow-lg transition-all duration-200">
              <CardHeader className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <CategoryIcon className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{project.title}</CardTitle>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge 
                          variant="outline" 
                          className={`text-xs ${DIFFICULTY_COLORS[project.difficulty]}`}
                        >
                          {project.difficulty}
                        </Badge>
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          <Clock className="w-3 h-3" />
                          {project.estimatedTime}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <p className="text-sm text-muted-foreground">{project.description}</p>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Content Stats */}
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="space-y-1">
                    <div className="text-lg font-semibold">{project.content.documents}</div>
                    <div className="text-xs text-muted-foreground">Documents</div>
                  </div>
                  <div className="space-y-1">
                    <div className="text-lg font-semibold">{project.content.sources}</div>
                    <div className="text-xs text-muted-foreground">Sources</div>
                  </div>
                  <div className="space-y-1">
                    <div className="text-lg font-semibold">{project.content.annotations}</div>
                    <div className="text-xs text-muted-foreground">Annotations</div>
                  </div>
                </div>

                {/* Features */}
                <div className="space-y-2">
                  <div className="text-sm font-medium">Featured Tools:</div>
                  <div className="flex flex-wrap gap-1">
                    {project.features.map((feature) => (
                      <Badge key={feature} variant="secondary" className="text-xs">
                        {feature}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePreview(project)}
                    className="flex-1"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Preview
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => handleCreateProject(project)}
                    className="flex-1"
                  >
                    <Play className="w-4 h-4 mr-2" />
                    Create Project
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Skip Option */}
      <div className="text-center pt-6 border-t">
        <p className="text-sm text-muted-foreground mb-3">
          Prefer to start from scratch?
        </p>
        <Button variant="ghost" onClick={onSkip} className="text-muted-foreground">
          Skip sample projects and create my own
        </Button>
      </div>

      {/* Project Preview Modal */}
      {selectedProject && !isCreating && (
        <Dialog open={!!selectedProject} onClose={() => setSelectedProject(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-primary/10">
                  {(() => {
                    const Icon = CATEGORY_ICONS[selectedProject.category];
                    return <Icon className="w-5 h-5 text-primary" />;
                  })()}
                </div>
                {selectedProject.title}
              </DialogTitle>
              <DialogDescription>
                {selectedProject.description}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-6">
              {/* Preview Content */}
              <div className="bg-muted/50 rounded-lg p-4">
                <h3 className="font-medium mb-2">What's included:</h3>
                <p className="text-sm text-muted-foreground">{selectedProject.preview}</p>
              </div>

              {/* Setup Steps */}
              <div className="space-y-3">
                <h3 className="font-medium">Setup includes:</h3>
                <div className="space-y-2">
                  {selectedProject.setupSteps.map((step, index) => (
                    <div key={index} className="flex items-center gap-3 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      {step}
                    </div>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-4 border-t">
                <Button
                  variant="outline"
                  onClick={() => setSelectedProject(null)}
                  className="flex-1"
                >
                  Back to Projects
                </Button>
                <Button
                  onClick={() => handleCreateProject(selectedProject)}
                  className="flex-1"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Create This Project
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Creation Progress Modal */}
      {isCreating && selectedProject && (
        <Dialog open={isCreating} onClose={() => {}}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Creating Sample Project</DialogTitle>
              <DialogDescription>
                Setting up "{selectedProject.title}" with sample content...
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-6">
              <Progress value={creationProgress} className="w-full" />
              
              <div className="space-y-2">
                {selectedProject.setupSteps.map((step, index) => {
                  const stepProgress = (creationProgress / 100) * selectedProject.setupSteps.length;
                  const isCompleted = stepProgress > index;
                  const isCurrent = Math.floor(stepProgress) === index;
                  
                  return (
                    <div
                      key={index}
                      className={`flex items-center gap-3 text-sm transition-colors ${
                        isCompleted ? 'text-green-600' : isCurrent ? 'text-primary' : 'text-muted-foreground'
                      }`}
                    >
                      {isCompleted ? (
                        <CheckCircle className="w-4 h-4" />
                      ) : isCurrent ? (
                        <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <div className="w-4 h-4 border-2 border-muted-foreground/30 rounded-full" />
                      )}
                      {step}
                    </div>
                  );
                })}
              </div>

              <div className="text-center text-sm text-muted-foreground">
                This may take a few moments...
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
