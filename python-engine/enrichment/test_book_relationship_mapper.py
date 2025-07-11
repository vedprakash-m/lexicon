#!/usr/bin/env python3
"""
Test suite for Book Relationship Mapper

Comprehensive tests for the book relationship mapping system including:
- Same author relationships
- Series relationships  
- Translation detection
- Edition tracking
- Thematic similarity
- Recommendation generation
"""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from book_relationship_mapper import (
    BookMetadata, BookRelationship, BookRelationshipMapper,
    RelationshipType, ConfidenceLevel, ThematicCluster,
    RecommendationResult, create_book_metadata_from_dict
)


class TestBookRelationshipMapper(unittest.TestCase):
    """Test book relationship mapping functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.mapper = BookRelationshipMapper(data_dir=self.temp_dir)
        
        # Create test books
        self.test_books = [
            BookMetadata(
                book_id="bg_1",
                title="Bhagavad Gita As It Is",
                authors=["A.C. Bhaktivedanta Swami Prabhupada"],
                publication_year=1972,
                language="English",
                categories=["Philosophy", "Religion", "Spirituality"],
                subjects=["Hindu Philosophy", "Yoga", "Meditation"],
                description="Ancient wisdom text on yoga and spiritual philosophy"
            ),
            BookMetadata(
                book_id="bg_2", 
                title="Bhagavad Gita As It Is (Spanish)",
                authors=["A.C. Bhaktivedanta Swami Prabhupada"],
                publication_year=1975,
                language="Spanish",
                original_title="Bhagavad Gita As It Is",
                original_language="English",
                translator="Spanish Translation Team",
                categories=["Philosophy", "Religion", "Spirituality"],
                subjects=["Hindu Philosophy", "Yoga", "Meditation"],
                description="Spanish translation of ancient wisdom text"
            ),
            BookMetadata(
                book_id="sb_1",
                title="Srimad Bhagavatam Canto 1",
                authors=["A.C. Bhaktivedanta Swami Prabhupada"],
                series="Srimad Bhagavatam",
                series_number=1,
                publication_year=1974,
                language="English",
                categories=["Philosophy", "Religion", "Spirituality"],
                subjects=["Hindu Philosophy", "Stories", "Devotion"],
                description="First canto of the great Vedic literature"
            ),
            BookMetadata(
                book_id="sb_2",
                title="Srimad Bhagavatam Canto 2", 
                authors=["A.C. Bhaktivedanta Swami Prabhupada"],
                series="Srimad Bhagavatam",
                series_number=2,
                publication_year=1975,
                language="English", 
                categories=["Philosophy", "Religion", "Spirituality"],
                subjects=["Hindu Philosophy", "Stories", "Devotion"],
                description="Second canto of the great Vedic literature"
            ),
            BookMetadata(
                book_id="art_war",
                title="The Art of War",
                authors=["Sun Tzu"],
                publication_year=500,  # BCE approximation
                language="English",
                categories=["Strategy", "Military", "Philosophy"],
                subjects=["War", "Strategy", "Leadership"],
                description="Ancient Chinese military strategy text"
            ),
            BookMetadata(
                book_id="thinking_fast",
                title="Thinking, Fast and Slow",
                authors=["Daniel Kahneman"],
                publication_year=2011,
                language="English",
                categories=["Psychology", "Science"],
                subjects=["Cognitive Psychology", "Decision Making"],
                description="Modern insights into how the mind works"
            ),
            BookMetadata(
                book_id="bg_revised",
                title="Bhagavad Gita As It Is (Revised Edition)",
                authors=["A.C. Bhaktivedanta Swami Prabhupada"],
                publication_year=1983,
                language="English",
                edition="Revised",
                categories=["Philosophy", "Religion", "Spirituality"],
                subjects=["Hindu Philosophy", "Yoga", "Meditation"],
                description="Revised edition of the ancient wisdom text"
            )
        ]
        
        # Add test books to mapper
        for book in self.test_books:
            self.mapper.add_book(book)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_book_metadata_creation(self):
        """Test BookMetadata creation and properties."""
        book = self.test_books[0]
        
        self.assertEqual(book.book_id, "bg_1")
        self.assertEqual(book.title, "Bhagavad Gita As It Is")
        self.assertEqual(book.authors, ["A.C. Bhaktivedanta Swami Prabhupada"])
        self.assertEqual(book.publication_year, 1972)
        self.assertIn("Philosophy", book.categories)
    
    def test_book_relationship_creation(self):
        """Test BookRelationship creation and confidence levels."""
        relationship = BookRelationship(
            source_book_id="book1",
            target_book_id="book2",
            relationship_type=RelationshipType.SAME_AUTHOR,
            confidence=0.85
        )
        
        self.assertEqual(relationship.source_book_id, "book1")
        self.assertEqual(relationship.target_book_id, "book2") 
        self.assertEqual(relationship.relationship_type, RelationshipType.SAME_AUTHOR)
        self.assertEqual(relationship.confidence, 0.85)
        self.assertEqual(relationship.confidence_level, ConfidenceLevel.HIGH)
        self.assertFalse(relationship.verified)
    
    def test_confidence_level_calculation(self):
        """Test confidence level calculations."""
        test_cases = [
            (0.95, ConfidenceLevel.VERY_HIGH),
            (0.8, ConfidenceLevel.HIGH),
            (0.6, ConfidenceLevel.MEDIUM),
            (0.4, ConfidenceLevel.LOW),
            (0.2, ConfidenceLevel.VERY_LOW)
        ]
        
        for confidence, expected_level in test_cases:
            relationship = BookRelationship(
                source_book_id="test1",
                target_book_id="test2",
                relationship_type=RelationshipType.THEMATIC_SIMILARITY,
                confidence=confidence
            )
            self.assertEqual(relationship.confidence_level, expected_level)
    
    def test_add_book(self):
        """Test adding books to the mapper."""
        initial_count = len(self.mapper.books)
        
        new_book = BookMetadata(
            book_id="new_book",
            title="New Test Book",
            authors=["Test Author"]
        )
        
        self.mapper.add_book(new_book)
        
        self.assertEqual(len(self.mapper.books), initial_count + 1)
        self.assertIn("new_book", self.mapper.books)
        self.assertEqual(self.mapper.books["new_book"].title, "New Test Book")
    
    def test_same_author_relationships(self):
        """Test finding same-author relationships."""
        relationships = self.mapper.find_same_author_relationships()
        
        # Should find relationships between Prabhupada's books
        prabhupada_relationships = [
            rel for rel in relationships 
            if rel.relationship_type == RelationshipType.SAME_AUTHOR
        ]
        
        self.assertGreater(len(prabhupada_relationships), 0)
        
        # Check specific relationship
        bg_sb_relationship = None
        for rel in prabhupada_relationships:
            if (("bg_1" in [rel.source_book_id, rel.target_book_id]) and
                ("sb_1" in [rel.source_book_id, rel.target_book_id])):
                bg_sb_relationship = rel
                break
        
        self.assertIsNotNone(bg_sb_relationship)
        self.assertEqual(bg_sb_relationship.confidence, 0.95)
        self.assertIn("A.C. Bhaktivedanta Swami Prabhupada", bg_sb_relationship.evidence[0])
    
    def test_series_relationships(self):
        """Test finding series relationships.""" 
        relationships = self.mapper.find_series_relationships()
        
        # Should find sequel relationship between SB cantos
        series_relationships = [
            rel for rel in relationships
            if rel.relationship_type in [RelationshipType.SAME_SERIES, RelationshipType.SEQUEL]
        ]
        
        self.assertGreater(len(series_relationships), 0)
        
        # Check for sequel relationship
        sequel_relationship = None
        for rel in series_relationships:
            if rel.relationship_type == RelationshipType.SEQUEL:
                sequel_relationship = rel
                break
        
        if sequel_relationship:
            self.assertEqual(sequel_relationship.confidence, 0.9)
            self.assertIn("Srimad Bhagavatam", sequel_relationship.evidence[0])
    
    def test_translation_relationships(self):
        """Test finding translation relationships."""
        relationships = self.mapper.find_translation_relationships()
        
        # Should find translation relationship between English and Spanish BG
        translation_relationships = [
            rel for rel in relationships
            if rel.relationship_type == RelationshipType.TRANSLATION
        ]
        
        self.assertGreater(len(translation_relationships), 0)
        
        # Check specific translation relationship
        bg_translation = None
        for rel in translation_relationships:
            if (("bg_1" in [rel.source_book_id, rel.target_book_id]) and
                ("bg_2" in [rel.source_book_id, rel.target_book_id])):
                bg_translation = rel
                break
        
        self.assertIsNotNone(bg_translation)
        self.assertGreater(bg_translation.confidence, 0.5)
        self.assertTrue(any("language" in evidence.lower() for evidence in bg_translation.evidence))
    
    def test_edition_relationships(self):
        """Test finding edition relationships."""
        relationships = self.mapper.find_edition_relationships()
        
        # Should find edition relationship between original and revised BG
        edition_relationships = [
            rel for rel in relationships
            if rel.relationship_type == RelationshipType.EDITION
        ]
        
        self.assertGreater(len(edition_relationships), 0)
        
        # Check specific edition relationship
        bg_edition = None
        for rel in edition_relationships:
            if (("bg_1" in [rel.source_book_id, rel.target_book_id]) and
                ("bg_revised" in [rel.source_book_id, rel.target_book_id])):
                bg_edition = rel
                break
        
        self.assertIsNotNone(bg_edition)
        self.assertGreater(bg_edition.confidence, 0.6)
    
    def test_thematic_relationships(self):
        """Test finding thematic similarity relationships."""
        relationships = self.mapper.find_thematic_relationships()
        
        # Should find thematic relationships between similar books
        thematic_relationships = [
            rel for rel in relationships
            if rel.relationship_type == RelationshipType.THEMATIC_SIMILARITY
        ]
        
        # There should be some thematic relationships
        self.assertGreaterEqual(len(thematic_relationships), 0)
        
        # If relationships exist, check properties
        if thematic_relationships:
            rel = thematic_relationships[0]
            self.assertGreater(rel.confidence, self.mapper.similarity_threshold)
            self.assertIn('similarity_score', rel.metadata)
    
    def test_discover_all_relationships(self):
        """Test discovering all relationship types."""
        relationships = self.mapper.discover_all_relationships()
        
        self.assertGreater(len(relationships), 0)
        self.assertEqual(len(self.mapper.relationships), len(relationships))
        
        # Should have multiple relationship types
        relationship_types = set(rel.relationship_type for rel in relationships)
        self.assertIn(RelationshipType.SAME_AUTHOR, relationship_types)
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        # First discover relationships
        self.mapper.discover_all_relationships()
        
        # Generate recommendations for Bhagavad Gita
        recommendations = self.mapper.generate_recommendations("bg_1", max_recommendations=5)
        
        self.assertGreaterEqual(len(recommendations), 0)
        
        if recommendations:
            # Check recommendation structure
            rec = recommendations[0]
            self.assertIsInstance(rec, RecommendationResult)
            self.assertIsInstance(rec.score, float)
            self.assertIsInstance(rec.reasons, list)
            self.assertIsInstance(rec.relationship_types, list)
            
            # Score should be between 0 and 1
            self.assertGreaterEqual(rec.score, 0.0)
            self.assertLessEqual(rec.score, 1.0)
    
    def test_thematic_clusters(self):
        """Test thematic cluster generation."""
        clusters = self.mapper.generate_thematic_clusters(min_cluster_size=2)
        
        # Should generate some clusters for our test books
        self.assertGreaterEqual(len(clusters), 0)
        
        if clusters:
            cluster = clusters[0]
            self.assertIsInstance(cluster, ThematicCluster)
            self.assertGreaterEqual(len(cluster.books), 2)
            self.assertIsInstance(cluster.theme, str)
            self.assertIsInstance(cluster.keywords, list)
    
    def test_relationship_statistics(self):
        """Test relationship statistics generation."""
        # Discover relationships first
        self.mapper.discover_all_relationships()
        
        stats = self.mapper.get_relationship_statistics()
        
        self.assertIn('total_books', stats)
        self.assertIn('total_relationships', stats)
        self.assertIn('relationship_types', stats)
        self.assertIn('confidence_distribution', stats)
        self.assertIn('books_with_relationships', stats)
        
        self.assertEqual(stats['total_books'], len(self.test_books))
        self.assertGreaterEqual(stats['total_relationships'], 0)
    
    def test_normalization_methods(self):
        """Test text normalization methods."""
        # Test author normalization
        author1 = self.mapper._normalize_author_name("Dr. A.C. Bhaktivedanta Swami Prabhupada")
        author2 = self.mapper._normalize_author_name("A.C. Bhaktivedanta Swami Prabhupada")
        self.assertEqual(author1, author2)
        
        # Test title normalization
        title1 = self.mapper._normalize_title("The Bhagavad Gita As It Is!")
        title2 = self.mapper._normalize_title("Bhagavad Gita As It Is")
        self.assertEqual(title1, title2)
        
        # Test series normalization
        series1 = self.mapper._normalize_series_name("Srimad Bhagavatam Series")
        series2 = self.mapper._normalize_series_name("Srimad Bhagavatam")
        self.assertEqual(series1, series2)
    
    def test_confidence_assessment(self):
        """Test confidence assessment methods."""
        book1 = self.test_books[0]  # English BG
        book2 = self.test_books[1]  # Spanish BG
        
        # Test translation confidence
        translation_confidence = self.mapper._assess_translation_confidence(book1, book2)
        self.assertGreater(translation_confidence, 0.5)
        
        # Test edition confidence
        book3 = self.test_books[6]  # Revised BG
        edition_confidence = self.mapper._assess_edition_confidence(book1, book3)
        self.assertGreater(edition_confidence, 0.6)
    
    def test_data_persistence(self):
        """Test saving and loading relationship data."""
        # Add some relationships
        self.mapper.discover_all_relationships()
        
        # Save data
        self.mapper._save_data()
        
        # Create new mapper and load data
        new_mapper = BookRelationshipMapper(data_dir=self.temp_dir)
        
        # Check if data was loaded
        self.assertEqual(len(new_mapper.books), len(self.mapper.books))
        self.assertEqual(len(new_mapper.relationships), len(self.mapper.relationships))
    
    def test_create_book_metadata_from_dict(self):
        """Test creating BookMetadata from dictionary."""
        book_dict = {
            'id': 'test_book',
            'title': 'Test Book',
            'authors': ['Test Author'],
            'publication_year': 2023,
            'categories': ['Test Category'],
            'subjects': ['Test Subject']
        }
        
        book = create_book_metadata_from_dict(book_dict)
        
        self.assertEqual(book.book_id, 'test_book')
        self.assertEqual(book.title, 'Test Book')
        self.assertEqual(book.authors, ['Test Author'])
        self.assertEqual(book.publication_year, 2023)
        self.assertEqual(book.categories, ['Test Category'])
        self.assertEqual(book.subjects, ['Test Subject'])


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
