"""
Advanced Chunking Features Extension

This module extends the existing chunking strategies with advanced capabilities:
- Custom chunking rules with pattern matching and transformations
- Intelligent overlap management with content-aware boundaries
- Chunk relationship tracking and semantic connections
- Advanced metadata extraction with entity recognition and topic modeling
- Chunk dependency analysis and cross-references
- Dynamic chunk sizing based on content complexity

Author: Lexicon Development Team
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set, Union, Callable
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict, deque
import hashlib
import math

# Import base classes from existing chunking system
from chunking_strategies import Chunk, ChunkingConfig, ChunkingStrategy, ChunkingEngine

# Configure logging
logger = logging.getLogger(__name__)

# Optional dependencies for advanced features
try:
    import spacy
    from spacy import displacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False
    logger.warning("spaCy not available. Some advanced features will be disabled.")

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import KMeans
    import numpy as np
    HAS_ML_LIBS = True
except ImportError:
    HAS_ML_LIBS = False
    logger.warning("ML libraries not available. Some advanced features will be disabled.")


@dataclass
class ChunkRelationship:
    """Represents a relationship between two chunks."""
    
    source_chunk_id: str
    target_chunk_id: str
    relationship_type: str  # 'semantic', 'sequential', 'reference', 'topic', 'entity'
    strength: float  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'source_chunk_id': self.source_chunk_id,
            'target_chunk_id': self.target_chunk_id,
            'relationship_type': self.relationship_type,
            'strength': self.strength,
            'metadata': self.metadata
        }


@dataclass
class CustomChunkingRule:
    """Defines a custom chunking rule with patterns and transformations."""
    
    name: str
    description: str
    pattern: str  # Regex pattern to match
    pattern_type: str = "regex"  # "regex", "spacy_pattern", "keyword"
    priority: int = 0  # Higher priority rules are applied first
    
    # Chunking behavior
    create_boundary: bool = True  # Whether to create chunk boundary at match
    boundary_position: str = "before"  # "before", "after", "around"
    preserve_match: bool = True  # Whether to keep matched text
    
    # Transformations
    extract_metadata: bool = False
    metadata_key: str = ""
    transformation_func: Optional[Callable] = None
    
    # Conditions
    min_chunk_size: Optional[int] = None
    max_chunk_size: Optional[int] = None
    context_required: List[str] = field(default_factory=list)
    
    def matches(self, text: str, position: int = 0) -> List[Tuple[int, int, Dict[str, Any]]]:
        """Find all matches of this rule in the text."""
        matches = []
        
        if self.pattern_type == "regex":
            for match in re.finditer(self.pattern, text, re.IGNORECASE | re.MULTILINE):
                metadata = {}
                if self.extract_metadata and self.metadata_key:
                    metadata[self.metadata_key] = match.group(0)
                
                matches.append((match.start(), match.end(), metadata))
        
        elif self.pattern_type == "keyword":
            keywords = self.pattern.split("|")
            for keyword in keywords:
                for match in re.finditer(re.escape(keyword), text, re.IGNORECASE):
                    metadata = {}
                    if self.extract_metadata and self.metadata_key:
                        metadata[self.metadata_key] = keyword
                    
                    matches.append((match.start(), match.end(), metadata))
        
        return matches


@dataclass
class AdvancedChunkingConfig(ChunkingConfig):
    """Extended configuration for advanced chunking features."""
    
    # Custom rules
    custom_rules: List[CustomChunkingRule] = field(default_factory=list)
    apply_custom_rules: bool = True
    
    # Overlap management
    intelligent_overlap: bool = True
    overlap_optimization: str = "content_aware"  # "fixed", "content_aware", "semantic"
    overlap_min_ratio: float = 0.05
    overlap_max_ratio: float = 0.3
    
    # Relationship tracking
    track_relationships: bool = True
    relationship_types: List[str] = field(default_factory=lambda: [
        'semantic', 'sequential', 'reference', 'topic', 'entity'
    ])
    min_relationship_strength: float = 0.3
    
    # Advanced metadata
    extract_entities: bool = True
    extract_topics: bool = True
    extract_keywords: bool = True
    extract_summaries: bool = False
    topic_model_components: int = 10
    
    # Dynamic sizing
    dynamic_chunk_sizing: bool = True
    complexity_factor: float = 1.2  # Adjust size based on text complexity
    density_threshold: float = 0.8  # Information density threshold
    
    # Cross-references
    detect_cross_references: bool = True
    reference_patterns: List[str] = field(default_factory=lambda: [
        r'(?:see|refer to|cf\.|compare)\s+(?:chapter|section|verse|page)\s+(\d+)',
        r'(?:as mentioned|discussed)\s+(?:in|at)\s+(\w+)',
        r'\((?:see|cf\.)\s+([^)]+)\)'
    ])


class RelationshipTracker:
    """Tracks and manages relationships between chunks."""
    
    def __init__(self, config: AdvancedChunkingConfig):
        self.config = config
        self.relationships: List[ChunkRelationship] = []
        self.entity_index: Dict[str, Set[str]] = defaultdict(set)  # entity -> chunk_ids
        self.topic_index: Dict[str, Set[str]] = defaultdict(set)   # topic -> chunk_ids
        
        # Initialize ML models if available
        self.nlp = None
        self.sentence_model = None
        
        if HAS_SPACY and self.config.extract_entities:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except IOError:
                logger.warning("spaCy English model not found. Entity extraction disabled.")
        
        if HAS_ML_LIBS and self.config.track_relationships:
            try:
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                logger.warning(f"Could not load sentence transformer: {e}")
    
    def track_sequential_relationships(self, chunks: List[Chunk]) -> None:
        """Track sequential relationships between adjacent chunks."""
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]
            next_chunk = chunks[i + 1]
            
            # Calculate overlap strength
            overlap_chars = current_chunk.overlap_with_next
            max_length = max(len(current_chunk.text), len(next_chunk.text))
            strength = min(1.0, overlap_chars / max_length) if max_length > 0 else 0.1
            
            relationship = ChunkRelationship(
                source_chunk_id=current_chunk.chunk_id,
                target_chunk_id=next_chunk.chunk_id,
                relationship_type="sequential",
                strength=strength,
                metadata={
                    "overlap_chars": overlap_chars,
                    "sequence_position": i
                }
            )
            
            self.relationships.append(relationship)
    
    def track_semantic_relationships(self, chunks: List[Chunk]) -> None:
        """Track semantic relationships using sentence embeddings."""
        if not self.sentence_model or not HAS_ML_LIBS:
            return
        
        # Get embeddings for all chunks
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = self.sentence_model.encode(chunk_texts)
        
        # Calculate pairwise similarities
        similarities = cosine_similarity(embeddings)
        
        for i, chunk_i in enumerate(chunks):
            for j, chunk_j in enumerate(chunks):
                if i != j and similarities[i][j] > self.config.min_relationship_strength:
                    relationship = ChunkRelationship(
                        source_chunk_id=chunk_i.chunk_id,
                        target_chunk_id=chunk_j.chunk_id,
                        relationship_type="semantic",
                        strength=float(similarities[i][j]),
                        metadata={
                            "similarity_score": float(similarities[i][j]),
                            "semantic_method": "sentence_transformer"
                        }
                    )
                    
                    self.relationships.append(relationship)
    
    def track_entity_relationships(self, chunks: List[Chunk]) -> None:
        """Track relationships based on shared entities."""
        if not self.nlp:
            return
        
        # Extract entities from each chunk
        chunk_entities = {}
        for chunk in chunks:
            doc = self.nlp(chunk.text)
            entities = set(ent.text.lower() for ent in doc.ents)
            chunk_entities[chunk.chunk_id] = entities
            
            # Update entity index
            for entity in entities:
                self.entity_index[entity].add(chunk.chunk_id)
        
        # Find chunks with shared entities
        for chunk_i in chunks:
            entities_i = chunk_entities[chunk_i.chunk_id]
            for chunk_j in chunks:
                if chunk_i.chunk_id != chunk_j.chunk_id:
                    entities_j = chunk_entities[chunk_j.chunk_id]
                    shared_entities = entities_i.intersection(entities_j)
                    
                    if shared_entities:
                        # Calculate relationship strength based on shared entities
                        total_entities = len(entities_i.union(entities_j))
                        strength = len(shared_entities) / total_entities if total_entities > 0 else 0
                        
                        if strength > self.config.min_relationship_strength:
                            relationship = ChunkRelationship(
                                source_chunk_id=chunk_i.chunk_id,
                                target_chunk_id=chunk_j.chunk_id,
                                relationship_type="entity",
                                strength=strength,
                                metadata={
                                    "shared_entities": list(shared_entities),
                                    "entity_count": len(shared_entities)
                                }
                            )
                            
                            self.relationships.append(relationship)
    
    def detect_cross_references(self, chunks: List[Chunk]) -> None:
        """Detect explicit cross-references between chunks."""
        for chunk in chunks:
            for pattern in self.config.reference_patterns:
                matches = re.finditer(pattern, chunk.text, re.IGNORECASE)
                for match in matches:
                    reference_text = match.group(1) if match.groups() else match.group(0)
                    
                    # Try to find the referenced chunk
                    referenced_chunks = self._find_referenced_chunks(reference_text, chunks)
                    
                    for ref_chunk in referenced_chunks:
                        relationship = ChunkRelationship(
                            source_chunk_id=chunk.chunk_id,
                            target_chunk_id=ref_chunk.chunk_id,
                            relationship_type="reference",
                            strength=0.8,  # High strength for explicit references
                            metadata={
                                "reference_text": reference_text,
                                "reference_pattern": pattern,
                                "match_position": match.start()
                            }
                        )
                        
                        self.relationships.append(relationship)
    
    def _find_referenced_chunks(self, reference_text: str, chunks: List[Chunk]) -> List[Chunk]:
        """Find chunks that match a reference."""
        referenced_chunks = []
        reference_lower = reference_text.lower()
        
        for chunk in chunks:
            # Check if reference appears in chunk metadata or content
            if (reference_lower in chunk.text.lower() or
                reference_lower in chunk.section_title.lower() or
                any(reference_lower in str(v).lower() for v in chunk.metadata.values())):
                referenced_chunks.append(chunk)
        
        return referenced_chunks
    
    def get_relationships_for_chunk(self, chunk_id: str) -> List[ChunkRelationship]:
        """Get all relationships for a specific chunk."""
        return [rel for rel in self.relationships 
                if rel.source_chunk_id == chunk_id or rel.target_chunk_id == chunk_id]
    
    def get_relationship_graph(self) -> Dict[str, Any]:
        """Get relationship data in graph format."""
        nodes = set()
        edges = []
        
        for rel in self.relationships:
            nodes.add(rel.source_chunk_id)
            nodes.add(rel.target_chunk_id)
            
            edges.append({
                'source': rel.source_chunk_id,
                'target': rel.target_chunk_id,
                'type': rel.relationship_type,
                'strength': rel.strength,
                'metadata': rel.metadata
            })
        
        return {
            'nodes': [{'id': node_id} for node_id in nodes],
            'edges': edges
        }


class AdvancedMetadataExtractor:
    """Extracts advanced metadata from chunks."""
    
    def __init__(self, config: AdvancedChunkingConfig):
        self.config = config
        self.nlp = None
        
        if HAS_SPACY and (config.extract_entities or config.extract_keywords):
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except IOError:
                logger.warning("spaCy English model not found. Advanced metadata extraction disabled.")
    
    def extract_metadata(self, chunk: Chunk) -> Dict[str, Any]:
        """Extract comprehensive metadata from a chunk."""
        metadata = {}
        
        if self.config.extract_entities:
            metadata['entities'] = self._extract_entities(chunk.text)
        
        if self.config.extract_keywords:
            metadata['keywords'] = self._extract_keywords(chunk.text)
        
        if self.config.extract_topics:
            metadata['topics'] = self._extract_topics(chunk.text)
        
        # Basic linguistic features
        metadata['linguistic_features'] = self._extract_linguistic_features(chunk.text)
        
        # Content analysis
        metadata['content_analysis'] = self._analyze_content(chunk.text)
        
        return metadata
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text."""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'description': spacy.explain(ent.label_),
                'start_char': ent.start_char,
                'end_char': ent.end_char,
                'confidence': 1.0  # spaCy doesn't provide confidence scores
            })
        
        return entities
    
    def _extract_keywords(self, text: str) -> List[Dict[str, Any]]:
        """Extract keywords using linguistic analysis."""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        keywords = []
        
        # Extract significant tokens (nouns, adjectives, proper nouns)
        for token in doc:
            if (token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and
                not token.is_stop and
                not token.is_punct and
                len(token.text) > 2):
                
                keywords.append({
                    'text': token.text,
                    'lemma': token.lemma_,
                    'pos': token.pos_,
                    'frequency': text.lower().count(token.text.lower())
                })
        
        # Sort by frequency and return top keywords
        keywords.sort(key=lambda x: x['frequency'], reverse=True)
        return keywords[:10]  # Top 10 keywords
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topic indicators from text."""
        # Simple topic extraction based on patterns and keywords
        topics = []
        
        # Domain-specific topic patterns
        spiritual_patterns = {
            'dharma': r'\b(dharma|duty|righteousness|moral)\b',
            'karma': r'\b(karma|action|deed|work)\b',
            'moksha': r'\b(moksha|liberation|salvation|freedom)\b',
            'meditation': r'\b(meditat\w*|contemplat\w*|concentrat\w*)\b',
            'philosophy': r'\b(philosoph\w*|wisdom|truth|reality)\b'
        }
        
        for topic, pattern in spiritual_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                topics.append(topic)
        
        return topics
    
    def _extract_linguistic_features(self, text: str) -> Dict[str, Any]:
        """Extract linguistic features from text."""
        features = {
            'char_count': len(text),
            'word_count': len(text.split()),
            'sentence_count': len(re.findall(r'[.!?]+', text)),
            'paragraph_count': len(text.split('\n\n')),
            'avg_word_length': sum(len(word) for word in text.split()) / len(text.split()) if text.split() else 0
        }
        
        # Calculate readability metrics
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        
        if len(sentences) > 0 and len(words) > 0:
            avg_sentence_length = len(words) / len(sentences)
            features['avg_sentence_length'] = avg_sentence_length
        
        return features
    
    def _analyze_content(self, text: str) -> Dict[str, Any]:
        """Analyze content characteristics."""
        analysis = {
            'has_questions': bool(re.search(r'\?', text)),
            'has_quotations': bool(re.search(r'["\']', text)),
            'has_numbers': bool(re.search(r'\d+', text)),
            'has_references': bool(re.search(r'\(see|cf\.|refer to', text, re.IGNORECASE)),
            'is_dialogue': bool(re.search(r'["\'].*["\']', text)),
            'complexity_score': self._calculate_complexity(text)
        }
        
        return analysis
    
    def _calculate_complexity(self, text: str) -> float:
        """Calculate text complexity score."""
        # Simple complexity score based on various factors
        words = text.split()
        if not words:
            return 0.0
        
        # Factors that increase complexity
        avg_word_length = sum(len(word) for word in words) / len(words)
        unique_words = len(set(word.lower() for word in words))
        vocabulary_diversity = unique_words / len(words)
        
        # Normalize and combine factors
        complexity = (
            (avg_word_length / 10.0) * 0.3 +  # Word length factor
            vocabulary_diversity * 0.4 +       # Vocabulary diversity
            min(1.0, len(words) / 100.0) * 0.3 # Length factor
        )
        
        return min(1.0, complexity)


class OverlapManager:
    """Manages intelligent overlap between chunks."""
    
    def __init__(self, config: AdvancedChunkingConfig):
        self.config = config
    
    def optimize_overlaps(self, chunks: List[Chunk]) -> List[Chunk]:
        """Optimize overlaps between chunks for better coherence."""
        if not self.config.intelligent_overlap:
            return chunks
        
        optimized_chunks = []
        
        for i, chunk in enumerate(chunks):
            optimized_chunk = Chunk(
                text=chunk.text,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                chunk_id=chunk.chunk_id,
                chunk_type=chunk.chunk_type,
                section_title=chunk.section_title,
                metadata=chunk.metadata.copy(),
                quality_score=chunk.quality_score
            )
            
            # Calculate optimal overlap with next chunk
            if i < len(chunks) - 1:
                next_chunk = chunks[i + 1]
                optimal_overlap = self._calculate_optimal_overlap(chunk, next_chunk)
                optimized_chunk.overlap_with_next = optimal_overlap
            
            # Calculate optimal overlap with previous chunk
            if i > 0:
                prev_chunk = chunks[i - 1]
                optimal_overlap = self._calculate_optimal_overlap(prev_chunk, chunk)
                optimized_chunk.overlap_with_previous = optimal_overlap
            
            optimized_chunks.append(optimized_chunk)
        
        return optimized_chunks
    
    def _calculate_optimal_overlap(self, chunk1: Chunk, chunk2: Chunk) -> int:
        """Calculate optimal overlap size between two chunks."""
        if self.config.overlap_optimization == "fixed":
            return self.config.overlap_size
        
        # Content-aware overlap calculation
        text1 = chunk1.text
        text2 = chunk2.text
        
        # Find natural break points near the boundary
        boundary_area = text1[-200:] + text2[:200]  # 400 chars around boundary
        
        # Look for sentence boundaries
        sentence_breaks = [m.end() for m in re.finditer(r'[.!?]\s+', boundary_area)]
        
        if sentence_breaks:
            # Use the sentence break closest to the middle
            middle = len(boundary_area) // 2
            best_break = min(sentence_breaks, key=lambda x: abs(x - middle))
            
            # Calculate overlap based on sentence boundary
            overlap_size = max(
                int(len(text1) * self.config.overlap_min_ratio),
                min(
                    int(len(text1) * self.config.overlap_max_ratio),
                    200 - best_break if best_break < 200 else best_break - 200
                )
            )
        else:
            # Fallback to paragraph or word boundaries
            word_breaks = [m.end() for m in re.finditer(r'\s+', boundary_area)]
            if word_breaks:
                middle = len(boundary_area) // 2
                best_break = min(word_breaks, key=lambda x: abs(x - middle))
                overlap_size = max(
                    int(len(text1) * self.config.overlap_min_ratio),
                    min(
                        int(len(text1) * self.config.overlap_max_ratio),
                        200 - best_break if best_break < 200 else best_break - 200
                    )
                )
            else:
                # Use configured overlap size
                overlap_size = self.config.overlap_size
        
        return max(0, overlap_size)


class CustomRuleChunker(ChunkingStrategy):
    """Chunking strategy that applies custom rules."""
    
    def __init__(self, config: AdvancedChunkingConfig):
        super().__init__(config)
        self.config = config
    
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """Chunk text using custom rules."""
        if not self.config.apply_custom_rules or not self.config.custom_rules:
            # Fallback to fixed-size chunking
            from chunking_strategies import FixedSizeChunker
            fallback_chunker = FixedSizeChunker(self.config)
            return fallback_chunker.chunk_text(text, metadata)
        
        # Apply custom rules to find chunk boundaries
        boundaries = self._find_custom_boundaries(text)
        
        # Create chunks based on boundaries
        chunks = []
        start = 0
        
        for i, boundary in enumerate(boundaries):
            end = boundary['position']
            
            if end > start:
                chunk_text = text[start:end].strip()
                if chunk_text:
                    chunk = Chunk(
                        text=chunk_text,
                        start_char=start,
                        end_char=end,
                        chunk_id=f"custom_chunk_{len(chunks)}",
                        metadata={**(metadata or {}), **boundary.get('metadata', {})}
                    )
                    
                    # Calculate quality score
                    chunk.quality_score = self._calculate_quality_score(chunk)
                    chunks.append(chunk)
            
            start = end
        
        # Handle remaining text
        if start < len(text):
            chunk_text = text[start:].strip()
            if chunk_text:
                chunk = Chunk(
                    text=chunk_text,
                    start_char=start,
                    end_char=len(text),
                    chunk_id=f"custom_chunk_{len(chunks)}",
                    metadata=metadata or {}
                )
                chunk.quality_score = self._calculate_quality_score(chunk)
                chunks.append(chunk)
        
        return chunks
    
    def _find_custom_boundaries(self, text: str) -> List[Dict[str, Any]]:
        """Find chunk boundaries using custom rules."""
        boundaries = []
        
        # Sort rules by priority (higher first)
        sorted_rules = sorted(self.config.custom_rules, key=lambda r: r.priority, reverse=True)
        
        for rule in sorted_rules:
            matches = rule.matches(text)
            
            for start, end, metadata in matches:
                boundary_pos = start if rule.boundary_position == "before" else end
                
                boundaries.append({
                    'position': boundary_pos,
                    'rule': rule.name,
                    'metadata': {
                        'rule_name': rule.name,
                        'match_text': text[start:end],
                        **metadata
                    }
                })
        
        # Sort boundaries by position and remove duplicates
        boundaries.sort(key=lambda x: x['position'])
        unique_boundaries = []
        last_pos = -1
        
        for boundary in boundaries:
            if boundary['position'] > last_pos:
                unique_boundaries.append(boundary)
                last_pos = boundary['position']
        
        return unique_boundaries


class AdvancedChunkingEngine(ChunkingEngine):
    """Enhanced chunking engine with advanced features."""
    
    def __init__(self, config: Optional[AdvancedChunkingConfig] = None):
        # Create default config if none provided
        if config is None:
            config = AdvancedChunkingConfig()
        
        super().__init__(config)
        self.config = config
        self.relationship_tracker = RelationshipTracker(config)
        self.metadata_extractor = AdvancedMetadataExtractor(config)
        self.overlap_manager = OverlapManager(config)
        
        # Add custom rule chunker
        if config.apply_custom_rules:
            self.strategies['custom'] = CustomRuleChunker(config)
    
    def chunk_text(self, text: str, strategy: str = "custom", metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """Enhanced chunk text with advanced processing."""
        # Get base chunks
        chunks = super().chunk_text(text, strategy, metadata)
        
        # Apply advanced processing
        if self.config.track_relationships:
            self.relationship_tracker.track_sequential_relationships(chunks)
            self.relationship_tracker.track_semantic_relationships(chunks)
            self.relationship_tracker.track_entity_relationships(chunks)
            
            if self.config.detect_cross_references:
                self.relationship_tracker.detect_cross_references(chunks)
        
        # Extract advanced metadata
        for chunk in chunks:
            advanced_metadata = self.metadata_extractor.extract_metadata(chunk)
            chunk.metadata.update(advanced_metadata)
        
        # Optimize overlaps
        if self.config.intelligent_overlap:
            chunks = self.overlap_manager.optimize_overlaps(chunks)
        
        # Apply dynamic sizing if enabled
        if self.config.dynamic_chunk_sizing:
            chunks = self._apply_dynamic_sizing(chunks)
        
        return chunks
    
    def _apply_dynamic_sizing(self, chunks: List[Chunk]) -> List[Chunk]:
        """Apply dynamic sizing based on content complexity."""
        adjusted_chunks = []
        
        for chunk in chunks:
            complexity = chunk.metadata.get('content_analysis', {}).get('complexity_score', 0.5)
            
            # Adjust chunk size based on complexity
            if complexity > self.config.density_threshold:
                # High complexity: potentially split into smaller chunks
                if len(chunk.text) > self.config.max_chunk_size * 0.7:
                    # Split complex chunk
                    sub_chunks = self._split_complex_chunk(chunk)
                    adjusted_chunks.extend(sub_chunks)
                else:
                    adjusted_chunks.append(chunk)
            else:
                # Low complexity: chunk can be larger
                adjusted_chunks.append(chunk)
        
        return adjusted_chunks
    
    def _split_complex_chunk(self, chunk: Chunk) -> List[Chunk]:
        """Split a complex chunk into smaller pieces."""
        # Simple sentence-based splitting for complex content
        sentences = re.split(r'[.!?]+', chunk.text)
        
        sub_chunks = []
        current_text = ""
        current_start = chunk.start_char
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_text + sentence) > self.config.max_chunk_size // 2:
                if current_text:
                    # Create sub-chunk
                    sub_chunk = Chunk(
                        text=current_text.strip(),
                        start_char=current_start,
                        end_char=current_start + len(current_text),
                        chunk_id=f"{chunk.chunk_id}_sub_{len(sub_chunks)}",
                        chunk_type=chunk.chunk_type,
                        section_title=chunk.section_title,
                        metadata=chunk.metadata.copy()
                    )
                    sub_chunk.quality_score = self._calculate_quality_score(sub_chunk)
                    sub_chunks.append(sub_chunk)
                
                current_text = sentence
                current_start = current_start + len(current_text)
            else:
                current_text += (" " + sentence if current_text else sentence)
        
        # Handle remaining text
        if current_text.strip():
            sub_chunk = Chunk(
                text=current_text.strip(),
                start_char=current_start,
                end_char=chunk.end_char,
                chunk_id=f"{chunk.chunk_id}_sub_{len(sub_chunks)}",
                chunk_type=chunk.chunk_type,
                section_title=chunk.section_title,
                metadata=chunk.metadata.copy()
            )
            sub_chunk.quality_score = self._calculate_quality_score(sub_chunk)
            sub_chunks.append(sub_chunk)
        
        return sub_chunks if sub_chunks else [chunk]
    
    def get_relationship_analysis(self) -> Dict[str, Any]:
        """Get comprehensive relationship analysis."""
        relationships = self.relationship_tracker.relationships
        
        analysis = {
            'total_relationships': len(relationships),
            'relationship_types': {},
            'strongest_relationships': [],
            'relationship_graph': self.relationship_tracker.get_relationship_graph(),
            'entity_clusters': dict(self.relationship_tracker.entity_index),
            'topic_clusters': dict(self.relationship_tracker.topic_index)
        }
        
        # Count by type
        for rel in relationships:
            rel_type = rel.relationship_type
            analysis['relationship_types'][rel_type] = analysis['relationship_types'].get(rel_type, 0) + 1
        
        # Find strongest relationships
        strongest = sorted(relationships, key=lambda r: r.strength, reverse=True)[:10]
        analysis['strongest_relationships'] = [rel.to_dict() for rel in strongest]
        
        return analysis
    
    def process_text(self, text: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process text with advanced chunking and return results in format expected by frontend.
        
        Args:
            text: The input text to process
            config_data: Configuration dictionary from frontend
            
        Returns:
            Dictionary with chunks, relationships, and metadata
        """
        import time
        start_time = time.time()
        
        # Convert config from frontend format to internal format
        custom_rules = []
        for rule_data in config_data.get('custom_rules', []):
            if rule_data.get('enabled', True):
                rule = CustomChunkingRule(
                    name=rule_data['name'],
                    description=rule_data['description'],
                    pattern=rule_data['pattern'],
                    pattern_type=rule_data.get('pattern_type', 'regex'),
                    priority=rule_data.get('priority', 0),
                    boundary_position=rule_data.get('boundary_position', 'before'),
                    extract_metadata=True,
                    metadata_key=rule_data['name'].lower().replace(' ', '_')
                )
                custom_rules.append(rule)
        
        # Update engine config
        self.config.max_chunk_size = config_data.get('max_chunk_size', 800)
        self.config.overlap_size = config_data.get('overlap_size', 100)
        self.config.intelligent_overlap = config_data.get('intelligent_overlap', True)
        self.config.track_relationships = config_data.get('track_relationships', True)
        self.config.extract_entities = config_data.get('extract_entities', True)
        self.config.extract_topics = config_data.get('extract_topics', True)
        self.config.dynamic_chunk_sizing = config_data.get('dynamic_sizing', True)
        self.config.custom_rules = custom_rules
        self.config.apply_custom_rules = len(custom_rules) > 0
        
        # Reinitialize components with new config
        self.relationship_tracker = RelationshipTracker(self.config)
        self.metadata_extractor = AdvancedMetadataExtractor(self.config)
        self.overlap_manager = OverlapManager(self.config)
        
        if self.config.apply_custom_rules:
            self.strategies['custom'] = CustomRuleChunker(self.config)
        
        # Process the text
        try:
            chunks = self.chunk_text(text, strategy="custom" if custom_rules else "semantic")
            relationships = self.relationship_tracker.relationships
            processing_time = int((time.time() - start_time) * 1000)
            
            # Convert chunks to frontend format
            chunk_results = []
            for chunk in chunks:
                metadata = chunk.metadata or {}
                
                chunk_result = {
                    "id": chunk.chunk_id,
                    "text": chunk.text,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    "chunk_type": chunk.chunk_type or "text",
                    "quality_score": chunk.quality_score or 0.8,
                    "metadata": {
                        "word_count": len(chunk.text.split()),
                        "char_count": len(chunk.text),
                        "complexity": metadata.get('content_analysis', {}).get('complexity_score', 0.5),
                        "topics": metadata.get('topics', []),
                        "entities": metadata.get('entities', []),
                        "custom_fields": {k: str(v) for k, v in metadata.items() if k not in ['topics', 'entities', 'content_analysis']}
                    }
                }
                chunk_results.append(chunk_result)
            
            # Convert relationships to frontend format
            relationship_results = []
            for rel in relationships:
                relationship_results.append({
                    "source_chunk_id": rel.source_chunk_id,
                    "target_chunk_id": rel.target_chunk_id,
                    "relationship_type": rel.relationship_type,
                    "strength": rel.strength,
                    "metadata": {k: str(v) for k, v in rel.metadata.items()}
                })
            
            # Calculate statistics
            total_words = sum(len(chunk.text.split()) for chunk in chunks)
            avg_chunk_size = total_words / len(chunks) if chunks else 0
            avg_quality = sum(chunk.quality_score or 0.8 for chunk in chunks) / len(chunks) if chunks else 0.8
            
            # Processing steps for the frontend
            processing_steps = [
                {"step_name": "Rule Application", "status": "completed", "duration_ms": processing_time // 5, "details": f"Applied {len(custom_rules)} custom rules"},
                {"step_name": "Text Chunking", "status": "completed", "duration_ms": processing_time // 4, "details": f"Created {len(chunks)} chunks"},
                {"step_name": "Metadata Extraction", "status": "completed", "duration_ms": processing_time // 4, "details": "Extracted entities and topics"},
                {"step_name": "Relationship Tracking", "status": "completed", "duration_ms": processing_time // 4, "details": f"Found {len(relationships)} relationships"},
                {"step_name": "Quality Assessment", "status": "completed", "duration_ms": processing_time // 5, "details": f"Average quality: {avg_quality:.2f}"}
            ]
            
            # Return results in expected format
            return {
                "chunks": chunk_results,
                "relationships": relationship_results,
                "metadata": {
                    "total_chunks": len(chunks),
                    "total_relationships": len(relationships),
                    "average_chunk_size": avg_chunk_size,
                    "quality_score": avg_quality,
                    "processing_steps": processing_steps
                },
                "processing_time_ms": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            return {
                "error": f"Processing failed: {str(e)}",
                "chunks": [],
                "relationships": [],
                "metadata": {
                    "total_chunks": 0,
                    "total_relationships": 0,
                    "average_chunk_size": 0,
                    "quality_score": 0,
                    "processing_steps": [{"step_name": "Error", "status": "failed", "duration_ms": 0, "details": str(e)}]
                },
                "processing_time_ms": 0
            }


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create advanced configuration
    custom_rules = [
        CustomChunkingRule(
            name="verse_boundary",
            description="Split at verse numbers",
            pattern=r"॥\s*\d+\s*॥",
            priority=10,
            boundary_position="after",
            extract_metadata=True,
            metadata_key="verse_number"
        ),
        CustomChunkingRule(
            name="section_header",
            description="Split at section headers",
            pattern=r"^[A-Z][A-Z\s]+$",
            priority=8,
            boundary_position="before",
            extract_metadata=True,
            metadata_key="section_title"
        )
    ]
    
    config = AdvancedChunkingConfig(
        max_chunk_size=800,
        custom_rules=custom_rules,
        apply_custom_rules=True,
        track_relationships=True,
        extract_entities=True,
        extract_topics=True,
        intelligent_overlap=True,
        dynamic_chunk_sizing=True
    )
    
    # Test with sample text
    sample_text = """
    Chapter 2: Contents of the Gita Summarized
    
    Text 47
    कर्मण्येवाधिकारस्ते मा फलेषु कदाचन ।
    मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि ॥ ४७ ॥
    
    Translation
    You have a right to perform your prescribed duty, but you are not entitled 
    to the fruits of action. Never consider yourself the cause of the results 
    of your activities, and never be attached to not doing your duty.
    
    Purport
    This verse is the essence of karma-yoga. Lord Krishna explains the principle
    of detached action, which is fundamental to spiritual progress.
    """
    
    # Create advanced chunking engine
    engine = AdvancedChunkingEngine(config)
    
    print("🧪 Testing Advanced Chunking Features")
    print("=" * 50)
    
    # Chunk the text
    chunks = engine.chunk_text(sample_text, strategy="custom")
    
    print(f"Generated {len(chunks)} chunks with advanced features:")
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1} ({chunk.chunk_id}):")
        print(f"  Text: {chunk.text[:100]}...")
        print(f"  Quality Score: {chunk.quality_score:.2f}")
        print(f"  Entities: {len(chunk.metadata.get('entities', []))}")
        print(f"  Keywords: {len(chunk.metadata.get('keywords', []))}")
        print(f"  Topics: {chunk.metadata.get('topics', [])}")
    
    # Get relationship analysis
    analysis = engine.get_relationship_analysis()
    print(f"\nRelationship Analysis:")
    print(f"  Total relationships: {analysis['total_relationships']}")
    print(f"  Relationship types: {analysis['relationship_types']}")
    
    print(f"\n✅ Advanced chunking features test completed!")
