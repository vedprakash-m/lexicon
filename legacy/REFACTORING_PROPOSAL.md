# RAG Pipeline Refactoring Proposal

## Core Architecture Changes

### 1. Document Abstraction Layer

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

class DocumentType(Enum):
    SCRIPTURE = "scripture"
    PDF = "pdf" 
    HTML = "html"
    MARKDOWN = "markdown"
    PLAIN_TEXT = "text"
    JSON = "json"
    XML = "xml"

@dataclass
class ContentUnit:
    """Universal content unit for any document type"""
    id: str
    content: str
    content_type: str  # verse, paragraph, section, etc.
    metadata: Dict[str, Any]
    parent_id: Optional[str] = None
    children_ids: List[str] = None
    
class DocumentProcessor(ABC):
    """Abstract base class for document processing"""
    
    @abstractmethod
    def load(self, source: str) -> Any:
        """Load document from source"""
        pass
    
    @abstractmethod
    def extract_content_units(self) -> List[ContentUnit]:
        """Extract content units from document"""
        pass
    
    @abstractmethod
    def get_document_metadata(self) -> Dict[str, Any]:
        """Get document-level metadata"""
        pass

class ScriptureProcessor(DocumentProcessor):
    """Processor for Vedic scriptures (current implementation)"""
    pass

class PDFProcessor(DocumentProcessor):
    """Processor for PDF documents"""
    pass

class HTMLProcessor(DocumentProcessor):
    """Processor for HTML documents"""
    pass
```

### 2. Intelligent Chunking Engine

```python
from typing import Protocol
import spacy
import nltk
from transformers import AutoTokenizer

class ChunkingStrategy(Protocol):
    def chunk(self, content_units: List[ContentUnit], **kwargs) -> List[Dict]:
        pass

class SemanticChunker:
    """Semantic-aware chunking using NLP"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.nlp = spacy.load("en_core_web_sm")
    
    def chunk_by_semantic_similarity(self, content_units: List[ContentUnit], 
                                   similarity_threshold: float = 0.7) -> List[Dict]:
        """Group content by semantic similarity"""
        pass
    
    def chunk_by_discourse_markers(self, content_units: List[ContentUnit]) -> List[Dict]:
        """Split on discourse markers and topic boundaries"""
        pass

class AdaptiveChunker:
    """Adaptive chunking based on content complexity"""
    
    def chunk_by_complexity(self, content_units: List[ContentUnit]) -> List[Dict]:
        """Adjust chunk size based on content complexity"""
        pass

class TokenAwareChunker:
    """Token-aware chunking for LLM optimization"""
    
    def chunk_by_token_limit(self, content_units: List[ContentUnit], 
                           max_tokens: int = 512, overlap_tokens: int = 50) -> List[Dict]:
        """Chunk with token limits and overlap"""
        pass
```

### 3. Configurable RAG Pipeline

```python
@dataclass
class RAGConfig:
    """Configuration for RAG pipeline"""
    document_type: DocumentType
    chunking_strategies: List[str]
    chunk_size_range: tuple = (100, 1000)
    overlap_ratio: float = 0.1
    semantic_similarity_threshold: float = 0.7
    include_metadata: bool = True
    output_formats: List[str] = ("json", "jsonl")
    quality_threshold: float = 0.8

class UniversalRAGPipeline:
    """Universal RAG pipeline for any document type"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.processor = self._get_processor()
        self.chunkers = self._get_chunkers()
        self.quality_assessor = QualityAssessor()
    
    def process_document(self, source: str) -> Dict[str, Any]:
        """Main pipeline processing method"""
        # 1. Load and parse document
        document = self.processor.load(source)
        content_units = self.processor.extract_content_units()
        
        # 2. Apply chunking strategies
        chunked_results = {}
        for strategy in self.config.chunking_strategies:
            chunker = self.chunkers[strategy]
            chunks = chunker.chunk(content_units)
            chunked_results[strategy] = chunks
        
        # 3. Quality assessment
        quality_scores = self.quality_assessor.assess(chunked_results)
        
        # 4. Export optimized chunks
        return self._export_chunks(chunked_results, quality_scores)
```

### 4. Quality Assessment Framework

```python
class QualityAssessor:
    """Assess chunk quality for RAG optimization"""
    
    def assess_semantic_coherence(self, chunks: List[Dict]) -> float:
        """Measure semantic coherence within chunks"""
        pass
    
    def assess_information_density(self, chunks: List[Dict]) -> float:
        """Measure information density"""
        pass
    
    def assess_retrieval_potential(self, chunks: List[Dict]) -> float:
        """Predict retrieval effectiveness"""
        pass
    
    def recommend_optimizations(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Suggest improvements"""
        pass
```

## Implementation Phases

### Phase 1: Core Abstraction (Weeks 1-2)
- Implement DocumentProcessor abstract base class
- Create ContentUnit data structure
- Refactor existing scripture processors to inherit from base class
- Add configuration system

### Phase 2: Enhanced Chunking (Weeks 3-4)
- Implement semantic chunking algorithms
- Add token-aware chunking
- Create adaptive chunking strategies
- Integrate NLP libraries (spaCy, transformers)

### Phase 3: Quality Framework (Weeks 5-6)
- Build quality assessment tools
- Add chunk optimization recommendations
- Implement automatic parameter tuning
- Create performance benchmarks

### Phase 4: Format Expansion (Weeks 7-8)
- Add PDF processor
- Add HTML/web content processor
- Add Markdown processor
- Create format detection utilities

### Phase 5: Advanced Features (Weeks 9-10)
- Add multi-modal content support
- Implement hierarchical chunking
- Add cross-document relationship detection
- Create RAG-specific embeddings optimization

## Benefits of Refactored Architecture

### 🚀 **Extensibility**
- Easy addition of new document types
- Pluggable chunking strategies
- Configurable quality thresholds

### 🎯 **RAG Optimization**
- Semantic-aware chunking
- Token-limit optimization
- Quality-driven chunk selection

### 🔧 **Maintainability**
- Clear separation of concerns
- Testable components
- Configuration-driven behavior

### 📈 **Performance**
- Adaptive chunk sizing
- Quality assessment feedback loops
- Optimized for different RAG use cases

## Migration Strategy

### Backward Compatibility
- Keep existing scripture-specific methods
- Gradually migrate to new architecture
- Maintain current output formats

### Testing Strategy
- Unit tests for each component
- Integration tests for full pipeline
- Quality regression tests
- Performance benchmarks

### Documentation
- API documentation for new interfaces
- Migration guides for existing users
- Best practices for different document types
- Performance tuning guides
