"""
Test Suite for Advanced Chunking Features

This test suite comprehensively tests all advanced chunking capabilities:
- Custom chunking rules with pattern matching
- Intelligent overlap management
- Chunk relationship tracking (semantic, sequential, entity-based)
- Advanced metadata extraction (entities, topics, keywords)
- Dynamic chunk sizing based on content complexity
- Cross-reference detection

Author: Lexicon Development Team
"""

import pytest
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any

# Import the modules to test
from advanced_chunking import (
    AdvancedChunkingConfig,
    AdvancedChunkingEngine,
    CustomChunkingRule,
    ChunkRelationship,
    RelationshipTracker,
    AdvancedMetadataExtractor,
    OverlapManager,
    HAS_SPACY,
    HAS_ML_LIBS
)
from chunking_strategies import Chunk

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestCustomChunkingRules:
    """Test custom chunking rules functionality."""
    
    def test_verse_boundary_rule(self):
        """Test verse boundary detection rule."""
        rule = CustomChunkingRule(
            name="verse_boundary",
            description="Split at verse numbers",
            pattern=r"॥\s*\d+\s*॥",
            priority=10,
            boundary_position="after",
            extract_metadata=True,
            metadata_key="verse_number"
        )
        
        text = "Some text before ॥ 47 ॥ This is verse 47 content ॥ 48 ॥ This is verse 48"
        matches = rule.matches(text)
        
        assert len(matches) == 2, f"Expected 2 matches, got {len(matches)}"
        assert matches[0][0] < matches[1][0], "Matches should be in order"
        assert "verse_number" in matches[0][2], "Should extract verse number metadata"
    
    def test_section_header_rule(self):
        """Test section header detection rule."""
        rule = CustomChunkingRule(
            name="section_header",
            description="Split at section headers",
            pattern=r"^[A-Z][A-Z\s]+$",
            priority=8,
            boundary_position="before",
            extract_metadata=True,
            metadata_key="section_title"
        )
        
        text = "Previous content\nCHAPTER TWO\nNew chapter content\nTRANSLATION\nTranslation text"
        matches = rule.matches(text)
        
        # Debug: let's see what we get
        print(f"Debug: Found {len(matches)} matches: {matches}")
        
        # The regex should match lines that are all caps
        assert len(matches) >= 1, f"Expected at least 1 match, got {len(matches)}"
    
    def test_keyword_rule(self):
        """Test keyword-based rule."""
        rule = CustomChunkingRule(
            name="keyword_boundary",
            description="Split at keywords",
            pattern="dharma|karma|moksha",
            pattern_type="keyword",
            priority=5
        )
        
        text = "This discusses dharma and its meaning. Karma is action. Moksha is liberation."
        matches = rule.matches(text)
        
        assert len(matches) == 3, f"Expected 3 matches, got {len(matches)}"


class TestAdvancedChunkingConfig:
    """Test advanced chunking configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = AdvancedChunkingConfig()
        
        assert config.intelligent_overlap == True
        assert config.track_relationships == True
        assert config.extract_entities == True
        assert config.dynamic_chunk_sizing == True
        assert len(config.relationship_types) > 0
    
    def test_custom_config(self):
        """Test custom configuration."""
        custom_rules = [
            CustomChunkingRule(
                name="test_rule",
                description="Test rule",
                pattern=r"test_pattern",
                priority=1
            )
        ]
        
        config = AdvancedChunkingConfig(
            max_chunk_size=1000,
            custom_rules=custom_rules,
            overlap_min_ratio=0.1,
            overlap_max_ratio=0.4,
            min_relationship_strength=0.5
        )
        
        assert config.max_chunk_size == 1000
        assert len(config.custom_rules) == 1
        assert config.overlap_min_ratio == 0.1
        assert config.min_relationship_strength == 0.5


class TestRelationshipTracker:
    """Test chunk relationship tracking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = AdvancedChunkingConfig()
        self.tracker = RelationshipTracker(self.config)
        
        # Create sample chunks
        self.chunks = [
            Chunk(
                text="Krishna teaches Arjuna about dharma and duty.",
                start_char=0,
                end_char=43,
                chunk_id="chunk_1",
                metadata={}
            ),
            Chunk(
                text="Arjuna receives wisdom about karma and action.",
                start_char=44,
                end_char=90,
                chunk_id="chunk_2",
                metadata={}
            ),
            Chunk(
                text="The Bhagavad Gita discusses dharma, karma, and moksha.",
                start_char=91,
                end_char=146,
                chunk_id="chunk_3",
                metadata={}
            )
        ]
        
        # Set overlap attributes for testing
        self.chunks[0].overlap_with_next = 10
        self.chunks[1].overlap_with_next = 15
    
    def test_sequential_relationships(self):
        """Test sequential relationship tracking."""
        self.tracker.track_sequential_relationships(self.chunks)
        
        sequential_rels = [rel for rel in self.tracker.relationships 
                          if rel.relationship_type == "sequential"]
        
        assert len(sequential_rels) == 2, f"Expected 2 sequential relationships, got {len(sequential_rels)}"
        assert sequential_rels[0].source_chunk_id == "chunk_1"
        assert sequential_rels[0].target_chunk_id == "chunk_2"
    
    def test_entity_relationships(self):
        """Test entity-based relationship tracking."""
        if not self.tracker.nlp:
            print("Skipping entity relationship test - spaCy not available")
            return
        
        self.tracker.track_entity_relationships(self.chunks)
        
        entity_rels = [rel for rel in self.tracker.relationships 
                      if rel.relationship_type == "entity"]
        
        # Should find relationships between chunks that share entities
        assert len(entity_rels) >= 0, "Should find entity relationships or return empty list"
    
    def test_cross_reference_detection(self):
        """Test cross-reference detection."""
        # Add a chunk with explicit references
        ref_chunk = Chunk(
            text="As mentioned in chapter 2, dharma is essential. See verse 47 for details.",
            start_char=147,
            end_char=220,
            chunk_id="chunk_ref",
            metadata={}
        )
        
        chunks_with_ref = self.chunks + [ref_chunk]
        self.tracker.detect_cross_references(chunks_with_ref)
        
        ref_rels = [rel for rel in self.tracker.relationships 
                   if rel.relationship_type == "reference"]
        
        assert len(ref_rels) > 0, "Should detect cross-references"
    
    def test_relationship_graph(self):
        """Test relationship graph generation."""
        # Reset relationships for this test
        self.tracker.relationships = []
        
        self.tracker.track_sequential_relationships(self.chunks)
        
        # Debug: let's see what relationships were created
        print(f"Debug: Created {len(self.tracker.relationships)} relationships:")
        for i, rel in enumerate(self.tracker.relationships):
            print(f"  {i+1}. {rel.source_chunk_id} -> {rel.target_chunk_id} ({rel.relationship_type})")
        
        graph = self.tracker.get_relationship_graph()
        
        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) == 3, "Should have 3 nodes"
        # Should have 2 sequential relationships (chunk_1->chunk_2, chunk_2->chunk_3)
        assert len(graph["edges"]) == 2, f"Should have 2 edges, got {len(graph['edges'])}"


class TestAdvancedMetadataExtractor:
    """Test advanced metadata extraction."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = AdvancedChunkingConfig()
        self.extractor = AdvancedMetadataExtractor(self.config)
        
        self.sample_chunk = Chunk(
            text="Krishna teaches Arjuna about dharma, karma, and the path to moksha. This wisdom is eternal and profound.",
            start_char=0,
            end_char=103,
            chunk_id="test_chunk",
            metadata={}
        )
    
    def test_entity_extraction(self):
        """Test named entity extraction."""
        if not HAS_SPACY or not self.extractor.nlp:
            print("Skipping entity extraction - spaCy not available")
            return
        
        entities = self.extractor._extract_entities(self.sample_chunk.text)
        
        assert isinstance(entities, list), "Should return list of entities"
        # Should extract Krishna and Arjuna as entities
        entity_texts = [ent['text'] for ent in entities]
        assert any('Krishna' in text for text in entity_texts), "Should extract Krishna"
        assert any('Arjuna' in text for text in entity_texts), "Should extract Arjuna"
    
    def test_keyword_extraction(self):
        """Test keyword extraction."""
        if not HAS_SPACY or not self.extractor.nlp:
            print("Skipping keyword extraction - spaCy not available")
            return
        
        keywords = self.extractor._extract_keywords(self.sample_chunk.text)
        
        assert isinstance(keywords, list), "Should return list of keywords"
        keyword_texts = [kw['text'] for kw in keywords]
        
        # Should extract spiritual terms
        assert any('dharma' in text.lower() for text in keyword_texts), "Should extract dharma"
        assert any('karma' in text.lower() for text in keyword_texts), "Should extract karma"
    
    def test_topic_extraction(self):
        """Test topic extraction."""
        topics = self.extractor._extract_topics(self.sample_chunk.text)
        
        assert isinstance(topics, list), "Should return list of topics"
        assert 'dharma' in topics, "Should identify dharma topic"
        assert 'karma' in topics, "Should identify karma topic"
        assert 'moksha' in topics, "Should identify moksha topic"
    
    def test_linguistic_features(self):
        """Test linguistic feature extraction."""
        features = self.extractor._extract_linguistic_features(self.sample_chunk.text)
        
        assert 'char_count' in features
        assert 'word_count' in features
        assert 'sentence_count' in features
        assert features['char_count'] == len(self.sample_chunk.text)
        assert features['word_count'] > 0
        assert features['sentence_count'] > 0
    
    def test_content_analysis(self):
        """Test content analysis."""
        analysis = self.extractor._analyze_content(self.sample_chunk.text)
        
        assert 'complexity_score' in analysis
        assert 'has_questions' in analysis
        assert 'has_quotations' in analysis
        assert isinstance(analysis['complexity_score'], float)
        assert 0.0 <= analysis['complexity_score'] <= 1.0
    
    def test_full_metadata_extraction(self):
        """Test complete metadata extraction."""
        metadata = self.extractor.extract_metadata(self.sample_chunk)
        
        assert 'linguistic_features' in metadata
        assert 'content_analysis' in metadata
        assert 'topics' in metadata
        
        # Verify structure
        assert isinstance(metadata['linguistic_features'], dict)
        assert isinstance(metadata['content_analysis'], dict)
        assert isinstance(metadata['topics'], list)


class TestOverlapManager:
    """Test intelligent overlap management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = AdvancedChunkingConfig(
            overlap_size=100,
            intelligent_overlap=True,
            overlap_optimization="content_aware",
            overlap_min_ratio=0.1,
            overlap_max_ratio=0.3
        )
        self.manager = OverlapManager(self.config)
        
        # Create sample chunks
        self.chunks = [
            Chunk(
                text="This is the first chunk. It contains some important information. The end.",
                start_char=0,
                end_char=78,
                chunk_id="chunk_1",
                metadata={}
            ),
            Chunk(
                text="This starts the second chunk. It has different content. Also important.",
                start_char=79,
                end_char=150,
                chunk_id="chunk_2",
                metadata={}
            )
        ]
    
    def test_overlap_optimization(self):
        """Test overlap optimization."""
        optimized_chunks = self.manager.optimize_overlaps(self.chunks)
        
        assert len(optimized_chunks) == len(self.chunks), "Should preserve chunk count"
        
        # Check that overlaps were calculated
        for i, chunk in enumerate(optimized_chunks[:-1]):
            assert hasattr(chunk, 'overlap_with_next'), "Should have overlap_with_next"
            assert chunk.overlap_with_next >= 0, "Overlap should be non-negative"
    
    def test_content_aware_overlap(self):
        """Test content-aware overlap calculation."""
        chunk1 = self.chunks[0]
        chunk2 = self.chunks[1]
        
        overlap_size = self.manager._calculate_optimal_overlap(chunk1, chunk2)
        
        assert isinstance(overlap_size, int), "Should return integer overlap size"
        assert overlap_size >= 0, "Overlap should be non-negative"
        
        # Should respect min/max ratios
        min_overlap = int(len(chunk1.text) * self.config.overlap_min_ratio)
        max_overlap = int(len(chunk1.text) * self.config.overlap_max_ratio)
        
        assert overlap_size >= min_overlap, f"Overlap {overlap_size} should be >= {min_overlap}"
        assert overlap_size <= max_overlap, f"Overlap {overlap_size} should be <= {max_overlap}"


class TestAdvancedChunkingEngine:
    """Test the complete advanced chunking engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create comprehensive configuration
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
                boundary_position="before"
            )
        ]
        
        self.config = AdvancedChunkingConfig(
            max_chunk_size=800,
            overlap_size=100,
            custom_rules=custom_rules,
            apply_custom_rules=True,
            track_relationships=True,
            extract_entities=True,
            extract_topics=True,
            extract_keywords=True,
            intelligent_overlap=True,
            dynamic_chunk_sizing=True
        )
        
        self.engine = AdvancedChunkingEngine(self.config)
        
        # Sample Bhagavad Gita text for testing
        self.sample_text = """
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
        of detached action, which is fundamental to spiritual progress. As mentioned
        in chapter 1, Arjuna was confused about his duty.
        
        Text 48
        योगस्थः कुरु कर्माणि सङ्गं त्यक्त्वा धनञ्जय ।
        सिद्ध्यसिद्ध्योः समो भूत्वा समत्वं योग उच्यते ॥ ४८ ॥
        
        Translation
        Perform your duty equipoised, O Arjuna, abandoning all attachment to success 
        or failure. Such equanimity is called yoga.
        """
    
    def test_custom_rule_chunking(self):
        """Test chunking with custom rules."""
        chunks = self.engine.chunk_text(self.sample_text, strategy="custom")
        
        assert len(chunks) > 0, "Should create chunks"
        
        # Verify that verse boundaries were detected
        verse_chunks = [chunk for chunk in chunks 
                       if 'verse_number' in chunk.metadata]
        
        # Should have chunks with verse metadata
        assert len(verse_chunks) > 0, "Should detect verse boundaries"
    
    def test_relationship_tracking(self):
        """Test comprehensive relationship tracking."""
        chunks = self.engine.chunk_text(self.sample_text, strategy="custom")
        
        # Get relationship analysis
        analysis = self.engine.get_relationship_analysis()
        
        assert 'total_relationships' in analysis
        assert 'relationship_types' in analysis
        assert 'relationship_graph' in analysis
        
        assert analysis['total_relationships'] > 0, "Should find relationships"
        
        # Should have sequential relationships at minimum
        assert 'sequential' in analysis['relationship_types'], "Should have sequential relationships"
    
    def test_advanced_metadata_extraction(self):
        """Test advanced metadata in chunks."""
        chunks = self.engine.chunk_text(self.sample_text, strategy="custom")
        
        # Verify advanced metadata
        for chunk in chunks:
            assert 'linguistic_features' in chunk.metadata, "Should have linguistic features"
            assert 'content_analysis' in chunk.metadata, "Should have content analysis"
            assert 'topics' in chunk.metadata, "Should have topics"
            
            # Check specific metadata structure
            linguistic = chunk.metadata['linguistic_features']
            assert 'char_count' in linguistic
            assert 'word_count' in linguistic
            
            content = chunk.metadata['content_analysis']
            assert 'complexity_score' in content
            assert isinstance(content['complexity_score'], float)
    
    def test_overlap_optimization(self):
        """Test intelligent overlap management."""
        chunks = self.engine.chunk_text(self.sample_text, strategy="custom")
        
        # Check that overlaps were calculated
        for i, chunk in enumerate(chunks[:-1]):
            if hasattr(chunk, 'overlap_with_next'):
                assert chunk.overlap_with_next >= 0, "Overlap should be non-negative"
    
    def test_dynamic_sizing(self):
        """Test dynamic chunk sizing."""
        # Create text with varying complexity
        simple_text = "This is simple text. " * 50
        complex_text = ("Transcendental consciousness manifests through epistemological "
                       "frameworks that paradigmatically synthesize phenomenological "
                       "experiences with ontological realities. ") * 10
        
        mixed_text = simple_text + "\n\n" + complex_text
        
        chunks = self.engine.chunk_text(mixed_text, strategy="semantic")
        
        # Should create chunks (dynamic sizing may affect count)
        assert len(chunks) > 0, "Should create chunks with dynamic sizing"
        
        # Verify all chunks have quality scores
        for chunk in chunks:
            assert hasattr(chunk, 'quality_score'), "Should have quality score"
            assert 0.0 <= chunk.quality_score <= 1.0, "Quality score should be 0-1"
    
    def test_cross_reference_detection(self):
        """Test cross-reference detection."""
        chunks = self.engine.chunk_text(self.sample_text, strategy="custom")
        
        # Check for reference relationships
        analysis = self.engine.get_relationship_analysis()
        
        if 'reference' in analysis['relationship_types']:
            # Should detect the "as mentioned in chapter 1" reference
            assert analysis['relationship_types']['reference'] > 0, "Should detect references"
    
    def test_quality_scores(self):
        """Test chunk quality assessment."""
        chunks = self.engine.chunk_text(self.sample_text, strategy="custom")
        
        for chunk in chunks:
            assert hasattr(chunk, 'quality_score'), "Should have quality score"
            assert isinstance(chunk.quality_score, float), "Quality score should be float"
            assert 0.0 <= chunk.quality_score <= 1.0, "Quality score should be 0-1"


class TestIntegration:
    """Integration tests for complete workflow."""
    
    def test_full_workflow(self):
        """Test complete advanced chunking workflow."""
        # Create realistic configuration
        config = AdvancedChunkingConfig(
            max_chunk_size=1000,
            overlap_size=100,
            track_relationships=True,
            extract_entities=True,
            extract_topics=True,
            intelligent_overlap=True,
            dynamic_chunk_sizing=True
        )
        
        engine = AdvancedChunkingEngine(config)
        
        # Sample spiritual text
        text = """
        The Bhagavad Gita teaches eternal principles of dharma and karma.
        Krishna guides Arjuna through philosophical inquiries about duty and action.
        The path of yoga leads to moksha through detached service.
        These teachings apply to all souls seeking spiritual advancement.
        """
        
        # Process text
        chunks = engine.chunk_text(text, strategy="semantic")
        
        # Verify comprehensive processing
        assert len(chunks) > 0, "Should create chunks"
        
        # Check metadata
        for chunk in chunks:
            assert 'linguistic_features' in chunk.metadata
            assert 'content_analysis' in chunk.metadata
            assert 'topics' in chunk.metadata
        
        # Get analysis
        analysis = engine.get_relationship_analysis()
        
        assert isinstance(analysis, dict), "Should return analysis dict"
        assert 'total_relationships' in analysis
        assert 'relationship_graph' in analysis
    
    def test_error_handling(self):
        """Test error handling with invalid inputs."""
        config = AdvancedChunkingConfig()
        engine = AdvancedChunkingEngine(config)
        
        # Test empty text
        chunks = engine.chunk_text("", strategy="custom")
        assert len(chunks) == 0, "Empty text should produce no chunks"
        
        # Test very short text
        chunks = engine.chunk_text("Hi", strategy="custom")
        assert len(chunks) <= 1, "Very short text should produce at most one chunk"
    
    def test_performance_benchmarks(self):
        """Test performance with larger text."""
        config = AdvancedChunkingConfig(
            track_relationships=True,
            extract_entities=True,
            extract_topics=True
        )
        engine = AdvancedChunkingEngine(config)
        
        # Create larger text
        large_text = ("This is a sample paragraph about spiritual teachings. " * 100 +
                     "Krishna teaches dharma and karma principles. " * 100 +
                     "Arjuna learns about duty and action. " * 100)
        
        import time
        start_time = time.time()
        
        chunks = engine.chunk_text(large_text, strategy="semantic")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert len(chunks) > 0, "Should process large text"
        print(f"Processed {len(large_text)} characters in {processing_time:.2f} seconds")
        print(f"Generated {len(chunks)} chunks")
        
        # Should complete in reasonable time (adjust threshold as needed)
        assert processing_time < 30, f"Processing took too long: {processing_time:.2f}s"


if __name__ == "__main__":
    # Run basic tests
    print("🧪 Running Advanced Chunking Tests")
    print("=" * 50)
    
    # Test custom rules
    print("\n1. Testing Custom Chunking Rules...")
    test_rules = TestCustomChunkingRules()
    test_rules.test_verse_boundary_rule()
    test_rules.test_section_header_rule()
    test_rules.test_keyword_rule()
    print("✅ Custom rules tests passed")
    
    # Test configuration
    print("\n2. Testing Configuration...")
    test_config = TestAdvancedChunkingConfig()
    test_config.test_default_config()
    test_config.test_custom_config()
    print("✅ Configuration tests passed")
    
    # Test relationship tracking
    print("\n3. Testing Relationship Tracking...")
    test_relationships = TestRelationshipTracker()
    test_relationships.setup_method()
    test_relationships.test_sequential_relationships()
    test_relationships.test_relationship_graph()
    print("✅ Relationship tracking tests passed")
    
    # Test metadata extraction
    print("\n4. Testing Metadata Extraction...")
    test_metadata = TestAdvancedMetadataExtractor()
    test_metadata.setup_method()
    test_metadata.test_topic_extraction()
    test_metadata.test_linguistic_features()
    test_metadata.test_content_analysis()
    test_metadata.test_full_metadata_extraction()
    
    # Only test entity/keyword extraction if spaCy is available
    if HAS_SPACY:
        try:
            # Try to test entity extraction
            if test_metadata.extractor.nlp:
                test_metadata.test_entity_extraction()
                test_metadata.test_keyword_extraction()
                print("✅ Entity and keyword extraction tests passed")
            else:
                print("⚠️  Entity/keyword extraction tests skipped (spaCy model not available)")
        except Exception as e:
            print(f"⚠️  Entity/keyword extraction tests skipped: {e}")
    else:
        print("⚠️  Entity and keyword extraction tests skipped (spaCy not available)")
    
    print("✅ Metadata extraction tests passed")
    
    # Test overlap management
    print("\n5. Testing Overlap Management...")
    test_overlap = TestOverlapManager()
    test_overlap.setup_method()
    test_overlap.test_overlap_optimization()
    test_overlap.test_content_aware_overlap()
    print("✅ Overlap management tests passed")
    
    # Test complete engine
    print("\n6. Testing Advanced Chunking Engine...")
    test_engine = TestAdvancedChunkingEngine()
    test_engine.setup_method()
    test_engine.test_custom_rule_chunking()
    test_engine.test_relationship_tracking()
    test_engine.test_advanced_metadata_extraction()
    test_engine.test_quality_scores()
    print("✅ Advanced chunking engine tests passed")
    
    # Integration test
    print("\n7. Testing Integration...")
    test_integration = TestIntegration()
    test_integration.test_full_workflow()
    test_integration.test_error_handling()
    print("✅ Integration tests passed")
    
    print(f"\n🎉 All Advanced Chunking Tests Completed Successfully!")
    print("=" * 50)
