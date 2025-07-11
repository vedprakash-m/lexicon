#!/usr/bin/env python3
"""
Demo script for Book Relationship Mapper

This script demonstrates the capabilities of the book relationship mapping system,
including finding various types of relationships, generating recommendations,
and creating thematic clusters.
"""

import asyncio
import json
import tempfile
from pathlib import Path

from book_relationship_mapper import (
    BookMetadata, BookRelationshipMapper, RelationshipType,
    create_book_metadata_from_dict
)


# Sample book library with diverse content
SAMPLE_BOOKS = [
    {
        "id": "bhagavad_gita_en",
        "title": "Bhagavad Gita As It Is",
        "authors": ["A.C. Bhaktivedanta Swami Prabhupada"],
        "publication_year": 1972,
        "language": "English",
        "categories": ["Philosophy", "Religion", "Spirituality"],
        "subjects": ["Hindu Philosophy", "Yoga", "Meditation", "Bhakti"],
        "description": "The Bhagavad Gita is one of the most important philosophical texts in the world",
        "keywords": ["Krishna", "Arjuna", "dharma", "karma", "yoga", "spirituality"]
    },
    {
        "id": "bhagavad_gita_es",
        "title": "Bhagavad Gita Tal Como Es",
        "authors": ["A.C. Bhaktivedanta Swami Prabhupada"],
        "publication_year": 1975,
        "language": "Spanish",
        "original_title": "Bhagavad Gita As It Is",
        "original_language": "English",
        "translator": "Spanish Translation Team",
        "categories": ["Philosophy", "Religion", "Spirituality"],
        "subjects": ["Hindu Philosophy", "Yoga", "Meditation", "Bhakti"],
        "description": "Spanish translation of the Bhagavad Gita",
        "keywords": ["Krishna", "Arjuna", "dharma", "karma", "yoga", "espiritualidad"]
    },
    {
        "id": "bhagavad_gita_revised",
        "title": "Bhagavad Gita As It Is (Revised Edition)",
        "authors": ["A.C. Bhaktivedanta Swami Prabhupada"],
        "publication_year": 1983,
        "language": "English",
        "edition": "Revised",
        "categories": ["Philosophy", "Religion", "Spirituality"],
        "subjects": ["Hindu Philosophy", "Yoga", "Meditation", "Bhakti"],
        "description": "Revised edition with updated commentary",
        "keywords": ["Krishna", "Arjuna", "dharma", "karma", "yoga", "spirituality"]
    },
    {
        "id": "srimad_bhagavatam_1",
        "title": "Srimad Bhagavatam Canto 1",
        "authors": ["A.C. Bhaktivedanta Swami Prabhupada"],
        "series": "Srimad Bhagavatam",
        "series_number": 1,
        "publication_year": 1974,
        "language": "English",
        "categories": ["Philosophy", "Religion", "Spirituality", "Literature"],
        "subjects": ["Hindu Philosophy", "Stories", "Devotion", "Bhakti"],
        "description": "First canto of the great Vedic literature",
        "keywords": ["Krishna", "Vishnu", "devotion", "stories", "Vedic"]
    },
    {
        "id": "srimad_bhagavatam_2",
        "title": "Srimad Bhagavatam Canto 2",
        "authors": ["A.C. Bhaktivedanta Swami Prabhupada"],
        "series": "Srimad Bhagavatam",
        "series_number": 2,
        "publication_year": 1975,
        "language": "English",
        "categories": ["Philosophy", "Religion", "Spirituality", "Literature"],
        "subjects": ["Hindu Philosophy", "Stories", "Devotion", "Bhakti"],
        "description": "Second canto describing the cosmic creation",
        "keywords": ["Krishna", "Vishnu", "creation", "cosmos", "Vedic"]
    },
    {
        "id": "srimad_bhagavatam_3",
        "title": "Srimad Bhagavatam Canto 3",
        "authors": ["A.C. Bhaktivedanta Swami Prabhupada"],
        "series": "Srimad Bhagavatam",
        "series_number": 3,
        "publication_year": 1976,
        "language": "English",
        "categories": ["Philosophy", "Religion", "Spirituality", "Literature"],
        "subjects": ["Hindu Philosophy", "Stories", "Devotion", "Bhakti"],
        "description": "Third canto about the status quo",
        "keywords": ["Krishna", "Vishnu", "material", "spiritual", "Vedic"]
    },
    {
        "id": "art_of_war",
        "title": "The Art of War",
        "authors": ["Sun Tzu"],
        "publication_year": 500,  # BCE approximation
        "language": "English",
        "categories": ["Strategy", "Military", "Philosophy"],
        "subjects": ["War", "Strategy", "Leadership", "Tactics"],
        "description": "Ancient Chinese military strategy and philosophy",
        "keywords": ["strategy", "war", "leadership", "tactics", "military"]
    },
    {
        "id": "tao_te_ching",
        "title": "Tao Te Ching",
        "authors": ["Lao Tzu"],
        "publication_year": 400,  # BCE approximation
        "language": "English",
        "categories": ["Philosophy", "Religion", "Spirituality"],
        "subjects": ["Taoism", "Eastern Philosophy", "Wisdom"],
        "description": "Fundamental text for both philosophical and religious Taoism",
        "keywords": ["tao", "wisdom", "balance", "nature", "philosophy"]
    },
    {
        "id": "thinking_fast_slow",
        "title": "Thinking, Fast and Slow",
        "authors": ["Daniel Kahneman"],
        "publication_year": 2011,
        "language": "English",
        "categories": ["Psychology", "Science", "Behavioral Economics"],
        "subjects": ["Cognitive Psychology", "Decision Making", "Behavioral Science"],
        "description": "Revolutionary book about how the mind makes decisions",
        "keywords": ["psychology", "decision making", "cognitive bias", "thinking"]
    },
    {
        "id": "mindfulness_plain_english",
        "title": "Mindfulness in Plain English",
        "authors": ["Bhante Henepola Gunaratana"],
        "publication_year": 1991,
        "language": "English",
        "categories": ["Religion", "Spirituality", "Self-Help"],
        "subjects": ["Buddhism", "Meditation", "Mindfulness"],
        "description": "Clear and practical guide to mindfulness meditation",
        "keywords": ["mindfulness", "meditation", "Buddhism", "awareness", "practice"]
    },
    {
        "id": "power_of_now",
        "title": "The Power of Now",
        "authors": ["Eckhart Tolle"],
        "publication_year": 1997,
        "language": "English",
        "categories": ["Spirituality", "Self-Help", "Philosophy"],
        "subjects": ["Spiritual Awakening", "Present Moment", "Consciousness"],
        "description": "A guide to spiritual enlightenment through presence",
        "keywords": ["presence", "consciousness", "awakening", "spirituality", "now"]
    },
    {
        "id": "meditations",
        "title": "Meditations",
        "authors": ["Marcus Aurelius"],
        "publication_year": 180,  # CE approximation
        "language": "English",
        "categories": ["Philosophy", "Classical Literature"],
        "subjects": ["Stoicism", "Ethics", "Personal Development"],
        "description": "Personal writings of the Roman Emperor on Stoic philosophy",
        "keywords": ["stoicism", "virtue", "wisdom", "discipline", "philosophy"]
    }
]


def test_relationship_discovery(mapper: BookRelationshipMapper):
    """Test discovery of various relationship types."""
    print("📚 Testing relationship discovery...")
    
    print("   Finding same-author relationships...")
    author_relationships = mapper.find_same_author_relationships()
    print(f"   ✓ Found {len(author_relationships)} same-author relationships")
    
    for rel in author_relationships[:3]:  # Show first 3
        source_title = mapper.books[rel.source_book_id].title
        target_title = mapper.books[rel.target_book_id].title
        print(f"     • {source_title} ↔ {target_title}")
        print(f"       Evidence: {rel.evidence[0]}")
    
    print("   Finding series relationships...")
    series_relationships = mapper.find_series_relationships()
    print(f"   ✓ Found {len(series_relationships)} series relationships")
    
    for rel in series_relationships[:3]:
        source_title = mapper.books[rel.source_book_id].title
        target_title = mapper.books[rel.target_book_id].title
        print(f"     • {source_title} → {target_title} ({rel.relationship_type.value})")
    
    print("   Finding translation relationships...")
    translation_relationships = mapper.find_translation_relationships()
    print(f"   ✓ Found {len(translation_relationships)} translation relationships")
    
    for rel in translation_relationships:
        source_title = mapper.books[rel.source_book_id].title
        target_title = mapper.books[rel.target_book_id].title
        print(f"     • {source_title} ↔ {target_title}")
        print(f"       Confidence: {rel.confidence:.2f}")
    
    print("   Finding edition relationships...")
    edition_relationships = mapper.find_edition_relationships()
    print(f"   ✓ Found {len(edition_relationships)} edition relationships")
    
    for rel in edition_relationships:
        source_title = mapper.books[rel.source_book_id].title
        target_title = mapper.books[rel.target_book_id].title
        print(f"     • {source_title} ↔ {target_title}")
        print(f"       Confidence: {rel.confidence:.2f}")
    
    print("   Finding thematic relationships...")
    thematic_relationships = mapper.find_thematic_relationships()
    print(f"   ✓ Found {len(thematic_relationships)} thematic relationships")
    
    for rel in thematic_relationships[:5]:  # Show first 5
        source_title = mapper.books[rel.source_book_id].title
        target_title = mapper.books[rel.target_book_id].title
        print(f"     • {source_title} ↔ {target_title}")
        print(f"       Similarity: {rel.confidence:.3f}")
        if rel.metadata.get('common_themes'):
            print(f"       Themes: {', '.join(rel.metadata['common_themes'][:2])}")


def test_comprehensive_discovery(mapper: BookRelationshipMapper):
    """Test comprehensive relationship discovery."""
    print("\n📚 Running comprehensive relationship discovery...")
    
    all_relationships = mapper.discover_all_relationships()
    
    print(f"   ✓ Discovered {len(all_relationships)} total relationships")
    
    # Analyze relationship types
    relationship_counts = {}
    for rel in all_relationships:
        rel_type = rel.relationship_type.value
        relationship_counts[rel_type] = relationship_counts.get(rel_type, 0) + 1
    
    print("   Relationship breakdown:")
    for rel_type, count in relationship_counts.items():
        print(f"     • {rel_type.replace('_', ' ').title()}: {count}")


def test_thematic_clustering(mapper: BookRelationshipMapper):
    """Test thematic clustering functionality."""
    print("\n📚 Testing thematic clustering...")
    
    clusters = mapper.generate_thematic_clusters(min_cluster_size=2)
    print(f"   ✓ Generated {len(clusters)} thematic clusters")
    
    for i, cluster in enumerate(clusters):
        print(f"   Cluster {i+1}: {cluster.theme}")
        print(f"     Books: {len(cluster.books)}")
        print(f"     Confidence: {cluster.confidence:.3f}")
        
        # Show book titles
        for book_id in cluster.books[:3]:  # Show first 3 books
            book_title = mapper.books[book_id].title
            print(f"       • {book_title}")
        
        if len(cluster.books) > 3:
            print(f"       ... and {len(cluster.books) - 3} more")
        
        # Show keywords
        if cluster.keywords:
            print(f"     Keywords: {', '.join(cluster.keywords[:5])}")
        print()


def test_recommendation_system(mapper: BookRelationshipMapper):
    """Test the recommendation system."""
    print("\n📚 Testing recommendation system...")
    
    # Test recommendations for different books
    test_books = ["bhagavad_gita_en", "art_of_war", "thinking_fast_slow"]
    
    for book_id in test_books:
        if book_id not in mapper.books:
            continue
            
        book_title = mapper.books[book_id].title
        print(f"\n   Recommendations for '{book_title}':")
        
        recommendations = mapper.generate_recommendations(book_id, max_recommendations=5)
        
        if not recommendations:
            print("     No recommendations found")
            continue
        
        for i, rec in enumerate(recommendations, 1):
            rec_title = mapper.books[rec.recommended_book_id].title
            print(f"     {i}. {rec_title}")
            print(f"        Score: {rec.score:.3f}")
            print(f"        Reasons: {', '.join(rec.reasons)}")
            print()


def test_relationship_statistics(mapper: BookRelationshipMapper):
    """Test relationship statistics generation."""
    print("\n📊 Relationship Statistics:")
    
    stats = mapper.get_relationship_statistics()
    
    print(f"   Total books: {stats['total_books']}")
    print(f"   Total relationships: {stats['total_relationships']}")
    print(f"   Books with relationships: {stats['books_with_relationships']}")
    print(f"   Thematic clusters: {stats['thematic_clusters']}")
    
    print("\n   Relationship types:")
    for rel_type, count in stats['relationship_types'].items():
        print(f"     • {rel_type.replace('_', ' ').title()}: {count}")
    
    print("\n   Confidence distribution:")
    for conf_level, count in stats['confidence_distribution'].items():
        print(f"     • {conf_level.replace('_', ' ').title()}: {count}")


def export_results_to_json(mapper: BookRelationshipMapper, filename: str):
    """Export relationship mapping results to JSON."""
    print(f"\n💾 Exporting results to {filename}...")
    
    # Get comprehensive stats
    stats = mapper.get_relationship_statistics()
    
    export_data = {
        "timestamp": "2025-06-26T21:00:00.000000",
        "summary": {
            "total_books": len(mapper.books),
            "total_relationships": len(mapper.relationships),
            "relationship_types": len(set(rel.relationship_type for rel in mapper.relationships)),
            "thematic_clusters": len(mapper.thematic_clusters)
        },
        "statistics": stats,
        "books": {},
        "relationships": [],
        "thematic_clusters": []
    }
    
    # Export books
    for book_id, book in mapper.books.items():
        export_data["books"][book_id] = {
            "title": book.title,
            "authors": book.authors,
            "publication_year": book.publication_year,
            "language": book.language,
            "categories": book.categories,
            "subjects": book.subjects,
            "series": book.series,
            "series_number": book.series_number,
            "edition": book.edition
        }
    
    # Export relationships
    for rel in mapper.relationships:
        export_data["relationships"].append({
            "source_book_id": rel.source_book_id,
            "target_book_id": rel.target_book_id,
            "relationship_type": rel.relationship_type.value,
            "confidence": rel.confidence,
            "confidence_level": rel.confidence_level.value,
            "evidence": rel.evidence,
            "metadata": rel.metadata
        })
    
    # Export clusters
    for cluster in mapper.thematic_clusters:
        export_data["thematic_clusters"].append({
            "cluster_id": cluster.cluster_id,
            "theme": cluster.theme,
            "books": cluster.books,
            "keywords": cluster.keywords,
            "confidence": cluster.confidence
        })
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Exported complete relationship mapping data")


def main():
    """Run all book relationship mapping demos."""
    print("🚀 Testing Lexicon Book Relationship Mapping System")
    print("=" * 60)
    
    # Create temporary directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = Path(temp_dir) / "relationships"
        
        # Create mapper
        mapper = BookRelationshipMapper(
            data_dir=data_dir,
            similarity_threshold=0.3,
            max_recommendations=10
        )
        
        # Add sample books
        print("📚 Adding sample books to library...")
        books = [create_book_metadata_from_dict(book_data) for book_data in SAMPLE_BOOKS]
        mapper.add_books(books)
        print(f"   ✓ Added {len(books)} books to the library")
        
        try:
            # Run tests
            test_relationship_discovery(mapper)
            test_comprehensive_discovery(mapper)
            test_thematic_clustering(mapper)
            test_recommendation_system(mapper)
            test_relationship_statistics(mapper)
            
            # Export results
            export_results_to_json(mapper, 'book_relationship_demo_results.json')
            
            print("\n" + "=" * 60)
            print("✅ All book relationship mapping tests completed successfully!")
            
            print("\nKey Features Demonstrated:")
            print("• Same-author relationship detection")
            print("• Series and sequel/prequel identification")
            print("• Translation relationship mapping")
            print("• Edition tracking and comparison")
            print("• Thematic similarity analysis using TF-IDF")
            print("• Intelligent book recommendation system")
            print("• Thematic clustering for content organization")
            print("• Comprehensive relationship statistics")
            print("• Data persistence and JSON export")
            
        except Exception as e:
            print(f"\n❌ Demo failed with error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
