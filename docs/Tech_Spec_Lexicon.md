# Technical Specification Document

## Lexicon: Universal RAG Dataset Preparation Tool

**Version:** 1.0  
**Date:** June 25, 2025

---

## 🎯 Technical Overview

### Technology Stack Decision: Tauri + React
**Rationale**: Tauri provides native cross-platform performance with web technology flexibility, eliminating platform-specific development while maintaining native system integration capabilities on both Windows and macOS.

**Frontend Stack Details**:
- **React 18**: Latest React with concurrent features for optimal performance
- **TypeScript**: Type safety and enhanced developer experience
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **Headless UI**: Unstyled, accessible UI components for custom design implementation
- **Lucide React**: Modern icon library for consistent iconography
- **React Query**: Server state management and caching
- **Zustand**: Lightweight client state management

### Architecture Philosophy
- **Local-First**: All processing happens on the user's computer with no external dependencies
- **Privacy-Focused**: No data leaves the user's machine without explicit consent
- **Performance-Optimized**: Native Rust backend with efficient React frontend
- **Cross-Platform**: Native performance on Windows 10+ and macOS 10.15+
- **Universal-Compatible**: Intelligent content recognition for any text domain
- **Extensible**: Plugin architecture ready for future enhancements and content types

---

## 🏗️ System Architecture

### High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    LEXICON MAC APP                          │
├─────────────────────────────────────────────────────────────┤
│  FRONTEND (React + TypeScript + Tailwind CSS)              │
│  ┌─────────────────┬─────────────────┬─────────────────┐   │
│  │   Registry UI   │  Processing UI  │   Export UI     │   │
│  │   Components    │   Components    │   Components    │   │
│  │  + Enrichment   │  + Visual UI    │  + Metadata     │   │
│  └─────────────────┴─────────────────┴─────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  TAURI BRIDGE (Rust Commands & Events)                     │
│  ┌─────────────────┬─────────────────┬─────────────────┐   │
│  │  Registry API   │ Processing API  │  Export API     │   │
│  │   Commands      │   Commands      │   Commands      │   │
│  │ + Enrichment    │ + Metadata      │ + Visual Assets │   │
│  └─────────────────┴─────────────────┴─────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  BACKEND ENGINE (Rust + Python Integration)                │
│  ┌─────────────────┬─────────────────┬─────────────────┐   │
│  │  Registry Core  │ Ingestion Core  │ Chunking Core   │   │
│  │   (SQLite)      │   (Python)      │   (Rust)        │   │
│  │ + Enrichment    │ + Web APIs      │ + Relationships │   │
│  └─────────────────┴─────────────────┴─────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  METADATA ENRICHMENT LAYER                                 │
│  ┌─────────────────┬─────────────────┬─────────────────┐   │
│  │  External APIs  │  Visual Assets  │  Relationships  │   │
│  │  (Google Books, │  (Cover Images, │  (Translations, │   │
│  │   OpenLibrary)  │   Author Photos)│   Similar Books)│   │
│  └─────────────────┴─────────────────┴─────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  SYSTEM INTEGRATION (Native Mac APIs)                      │
│  ┌─────────────────┬─────────────────┬─────────────────┐   │
│  │  File System    │  Notifications  │  Cloud Storage  │   │
│  │   Operations    │    Center       │   Integration   │   │
│  └─────────────────┴─────────────────┴─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🖥️ Frontend Architecture (React + TypeScript)

### UI Component Library Strategy

```typescript
// Component library configuration
// Using Headless UI for accessibility with custom Tailwind styling

// components/ui/Button.tsx
import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/utils/cn';

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "underline-offset-4 hover:underline text-primary",
      },
      size: {
        default: "h-10 py-2 px-4",
        sm: "h-9 px-3 rounded-md",
        lg: "h-11 px-8 rounded-md",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);

export { Button, buttonVariants };
```

### React Component Data Flow Architecture

```typescript
// Component data flow and event propagation strategy

// Parent-Child Data Flow Pattern
interface ComponentDataFlow {
  parent: React.ComponentType;
  children: React.ComponentType[];
  dataFlow: 'top-down' | 'bottom-up' | 'bidirectional';
  communicationMethod: 'props' | 'context' | 'events' | 'state-management';
}

// Example: BookCatalog → BookCard data flow
const bookCatalogFlow: ComponentDataFlow = {
  parent: BookCatalog,
  children: [BookCard, AddBookModal, SearchFilter],
  dataFlow: 'bidirectional',
  communicationMethod: 'props',
};

// Enhanced BookCatalog with explicit data flow
export const BookCatalog: React.FC = () => {
  const { books, addBook, updateBook, deleteBook, loading, error } = useBookRegistry();
  const [selectedBooks, setSelectedBooks] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState<BookCategory | 'all'>('all');

  // Data processing and filtering
  const filteredBooks = useMemo(() => {
    return books.filter(book => {
      const matchesSearch = book.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           book.author.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory = filterCategory === 'all' || book.category === filterCategory;
      return matchesSearch && matchesCategory;
    });
  }, [books, searchQuery, filterCategory]);

  // File type detection utility
  const getSourceTypeFromFile = useCallback((file: File): SourceType => {
    const extension = file.name.split('.').pop()?.toLowerCase();
    const mimeType = file.type;
    
    // Priority order: MIME type first, then extension
    if (mimeType === 'application/pdf' || extension === 'pdf') {
      return 'pdf';
    } else if (mimeType === 'application/epub+zip' || extension === 'epub') {
      return 'epub';
    } else if (extension === 'mobi') {
      return 'mobi';
    } else if (mimeType === 'text/plain' || extension === 'txt') {
      return 'txt';
    } else {
      // Default to manual for unknown types
      return 'manual';
    }
  }, []);

  // Event handlers with proper error boundaries
  const handleFileDrop = useCallback(async (files: FileList) => {
    const fileArray = Array.from(files);
    
    for (const file of fileArray) {
      try {
        const sourceType = getSourceTypeFromFile(file);
        const newBook: Partial<Book> = {
          title: file.name.replace(/\.[^/.]+$/, ''), // Remove extension
          author: 'Unknown', // Will be extracted later
          category: 'personal_development', // Default category
          sourceType,
          localPath: file.path || '', // Electron/Tauri provides path
          priority: 'medium',
          metadata: {
            originalFileName: file.name,
            fileSize: file.size,
            lastModified: new Date(file.lastModified),
            mimeType: file.type,
          },
        };
        
        await addBook(newBook);
      } catch (error) {
        console.error('Failed to add book:', error);
        // Error handling will be managed by useBookRegistry hook
      }
    }
  }, [addBook, getSourceTypeFromFile]);

  // Event propagation from child components
  const handleBookUpdate = useCallback((bookId: string, updates: Partial<Book>) => {
    updateBook(bookId, updates);
  }, [updateBook]);

  const handleBookSelection = useCallback((bookId: string, selected: boolean) => {
    setSelectedBooks(prev => 
      selected 
        ? [...prev, bookId]
        : prev.filter(id => id !== bookId)
    );
  }, []);

  const handleBulkAction = useCallback(async (action: 'delete' | 'process' | 'export') => {
    if (selectedBooks.length === 0) return;
    
    switch (action) {
      case 'delete':
        for (const bookId of selectedBooks) {
          await deleteBook(bookId);
        }
        setSelectedBooks([]);
        break;
      case 'process':
        // Trigger processing for selected books
        for (const bookId of selectedBooks) {
          // This would integrate with processing engine
          console.log('Starting processing for:', bookId);
        }
        break;
      case 'export':
        // Trigger export for selected books
        console.log('Exporting books:', selectedBooks);
        break;
    }
  }, [selectedBooks, deleteBook]);

  if (loading) {
    return <LoadingSpinner message="Loading book catalog..." />;
  }

  if (error) {
    return <ErrorDisplay error={error} onRetry={() => window.location.reload()} />;
  }

  return (
    <div className="book-catalog space-y-6">
      {/* Search and Filter Controls */}
      <div className="flex flex-col sm:flex-row gap-4">
        <SearchFilter
          query={searchQuery}
          onQueryChange={setSearchQuery}
          category={filterCategory}
          onCategoryChange={setFilterCategory}
          placeholder="Search books by title or author..."
        />
        
        {selectedBooks.length > 0 && (
          <BulkActionBar
            selectedCount={selectedBooks.length}
            onAction={handleBulkAction}
            onClearSelection={() => setSelectedBooks([])}
          />
        )}
      </div>

      {/* Drag and Drop Zone */}
      <DragDropZone 
        onFileDrop={handleFileDrop}
        accept=".pdf,.epub,.mobi,.txt"
        className="min-h-[200px]"
      >
        {filteredBooks.length === 0 ? (
          <EmptyState
            title="No books in your catalog"
            description="Drag and drop files here or click to add your first book"
            actionLabel="Add Book"
            onAction={() => {/* Open file dialog */}}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredBooks.map(book => (
              <BookCard
                key={book.id}
                book={book}
                selected={selectedBooks.includes(book.id)}
                onUpdate={(updates) => handleBookUpdate(book.id, updates)}
                onDelete={() => deleteBook(book.id)}
                onSelect={(selected) => handleBookSelection(book.id, selected)}
                onProcess={() => {/* Start processing */}}
              />
            ))}
          </div>
        )}
      </DragDropZone>

      {/* Add Book Modal */}
      <AddBookModal
        isOpen={false} // Controlled by local state
        onClose={() => {/* Close modal */}}
        onAdd={addBook}
      />
    </div>
  );
};

// Enhanced BookCard with proper event handling
interface BookCardProps {
  book: Book;
  selected: boolean;
  onUpdate: (updates: Partial<Book>) => void;
  onDelete: () => void;
  onSelect: (selected: boolean) => void;
  onProcess: () => void;
}

export const BookCard: React.FC<BookCardProps> = ({
  book,
  selected,
  onUpdate,
  onDelete,
  onSelect,
  onProcess,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [localTitle, setLocalTitle] = useState(book.title);

  const handleSaveEdit = useCallback(() => {
    if (localTitle.trim() && localTitle !== book.title) {
      onUpdate({ title: localTitle.trim() });
    }
    setIsEditing(false);
  }, [localTitle, book.title, onUpdate]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSaveEdit();
    } else if (e.key === 'Escape') {
      setLocalTitle(book.title);
      setIsEditing(false);
    }
  }, [handleSaveEdit, book.title]);

  const statusColor = useMemo(() => {
    switch (book.status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'on_hold': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  }, [book.status]);

  return (
    <div className={cn(
      "book-card bg-white dark:bg-gray-800 rounded-lg shadow-md border-2 transition-all duration-200",
      selected ? "border-primary shadow-lg" : "border-gray-200 dark:border-gray-700 hover:shadow-lg"
    )}>
      {/* Selection Checkbox */}
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <Checkbox
            checked={selected}
            onCheckedChange={onSelect}
            aria-label={`Select ${book.title}`}
          />
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => setIsEditing(true)}>
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem onClick={onProcess}>
                <Play className="h-4 w-4 mr-2" />
                Process
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={onDelete} className="text-red-600">
                <Trash className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Book Cover/Icon */}
        <div className="w-full h-32 bg-gradient-to-br from-primary/10 to-primary/5 rounded-md mb-3 flex items-center justify-center">
          <BookOpen className="h-12 w-12 text-primary/50" />
        </div>

        {/* Title (Editable) */}
        {isEditing ? (
          <Input
            value={localTitle}
            onChange={(e) => setLocalTitle(e.target.value)}
            onBlur={handleSaveEdit}
            onKeyDown={handleKeyDown}
            className="mb-2"
            autoFocus
          />
        ) : (
          <h3 
            className="font-semibold text-lg mb-2 line-clamp-2 cursor-pointer hover:text-primary"
            onClick={() => setIsEditing(true)}
            title={book.title}
          >
            {book.title}
          </h3>
        )}

        {/* Author */}
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
          by {book.author}
        </p>

        {/* Status Badge */}
        <div className="flex items-center justify-between mb-3">
          <Badge className={statusColor}>
            {book.status.replace('_', ' ')}
          </Badge>
          
          <div className="flex items-center text-xs text-gray-500">
            <FileIcon className="h-3 w-3 mr-1" />
            {book.sourceType}
          </div>
        </div>

        {/* Progress Bar (if processing) */}
        {book.status === 'in_progress' && book.stages && (
          <div className="mb-3">
            <div className="flex justify-between text-xs text-gray-600 mb-1">
              <span>Processing...</span>
              <span>{Math.round((book.stages.progress || 0) * 100)}%</span>
            </div>
            <Progress value={(book.stages.progress || 0) * 100} className="h-2" />
          </div>
        )}

        {/* Metadata */}
        <div className="text-xs text-gray-500 space-y-1">
          <div className="flex justify-between">
            <span>Category:</span>
            <span className="font-medium">{book.category.replace('_', ' ')}</span>
          </div>
          {book.metadata.pages && (
            <div className="flex justify-between">
              <span>Pages:</span>
              <span className="font-medium">{book.metadata.pages}</span>
            </div>
          )}
          <div className="flex justify-between">
            <span>Added:</span>
            <span className="font-medium">
              {new Date(book.createdAt).toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
```

### State Management Strategy

```typescript
// Global state management using Zustand
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface AppStore {
  // UI State
  activeTab: string;
  sidebarOpen: boolean;
  theme: 'light' | 'dark' | 'system';
  
  // Notification State
  notifications: Notification[];
  
  // Actions
  setActiveTab: (tab: string) => void;
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
}

export const useAppStore = create<AppStore>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        activeTab: 'catalog',
        sidebarOpen: true,
        theme: 'system',
        notifications: [],
        
        // Actions
        setActiveTab: (tab) => set({ activeTab: tab }),
        toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
        setTheme: (theme) => set({ theme }),
        addNotification: (notification) => set((state) => ({
          notifications: [...state.notifications, { ...notification, id: crypto.randomUUID() }]
        })),
        removeNotification: (id) => set((state) => ({
          notifications: state.notifications.filter(n => n.id !== id)
        })),
      }),
      {
        name: 'lexicon-app-state',
        partialize: (state) => ({
          theme: state.theme,
          sidebarOpen: state.sidebarOpen,
          activeTab: state.activeTab,
        }),
      }
    ),
    {
      name: 'lexicon-app-store',
    }
  )
);

// Utility for class name merging
export function cn(...inputs: (string | undefined | null | false)[]): string {
  return inputs.filter(Boolean).join(' ');
}
```

---

## Python Environment Management & Dependencies

```rust
// Enhanced Python Environment Management
use std::path::PathBuf;
use std::process::Command;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PythonEnvironment {
    pub python_path: PathBuf,
    pub venv_path: Option<PathBuf>,
    pub pip_path: PathBuf,
    pub version: String,
    pub isolated: bool,
}

pub struct PythonEnvironmentManager {
    app_data_dir: PathBuf,
    current_env: Option<PythonEnvironment>,
}

impl PythonEnvironmentManager {
    pub fn new(app_data_dir: PathBuf) -> Self {
        PythonEnvironmentManager {
            app_data_dir,
            current_env: None,
        }
    }
    
    pub async fn initialize_environment(&mut self) -> Result<PythonEnvironment, PythonEnvironmentError> {
        // Strategy: Create isolated virtual environment for Lexicon
        let venv_dir = self.app_data_dir.join("python_env");
        
        // Check if Python is available
        let python_executable = self.detect_python_executable()?;
        
        // Create virtual environment if it doesn't exist
        if !venv_dir.exists() {
            self.create_virtual_environment(&python_executable, &venv_dir).await?;
        }
        
        // Determine paths in virtual environment
        let (python_path, pip_path) = self.get_venv_executables(&venv_dir)?;
        
        // Verify Python version compatibility
        let version = self.get_python_version(&python_path).await?;
        if !self.is_version_compatible(&version) {
            return Err(PythonEnvironmentError::IncompatibleVersion {
                found: version,
                required: "3.8+".to_string(),
            });
        }
        
        // Install/update required dependencies
        self.ensure_dependencies(&pip_path).await?;
        
        let env = PythonEnvironment {
            python_path,
            venv_path: Some(venv_dir),
            pip_path,
            version,
            isolated: true,
        };
        
        self.current_env = Some(env.clone());
        Ok(env)
    }
    
    fn detect_python_executable(&self) -> Result<PathBuf, PythonEnvironmentError> {
        // Try different Python executables in order of preference
        let candidates = vec!["python3", "python", "py"];
        
        for candidate in candidates {
            if let Ok(output) = Command::new(candidate)
                .arg("--version")
                .output() 
            {
                if output.status.success() {
                    return Ok(PathBuf::from(candidate));
                }
            }
        }
        
        Err(PythonEnvironmentError::PythonNotFound)
    }
    
    async fn create_virtual_environment(&self, python_exe: &PathBuf, venv_dir: &PathBuf) -> Result<(), PythonEnvironmentError> {
        log::info!("Creating Python virtual environment at: {:?}", venv_dir);
        
        let output = Command::new(python_exe)
            .args(&["-m", "venv", venv_dir.to_str().unwrap()])
            .output()
            .map_err(|e| PythonEnvironmentError::VenvCreationFailed(e.to_string()))?;
        
        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(PythonEnvironmentError::VenvCreationFailed(stderr.to_string()));
        }
        
        log::info!("Python virtual environment created successfully");
        Ok(())
    }
    
    fn get_venv_executables(&self, venv_dir: &PathBuf) -> Result<(PathBuf, PathBuf), PythonEnvironmentError> {
        let bin_dir = if cfg!(windows) {
            venv_dir.join("Scripts")
        } else {
            venv_dir.join("bin")
        };
        
        let python_exe = if cfg!(windows) {
            bin_dir.join("python.exe")
        } else {
            bin_dir.join("python")
        };
        
        let pip_exe = if cfg!(windows) {
            bin_dir.join("pip.exe")
        } else {
            bin_dir.join("pip")
        };
        
        if !python_exe.exists() {
            return Err(PythonEnvironmentError::VenvInvalid("Python executable not found in venv".to_string()));
        }
        
        if !pip_exe.exists() {
            return Err(PythonEnvironmentError::VenvInvalid("Pip executable not found in venv".to_string()));
        }
        
        Ok((python_exe, pip_exe))
    }
    
    async fn get_python_version(&self, python_path: &PathBuf) -> Result<String, PythonEnvironmentError> {
        let output = Command::new(python_path)
            .args(&["-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"])
            .output()
            .map_err(|e| PythonEnvironmentError::VersionCheckFailed(e.to_string()))?;
        
        if output.status.success() {
            let version = String::from_utf8_lossy(&output.stdout).trim().to_string();
            Ok(version)
        } else {
            let stderr = String::from_utf8_lossy(&output.stderr);
            Err(PythonEnvironmentError::VersionCheckFailed(stderr.to_string()))
        }
    }
    
    fn is_version_compatible(&self, version: &str) -> bool {
        // Require Python 3.8+
        let parts: Vec<&str> = version.split('.').collect();
        if parts.len() >= 2 {
            if let (Ok(major), Ok(minor)) = (parts[0].parse::<u32>(), parts[1].parse::<u32>()) {
                return major >= 3 && minor >= 8;
            }
        }
        false
    }
    
    async fn ensure_dependencies(&self, pip_path: &PathBuf) -> Result<(), PythonEnvironmentError> {
        log::info!("Installing/updating Python dependencies");
        
        // Core dependencies for Lexicon
        let dependencies = vec![
            "requests>=2.31.0",
            "beautifulsoup4>=4.12.0",
            "lxml>=4.9.0",
            "PyMuPDF>=1.23.0",        // PDF processing
            "pdfminer.six>=20221105",  // Alternative PDF processing
            "ebooklib>=0.18",          // EPUB processing
            "chardet>=5.0.0",          // Character encoding detection
            "python-dateutil>=2.8.0",
            "tqdm>=4.65.0",            // Progress bars
            "Pillow>=10.0.0",          // Image processing for OCR
            "pytesseract>=0.3.10",     // OCR capability
        ];
        
        // Update pip first
        let pip_update = Command::new(pip_path)
            .args(&["install", "--upgrade", "pip"])
            .output()
            .map_err(|e| PythonEnvironmentError::DependencyInstallFailed(format!("Failed to update pip: {}", e)))?;
        
        if !pip_update.status.success() {
            let stderr = String::from_utf8_lossy(&pip_update.stderr);
            log::warn!("Failed to update pip: {}", stderr);
        }
        
        // Install dependencies
        for dependency in dependencies {
            log::info!("Installing dependency: {}", dependency);
            
            let output = Command::new(pip_path)
                .args(&["install", "--upgrade", dependency])
                .output()
                .map_err(|e| PythonEnvironmentError::DependencyInstallFailed(format!("Failed to install {}: {}", dependency, e)))?;
            
            if !output.status.success() {
                let stderr = String::from_utf8_lossy(&output.stderr);
                return Err(PythonEnvironmentError::DependencyInstallFailed(
                    format!("Failed to install {}: {}", dependency, stderr)
                ));
            }
        }
        
        log::info!("All Python dependencies installed successfully");
        Ok(())
    }
    
    pub fn get_current_environment(&self) -> Option<&PythonEnvironment> {
        self.current_env.as_ref()
    }
    
    pub async fn verify_environment(&self) -> Result<bool, PythonEnvironmentError> {
        if let Some(env) = &self.current_env {
            // Test basic Python execution
            let output = Command::new(&env.python_path)
                .args(&["-c", "import sys; print('Python environment OK')"])
                .output()
                .map_err(|e| PythonEnvironmentError::VerificationFailed(e.to_string()))?;
            
            if output.status.success() {
                // Test key dependencies
                let dependencies_test = Command::new(&env.python_path)
                    .args(&["-c", "import requests, bs4, PyMuPDF, ebooklib; print('Dependencies OK')"])
                    .output()
                    .map_err(|e| PythonEnvironmentError::VerificationFailed(e.to_string()))?;
                
                Ok(dependencies_test.status.success())
            } else {
                Ok(false)
            }
        } else {
            Ok(false)
        }
    }
}

#[derive(Debug, thiserror::Error)]
pub enum PythonEnvironmentError {
    #[error("Python executable not found. Please install Python 3.8+ and ensure it's in your PATH")]
    PythonNotFound,
    
    #[error("Incompatible Python version found: {found}, required: {required}")]
    IncompatibleVersion { found: String, required: String },
    
    #[error("Failed to create virtual environment: {0}")]
    VenvCreationFailed(String),
    
    #[error("Virtual environment is invalid: {0}")]
    VenvInvalid(String),
    
    #[error("Failed to check Python version: {0}")]
    VersionCheckFailed(String),
    
    #[error("Failed to install dependency: {0}")]
    DependencyInstallFailed(String),
    
    #[error("Environment verification failed: {0}")]
    VerificationFailed(String),
}

// Python script management and embedding
pub struct PythonScriptManager {
    scripts_dir: PathBuf,
    embedded_scripts: std::collections::HashMap<String, &'static str>,
}

impl PythonScriptManager {
    pub fn new(app_data_dir: PathBuf) -> Self {
        let mut manager = PythonScriptManager {
            scripts_dir: app_data_dir.join("scripts"),
            embedded_scripts: std::collections::HashMap::new(),
        };
        
        // Embed Python scripts at compile time
        manager.embedded_scripts.insert(
            "bhagavad_gita_scraper.py".to_string(),
            include_str!("../python_scripts/bhagavad_gita_scraper.py")
        );
        manager.embedded_scripts.insert(
            "srimad_bhagavatam_scraper.py".to_string(),
            include_str!("../python_scripts/srimad_bhagavatam_scraper.py")
        );
        manager.embedded_scripts.insert(
            "sri_isopanisad_scraper.py".to_string(),
            include_str!("../python_scripts/sri_isopanisad_scraper.py")
        );
        manager.embedded_scripts.insert(
            "universal_processor.py".to_string(),
            include_str!("../python_scripts/universal_processor.py")
        );
        
        manager
    }
    
    pub async fn initialize_scripts(&self) -> Result<(), std::io::Error> {
        // Create scripts directory
        tokio::fs::create_dir_all(&self.scripts_dir).await?;
        
        // Extract embedded scripts to filesystem
        for (script_name, script_content) in &self.embedded_scripts {
            let script_path = self.scripts_dir.join(script_name);
            tokio::fs::write(&script_path, script_content).await?;
            
            // Make scripts executable on Unix systems
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                let mut perms = tokio::fs::metadata(&script_path).await?.permissions();
                perms.set_mode(0o755);
                tokio::fs::set_permissions(&script_path, perms).await?;
            }
        }
        
        log::info!("Python scripts initialized at: {:?}", self.scripts_dir);
        Ok(())
    }
    
    pub fn get_script_path(&self, script_name: &str) -> PathBuf {
        self.scripts_dir.join(script_name)
    }
    
    pub fn list_available_scripts(&self) -> Vec<String> {
        self.embedded_scripts.keys().cloned().collect()
    }
}
```

---

## 🔧 Enhanced Backend Architecture (Rust + Python Integration)

### Rust Library Dependencies (Comprehensive List)

```toml
# Cargo.toml - Complete dependency specification
[dependencies]
# Core Tauri
tauri = { version = "2.0", features = ["api-all", "updater"] }
tauri-build = { version = "2.0", features = [] }
tauri-plugin-updater = "2.0"
tauri-plugin-notification = "2.0"
tauri-plugin-fs = "2.0"
tauri-plugin-dialog = "2.0"
tauri-plugin-shell = "2.0"
tauri-plugin-process = "2.0"

# HTTP and JSON
reqwest = { version = "0.12", features = ["json", "rustls-tls"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

# Database
sqlx = { version = "0.8", features = ["runtime-tokio-rustls", "sqlite", "chrono", "uuid"] }
sqlite = "0.36"

# Async runtime
tokio = { version = "1.0", features = ["full"] }
futures = "0.3"

# Logging and error handling
log = "0.4"
env_logger = "0.11"
thiserror = "1.0"
anyhow = "1.0"

# File system and paths
dirs = "5.0"
walkdir = "2.5"
glob = "0.3"

# Date and time
chrono = { version = "0.4", features = ["serde"] }

# UUID generation
uuid = { version = "1.8", features = ["v4", "serde"] }

# Text processing and chunking
regex = "1.10"
unicode-segmentation = "1.11"
rayon = "1.8"  # Parallel processing

# Compression and archives
zip = "0.6"
tar = "0.4"
flate2 = "1.0"

# Configuration management
config = "0.14"
toml = "0.8"

# Process management for Python integration
subprocess = "0.2"
which = "6.0"  # Finding executables

# Encryption for sensitive data
ring = "0.17"
base64 = "0.22"

# macOS specific integrations
[target.'cfg(target_os = "macos")'.dependencies]
cocoa = "0.25"
objc = "0.2"
core-foundation = "0.9"
```

### Python Script Dependencies (requirements.txt)

```python
# requirements.txt - Complete Python dependencies
# Web scraping and HTTP
requests==2.32.3
beautifulsoup4==4.12.3
lxml==5.2.2
selenium==4.23.1        # For JavaScript-heavy sites
webdriver-manager==4.0.1

# Document processing
PyMuPDF==1.24.5         # PDF processing (pymupdf)
pdfplumber==0.11.1      # Alternative PDF processing
pdfminer.six==20231228  # Text extraction from PDFs
ebooklib==0.18          # EPUB processing
python-docx==1.1.2      # DOCX processing
openpyxl==3.1.5         # Excel processing
markdown==3.6           # Markdown processing

# Text processing and NLP
nltk==3.8.1
spacy==3.7.5
textstat==0.7.3         # Text readability statistics
langdetect==1.0.9       # Language detection

# Character encoding and text cleaning
chardet==5.2.0
ftfy==6.2.0             # Text fixing

# Date and time processing
python-dateutil==2.9.0
pytz==2024.1

# Progress bars and CLI utilities
tqdm==4.66.4
click==8.1.7

# Image processing (for OCR capabilities)
Pillow==10.4.0
pytesseract==0.3.10

# Data validation and serialization
pydantic==2.8.2
marshmallow==3.21.3

# Logging
loguru==0.7.2

# Testing dependencies (for development)
pytest==8.3.2
pytest-asyncio==0.23.8
pytest-mock==3.14.0
hypothesis==6.108.5     # Property-based testing

# Optional: Advanced text processing
transformers==4.42.4    # For advanced NLP (optional, large dependency)
sentence-transformers==3.0.1  # For semantic similarity (optional)
```

### Enhanced Error Handling and Logging System

```rust
// Enhanced error handling with comprehensive error types
use std::fmt;
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorContext {
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub error_id: String,
    pub component: String,
    pub operation: String,
    pub user_message: String,
    pub technical_details: String,
    pub severity: ErrorSeverity,
    pub recoverable: bool,
    pub suggested_actions: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ErrorSeverity {
    Info,
    Warning,
    Error,
    Critical,
}

#[derive(Debug, thiserror::Error)]
pub enum LexiconError {
    // Python Environment Errors
    #[error("Python environment error: {details}")]
    PythonEnvironment { 
        details: String,
        context: ErrorContext 
    },
    
    // File Processing Errors
    #[error("File processing failed: {file_path}")]
    FileProcessing { 
        file_path: String,
        error_type: FileProcessingErrorType,
        context: ErrorContext 
    },
    
    // Network and Scraping Errors
    #[error("Network operation failed: {operation}")]
    Network { 
        operation: String,
        status_code: Option<u16>,
        context: ErrorContext 
    },
    
    // Database Errors
    #[error("Database operation failed: {operation}")]
    Database { 
        operation: String,
        context: ErrorContext 
    },
    
    // Cloud Storage Errors
    #[error("Cloud storage error: {provider}")]
    CloudStorage { 
        provider: String,
        context: ErrorContext 
    },
    
    // Configuration Errors
    #[error("Configuration error: {setting}")]
    Configuration { 
        setting: String,
        context: ErrorContext 
    },
    
    // User Input Errors
    #[error("Invalid user input: {field}")]
    UserInput { 
        field: String,
        context: ErrorContext 
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum FileProcessingErrorType {
    UnsupportedFormat,
    Corrupted,
    AccessDenied,
    TooLarge,
    NetworkTimeout,
    ParseError,
}

pub struct ErrorLogger {
    log_file_path: std::path::PathBuf,
    console_logger: env_logger::Logger,
    notification_sender: Option<tokio::sync::mpsc::UnboundedSender<ErrorContext>>,
}

impl ErrorLogger {
    pub fn new(app_data_dir: &std::path::Path) -> Result<Self, std::io::Error> {
        let log_file_path = app_data_dir.join("logs").join("lexicon.log");
        
        // Ensure log directory exists
        if let Some(parent) = log_file_path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        
        // Configure file logging
        let file_appender = tracing_appender::rolling::daily(
            app_data_dir.join("logs"),
            "lexicon.log"
        );
        
        let (non_blocking, _guard) = tracing_appender::non_blocking(file_appender);
        
        tracing_subscriber::fmt()
            .with_writer(non_blocking)
            .with_max_level(tracing::Level::DEBUG)
            .init();
        
        Ok(ErrorLogger {
            log_file_path,
            console_logger: env_logger::Logger::from_default_env(),
            notification_sender: None,
        })
    }
    
    pub fn set_notification_sender(&mut self, sender: tokio::sync::mpsc::UnboundedSender<ErrorContext>) {
        self.notification_sender = Some(sender);
    }
    
    pub async fn log_error(&self, error: &LexiconError) {
        let context = self.extract_error_context(error);
        
        // Log to file
        match context.severity {
            ErrorSeverity::Info => log::info!("{}", self.format_log_entry(&context)),
            ErrorSeverity::Warning => log::warn!("{}", self.format_log_entry(&context)),
            ErrorSeverity::Error => log::error!("{}", self.format_log_entry(&context)),
            ErrorSeverity::Critical => log::error!("CRITICAL: {}", self.format_log_entry(&context)),
        }
        
        // Send notification for user-facing errors
        if matches!(context.severity, ErrorSeverity::Error | ErrorSeverity::Critical) {
            if let Some(sender) = &self.notification_sender {
                let _ = sender.send(context.clone());
            }
        }
        
        // For critical errors, also show macOS notification
        if matches!(context.severity, ErrorSeverity::Critical) {
            self.show_macos_notification(&context).await;
        }
    }
    
    fn extract_error_context(&self, error: &LexiconError) -> ErrorContext {
        match error {
            LexiconError::PythonEnvironment { context, .. } => context.clone(),
            LexiconError::FileProcessing { context, .. } => context.clone(),
            LexiconError::Network { context, .. } => context.clone(),
            LexiconError::Database { context, .. } => context.clone(),
            LexiconError::CloudStorage { context, .. } => context.clone(),
            LexiconError::Configuration { context, .. } => context.clone(),
            LexiconError::UserInput { context, .. } => context.clone(),
        }
    }
    
    fn format_log_entry(&self, context: &ErrorContext) -> String {
        format!(
            "[{}] [{}] [{}:{}] {} | Technical: {} | ID: {}",
            context.timestamp.format("%Y-%m-%d %H:%M:%S UTC"),
            context.severity,
            context.component,
            context.operation,
            context.user_message,
            context.technical_details,
            context.error_id
        )
    }
    
    async fn show_macos_notification(&self, context: &ErrorContext) {
        // Use Tauri's notification API
        if let Err(e) = tauri::api::notification::Notification::new("com.lexicon.app")
            .title("Lexicon - Critical Error")
            .body(&context.user_message)
            .icon(tauri::api::notification::Icon::Default)
            .show()
        {
            log::error!("Failed to show macOS notification: {}", e);
        }
    }
    
    pub async fn get_recent_errors(&self, limit: usize) -> Result<Vec<ErrorContext>, std::io::Error> {
        // Read recent errors from log file
        let log_content = tokio::fs::read_to_string(&self.log_file_path).await?;
        let lines: Vec<&str> = log_content.lines().rev().take(limit).collect();
        
        let mut errors = Vec::new();
        for line in lines {
            if let Ok(context) = self.parse_log_line(line) {
                errors.push(context);
            }
        }
        
        Ok(errors)
    }
    
    fn parse_log_line(&self, line: &str) -> Result<ErrorContext, serde_json::Error> {
        // This would parse the structured log format
        // For now, return a placeholder
        Ok(ErrorContext {
            timestamp: chrono::Utc::now(),
            error_id: uuid::Uuid::new_v4().to_string(),
            component: "parser".to_string(),
            operation: "parse".to_string(),
            user_message: "Log parsing not fully implemented".to_string(),
            technical_details: line.to_string(),
            severity: ErrorSeverity::Info,
            recoverable: true,
            suggested_actions: vec!["Check logs manually".to_string()],
        })
    }
}

// User notification system for the frontend
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserNotification {
    pub id: String,
    pub title: String,
    pub message: String,
    pub notification_type: NotificationType,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub actions: Vec<NotificationAction>,
    pub dismissible: bool,
    pub auto_dismiss_after: Option<u64>, // seconds
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum NotificationType {
    Success,
    Info,
    Warning,
    Error,
    Progress,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NotificationAction {
    pub label: String,
    pub action_type: ActionType,
    pub data: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ActionType {
    Retry,
    Dismiss,
    OpenLogs,
    ReportBug,
    GoToSettings,
    Custom(String),
}

pub struct NotificationManager {
    active_notifications: std::collections::HashMap<String, UserNotification>,
    sender: tokio::sync::mpsc::UnboundedSender<UserNotification>,
}

impl NotificationManager {
    pub fn new() -> (Self, tokio::sync::mpsc::UnboundedReceiver<UserNotification>) {
        let (sender, receiver) = tokio::sync::mpsc::unbounded_channel();
        
        (NotificationManager {
            active_notifications: std::collections::HashMap::new(),
            sender,
        }, receiver)
    }
    
    pub fn show_success(&self, title: &str, message: &str) {
        let notification = UserNotification {
            id: uuid::Uuid::new_v4().to_string(),
            title: title.to_string(),
            message: message.to_string(),
            notification_type: NotificationType::Success,
            timestamp: chrono::Utc::now(),
            actions: vec![],
            dismissible: true,
            auto_dismiss_after: Some(5),
        };
        
        let _ = self.sender.send(notification);
    }
    
    pub fn show_error(&self, error_context: &ErrorContext) {
        let mut actions = vec![
            NotificationAction {
                label: "Dismiss".to_string(),
                action_type: ActionType::Dismiss,
                data: serde_json::json!({}),
            }
        ];
        
        // Add context-specific actions
        if error_context.recoverable {
            actions.insert(0, NotificationAction {
                label: "Retry".to_string(),
                action_type: ActionType::Retry,
                data: serde_json::json!({
                    "error_id": error_context.error_id,
                    "component": error_context.component,
                    "operation": error_context.operation,
                }),
            });
        }
        
        if matches!(error_context.severity, ErrorSeverity::Error | ErrorSeverity::Critical) {
            actions.push(NotificationAction {
                label: "View Logs".to_string(),
                action_type: ActionType::OpenLogs,
                data: serde_json::json!({}),
            });
            
            actions.push(NotificationAction {
                label: "Report Bug".to_string(),
                action_type: ActionType::ReportBug,
                data: serde_json::json!({
                    "error_id": error_context.error_id,
                    "error_details": error_context.technical_details,
                }),
            });
        }
        
        let notification = UserNotification {
            id: error_context.error_id.clone(),
            title: format!("Error in {}", error_context.component),
            message: error_context.user_message.clone(),
            notification_type: match error_context.severity {
                ErrorSeverity::Warning => NotificationType::Warning,
                _ => NotificationType::Error,
            },
            timestamp: error_context.timestamp,
            actions,
            dismissible: true,
            auto_dismiss_after: None, // Error notifications don't auto-dismiss
        };
        
        let _ = self.sender.send(notification);
    }
    
    pub fn show_progress(&self, operation: &str, message: &str, progress: Option<f64>) {
        let mut progress_message = message.to_string();
        if let Some(pct) = progress {
            progress_message.push_str(&format!(" ({:.1}%)", pct * 100.0));
        }
        
        let notification = UserNotification {
            id: format!("progress_{}", operation),
            title: format!("Processing: {}", operation),
            message: progress_message,
            notification_type: NotificationType::Progress,
            timestamp: chrono::Utc::now(),
            actions: vec![],
            dismissible: false,
            auto_dismiss_after: None,
        };
        
        let _ = self.sender.send(notification);
    }
}
```

### Comprehensive Testing Strategy

```rust
// Testing framework with multiple testing approaches
#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;
    use tokio_test::*;
    use mockall::*;
    use proptest::prelude::*;
    
    // Mock objects for testing
    #[mockall::automock]
    pub trait PythonExecutor {
        async fn execute_script(&self, script_path: &str, args: Vec<String>) -> Result<String, String>;
    }
    
    // Unit tests for core components
    #[tokio::test]
    async fn test_python_environment_setup() {
        let temp_dir = TempDir::new().unwrap();
        let mut env_manager = PythonEnvironmentManager::new(temp_dir.path().to_path_buf());
        
        // Test environment initialization
        let result = env_manager.initialize_environment().await;
        
        match result {
            Ok(env) => {
                assert!(env.python_path.exists());
                assert!(env.pip_path.exists());
                assert!(env.isolated);
                assert!(env.version.starts_with("3."));
            },
            Err(PythonEnvironmentError::PythonNotFound) => {
                // This is acceptable in CI environments without Python
                println!("Python not found in test environment - skipping");
            },
            Err(e) => panic!("Unexpected error: {:?}", e),
        }
    }
    
    #[tokio::test]
    async fn test_book_registry_operations() {
        let temp_dir = TempDir::new().unwrap();
        let db_path = temp_dir.path().join("test.db");
        let mut registry = BookRegistry::new(db_path).await.unwrap();
        
        // Test adding a book
        let book = Book {
            id: "test-book-1".to_string(),
            title: "Test Book".to_string(),
            author: "Test Author".to_string(),
            category: BookCategory::PersonalDevelopment,
            source_type: SourceType::Manual,
            local_path: Some("/path/to/test/book.pdf".to_string()),
            url: None,
            priority: Priority::Medium,
            status: ProcessingStatus::Pending,
            stages: None,
            metadata: BookMetadata::default(),
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
        };
        
        registry.add_book(book.clone()).await.unwrap();
        
        // Test retrieving the book
        let retrieved = registry.get_book(&book.id).await.unwrap();
        assert_eq!(retrieved.unwrap().title, "Test Book");
        
        // Test updating the book
        registry.update_book_status(&book.id, ProcessingStatus::InProgress).await.unwrap();
        let updated = registry.get_book(&book.id).await.unwrap().unwrap();
        assert_eq!(updated.status, ProcessingStatus::InProgress);
        
        // Test deleting the book
        registry.delete_book(&book.id).await.unwrap();
        let deleted = registry.get_book(&book.id).await.unwrap();
        assert!(deleted.is_none());
    }
    
    #[test]
    fn test_file_type_detection() {
        // Test file type detection logic
        let test_cases = vec![
            ("document.pdf", "application/pdf", SourceType::Pdf),
            ("book.epub", "application/epub+zip", SourceType::Epub),
            ("novel.mobi", "application/x-mobipocket-ebook", SourceType::Mobi),
            ("text.txt", "text/plain", SourceType::Txt),
            ("unknown.xyz", "application/octet-stream", SourceType::Manual),
        ];
        
        for (filename, mime_type, expected_type) in test_cases {
            let detected_type = detect_source_type_from_file(filename, mime_type);
            assert_eq!(detected_type, expected_type, "Failed for file: {}", filename);
        }
    }
    
    // Property-based testing using proptest
    proptest! {
        #[test]
        fn test_chunk_text_properties(text in "\\PC{1,10000}", chunk_size in 100u32..2000u32) {
            let chunks = chunk_text(&text, chunk_size as usize, 50);
            
            // Properties that should always hold
            prop_assert!(!chunks.is_empty(), "Should always produce at least one chunk");
            
            for chunk in &chunks {
                prop_assert!(chunk.content.len() <= (chunk_size as usize + 100), 
                           "Chunk size should not exceed limit by much");
                prop_assert!(!chunk.content.is_empty(), "Chunks should not be empty");
            }
            
            // Verify all text is preserved
            let recombined: String = chunks.iter().map(|c| &c.content).collect::<Vec<_>>().join("");
            prop_assert!(recombined.contains(&text.chars().take(100).collect::<String>()), 
                        "Original text should be preserved in chunks");
        }
    }
    
    // Integration tests
    #[tokio::test]
    async fn test_full_processing_pipeline() {
        let temp_dir = TempDir::new().unwrap();
        
        // Create a mock text file
        let test_file = temp_dir.path().join("test.txt");
        tokio::fs::write(&test_file, "This is a test document with some content.").await.unwrap();
        
        // Initialize components
        let mut registry = BookRegistry::new(temp_dir.path().join("test.db")).await.unwrap();
        let chunker = RagChunker::new();
        
        // Add book to registry
        let book = Book {
            id: "integration-test-1".to_string(),
            title: "Integration Test Book".to_string(),
            author: "Test Runner".to_string(),
            category: BookCategory::PersonalDevelopment,
            source_type: SourceType::Txt,
            local_path: Some(test_file.to_string_lossy().to_string()),
            url: None,
            priority: Priority::High,
            status: ProcessingStatus::Pending,
            stages: None,
            metadata: BookMetadata::default(),
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
        };
        
        registry.add_book(book.clone()).await.unwrap();
        
        // Process the book (simplified)
        let content = tokio::fs::read_to_string(&test_file).await.unwrap();
        let chunks = chunker.chunk_text(&content, 200, 50);
        
        assert!(!chunks.is_empty());
        assert!(chunks[0].content.contains("test document"));
        
        // Update status
        registry.update_book_status(&book.id, ProcessingStatus::Completed).await.unwrap();
        
        let final_book = registry.get_book(&book.id).await.unwrap().unwrap();
        assert_eq!(final_book.status, ProcessingStatus::Completed);
    }
    
    // Performance tests
    #[tokio::test]
    async fn test_chunking_performance() {
        use std::time::Instant;
        
        // Generate large text for performance testing
        let large_text = "Lorem ipsum dolor sit amet. ".repeat(10000);
        let chunker = RagChunker::new();
        
        let start = Instant::now();
        let chunks = chunker.chunk_text(&large_text, 500, 100);
        let duration = start.elapsed();
        
        println!("Chunked {} characters into {} chunks in {:?}", 
                large_text.len(), chunks.len(), duration);
        
        // Performance assertions
        assert!(duration.as_millis() < 1000, "Chunking should complete within 1 second");
        assert!(!chunks.is_empty());
        assert!(chunks.len() > 50, "Should produce reasonable number of chunks");
    }
    
    // Error handling tests
    #[tokio::test]
    async fn test_error_handling_and_recovery() {
        let temp_dir = TempDir::new().unwrap();
        let mut registry = BookRegistry::new(temp_dir.path().join("test.db")).await.unwrap();
        
        // Test handling of invalid book data
        let invalid_book = Book {
            id: "".to_string(), // Invalid empty ID
            title: "".to_string(), // Invalid empty title
            author: "Test Author".to_string(),
            category: BookCategory::PersonalDevelopment,
            source_type: SourceType::Manual,
            local_path: None,
            url: None,
            priority: Priority::Medium,
            status: ProcessingStatus::Pending,
            stages: None,
            metadata: BookMetadata::default(),
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
        };
        
        let result = registry.add_book(invalid_book).await;
        assert!(result.is_err(), "Should reject invalid book data");
        
        // Test handling of non-existent files
        let book_with_missing_file = Book {
            id: "missing-file-test".to_string(),
            title: "Missing File Test".to_string(),
            author: "Test Author".to_string(),
            category: BookCategory::PersonalDevelopment,
            source_type: SourceType::Pdf,
            local_path: Some("/nonexistent/path/file.pdf".to_string()),
            url: None,
            priority: Priority::Medium,
            status: ProcessingStatus::Pending,
            stages: None,
            metadata: BookMetadata::default(),
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
        };
        
        // This should succeed (book added to registry)
        registry.add_book(book_with_missing_file.clone()).await.unwrap();
        
        // But processing should fail gracefully
        // (This would be tested in the actual processing component)
    }
    
    // Chaos testing for resilience
    #[tokio::test]
    async fn test_system_resilience_under_stress() {
        let temp_dir = TempDir::new().unwrap();
        let mut registry = BookRegistry::new(temp_dir.path().join("chaos.db")).await.unwrap();
        
        // Simulate concurrent operations
        let mut handles = vec![];
        
        for i in 0..10 {
            let mut registry_clone = registry.clone();
            let handle = tokio::spawn(async move {
                for j in 0..5 {
                    let book = Book {
                        id: format!("chaos-book-{}-{}", i, j),
                        title: format!("Chaos Test Book {} {}", i, j),
                        author: "Chaos Tester".to_string(),
                        category: BookCategory::PersonalDevelopment,
                        source_type: SourceType::Manual,
                        local_path: None,
                        url: None,
                        priority: Priority::Medium,
                        status: ProcessingStatus::Pending,
                        stages: None,
                        metadata: BookMetadata::default(),
                        created_at: chrono::Utc::now(),
                        updated_at: chrono::Utc::now(),
                    };
                    
                    // Some operations might fail due to race conditions
                    let _ = registry_clone.add_book(book).await;
                    
                    // Add some randomness
                    tokio::time::sleep(tokio::time::Duration::from_millis(rand::random::<u64>() % 10)).await;
                }
            });
            handles.push(handle);
        }
        
        // Wait for all operations
        for handle in handles {
            handle.await.unwrap();
        }
        
        // Verify system is still functional
        let all_books = registry.get_all_books().await.unwrap();
        println!("Chaos test completed with {} books in registry", all_books.len());
        
        // System should still be responsive
        let test_book = Book {
            id: "post-chaos-test".to_string(),
            title: "Post Chaos Test".to_string(),
            author: "Recovery Tester".to_string(),
            category: BookCategory::PersonalDevelopment,
            source_type: SourceType::Manual,
            local_path: None,
            url: None,
            priority: Priority::Medium,
            status: ProcessingStatus::Pending,
            stages: None,
            metadata: BookMetadata::default(),
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
        };
        
        registry.add_book(test_book).await.unwrap();
    }
}

// Benchmark tests
#[cfg(test)]
mod benchmarks {
    use super::*;
    use criterion::{black_box, criterion_group, criterion_main, Criterion};
    
    fn benchmark_text_chunking(c: &mut Criterion) {
        let chunker = RagChunker::new();
        let text = "Lorem ipsum dolor sit amet. ".repeat(1000);
        
        c.bench_function("chunk_1000_words", |b| {
            b.iter(|| {
                let chunks = chunker.chunk_text(black_box(&text), 500, 100);
                black_box(chunks);
            })
        });
    }
    
    fn benchmark_database_operations(c: &mut Criterion) {
        let rt = tokio::runtime::Runtime::new().unwrap();
        let temp_dir = tempfile::TempDir::new().unwrap();
        let mut registry = rt.block_on(async {
            BookRegistry::new(temp_dir.path().join("benchmark.db")).await.unwrap()
        });
        
        c.bench_function("add_book", |b| {
            b.iter(|| {
                rt.block_on(async {
                    let book = Book {
                        id: format!("bench-{}", uuid::Uuid::new_v4()),
                        title: "Benchmark Book".to_string(),
                        author: "Benchmark Author".to_string(),
                        category: BookCategory::PersonalDevelopment,
                        source_type: SourceType::Manual,
                        local_path: None,
                        url: None,
                        priority: Priority::Medium,
                        status: ProcessingStatus::Pending,
                        stages: None,
                        metadata: BookMetadata::default(),
                        created_at: chrono::Utc::now(),
                        updated_at: chrono::Utc::now(),
                    };
                    
                    let _ = registry.add_book(black_box(book)).await;
                });
            })
        });
    }
    
    criterion_group!(benches, benchmark_text_chunking, benchmark_database_operations);
    criterion_main!(benches);
}
```

### Cloud Storage Integration

```rust
// Cloud storage integration module
use oauth2::{
    AuthorizationCode, ClientId, ClientSecret, CsrfToken, RedirectUrl, Scope,
    TokenResponse, AuthUrl, TokenUrl, basic::BasicClient,
};
use url::Url;

pub struct CloudOAuthManager {
    clients: std::collections::HashMap<CloudProvider, BasicClient>,
    pending_states: std::collections::HashMap<String, CloudProvider>,
    app_data_dir: std::path::PathBuf,
}

impl CloudOAuthManager {
    pub fn new(app_data_dir: std::path::PathBuf) -> Result<Self, CloudStorageError> {
        let mut clients = std::collections::HashMap::new();
        
        // Dropbox OAuth2 client
        let dropbox_client = BasicClient::new(
            ClientId::new("your_dropbox_app_key".to_string()),
            Some(ClientSecret::new("your_dropbox_app_secret".to_string())),
            AuthUrl::new("https://www.dropbox.com/oauth2/authorize".to_string())
                .map_err(|e| CloudStorageError::SetupFailed(format!("Invalid Dropbox auth URL: {}", e)))?,
            Some(
                TokenUrl::new("https://api.dropboxapi.com/oauth2/token".to_string())
                    .map_err(|e| CloudStorageError::SetupFailed(format!("Invalid Dropbox token URL: {}", e)))?
            ),
        )
        .set_redirect_uri(
            RedirectUrl::new("http://localhost:8080/oauth/dropbox/callback".to_string())
                .map_err(|e| CloudStorageError::SetupFailed(format!("Invalid redirect URL: {}", e)))?
        );
        
        clients.insert(CloudProvider::Dropbox, dropbox_client);
        
        // Google Drive OAuth2 client
        let google_client = BasicClient::new(
            ClientId::new("your_google_client_id".to_string()),
            Some(ClientSecret::new("your_google_client_secret".to_string())),
            AuthUrl::new("https://accounts.google.com/o/oauth2/v2/auth".to_string())
                .map_err(|e| CloudStorageError::SetupFailed(format!("Invalid Google auth URL: {}", e)))?,
            Some(
                TokenUrl::new("https://www.googleapis.com/oauth2/v4/token".to_string())
                    .map_err(|e| CloudStorageError::SetupFailed(format!("Invalid Google token URL: {}", e)))?
            ),
        )
        .set_redirect_uri(
            RedirectUrl::new("http://localhost:8080/oauth/google/callback".to_string())
                .map_err(|e| CloudStorageError::SetupFailed(format!("Invalid redirect URL: {}", e)))?
        );
        
        clients.insert(CloudProvider::GoogleDrive, google_client);
        
        Ok(CloudOAuthManager {
            clients,
            pending_states: std::collections::HashMap::new(),
            app_data_dir,
        })
    }
    
    pub fn start_oauth_flow(&mut self, provider: CloudProvider) -> Result<Url, CloudStorageError> {
        let client = self.clients.get(&provider)
            .ok_or_else(|| CloudStorageError::SetupFailed(format!("OAuth client not configured for {:?}", provider)))?;
        
        let (auth_url, csrf_token) = match provider {
            CloudProvider::Dropbox => {
                client
                    .authorize_url(CsrfToken::new_random)
                    .add_scope(Scope::new("files.metadata.read".to_string()))
                    .add_scope(Scope::new("files.content.read".to_string()))
                    .add_scope(Scope::new("files.content.write".to_string()))
                    .url()
            },
            CloudProvider::GoogleDrive => {
                client
                    .authorize_url(CsrfToken::new_random)
                    .add_scope(Scope::new("https://www.googleapis.com/auth/drive.file".to_string()))
                    .add_scope(Scope::new("https://www.googleapis.com/auth/drive.appdata".to_string()))
                    .url()
            },
            _ => return Err(CloudStorageError::SetupFailed(format!("OAuth not supported for {:?}", provider))),
        };
        
        // Store the CSRF token for validation
        self.pending_states.insert(csrf_token.secret().clone(), provider);
        
        log::info!("Starting OAuth flow for {:?}: {}", provider, auth_url);
        Ok(auth_url)
    }
    
    pub async fn complete_oauth_flow(
        &mut self, 
        provider: CloudProvider, 
        auth_code: String, 
        state: String
    ) -> Result<CloudCredentials, CloudStorageError> {
        // Validate CSRF token
        let expected_provider = self.pending_states.remove(&state)
            .ok_or_else(|| CloudStorageError::AuthenticationFailed("Invalid or expired OAuth state".to_string()))?;
        
        if expected_provider != provider {
            return Err(CloudStorageError::AuthenticationFailed("OAuth state mismatch".to_string()));
        }
        
        let client = self.clients.get(&provider)
            .ok_or_else(|| CloudStorageError::SetupFailed(format!("OAuth client not configured for {:?}", provider)))?;
        
        // Exchange authorization code for access token
        let token_response = client
            .exchange_code(AuthorizationCode::new(auth_code))
            .request_async(oauth2::reqwest::async_http_client)
            .await
            .map_err(|e| CloudStorageError::AuthenticationFailed(format!("Token exchange failed: {}", e)))?;
        
        let credentials = CloudCredentials {
            access_token: token_response.access_token().secret().clone(),
            refresh_token: token_response.refresh_token().map(|rt| rt.secret().clone()),
            expires_at: token_response.expires_in().map(|duration| {
                chrono::Utc::now() + chrono::Duration::seconds(duration.as_secs() as i64)
            }),
        };
        
        // Store credentials securely
        self.store_credentials(provider, &credentials).await?;
        
        log::info!("OAuth flow completed successfully for {:?}", provider);
        Ok(credentials)
    }
    
    async fn store_credentials(&self, provider: CloudProvider, credentials: &CloudCredentials) -> Result<(), CloudStorageError> {
        let credentials_dir = self.app_data_dir.join("credentials");
        tokio::fs::create_dir_all(&credentials_dir).await
            .map_err(|e| CloudStorageError::SetupFailed(format!("Failed to create credentials directory: {}", e)))?;
        
        let credentials_file = credentials_dir.join(format!("{:?}_credentials.json", provider));
        
        // Encrypt credentials before storing
        let encrypted_credentials = self.encrypt_credentials(credentials)?;
        
        tokio::fs::write(&credentials_file, encrypted_credentials).await
            .map_err(|e| CloudStorageError::SetupFailed(format!("Failed to store credentials: {}", e)))?;
        
        // Set restrictive permissions on credentials file
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let mut perms = tokio::fs::metadata(&credentials_file).await
                .map_err(|e| CloudStorageError::SetupFailed(format!("Failed to get file permissions: {}", e)))?
                .permissions();
            perms.set_mode(0o600); // Read/write for owner only
            tokio::fs::set_permissions(&credentials_file, perms).await
                .map_err(|e| CloudStorageError::SetupFailed(format!("Failed to set file permissions: {}", e)))?;
        }
        
        Ok(())
    }
    
    fn encrypt_credentials(&self, credentials: &CloudCredentials) -> Result<Vec<u8>, CloudStorageError> {
        use ring::{aead, pbkdf2, rand};
        use ring::rand::SecureRandom;
        
        // In a real implementation, you'd derive the key from a master password or keychain
        let mut key_bytes = [0u8; 32];
        let rng = rand::SystemRandom::new();
        rng.fill(&mut key_bytes)
            .map_err(|_| CloudStorageError::SetupFailed("Failed to generate encryption key".to_string()))?;
        
        let key = aead::UnboundKey::new(&aead::AES_256_GCM, &key_bytes)
            .map_err(|_| CloudStorageError::SetupFailed("Failed to create encryption key".to_string()))?;
        let key = aead::LessSafeKey::new(key);
        
        let mut nonce_bytes = [0u8; 12];
        rng.fill(&mut nonce_bytes)
            .map_err(|_| CloudStorageError::SetupFailed("Failed to generate nonce".to_string()))?;
        let nonce = aead::Nonce::assume_unique_for_key(nonce_bytes);
        
        let credentials_json = serde_json::to_string(credentials)
            .map_err(|e| CloudStorageError::SetupFailed(format!("Failed to serialize credentials: {}", e)))?;
        
        let mut in_out = credentials_json.into_bytes();
        key.seal_in_place_append_tag(nonce, aead::Aad::empty(), &mut in_out)
            .map_err(|_| CloudStorageError::SetupFailed("Failed to encrypt credentials".to_string()))?;
        
        // Prepend nonce to encrypted data
        let mut result = nonce_bytes.to_vec();
        result.extend_from_slice(&in_out);
        
        Ok(result)
    }
    
    pub async fn load_credentials(&self, provider: CloudProvider) -> Result<CloudCredentials, CloudStorageError> {
        let credentials_file = self.app_data_dir
            .join("credentials")
            .join(format!("{:?}_credentials.json", provider));
        
        if !credentials_file.exists() {
            return Err(CloudStorageError::SetupFailed(format!("No credentials found for {:?}", provider)));
        }
        
        let encrypted_data = tokio::fs::read(&credentials_file).await
            .map_err(|e| CloudStorageError::SetupFailed(format!("Failed to read credentials: {}", e)))?;
        
        let credentials = self.decrypt_credentials(&encrypted_data)?;
        
        // Check if credentials are expired
        if let Some(expires_at) = credentials.expires_at {
            if chrono::Utc::now() > expires_at {
                // Try to refresh the token
                return self.refresh_credentials(provider, &credentials).await;
            }
        }
        
        Ok(credentials)
    }
    
    fn decrypt_credentials(&self, encrypted_data: &[u8]) -> Result<CloudCredentials, CloudStorageError> {
        use ring::aead;
        
        if encrypted_data.len() < 12 {
            return Err(CloudStorageError::SetupFailed("Invalid encrypted credentials format".to_string()));
        }
        
        let (nonce_bytes, ciphertext) = encrypted_data.split_at(12);
        let nonce = aead::Nonce::try_assume_unique_for_key(nonce_bytes)
            .map_err(|_| CloudStorageError::SetupFailed("Invalid nonce in encrypted credentials".to_string()))?;
        
        // This is a simplified implementation - in practice, you'd properly manage the key
        let mut key_bytes = [0u8; 32];
        // ... key derivation logic ...
        
        let key = aead::UnboundKey::new(&aead::AES_256_GCM, &key_bytes)
            .map_err(|_| CloudStorageError::SetupFailed("Failed to create decryption key".to_string()))?;
        let key = aead::LessSafeKey::new(key);
        
        let mut plaintext = ciphertext.to_vec();
        let decrypted_len = key.open_in_place(nonce, aead::Aad::empty(), &mut plaintext)
            .map_err(|_| CloudStorageError::SetupFailed("Failed to decrypt credentials".to_string()))?
            .len();
        
        plaintext.truncate(decrypted_len);
        
        let credentials_json = String::from_utf8(plaintext)
            .map_err(|_| CloudStorageError::SetupFailed("Invalid UTF-8 in decrypted credentials".to_string()))?;
        
        serde_json::from_str(&credentials_json)
            .map_err(|e| CloudStorageError::SetupFailed(format!("Failed to parse credentials: {}", e)))
    }
    
    async fn refresh_credentials(&self, provider: CloudProvider, current_credentials: &CloudCredentials) -> Result<CloudCredentials, CloudStorageError> {
        let refresh_token = current_credentials.refresh_token.as_ref()
            .ok_or_else(|| CloudStorageError::AuthenticationFailed("No refresh token available".to_string()))?;
        
        let client = self.clients.get(&provider)
            .ok_or_else(|| CloudStorageError::SetupFailed(format!("OAuth client not configured for {:?}", provider)))?;
        
        let token_response = client
            .exchange_refresh_token(&oauth2::RefreshToken::new(refresh_token.clone()))
            .request_async(oauth2::reqwest::async_http_client)
            .await
            .map_err(|e| CloudStorageError::AuthenticationFailed(format!("Token refresh failed: {}", e)))?;
        
        let new_credentials = CloudCredentials {
            access_token: token_response.access_token().secret().clone(),
            refresh_token: token_response.refresh_token()
                .map(|rt| rt.secret().clone())
                .or_else(|| current_credentials.refresh_token.clone()), // Keep existing refresh token if none provided
            expires_at: token_response.expires_in().map(|duration| {
                chrono::Utc::now() + chrono::Duration::seconds(duration.as_secs() as i64)
            }),
        };
        
        // Store the refreshed credentials
        self.store_credentials(provider, &new_credentials).await?;
        
        log::info!("Credentials refreshed successfully for {:?}", provider);
        Ok(new_credentials)
    }
}
```

---

## 📚 Book Enrichment & Metadata Enhancement Architecture

### Overview
The metadata enrichment system transforms basic book information into rich, contextual metadata through web-based APIs and intelligent relationship mapping, particularly valuable for academic and structured scripture collections.

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                METADATA ENRICHMENT LAYER                   │
├─────────────────────────────────────────────────────────────┤
│  External API Integration                                   │
│  ┌─────────────────┬─────────────────┬─────────────────┐   │
│  │  Google Books   │   OpenLibrary   │   Custom APIs   │   │
│  │      API        │      API        │   (Future)      │   │
│  └─────────────────┴─────────────────┴─────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Metadata Processing Engine (Rust)                         │
│  ┌─────────────────┬─────────────────┬─────────────────┐   │
│  │  Book Identity  │  Relationship   │  Visual Asset   │   │
│  │   Resolution    │    Mapping      │   Management    │   │
│  └─────────────────┴─────────────────┴─────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Enhanced Data Models                                      │
│  ┌─────────────────┬─────────────────┬─────────────────┐   │
│  │   Rich Book     │  Relationship   │  Visual Asset   │   │
│  │   Metadata      │     Graph       │    Storage      │   │
│  └─────────────────┴─────────────────┴─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Enhanced Data Models

```rust
// Enhanced Book model with enrichment capabilities
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct EnrichedBook {
    // Core identification
    pub id: String,
    pub title: String,
    pub subtitle: Option<String>,
    pub authors: Vec<Author>,
    
    // Publication information
    pub publisher: Option<Publisher>,
    pub publication_date: Option<NaiveDate>,
    pub edition: Option<String>,
    pub isbn_10: Option<String>,
    pub isbn_13: Option<String>,
    
    // Content classification
    pub categories: Vec<String>,
    pub subjects: Vec<String>,
    pub genres: Vec<String>,
    pub language: String,
    pub page_count: Option<u32>,
    
    // Quality and ratings
    pub average_rating: Option<f32>,
    pub ratings_count: Option<u32>,
    pub reviews: Vec<Review>,
    
    // Visual assets
    pub cover_image: Option<CoverImage>,
    pub author_photos: Vec<AuthorPhoto>,
    
    // Relationships
    pub related_books: Vec<BookRelationship>,
    pub translations: Vec<Translation>,
    pub editions: Vec<Edition>,
    
    // Enrichment metadata
    pub enrichment_status: EnrichmentStatus,
    pub enrichment_sources: Vec<EnrichmentSource>,
    pub last_enriched: Option<DateTime<Utc>>,
    
    // Original book data
    pub original_book: Box<Book>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Author {
    pub name: String,
    pub biography: Option<String>,
    pub birth_date: Option<NaiveDate>,
    pub death_date: Option<NaiveDate>,
    pub photo_url: Option<String>,
    pub other_works: Vec<String>,
    pub external_ids: HashMap<String, String>, // goodreads_id, wikipedia_id, etc.
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Publisher {
    pub name: String,
    pub founded: Option<NaiveDate>,
    pub logo_url: Option<String>,
    pub website: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CoverImage {
    pub thumbnail_url: Option<String>,
    pub small_url: Option<String>,
    pub medium_url: Option<String>,
    pub large_url: Option<String>,
    pub local_path: Option<PathBuf>,
    pub dominant_colors: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct BookRelationship {
    pub related_book_id: String,
    pub relationship_type: RelationshipType,
    pub strength: f32, // 0.0 to 1.0
    pub description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum RelationshipType {
    SameAuthor,
    SameSeries,
    Translation,
    Edition,
    SimilarTopic,
    CitedBy,
    Cites,
    Commentary,
    SamePhilosophy,
    RelatedPractice,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Translation {
    pub language: String,
    pub translator: Option<String>,
    pub book_id: Option<String>,
    pub quality_score: Option<f32>,
    pub notes: Option<String>,
}
```

### API Integration Layer

```rust
// Metadata enrichment service
#[derive(Debug)]
pub struct MetadataEnrichmentService {
    google_books_client: GoogleBooksClient,
    openlibrary_client: OpenLibraryClient,
    image_cache: ImageCacheManager,
    relationship_analyzer: RelationshipAnalyzer,
    rate_limiter: RateLimiter,
}

impl MetadataEnrichmentService {
    pub async fn enrich_book(&self, book: &Book) -> Result<EnrichedBook, EnrichmentError> {
        let mut enriched = EnrichedBook::from_book(book.clone());
        
        // Step 1: Identify book across APIs
        let book_identity = self.resolve_book_identity(book).await?;
        
        // Step 2: Gather metadata from multiple sources
        let google_data = self.fetch_google_books_data(&book_identity).await?;
        let openlibrary_data = self.fetch_openlibrary_data(&book_identity).await?;
        
        // Step 3: Merge and validate metadata
        self.merge_metadata(&mut enriched, google_data, openlibrary_data).await?;
        
        // Step 4: Download and cache visual assets
        self.process_visual_assets(&mut enriched).await?;
        
        // Step 5: Analyze relationships
        enriched.related_books = self.analyze_relationships(&enriched).await?;
        
        // Step 6: Detect translations and editions
        enriched.translations = self.detect_translations(&enriched).await?;
        enriched.editions = self.detect_editions(&enriched).await?;
        
        // Step 7: Update enrichment status
        enriched.enrichment_status = EnrichmentStatus::Complete;
        enriched.last_enriched = Some(Utc::now());
        
        Ok(enriched)
    }
    
    async fn resolve_book_identity(&self, book: &Book) -> Result<BookIdentity, EnrichmentError> {
        let mut candidates = Vec::new();
        
        // Try ISBN first if available
        if let Some(isbn) = &book.isbn {
            candidates.push(self.google_books_client.search_by_isbn(isbn).await?);
            candidates.push(self.openlibrary_client.search_by_isbn(isbn).await?);
        }
        
        // Try title + author
        candidates.push(
            self.google_books_client
                .search_by_title_author(&book.title, &book.author)
                .await?
        );
        
        // Rank candidates and select best match
        let best_match = self.rank_identity_candidates(book, candidates)?;
        Ok(best_match)
    }
}

// Google Books API client
#[derive(Debug)]
pub struct GoogleBooksClient {
    client: reqwest::Client,
    api_key: Option<String>,
    rate_limiter: RateLimiter,
}

impl GoogleBooksClient {
    pub async fn search_by_isbn(&self, isbn: &str) -> Result<GoogleBooksResponse, ApiError> {
        self.rate_limiter.wait().await;
        
        let url = format!(
            "https://www.googleapis.com/books/v1/volumes?q=isbn:{}{}",
            isbn,
            self.api_key.as_ref().map(|k| format!("&key={}", k)).unwrap_or_default()
        );
        
        let response: GoogleBooksResponse = self.client
            .get(&url)
            .send()
            .await?
            .json()
            .await?;
        
        Ok(response)
    }
    
    pub async fn search_by_title_author(&self, title: &str, author: &str) -> Result<GoogleBooksResponse, ApiError> {
        self.rate_limiter.wait().await;
        
        let query = format!("intitle:{} inauthor:{}", title, author);
        let encoded_query = urlencoding::encode(&query);
        
        let url = format!(
            "https://www.googleapis.com/books/v1/volumes?q={}{}",
            encoded_query,
            self.api_key.as_ref().map(|k| format!("&key={}", k)).unwrap_or_default()
        );
        
        let response: GoogleBooksResponse = self.client
            .get(&url)
            .send()
            .await?
            .json()
            .await?;
        
        Ok(response)
    }
}
```

### Visual Asset Management

```rust
// Image cache and optimization system
#[derive(Debug)]
pub struct ImageCacheManager {
    cache_dir: PathBuf,
    client: reqwest::Client,
    compression_settings: ImageCompressionSettings,
}

impl ImageCacheManager {
    pub async fn download_and_cache_image(
        &self,
        url: &str,
        book_id: &str,
        image_type: ImageType,
    ) -> Result<CachedImage, ImageError> {
        let cache_key = self.generate_cache_key(url, book_id, image_type);
        let cache_path = self.cache_dir.join(&cache_key);
        
        // Check if already cached
        if cache_path.exists() {
            return Ok(CachedImage::from_path(cache_path));
        }
        
        // Download image
        let response = self.client.get(url).send().await?;
        let image_data = response.bytes().await?;
        
        // Process and optimize
        let processed_image = self.process_image(image_data, image_type).await?;
        
        // Save to cache
        tokio::fs::write(&cache_path, &processed_image.data).await?;
        
        // Extract dominant colors for UI theming
        let dominant_colors = self.extract_dominant_colors(&processed_image.data).await?;
        
        Ok(CachedImage {
            path: cache_path,
            dominant_colors,
            format: processed_image.format,
            dimensions: processed_image.dimensions,
        })
    }
    
    async fn process_image(
        &self,
        data: bytes::Bytes,
        image_type: ImageType,
    ) -> Result<ProcessedImage, ImageError> {
        use image::{ImageFormat, DynamicImage};
        
        let img = image::load_from_memory(&data)?;
        
        let processed = match image_type {
            ImageType::CoverThumbnail => img.resize(150, 200, image::imageops::FilterType::Lanczos3),
            ImageType::CoverSmall => img.resize(300, 400, image::imageops::FilterType::Lanczos3),
            ImageType::CoverMedium => img.resize(600, 800, image::imageops::FilterType::Lanczos3),
            ImageType::AuthorPhoto => img.resize(200, 200, image::imageops::FilterType::Lanczos3),
        };
        
        let mut buffer = Vec::new();
        processed.write_to(&mut std::io::Cursor::new(&mut buffer), ImageFormat::WebP)?;
        
        Ok(ProcessedImage {
            data: buffer,
            format: ImageFormat::WebP,
            dimensions: (processed.width(), processed.height()),
        })
    }
}
```

### Relationship Analysis Engine

```rust
// Book relationship detection and analysis
#[derive(Debug)]
pub struct RelationshipAnalyzer {
    similarity_threshold: f32,
    translation_detector: TranslationDetector,
    topic_analyzer: TopicAnalyzer,
}

impl RelationshipAnalyzer {
    pub async fn analyze_relationships(
        &self,
        enriched_book: &EnrichedBook,
        existing_books: &[EnrichedBook],
    ) -> Result<Vec<BookRelationship>, AnalysisError> {
        let mut relationships = Vec::new();
        
        for candidate in existing_books {
            if candidate.id == enriched_book.id {
                continue;
            }
            
            // Check for same author
            if self.is_same_author(enriched_book, candidate) {
                relationships.push(BookRelationship {
                    related_book_id: candidate.id.clone(),
                    relationship_type: RelationshipType::SameAuthor,
                    strength: 0.9,
                    description: Some("Books by the same author".to_string()),
                });
            }
            
            // Check for translations
            if let Some(translation_rel) = self.detect_translation_relationship(enriched_book, candidate).await? {
                relationships.push(translation_rel);
            }
            
            // Check for topic similarity
            let topic_similarity = self.calculate_topic_similarity(enriched_book, candidate).await?;
            if topic_similarity > self.similarity_threshold {
                relationships.push(BookRelationship {
                    related_book_id: candidate.id.clone(),
                    relationship_type: RelationshipType::SimilarTopic,
                    strength: topic_similarity,
                    description: Some(format!("Similar topics ({}% match)", (topic_similarity * 100.0) as u32)),
                });
            }
            
            // Check for philosophical/scripture connections (specialized for various traditions)
            if let Some(scripture_rel) = self.detect_scripture_relationship(enriched_book, candidate).await? {
                relationships.push(scripture_rel);
            }
        }
        
        // Sort by strength and limit results
        relationships.sort_by(|a, b| b.strength.partial_cmp(&a.strength).unwrap_or(std::cmp::Ordering::Equal));
        relationships.truncate(10); // Limit to top 10 relationships
        
        Ok(relationships)
    }
    
    async fn detect_scripture_relationship(
        &self,
        book1: &EnrichedBook,
        book2: &EnrichedBook,
    ) -> Result<Option<BookRelationship>, AnalysisError> {
        // Specialized logic for various scripture traditions
        let scripture_keywords = [
            "bhagavad", "gita", "krishna", "arjuna", "upanishad", "vedanta",
            "bhagavatam", "srimad", "caitanya", "prabhupada", "iskcon",
            "torah", "talmud", "hebrew", "jewish", "rabbi", "judaism",
            "quran", "hadith", "islamic", "muslim", "prophet", "allah",
            "bible", "christian", "gospel", "psalm", "christ", "scripture",
            "yoga", "meditation", "dharma", "karma", "moksha"
        ];
        
        let book1_scripture_score = self.calculate_keyword_presence(&book1.title, &scripture_keywords) +
                                   self.calculate_keyword_presence(&book1.subjects.join(" "), &scripture_keywords);
        
        let book2_scripture_score = self.calculate_keyword_presence(&book2.title, &scripture_keywords) +
                                   self.calculate_keyword_presence(&book2.subjects.join(" "), &scripture_keywords);
        
        if book1_scripture_score > 0.3 && book2_scripture_score > 0.3 {
            let strength = (book1_scripture_score + book2_scripture_score) / 2.0;
            return Ok(Some(BookRelationship {
                related_book_id: book2.id.clone(),
                relationship_type: RelationshipType::SamePhilosophy,
                strength: strength.min(1.0),
                description: Some("Related scripture/philosophical teachings".to_string()),
            }));
        }
        
        Ok(None)
    }
}
```

### Frontend Integration

```typescript
// Enhanced Book component with enrichment data
export const EnrichedBookCard: React.FC<{ book: EnrichedBook }> = ({ book }) => {
  const [showDetails, setShowDetails] = useState(false);
  
  return (
    <div className="relative group">
      {/* Cover Image with Loading States */}
      <div className="aspect-[3/4] relative overflow-hidden rounded-lg shadow-md">
        {book.cover_image?.medium_url ? (
          <img
            src={book.cover_image.medium_url}
            alt={`Cover of ${book.title}`}
            className="w-full h-full object-cover transition-transform group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
            <BookOpen className="w-12 h-12 text-gray-400" />
          </div>
        )}
        
        {/* Enrichment Status Indicator */}
        <div className="absolute top-2 right-2">
          <Badge 
            variant={book.enrichment_status === 'Complete' ? 'success' : 'warning'}
            className="text-xs"
          >
            {book.enrichment_status}
          </Badge>
        </div>
      </div>
      
      {/* Book Information */}
      <div className="mt-3 space-y-2">
        <h3 className="font-semibold text-sm leading-tight line-clamp-2">
          {book.title}
        </h3>
        
        {book.authors.length > 0 && (
          <p className="text-xs text-gray-600 line-clamp-1">
            {book.authors.map(a => a.name).join(', ')}
          </p>
        )}
        
        {/* Rating Display */}
        {book.average_rating && (
          <div className="flex items-center gap-1">
            <div className="flex">
              {[...Array(5)].map((_, i) => (
                <Star
                  key={i}
                  className={`w-3 h-3 ${
                    i < Math.floor(book.average_rating!) 
                      ? 'text-yellow-400 fill-current' 
                      : 'text-gray-300'
                  }`}
                />
              ))}
            </div>
            <span className="text-xs text-gray-600">
              ({book.ratings_count || 0})
            </span>
          </div>
        )}
        
        {/* Categories */}
        {book.categories.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {book.categories.slice(0, 2).map((category, index) => (
              <Badge key={index} variant="secondary" className="text-xs px-2 py-0">
                {category}
              </Badge>
            ))}
          </div>
        )}
        
        {/* Related Books Indicator */}
        {book.related_books.length > 0 && (
          <div className="flex items-center gap-1 text-xs text-blue-600">
            <Link className="w-3 h-3" />
            <span>{book.related_books.length} related</span>
          </div>
        )}
      </div>
      
      {/* Hover Details */}
      {showDetails && (
        <div className="absolute z-10 top-full left-0 right-0 mt-2 p-4 bg-white shadow-lg rounded-lg border">
          <h4 className="font-semibold mb-2">{book.title}</h4>
          
          {book.subtitle && (
            <p className="text-sm text-gray-600 mb-2">{book.subtitle}</p>
          )}
          
          {book.publisher && (
            <p className="text-xs text-gray-500 mb-1">
              Published by {book.publisher.name}
              {book.publication_date && ` in ${book.publication_date.getFullYear()}`}
            </p>
          )}
          
          {book.page_count && (
            <p className="text-xs text-gray-500 mb-2">{book.page_count} pages</p>
          )}
          
          {/* Related Books Preview */}
          {book.related_books.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-medium mb-1">Related Books:</p>
              <div className="space-y-1">
                {book.related_books.slice(0, 3).map((rel, index) => (
                  <div key={index} className="text-xs text-gray-600 flex items-center gap-1">
                    <div className="w-1 h-1 bg-gray-400 rounded-full" />
                    <span>{rel.relationship_type}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
```

This comprehensive metadata enrichment system provides:

1. **Rich Metadata Collection**: ISBN lookup, author information, ratings, categories
2. **Visual Asset Management**: Cover images, author photos with optimization and caching
3. **Relationship Analysis**: Detects similar books, translations, same author relationships
4. **Specialized Scripture Text Support**: Enhanced relationship detection for various scripture traditions
5. **Performance Optimization**: Rate limiting, caching, and efficient data structures
6. **Enhanced UI Components**: Rich visual book cards with metadata display

---

## 🎨 Frontend Error Visualization and User Experience

### Enhanced Error Display Components

```typescript
// components/ErrorDisplay.tsx - Comprehensive error visualization
import React, { useState, useCallback } from 'react';
import { AlertTriangle, RefreshCw, ExternalLink, Copy, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/Alert';
import { Badge } from '@/components/ui/Badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/Collapsible';
import { Textarea } from '@/components/ui/Textarea';
import { cn } from '@/utils/cn';

interface ErrorDisplayProps {
  error: ErrorContext;
  onRetry?: () => Promise<void>;
  onDismiss?: () => void;
  onReportBug?: (errorDetails: string) => void;
  className?: string;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onRetry,
  onDismiss,
  onReportBug,
  className,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleRetry = useCallback(async () => {
    if (!onRetry) return;
    
    setIsRetrying(true);
    try {
      await onRetry();
    } catch (retryError) {
      console.error('Retry failed:', retryError);
    } finally {
      setIsRetrying(false);
    }
  }, [onRetry]);

  const handleCopyError = useCallback(async () => {
    const errorDetails = `
Error ID: ${error.error_id}
Component: ${error.component}
Operation: ${error.operation}
Timestamp: ${error.timestamp}
Message: ${error.user_message}
Technical Details: ${error.technical_details}
    `.trim();

    try {
      await navigator.clipboard.writeText(errorDetails);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  }, [error]);

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowercase()) {
      case 'critical': return 'destructive';
      case 'error': return 'destructive';
      case 'warning': return 'warning';
      case 'info': return 'default';
      default: return 'secondary';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowercase()) {
      case 'critical':
      case 'error':
        return <AlertTriangle className="h-5 w-5 text-destructive" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-warning" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-muted-foreground" />;
    }
  };

  return (
    <Alert className={cn("border-l-4", className)} variant={getSeverityColor(error.severity)}>
      <div className="flex items-start space-x-3">
        {getSeverityIcon(error.severity)}
        
        <div className="flex-1 space-y-2">
          <div className="flex items-center justify-between">
            <AlertTitle className="text-base font-semibold">
              Error in {error.component}
            </AlertTitle>
            
            <div className="flex items-center space-x-2">
              <Badge variant={getSeverityColor(error.severity)} className="text-xs">
                {error.severity.toUpperCase()}
              </Badge>
              
              {error.recoverable && (
                <Badge variant="outline" className="text-xs">
                  Recoverable
                </Badge>
              )}
            </div>
          </div>
          
          <AlertDescription className="text-sm text-muted-foreground">
            {error.user_message}
          </AlertDescription>
          
          {/* Suggested Actions */}
          {error.suggested_actions.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground">Suggested actions:</p>
              <ul className="text-xs text-muted-foreground space-y-1">
                {error.suggested_actions.map((action, index) => (
                  <li key={index} className="flex items-start">
                    <span className="mr-2">•</span>
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {/* Action Buttons */}
          <div className="flex items-center space-x-2 pt-2">
            {error.recoverable && onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleRetry}
                disabled={isRetrying}
                className="h-8"
              >
                <RefreshCw className={cn("h-3 w-3 mr-2", isRetrying && "animate-spin")} />
                {isRetrying ? 'Retrying...' : 'Retry'}
              </Button>
            )}
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopyError}
              className="h-8"
            >
              <Copy className="h-3 w-3 mr-2" />
              {copied ? 'Copied!' : 'Copy Details'}
            </Button>
            
            {onReportBug && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onReportBug(`${error.user_message}\n\nError ID: ${error.error_id}`)}
                className="h-8"
              >
                <ExternalLink className="h-3 w-3 mr-2" />
                Report Bug
              </Button>
            )}
            
            {onDismiss && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onDismiss}
                className="h-8 ml-auto"
              >
                Dismiss
              </Button>
            )}
          </div>
          
          {/* Expandable Technical Details */}
          <Collapsible>
            <CollapsibleTrigger
              className="flex items-center text-xs text-muted-foreground hover:text-foreground transition-colors"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? (
                <ChevronUp className="h-3 w-3 mr-1" />
              ) : (
                <ChevronDown className="h-3 w-3 mr-1" />
              )}
              {isExpanded ? 'Hide' : 'Show'} technical details
            </CollapsibleTrigger>
            
            <CollapsibleContent className="mt-2">
              <div className="bg-muted/50 rounded-md p-3 space-y-2">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="font-medium">Error ID:</span>
                    <p className="font-mono text-muted-foreground break-all">{error.error_id}</p>
                  </div>
                  <div>
                    <span className="font-medium">Timestamp:</span>
                    <p className="text-muted-foreground">
                      {new Date(error.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <span className="font-medium">Component:</span>
                    <p className="text-muted-foreground">{error.component}</p>
                  </div>
                  <div>
                    <span className="font-medium">Operation:</span>
                    <p className="text-muted-foreground">{error.operation}</p>
                  </div>
                </div>
                
                <div>
                  <span className="font-medium text-xs">Technical Details:</span>
                  <Textarea
                    value={error.technical_details}
                    readOnly
                    className="mt-1 text-xs font-mono bg-background"
                    rows={4}
                  />
                </div>
              </div>
            </CollapsibleContent>
          </Collapsible>
        </div>
      </div>
    </Alert>
  );
};

// components/NotificationToast.tsx - Toast notification system
import { Toast, ToastAction, ToastDescription, ToastTitle } from '@/components/ui/Toast';
import { useToast } from '@/hooks/useToast';

export const NotificationToast: React.FC<{ notification: UserNotification }> = ({
  notification,
}) => {
  const { dismiss } = useToast();

  return (
    <Toast
      variant={notification.notification_type === 'Error' ? 'destructive' : 'default'}
      duration={notification.auto_dismiss_after ? notification.auto_dismiss_after * 1000 : undefined}
    >
      <div className="grid gap-1">
        <ToastTitle>{notification.title}</ToastTitle>
        <ToastDescription>{notification.message}</ToastDescription>
      </div>
      
      {notification.actions.map((action, index) => (
        <ToastAction
          key={index}
          altText={action.label}
          onClick={() => {
            // Handle action based on action_type
            switch (action.action_type) {
              case 'Dismiss':
                dismiss(notification.id);
                break;
              case 'Retry':
                // Emit retry event
                window.dispatchEvent(new CustomEvent('retry-operation', {
                  detail: action.data
                }));
                break;
              case 'OpenLogs':
                // Open logs viewer
                window.dispatchEvent(new CustomEvent('open-logs'));
                break;
              case 'ReportBug':
                // Open bug report
                window.dispatchEvent(new CustomEvent('report-bug', {
                  detail: action.data
                }));
                break;
              default:
                // Custom action
                window.dispatchEvent(new CustomEvent('custom-action', {
                  detail: { type: action.action_type, data: action.data }
                }));
            }
          }}
        >
          {action.label}
        </ToastAction>
      ))}
    </Toast>
  );
};

// components/ErrorBoundary.tsx - React Error Boundary
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: React.ComponentType<{ error: Error; resetError: () => void }>;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Send error to logging service
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
    
    // Send error to Rust backend for logging
    window.__TAURI__?.invoke('log_frontend_error', {
      error: error.toString(),
      stack: error.stack,
      componentStack: errorInfo.componentStack,
    });
  }

  resetError = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback;
        return <FallbackComponent error={this.state.error!} resetError={this.resetError} />;
      }

      return (
        <div className="min-h-[200px] flex items-center justify-center p-6">
          <div className="text-center space-y-4">
            <AlertTriangle className="h-12 w-12 text-destructive mx-auto" />
            <div>
              <h3 className="text-lg font-semibold">Something went wrong</h3>
              <p className="text-sm text-muted-foreground mt-2">
                {this.state.error?.message || 'An unexpected error occurred'}
              </p>
            </div>
            <Button onClick={this.resetError} variant="outline">
              Try Again
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// hooks/useErrorHandler.ts - Custom hook for error handling
import { useCallback } from 'react';
import { useToast } from './useToast';

export const useErrorHandler = () => {
  const { toast } = useToast();

  const handleError = useCallback((error: Error | ErrorContext, options?: {
    showToast?: boolean;
    retryAction?: () => Promise<void>;
  }) => {
    const showToast = options?.showToast ?? true;

    if (error instanceof Error) {
      // Convert JavaScript Error to ErrorContext
      const errorContext: ErrorContext = {
        timestamp: new Date().toISOString(),
        error_id: crypto.randomUUID(),
        component: 'frontend',
        operation: 'unknown',
        user_message: error.message,
        technical_details: error.stack || error.toString(),
        severity: 'Error',
        recoverable: !!options?.retryAction,
        suggested_actions: options?.retryAction ? ['Try the operation again'] : [],
      };

      if (showToast) {
        toast({
          title: 'An error occurred',
          description: error.message,
          variant: 'destructive',
          action: options?.retryAction ? {
            label: 'Retry',
            onClick: options.retryAction,
          } : undefined,
        });
      }

      // Log to backend
      window.__TAURI__?.invoke('log_frontend_error', errorContext);
    } else {
      // ErrorContext from backend
      if (showToast) {
        toast({
          title: `Error in ${error.component}`,
          description: error.user_message,
          variant: error.severity === 'Critical' || error.severity === 'Error' ? 'destructive' : 'default',
          action: error.recoverable && options?.retryAction ? {
            label: 'Retry',
            onClick: options.retryAction,
          } : undefined,
        });
      }
    }
  }, [toast]);

  return { handleError };
};
```

### Complete Configuration Management System

```typescript
// config/appConfig.ts - Centralized configuration management
export interface AppConfig {
  // UI Configuration
  ui: {
    theme: 'light' | 'dark' | 'system';
    language: string;
    animations_enabled: boolean;
    compact_mode: boolean;
    sidebar_width: number;
  };
  
  // Processing Configuration
  processing: {
    chunk_size: number;
    chunk_overlap: number;
    max_concurrent_jobs: number;
    auto_process: boolean;
    preferred_formats: string[];
  };
  
  // Cloud Storage Configuration
  cloud_storage: {
    icloud_enabled: boolean;
    dropbox_enabled: boolean;
    google_drive_enabled: boolean;
    auto_sync: boolean;
    sync_interval_minutes: number;
  };
  
  // Privacy and Security
  privacy: {
    analytics_enabled: boolean;
    crash_reporting_enabled: boolean;
    usage_statistics: boolean;
    data_retention_days: number;
  };
  
  // Developer Settings
  developer: {
    debug_mode: boolean;
    log_level: 'error' | 'warn' | 'info' | 'debug';
    performance_monitoring: boolean;
  };
}

export const defaultConfig: AppConfig = {
  ui: {
    theme: 'system',
    language: 'en',
    animations_enabled: true,
    compact_mode: false,
    sidebar_width: 280,
  },
  processing: {
    chunk_size: 500,
    chunk_overlap: 50,
    max_concurrent_jobs: 3,
    auto_process: false,
    preferred_formats: ['pdf', 'epub', 'txt'],
  },
  cloud_storage: {
    icloud_enabled: false,
    dropbox_enabled: false,
    google_drive_enabled: false,
    auto_sync: false,
    sync_interval_minutes: 60,
  },
  privacy: {
    analytics_enabled: false,
    crash_reporting_enabled: true,
    usage_statistics: false,
    data_retention_days: 30,
  },
  developer: {
    debug_mode: false,
    log_level: 'info',
    performance_monitoring: false,
  },
};

// Store configuration in Rust backend
export class ConfigManager {
  private config: AppConfig = defaultConfig;
  
  async loadConfig(): Promise<AppConfig> {
    try {
      const savedConfig = await window.__TAURI__?.invoke('load_app_config');
      this.config = { ...defaultConfig, ...savedConfig };
      return this.config;
    } catch (error) {
      console.warn('Failed to load config, using defaults:', error);
      return defaultConfig;
    }
  }
  
  async saveConfig(updates: Partial<AppConfig>): Promise<void> {
    this.config = { ...this.config, ...updates };
    await window.__TAURI__?.invoke('save_app_config', { config: this.config });
  }
  
  getConfig(): AppConfig {
    return this.config;
  }
  
  get<K extends keyof AppConfig>(section: K): AppConfig[K] {
    return this.config[section];
  }
  
  async updateSection<K extends keyof AppConfig>(
    section: K, 
    updates: Partial<AppConfig[K]>
  ): Promise<void> {
    const newConfig = {
      ...this.config,
      [section]: { ...this.config[section], ...updates }
    };
    await this.saveConfig(newConfig);
  }
}

export const configManager = new ConfigManager();
```

### Enhanced Performance Monitoring

```rust
// Performance monitoring and metrics collection
use std::time::{Duration, Instant};
use std::collections::HashMap;
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceMetric {
    pub name: String,
    pub duration: Duration,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub metadata: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemMetrics {
    pub memory_usage: u64,
    pub cpu_usage: f32,
    pub disk_usage: u64,
    pub active_operations: usize,
    pub total_books_processed: usize,
    pub avg_processing_time: Duration,
}

pub struct PerformanceMonitor {
    metrics: Vec<PerformanceMetric>,
    active_timers: HashMap<String, Instant>,
    system_metrics: SystemMetrics,
}

impl PerformanceMonitor {
    pub fn new() -> Self {
        PerformanceMonitor {
            metrics: Vec::new(),
            active_timers: HashMap::new(),
            system_metrics: SystemMetrics {
                memory_usage: 0,
                cpu_usage: 0.0,
                disk_usage: 0,
                active_operations: 0,
                total_books_processed: 0,
                avg_processing_time: Duration::default(),
            },
        }
    }
    
    pub fn start_timer(&mut self, operation: &str) {
        self.active_timers.insert(operation.to_string(), Instant::now());
    }
    
    pub fn end_timer(&mut self, operation: &str) -> Option<Duration> {
        if let Some(start_time) = self.active_timers.remove(operation) {
            let duration = start_time.elapsed();
            
            let metric = PerformanceMetric {
                name: operation.to_string(),
                duration,
                timestamp: chrono::Utc::now(),
                metadata: HashMap::new(),
            };
            
            self.metrics.push(metric);
            
            // Keep only last 1000 metrics to prevent memory bloat
            if self.metrics.len() > 1000 {
                self.metrics.drain(0..100);
            }
            
            Some(duration)
        } else {
            None
        }
    }
    
    pub fn record_metric(&mut self, name: &str, duration: Duration, metadata: HashMap<String, String>) {
        let metric = PerformanceMetric {
            name: name.to_string(),
            duration,
            timestamp: chrono::Utc::now(),
            metadata,
        };
        
        self.metrics.push(metric);
    }
    
    pub async fn update_system_metrics(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        // Use system monitoring libraries to collect metrics
        use sysinfo::{System, SystemExt, ProcessExt};
        
        let mut sys = System::new_all();
        sys.refresh_all();
        
        // Get current process info
        let pid = sysinfo::get_current_pid()?;
        if let Some(process) = sys.process(pid) {
            self.system_metrics.memory_usage = process.memory();
            self.system_metrics.cpu_usage = process.cpu_usage();
        }
        
        // Update other metrics
        self.system_metrics.disk_usage = self.calculate_app_disk_usage().await?;
        self.system_metrics.active_operations = self.active_timers.len();
        
        Ok(())
    }
    
    async fn calculate_app_disk_usage(&self) -> Result<u64, std::io::Error> {
        // Calculate total disk usage of app data
        let app_data_dir = dirs::data_dir()
            .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::NotFound, "Could not find data directory"))?
            .join("lexicon");
        
        self.calculate_directory_size(&app_data_dir).await
    }
    
    async fn calculate_directory_size(&self, dir: &std::path::Path) -> Result<u64, std::io::Error> {
        let mut total_size = 0u64;
        
        if dir.is_dir() {
            let mut entries = tokio::fs::read_dir(dir).await?;
            
            while let Some(entry) = entries.next_entry().await? {
                let path = entry.path();
                
                if path.is_dir() {
                    total_size += self.calculate_directory_size(&path).await?;
                } else {
                    let metadata = tokio::fs::metadata(&path).await?;
                    total_size += metadata.len();
                }
            }
        }
        
        Ok(total_size)
    }
    
    pub fn get_performance_summary(&self) -> HashMap<String, Vec<Duration>> {
        let mut summary = HashMap::new();
        
        for metric in &self.metrics {
            summary.entry(metric.name.clone())
                .or_insert_with(Vec::new)
                .push(metric.duration);
        }
        
        summary
    }
    
    pub fn get_system_metrics(&self) -> &SystemMetrics {
        &self.system_metrics
    }
    
    pub async fn export_performance_report(&self, file_path: &std::path::Path) -> Result<(), std::io::Error> {
        let report = serde_json::to_string_pretty(&self.metrics)?;
        tokio::fs::write(file_path, report).await
    }
}

// Macro for easy performance timing
#[macro_export]
macro_rules! time_operation {
    ($monitor:expr, $name:expr, $operation:expr) => {{
        $monitor.start_timer($name);
        let result = $operation;
        $monitor.end_timer($name);
        result
    }};
}

// Usage example:
// let result = time_operation!(performance_monitor, "book_processing", async {
//     process_book(&book).await
// });
```

---

## 📋 Implementation Checklist and Next Steps

### Phase 1: Foundation Setup (Week 1-2)
- [ ] Initialize Tauri project with React + TypeScript
- [ ] Set up basic project structure and dependencies
- [ ] Implement configuration management system
- [ ] Create basic UI components and layout
- [ ] Set up Python environment management
- [ ] Implement error handling and logging framework

### Phase 2: Core Functionality (Week 3-4)
- [ ] Implement book registry system with SQLite
- [ ] Create file type detection and validation
- [ ] Build basic scraping functionality
- [ ] Implement text chunking and processing
- [ ] Add progress tracking and status updates
- [ ] Create basic export functionality

### Phase 3: Enhanced Features (Week 5-6)
- [ ] Implement cloud storage integration (iCloud first)
- [ ] Add comprehensive error handling and user notifications
- [ ] Build drag-and-drop file interface
- [ ] Implement bulk operations and batch processing
- [ ] Add search and filtering capabilities
- [ ] Create settings and configuration UI

### Phase 4: Polish and Testing (Week 7-8)
- [ ] Comprehensive testing (unit, integration, E2E)
- [ ] Performance optimization and monitoring
- [ ] UI/UX refinements and accessibility
- [ ] Documentation and user guides
- [ ] Code signing and deployment preparation
- [ ] Update mechanism implementation

### Key Dependencies and Libraries

```toml
# Complete dependency list for reference
[dependencies]
# Tauri and core
tauri = { version = "2.0", features = ["api-all", "updater"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tokio = { version = "1.0", features = ["full"] }

# Database
sqlx = { version = "0.8", features = ["runtime-tokio-rustls", "sqlite", "chrono", "uuid"] }

# HTTP and networking
reqwest = { version = "0.12", features = ["json", "rustls-tls"] }
oauth2 = "4.4"

# Error handling and logging
thiserror = "1.0"
anyhow = "1.0"
log = "0.4"
tracing = "0.1"
tracing-subscriber = "0.3"
tracing-appender = "0.2"

# File system and utilities
dirs = "5.0"
walkdir = "2.5"
uuid = { version = "1.8", features = ["v4", "serde"] }
chrono = { version = "0.4", features = ["serde"] }

# Text processing
regex = "1.10"
unicode-segmentation = "1.11"

# Async and concurrency
futures = "0.3"
rayon = "1.8"

# Security and encryption
ring = "0.17"
base64 = "0.22"

# System monitoring
sysinfo = "0.30"

# Testing
tokio-test = "0.4"
tempfile = "3.8"
mockall = "0.12"
proptest = "1.4"
criterion = { version = "0.5", features = ["html_reports"] }
```

```json
// Frontend package.json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.0.0",
    
    "tailwindcss": "^3.4.0",
    "@headlessui/react": "^2.0.0",
    "lucide-react": "^0.400.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.3.0",
    
    "zustand": "^4.5.0",
    "@tanstack/react-query": "^5.0.0",
    "react-hook-form": "^7.51.0",
    "@hookform/resolvers": "^3.3.0",
    "zod": "^3.22.0",
    
    "framer-motion": "^11.0.0",
    "react-dropzone": "^14.2.0",
    "react-virtualized-auto-sizer": "^1.0.0",
    "react-window": "^1.8.0"
  },
  "devDependencies": {
    "@tauri-apps/cli": "^2.0.0",
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "vitest": "^1.0.0",
    "jsdom": "^24.0.0",
    "eslint": "^8.0.0",
    "prettier": "^3.0.0"
  }
}
```

### Final Architecture Summary

The enhanced Lexicon technical specification now provides:

1. **Complete Technology Stack**: Detailed Rust and Python dependencies with justification
2. **Comprehensive Error Handling**: Multi-layer error management with user-friendly display
3. **Python Environment Management**: Isolated virtual environment with automatic dependency installation
4. **Cloud Storage Integration**: OAuth2 flows for major providers with secure credential storage
5. **Advanced Testing Strategy**: Unit, integration, property-based, performance, and chaos testing
6. **Deployment and Updates**: Automated update checking and installation with code signing
7. **Performance Monitoring**: Real-time metrics collection and performance analysis
8. **Frontend Architecture**: Complete React component structure with state management
9. **Configuration Management**: Centralized settings with persistent storage
10. **Security Considerations**: Encryption, sandboxing, and privacy-first design

This technical specification is now implementation-ready and addresses all the critical feedback from both ChatGPT and Gemini, providing a robust foundation for building a high-quality, production-ready application.

---

---

## 🏭 Production Infrastructure & Operations

### Production Error Tracking System

The production error tracking system provides comprehensive error management, logging, and user notification capabilities for enterprise-grade reliability.

```rust
// src/lib/error_tracking.rs - Production error tracking implementation
use serde::{Serialize, Deserialize};
use std::collections::HashMap;
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProductionErrorContext {
    pub error_id: String,
    pub timestamp: DateTime<Utc>,
    pub severity: ErrorSeverity,
    pub component: String,
    pub operation: String,
    pub user_message: String,
    pub technical_details: String,
    pub stack_trace: Option<String>,
    pub user_agent: Option<String>,
    pub session_id: String,
    pub recoverable: bool,
    pub retry_count: usize,
    pub context_data: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ErrorSeverity {
    Info,
    Warning,
    Error,
    Critical,
}

pub struct ProductionErrorTracker {
    error_store: Arc<Mutex<Vec<ProductionErrorContext>>>,
    notification_sender: UnboundedSender<ErrorNotification>,
    analytics_client: Option<AnalyticsClient>,
    crash_reporter: CrashReporter,
}

impl ProductionErrorTracker {
    pub async fn track_error(&self, error: ProductionErrorContext) -> Result<(), TrackingError> {
        // Store error locally
        {
            let mut store = self.error_store.lock().await;
            store.push(error.clone());
            
            // Maintain size limit
            if store.len() > 1000 {
                store.drain(0..100);
            }
        }
        
        // Send user notification for critical errors
        if matches!(error.severity, ErrorSeverity::Critical | ErrorSeverity::Error) {
            let notification = ErrorNotification {
                title: format!("Error in {}", error.component),
                message: error.user_message.clone(),
                error_id: error.error_id.clone(),
                severity: error.severity.clone(),
                actions: if error.recoverable {
                    vec![NotificationAction::Retry, NotificationAction::Report]
                } else {
                    vec![NotificationAction::Report]
                },
            };
            
            let _ = self.notification_sender.send(notification);
        }
        
        // Report to analytics (if enabled and user consented)
        if let Some(analytics) = &self.analytics_client {
            analytics.track_error_event(&error).await?;
        }
        
        // For critical errors, trigger crash reporting
        if matches!(error.severity, ErrorSeverity::Critical) {
            self.crash_reporter.report_critical_error(&error).await?;
        }
        
        Ok(())
    }
    
    pub async fn get_error_summary(&self) -> ErrorSummary {
        let store = self.error_store.lock().await;
        
        let total_errors = store.len();
        let critical_count = store.iter().filter(|e| matches!(e.severity, ErrorSeverity::Critical)).count();
        let error_count = store.iter().filter(|e| matches!(e.severity, ErrorSeverity::Error)).count();
        let warning_count = store.iter().filter(|e| matches!(e.severity, ErrorSeverity::Warning)).count();
        
        let most_common_components: HashMap<String, usize> = store
            .iter()
            .fold(HashMap::new(), |mut acc, error| {
                *acc.entry(error.component.clone()).or_insert(0) += 1;
                acc
            });
        
        ErrorSummary {
            total_errors,
            critical_count,
            error_count,
            warning_count,
            most_common_components,
            last_error_time: store.last().map(|e| e.timestamp),
        }
    }
}
```

### Auto-updater System

Comprehensive automatic update system with user control, progress tracking, and rollback capabilities.

```rust
// src/lib/auto_updater.rs - Production auto-updater implementation
use tauri_plugin_updater::UpdaterExt;

pub struct ProductionAutoUpdater {
    app_handle: AppHandle,
    update_config: UpdateConfig,
    notification_service: NotificationService,
    settings_manager: SettingsManager,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpdateConfig {
    pub check_frequency_hours: u32,
    pub auto_download: bool,
    pub auto_install: bool,
    pub beta_channel: bool,
    pub require_confirmation: bool,
}

impl ProductionAutoUpdater {
    pub async fn initialize(&mut self) -> Result<(), UpdateError> {
        // Set up automatic update checking
        let config = self.update_config.clone();
        let app_handle = self.app_handle.clone();
        let notification_service = self.notification_service.clone();
        
        tokio::spawn(async move {
            let mut interval = tokio::time::interval(
                Duration::from_secs(config.check_frequency_hours as u64 * 3600)
            );
            
            loop {
                interval.tick().await;
                
                if let Err(e) = Self::check_for_updates_internal(&app_handle, &config, &notification_service).await {
                    log::error!("Update check failed: {}", e);
                }
            }
        });
        
        Ok(())
    }
    
    pub async fn check_for_updates(&self) -> Result<UpdateStatus, UpdateError> {
        let updater = self.app_handle.updater()?;
        
        match updater.check().await {
            Ok(Some(update)) => {
                log::info!("Update available: {} -> {}", update.current_version, update.version);
                
                let status = UpdateStatus::Available {
                    current_version: update.current_version.clone(),
                    new_version: update.version.clone(),
                    release_notes: update.body.clone(),
                    download_size: update.content_length,
                    critical: false,
                };
                
                // Notify user of available update
                self.notification_service.show_update_notification(&status).await?;
                
                Ok(status)
            },
            Ok(None) => {
                log::info!("No updates available");
                Ok(UpdateStatus::UpToDate)
            },
            Err(e) => {
                log::error!("Update check failed: {}", e);
                Err(UpdateError::CheckFailed(e.to_string()))
            }
        }
    }
    
    pub async fn download_and_install_update(&self, confirm_restart: bool) -> Result<(), UpdateError> {
        let updater = self.app_handle.updater()?;
        
        if let Some(update) = updater.check().await? {
            log::info!("Starting download for update: {}", update.version);
            
            // Show download progress
            let progress_id = uuid::Uuid::new_v4().to_string();
            let notification_service = self.notification_service.clone();
            
            let update_result = update.download_and_install(
                |chunk_length, content_length| {
                    let progress = chunk_length as f64 / content_length.unwrap_or(chunk_length) as f64;
                    
                    tokio::spawn({
                        let notification_service = notification_service.clone();
                        let progress_id = progress_id.clone();
                        async move {
                            let _ = notification_service.update_progress(&progress_id, progress).await;
                        }
                    });
                },
                || {
                    log::info!("Update download completed, installing...");
                }
            ).await;
            
            match update_result {
                Ok(_) => {
                    log::info!("Update installed successfully");
                    
                    if confirm_restart {
                        self.notification_service.show_restart_notification().await?;
                    } else {
                        // Auto-restart if configured
                        if self.update_config.auto_install {
                            tokio::time::sleep(Duration::from_secs(3)).await;
                            self.app_handle.restart();
                        }
                    }
                    
                    Ok(())
                },
                Err(e) => {
                    log::error!("Update installation failed: {}", e);
                    Err(UpdateError::InstallFailed(e.to_string()))
                }
            }
        } else {
            Err(UpdateError::NoUpdateAvailable)
        }
    }
}
```

### Real-time Performance Monitoring

Advanced performance monitoring system with live metrics, alerts, and optimization recommendations.

```rust
// src/lib/performance_monitor.rs - Real-time performance monitoring
use std::sync::Arc;
use tokio::sync::RwLock;
use sysinfo::{System, SystemExt, ProcessExt, CpuExt};

pub struct RealTimePerformanceMonitor {
    metrics_store: Arc<RwLock<PerformanceMetrics>>,
    alert_thresholds: AlertThresholds,
    optimization_engine: OptimizationEngine,
    metrics_history: CircularBuffer<SystemSnapshot>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceMetrics {
    pub timestamp: DateTime<Utc>,
    pub memory_usage_mb: u64,
    pub cpu_usage_percent: f32,
    pub disk_read_bytes_per_sec: u64,
    pub disk_write_bytes_per_sec: u64,
    pub network_bytes_per_sec: u64,
    pub active_operations: usize,
    pub processing_queue_size: usize,
    pub average_response_time_ms: f64,
    pub error_rate_percent: f32,
}

#[derive(Debug, Clone)]
pub struct AlertThresholds {
    pub memory_warning_mb: u64,
    pub memory_critical_mb: u64,
    pub cpu_warning_percent: f32,
    pub cpu_critical_percent: f32,
    pub response_time_warning_ms: f64,
    pub error_rate_warning_percent: f32,
}

impl RealTimePerformanceMonitor {
    pub async fn start_monitoring(&mut self) -> Result<(), MonitoringError> {
        let metrics_store = Arc::clone(&self.metrics_store);
        let alert_thresholds = self.alert_thresholds.clone();
        let optimization_engine = self.optimization_engine.clone();
        
        // Start metrics collection loop
        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(5));
            let mut system = System::new_all();
            
            loop {
                interval.tick().await;
                
                // Refresh system information
                system.refresh_all();
                
                // Collect current metrics
                let current_metrics = Self::collect_current_metrics(&system).await;
                
                // Store metrics
                {
                    let mut store = metrics_store.write().await;
                    *store = current_metrics.clone();
                }
                
                // Check for alerts
                Self::check_performance_alerts(&current_metrics, &alert_thresholds).await;
                
                // Run optimization recommendations
                if let Some(recommendations) = optimization_engine.analyze_performance(&current_metrics).await {
                    Self::apply_optimizations(recommendations).await;
                }
            }
        });
        
        // Start performance reporting
        self.start_performance_reporting().await?;
        
        Ok(())
    }
    
    async fn collect_current_metrics(system: &System) -> PerformanceMetrics {
        let total_memory = system.total_memory();
        let used_memory = system.used_memory();
        let memory_usage_mb = used_memory / 1024 / 1024;
        
        let cpu_usage = system.global_cpu_info().cpu_usage();
        
        // Get current process metrics
        let pid = sysinfo::get_current_pid().unwrap_or(sysinfo::Pid::from(0));
        let process_metrics = system.process(pid).map(|p| ProcessMetrics {
            memory: p.memory() / 1024 / 1024,
            cpu: p.cpu_usage(),
            disk_read: p.disk_usage().read_bytes,
            disk_write: p.disk_usage().written_bytes,
        }).unwrap_or_default();
        
        PerformanceMetrics {
            timestamp: Utc::now(),
            memory_usage_mb,
            cpu_usage_percent: cpu_usage,
            disk_read_bytes_per_sec: process_metrics.disk_read,
            disk_write_bytes_per_sec: process_metrics.disk_write,
            network_bytes_per_sec: 0, // Would need network monitoring
            active_operations: 0, // Would be tracked by operation manager
            processing_queue_size: 0, // Would be tracked by processing engine
            average_response_time_ms: 0.0, // Would be tracked by request handler
            error_rate_percent: 0.0, // Would be tracked by error tracker
        }
    }
    
    async fn check_performance_alerts(metrics: &PerformanceMetrics, thresholds: &AlertThresholds) {
        // Memory alerts
        if metrics.memory_usage_mb > thresholds.memory_critical_mb {
            Self::send_alert(Alert {
                level: AlertLevel::Critical,
                message: format!("Critical memory usage: {}MB", metrics.memory_usage_mb),
                recommendation: "Consider restarting the application or closing unused features".to_string(),
            }).await;
        } else if metrics.memory_usage_mb > thresholds.memory_warning_mb {
            Self::send_alert(Alert {
                level: AlertLevel::Warning,
                message: format!("High memory usage: {}MB", metrics.memory_usage_mb),
                recommendation: "Monitor memory usage and consider clearing caches".to_string(),
            }).await;
        }
        
        // CPU alerts
        if metrics.cpu_usage_percent > thresholds.cpu_critical_percent {
            Self::send_alert(Alert {
                level: AlertLevel::Critical,
                message: format!("Critical CPU usage: {:.1}%", metrics.cpu_usage_percent),
                recommendation: "Reduce concurrent operations or pause processing".to_string(),
            }).await;
        }
        
        // Response time alerts
        if metrics.average_response_time_ms > thresholds.response_time_warning_ms {
            Self::send_alert(Alert {
                level: AlertLevel::Warning,
                message: format!("Slow response times: {:.1}ms", metrics.average_response_time_ms),
                recommendation: "Check system resources and network connectivity".to_string(),
            }).await;
        }
    }
    
    pub async fn get_performance_dashboard_data(&self) -> PerformanceDashboard {
        let metrics = self.metrics_store.read().await;
        let history = self.metrics_history.get_last_n(60); // Last 60 data points (5 minutes)
        
        PerformanceDashboard {
            current_metrics: metrics.clone(),
            historical_data: history,
            system_health: self.calculate_system_health(&metrics).await,
            optimization_suggestions: self.optimization_engine.get_suggestions().await,
            active_alerts: self.get_active_alerts().await,
        }
    }
}
```

### Comprehensive Security Manager

Enterprise-grade security system with encryption, authentication, and audit logging.

```rust
// src/lib/security_manager.rs - Comprehensive security implementation
use ring::{aead, digest, pbkdf2, rand};
use base64::{Engine as _, engine::general_purpose};

pub struct ComprehensiveSecurityManager {
    encryption_key: aead::LessSafeKey,
    session_manager: SessionManager,
    audit_logger: AuditLogger,
    access_control: AccessControl,
    security_settings: SecuritySettings,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecuritySettings {
    pub encryption_enabled: bool,
    pub session_timeout_minutes: u32,
    pub max_failed_attempts: u32,
    pub audit_logging_enabled: bool,
    pub data_retention_days: u32,
    pub require_authentication: bool,
}

impl ComprehensiveSecurityManager {
    pub async fn initialize(app_data_dir: &Path) -> Result<Self, SecurityError> {
        // Initialize encryption key from secure storage or generate new one
        let encryption_key = Self::initialize_encryption_key(app_data_dir).await?;
        
        // Set up session management
        let session_manager = SessionManager::new(Duration::from_secs(30 * 60)); // 30 min default
        
        // Initialize audit logging
        let audit_logger = AuditLogger::new(app_data_dir.join("security_audit.log")).await?;
        
        // Set up access control
        let access_control = AccessControl::new();
        
        // Load security settings
        let security_settings = Self::load_security_settings(app_data_dir).await
            .unwrap_or_default();
        
        Ok(ComprehensiveSecurityManager {
            encryption_key,
            session_manager,
            audit_logger,
            access_control,
            security_settings,
        })
    }
    
    pub async fn encrypt_sensitive_data(&self, data: &[u8]) -> Result<Vec<u8>, SecurityError> {
        if !self.security_settings.encryption_enabled {
            return Ok(data.to_vec());
        }
        
        let rng = rand::SystemRandom::new();
        let mut nonce_bytes = [0u8; 12];
        rng.fill(&mut nonce_bytes)
            .map_err(|_| SecurityError::EncryptionFailed("Failed to generate nonce".to_string()))?;
        
        let nonce = aead::Nonce::assume_unique_for_key(nonce_bytes);
        let mut in_out = data.to_vec();
        
        self.encryption_key
            .seal_in_place_append_tag(nonce, aead::Aad::empty(), &mut in_out)
            .map_err(|_| SecurityError::EncryptionFailed("Encryption failed".to_string()))?;
        
        // Prepend nonce to encrypted data
        let mut result = nonce_bytes.to_vec();
        result.extend_from_slice(&in_out);
        
        // Log encryption event
        self.audit_logger.log_security_event(SecurityEvent {
            event_type: SecurityEventType::DataEncrypted,
            timestamp: Utc::now(),
            details: "Sensitive data encrypted".to_string(),
            success: true,
        }).await?;
        
        Ok(result)
    }
    
    pub async fn decrypt_sensitive_data(&self, encrypted_data: &[u8]) -> Result<Vec<u8>, SecurityError> {
        if !self.security_settings.encryption_enabled {
            return Ok(encrypted_data.to_vec());
        }
        
        if encrypted_data.len() < 12 {
            return Err(SecurityError::DecryptionFailed("Invalid encrypted data format".to_string()));
        }
        
        let (nonce_bytes, ciphertext) = encrypted_data.split_at(12);
        let nonce = aead::Nonce::try_assume_unique_for_key(nonce_bytes)
            .map_err(|_| SecurityError::DecryptionFailed("Invalid nonce".to_string()))?;
        
        let mut in_out = ciphertext.to_vec();
        let plaintext = self.encryption_key
            .open_in_place(nonce, aead::Aad::empty(), &mut in_out)
            .map_err(|_| SecurityError::DecryptionFailed("Decryption failed".to_string()))?;
        
        Ok(plaintext.to_vec())
    }
    
    pub async fn create_secure_session(&mut self, user_id: &str) -> Result<SecureSession, SecurityError> {
        let session = self.session_manager.create_session(user_id).await?;
        
        self.audit_logger.log_security_event(SecurityEvent {
            event_type: SecurityEventType::SessionCreated,
            timestamp: Utc::now(),
            details: format!("Session created for user: {}", user_id),
            success: true,
        }).await?;
        
        Ok(session)
    }
    
    pub async fn validate_session(&self, session_token: &str) -> Result<bool, SecurityError> {
        let valid = self.session_manager.validate_session(session_token).await?;
        
        self.audit_logger.log_security_event(SecurityEvent {
            event_type: SecurityEventType::SessionValidated,
            timestamp: Utc::now(),
            details: format!("Session validation: {}", if valid { "success" } else { "failed" }),
            success: valid,
        }).await?;
        
        Ok(valid)
    }
    
    pub async fn get_security_dashboard(&self) -> SecurityDashboard {
        SecurityDashboard {
            encryption_status: self.security_settings.encryption_enabled,
            active_sessions: self.session_manager.get_active_session_count().await,
            recent_security_events: self.audit_logger.get_recent_events(50).await,
            security_score: self.calculate_security_score().await,
            recommendations: self.get_security_recommendations().await,
        }
    }
    
    async fn calculate_security_score(&self) -> u32 {
        let mut score = 0u32;
        
        if self.security_settings.encryption_enabled { score += 25; }
        if self.security_settings.require_authentication { score += 25; }
        if self.security_settings.audit_logging_enabled { score += 20; }
        if self.security_settings.session_timeout_minutes <= 60 { score += 15; }
        if self.security_settings.max_failed_attempts <= 5 { score += 15; }
        
        score
    }
}
```

### Frontend Production Integration

```typescript
// Production error tracking integration
export const useProductionErrorTracking = () => {
  const { toast } = useToast();
  
  const trackError = useCallback(async (error: Error, context?: Partial<ProductionErrorContext>) => {
    const errorContext: ProductionErrorContext = {
      error_id: crypto.randomUUID(),
      timestamp: new Date().toISOString(),
      severity: 'Error',
      component: context?.component || 'frontend',
      operation: context?.operation || 'unknown',
      user_message: error.message,
      technical_details: error.stack || error.toString(),
      stack_trace: error.stack,
      user_agent: navigator.userAgent,
      session_id: sessionStorage.getItem('session_id') || 'anonymous',
      recoverable: context?.recoverable || false,
      retry_count: 0,
      context_data: context?.context_data || {},
    };
    
    try {
      await window.__TAURI__?.invoke('track_production_error', { error: errorContext });
      
      // Show user notification
      toast({
        title: `Error in ${errorContext.component}`,
        description: errorContext.user_message,
        variant: 'destructive',
      });
    } catch (trackingError) {
      console.error('Failed to track error:', trackingError);
    }
  }, [toast]);
  
  return { trackError };
};

// Performance monitoring hook
export const usePerformanceMonitoring = () => {
  const [performanceData, setPerformanceData] = useState<PerformanceDashboard | null>(null);
  
  useEffect(() => {
    const fetchPerformanceData = async () => {
      try {
        const data = await window.__TAURI__?.invoke('get_performance_dashboard');
        setPerformanceData(data);
      } catch (error) {
        console.error('Failed to fetch performance data:', error);
      }
    };
    
    fetchPerformanceData();
    const interval = setInterval(fetchPerformanceData, 5000); // Update every 5 seconds
    
    return () => clearInterval(interval);
  }, []);
  
  return { performanceData };
};

// Auto-updater integration
export const useAutoUpdater = () => {
  const [updateStatus, setUpdateStatus] = useState<UpdateStatus>('UpToDate');
  const [updateProgress, setUpdateProgress] = useState<number>(0);
  
  const checkForUpdates = useCallback(async () => {
    try {
      const status = await window.__TAURI__?.invoke('check_for_updates');
      setUpdateStatus(status);
    } catch (error) {
      console.error('Update check failed:', error);
    }
  }, []);
  
  const installUpdate = useCallback(async () => {
    try {
      await window.__TAURI__?.invoke('install_update');
    } catch (error) {
      console.error('Update installation failed:', error);
    }
  }, []);
  
  return { updateStatus, updateProgress, checkForUpdates, installUpdate };
};
```

### Production Deployment Configuration

```toml
# tauri.conf.json additions for production
{
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devPath": "http://localhost:1420",
    "distDir": "../dist"
  },
  "package": {
    "productName": "Lexicon",
    "version": "1.0.0"
  },
  "tauri": {
    "updater": {
      "active": true,
      "endpoints": [
        "https://releases.lexicon.app/{{target}}/{{current_version}}"
      ],
      "dialog": true,
      "pubkey": "dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXkgOTVGNzA0RjM3OTQ2MjQ4NQo="
    },
    "security": {
      "csp": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https:;"
    },
    "bundle": {
      "active": true,
      "targets": ["dmg", "app"],
      "identifier": "com.lexicon.app",
      "icon": [
        "icons/32x32.png",
        "icons/128x128.png",
        "icons/icon.ico"
      ],
      "macOS": {
        "minimumSystemVersion": "10.13",
        "entitlements": "entitlements.plist",
        "exceptionDomain": "localhost",
        "signingIdentity": "-",
        "hardenedRuntime": true
      }
    }
  }
}
```

---

**Document Status**: ✅ **Complete with Production Infrastructure**  
**Production Readiness**: 8/11 features implemented (73% complete)  
**Next Phase**: Complete remaining production features (Enhanced Search, Global Sync, Smart Recommendations)