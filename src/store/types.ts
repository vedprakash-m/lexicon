// State management types for Lexicon

export interface SourceText {
  id: string;
  title: string;
  author?: string;
  language: string;
  sourceType: 'book' | 'article' | 'manuscript' | 'scripture' | 'other';
  filePath?: string;
  url?: string;
  metadata: TextMetadata;
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed';
  createdAt: string;
  updatedAt: string;
}

export interface TextMetadata {
  wordCount?: number;
  characterCount?: number;
  pageCount?: number;
  isbn?: string;
  publisher?: string;
  publicationDate?: string;
  genre?: string;
  tags: string[];
  description?: string;
  encoding?: string;
  fileSizeBytes?: number;
  checksum?: string;
  customFields: Record<string, any>;
}

export interface Dataset {
  id: string;
  name: string;
  description?: string;
  sourceTexts: string[]; // Array of SourceText IDs
  chunks: TextChunk[];
  metadata: DatasetMetadata;
  status: 'draft' | 'processing' | 'ready' | 'archived';
  createdAt: string;
  updatedAt: string;
}

export interface TextChunk {
  id: string;
  content: string;
  metadata: ChunkMetadata;
  weight?: number;
  relationships: ChunkRelationship[];
}

export interface ChunkMetadata {
  wordCount: number;
  characterCount: number;
  language?: string;
  semanticType?: 'narrative' | 'dialogue' | 'description' | 'commentary' | 'verse';
  sourceTextId: string;
  position: ChunkPosition;
  tags: string[];
  customFields: Record<string, any>;
}

export interface ChunkPosition {
  chapter?: number;
  section?: number;
  paragraph?: number;
  line?: number;
  startOffset: number;
  endOffset: number;
}

export interface ChunkRelationship {
  targetChunkId: string;
  relationshipType: 'continuation' | 'reference' | 'commentary' | 'translation';
  strength: number; // 0.0 to 1.0
}

export interface DatasetMetadata {
  totalChunks: number;
  totalWords: number;
  languages: string[];
  chunkingStrategy: ChunkingStrategy;
  exportConfig: ExportConfig;
  customFields: Record<string, any>;
}

export interface ChunkingStrategy {
  type: 'sentence' | 'paragraph' | 'semantic' | 'fixed_size' | 'custom';
  maxTokens?: number;
  overlap?: number;
  separators?: string[];
  preserveStructure: boolean;
}

export interface ExportConfig {
  format: 'jsonl' | 'json' | 'csv' | 'parquet';
  includeMetadata: boolean;
  chunkSizeLimit?: number;
  weightingStrategy?: 'balanced' | 'commentary_focused' | 'translation_first' | 'essential_only';
}

export interface AppSettings {
  theme: 'light' | 'dark' | 'system';
  language: string;
  autoSave: boolean;
  backupFrequency: 'none' | 'daily' | 'weekly' | 'monthly';
  pythonPath?: string;
  defaultChunkingStrategy: ChunkingStrategy;
  defaultExportConfig: ExportConfig;
  notifications: {
    processingComplete: boolean;
    errors: boolean;
    updates: boolean;
  };
}

// Action types for state management
export interface StateActions {
  // Source Text actions
  addSourceText: (sourceText: Omit<SourceText, 'id' | 'createdAt' | 'updatedAt'>) => string;
  updateSourceText: (id: string, updates: Partial<SourceText>) => void;
  deleteSourceText: (id: string) => void;
  setSourceTextStatus: (id: string, status: SourceText['processingStatus']) => void;

  // Dataset actions
  createDataset: (dataset: Omit<Dataset, 'id' | 'createdAt' | 'updatedAt'>) => string;
  updateDataset: (id: string, updates: Partial<Dataset>) => void;
  deleteDataset: (id: string) => void;
  addSourceToDataset: (datasetId: string, sourceTextId: string) => void;
  removeSourceFromDataset: (datasetId: string, sourceTextId: string) => void;
  updateDatasetChunks: (datasetId: string, chunks: TextChunk[]) => void;

  // Settings actions
  updateSettings: (updates: Partial<AppSettings>) => void;
  resetSettings: () => void;

  // Undo/Redo actions
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;

  // Persistence actions
  saveState: () => Promise<void>;
  loadState: () => Promise<void>;
  exportState: () => Promise<string>;
  importState: (data: string) => Promise<void>;

  // UI state actions
  setActiveDataset: (id: string | null) => void;
  setActiveSourceText: (id: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

// Main application state
export interface AppState {
  sourceTexts: Record<string, SourceText>;
  datasets: Record<string, Dataset>;
  settings: AppSettings;
  
  // UI state
  activeDatasetId: string | null;
  activeSourceTextId: string | null;
  isLoading: boolean;
  error: string | null;

  // History for undo/redo
  history: AppState[];
  historyIndex: number;
  maxHistorySize: number;
}

// Store interface combining state and actions
export interface LexiconStore extends AppState, StateActions {}
