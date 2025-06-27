/**
 * Component Showcase
 * 
 * A demonstration page showcasing all available UI components
 * in the Lexicon design system.
 */

import { useState } from 'react';
import {
  Button,
  Input,
  Label,
  Textarea,
  Select,
  Card,
  Badge,
  Progress,
  Tabs,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
  Spinner,
  ThemeToggle,
  useToastActions,
} from './ui';
import { Plus, Settings } from 'lucide-react';

export function ComponentShowcase() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectValue, setSelectValue] = useState('');
  const [progress, setProgress] = useState(65);
  const toast = useToastActions();

  const selectOptions = [
    { value: 'option1', label: 'Option 1' },
    { value: 'option2', label: 'Option 2' },
    { value: 'option3', label: 'Option 3' },
    { value: 'option4', label: 'Option 4 (Disabled)', disabled: true },
  ];

  const showToast = (type: 'success' | 'error' | 'warning' | 'info') => {
    switch (type) {
      case 'success':
        toast.success('Success!', 'This is a success message.');
        break;
      case 'error':
        toast.error('Error!', 'This is an error message.');
        break;
      case 'warning':
        toast.warning('Warning!', 'This is a warning message.');
        break;
      case 'info':
        toast.info('Info!', 'This is an info message.');
        break;
    }
  };

  return (
    <div className="p-8 space-y-12 max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-foreground">Lexicon UI Components</h1>
        <p className="text-lg text-muted-foreground">
          A comprehensive design system for the Lexicon RAG dataset preparation tool.
        </p>
        <div className="flex justify-center">
          <ThemeToggle />
        </div>
      </div>

      {/* Buttons */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Buttons</h2>
        <Card className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Default</Label>
              <Button>Primary Button</Button>
            </div>
            <div className="space-y-2">
              <Label>Secondary</Label>
              <Button variant="secondary">Secondary</Button>
            </div>
            <div className="space-y-2">
              <Label>Outline</Label>
              <Button variant="outline">Outline</Button>
            </div>
            <div className="space-y-2">
              <Label>Ghost</Label>
              <Button variant="ghost">Ghost</Button>
            </div>
            <div className="space-y-2">
              <Label>Destructive</Label>
              <Button variant="destructive">Delete</Button>
            </div>
            <div className="space-y-2">
              <Label>With Icon</Label>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add New
              </Button>
            </div>
          </div>
          <div className="mt-4 space-y-2">
            <Label>Sizes</Label>
            <div className="flex items-center space-x-2">
              <Button size="sm">Small</Button>
              <Button size="default">Default</Button>
              <Button size="lg">Large</Button>
              <Button size="icon">
                <Settings className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </Card>
      </section>

      {/* Form Elements */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Form Elements</h2>
        <Card className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="input-example">Input Field</Label>
                <Input
                  id="input-example"
                  placeholder="Enter some text..."
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="select-example">Select Dropdown</Label>
                <Select
                  value={selectValue}
                  onValueChange={setSelectValue}
                  options={selectOptions}
                  placeholder="Choose an option..."
                />
              </div>
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="textarea-example">Textarea</Label>
                <Textarea
                  id="textarea-example"
                  placeholder="Enter a longer description..."
                  rows={4}
                />
              </div>
            </div>
          </div>
        </Card>
      </section>

      {/* Feedback Elements */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Feedback Elements</h2>
        <Card className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Badges</Label>
                <div className="flex space-x-2">
                  <Badge>Default</Badge>
                  <Badge variant="secondary">Secondary</Badge>
                  <Badge variant="destructive">Error</Badge>
                  <Badge variant="outline">Outline</Badge>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Spinners</Label>
                <div className="flex items-center space-x-4">
                  <Spinner size="sm" />
                  <Spinner size="md" />
                  <Spinner size="lg" />
                </div>
              </div>
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Progress Bar</Label>
                <Progress value={progress} className="w-full" />
                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setProgress(Math.max(0, progress - 10))}
                  >
                    -10%
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setProgress(Math.min(100, progress + 10))}
                  >
                    +10%
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </section>

      {/* Toasts */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Toast Notifications</h2>
        <Card className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button onClick={() => showToast('success')} variant="outline">
              Success Toast
            </Button>
            <Button onClick={() => showToast('error')} variant="outline">
              Error Toast
            </Button>
            <Button onClick={() => showToast('warning')} variant="outline">
              Warning Toast
            </Button>
            <Button onClick={() => showToast('info')} variant="outline">
              Info Toast
            </Button>
          </div>
        </Card>
      </section>

      {/* Tabs */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Tabs</h2>
        <Card className="p-6">
          <Tabs defaultIndex={0}>
            <TabList>
              <Tab>Overview</Tab>
              <Tab>Settings</Tab>
              <Tab>Advanced</Tab>
            </TabList>
            <TabPanels>
              <TabPanel>
                <div className="space-y-4">
                  <h3 className="text-lg font-medium">Overview</h3>
                  <p className="text-muted-foreground">
                    This is the overview tab content. Here you can see general information
                    about your project and recent activity.
                  </p>
                </div>
              </TabPanel>
              <TabPanel>
                <div className="space-y-4">
                  <h3 className="text-lg font-medium">Settings</h3>
                  <p className="text-muted-foreground">
                    Configure your project settings, preferences, and integrations here.
                  </p>
                </div>
              </TabPanel>
              <TabPanel>
                <div className="space-y-4">
                  <h3 className="text-lg font-medium">Advanced</h3>
                  <p className="text-muted-foreground">
                    Advanced configuration options for power users and developers.
                  </p>
                </div>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </Card>
      </section>

      {/* Dialog */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Dialog</h2>
        <Card className="p-6">
          <Button onClick={() => setDialogOpen(true)}>
            Open Dialog
          </Button>
          
          <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
            <DialogContent>
              <DialogClose onClose={() => setDialogOpen(false)} />
              <DialogHeader>
                <DialogTitle>Confirm Action</DialogTitle>
                <DialogDescription>
                  Are you sure you want to proceed with this action? This cannot be undone.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={() => setDialogOpen(false)}>
                  Confirm
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </Card>
      </section>

      {/* Component Stats */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Component Library Stats</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="p-6 text-center">
            <div className="text-3xl font-bold text-primary">15+</div>
            <div className="text-sm text-muted-foreground">Components</div>
          </Card>
          <Card className="p-6 text-center">
            <div className="text-3xl font-bold text-primary">2</div>
            <div className="text-sm text-muted-foreground">Themes</div>
          </Card>
          <Card className="p-6 text-center">
            <div className="text-3xl font-bold text-primary">100%</div>
            <div className="text-sm text-muted-foreground">Accessible</div>
          </Card>
        </div>
      </section>
    </div>
  );
}
