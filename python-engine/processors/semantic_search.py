"""
Advanced semantic search engine for Lexicon.

This module provides semantic similarity search, fuzzy matching, and faceted search
capabilities for finding relevant content in processed book catalogs.
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import asyncio
import time
from datetime import datetime, timedelta

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_ML_LIBS = True
except ImportError:
    HAS_ML_LIBS = False
    np = None
    SentenceTransformer = None
    TfidfVectorizer = None
    cosine_similarity = None

try:
    import Levenshtein
    HAS_FUZZY = True
except ImportError:
    HAS_FUZZY = False
    
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchConfig:
    """Configuration for semantic search engine."""
    # Model settings
    semantic_model: str = "all-MiniLM-L6-v2"
    use_semantic_similarity: bool = True
    similarity_threshold: float = 0.7
    
    # Fuzzy matching
    use_fuzzy_matching: bool = True
    fuzzy_threshold: float = 0.8
    max_edit_distance: int = 2
    
    # Search settings
    max_results: int = 50
    boost_exact_matches: bool = True
    boost_title_matches: float = 2.0
    boost_author_matches: float = 1.5
    
    # Cache settings
    enable_cache: bool = True
    cache_ttl_hours: int = 24
    max_cache_size: int = 1000

@dataclass 
class SearchResult:
    """Individual search result with relevance scoring."""
    id: str
    title: str
    author: str
    content: str
    metadata: Dict[str, Any]
    relevance_score: float
    match_type: str  # "exact", "semantic", "fuzzy", "metadata"
    highlighted_fields: Dict[str, str] = field(default_factory=dict)

@dataclass
class SearchQuery:
    """Structured search query with filters."""
    text: str
    filters: Dict[str, Any] = field(default_factory=dict)
    facets: List[str] = field(default_factory=list)
    sort_by: str = "relevance"
    sort_order: str = "desc"
    limit: int = 20
    offset: int = 0

@dataclass 
class SearchFacet:
    """Search facet for filtering results."""
    name: str
    values: List[Tuple[str, int]]  # (value, count) pairs

@dataclass
class SearchResponse:
    """Complete search response with results and metadata."""
    results: List[SearchResult]
    total_count: int
    facets: List[SearchFacet]
    query_time_ms: int
    suggestions: List[str] = field(default_factory=list)

class SemanticSearchEngine:
    """
    Advanced semantic search engine with ML-powered similarity search,
    fuzzy matching, and faceted search capabilities.
    """
    
    def __init__(self, config: SearchConfig = None):
        self.config = config or SearchConfig()
        self.documents: List[Dict[str, Any]] = []
        self.document_embeddings: Optional[np.ndarray] = None
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix: Optional[np.ndarray] = None
        self.semantic_model: Optional[SentenceTransformer] = None
        self.search_cache: Dict[str, Tuple[SearchResponse, datetime]] = {}
        
        # Initialize ML models if available
        if HAS_ML_LIBS and self.config.use_semantic_similarity:
            try:
                self.semantic_model = SentenceTransformer(self.config.semantic_model)
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=5000,
                    stop_words='english',
                    ngram_range=(1, 2)
                )
                logger.info(f"Initialized semantic model: {self.config.semantic_model}")
            except Exception as e:
                logger.warning(f"Failed to load semantic model: {e}")
                self.semantic_model = None
    
    def index_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Index a collection of documents for searching."""
        logger.info(f"Indexing {len(documents)} documents...")
        start_time = time.time()
        
        self.documents = documents
        
        # Build text corpus for indexing
        corpus = []
        for doc in documents:
            text_parts = []
            
            # Include searchable fields
            if doc.get('title'):
                text_parts.append(doc['title'])
            if doc.get('author'):
                text_parts.append(doc['author'])
            if doc.get('description'):
                text_parts.append(doc['description'])
            if doc.get('content'):
                text_parts.append(doc['content'][:1000])  # First 1000 chars
            if doc.get('categories'):
                text_parts.extend(doc['categories'])
            if doc.get('subjects'):
                text_parts.extend(doc['subjects'])
            if doc.get('keywords'):
                text_parts.extend(doc['keywords'])
            
            corpus.append(' '.join(text_parts))
        
        # Build TF-IDF index
        if self.tfidf_vectorizer and corpus:
            try:
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus)
                logger.info("Built TF-IDF index")
            except Exception as e:
                logger.warning(f"Failed to build TF-IDF index: {e}")
        
        # Build semantic embeddings
        if self.semantic_model and corpus:
            try:
                self.document_embeddings = self.semantic_model.encode(corpus)
                logger.info("Built semantic embeddings")
            except Exception as e:
                logger.warning(f"Failed to build semantic embeddings: {e}")
        
        index_time = time.time() - start_time
        logger.info(f"Indexing completed in {index_time:.2f}s")
    
    def search(self, query: Union[str, SearchQuery]) -> SearchResponse:
        """Perform comprehensive search with multiple search strategies."""
        if isinstance(query, str):
            query = SearchQuery(text=query)
        
        start_time = time.time()
        
        # Check cache first
        cache_key = self._get_cache_key(query)
        if self.config.enable_cache and cache_key in self.search_cache:
            cached_result, cache_time = self.search_cache[cache_key]
            if datetime.now() - cache_time < timedelta(hours=self.config.cache_ttl_hours):
                logger.debug("Returning cached search result")
                return cached_result
        
        # Perform multi-strategy search
        all_results = []
        
        # 1. Exact text matching
        exact_results = self._exact_search(query.text, query.filters)
        all_results.extend([(result, "exact") for result in exact_results])
        
        # 2. Semantic similarity search
        if self.semantic_model and self.document_embeddings is not None:
            semantic_results = self._semantic_search(query.text, query.filters)
            all_results.extend([(result, "semantic") for result in semantic_results])
        
        # 3. TF-IDF search  
        if self.tfidf_vectorizer and self.tfidf_matrix is not None:
            tfidf_results = self._tfidf_search(query.text, query.filters)
            all_results.extend([(result, "tfidf") for result in tfidf_results])
        
        # 4. Fuzzy matching
        if self.config.use_fuzzy_matching and HAS_FUZZY:
            fuzzy_results = self._fuzzy_search(query.text, query.filters)
            all_results.extend([(result, "fuzzy") for result in fuzzy_results])
        
        # 5. Metadata search
        metadata_results = self._metadata_search(query.text, query.filters)
        all_results.extend([(result, "metadata") for result in metadata_results])
        
        # Combine and rank results
        combined_results = self._combine_and_rank_results(all_results, query.text)
        
        # Apply sorting
        if query.sort_by != "relevance":
            combined_results = self._sort_results(combined_results, query.sort_by, query.sort_order)
        
        # Apply pagination
        total_count = len(combined_results)
        paginated_results = combined_results[query.offset:query.offset + query.limit]
        
        # Generate facets
        facets = self._generate_facets(combined_results, query.facets)
        
        # Generate search suggestions
        suggestions = self._generate_suggestions(query.text, combined_results)
        
        query_time = int((time.time() - start_time) * 1000)
        
        response = SearchResponse(
            results=paginated_results,
            total_count=total_count,
            facets=facets,
            query_time_ms=query_time,
            suggestions=suggestions
        )
        
        # Cache the result
        if self.config.enable_cache:
            self._cache_result(cache_key, response)
        
        return response
    
    def _exact_search(self, query_text: str, filters: Dict[str, Any]) -> List[SearchResult]:
        """Perform exact text matching search."""
        results = []
        query_lower = query_text.lower()
        
        for doc in self.documents:
            if not self._matches_filters(doc, filters):
                continue
            
            score = 0.0
            highlighted = {}
            
            # Check title
            if doc.get('title') and query_lower in doc['title'].lower():
                score += 2.0 * self.config.boost_title_matches
                highlighted['title'] = self._highlight_text(doc['title'], query_text)
            
            # Check author
            if doc.get('author') and query_lower in doc['author'].lower():
                score += 1.5 * self.config.boost_author_matches
                highlighted['author'] = self._highlight_text(doc['author'], query_text)
            
            # Check description
            if doc.get('description') and query_lower in doc['description'].lower():
                score += 1.0
                highlighted['description'] = self._highlight_text(doc['description'], query_text)
            
            # Check content
            if doc.get('content') and query_lower in doc['content'].lower():
                score += 0.8
                highlighted['content'] = self._highlight_text(doc['content'][:500], query_text)
            
            # Check categories and subjects
            for field in ['categories', 'subjects', 'keywords']:
                if doc.get(field):
                    for item in doc[field]:
                        if query_lower in item.lower():
                            score += 0.5
                            break
            
            if score > 0:
                results.append(SearchResult(
                    id=doc.get('id', ''),
                    title=doc.get('title', ''),
                    author=doc.get('author', ''),
                    content=doc.get('description', '')[:200],
                    metadata=doc.get('metadata', {}),
                    relevance_score=score,
                    match_type="exact",
                    highlighted_fields=highlighted
                ))
        
        return results
    
    def _semantic_search(self, query_text: str, filters: Dict[str, Any]) -> List[SearchResult]:
        """Perform semantic similarity search using embeddings."""
        if not self.semantic_model or self.document_embeddings is None:
            return []
        
        try:
            # Encode query
            query_embedding = self.semantic_model.encode([query_text])
            
            # Calculate similarities
            similarities = cosine_similarity(query_embedding, self.document_embeddings)[0]
            
            results = []
            for i, similarity in enumerate(similarities):
                if similarity < self.config.similarity_threshold:
                    continue
                
                doc = self.documents[i]
                if not self._matches_filters(doc, filters):
                    continue
                
                results.append(SearchResult(
                    id=doc.get('id', ''),
                    title=doc.get('title', ''),
                    author=doc.get('author', ''),
                    content=doc.get('description', '')[:200],
                    metadata=doc.get('metadata', {}),
                    relevance_score=float(similarity),
                    match_type="semantic"
                ))
            
            return results
            
        except Exception as e:
            logger.warning(f"Semantic search failed: {e}")
            return []
    
    def _tfidf_search(self, query_text: str, filters: Dict[str, Any]) -> List[SearchResult]:
        """Perform TF-IDF based search."""
        if not self.tfidf_vectorizer or self.tfidf_matrix is None:
            return []
        
        try:
            # Transform query
            query_vector = self.tfidf_vectorizer.transform([query_text])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0]
            
            results = []
            for i, similarity in enumerate(similarities):
                if similarity < 0.1:  # Lower threshold for TF-IDF
                    continue
                
                doc = self.documents[i]
                if not self._matches_filters(doc, filters):
                    continue
                
                results.append(SearchResult(
                    id=doc.get('id', ''),
                    title=doc.get('title', ''),
                    author=doc.get('author', ''),
                    content=doc.get('description', '')[:200],
                    metadata=doc.get('metadata', {}),
                    relevance_score=float(similarity),
                    match_type="tfidf"
                ))
            
            return results
            
        except Exception as e:
            logger.warning(f"TF-IDF search failed: {e}")
            return []
    
    def _fuzzy_search(self, query_text: str, filters: Dict[str, Any]) -> List[SearchResult]:
        """Perform fuzzy string matching search."""
        if not HAS_FUZZY:
            return []
        
        results = []
        query_words = query_text.lower().split()
        
        for doc in self.documents:
            if not self._matches_filters(doc, filters):
                continue
            
            max_score = 0.0
            
            # Check against title and author primarily
            for field in ['title', 'author']:
                if not doc.get(field):
                    continue
                
                field_text = doc[field].lower()
                field_words = field_text.split()
                
                for query_word in query_words:
                    for field_word in field_words:
                        if len(query_word) < 3 or len(field_word) < 3:
                            continue
                        
                        similarity = Levenshtein.ratio(query_word, field_word)
                        if similarity >= self.config.fuzzy_threshold:
                            boost = self.config.boost_title_matches if field == 'title' else self.config.boost_author_matches
                            score = similarity * boost
                            max_score = max(max_score, score)
            
            if max_score > 0:
                results.append(SearchResult(
                    id=doc.get('id', ''),
                    title=doc.get('title', ''),
                    author=doc.get('author', ''),
                    content=doc.get('description', '')[:200],
                    metadata=doc.get('metadata', {}),
                    relevance_score=max_score,
                    match_type="fuzzy"
                ))
        
        return results
    
    def _metadata_search(self, query_text: str, filters: Dict[str, Any]) -> List[SearchResult]:
        """Search within metadata fields."""
        results = []
        query_lower = query_text.lower()
        
        for doc in self.documents:
            if not self._matches_filters(doc, filters):
                continue
            
            score = 0.0
            
            # Search in categories
            if doc.get('categories'):
                for category in doc['categories']:
                    if query_lower in category.lower():
                        score += 0.8
            
            # Search in subjects
            if doc.get('subjects'):
                for subject in doc['subjects']:
                    if query_lower in subject.lower():
                        score += 0.6
            
            # Search in keywords
            if doc.get('keywords'):
                for keyword in doc['keywords']:
                    if query_lower in keyword.lower():
                        score += 0.4
            
            # Search in metadata
            if doc.get('metadata'):
                metadata_text = json.dumps(doc['metadata']).lower()
                if query_lower in metadata_text:
                    score += 0.3
            
            if score > 0:
                results.append(SearchResult(
                    id=doc.get('id', ''),
                    title=doc.get('title', ''),
                    author=doc.get('author', ''),
                    content=doc.get('description', '')[:200],
                    metadata=doc.get('metadata', {}),
                    relevance_score=score,
                    match_type="metadata"
                ))
        
        return results
    
    def _combine_and_rank_results(self, all_results: List[Tuple[SearchResult, str]], query_text: str) -> List[SearchResult]:
        """Combine results from different search strategies and rank them."""
        # Group results by document ID
        result_groups = {}
        
        for result, search_type in all_results:
            doc_id = result.id
            if doc_id not in result_groups:
                result_groups[doc_id] = []
            result_groups[doc_id].append((result, search_type))
        
        # Combine scores for each document
        final_results = []
        
        for doc_id, group in result_groups.items():
            # Use the highest scoring result as base
            best_result = max(group, key=lambda x: x[0].relevance_score)[0]
            
            # Combine scores from different search types
            combined_score = 0.0
            match_types = []
            
            for result, search_type in group:
                match_types.append(search_type)
                
                # Weight different search types
                if search_type == "exact":
                    combined_score += result.relevance_score * 1.0
                elif search_type == "semantic":
                    combined_score += result.relevance_score * 0.8
                elif search_type == "tfidf":
                    combined_score += result.relevance_score * 0.6
                elif search_type == "fuzzy":
                    combined_score += result.relevance_score * 0.4
                elif search_type == "metadata":
                    combined_score += result.relevance_score * 0.3
            
            # Apply boosting for exact matches
            if "exact" in match_types and self.config.boost_exact_matches:
                combined_score *= 1.5
            
            best_result.relevance_score = combined_score
            best_result.match_type = "/".join(sorted(set(match_types)))
            
            final_results.append(best_result)
        
        # Sort by relevance score
        final_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Limit results
        return final_results[:self.config.max_results]
    
    def _matches_filters(self, doc: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if document matches the given filters."""
        if not filters:
            return True
        
        for field, filter_value in filters.items():
            doc_value = doc.get(field)
            
            if doc_value is None:
                return False
            
            if isinstance(filter_value, list):
                # OR condition for list values
                if isinstance(doc_value, list):
                    if not any(item in filter_value for item in doc_value):
                        return False
                else:
                    if doc_value not in filter_value:
                        return False
            elif isinstance(filter_value, dict):
                # Range or special filters
                if 'min' in filter_value and doc_value < filter_value['min']:
                    return False
                if 'max' in filter_value and doc_value > filter_value['max']:
                    return False
            else:
                # Exact match
                if isinstance(doc_value, list):
                    if filter_value not in doc_value:
                        return False
                else:
                    if doc_value != filter_value:
                        return False
        
        return True
    
    def _sort_results(self, results: List[SearchResult], sort_by: str, sort_order: str) -> List[SearchResult]:
        """Sort results by specified field."""
        reverse = sort_order.lower() == "desc"
        
        if sort_by == "title":
            results.sort(key=lambda x: x.title.lower(), reverse=reverse)
        elif sort_by == "author":
            results.sort(key=lambda x: x.author.lower(), reverse=reverse)
        elif sort_by == "relevance":
            results.sort(key=lambda x: x.relevance_score, reverse=reverse)
        # Add more sort fields as needed
        
        return results
    
    def _generate_facets(self, results: List[SearchResult], requested_facets: List[str]) -> List[SearchFacet]:
        """Generate facets for search results."""
        facets = []
        
        if not requested_facets:
            return facets
        
        # Count values for each facet
        facet_counts = {}
        
        for result in results:
            doc = next((doc for doc in self.documents if doc.get('id') == result.id), None)
            if not doc:
                continue
            
            for facet_name in requested_facets:
                if facet_name not in facet_counts:
                    facet_counts[facet_name] = {}
                
                values = doc.get(facet_name, [])
                if not isinstance(values, list):
                    values = [values]
                
                for value in values:
                    if value:
                        str_value = str(value)
                        facet_counts[facet_name][str_value] = facet_counts[facet_name].get(str_value, 0) + 1
        
        # Convert to facet objects
        for facet_name, counts in facet_counts.items():
            sorted_values = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            facets.append(SearchFacet(
                name=facet_name,
                values=sorted_values[:20]  # Limit to top 20 values
            ))
        
        return facets
    
    def _generate_suggestions(self, query_text: str, results: List[SearchResult]) -> List[str]:
        """Generate search suggestions based on query and results."""
        suggestions = []
        
        # Extract common terms from top results
        top_results = results[:10]
        term_counts = {}
        
        for result in top_results:
            doc = next((doc for doc in self.documents if doc.get('id') == result.id), None)
            if not doc:
                continue
            
            # Extract terms from categories, subjects, keywords
            for field in ['categories', 'subjects', 'keywords']:
                if doc.get(field):
                    for term in doc[field]:
                        if len(term) > 2 and term.lower() != query_text.lower():
                            term_counts[term] = term_counts.get(term, 0) + 1
        
        # Sort by frequency and take top suggestions
        sorted_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)
        suggestions = [term for term, count in sorted_terms[:5]]
        
        return suggestions
    
    def _highlight_text(self, text: str, query: str) -> str:
        """Add highlighting markup to text."""
        if not text or not query:
            return text
        
        # Simple highlighting - in production would use more sophisticated highlighting
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        return pattern.sub(f'<mark>{query}</mark>', text)
    
    def _get_cache_key(self, query: SearchQuery) -> str:
        """Generate cache key for query."""
        return f"{query.text}:{json.dumps(query.filters, sort_keys=True)}:{query.sort_by}:{query.sort_order}"
    
    def _cache_result(self, key: str, result: SearchResponse) -> None:
        """Cache search result."""
        if len(self.search_cache) >= self.config.max_cache_size:
            # Remove oldest entry
            oldest_key = min(self.search_cache.keys(), key=lambda k: self.search_cache[k][1])
            del self.search_cache[oldest_key]
        
        self.search_cache[key] = (result, datetime.now())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get search engine statistics."""
        return {
            "total_documents": len(self.documents),
            "has_semantic_model": self.semantic_model is not None,
            "has_tfidf_index": self.tfidf_matrix is not None,
            "cache_size": len(self.search_cache),
            "ml_libraries_available": HAS_ML_LIBS,
            "fuzzy_matching_available": HAS_FUZZY
        }


def main():
    """Demo of semantic search engine."""
    # Sample documents for testing
    sample_docs = [
        {
            "id": "doc1",
            "title": "Introduction to Machine Learning",
            "author": "John Smith",
            "description": "A comprehensive guide to machine learning algorithms and techniques.",
            "categories": ["Technology", "AI", "Education"],
            "subjects": ["Machine Learning", "Algorithms", "Data Science"],
            "keywords": ["ML", "neural networks", "classification", "regression"],
            "metadata": {"year": 2023, "pages": 350, "level": "beginner"}
        },
        {
            "id": "doc2", 
            "title": "Advanced Neural Networks",
            "author": "Jane Doe",
            "description": "Deep dive into neural network architectures and optimization.",
            "categories": ["Technology", "AI", "Research"],
            "subjects": ["Neural Networks", "Deep Learning", "Optimization"],
            "keywords": ["deep learning", "backpropagation", "CNN", "RNN"],
            "metadata": {"year": 2023, "pages": 450, "level": "advanced"}
        },
        {
            "id": "doc3",
            "title": "Data Science Fundamentals", 
            "author": "Bob Johnson",
            "description": "Essential concepts and tools for data science practitioners.",
            "categories": ["Technology", "Analytics", "Education"],
            "subjects": ["Data Science", "Statistics", "Programming"],
            "keywords": ["python", "statistics", "visualization", "pandas"],
            "metadata": {"year": 2022, "pages": 280, "level": "intermediate"}
        }
    ]
    
    # Initialize search engine
    search_engine = SemanticSearchEngine()
    search_engine.index_documents(sample_docs)
    
    # Test searches
    print("=== Semantic Search Engine Demo ===\n")
    
    # Test 1: Simple text search
    print("1. Simple search for 'machine learning':")
    results = search_engine.search("machine learning")
    for result in results.results:
        print(f"  - {result.title} by {result.author} (score: {result.relevance_score:.2f}, type: {result.match_type})")
    print(f"  Query time: {results.query_time_ms}ms\n")
    
    # Test 2: Fuzzy search
    print("2. Fuzzy search for 'machne lerning' (with typos):")
    results = search_engine.search("machne lerning")
    for result in results.results:
        print(f"  - {result.title} by {result.author} (score: {result.relevance_score:.2f}, type: {result.match_type})")
    print(f"  Query time: {results.query_time_ms}ms\n")
    
    # Test 3: Filtered search
    print("3. Search with filters (category: Technology, level: beginner):")
    query = SearchQuery(
        text="learning",
        filters={"categories": ["Technology"], "metadata": {"level": "beginner"}}
    )
    results = search_engine.search(query)
    for result in results.results:
        print(f"  - {result.title} by {result.author} (score: {result.relevance_score:.2f})")
    print(f"  Query time: {results.query_time_ms}ms\n")
    
    # Test 4: Faceted search
    print("4. Search with facets:")
    query = SearchQuery(
        text="data",
        facets=["categories", "subjects"]
    )
    results = search_engine.search(query)
    print(f"  Found {results.total_count} results")
    for facet in results.facets:
        print(f"  Facet {facet.name}:")
        for value, count in facet.values[:3]:
            print(f"    - {value}: {count}")
    print(f"  Query time: {results.query_time_ms}ms\n")
    
    # Test 5: Search statistics
    print("5. Search engine statistics:")
    stats = search_engine.get_statistics()
    for key, value in stats.items():
        print(f"  - {key}: {value}")


if __name__ == "__main__":
    main()
