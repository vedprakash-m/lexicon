#!/usr/bin/env python3

"""
Test script for Chunking Strategies

This script tests all chunking strategies including:
- Fixed-size chunking with boundary detection
- Semantic chunking (when available)
- Hierarchical chunking with structure preservation
- Universal content chunking with intelligent domain recognition
- Chunk quality assessment and post-processing

Author: Lexicon Development Team
"""

import sys
sys.path.append('.')

from processors.chunking_strategies import *


def test_chunk_creation():
    """Test basic chunk creation and properties."""
    print("\nTesting chunk creation...")
    
    try:
        # Test basic chunk creation
        chunk = Chunk(
            text="This is a test chunk with some content.",
            start_char=0,
            end_char=40
        )
        
        # Test computed properties
        if (chunk.length == 40 and 
            chunk.word_count == 8 and
            chunk.chunk_id.startswith("chunk_")):
            print("✓ Basic chunk creation successful")
        else:
            print("✗ Basic chunk properties failed")
            return False
        
        # Test chunk serialization
        chunk_dict = chunk.to_dict()
        required_fields = ['text', 'start_char', 'end_char', 'chunk_id', 'length', 'word_count']
        
        if all(field in chunk_dict for field in required_fields):
            print("✓ Chunk serialization successful")
        else:
            print("✗ Chunk serialization failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Chunk creation failed: {e}")
        return False


def test_chunking_config():
    """Test chunking configuration."""
    print("\nTesting chunking configuration...")
    
    try:
        # Test default config
        config = ChunkingConfig()
        
        if (config.max_chunk_size == 1000 and
            config.min_chunk_size == 100 and
            config.respect_sentence_boundaries):
            print("✓ Default configuration successful")
        else:
            print("✗ Default configuration failed")
            return False
        
        # Test custom config
        custom_config = ChunkingConfig(
            max_chunk_size=500,
            overlap_size=50,
            use_semantic_similarity=True
        )
        
        if (custom_config.max_chunk_size == 500 and
            custom_config.overlap_size == 50 and
            custom_config.use_semantic_similarity):
            print("✓ Custom configuration successful")
        else:
            print("✗ Custom configuration failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_fixed_size_chunking():
    """Test fixed-size chunking strategy."""
    print("\nTesting fixed-size chunking...")
    
    try:
        config = ChunkingConfig(max_chunk_size=200, min_chunk_size=50, overlap_size=20)
        chunker = FixedSizeChunker(config)
        
        # Test text
        test_text = """
        This is the first paragraph of our test document. It contains several sentences
        that should be split appropriately. The chunker should respect sentence boundaries
        when possible.
        
        This is the second paragraph. It provides additional content for testing the
        chunking algorithm. The text should be divided into reasonable chunks.
        
        Finally, this is the third paragraph. It concludes our test document and
        provides enough content to test multiple chunks.
        """
        
        chunks = chunker.chunk_text(test_text.strip())
        
        # Validate results
        if not chunks:
            print("✗ No chunks generated")
            return False
        
        # Check chunk sizes
        valid_sizes = all(
            config.min_chunk_size <= chunk.length <= config.max_chunk_size 
            for chunk in chunks
        )
        
        if not valid_sizes:
            print("✗ Chunk sizes out of bounds")
            return False
        
        # Check for content coverage
        total_content = ''.join(chunk.text for chunk in chunks)
        if len(total_content) < len(test_text.strip()) * 0.8:  # Allow for some loss due to processing
            print("✗ Significant content loss during chunking")
            return False
        
        print(f"✓ Fixed-size chunking successful")
        print(f"  Generated {len(chunks)} chunks")
        print(f"  Average length: {sum(c.length for c in chunks) / len(chunks):.1f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Fixed-size chunking failed: {e}")
        return False


def test_hierarchical_chunking():
    """Test hierarchical chunking strategy."""
    print("\nTesting hierarchical chunking...")
    
    try:
        config = ChunkingConfig(max_chunk_size=300)
        chunker = HierarchicalChunker(config)
        
        # Test text with headers
        test_text = """
        # Introduction
        
        This is the introduction section of our document. It provides an overview
        of the topics that will be covered in the subsequent sections.
        
        ## Background
        
        This subsection provides background information that is necessary to
        understand the main content.
        
        # Main Content
        
        This is the main content section. It contains the primary information
        that the document is meant to convey to readers.
        
        ## Details
        
        This subsection provides detailed information about specific aspects
        of the main topic.
        """
        
        chunks = chunker.chunk_text(test_text.strip())
        
        if not chunks:
            print("✗ No chunks generated")
            return False
        
        # Check that section titles are preserved
        has_section_titles = any(chunk.section_title for chunk in chunks)
        if not has_section_titles:
            print("✗ Section titles not preserved")
            return False
        
        # Check chunk types
        hierarchical_chunks = [c for c in chunks if 'hierarchical' in c.chunk_type]
        if not hierarchical_chunks:
            print("✗ No hierarchical chunks found")
            return False
        
        print(f"✓ Hierarchical chunking successful")
        print(f"  Generated {len(chunks)} chunks")
        print(f"  Section titles preserved: {len([c for c in chunks if c.section_title])}")
        
        return True
        
    except Exception as e:
        print(f"✗ Hierarchical chunking failed: {e}")
        return False


def test_universal_content_chunking():
    """Test universal content chunking strategy."""
    print("\nTesting universal content chunking...")
    
    try:
        config = ChunkingConfig(max_chunk_size=800, respect_section_boundaries=True)
        chunker = UniversalContentChunker(config)
        
        # Test technical documentation with structured content
        technical_text = """
        # API Reference Documentation
        
        ## Authentication
        
        All API requests require authentication using Bearer tokens.
        
        ### Headers
        
        Authorization: Bearer <your_api_key>
        Content-Type: application/json
        
        ## Endpoints
        
        ### GET /api/v1/users
        
        Description: Retrieve a list of users
        
        Parameters:
        - limit (integer): Maximum number of users to return (default: 10)
        - offset (integer): Number of users to skip (default: 0)
        
        Response:
        {
          "users": [
            {
              "id": 1,
              "name": "John Doe",
              "email": "john@example.com"
            }
          ],
          "total": 1
        }
        
        ### POST /api/v1/users
        
        Description: Create a new user
        
        Request Body:
        {
          "name": "Jane Doe",
          "email": "jane@example.com"
        }
        
        Response:
        {
          "id": 2,
          "name": "Jane Doe",
          "email": "jane@example.com",
          "created_at": "2025-07-12T10:00:00Z"
        }
        """
        
        chunks = chunker.chunk_text(technical_text.strip())
        
        if not chunks:
            print("✗ No chunks generated")
            return False
        
        # Check for structured content chunks
        api_chunks = [c for c in chunks if 'api' in c.text.lower()]
        if not api_chunks:
            print("✗ No API documentation chunks found")
            return False
        
        # Check that structured content is preserved
        has_headers = any('#' in chunk.text for chunk in chunks)
        if not has_headers:
            print("✗ Header structure not preserved")
            return False
        
        # Check API documentation content
        has_endpoints = any('GET' in chunk.text or 'POST' in chunk.text for chunk in chunks)
        if not has_endpoints:
            print("✗ API endpoint information not preserved")
            return False
        
        print(f"✓ Universal content chunking successful")
        print(f"  Generated {len(chunks)} chunks")
        print(f"  API chunks: {len(api_chunks)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Universal content chunking failed: {e}")
        return False


def test_semantic_chunking():
    """Test semantic chunking strategy (if available)."""
    print("\nTesting semantic chunking...")
    
    try:
        config = ChunkingConfig(max_chunk_size=300, use_semantic_similarity=True)
        chunker = SemanticChunker(config)
        
        # Test text with different topics
        test_text = """
        Machine learning is a subset of artificial intelligence. It involves algorithms
        that can learn from data without being explicitly programmed.
        
        Neural networks are a key component of deep learning. They are inspired by
        the structure of the human brain and consist of interconnected nodes.
        
        Cooking is an essential life skill. It involves preparing food by combining
        ingredients and applying heat through various methods.
        
        Baking requires precise measurements and timing. It is a specific type of
        cooking that uses dry heat in an oven to prepare foods like bread and cakes.
        """
        
        chunks = chunker.chunk_text(test_text.strip())
        
        if not chunks:
            print("✗ No chunks generated")
            return False
        
        # Check that chunks were created
        if len(chunks) < 2:
            print("✗ Expected multiple chunks for diverse content")
            return False
        
        # If semantic model is available, expect better grouping
        if chunker.model:
            print(f"✓ Semantic chunking with model successful")
            print(f"  Generated {len(chunks)} semantic chunks")
        else:
            print(f"✓ Semantic chunking fallback successful")
            print(f"  Generated {len(chunks)} sentence-based chunks")
        
        return True
        
    except Exception as e:
        print(f"✗ Semantic chunking failed: {e}")
        return False


def test_chunking_engine():
    """Test the main chunking engine."""
    print("\nTesting chunking engine...")
    
    try:
        config = ChunkingConfig(max_chunk_size=400, min_chunk_size=50)
        engine = ChunkingEngine(config)
        
        test_text = """
        This is a comprehensive test of the chunking engine. The engine should be able
        to handle different types of content and apply various chunking strategies
        based on the specified parameters.
        
        The text includes multiple paragraphs to test boundary detection and should
        result in well-formed chunks that respect the configuration settings.
        """
        
        # Test different strategies
        strategies = ['fixed_size', 'hierarchical']
        
        for strategy in strategies:
            chunks = engine.chunk_text(test_text, strategy)
            
            if not chunks:
                print(f"✗ No chunks generated for {strategy}")
                return False
            
            # Check chunk quality
            avg_quality = sum(chunk.quality_score for chunk in chunks) / len(chunks)
            if avg_quality < 0.3:
                print(f"✗ Low average quality for {strategy}: {avg_quality}")
                return False
        
        # Test statistics
        chunks = engine.chunk_text(test_text, 'fixed_size')
        stats = engine.get_chunking_stats(chunks)
        
        required_stats = ['total_chunks', 'avg_chunk_length', 'avg_quality_score']
        if not all(stat in stats for stat in required_stats):
            print("✗ Missing required statistics")
            return False
        
        print(f"✓ Chunking engine successful")
        print(f"  Tested {len(strategies)} strategies")
        print(f"  Average quality: {stats['avg_quality_score']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Chunking engine failed: {e}")
        return False


def test_quality_scoring():
    """Test chunk quality scoring."""
    print("\nTesting quality scoring...")
    
    try:
        config = ChunkingConfig()
        chunker = FixedSizeChunker(config)
        
        # Test different quality texts
        test_cases = [
            ("High quality text with complete sentences. This text has good structure and appropriate length.", "high"),
            ("txt w/ lots of issues!!! &&& bad formatting", "low"),
            ("", "empty"),
            ("Short.", "short"),
            ("Very long text that goes on and on without proper structure or meaningful content just to test the length scoring mechanism and see how it handles extremely verbose content that might not be very useful for chunking purposes.", "verbose")
        ]
        
        for text, expected_quality in test_cases:
            if not text:  # Skip empty text
                continue
                
            chunk = Chunk(text=text, start_char=0, end_char=len(text))
            score = chunker._calculate_quality_score(chunk)
            
            if expected_quality == "high" and score < 0.6:
                print(f"✗ High quality text scored too low: {score}")
                return False
            elif expected_quality == "low" and score > 0.4:
                print(f"✗ Low quality text scored too high: {score}")
                return False
        
        print("✓ Quality scoring working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Quality scoring failed: {e}")
        return False


def test_boundary_detection():
    """Test boundary detection functionality."""
    print("\nTesting boundary detection...")
    
    try:
        config = ChunkingConfig()
        chunker = FixedSizeChunker(config)
        
        test_text = """First sentence. Second sentence! Third sentence?
        
        New paragraph starts here. Another sentence in this paragraph.
        
        Final paragraph. Last sentence."""
        
        # Test sentence boundaries
        sentence_boundaries = chunker._find_sentence_boundaries(test_text)
        if len(sentence_boundaries) < 5:  # Should find several sentence boundaries
            print("✗ Insufficient sentence boundaries detected")
            return False
        
        # Test paragraph boundaries  
        paragraph_boundaries = chunker._find_paragraph_boundaries(test_text)
        if len(paragraph_boundaries) < 3:  # Should find paragraph breaks
            print("✗ Insufficient paragraph boundaries detected")
            return False
        
        print("✓ Boundary detection working correctly")
        print(f"  Sentence boundaries: {len(sentence_boundaries)}")
        print(f"  Paragraph boundaries: {len(paragraph_boundaries)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Boundary detection failed: {e}")
        return False


def run_all_tests():
    """Run all chunking strategy tests."""
    print("🧪 Testing Lexicon Chunking Strategies")
    print("=" * 60)
    
    tests = [
        ("Chunk Creation", test_chunk_creation),
        ("Chunking Configuration", test_chunking_config),
        ("Fixed-Size Chunking", test_fixed_size_chunking),
        ("Hierarchical Chunking", test_hierarchical_chunking),
        ("Universal Content Chunking", test_universal_content_chunking),
        ("Semantic Chunking", test_semantic_chunking),
        ("Chunking Engine", test_chunking_engine),
        ("Quality Scoring", test_quality_scoring),
        ("Boundary Detection", test_boundary_detection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Chunking strategies are working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
