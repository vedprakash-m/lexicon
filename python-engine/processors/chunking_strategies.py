"""
Text Chunking Strategies

This module provides multiple sophisticated text chunking approaches for creating
high-quality RAG datasets from any text content. Each strategy is optimized for 
different content types and use cases, supporting technical documentation, academic
papers, business documents, literature, legal texts, medical content, educational
materials, web content, religious texts, and any structured text.

Features:
- Semantic chunking based on meaning and context
- Fixed-size chunking with smart boundary detection
- Hierarchical chunking preserving document structure
- Custom chunking rules for universal content types
- Overlap management and boundary optimization
- Quality assessment for generated chunks across all domains

Author: Lexicon Development Team
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from pathlib import Path
import math

# Configure logging
logger = logging.getLogger(__name__)

# Required imports
import numpy as np

# Optional dependencies for advanced features
try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


@dataclass
class Chunk:
    """Represents a text chunk with metadata."""
    
    text: str
    start_char: int
    end_char: int
    chunk_id: str = ""
    chunk_type: str = "text"
    section_title: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    overlap_with_previous: int = 0
    overlap_with_next: int = 0
    quality_score: float = 0.0
    
    def __post_init__(self):
        """Initialize computed properties."""
        if not self.chunk_id:
            self.chunk_id = f"chunk_{self.start_char}_{self.end_char}"
        
        if not self.text.strip():
            logger.warning(f"Empty chunk created: {self.chunk_id}")
    
    @property
    def length(self) -> int:
        """Get chunk length in characters."""
        return len(self.text)
    
    @property
    def word_count(self) -> int:
        """Get chunk word count."""
        return len(self.text.split())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary for serialization."""
        return {
            'text': self.text,
            'start_char': self.start_char,
            'end_char': self.end_char,
            'chunk_id': self.chunk_id,
            'chunk_type': self.chunk_type,
            'section_title': self.section_title,
            'metadata': self.metadata,
            'overlap_with_previous': self.overlap_with_previous,
            'overlap_with_next': self.overlap_with_next,
            'quality_score': self.quality_score,
            'length': self.length,
            'word_count': self.word_count
        }


@dataclass
class ChunkingConfig:
    """Configuration for chunking strategies."""
    
    # General settings
    max_chunk_size: int = 1000  # Maximum characters per chunk
    min_chunk_size: int = 100   # Minimum characters per chunk
    overlap_size: int = 100     # Characters to overlap between chunks
    overlap_ratio: float = 0.1  # Overlap as ratio of chunk size
    
    # Boundary detection
    respect_sentence_boundaries: bool = True
    respect_paragraph_boundaries: bool = True
    respect_section_boundaries: bool = True
    
    # Quality control
    min_quality_score: float = 0.5
    remove_empty_chunks: bool = True
    merge_small_chunks: bool = True
    
    # Domain-specific settings
    preserve_verse_structure: bool = True
    preserve_dialogue: bool = True
    preserve_citations: bool = True
    
    # Advanced features
    use_semantic_similarity: bool = False
    semantic_model: str = "all-MiniLM-L6-v2"
    similarity_threshold: float = 0.7


class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies."""
    
    def __init__(self, config: ChunkingConfig):
        self.config = config
    
    @abstractmethod
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """Chunk text using this strategy."""
        pass
    
    def _calculate_quality_score(self, chunk: Chunk) -> float:
        """Calculate quality score for a chunk."""
        text = chunk.text.strip()
        
        if not text:
            return 0.0
        
        # Base score
        score = 0.5
        
        # Length scoring - prefer chunks close to target size
        target_size = (self.config.max_chunk_size + self.config.min_chunk_size) / 2
        length_ratio = len(text) / target_size
        if 0.5 <= length_ratio <= 1.5:
            score += 0.2
        elif length_ratio < 0.3 or length_ratio > 2.0:
            score -= 0.2
        
        # Content coherence - check for complete sentences
        sentences = re.split(r'[.!?]+', text)
        complete_sentences = [s for s in sentences if s.strip()]
        if len(complete_sentences) >= 2:
            score += 0.1
        
        # Structural integrity - check for balanced punctuation
        open_parens = text.count('(') - text.count(')')
        open_quotes = text.count('"') % 2
        if open_parens == 0 and open_quotes == 0:
            score += 0.1
        
        # Content density - avoid chunks with too much whitespace
        content_ratio = len(text.replace(' ', '').replace('\n', '')) / len(text)
        if content_ratio > 0.7:
            score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _find_sentence_boundaries(self, text: str) -> List[int]:
        """Find sentence boundary positions in text."""
        boundaries = []
        
        # Look for sentence endings
        for match in re.finditer(r'[.!?]+\s+', text):
            boundaries.append(match.end())
        
        # Add text end
        boundaries.append(len(text))
        
        return boundaries
    
    def _find_paragraph_boundaries(self, text: str) -> List[int]:
        """Find paragraph boundary positions in text."""
        boundaries = []
        
        # Look for paragraph breaks (double newlines)
        for match in re.finditer(r'\n\s*\n', text):
            boundaries.append(match.end())
        
        # Add text end
        boundaries.append(len(text))
        
        return boundaries
    
    def _find_section_boundaries(self, text: str) -> List[int]:
        """Find section boundary positions in text."""
        boundaries = []
        
        # Look for section headers
        patterns = [
            r'\n#{1,6}\s+.+\n',  # Markdown headers
            r'\n[A-Z][^.\n]{10,}\n\n',  # Standalone headers
            r'॥\s*\d+\s*॥',  # Sanskrit verse markers
            r'\n\d+\.\d+',  # Numbered sections
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                boundaries.append(match.start())
        
        # Add text end
        boundaries.append(len(text))
        
        return sorted(set(boundaries))


class FixedSizeChunker(ChunkingStrategy):
    """Simple fixed-size chunking with boundary awareness."""
    
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """Chunk text into fixed-size pieces with smart boundaries."""
        if not text.strip():
            return []
        
        chunks = []
        current_pos = 0
        chunk_counter = 0
        
        # Get boundary positions for smart splitting
        sentence_boundaries = self._find_sentence_boundaries(text) if self.config.respect_sentence_boundaries else []
        paragraph_boundaries = self._find_paragraph_boundaries(text) if self.config.respect_paragraph_boundaries else []
        
        while current_pos < len(text):
            # Calculate chunk end position
            target_end = min(current_pos + self.config.max_chunk_size, len(text))
            
            # Find the best boundary to split at
            chunk_end = self._find_best_boundary(
                text, current_pos, target_end, 
                sentence_boundaries, paragraph_boundaries
            )
            
            # Extract chunk text
            chunk_text = text[current_pos:chunk_end].strip()
            
            if chunk_text and len(chunk_text) >= self.config.min_chunk_size:
                chunk = Chunk(
                    text=chunk_text,
                    start_char=current_pos,
                    end_char=chunk_end,
                    chunk_id=f"fixed_{chunk_counter}",
                    chunk_type="fixed_size",
                    metadata=metadata or {}
                )
                
                # Calculate overlap with previous chunk
                if chunks and self.config.overlap_size > 0:
                    prev_chunk = chunks[-1]
                    overlap_start = max(current_pos - self.config.overlap_size, prev_chunk.start_char)
                    chunk.overlap_with_previous = current_pos - overlap_start
                    prev_chunk.overlap_with_next = chunk.overlap_with_previous
                
                chunk.quality_score = self._calculate_quality_score(chunk)
                chunks.append(chunk)
                chunk_counter += 1
            
            # Move to next position with overlap
            current_pos = max(chunk_end - self.config.overlap_size, chunk_end)
            if current_pos >= chunk_end:  # Avoid infinite loop
                current_pos = chunk_end
        
        return chunks
    
    def _find_best_boundary(self, text: str, start: int, target_end: int, 
                           sentence_boundaries: List[int], 
                           paragraph_boundaries: List[int]) -> int:
        """Find the best position to end a chunk."""
        
        # If we're at the end of text, use that
        if target_end >= len(text):
            return len(text)
        
        # Look for paragraph boundary first (preferred)
        if paragraph_boundaries:
            for boundary in paragraph_boundaries:
                if start < boundary <= target_end:
                    return boundary
        
        # Look for sentence boundary
        if sentence_boundaries:
            for boundary in sentence_boundaries:
                if start < boundary <= target_end:
                    return boundary
        
        # Look for word boundary
        word_boundary = self._find_word_boundary(text, target_end)
        if word_boundary > start:
            return word_boundary
        
        # Fall back to target position
        return target_end
    
    def _find_word_boundary(self, text: str, position: int) -> int:
        """Find the nearest word boundary before the given position."""
        # Look backwards for whitespace
        for i in range(position, max(0, position - 50), -1):
            if text[i].isspace():
                return i + 1
        
        return position


class SemanticChunker(ChunkingStrategy):
    """Semantic chunking based on content similarity and meaning."""
    
    def __init__(self, config: ChunkingConfig):
        super().__init__(config)
        self.model = None
        
        if HAS_SENTENCE_TRANSFORMERS and config.use_semantic_similarity:
            try:
                self.model = SentenceTransformer(config.semantic_model)
                logger.info(f"Loaded semantic model: {config.semantic_model}")
            except Exception as e:
                logger.warning(f"Failed to load semantic model: {e}")
                self.model = None
    
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """Chunk text based on semantic similarity."""
        if not text.strip():
            return []
        
        # First, split into sentences
        sentences = self._split_into_sentences(text)
        
        if not sentences:
            return []
        
        # If semantic model is not available, fall back to fixed-size
        if not self.model:
            logger.info("Semantic model not available, falling back to sentence-based chunking")
            return self._sentence_based_chunking(text, sentences, metadata)
        
        # Calculate sentence embeddings
        sentence_embeddings = self.model.encode(sentences)
        
        # Group sentences into chunks based on similarity
        chunks = self._group_by_similarity(text, sentences, sentence_embeddings, metadata)
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Enhanced sentence splitting for structured scriptures
        sentences = []
        
        # Handle verse markers specially
        parts = re.split(r'(॥\s*\d+\s*॥)', text)
        
        for part in parts:
            if re.match(r'॥\s*\d+\s*॥', part):
                # Verse marker - keep as separate sentence
                sentences.append(part.strip())
            else:
                # Regular text - split into sentences
                part_sentences = re.split(r'[.!?]+(?:\s+|$)', part)
                for sentence in part_sentences:
                    sentence = sentence.strip()
                    if sentence and len(sentence) > 10:  # Filter very short fragments
                        sentences.append(sentence)
        
        return [s for s in sentences if s.strip()]
    
    def _sentence_based_chunking(self, text: str, sentences: List[str], 
                                metadata: Optional[Dict[str, Any]]) -> List[Chunk]:
        """Fall back to sentence-based chunking when semantic model is unavailable."""
        chunks = []
        current_chunk = []
        current_length = 0
        start_pos = 0
        chunk_counter = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # Check if adding this sentence would exceed max size
            if (current_chunk and 
                current_length + sentence_length > self.config.max_chunk_size):
                
                # Create chunk from current sentences
                chunk_text = ' '.join(current_chunk)
                chunk_end = start_pos + len(chunk_text)
                
                chunk = Chunk(
                    text=chunk_text,
                    start_char=start_pos,
                    end_char=chunk_end,
                    chunk_id=f"semantic_{chunk_counter}",
                    chunk_type="sentence_based",
                    metadata=metadata or {}
                )
                chunk.quality_score = self._calculate_quality_score(chunk)
                chunks.append(chunk)
                chunk_counter += 1
                
                # Start new chunk
                start_pos = chunk_end
                current_chunk = []
                current_length = 0
            
            current_chunk.append(sentence)
            current_length += sentence_length + 1  # +1 for space
        
        # Add final chunk if any content remains
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk = Chunk(
                text=chunk_text,
                start_char=start_pos,
                end_char=start_pos + len(chunk_text),
                chunk_id=f"semantic_{chunk_counter}",
                chunk_type="sentence_based",
                metadata=metadata or {}
            )
            chunk.quality_score = self._calculate_quality_score(chunk)
            chunks.append(chunk)
        
        return chunks
    
    def _group_by_similarity(self, text: str, sentences: List[str], 
                           embeddings: np.ndarray, 
                           metadata: Optional[Dict[str, Any]]) -> List[Chunk]:
        """Group sentences into chunks based on semantic similarity."""
        if len(sentences) == 0:
            return []
        
        chunks = []
        current_group = [0]  # Start with first sentence
        chunk_counter = 0
        
        for i in range(1, len(sentences)):
            # Calculate similarity with current group
            current_embedding = embeddings[i]
            group_embeddings = embeddings[current_group]
            
            # Calculate average similarity to group
            similarities = cosine_similarity([current_embedding], group_embeddings)[0]
            avg_similarity = np.mean(similarities)
            
            # Check if sentence should be added to current group
            current_length = sum(len(sentences[j]) for j in current_group)
            should_add = (
                avg_similarity >= self.config.similarity_threshold and
                current_length + len(sentences[i]) <= self.config.max_chunk_size
            )
            
            if should_add:
                current_group.append(i)
            else:
                # Create chunk from current group
                chunk = self._create_chunk_from_group(
                    text, sentences, current_group, chunk_counter, metadata
                )
                chunks.append(chunk)
                chunk_counter += 1
                
                # Start new group
                current_group = [i]
        
        # Add final chunk
        if current_group:
            chunk = self._create_chunk_from_group(
                text, sentences, current_group, chunk_counter, metadata
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_chunk_from_group(self, text: str, sentences: List[str], 
                               group_indices: List[int], chunk_id: int,
                               metadata: Optional[Dict[str, Any]]) -> Chunk:
        """Create a chunk from a group of sentence indices."""
        group_sentences = [sentences[i] for i in group_indices]
        chunk_text = ' '.join(group_sentences)
        
        # Find position in original text (approximate)
        start_pos = text.find(group_sentences[0])
        if start_pos == -1:
            start_pos = 0
        
        end_pos = start_pos + len(chunk_text)
        
        chunk = Chunk(
            text=chunk_text,
            start_char=start_pos,
            end_char=end_pos,
            chunk_id=f"semantic_{chunk_id}",
            chunk_type="semantic",
            metadata=metadata or {}
        )
        
        chunk.quality_score = self._calculate_quality_score(chunk)
        return chunk


class HierarchicalChunker(ChunkingStrategy):
    """Hierarchical chunking that preserves document structure."""
    
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """Chunk text hierarchically based on structure."""
        if not text.strip():
            return []
        
        # Parse document structure
        sections = self._parse_document_structure(text)
        
        # Create chunks respecting hierarchy
        chunks = []
        for section in sections:
            section_chunks = self._chunk_section(section, metadata)
            chunks.extend(section_chunks)
        
        return chunks
    
    def _parse_document_structure(self, text: str) -> List[Dict[str, Any]]:
        """Parse text into hierarchical sections."""
        sections = []
        
        # Look for different types of section markers
        patterns = [
            (r'(^|\n)(#{1,6})\s+(.+)(\n|$)', 'markdown_header'),
            (r'(^|\n)([A-Z][^.\n]{10,50})\n\n', 'text_header'), 
            (r'॥\s*(\d+)\s*॥', 'verse_marker'),
            (r'(^|\n)(\d+\.\d+)', 'numbered_section'),
        ]
        
        current_pos = 0
        
        for pattern, section_type in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                if match.start() > current_pos:
                    # Add content before this section
                    content = text[current_pos:match.start()].strip()
                    if content:
                        sections.append({
                            'type': 'content',
                            'title': '',
                            'content': content,
                            'start': current_pos,
                            'end': match.start()
                        })
                
                # Add the section marker
                title = match.group(3) if match.lastindex >= 3 else match.group(0)
                sections.append({
                    'type': section_type,
                    'title': title.strip(),
                    'content': '',
                    'start': match.start(),
                    'end': match.end()
                })
                
                current_pos = match.end()
        
        # Add remaining content
        if current_pos < len(text):
            content = text[current_pos:].strip()
            if content:
                sections.append({
                    'type': 'content',
                    'title': '',
                    'content': content,
                    'start': current_pos,
                    'end': len(text)
                })
        
        return sections
    
    def _chunk_section(self, section: Dict[str, Any], 
                      metadata: Optional[Dict[str, Any]]) -> List[Chunk]:
        """Chunk a single section."""
        content = section['content']
        if not content.strip():
            return []
        
        # For small sections, keep as single chunk
        if len(content) <= self.config.max_chunk_size:
            chunk = Chunk(
                text=content,
                start_char=section['start'],
                end_char=section['end'],
                chunk_id=f"hierarchical_{section['start']}",
                chunk_type="hierarchical",
                section_title=section['title'],
                metadata={**(metadata or {}), 'section_type': section['type']}
            )
            chunk.quality_score = self._calculate_quality_score(chunk)
            return [chunk]
        
        # For larger sections, use fixed-size chunking within the section
        fixed_chunker = FixedSizeChunker(self.config)
        sub_chunks = fixed_chunker.chunk_text(content, metadata)
        
        # Update chunk metadata to include section information
        for chunk in sub_chunks:
            chunk.section_title = section['title']
            chunk.chunk_type = "hierarchical_sub"
            chunk.metadata.update({'section_type': section['type']})
            chunk.start_char += section['start']
            chunk.end_char += section['start']
        
        return sub_chunks


class UniversalContentChunker(ChunkingStrategy):
    """Specialized chunker for any structured content with intelligent domain recognition.
    
    Handles texts with multi-component structure across all domains:
    - Technical documentation: API specs, code examples, procedures
    - Academic papers: abstracts, sections, citations, references
    - Business documents: executive summaries, sections, appendices
    - Legal texts: clauses, subsections, citations, precedents
    - Medical content: procedures, symptoms, treatments, studies
    - Educational materials: lessons, exercises, examples
    - Literature: chapters, verses, stanzas, commentary
    - Religious texts: verses, commentary, translations
    - Web content: articles, sections, metadata
    
    Supports universal content recognition for:
    - Any structured text with sections and subsections
    - Multi-language content with translations
    - Texts with commentary and explanations
    - Documents with citations and references
    - Content with code blocks and examples
    """
    
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """Chunk any structured content preserving sections, subsections, and component structure."""
        """Chunk structured scripture text preserving verse and commentary structure."""
        if not text.strip():
            return []
        
        chunks = []
        
        # First, identify and separate verses from commentary
        verse_sections = self._extract_verse_sections(text)
        
        for section in verse_sections:
            section_chunks = self._chunk_scripture_section(section, metadata)
            chunks.extend(section_chunks)
            chunks.extend(section_chunks)
        
        return chunks
    
    def _extract_verse_sections(self, text: str) -> List[Dict[str, Any]]:
        """Extract verse sections with their components."""
        sections = []
        
        # Look for verse patterns (Sanskrit verse markers)
        verse_pattern = r'(.*?)(॥\s*\d+\s*॥)(.*?)(?=॥\s*\d+\s*॥|$)'
        
        current_pos = 0
        
        for match in re.finditer(verse_pattern, text, re.DOTALL):
            pre_verse = match.group(1).strip()
            verse_marker = match.group(2).strip()
            post_verse = match.group(3).strip()
            
            # Extract verse components from post_verse
            components = self._parse_verse_components(post_verse)
            
            sections.append({
                'type': 'verse_section',
                'verse_marker': verse_marker,
                'pre_verse': pre_verse,
                'components': components,
                'start': match.start(),
                'end': match.end(),
                'full_text': match.group(0)
            })
            
            current_pos = match.end()
        
        # Handle any remaining text that doesn't contain verses
        if current_pos < len(text):
            remaining = text[current_pos:].strip()
            if remaining:
                sections.append({
                    'type': 'general_text',
                    'content': remaining,
                    'start': current_pos,
                    'end': len(text)
                })
        
        return sections
    
    def _parse_verse_components(self, text: str) -> Dict[str, str]:
        """Parse verse components (Sanskrit, translation, synonyms, purport)."""
        components = {}
        
        # Common section headers
        section_patterns = {
            'sanskrit': r'(sanskrit|devanagari)',
            'transliteration': r'(transliteration|iast)',
            'translation': r'(translation|meaning)',
            'synonyms': r'(synonyms|word[\s-]for[\s-]word)',
            'purport': r'(purport|commentary|explanation)'
        }
        
        # Split text by common section headers
        current_text = text
        current_pos = 0
        
        for section_name, pattern in section_patterns.items():
            # Look for section header
            header_match = re.search(rf'\n\s*{pattern}\s*\n', current_text, re.IGNORECASE)
            if header_match:
                # Find where this section ends (next header or end of text)
                start = header_match.end()
                
                # Look for next section
                next_section_start = len(current_text)
                for next_pattern in section_patterns.values():
                    next_match = re.search(rf'\n\s*{next_pattern}\s*\n', 
                                         current_text[start:], re.IGNORECASE)
                    if next_match:
                        next_section_start = min(next_section_start, start + next_match.start())
                
                section_content = current_text[start:next_section_start].strip()
                if section_content:
                    components[section_name] = section_content
        
        # If no headers found, try to identify content by pattern
        if not components:
            components = self._identify_content_by_pattern(text)
        
        return components
    
    def _identify_content_by_pattern(self, text: str) -> Dict[str, str]:
        """Identify content types by patterns when headers are missing."""
        components = {}
        
        lines = text.split('\n')
        current_component = []
        current_type = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line contains Devanagari (Sanskrit)
            if re.search(r'[\u0900-\u097F]', line):
                if current_type != 'sanskrit':
                    if current_component and current_type:
                        components[current_type] = '\n'.join(current_component)
                    current_component = []
                    current_type = 'sanskrit'
                current_component.append(line)
            
            # Check if line looks like transliteration
            elif re.search(r'[āīūēōṁṃṇṛḷṭḍṅñṣś]', line):
                if current_type != 'transliteration':
                    if current_component and current_type:
                        components[current_type] = '\n'.join(current_component)
                    current_component = []
                    current_type = 'transliteration'
                current_component.append(line)
            
            # Check if line looks like synonyms (contains em-dashes or semicolons)
            elif re.search(r'[—;].*—', line) or ' — ' in line:
                if current_type != 'synonyms':
                    if current_component and current_type:
                        components[current_type] = '\n'.join(current_component)
                    current_component = []
                    current_type = 'synonyms'
                current_component.append(line)
            
            # Otherwise, assume it's translation or purport
            else:
                if current_type not in ['translation', 'purport']:
                    if current_component and current_type:
                        components[current_type] = '\n'.join(current_component)
                    current_component = []
                    current_type = 'translation'  # Default to translation
                current_component.append(line)
        
        # Add final component
        if current_component and current_type:
            components[current_type] = '\n'.join(current_component)
        
        return components
    
    def _chunk_scripture_section(self, section: Dict[str, Any], 
                               metadata: Optional[Dict[str, Any]]) -> List[Chunk]:
        """Chunk a structured scripture text section."""
        chunks = []
        
        if section['type'] == 'verse_section':
            # Create chunks for verse components
            verse_marker = section['verse_marker']
            components = section['components']
            
            # Create a comprehensive chunk with all components
            full_content = []
            
            if verse_marker:
                full_content.append(verse_marker)
            
            # Add components in logical order
            component_order = ['sanskrit', 'transliteration', 'translation', 'synonyms', 'purport']
            
            for component_type in component_order:
                if component_type in components:
                    full_content.append(f"\n{component_type.title()}:\n{components[component_type]}")
            
            if full_content:
                chunk_text = '\n'.join(full_content)
                
                chunk = Chunk(
                    text=chunk_text,
                    start_char=section['start'],
                    end_char=section['end'],
                    chunk_id=f"verse_{verse_marker.replace(' ', '_')}",
                    chunk_type="scripture_verse",
                    section_title=verse_marker,
                    metadata={
                        **(metadata or {}),
                        'verse_marker': verse_marker,
                        'components': list(components.keys())
                    }
                )
                chunk.quality_score = self._calculate_quality_score(chunk)
                chunks.append(chunk)
        
        else:
            # Handle general text with fixed-size chunking
            fixed_chunker = FixedSizeChunker(self.config)
            general_chunks = fixed_chunker.chunk_text(section['content'], metadata)
            chunks.extend(general_chunks)
        
        return chunks


class ChunkingEngine:
    """Main engine for managing different chunking strategies."""
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        self.config = config or ChunkingConfig()
        self.strategies = {
            'fixed_size': FixedSizeChunker(self.config),
            'semantic': SemanticChunker(self.config),
            'hierarchical': HierarchicalChunker(self.config),
            'universal_content': UniversalContentChunker(self.config),
            # Backward compatibility
            'spiritual': UniversalContentChunker(self.config)
        }
    
    def chunk_text(self, text: str, strategy: str = 'fixed_size', 
                   metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """Chunk text using the specified strategy."""
        if strategy not in self.strategies:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
        
        chunker = self.strategies[strategy]
        chunks = chunker.chunk_text(text, metadata)
        
        # Post-process chunks
        chunks = self._post_process_chunks(chunks)
        
        return chunks
    
    def _post_process_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Apply post-processing to generated chunks."""
        processed_chunks = []
        
        for chunk in chunks:
            # Remove empty chunks
            if self.config.remove_empty_chunks and not chunk.text.strip():
                continue
            
            # Filter by quality score
            if chunk.quality_score < self.config.min_quality_score:
                logger.debug(f"Filtered low-quality chunk: {chunk.chunk_id}")
                continue
            
            processed_chunks.append(chunk)
        
        # Merge small chunks if configured
        if self.config.merge_small_chunks:
            processed_chunks = self._merge_small_chunks(processed_chunks)
        
        return processed_chunks
    
    def _merge_small_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Merge chunks that are smaller than minimum size."""
        if not chunks:
            return chunks
        
        merged = []
        i = 0
        
        while i < len(chunks):
            current_chunk = chunks[i]
            
            # If chunk is too small and there's a next chunk, try to merge
            if (current_chunk.length < self.config.min_chunk_size and 
                i + 1 < len(chunks)):
                
                next_chunk = chunks[i + 1]
                
                # Check if merging would exceed max size
                combined_length = current_chunk.length + next_chunk.length
                if combined_length <= self.config.max_chunk_size:
                    # Merge the chunks
                    merged_text = current_chunk.text + "\n\n" + next_chunk.text
                    merged_chunk = Chunk(
                        text=merged_text,
                        start_char=current_chunk.start_char,
                        end_char=next_chunk.end_char,
                        chunk_id=f"merged_{current_chunk.chunk_id}_{next_chunk.chunk_id}",
                        chunk_type="merged",
                        section_title=current_chunk.section_title or next_chunk.section_title,
                        metadata={**current_chunk.metadata, **next_chunk.metadata}
                    )
                    merged_chunk.quality_score = (current_chunk.quality_score + next_chunk.quality_score) / 2
                    merged.append(merged_chunk)
                    i += 2  # Skip next chunk since we merged it
                    continue
            
            merged.append(current_chunk)
            i += 1
        
        return merged
    
    def get_chunking_stats(self, chunks: List[Chunk]) -> Dict[str, Any]:
        """Calculate statistics for a set of chunks."""
        if not chunks:
            return {}
        
        lengths = [chunk.length for chunk in chunks]
        word_counts = [chunk.word_count for chunk in chunks]
        quality_scores = [chunk.quality_score for chunk in chunks]
        
        return {
            'total_chunks': len(chunks),
            'total_characters': sum(lengths),
            'total_words': sum(word_counts),
            'avg_chunk_length': sum(lengths) / len(lengths),
            'avg_word_count': sum(word_counts) / len(word_counts),
            'avg_quality_score': sum(quality_scores) / len(quality_scores),
            'min_chunk_length': min(lengths),
            'max_chunk_length': max(lengths),
            'chunk_types': list(set(chunk.chunk_type for chunk in chunks))
        }


# Example usage
if __name__ == "__main__":
    # Example text (Bhagavad Gita verse)
    sample_text = """
    Bg. 2.47
    
    कर्मण्येवाधिकारस्ते मा फलेषु कदाचन ।
    मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि ॥ ४७ ॥
    
    Translation
    You have a right to perform your prescribed duty, but you are not entitled 
    to the fruits of action. Never consider yourself the cause of the results 
    of your activities, and never be attached to not doing your duty.
    
    Synonyms
    karmaṇi — in prescribed duties; eva — certainly; adhikāraḥ — right; te — of you; 
    mā — never; phaleṣu — in the fruits; kadācana — at any time; mā — never; 
    karma-phala — in the result of the work; hetuḥ — cause; bhūḥ — become; 
    mā — never; te — of you; saṅgaḥ — attachment; astu — there should be; 
    akarmaṇi — in not doing prescribed duties.
    
    Purport
    There are three considerations here: prescribed duties, capricious work, 
    and inaction. Prescribed duties refer to activities performed according 
    to one's position in the material world.
    """
    
    # Test different chunking strategies
    config = ChunkingConfig(max_chunk_size=500, use_semantic_similarity=False)
    engine = ChunkingEngine(config)
    
    print("🧪 Testing Chunking Strategies")
    print("=" * 50)
    
    strategies = ['fixed_size', 'hierarchical', 'spiritual']
    
    for strategy in strategies:
        print(f"\nTesting {strategy} chunking:")
        try:
            chunks = engine.chunk_text(sample_text, strategy)
            stats = engine.get_chunking_stats(chunks)
            
            print(f"  Generated {len(chunks)} chunks")
            print(f"  Average length: {stats['avg_chunk_length']:.1f} characters")
            print(f"  Average quality: {stats['avg_quality_score']:.2f}")
            
            for i, chunk in enumerate(chunks):
                preview = chunk.text[:100].replace('\n', ' ') + "..."
                print(f"    Chunk {i+1}: {preview}")
        
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"\n✅ Chunking strategies test completed!")
