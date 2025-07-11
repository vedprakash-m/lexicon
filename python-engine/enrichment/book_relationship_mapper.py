#!/usr/bin/env python3
"""
Book Relationship Mapping System for Lexicon

This module provides comprehensive relationship mapping between books,
including related works identification, translation tracking, edition comparison,
citation mapping, thematic clustering, and recommendation generation.
"""

import asyncio
import json
import re
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union
from urllib.parse import quote

import aiohttp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class RelationshipType(Enum):
    """Types of relationships between books."""
    SAME_AUTHOR = "same_author"
    SAME_SERIES = "same_series"
    TRANSLATION = "translation"
    EDITION = "edition"
    CITATION = "citation"
    THEMATIC_SIMILARITY = "thematic_similarity"
    SEQUEL = "sequel"
    PREQUEL = "prequel"
    ADAPTATION = "adaptation"
    COMMENTARY = "commentary"
    ANTHOLOGY_MEMBER = "anthology_member"
    INFLUENCED_BY = "influenced_by"
    INFLUENCES = "influences"


class ConfidenceLevel(Enum):
    """Confidence levels for relationship identification."""
    VERY_HIGH = "very_high"  # 0.9+
    HIGH = "high"           # 0.7-0.9
    MEDIUM = "medium"       # 0.5-0.7
    LOW = "low"            # 0.3-0.5
    VERY_LOW = "very_low"  # <0.3


@dataclass
class BookRelationship:
    """Represents a relationship between two books."""
    source_book_id: str
    target_book_id: str
    relationship_type: RelationshipType
    confidence: float
    evidence: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    discovered_date: datetime = field(default_factory=datetime.now)
    verified: bool = False
    
    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Get confidence level based on confidence score."""
        if self.confidence >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif self.confidence >= 0.7:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif self.confidence >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW


@dataclass
class BookMetadata:
    """Enhanced book metadata for relationship mapping."""
    book_id: str
    title: str
    authors: List[str] = field(default_factory=list)
    isbn: Optional[str] = None
    series: Optional[str] = None
    series_number: Optional[int] = None
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    language: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    subjects: List[str] = field(default_factory=list)
    description: Optional[str] = None
    page_count: Optional[int] = None
    original_title: Optional[str] = None
    original_language: Optional[str] = None
    translator: Optional[str] = None
    edition: Optional[str] = None
    citations: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


@dataclass
class ThematicCluster:
    """Represents a cluster of thematically related books."""
    cluster_id: str
    theme: str
    books: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    confidence: float = 0.0
    created_date: datetime = field(default_factory=datetime.now)


@dataclass
class RecommendationResult:
    """Represents a book recommendation with reasoning."""
    recommended_book_id: str
    score: float
    reasons: List[str] = field(default_factory=list)
    relationship_types: List[RelationshipType] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class BookRelationshipMapper:
    """
    Comprehensive book relationship mapping system.
    
    Identifies and tracks various types of relationships between books
    including authorship, series, translations, editions, citations,
    and thematic similarities.
    """
    
    def __init__(
        self,
        data_dir: Union[str, Path],
        similarity_threshold: float = 0.3,
        max_recommendations: int = 10
    ):
        """
        Initialize the book relationship mapper.
        
        Args:
            data_dir: Directory for storing relationship data
            similarity_threshold: Minimum similarity score for thematic relationships
            max_recommendations: Maximum number of recommendations to generate
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.similarity_threshold = similarity_threshold
        self.max_recommendations = max_recommendations
        
        # Data storage
        self.books: Dict[str, BookMetadata] = {}
        self.relationships: List[BookRelationship] = []
        self.thematic_clusters: List[ThematicCluster] = []
        
        # Caches
        self._similarity_cache: Dict[Tuple[str, str], float] = {}
        self._recommendation_cache: Dict[str, List[RecommendationResult]] = {}
        
        # Load existing data
        self._load_data()
        
        # Initialize ML components
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self._feature_matrix = None
        self._book_ids_order = []
    
    def _load_data(self):
        """Load existing relationship data from disk."""
        # Load books
        books_file = self.data_dir / "books.json"
        if books_file.exists():
            try:
                with open(books_file, 'r', encoding='utf-8') as f:
                    books_data = json.load(f)
                    self.books = {
                        book_id: BookMetadata(**book_data)
                        for book_id, book_data in books_data.items()
                    }
            except Exception as e:
                print(f"Warning: Could not load books data: {e}")
        
        # Load relationships
        relationships_file = self.data_dir / "relationships.json"
        if relationships_file.exists():
            try:
                with open(relationships_file, 'r', encoding='utf-8') as f:
                    relationships_data = json.load(f)
                    self.relationships = [
                        BookRelationship(
                            source_book_id=rel['source_book_id'],
                            target_book_id=rel['target_book_id'],
                            relationship_type=RelationshipType(rel['relationship_type']),
                            confidence=rel['confidence'],
                            evidence=rel.get('evidence', []),
                            metadata=rel.get('metadata', {}),
                            discovered_date=datetime.fromisoformat(rel['discovered_date']),
                            verified=rel.get('verified', False)
                        )
                        for rel in relationships_data
                    ]
            except Exception as e:
                print(f"Warning: Could not load relationships data: {e}")
        
        # Load thematic clusters
        clusters_file = self.data_dir / "thematic_clusters.json"
        if clusters_file.exists():
            try:
                with open(clusters_file, 'r', encoding='utf-8') as f:
                    clusters_data = json.load(f)
                    self.thematic_clusters = [
                        ThematicCluster(
                            cluster_id=cluster['cluster_id'],
                            theme=cluster['theme'],
                            books=cluster['books'],
                            keywords=cluster.get('keywords', []),
                            confidence=cluster.get('confidence', 0.0),
                            created_date=datetime.fromisoformat(cluster['created_date'])
                        )
                        for cluster in clusters_data
                    ]
            except Exception as e:
                print(f"Warning: Could not load clusters data: {e}")
    
    def _save_data(self):
        """Save relationship data to disk."""
        try:
            # Save books
            books_data = {
                book_id: {k: (v.isoformat() if isinstance(v, datetime) else v)
                         for k, v in book.__dict__.items()}
                for book_id, book in self.books.items()
            }
            with open(self.data_dir / "books.json", 'w', encoding='utf-8') as f:
                json.dump(books_data, f, indent=2, ensure_ascii=False)
            
            # Save relationships
            relationships_data = [
                {
                    'source_book_id': rel.source_book_id,
                    'target_book_id': rel.target_book_id,
                    'relationship_type': rel.relationship_type.value,
                    'confidence': rel.confidence,
                    'evidence': rel.evidence,
                    'metadata': rel.metadata,
                    'discovered_date': rel.discovered_date.isoformat(),
                    'verified': rel.verified
                }
                for rel in self.relationships
            ]
            with open(self.data_dir / "relationships.json", 'w', encoding='utf-8') as f:
                json.dump(relationships_data, f, indent=2, ensure_ascii=False)
            
            # Save thematic clusters
            clusters_data = [
                {
                    'cluster_id': cluster.cluster_id,
                    'theme': cluster.theme,
                    'books': cluster.books,
                    'keywords': cluster.keywords,
                    'confidence': cluster.confidence,
                    'created_date': cluster.created_date.isoformat()
                }
                for cluster in self.thematic_clusters
            ]
            with open(self.data_dir / "thematic_clusters.json", 'w', encoding='utf-8') as f:
                json.dump(clusters_data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            print(f"Warning: Could not save relationship data: {e}")
    
    def add_book(self, book: BookMetadata):
        """Add a book to the relationship mapping system."""
        self.books[book.book_id] = book
        # Clear caches when new book is added
        self._similarity_cache.clear()
        self._recommendation_cache.clear()
        self._feature_matrix = None
    
    def add_books(self, books: List[BookMetadata]):
        """Add multiple books to the system."""
        for book in books:
            self.books[book.book_id] = book
        # Clear caches
        self._similarity_cache.clear()
        self._recommendation_cache.clear()
        self._feature_matrix = None
    
    def find_same_author_relationships(self) -> List[BookRelationship]:
        """Find relationships between books by the same author."""
        relationships = []
        author_books = defaultdict(list)
        
        # Group books by author
        for book_id, book in self.books.items():
            for author in book.authors:
                # Normalize author name
                normalized_author = self._normalize_author_name(author)
                author_books[normalized_author].append(book_id)
        
        # Create relationships between books by same author
        for author, book_ids in author_books.items():
            if len(book_ids) > 1:
                for i, source_id in enumerate(book_ids):
                    for target_id in book_ids[i+1:]:
                        # Get the original author name from the first book
                        source_book = self.books[source_id]
                        original_author = source_book.authors[0] if source_book.authors else author
                        
                        relationship = BookRelationship(
                            source_book_id=source_id,
                            target_book_id=target_id,
                            relationship_type=RelationshipType.SAME_AUTHOR,
                            confidence=0.95,  # Very high confidence for exact author matches
                            evidence=[f"Same author: {original_author}"],
                            metadata={'author': original_author}
                        )
                        relationships.append(relationship)
        
        return relationships
    
    def find_series_relationships(self) -> List[BookRelationship]:
        """Find relationships between books in the same series."""
        relationships = []
        series_books = defaultdict(list)
        
        # Group books by series
        for book_id, book in self.books.items():
            if book.series:
                # Normalize series name
                normalized_series = self._normalize_series_name(book.series)
                series_books[normalized_series].append((book_id, book.series_number or 0))
        
        # Create series relationships
        for series, book_data in series_books.items():
            if len(book_data) > 1:
                # Sort by series number
                book_data.sort(key=lambda x: x[1])
                
                for i, (source_id, source_num) in enumerate(book_data):
                    for target_id, target_num in book_data[i+1:]:
                        # Determine relationship type
                        if source_num < target_num and target_num == source_num + 1:
                            rel_type = RelationshipType.SEQUEL
                        elif source_num > target_num and source_num == target_num + 1:
                            rel_type = RelationshipType.PREQUEL
                        else:
                            rel_type = RelationshipType.SAME_SERIES
                        
                        relationship = BookRelationship(
                            source_book_id=source_id,
                            target_book_id=target_id,
                            relationship_type=rel_type,
                            confidence=0.9,
                            evidence=[f"Same series: {self.books[source_id].series}"],
                            metadata={
                                'series': self.books[source_id].series,
                                'source_number': source_num,
                                'target_number': target_num
                            }
                        )
                        relationships.append(relationship)
        
        return relationships
    
    def find_translation_relationships(self) -> List[BookRelationship]:
        """Find translation relationships between books."""
        relationships = []
        
        # Group by normalized title and author
        title_groups = defaultdict(list)
        
        for book_id, book in self.books.items():
            # Use original title if available, otherwise regular title
            base_title = book.original_title or book.title
            normalized_title = self._normalize_title(base_title)
            
            # Group by title and primary author
            primary_author = book.authors[0] if book.authors else "unknown"
            key = (normalized_title, self._normalize_author_name(primary_author))
            title_groups[key].append(book_id)
        
        # Find translation relationships
        for (title, author), book_ids in title_groups.items():
            if len(book_ids) > 1:
                for i, source_id in enumerate(book_ids):
                    for target_id in book_ids[i+1:]:
                        source_book = self.books[source_id]
                        target_book = self.books[target_id]
                        
                        # Check if they're likely translations
                        confidence = self._assess_translation_confidence(source_book, target_book)
                        
                        if confidence > 0.5:
                            evidence = []
                            if source_book.language != target_book.language:
                                evidence.append(f"Different languages: {source_book.language} vs {target_book.language}")
                            if source_book.translator or target_book.translator:
                                evidence.append("Translator information available")
                            if source_book.original_title or target_book.original_title:
                                evidence.append("Original title information available")
                            
                            relationship = BookRelationship(
                                source_book_id=source_id,
                                target_book_id=target_id,
                                relationship_type=RelationshipType.TRANSLATION,
                                confidence=confidence,
                                evidence=evidence,
                                metadata={
                                    'source_language': source_book.language,
                                    'target_language': target_book.language,
                                    'translator': target_book.translator or source_book.translator
                                }
                            )
                            relationships.append(relationship)
        
        return relationships
    
    def find_edition_relationships(self) -> List[BookRelationship]:
        """Find edition relationships between books."""
        relationships = []
        
        # Group by ISBN root or normalized title+author
        edition_groups = defaultdict(list)
        
        for book_id, book in self.books.items():
            if book.isbn:
                # Use ISBN-10 prefix for grouping
                isbn_root = book.isbn.replace('-', '').replace(' ', '')[:9]
                edition_groups[f"isbn_{isbn_root}"].append(book_id)
            
            # Also group by title+author for books without ISBN
            normalized_title = self._normalize_title(book.title)
            primary_author = book.authors[0] if book.authors else "unknown"
            key = f"title_{normalized_title}_{self._normalize_author_name(primary_author)}"
            edition_groups[key].append(book_id)
        
        # Find edition relationships
        for group_key, book_ids in edition_groups.items():
            if len(book_ids) > 1:
                for i, source_id in enumerate(book_ids):
                    for target_id in book_ids[i+1:]:
                        source_book = self.books[source_id]
                        target_book = self.books[target_id]
                        
                        # Check if they're likely different editions
                        confidence = self._assess_edition_confidence(source_book, target_book)
                        
                        if confidence > 0.6:
                            evidence = []
                            if source_book.publication_year != target_book.publication_year:
                                evidence.append(f"Different publication years: {source_book.publication_year} vs {target_book.publication_year}")
                            if source_book.publisher != target_book.publisher:
                                evidence.append(f"Different publishers: {source_book.publisher} vs {target_book.publisher}")
                            if source_book.edition != target_book.edition:
                                evidence.append(f"Different editions: {source_book.edition} vs {target_book.edition}")
                            
                            relationship = BookRelationship(
                                source_book_id=source_id,
                                target_book_id=target_id,
                                relationship_type=RelationshipType.EDITION,
                                confidence=confidence,
                                evidence=evidence,
                                metadata={
                                    'source_edition': source_book.edition,
                                    'target_edition': target_book.edition,
                                    'source_year': source_book.publication_year,
                                    'target_year': target_book.publication_year
                                }
                            )
                            relationships.append(relationship)
        
        return relationships
    
    def find_thematic_relationships(self) -> List[BookRelationship]:
        """Find thematic similarity relationships between books."""
        if len(self.books) < 2:
            return []
        
        # Build feature matrix if not exists
        if self._feature_matrix is None:
            self._build_feature_matrix()
        
        relationships = []
        
        # Calculate pairwise similarities
        for i, source_id in enumerate(self._book_ids_order):
            for j, target_id in enumerate(self._book_ids_order[i+1:], i+1):
                cache_key = (source_id, target_id)
                
                if cache_key in self._similarity_cache:
                    similarity = self._similarity_cache[cache_key]
                else:
                    similarity = cosine_similarity(
                        self._feature_matrix[i:i+1],
                        self._feature_matrix[j:j+1]
                    )[0][0]
                    self._similarity_cache[cache_key] = similarity
                
                if similarity > self.similarity_threshold:
                    # Identify common themes
                    common_themes = self._identify_common_themes(source_id, target_id)
                    
                    relationship = BookRelationship(
                        source_book_id=source_id,
                        target_book_id=target_id,
                        relationship_type=RelationshipType.THEMATIC_SIMILARITY,
                        confidence=similarity,
                        evidence=[f"Thematic similarity score: {similarity:.3f}"] + common_themes,
                        metadata={
                            'similarity_score': similarity,
                            'common_themes': common_themes
                        }
                    )
                    relationships.append(relationship)
        
        return relationships
    
    def _build_feature_matrix(self):
        """Build TF-IDF feature matrix for thematic analysis."""
        if not self.books:
            return
        
        # Prepare text corpus
        texts = []
        self._book_ids_order = []
        
        for book_id, book in self.books.items():
            # Combine various text fields
            text_parts = []
            
            if book.title:
                text_parts.append(book.title)
            if book.description:
                text_parts.append(book.description)
            if book.categories:
                text_parts.extend(book.categories)
            if book.subjects:
                text_parts.extend(book.subjects)
            if book.keywords:
                text_parts.extend(book.keywords)
            
            combined_text = " ".join(text_parts)
            texts.append(combined_text)
            self._book_ids_order.append(book_id)
        
        # Build TF-IDF matrix
        if texts:
            self._feature_matrix = self.tfidf_vectorizer.fit_transform(texts)
    
    def _identify_common_themes(self, book1_id: str, book2_id: str) -> List[str]:
        """Identify common themes between two books."""
        book1 = self.books[book1_id]
        book2 = self.books[book2_id]
        
        common_themes = []
        
        # Common categories
        common_categories = set(book1.categories) & set(book2.categories)
        if common_categories:
            common_themes.extend([f"Category: {cat}" for cat in common_categories])
        
        # Common subjects
        common_subjects = set(book1.subjects) & set(book2.subjects)
        if common_subjects:
            common_themes.extend([f"Subject: {subj}" for subj in common_subjects])
        
        # Common keywords
        common_keywords = set(book1.keywords) & set(book2.keywords)
        if common_keywords:
            common_themes.extend([f"Keyword: {kw}" for kw in list(common_keywords)[:3]])
        
        return common_themes[:5]  # Limit to top 5 themes
    
    def generate_thematic_clusters(self, min_cluster_size: int = 2) -> List[ThematicCluster]:
        """Generate thematic clusters of related books."""
        if not self.books or len(self.books) < min_cluster_size:
            return []
        
        # Build feature matrix if not exists
        if self._feature_matrix is None:
            self._build_feature_matrix()
        
        clusters = []
        used_books = set()
        
        # Simple clustering based on similarity threshold
        for i, source_id in enumerate(self._book_ids_order):
            if source_id in used_books:
                continue
            
            cluster_books = [source_id]
            cluster_similarities = []
            
            for j, target_id in enumerate(self._book_ids_order):
                if i == j or target_id in used_books:
                    continue
                
                similarity = cosine_similarity(
                    self._feature_matrix[i:i+1],
                    self._feature_matrix[j:j+1]
                )[0][0]
                
                if similarity > self.similarity_threshold * 1.5:  # Higher threshold for clusters
                    cluster_books.append(target_id)
                    cluster_similarities.append(similarity)
            
            if len(cluster_books) >= min_cluster_size:
                # Generate cluster theme
                theme = self._generate_cluster_theme(cluster_books)
                keywords = self._extract_cluster_keywords(cluster_books)
                
                cluster = ThematicCluster(
                    cluster_id=f"cluster_{len(clusters)}_{datetime.now().strftime('%Y%m%d')}",
                    theme=theme,
                    books=cluster_books,
                    keywords=keywords,
                    confidence=np.mean(cluster_similarities) if cluster_similarities else 0.0
                )
                clusters.append(cluster)
                used_books.update(cluster_books)
        
        self.thematic_clusters = clusters
        return clusters
    
    def _generate_cluster_theme(self, book_ids: List[str]) -> str:
        """Generate a theme name for a cluster of books."""
        # Collect all categories and subjects
        all_categories = []
        all_subjects = []
        
        for book_id in book_ids:
            book = self.books[book_id]
            all_categories.extend(book.categories)
            all_subjects.extend(book.subjects)
        
        # Find most common category/subject
        if all_categories:
            most_common_category = Counter(all_categories).most_common(1)[0][0]
            return f"Books about {most_common_category}"
        elif all_subjects:
            most_common_subject = Counter(all_subjects).most_common(1)[0][0]
            return f"Books on {most_common_subject}"
        else:
            return f"Related Books Cluster"
    
    def _extract_cluster_keywords(self, book_ids: List[str]) -> List[str]:
        """Extract representative keywords for a cluster."""
        all_keywords = []
        
        for book_id in book_ids:
            book = self.books[book_id]
            all_keywords.extend(book.keywords)
            all_keywords.extend(book.categories)
            all_keywords.extend(book.subjects)
        
        # Return most common keywords
        keyword_counts = Counter(all_keywords)
        return [kw for kw, count in keyword_counts.most_common(10) if count > 1]
    
    def generate_recommendations(
        self, 
        book_id: str, 
        max_recommendations: Optional[int] = None
    ) -> List[RecommendationResult]:
        """Generate book recommendations based on relationships."""
        if book_id not in self.books:
            return []
        
        max_recs = max_recommendations or self.max_recommendations
        
        # Check cache first
        if book_id in self._recommendation_cache:
            return self._recommendation_cache[book_id][:max_recs]
        
        recommendations = []
        
        # Find all relationships involving this book
        related_books = defaultdict(list)
        
        for relationship in self.relationships:
            if relationship.source_book_id == book_id:
                related_books[relationship.target_book_id].append(relationship)
            elif relationship.target_book_id == book_id:
                related_books[relationship.source_book_id].append(relationship)
        
        # Score and rank recommendations
        for related_book_id, relationships in related_books.items():
            if related_book_id == book_id:
                continue
            
            # Calculate composite score
            score = self._calculate_recommendation_score(relationships)
            
            # Generate reasons
            reasons = []
            relationship_types = []
            
            for rel in relationships:
                relationship_types.append(rel.relationship_type)
                if rel.relationship_type == RelationshipType.SAME_AUTHOR:
                    reasons.append("Same author")
                elif rel.relationship_type == RelationshipType.SAME_SERIES:
                    reasons.append("Same series")
                elif rel.relationship_type == RelationshipType.THEMATIC_SIMILARITY:
                    reasons.append(f"Similar themes (similarity: {rel.confidence:.2f})")
                elif rel.relationship_type == RelationshipType.TRANSLATION:
                    reasons.append("Translation of the same work")
                elif rel.relationship_type == RelationshipType.EDITION:
                    reasons.append("Different edition")
            
            recommendation = RecommendationResult(
                recommended_book_id=related_book_id,
                score=score,
                reasons=reasons,
                relationship_types=relationship_types,
                metadata={
                    'relationship_count': len(relationships),
                    'avg_confidence': np.mean([r.confidence for r in relationships])
                }
            )
            recommendations.append(recommendation)
        
        # Sort by score
        recommendations.sort(key=lambda x: x.score, reverse=True)
        
        # Cache results
        self._recommendation_cache[book_id] = recommendations
        
        return recommendations[:max_recs]
    
    def _calculate_recommendation_score(self, relationships: List[BookRelationship]) -> float:
        """Calculate a composite recommendation score."""
        if not relationships:
            return 0.0
        
        # Weight different relationship types
        type_weights = {
            RelationshipType.SAME_AUTHOR: 0.8,
            RelationshipType.SAME_SERIES: 0.9,
            RelationshipType.SEQUEL: 0.95,
            RelationshipType.PREQUEL: 0.95,
            RelationshipType.TRANSLATION: 0.7,
            RelationshipType.EDITION: 0.6,
            RelationshipType.THEMATIC_SIMILARITY: 0.5,
            RelationshipType.CITATION: 0.4,
            RelationshipType.COMMENTARY: 0.3,
        }
        
        weighted_scores = []
        for rel in relationships:
            weight = type_weights.get(rel.relationship_type, 0.3)
            weighted_scores.append(rel.confidence * weight)
        
        # Use maximum score with bonus for multiple relationships
        base_score = max(weighted_scores)
        relationship_bonus = min(0.2, (len(relationships) - 1) * 0.05)
        
        return min(1.0, base_score + relationship_bonus)
    
    def discover_all_relationships(self) -> List[BookRelationship]:
        """Discover all types of relationships between books."""
        all_relationships = []
        
        # Find different types of relationships
        print("Finding same-author relationships...")
        all_relationships.extend(self.find_same_author_relationships())
        
        print("Finding series relationships...")
        all_relationships.extend(self.find_series_relationships())
        
        print("Finding translation relationships...")
        all_relationships.extend(self.find_translation_relationships())
        
        print("Finding edition relationships...")
        all_relationships.extend(self.find_edition_relationships())
        
        print("Finding thematic relationships...")
        all_relationships.extend(self.find_thematic_relationships())
        
        # Store relationships
        self.relationships = all_relationships
        
        # Generate thematic clusters
        print("Generating thematic clusters...")
        self.generate_thematic_clusters()
        
        return all_relationships
    
    def get_relationship_statistics(self) -> Dict:
        """Get statistics about discovered relationships."""
        stats = {
            'total_books': len(self.books),
            'total_relationships': len(self.relationships),
            'relationship_types': {},
            'confidence_distribution': {},
            'thematic_clusters': len(self.thematic_clusters),
            'books_with_relationships': 0
        }
        
        # Count relationship types
        for rel in self.relationships:
            rel_type = rel.relationship_type.value
            stats['relationship_types'][rel_type] = stats['relationship_types'].get(rel_type, 0) + 1
        
        # Count confidence levels
        for rel in self.relationships:
            conf_level = rel.confidence_level.value
            stats['confidence_distribution'][conf_level] = stats['confidence_distribution'].get(conf_level, 0) + 1
        
        # Count books with relationships
        books_with_relationships = set()
        for rel in self.relationships:
            books_with_relationships.add(rel.source_book_id)
            books_with_relationships.add(rel.target_book_id)
        stats['books_with_relationships'] = len(books_with_relationships)
        
        return stats
    
    # Utility methods for normalization and assessment
    
    def _normalize_author_name(self, author: str) -> str:
        """Normalize author name for comparison."""
        if not author:
            return ""
        
        # Remove common prefixes/suffixes
        name = re.sub(r'\b(Dr|Prof|Mr|Mrs|Ms|Sir|Lord|Saint|St)\.?\b', '', author, flags=re.IGNORECASE)
        
        # Remove extra whitespace and periods
        name = re.sub(r'[^\w\s]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Convert to lowercase for comparison
        return name.lower()
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison."""
        if not title:
            return ""
        
        # Remove articles and common words
        title = re.sub(r'\b(the|a|an)\b', '', title, flags=re.IGNORECASE)
        
        # Remove edition information for comparison
        title = re.sub(r'\b(revised|new|updated|expanded|abridged|complete|unabridged|annotated|illustrated)\b', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\b(edition|ed\.?)\b', '', title, flags=re.IGNORECASE)
        
        # Remove parenthetical information
        title = re.sub(r'\([^)]*\)', '', title)
        
        # Remove punctuation and extra whitespace
        title = re.sub(r'[^\w\s]', '', title)
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title.lower()
    
    def _normalize_series_name(self, series: str) -> str:
        """Normalize series name for comparison."""
        if not series:
            return ""
        
        # Remove "series" suffix
        series = re.sub(r'\bseries\b', '', series, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        series = re.sub(r'\s+', ' ', series).strip()
        
        return series.lower()
    
    def _assess_translation_confidence(self, book1: BookMetadata, book2: BookMetadata) -> float:
        """Assess confidence that two books are translations of each other."""
        confidence = 0.0
        
        # Different languages boost confidence
        if book1.language and book2.language and book1.language != book2.language:
            confidence += 0.4
        
        # Translator information
        if book1.translator or book2.translator:
            confidence += 0.3
        
        # Original title information
        if book1.original_title or book2.original_title:
            confidence += 0.2
        
        # Similar publication years (translations often published close to original)
        if book1.publication_year and book2.publication_year:
            year_diff = abs(book1.publication_year - book2.publication_year)
            if year_diff <= 5:
                confidence += 0.1
            elif year_diff <= 10:
                confidence += 0.05
        
        return min(1.0, confidence)
    
    def _assess_edition_confidence(self, book1: BookMetadata, book2: BookMetadata) -> float:
        """Assess confidence that two books are different editions."""
        confidence = 0.0
        
        # Different publication years
        if book1.publication_year and book2.publication_year and book1.publication_year != book2.publication_year:
            confidence += 0.3
        
        # Different publishers
        if book1.publisher and book2.publisher and book1.publisher != book2.publisher:
            confidence += 0.2
        
        # Different editions mentioned
        if book1.edition and book2.edition and book1.edition != book2.edition:
            confidence += 0.4
        elif book1.edition or book2.edition:  # One has edition info, other doesn't
            confidence += 0.3
        
        # Same language (editions usually in same language)
        if book1.language and book2.language and book1.language == book2.language:
            confidence += 0.1
        
        # Title similarity (for revised editions)
        if "revised" in book1.title.lower() or "revised" in book2.title.lower():
            confidence += 0.2
        
        return min(1.0, confidence)


# Convenience functions
def create_book_metadata_from_dict(book_data: Dict) -> BookMetadata:
    """Create BookMetadata from dictionary data."""
    return BookMetadata(
        book_id=book_data.get('id', ''),
        title=book_data.get('title', ''),
        authors=book_data.get('authors', []),
        isbn=book_data.get('isbn'),
        series=book_data.get('series'),
        series_number=book_data.get('series_number'),
        publication_year=book_data.get('publication_year'),
        publisher=book_data.get('publisher'),
        language=book_data.get('language'),
        categories=book_data.get('categories', []),
        subjects=book_data.get('subjects', []),
        description=book_data.get('description'),
        page_count=book_data.get('page_count'),
        original_title=book_data.get('original_title'),
        original_language=book_data.get('original_language'),
        translator=book_data.get('translator'),
        edition=book_data.get('edition'),
        citations=book_data.get('citations', []),
        references=book_data.get('references', []),
        keywords=book_data.get('keywords', [])
    )
