#!/usr/bin/env python3
"""
Demo script to test metadata enrichment functionality with real APIs.
"""

import asyncio
import json
from datetime import datetime
from enum import Enum

from metadata_enrichment import (
    BookIdentifier, MetadataEnrichmentEngine, enrich_book_metadata,
    MetadataSource, EnrichmentStatus
)

# Sample books to test with
SAMPLE_BOOKS = [
    {
        "title": "Bhagavad Gita As It Is",
        "author": "A.C. Bhaktivedanta Swami Prabhupada",
        "isbn": "9780892131945"
    },
    {
        "title": "The Art of War",
        "author": "Sun Tzu",
        "isbn": "9780486425559"
    },
    {
        "title": "Thinking, Fast and Slow",
        "author": "Daniel Kahneman",
        "isbn": "9780374533557"
    },
    {
        "title": "The Upanishads",
        "author": "Patrick Olivelle",
        "isbn": "9780192540782"
    },
    {
        "title": "Non-Existent Book That Should Fail",
        "author": "Unknown Author",
        "isbn": None
    }
]

async def test_single_book_enrichment():
    """Test enriching a single book."""
    print("📚 Testing single book enrichment...")
    
    book = SAMPLE_BOOKS[0]  # Bhagavad Gita
    print(f"   Book: {book['title']} by {book['author']}")
    
    try:
        metadata = await enrich_book_metadata(
            title=book['title'],
            author=book['author'],
            isbn=book['isbn']
        )
        
        print(f"   ✓ Title: {metadata.title}")
        print(f"   ✓ Subtitle: {metadata.subtitle}")
        print(f"   ✓ Authors: {[author.name for author in metadata.authors]}")
        print(f"   ✓ Publisher: {metadata.publisher.name if metadata.publisher else 'N/A'}")
        print(f"   ✓ Published: {metadata.published_date}")
        print(f"   ✓ Pages: {metadata.page_count}")
        print(f"   ✓ Categories: {metadata.categories[:3] if metadata.categories else []}")
        print(f"   ✓ Description: {metadata.description[:100] if metadata.description else 'N/A'}...")
        print(f"   ✓ Quality Score: {metadata.enrichment_quality_score:.2f}")
        print(f"   ✓ Sources: {[source.value for source in metadata.enrichment_sources]}")
        print(f"   ✓ Status: {metadata.enrichment_status.value}")
        
        if metadata.cover_image_url:
            print(f"   ✓ Cover Image: Available")
        
        return metadata
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None

async def test_batch_enrichment():
    """Test batch enrichment of multiple books."""
    print("\n📚 Testing batch enrichment...")
    
    identifiers = []
    for book in SAMPLE_BOOKS:
        identifier = BookIdentifier(
            title=book['title'],
            author=book['author'],
            isbn_13=book['isbn'] if book['isbn'] and len(book['isbn']) == 13 else None,
            isbn_10=book['isbn'] if book['isbn'] and len(book['isbn']) == 10 else None
        )
        identifiers.append(identifier)
    
    engine = MetadataEnrichmentEngine()
    
    try:
        results = await engine.batch_enrich(identifiers, batch_size=2)
        
        print(f"   ✓ Processed {len(results)} books")
        
        for i, (book, metadata) in enumerate(zip(SAMPLE_BOOKS, results)):
            print(f"\n   Book {i+1}: {book['title']}")
            print(f"   Status: {metadata.enrichment_status.value}")
            print(f"   Quality: {metadata.enrichment_quality_score:.2f}")
            print(f"   Sources: {[s.value for s in metadata.enrichment_sources]}")
            
            if metadata.enrichment_status == EnrichmentStatus.COMPLETED:
                print(f"   Publisher: {metadata.publisher.name if metadata.publisher else 'N/A'}")
                print(f"   Pages: {metadata.page_count or 'N/A'}")
            elif metadata.enrichment_status == EnrichmentStatus.FAILED:
                print(f"   Note: This was expected for the non-existent book")
        
        return results
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return []

async def test_source_specific_enrichment():
    """Test enrichment from specific sources."""
    print("\n📚 Testing source-specific enrichment...")
    
    book = SAMPLE_BOOKS[1]  # The Art of War
    identifier = BookIdentifier(
        title=book['title'],
        author=book['author'],
        isbn_13=book['isbn']
    )
    
    engine = MetadataEnrichmentEngine()
    
    # Test Google Books only
    print("   Testing Google Books API...")
    try:
        google_metadata = await engine.enrich_book(identifier, sources=[MetadataSource.GOOGLE_BOOKS])
        print(f"   ✓ Google Books: {google_metadata.enrichment_quality_score:.2f} quality")
        print(f"     Title: {google_metadata.title}")
        print(f"     Publisher: {google_metadata.publisher.name if google_metadata.publisher else 'N/A'}")
    except Exception as e:
        print(f"   ❌ Google Books error: {str(e)}")
    
    # Test OpenLibrary only
    print("   Testing OpenLibrary API...")
    try:
        ol_metadata = await engine.enrich_book(identifier, sources=[MetadataSource.OPENLIBRARY])
        print(f"   ✓ OpenLibrary: {ol_metadata.enrichment_quality_score:.2f} quality")
        print(f"     Title: {ol_metadata.title}")
        print(f"     Publisher: {ol_metadata.publisher.name if ol_metadata.publisher else 'N/A'}")
    except Exception as e:
        print(f"   ❌ OpenLibrary error: {str(e)}")
    
    # Test both sources combined
    print("   Testing combined sources...")
    try:
        combined_metadata = await engine.enrich_book(identifier)
        print(f"   ✓ Combined: {combined_metadata.enrichment_quality_score:.2f} quality")
        print(f"     Sources: {[s.value for s in combined_metadata.enrichment_sources]}")
        print(f"     Authors: {len(combined_metadata.authors)} found")
    except Exception as e:
        print(f"   ❌ Combined error: {str(e)}")

async def test_caching_functionality():
    """Test caching functionality."""
    print("\n📚 Testing caching functionality...")
    
    book = SAMPLE_BOOKS[0]  # Bhagavad Gita
    identifier = BookIdentifier(
        title=book['title'],
        author=book['author'],
        isbn_13=book['isbn']
    )
    
    engine = MetadataEnrichmentEngine()
    
    # First enrichment (should hit APIs)
    print("   First enrichment (hitting APIs)...")
    start_time = asyncio.get_event_loop().time()
    metadata1 = await engine.enrich_book(identifier)
    first_time = asyncio.get_event_loop().time() - start_time
    print(f"   ✓ First call took {first_time:.2f} seconds")
    
    # Second enrichment (should use cache)
    print("   Second enrichment (using cache)...")
    start_time = asyncio.get_event_loop().time()
    metadata2 = await engine.enrich_book(identifier)
    second_time = asyncio.get_event_loop().time() - start_time
    print(f"   ✓ Second call took {second_time:.2f} seconds")
    
    # Verify results are the same
    assert metadata1.title == metadata2.title
    print(f"   ✓ Results are consistent")
    print(f"   ✓ Cache speedup: {first_time/second_time:.1f}x faster")
    
    # Check cache stats
    stats = engine.get_cache_stats()
    print(f"   ✓ Cache stats: {stats['valid_entries']} valid, {stats['total_entries']} total")

def export_results_to_json(results, filename):
    """Export enrichment results to JSON for inspection."""
    print(f"\n💾 Exporting results to {filename}...")
    
    def serialize_value(value):
        """Recursively serialize values for JSON."""
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, Enum):
            return value.value
        elif hasattr(value, '__dict__'):
            # Handle dataclass objects
            return {k: serialize_value(v) for k, v in value.__dict__.items()}
        elif isinstance(value, list):
            return [serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: serialize_value(v) for k, v in value.items()}
        elif hasattr(value, '__class__') and hasattr(value.__class__, '__name__'):
            # Handle enum types and other special objects
            if hasattr(value, 'value'):
                return value.value
            elif hasattr(value, '__dict__'):
                return {k: serialize_value(v) for k, v in value.__dict__.items()}
        return value
    
    serializable_results = []
    for metadata in results:
        # Convert to dict and handle all serialization
        data = {}
        for field_name, field in metadata.__dataclass_fields__.items():
            value = getattr(metadata, field_name)
            data[field_name] = serialize_value(value)
        
        serializable_results.append(data)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Exported {len(serializable_results)} enriched metadata records")

async def main():
    """Run all metadata enrichment demos."""
    print("🚀 Testing Lexicon Metadata Enrichment System")
    print("=" * 60)
    
    try:
        # Test single book enrichment
        single_result = await test_single_book_enrichment()
        
        # Test batch enrichment
        batch_results = await test_batch_enrichment()
        
        # Test source-specific enrichment
        await test_source_specific_enrichment()
        
        # Test caching
        await test_caching_functionality()
        
        # Export results for inspection
        if batch_results:
            export_results_to_json(batch_results, 'enrichment_demo_results.json')
        
        print("\n" + "=" * 60)
        print("✅ All metadata enrichment tests completed successfully!")
        print("\nNote: This demo uses free APIs without authentication.")
        print("For production use, consider getting API keys for better rate limits:")
        print("- Google Books API: https://developers.google.com/books/docs/v1/using")
        print("- OpenLibrary is free and open, no key required")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
