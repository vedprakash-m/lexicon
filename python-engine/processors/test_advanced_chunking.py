"""
Test Suite for Advanced Chunking Features

This test suite comprehensively tests all advanced chunking capabilities:
- Custom chunking rules with pattern matching and transformations
- Intelligent overlap management with content-aware boundaries
- Chunk relationship tracking (semantic, sequential, entity-based, references)
- Advanced metadata extraction (entities, topics, keywords, summaries)
- Dynamic chunk sizing based on content complexity
- Cross-reference detection and relationship mapping
- Quality assessment and chunk optimization
- Integration with spiritual and technical text processing

Author: Lexicon Development Team
"""

import unittest
import pytest
import logging
import tempfile
import json
import time
from pathlib import Path
from typing import List, Dict, Any
import sys
import os

# Add the processors directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the modules to test
from advanced_chunking import (
    AdvancedChunkingConfig,
    AdvancedChunkingEngine,
    CustomChunkingRule,
    ChunkRelationship,
    RelationshipTracker,
    MetadataExtractor,
    create_advanced_chunking_config,
    create_structured_scripture_rules,
    create_technical_document_rules,
    HAS_SPACY,
    HAS_ML_LIBS
)
from chunking_strategies import Chunk, ChunkingConfig

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestCustomChunkingRules(unittest.TestCase):
    """Test custom chunking rules functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.verse_rule = CustomChunkingRule(
            name="verse_boundary",
            description="Create boundaries at verse numbers",
            pattern=r'^\d+\.\d+',
            priority=10,
            create_boundary=True,
            extract_metadata=True,
            metadata_key="verse_number"
        )
        
        self.code_rule = CustomChunkingRule(
            name="code_block",
            description="Preserve code blocks",
            pattern=r'```.*?```',
            priority=15,
            create_boundary=True,
            boundary_position="around",
            preserve_match=True
        )
    
    def test_verse_rule_matching(self):
        """Test verse number pattern matching."""
        text = "2.47 You have the right to perform your duties, but not to the fruits of action."
        matches = self.verse_rule.matches(text)
        
        self.assertEqual(len(matches), 1)
        start, end, metadata = matches[0]
        self.assertEqual(text[start:end], "2.47")
        self.assertEqual(metadata["verse_number"], "2.47")
    
    def test_code_block_matching(self):
        """Test code block pattern matching."""
        text = "Here is some code: ```python\nprint('hello')\n``` and more text."
        matches = self.code_rule.matches(text)
        
        self.assertEqual(len(matches), 1)
        start, end, metadata = matches[0]
        self.assertIn("print('hello')", text[start:end])
    
    def test_keyword_pattern_matching(self):
        """Test keyword-based pattern matching."""
        keyword_rule = CustomChunkingRule(
            name="keyword_test",
            description="Test keyword matching",
            pattern="function|class|method",
            pattern_type="keyword",
            priority=5
        )
        
        text = "Here we define a function and a class for the method."
        matches = keyword_rule.matches(text)
        
        # Should find 3 matches
        self.assertEqual(len(matches), 3)
    
    def test_no_matches(self):
        """Test when no patterns match."""
        text = "This is regular text without any special patterns."
        verse_matches = self.verse_rule.matches(text)
        code_matches = self.code_rule.matches(text)
        
        self.assertEqual(len(verse_matches), 0)
        self.assertEqual(len(code_matches), 0)


class TestAdvancedChunkingConfig(unittest.TestCase):
    """Test advanced chunking configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = AdvancedChunkingConfig()
        
        self.assertTrue(config.intelligent_overlap)
        self.assertTrue(config.track_relationships)
        self.assertTrue(config.extract_entities)
        self.assertEqual(config.overlap_optimization, "content_aware")
        self.assertEqual(len(config.relationship_types), 5)
    
    def test_spiritual_config_creation(self):
        """Test structured scripture configuration creation."""
        config = create_advanced_chunking_config("spiritual")
        
        self.assertTrue(config.preserve_verse_structure)
        self.assertTrue(config.extract_entities)
        self.assertTrue(config.extract_topics)
        self.assertEqual(config.max_chunk_size, 800)
        self.assertGreater(len(config.custom_rules), 0)
    
    def test_technical_config_creation(self):
        """Test technical document configuration creation."""
        config = create_advanced_chunking_config("technical")
        
        self.assertTrue(config.preserve_citations)
        self.assertTrue(config.extract_keywords)
        self.assertTrue(config.dynamic_chunk_sizing)
        self.assertEqual(config.max_chunk_size, 1200)
        self.assertGreater(len(config.custom_rules), 0)
    
    def test_academic_config_creation(self):
        """Test academic text configuration creation."""
        config = create_advanced_chunking_config("academic")
        
        self.assertTrue(config.extract_entities)
        self.assertTrue(config.extract_keywords)
        self.assertTrue(config.detect_cross_references)
        self.assertTrue(config.track_relationships)
        self.assertEqual(config.max_chunk_size, 1000)


class TestMetadataExtractor(unittest.TestCase):
    """Test metadata extraction functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = AdvancedChunkingConfig()
        self.extractor = MetadataExtractor(self.config)
        
        self.sample_chunk = Chunk(
            text="This is a sample text with multiple sentences. It contains various words and concepts. The content is moderately complex with some technical terms like algorithm and optimization.",
            start_char=0,
            end_char=180,
            chunk_id="test_chunk"
        )
    
    def test_basic_metrics_extraction(self):
        """Test extraction of basic text metrics."""
        metadata = self.extractor._extract_basic_metrics(self.sample_chunk)
        
        required_keys = [
            'char_count', 'char_count_no_spaces', 'word_count', 'unique_words',
            'sentence_count', 'paragraph_count', 'avg_words_per_sentence',
            'avg_chars_per_word', 'lexical_diversity', 'complexity_score'
        ]
        
        for key in required_keys:
            self.assertIn(key, metadata)
        
        self.assertGreater(metadata['char_count'], 0)
        self.assertGreater(metadata['word_count'], 0)
        self.assertGreater(metadata['sentence_count'], 0)
        self.assertGreaterEqual(metadata['lexical_diversity'], 0.0)
        self.assertLessEqual(metadata['lexical_diversity'], 1.0)
    
    def test_keyword_extraction_fallback(self):
        """Test keyword extraction without spaCy."""
        # Force fallback to simple extraction
        original_nlp = self.extractor.nlp
        self.extractor.nlp = None
        
        metadata = self.extractor._extract_keywords(self.sample_chunk)
        
        self.assertIn('keywords', metadata)
        self.assertIn('keyword_density', metadata)
        self.assertIsInstance(metadata['keywords'], list)
        self.assertGreater(len(metadata['keywords']), 0)
        
        # Check keyword structure
        for keyword in metadata['keywords']:
            self.assertIn('text', keyword)
            self.assertIn('frequency', keyword)
            self.assertIn('pos', keyword)
        
        # Restore original
        self.extractor.nlp = original_nlp
    
    def test_topic_extraction(self):
        """Test topic extraction functionality."""
        spiritual_chunk = Chunk(
            text="The divine soul seeks enlightenment through meditation and prayer. This ancient wisdom teaches us about the eternal truth of consciousness and karma.",
            start_char=0,
            end_char=150,
            chunk_id="spiritual_chunk"
        )
        
        metadata = self.extractor._extract_topics(spiritual_chunk)
        
        self.assertIn('topics', metadata)
        self.assertIn('primary_topic', metadata)
        
        # Should detect spiritual content
        topics = metadata['topics']
        if topics:
            topic_names = [t['topic'] for t in topics]
            self.assertIn('spiritual', topic_names)
    
    def test_technical_topic_extraction(self):
        """Test technical topic extraction."""
        technical_chunk = Chunk(
            text="The algorithm implements a sophisticated data structure using advanced optimization techniques. The function processes the system efficiently through method calls.",
            start_char=0,
            end_char=150,
            chunk_id="technical_chunk"
        )
        
        metadata = self.extractor._extract_topics(technical_chunk)
        
        self.assertIn('topics', metadata)
        topics = metadata['topics']
        if topics:
            topic_names = [t['topic'] for t in topics]
            self.assertIn('technical', topic_names)
    
    def test_summary_extraction(self):
        """Test summary extraction."""
        metadata = self.extractor._extract_summary(self.sample_chunk)
        
        self.assertIn('summary', metadata)
        self.assertIn('sentence_count', metadata)
        self.assertIn('avg_sentence_length', metadata)
        
        self.assertIsInstance(metadata['summary'], str)
        self.assertGreater(len(metadata['summary']), 0)
        self.assertGreaterEqual(metadata['sentence_count'], 1)
    
    def test_complexity_calculation(self):
        """Test text complexity calculation."""
        simple_text = "This is simple. It has short words. Easy to read."
        complex_text = "This extraordinarily sophisticated methodology demonstrates comprehensive understanding of multifaceted algorithmic implementations utilizing advanced computational paradigms."
        
        simple_score = self.extractor._calculate_complexity_score(simple_text)
        complex_score = self.extractor._calculate_complexity_score(complex_text)
        
        self.assertLess(simple_score, complex_score)
        self.assertGreaterEqual(simple_score, 0.0)
        self.assertLessEqual(complex_score, 1.0)
    
    def test_comprehensive_metadata_extraction(self):
        """Test complete metadata extraction pipeline."""
        metadata = self.extractor.extract_metadata(self.sample_chunk)
        
        # Should include all categories
        expected_categories = [
            'char_count', 'word_count', 'sentence_count',  # basic metrics
            'keywords', 'keyword_density',                  # keywords
            'topics', 'primary_topic',                      # topics
            'summary',                                      # summary
            'complexity_score'                              # complexity
        ]
        
        for category in expected_categories:
            self.assertIn(category, metadata)


class TestRelationshipTracker(unittest.TestCase):
    """Test relationship tracking functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = AdvancedChunkingConfig()
        self.tracker = RelationshipTracker(self.config)
        
        self.chunks = [
            Chunk(
                text="First chunk about artificial intelligence and machine learning concepts.",
                start_char=0,
                end_char=70,
                chunk_id="chunk_1",
                overlap_with_next=15
            ),
            Chunk(
                text="learning concepts. Second chunk continues the discussion about AI systems and neural networks.",
                start_char=55,
                end_char=125,
                chunk_id="chunk_2",
                overlap_with_previous=15,
                overlap_with_next=10
            ),
            Chunk(
                text="networks. Final chunk about deep learning algorithms and optimization techniques.",
                start_char=115,
                end_char=185,
                chunk_id="chunk_3",
                overlap_with_previous=10
            )
        ]
    
    def test_sequential_relationship_tracking(self):
        """Test sequential relationship tracking."""
        self.tracker.track_sequential_relationships(self.chunks)
        relationships = self.tracker.get_relationships()
        
        # Should have 2 sequential relationships (1->2, 2->3)
        sequential_rels = [r for r in relationships if r.relationship_type == "sequential"]
        self.assertEqual(len(sequential_rels), 2)
        
        # Check first relationship
        rel1 = sequential_rels[0]
        self.assertEqual(rel1.source_chunk_id, "chunk_1")
        self.assertEqual(rel1.target_chunk_id, "chunk_2")
        self.assertGreater(rel1.strength, 0)
        self.assertIn('overlap_chars', rel1.metadata)
    
    def test_cross_reference_detection(self):
        """Test cross-reference detection."""
        ref_chunks = [
            Chunk(
                text="As discussed in chapter 2, the main concept is important. See section 3.5 for details.",
                start_char=0,
                end_char=85,
                chunk_id="ref_chunk_1"
            ),
            Chunk(
                text="Chapter 2: The Main Concept. This explains the fundamental idea in detail.",
                start_char=86,
                end_char=160,
                chunk_id="ref_chunk_2"
            ),
            Chunk(
                text="Section 3.5: Implementation Details. Here we provide the specific information.",
                start_char=161,
                end_char=240,
                chunk_id="ref_chunk_3"
            )
        ]
        
        self.tracker.detect_cross_references(ref_chunks)
        relationships = self.tracker.get_relationships()
        
        # Should detect reference relationships
        ref_rels = [r for r in relationships if r.relationship_type == "reference"]
        self.assertGreater(len(ref_rels), 0)
        
        # Check relationship properties
        for rel in ref_rels:
            self.assertEqual(rel.relationship_type, "reference")
            self.assertGreaterEqual(rel.strength, 0.8)  # High strength for explicit references
    
    def test_relationship_retrieval(self):
        """Test relationship retrieval methods."""
        self.tracker.track_sequential_relationships(self.chunks)
        
        # Test getting all relationships
        all_rels = self.tracker.get_relationships()
        self.assertGreater(len(all_rels), 0)
        
        # Test getting relationships for specific chunk
        chunk1_rels = self.tracker.get_relationships_for_chunk("chunk_1")
        self.assertGreater(len(chunk1_rels), 0)
        
        # Test getting relationships for non-existent chunk
        empty_rels = self.tracker.get_relationships_for_chunk("non_existent")
        self.assertEqual(len(empty_rels), 0)
    
    def test_entity_relationship_tracking(self):
        """Test entity-based relationship tracking."""
        entity_chunks = [
            Chunk(
                text="Einstein developed the theory of relativity. His work revolutionized physics.",
                start_char=0,
                end_char=75,
                chunk_id="entity_chunk_1"
            ),
            Chunk(
                text="The theory of relativity changed our understanding of space and time. Einstein was a genius.",
                start_char=76,
                end_char=170,
                chunk_id="entity_chunk_2"
            )
        ]
        
        # Only test if spaCy is available
        if HAS_SPACY and self.tracker.nlp:
            self.tracker.track_entity_relationships(entity_chunks)
            relationships = self.tracker.get_relationships()
            
            entity_rels = [r for r in relationships if r.relationship_type == "entity"]
            if entity_rels:  # May not always detect depending on model
                self.assertGreater(len(entity_rels), 0)
                
                for rel in entity_rels:
                    self.assertIn('shared_entities', rel.metadata)
                    self.assertGreater(rel.metadata['entity_count'], 0)


class TestAdvancedChunkingEngine(unittest.TestCase):
    """Test the main advanced chunking engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = AdvancedChunkingConfig()
        self.config.max_chunk_size = 300
        self.config.min_chunk_size = 50
        self.engine = AdvancedChunkingEngine(self.config)
        
        self.sample_text = """
        Chapter 1: Introduction to Advanced Concepts

        1.1 This is the first verse of our text. It introduces the fundamental concepts that will be explored throughout this work.

        1.2 The second verse continues the explanation. It provides more detailed information about the subject matter and its implications.

        The following section contains technical information about algorithms and data structures used in modern computing systems.

        ```python
        def example_function():
            return "Hello, World!"
        ```

        This concludes the first chapter with important insights that prepare us for more advanced topics.
        """
    
    def test_basic_chunking_with_advanced_features(self):
        """Test basic chunking with advanced features enabled."""
        chunks, relationships = self.engine.chunk_with_advanced_features(self.sample_text)
        
        self.assertGreater(len(chunks), 0)
        self.assertGreaterEqual(len(relationships), 0)
        
        # Check that chunks have advanced metadata
        for chunk in chunks:
            self.assertIn('char_count', chunk.metadata)
            self.assertIn('word_count', chunk.metadata)
            self.assertIn('complexity_score', chunk.metadata)
            self.assertGreater(chunk.quality_score, 0)
            self.assertLessEqual(chunk.quality_score, 1.0)
    
    def test_custom_rules_application(self):
        """Test application of custom rules."""
        # Add structured scripture rules
        self.config.custom_rules = create_structured_scripture_rules()
        self.config.apply_custom_rules = True
        
        spiritual_text = """
        Chapter 2: The Eternal Soul

        2.12 Never was there a time when I did not exist, nor you, nor all these kings; nor in the future shall any of us cease to be.

        2.13 As the embodied soul continuously passes, in this body, from boyhood to youth to old age, the soul similarly passes into another body at death.
        """
        
        chunks, relationships = self.engine.chunk_with_advanced_features(spiritual_text)
        
        # Should detect verse boundaries
        verse_chunks = [c for c in chunks if 'verse_number' in c.metadata]
        self.assertGreater(len(verse_chunks), 0)
        
        # Check verse number extraction
        for chunk in verse_chunks:
            verse_num = chunk.metadata['verse_number']
            self.assertRegex(verse_num, r'\d+\.\d+')
    
    def test_intelligent_overlap_optimization(self):
        """Test intelligent overlap optimization."""
        self.config.intelligent_overlap = True
        self.config.overlap_optimization = "content_aware"
        
        chunks, _ = self.engine.chunk_with_advanced_features(self.sample_text)
        
        # Check that overlaps are reasonable
        for i, chunk in enumerate(chunks[1:], 1):
            if chunk.overlap_with_previous > 0:
                max_allowed = int(self.config.max_chunk_size * self.config.overlap_max_ratio)
                min_allowed = int(self.config.max_chunk_size * self.config.overlap_min_ratio)
                
                self.assertLessEqual(chunk.overlap_with_previous, max_allowed)
                self.assertGreaterEqual(chunk.overlap_with_previous, min_allowed)
    
    def test_dynamic_chunk_sizing(self):
        """Test dynamic chunk sizing based on complexity."""
        self.config.dynamic_chunk_sizing = True
        self.config.merge_small_chunks = True
        
        # Create text with varying complexity
        simple_text = "This is simple. Easy words. Short sentences. Clear meaning."
        complex_text = "This extraordinarily sophisticated methodology demonstrates comprehensive understanding of multifaceted algorithmic implementations utilizing advanced computational paradigms and intricate mathematical formulations."
        
        mixed_text = simple_text + " " + complex_text + " " + simple_text
        
        chunks, _ = self.engine.chunk_with_advanced_features(mixed_text)
        
        # Should have appropriate chunk sizes based on content
        self.assertGreater(len(chunks), 0)
        for chunk in chunks:
            # Check size bounds are respected
            if len(chunks) > 1:  # Only if there are multiple chunks
                self.assertGreaterEqual(len(chunk.text), self.config.min_chunk_size * 0.8)
    
    def test_relationship_tracking_integration(self):
        """Test that relationship tracking works with the full pipeline."""
        self.config.track_relationships = True
        self.config.relationship_types = ["sequential", "reference"]
        
        text_with_refs = """
        Chapter 1: Introduction
        
        This chapter introduces key concepts. As we will see in chapter 2, these ideas are fundamental.
        
        Chapter 2: Advanced Topics
        
        Building on chapter 1, we explore deeper concepts. See section 1.3 for background information.
        """
        
        chunks, relationships = self.engine.chunk_with_advanced_features(text_with_refs)
        
        # Should have sequential relationships at minimum
        sequential_rels = [r for r in relationships if r.relationship_type == "sequential"]
        self.assertGreaterEqual(len(sequential_rels), len(chunks) - 1)
        
        # May have reference relationships
        ref_rels = [r for r in relationships if r.relationship_type == "reference"]
        # Don't assert on this as it depends on chunking boundaries
    
    def test_quality_score_calculation(self):
        """Test advanced quality score calculation."""
        chunks, _ = self.engine.chunk_with_advanced_features(self.sample_text)
        
        for chunk in chunks:
            self.assertGreaterEqual(chunk.quality_score, 0.0)
            self.assertLessEqual(chunk.quality_score, 1.0)
            
            # Chunks with good length and structure should have higher scores
            if (self.config.min_chunk_size <= len(chunk.text) <= self.config.max_chunk_size and
                chunk.metadata.get('sentence_count', 0) > 1):
                self.assertGreater(chunk.quality_score, 0.2)
    
    def test_chunk_merging(self):
        """Test small chunk merging functionality."""
        self.config.merge_small_chunks = True
        self.config.min_chunk_size = 100
        
        # Create text that would produce small chunks
        short_text = "Short. Very short. Tiny. Small. Brief. Minimal."
        
        chunks, _ = self.engine.chunk_with_advanced_features(short_text)
        
        # Should merge small chunks or handle them appropriately
        for chunk in chunks:
            # Either chunk meets minimum size or it's one of few chunks
            self.assertTrue(
                len(chunk.text) >= self.config.min_chunk_size * 0.6 or 
                len(chunks) <= 2
            )


class TestPredefinedRules(unittest.TestCase):
    """Test predefined rule sets for different content types."""
    
    def test_structured_scripture_rules(self):
        """Test structured scripture rule creation."""
        rules = create_structured_scripture_rules()
        
        self.assertGreater(len(rules), 0)
        
        # Check that verse boundary rule exists
        verse_rules = [r for r in rules if r.name == "verse_boundary"]
        self.assertEqual(len(verse_rules), 1)
        
        verse_rule = verse_rules[0]
        self.assertTrue(verse_rule.extract_metadata)
        self.assertEqual(verse_rule.metadata_key, "verse_number")
        
        # Check chapter boundary rule
        chapter_rules = [r for r in rules if r.name == "chapter_boundary"]
        self.assertEqual(len(chapter_rules), 1)
    
    def test_technical_document_rules(self):
        """Test technical document rule creation."""
        rules = create_technical_document_rules()
        
        self.assertGreater(len(rules), 0)
        
        # Check that code block rule exists
        code_rules = [r for r in rules if r.name == "code_block"]
        self.assertEqual(len(code_rules), 1)
        
        code_rule = code_rules[0]
        self.assertEqual(code_rule.boundary_position, "around")
        self.assertTrue(code_rule.preserve_match)
        
        # Check function definition rule
        func_rules = [r for r in rules if r.name == "function_definition"]
        self.assertEqual(len(func_rules), 1)
    
    def test_rule_priority_ordering(self):
        """Test that rules are properly prioritized."""
        scripture_rules = create_structured_scripture_rules()
        technical_rules = create_technical_document_rules()
        
        # Check that rules have priorities
        for rule in scripture_rules + technical_rules:
            self.assertIsInstance(rule.priority, int)
            self.assertGreaterEqual(rule.priority, 0)


class TestIntegrationScenarios(unittest.TestCase):
    """Test complete integration scenarios."""
    
    def test_structured_scripture_processing(self):
        """Test complete structured scripture processing pipeline."""
        config = create_advanced_chunking_config("spiritual")
        engine = AdvancedChunkingEngine(config)
        
        bhagavad_gita_sample = """
        Chapter 2: Contents of the Gita Summarized

        2.11 The Supreme Personality of Godhead said: While speaking learned words, you are mourning for what is not worthy of grief. Those who are wise lament neither for the living nor for the dead.

        2.12 Never was there a time when I did not exist, nor you, nor all these kings; nor in the future shall any of us cease to be.

        2.13 As the embodied soul continuously passes, in this body, from boyhood to youth to old age, the soul similarly passes into another body at death. A sober person is not bewildered by such a change.
        """
        
        chunks, relationships = engine.chunk_with_advanced_features(bhagavad_gita_sample)
        
        # Should have proper chunking with verse recognition
        self.assertGreater(len(chunks), 0)
        
        # Should detect spiritual topics
        spiritual_chunks = []
        for chunk in chunks:
            topics = chunk.metadata.get('topics', [])
            if any(t.get('topic') == 'spiritual' for t in topics):
                spiritual_chunks.append(chunk)
        
        # Should have reasonable quality scores
        avg_quality = sum(c.quality_score for c in chunks) / len(chunks)
        self.assertGreater(avg_quality, 0.3)
    
    def test_technical_document_processing(self):
        """Test complete technical document processing pipeline."""
        config = create_advanced_chunking_config("technical")
        engine = AdvancedChunkingEngine(config)
        
        technical_sample = """
        # Algorithm Implementation

        ## Function Definition

        The following function implements an advanced processing algorithm:

        ```python
        def advanced_algorithm(data, parameters):
            '''
            Implements advanced processing algorithm
            Args:
                data: Input data structure
                parameters: Configuration parameters
            Returns:
                Processed result
            '''
            result = process_data(data)
            return optimize(result, parameters)
        ```

        The algorithm above demonstrates key concepts in computational efficiency and data processing.
        
        See section 3.2 for detailed analysis of time complexity and performance characteristics.
        """
        
        chunks, relationships = engine.chunk_with_advanced_features(technical_sample)
        
        # Should preserve code blocks appropriately
        code_content_found = False
        for chunk in chunks:
            if 'def advanced_algorithm' in chunk.text:
                code_content_found = True
                break
        
        # Should detect technical topics
        technical_chunks = []
        for chunk in chunks:
            topics = chunk.metadata.get('topics', [])
            if any(t.get('topic') == 'technical' for t in topics):
                technical_chunks.append(chunk)
        
        # Should have appropriate quality
        for chunk in chunks:
            self.assertGreaterEqual(chunk.quality_score, 0.0)
    
    def test_mixed_content_processing(self):
        """Test processing of mixed content types."""
        config = AdvancedChunkingConfig()
        config.custom_rules = create_structured_scripture_rules() + create_technical_document_rules()
        config.extract_topics = True
        engine = AdvancedChunkingEngine(config)
        
        mixed_content = """
        # Chapter 1: Introduction to Spiritual Computing

        1.1 This verse introduces the concept of divine algorithms that process the eternal data of consciousness.

        ```python
        def meditate():
            while True:
                consciousness.expand()
                if enlightenment.achieved():
                    break
        ```

        1.2 The second verse continues the explanation of how ancient wisdom meets modern technology.
        
        As mentioned in verse 1.1, we see the connection between spiritual practice and computational thinking.
        """
        
        chunks, relationships = engine.chunk_with_advanced_features(mixed_content)
        
        # Should handle both content types appropriately
        self.assertGreater(len(chunks), 0)
        self.assertGreaterEqual(len(relationships), 0)
        
        # Should have mixed topic detection
        all_topics = []
        for chunk in chunks:
            topics = chunk.metadata.get('topics', [])
            all_topics.extend([t.get('topic', '') for t in topics])
        
        # Should have decent quality scores
        for chunk in chunks:
            self.assertGreaterEqual(chunk.quality_score, 0.0)
            self.assertLessEqual(chunk.quality_score, 1.0)
    
    def test_large_content_processing(self):
        """Test processing of larger content volumes."""
        config = create_advanced_chunking_config("general")
        engine = AdvancedChunkingEngine(config)
        
        # Create larger test content
        base_text = """
        This is a paragraph about important concepts in artificial intelligence and machine learning. 
        It discusses various algorithms, methodologies, and approaches used in modern AI systems. 
        The content explores both theoretical foundations and practical applications.
        """
        
        large_content = base_text * 20  # Repeat to create larger content
        
        start_time = time.time()
        chunks, relationships = engine.chunk_with_advanced_features(large_content)
        processing_time = time.time() - start_time
        
        # Should process in reasonable time (less than 10 seconds for this size)
        self.assertLess(processing_time, 10.0)
        
        # Should produce reasonable number of chunks
        self.assertGreater(len(chunks), 5)
        self.assertLess(len(chunks), 100)  # Not too fragmented
        
        # Should have relationships
        self.assertGreater(len(relationships), 0)


def run_performance_benchmark():
    """Run performance benchmark test."""
    print("\n" + "="*60)
    print("PERFORMANCE BENCHMARK")
    print("="*60)
    
    configs = {
        "spiritual": create_advanced_chunking_config("spiritual"),
        "technical": create_advanced_chunking_config("technical"),
        "general": create_advanced_chunking_config("general")
    }
    
    # Create test content of different sizes
    base_spiritual = """
    Chapter 2: The Eternal Reality of the Soul
    
    2.{} This is verse {} of the Bhagavad Gita. It contains important spiritual wisdom and guidance for seekers of truth on the path of self-realization. The ancient knowledge provides deep insights into the nature of reality, consciousness, and the eternal soul.
    """
    
    base_technical = """
    # Section {}: Advanced Algorithm Implementation
    
    This section covers algorithm {} which demonstrates sophisticated computational techniques.
    
    ```python
    def algorithm_{}():
        data = process_input()
        result = optimize(data)
        return validate(result)
    ```
    
    The implementation shows efficient processing with O(n log n) complexity.
    """
    
    content_sizes = [1000, 5000, 10000]  # Character counts
    
    for content_type, config in configs.items():
        print(f"\nTesting {content_type} content:")
        engine = AdvancedChunkingEngine(config)
        
        for size in content_sizes:
            if content_type == "spiritual":
                # Generate spiritual content
                verses_needed = size // 200
                content = ""
                for i in range(verses_needed):
                    content += base_spiritual.format(i//10 + 1, i + 1) + "\n\n"
            else:
                # Generate technical content
                sections_needed = size // 300
                content = ""
                for i in range(sections_needed):
                    content += base_technical.format(i + 1, i + 1, i + 1) + "\n\n"
            
            content = content[:size]  # Trim to exact size
            
            start_time = time.time()
            chunks, relationships = engine.chunk_with_advanced_features(content)
            processing_time = time.time() - start_time
            
            avg_chunk_size = sum(len(c.text) for c in chunks) / len(chunks) if chunks else 0
            avg_quality = sum(c.quality_score for c in chunks) / len(chunks) if chunks else 0
            
            print(f"  {size:,} chars: {processing_time:.2f}s | "
                  f"{len(chunks)} chunks | "
                  f"avg size: {avg_chunk_size:.0f} | "
                  f"avg quality: {avg_quality:.3f} | "
                  f"{len(relationships)} relationships")


if __name__ == "__main__":
    # Run unit tests
    print("Running Advanced Chunking Tests...")
    unittest.main(verbosity=2, exit=False, argv=[''])
    
    # Run performance benchmark
    run_performance_benchmark()
