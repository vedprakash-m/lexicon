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
        """Find chunks that match a reference text."""
        referenced_chunks = []
        reference_lower = reference_text.lower()
        
        for chunk in chunks:
            # Check if chunk contains the reference
            if (reference_lower in chunk.text.lower() or 
                reference_lower in chunk.section_title.lower() or
                reference_lower in chunk.metadata.get('title', '').lower()):
                referenced_chunks.append(chunk)
        
        return referenced_chunks
    
    def get_relationships(self) -> List[ChunkRelationship]:
        """Get all tracked relationships."""
        return self.relationships
    
    def get_relationships_for_chunk(self, chunk_id: str) -> List[ChunkRelationship]:
        """Get all relationships for a specific chunk."""
        return [rel for rel in self.relationships 
                if rel.source_chunk_id == chunk_id or rel.target_chunk_id == chunk_id]


class MetadataExtractor:
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
            metadata.update(self._extract_entities(chunk))
        
        if self.config.extract_keywords:
            metadata.update(self._extract_keywords(chunk))
        
        if self.config.extract_topics:
            metadata.update(self._extract_topics(chunk))
        
        if self.config.extract_summaries:
            metadata.update(self._extract_summary(chunk))
        
        # Always extract basic metrics
        metadata.update(self._extract_basic_metrics(chunk))
        
        return metadata
    
    def _extract_entities(self, chunk: Chunk) -> Dict[str, Any]:
        """Extract named entities from chunk."""
        if not self.nlp:
            return {}
        
        doc = self.nlp(chunk.text)
        entities = {}
        
        for ent in doc.ents:
            label = ent.label_
            if label not in entities:
                entities[label] = []
            entities[label].append({
                'text': ent.text,
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': float(ent._.get('confidence', 1.0)) if hasattr(ent._, 'confidence') else 1.0
            })
        
        return {
            'entities': entities,
            'entity_count': len(doc.ents),
            'unique_entities': len(set(ent.text.lower() for ent in doc.ents))
        }
    
    def _extract_keywords(self, chunk: Chunk) -> Dict[str, Any]:
        """Extract keywords using frequency analysis."""
        if not self.nlp:
            # Fallback to simple keyword extraction
            return self._simple_keyword_extraction(chunk)
        
        doc = self.nlp(chunk.text)
        
        # Filter tokens (remove stop words, punctuation, etc.)
        keywords = []
        for token in doc:
            if (not token.is_stop and 
                not token.is_punct and 
                not token.is_space and 
                len(token.text) > 2 and
                token.pos_ in ['NOUN', 'PROPN', 'ADJ', 'VERB']):
                keywords.append({
                    'text': token.lemma_.lower(),
                    'pos': token.pos_,
                    'frequency': 1
                })
        
        # Count frequencies
        keyword_freq = {}
        for kw in keywords:
            text = kw['text']
            if text in keyword_freq:
                keyword_freq[text]['frequency'] += 1
            else:
                keyword_freq[text] = kw
        
        # Sort by frequency
        sorted_keywords = sorted(keyword_freq.values(), 
                               key=lambda x: x['frequency'], reverse=True)
        
        return {
            'keywords': sorted_keywords[:20],  # Top 20 keywords
            'keyword_density': len(keywords) / len(doc) if len(doc) > 0 else 0
        }
    
    def _simple_keyword_extraction(self, chunk: Chunk) -> Dict[str, Any]:
        """Simple keyword extraction without spaCy."""
        import string
        from collections import Counter
        
        # Simple stop words list
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                     'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        
        # Clean and tokenize text
        text = chunk.text.lower()
        text = text.translate(str.maketrans('', '', string.punctuation))
        words = text.split()
        
        # Filter words
        filtered_words = [word for word in words 
                         if word not in stop_words and len(word) > 2]
        
        # Count frequencies
        word_freq = Counter(filtered_words)
        
        keywords = [{'text': word, 'frequency': freq, 'pos': 'UNKNOWN'} 
                   for word, freq in word_freq.most_common(20)]
        
        return {
            'keywords': keywords,
            'keyword_density': len(filtered_words) / len(words) if len(words) > 0 else 0
        }
    
    def _extract_topics(self, chunk: Chunk) -> Dict[str, Any]:
        """Extract topic information from chunk."""
        # Simple topic detection based on keywords and patterns
        topics = []
        
        # Domain-specific topic patterns
        topic_patterns = {
            'spiritual': [r'\b(?:god|divine|soul|spirit|meditation|prayer|enlightenment|karma|dharma)\b'],
            'philosophy': [r'\b(?:wisdom|truth|reality|existence|consciousness|being|knowledge)\b'],
            'technical': [r'\b(?:algorithm|function|method|implementation|system|process|analysis)\b'],
            'historical': [r'\b(?:ancient|history|tradition|century|period|era|civilization)\b'],
            'instructional': [r'\b(?:step|procedure|how to|method|technique|practice|exercise)\b']
        }
        
        text_lower = chunk.text.lower()
        
        for topic, patterns in topic_patterns.items():
            matches = 0
            for pattern in patterns:
                matches += len(re.findall(pattern, text_lower))
            
            if matches > 0:
                confidence = min(1.0, matches / 10.0)  # Normalize confidence
                topics.append({
                    'topic': topic,
                    'confidence': confidence,
                    'match_count': matches
                })
        
        return {
            'topics': sorted(topics, key=lambda x: x['confidence'], reverse=True),
            'primary_topic': topics[0]['topic'] if topics else 'general'
        }
    
    def _extract_summary(self, chunk: Chunk) -> Dict[str, Any]:
        """Extract or generate a summary of the chunk."""
        text = chunk.text.strip()
        
        # Simple extractive summary: first and last sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 2:
            summary = text[:200] + "..." if len(text) > 200 else text
        else:
            summary = sentences[0] + " ... " + sentences[-1]
        
        return {
            'summary': summary,
            'sentence_count': len(sentences),
            'avg_sentence_length': sum(len(s) for s in sentences) / len(sentences) if sentences else 0
        }
    
    def _extract_basic_metrics(self, chunk: Chunk) -> Dict[str, Any]:
        """Extract basic text metrics."""
        text = chunk.text
        
        # Character counts
        char_count = len(text)
        char_count_no_spaces = len(text.replace(' ', ''))
        
        # Word counts
        words = text.split()
        word_count = len(words)
        unique_words = len(set(word.lower() for word in words))
        
        # Sentence counts
        sentences = re.split(r'[.!?]+', text)
        sentence_count = len([s for s in sentences if s.strip()])
        
        # Paragraph counts
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        # Readability metrics
        avg_words_per_sentence = word_count / sentence_count if sentence_count > 0 else 0
        avg_chars_per_word = char_count_no_spaces / word_count if word_count > 0 else 0
        
        # Complexity metrics
        complexity_score = self._calculate_complexity_score(text)
        
        return {
            'char_count': char_count,
            'char_count_no_spaces': char_count_no_spaces,
            'word_count': word_count,
            'unique_words': unique_words,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count,
            'avg_words_per_sentence': round(avg_words_per_sentence, 2),
            'avg_chars_per_word': round(avg_chars_per_word, 2),
            'lexical_diversity': round(unique_words / word_count, 3) if word_count > 0 else 0,
            'complexity_score': complexity_score
        }
    
    def _calculate_complexity_score(self, text: str) -> float:
        """Calculate text complexity score (0.0 to 1.0)."""
        words = text.split()
        if not words:
            return 0.0
        
        # Factors that increase complexity
        long_words = sum(1 for word in words if len(word) > 6)
        long_word_ratio = long_words / len(words)
        
        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Sentence complexity (based on punctuation)
        complex_punctuation = len(re.findall(r'[;:()[\]{}"]', text))
        
        # Combine factors
        complexity = (
            long_word_ratio * 0.4 +
            min(avg_word_length / 10, 1.0) * 0.3 +
            min(complex_punctuation / len(words), 1.0) * 0.3
        )
        
        return min(complexity, 1.0)


class AdvancedChunkingEngine:
    """Advanced chunking engine with custom rules and metadata extraction."""
    
    def __init__(self, config: AdvancedChunkingConfig):
        self.config = config
        self.base_engine = ChunkingEngine(config)
        self.relationship_tracker = RelationshipTracker(config)
        self.metadata_extractor = MetadataExtractor(config)
        
    def chunk_with_advanced_features(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[List[Chunk], List[ChunkRelationship]]:
        """Chunk text with all advanced features enabled."""
        # Start with base chunking
        chunks = self.base_engine.chunk_text(text, metadata)
        
        # Apply custom rules if enabled
        if self.config.apply_custom_rules and self.config.custom_rules:
            chunks = self._apply_custom_rules(chunks, text)
        
        # Optimize overlaps if enabled
        if self.config.intelligent_overlap:
            chunks = self._optimize_overlaps(chunks, text)
        
        # Apply dynamic sizing if enabled
        if self.config.dynamic_chunk_sizing:
            chunks = self._apply_dynamic_sizing(chunks)
        
        # Extract advanced metadata
        for chunk in chunks:
            extracted_metadata = self.metadata_extractor.extract_metadata(chunk)
            chunk.metadata.update(extracted_metadata)
        
        # Track relationships if enabled
        if self.config.track_relationships:
            if 'sequential' in self.config.relationship_types:
                self.relationship_tracker.track_sequential_relationships(chunks)
            if 'semantic' in self.config.relationship_types:
                self.relationship_tracker.track_semantic_relationships(chunks)
            if 'entity' in self.config.relationship_types:
                self.relationship_tracker.track_entity_relationships(chunks)
            if 'reference' in self.config.relationship_types:
                self.relationship_tracker.detect_cross_references(chunks)
        
        # Update chunk quality scores
        for chunk in chunks:
            chunk.quality_score = self._calculate_advanced_quality_score(chunk)
        
        relationships = self.relationship_tracker.get_relationships()
        
        return chunks, relationships
    
    def _apply_custom_rules(self, chunks: List[Chunk], original_text: str) -> List[Chunk]:
        """Apply custom chunking rules to modify chunk boundaries."""
        if not self.config.custom_rules:
            return chunks
        
        # Sort rules by priority (highest first)
        sorted_rules = sorted(self.config.custom_rules, key=lambda r: r.priority, reverse=True)
        
        new_chunks = []
        
        for chunk in chunks:
            chunk_start = chunk.start_char
            chunk_end = chunk.end_char
            chunk_text = original_text[chunk_start:chunk_end]
            
            # Find all rule matches in this chunk
            rule_matches = []
            for rule in sorted_rules:
                matches = rule.matches(chunk_text)
                for start, end, metadata in matches:
                    rule_matches.append({
                        'rule': rule,
                        'start': chunk_start + start,
                        'end': chunk_start + end,
                        'metadata': metadata
                    })
            
            # Sort matches by position
            rule_matches.sort(key=lambda m: m['start'])
            
            if not rule_matches:
                new_chunks.append(chunk)
                continue
            
            # Apply rules to split or modify chunks
            current_pos = chunk_start
            
            for match in rule_matches:
                rule = match['rule']
                match_start = match['start']
                match_end = match['end']
                
                if rule.create_boundary:
                    # Create chunk before the boundary
                    if current_pos < match_start:
                        pre_chunk = Chunk(
                            text=original_text[current_pos:match_start],
                            start_char=current_pos,
                            end_char=match_start,
                            chunk_type=chunk.chunk_type,
                            section_title=chunk.section_title,
                            metadata=chunk.metadata.copy()
                        )
                        new_chunks.append(pre_chunk)
                    
                    # Handle the matched content
                    if rule.preserve_match:
                        match_chunk = Chunk(
                            text=original_text[match_start:match_end],
                            start_char=match_start,
                            end_char=match_end,
                            chunk_type=f"{chunk.chunk_type}_rule_match",
                            section_title=chunk.section_title,
                            metadata={**chunk.metadata, **match['metadata'], 'rule_name': rule.name}
                        )
                        new_chunks.append(match_chunk)
                    
                    current_pos = match_end
            
            # Add remaining content
            if current_pos < chunk_end:
                remaining_chunk = Chunk(
                    text=original_text[current_pos:chunk_end],
                    start_char=current_pos,
                    end_char=chunk_end,
                    chunk_type=chunk.chunk_type,
                    section_title=chunk.section_title,
                    metadata=chunk.metadata.copy()
                )
                new_chunks.append(remaining_chunk)
        
        # Filter out chunks that are too small or too large
        filtered_chunks = []
        for chunk in new_chunks:
            chunk_size = len(chunk.text)
            if (chunk_size >= self.config.min_chunk_size and 
                chunk_size <= self.config.max_chunk_size):
                filtered_chunks.append(chunk)
        
        return filtered_chunks
    
    def _optimize_overlaps(self, chunks: List[Chunk], original_text: str) -> List[Chunk]:
        """Optimize overlap between chunks based on content awareness."""
        if len(chunks) <= 1:
            return chunks
        
        optimized_chunks = []
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                # First chunk - no previous overlap
                chunk.overlap_with_previous = 0
                optimized_chunks.append(chunk)
                continue
            
            prev_chunk = optimized_chunks[i - 1]
            
            # Calculate optimal overlap based on content
            optimal_overlap = self._calculate_optimal_overlap(prev_chunk, chunk, original_text)
            
            # Update chunk boundaries
            new_start = max(chunk.start_char - optimal_overlap, prev_chunk.start_char)
            new_text = original_text[new_start:chunk.end_char]
            
            updated_chunk = Chunk(
                text=new_text,
                start_char=new_start,
                end_char=chunk.end_char,
                chunk_id=chunk.chunk_id,
                chunk_type=chunk.chunk_type,
                section_title=chunk.section_title,
                metadata=chunk.metadata.copy(),
                overlap_with_previous=chunk.start_char - new_start,
                overlap_with_next=chunk.overlap_with_next,
                quality_score=chunk.quality_score
            )
            
            # Update previous chunk's overlap_with_next
            prev_chunk.overlap_with_next = max(0, prev_chunk.end_char - new_start)
            
            optimized_chunks.append(updated_chunk)
        
        return optimized_chunks
    
    def _calculate_optimal_overlap(self, prev_chunk: Chunk, current_chunk: Chunk, original_text: str) -> int:
        """Calculate optimal overlap size between two chunks."""
        max_overlap = int(min(len(prev_chunk.text), len(current_chunk.text)) * self.config.overlap_max_ratio)
        min_overlap = int(min(len(prev_chunk.text), len(current_chunk.text)) * self.config.overlap_min_ratio)
        
        if self.config.overlap_optimization == "fixed":
            return self.config.overlap_size
        
        # Content-aware overlap
        prev_text = prev_chunk.text
        current_text = current_chunk.text
        
        # Find natural boundary points (sentence endings)
        sentence_endings = []
        for match in re.finditer(r'[.!?]\s+', prev_text[-max_overlap:]):
            sentence_endings.append(match.end())
        
        if sentence_endings:
            # Use the last sentence boundary within the overlap range
            optimal_overlap = max_overlap - sentence_endings[-1]
        else:
            # Fallback to paragraph or word boundaries
            word_boundaries = []
            for match in re.finditer(r'\s+', prev_text[-max_overlap:]):
                word_boundaries.append(match.start())
            
            if word_boundaries:
                # Use a word boundary near the middle of the overlap range
                middle_target = max_overlap // 2
                closest_boundary = min(word_boundaries, key=lambda x: abs(x - middle_target))
                optimal_overlap = max_overlap - closest_boundary
            else:
                optimal_overlap = self.config.overlap_size
        
        return max(min_overlap, min(optimal_overlap, max_overlap))
    
    def _apply_dynamic_sizing(self, chunks: List[Chunk]) -> List[Chunk]:
        """Apply dynamic chunk sizing based on content complexity."""
        dynamic_chunks = []
        
        for chunk in chunks:
            # Calculate complexity from metadata if available
            complexity = chunk.metadata.get('complexity_score', 0.5)
            
            # Adjust target size based on complexity
            base_size = self.config.max_chunk_size
            complexity_adjustment = (complexity - 0.5) * self.config.complexity_factor
            target_size = int(base_size * (1 + complexity_adjustment))
            
            # Ensure target size is within bounds
            target_size = max(self.config.min_chunk_size, 
                            min(target_size, self.config.max_chunk_size * 2))
            
            current_size = len(chunk.text)
            
            # If chunk is much larger than target, consider splitting
            if current_size > target_size * 1.5:
                # Split the chunk
                split_chunks = self._split_chunk_intelligently(chunk, target_size)
                dynamic_chunks.extend(split_chunks)
            # If chunk is much smaller than target, it might be merged later
            else:
                dynamic_chunks.append(chunk)
        
        # Merge small adjacent chunks if beneficial
        merged_chunks = self._merge_small_chunks(dynamic_chunks)
        
        return merged_chunks
    
    def _split_chunk_intelligently(self, chunk: Chunk, target_size: int) -> List[Chunk]:
        """Split a chunk intelligently at natural boundaries."""
        text = chunk.text
        
        if len(text) <= target_size:
            return [chunk]
        
        # Find split points (sentence boundaries preferred)
        sentence_boundaries = [0]
        for match in re.finditer(r'[.!?]\s+', text):
            sentence_boundaries.append(match.end())
        sentence_boundaries.append(len(text))
        
        splits = []
        current_start = 0
        
        for i in range(1, len(sentence_boundaries)):
            current_end = sentence_boundaries[i]
            current_length = current_end - current_start
            
            # If this segment is close to target size, make a split
            if current_length >= target_size * 0.8:
                split_text = text[current_start:current_end]
                split_chunk = Chunk(
                    text=split_text,
                    start_char=chunk.start_char + current_start,
                    end_char=chunk.start_char + current_end,
                    chunk_id=f"{chunk.chunk_id}_split_{len(splits)}",
                    chunk_type=chunk.chunk_type,
                    section_title=chunk.section_title,
                    metadata=chunk.metadata.copy()
                )
                splits.append(split_chunk)
                current_start = current_end
        
        # Handle remaining text
        if current_start < len(text):
            remaining_text = text[current_start:]
            if len(remaining_text) >= self.config.min_chunk_size:
                remaining_chunk = Chunk(
                    text=remaining_text,
                    start_char=chunk.start_char + current_start,
                    end_char=chunk.end_char,
                    chunk_id=f"{chunk.chunk_id}_split_{len(splits)}",
                    chunk_type=chunk.chunk_type,
                    section_title=chunk.section_title,
                    metadata=chunk.metadata.copy()
                )
                splits.append(remaining_chunk)
            elif splits:
                # Merge with last split if too small
                last_split = splits[-1]
                merged_text = last_split.text + remaining_text
                updated_split = Chunk(
                    text=merged_text,
                    start_char=last_split.start_char,
                    end_char=chunk.end_char,
                    chunk_id=last_split.chunk_id,
                    chunk_type=last_split.chunk_type,
                    section_title=last_split.section_title,
                    metadata=last_split.metadata
                )
                splits[-1] = updated_split
        
        return splits if splits else [chunk]
    
    def _merge_small_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Merge adjacent small chunks if beneficial."""
        if not self.config.merge_small_chunks:
            return chunks
        
        merged = []
        i = 0
        
        while i < len(chunks):
            current_chunk = chunks[i]
            
            # Check if current chunk is small and can be merged with next
            if (i < len(chunks) - 1 and 
                len(current_chunk.text) < self.config.min_chunk_size * 1.5):
                
                next_chunk = chunks[i + 1]
                combined_length = len(current_chunk.text) + len(next_chunk.text)
                
                # Merge if combined size is reasonable
                if combined_length <= self.config.max_chunk_size * 1.2:
                    merged_text = current_chunk.text + " " + next_chunk.text
                    merged_chunk = Chunk(
                        text=merged_text,
                        start_char=current_chunk.start_char,
                        end_char=next_chunk.end_char,
                        chunk_id=f"merged_{current_chunk.chunk_id}_{next_chunk.chunk_id}",
                        chunk_type=current_chunk.chunk_type,
                        section_title=current_chunk.section_title,
                        metadata={**current_chunk.metadata, 'merged': True}
                    )
                    merged.append(merged_chunk)
                    i += 2  # Skip next chunk as it's been merged
                    continue
            
            merged.append(current_chunk)
            i += 1
        
        return merged
    
    def _calculate_advanced_quality_score(self, chunk: Chunk) -> float:
        """Calculate advanced quality score incorporating metadata."""
        base_score = 0.5
        
        # Text length factor
        length = len(chunk.text.strip())
        if length < self.config.min_chunk_size:
            length_score = length / self.config.min_chunk_size * 0.3
        elif length > self.config.max_chunk_size:
            length_score = max(0.3, 1.0 - (length - self.config.max_chunk_size) / self.config.max_chunk_size)
        else:
            length_score = 1.0
        
        # Content quality factors from metadata
        metadata = chunk.metadata
        
        # Sentence structure
        sentence_count = metadata.get('sentence_count', 1)
        if sentence_count == 0:
            sentence_score = 0.1
        else:
            avg_sentence_length = metadata.get('avg_words_per_sentence', 10)
            # Optimal sentence length is around 15-25 words
            if 10 <= avg_sentence_length <= 30:
                sentence_score = 1.0
            else:
                sentence_score = max(0.3, 1.0 - abs(avg_sentence_length - 20) / 50)
        
        # Lexical diversity
        diversity = metadata.get('lexical_diversity', 0.5)
        diversity_score = min(1.0, diversity * 2)  # Higher diversity is better
        
        # Entity and keyword richness
        entity_count = metadata.get('entity_count', 0)
        keyword_count = len(metadata.get('keywords', []))
        content_richness = min(1.0, (entity_count + keyword_count) / 10)
        
        # Complexity appropriateness
        complexity = metadata.get('complexity_score', 0.5)
        complexity_score = 1.0 - abs(complexity - 0.6)  # Moderate complexity is ideal
        
        # Combine all factors
        quality_score = (
            base_score * 0.1 +
            length_score * 0.3 +
            sentence_score * 0.2 +
            diversity_score * 0.15 +
            content_richness * 0.15 +
            complexity_score * 0.1
        )
        
        return min(1.0, max(0.0, quality_score))


# Predefined custom rules for common use cases
def create_structured_scripture_rules() -> List[CustomChunkingRule]:
    """Create custom rules for processing structured scriptures."""
    return [
        CustomChunkingRule(
            name="verse_boundary",
            description="Create boundaries at verse numbers",
            pattern=r'^\d+\.\d+',  # Matches patterns like "2.47" at start of line
            priority=10,
            create_boundary=True,
            boundary_position="before",
            preserve_match=True,
            extract_metadata=True,
            metadata_key="verse_number"
        ),
        CustomChunkingRule(
            name="chapter_boundary", 
            description="Create boundaries at chapter headings",
            pattern=r'(?i)^chapter\s+\d+',
            priority=15,
            create_boundary=True,
            boundary_position="before",
            preserve_match=True,
            extract_metadata=True,
            metadata_key="chapter_title"
        ),
        CustomChunkingRule(
            name="sanskrit_verse",
            description="Preserve Sanskrit verses as complete units",
            pattern=r'[ॐ-ॿ]+.*?[ॐ-ॿ]+',  # Devanagari script range
            priority=5,
            create_boundary=True,
            boundary_position="around",
            preserve_match=True,
            extract_metadata=True,
            metadata_key="sanskrit_verse"
        )
    ]


def create_technical_document_rules() -> List[CustomChunkingRule]:
    """Create custom rules for processing technical documents."""
    return [
        CustomChunkingRule(
            name="code_block",
            description="Preserve code blocks as complete units",
            pattern=r'```.*?```',
            priority=10,
            create_boundary=True,
            boundary_position="around",
            preserve_match=True,
            extract_metadata=True,
            metadata_key="code_block"
        ),
        CustomChunkingRule(
            name="function_definition",
            description="Create boundaries at function definitions",
            pattern=r'(?i)^(?:def|function|class)\s+\w+',
            priority=8,
            create_boundary=True,
            boundary_position="before",
            preserve_match=True,
            extract_metadata=True,
            metadata_key="function_name"
        ),
        CustomChunkingRule(
            name="section_header",
            description="Create boundaries at section headers",
            pattern=r'^#{1,6}\s+.+$',  # Markdown headers
            priority=12,
            create_boundary=True,
            boundary_position="before",
            preserve_match=True,
            extract_metadata=True,
            metadata_key="section_header"
        )
    ]


# Usage example and factory functions
def create_advanced_chunking_config(content_type: str = "general") -> AdvancedChunkingConfig:
    """Create optimized configuration for different content types."""
    config = AdvancedChunkingConfig()
    
    if content_type == "scripture":
        config.custom_rules = create_structured_scripture_rules()
        config.preserve_verse_structure = True
        config.extract_entities = True
        config.extract_topics = True
        config.max_chunk_size = 800  # Smaller chunks for verse-based content
        
    elif content_type == "technical":
        config.custom_rules = create_technical_document_rules()
        config.preserve_citations = True
        config.extract_keywords = True
        config.max_chunk_size = 1200  # Larger chunks for technical content
        config.dynamic_chunk_sizing = True
        
    elif content_type == "academic":
        config.extract_entities = True
        config.extract_keywords = True
        config.detect_cross_references = True
        config.track_relationships = True
        config.max_chunk_size = 1000
        
    return config


if __name__ == "__main__":
    # Example usage
    config = create_advanced_chunking_config("spiritual")
    engine = AdvancedChunkingEngine(config)
    
    sample_text = """
    Chapter 2: The Eternal Reality of the Soul
    
    2.12 Never was there a time when I did not exist, nor you, nor all these kings; 
    nor in the future shall any of us cease to be.
    
    2.13 As the embodied soul continuously passes, in this body, from boyhood to 
    youth to old age, the soul similarly passes into another body at death. 
    A sober person is not bewildered by such a change.
    """
    
    chunks, relationships = engine.chunk_with_advanced_features(sample_text)
    
    print(f"Generated {len(chunks)} chunks with {len(relationships)} relationships")
    for chunk in chunks:
        print(f"Chunk: {chunk.chunk_id}")
        print(f"Quality Score: {chunk.quality_score:.2f}")
        print(f"Metadata: {chunk.metadata}")
        print("---")
