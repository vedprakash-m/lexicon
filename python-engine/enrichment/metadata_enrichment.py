import requests
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import hashlib

@dataclass
class BookMetadata:
    title: str
    authors: List[str]
    isbn: Optional[str]
    publisher: Optional[str]
    published_date: Optional[str]
    description: Optional[str]
    categories: List[str]
    language: str
    page_count: Optional[int]
    cover_url: Optional[str]
    rating: Optional[float]
    ratings_count: Optional[int]
    source: str
    confidence: float

class MetadataEnricher:
    def __init__(self, google_books_api_key: Optional[str] = None):
        self.google_books_api_key = google_books_api_key
        self.logger = logging.getLogger(__name__)
        self.rate_limit_delay = 1.0  # seconds between API calls
        self.last_request_time = 0
        
        # Cache for API responses
        self.cache = {}
        
    def enrich_metadata(self, title: str, author: Optional[str] = None, isbn: Optional[str] = None) -> List[BookMetadata]:
        """Enrich metadata using multiple sources"""
        results = []
        
        # Try Google Books API first
        if self.google_books_api_key:
            google_results = self._search_google_books(title, author, isbn)
            results.extend(google_results)
            
        # Try OpenLibrary API
        openlibrary_results = self._search_openlibrary(title, author, isbn)
        results.extend(openlibrary_results)
        
        # Deduplicate and rank results
        deduplicated = self._deduplicate_results(results)
        ranked = self._rank_results(deduplicated, title, author)
        
        return ranked[:5]  # Return top 5 results
        
    def _search_google_books(self, title: str, author: Optional[str] = None, isbn: Optional[str] = None) -> List[BookMetadata]:
        """Search Google Books API"""
        self._respect_rate_limit()
        
        # Build search query
        query_parts = []
        if isbn:
            query_parts.append(f"isbn:{isbn}")
        else:
            query_parts.append(f'intitle:"{title}"')
            if author:
                query_parts.append(f'inauthor:"{author}"')
                
        query = "+".join(query_parts)
        
        # Check cache
        cache_key = hashlib.md5(f"google_books_{query}".encode()).hexdigest()
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        url = "https://www.googleapis.com/books/v1/volumes"
        params = {
            'q': query,
            'maxResults': 10,
            'key': self.google_books_api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get('items', []):
                volume_info = item.get('volumeInfo', {})
                
                # Extract metadata
                metadata = BookMetadata(
                    title=volume_info.get('title', ''),
                    authors=volume_info.get('authors', []),
                    isbn=self._extract_isbn(volume_info.get('industryIdentifiers', [])),
                    publisher=volume_info.get('publisher'),
                    published_date=volume_info.get('publishedDate'),
                    description=volume_info.get('description'),
                    categories=volume_info.get('categories', []),
                    language=volume_info.get('language', 'en'),
                    page_count=volume_info.get('pageCount'),
                    cover_url=self._extract_cover_url(volume_info.get('imageLinks', {})),
                    rating=volume_info.get('averageRating'),
                    ratings_count=volume_info.get('ratingsCount'),
                    source='google_books',
                    confidence=self._calculate_confidence(volume_info, title, author)
                )
                
                results.append(metadata)
                
            # Cache results
            self.cache[cache_key] = results
            return results
            
        except Exception as e:
            self.logger.error(f"Google Books API error: {e}")
            return []
            
    def _search_openlibrary(self, title: str, author: Optional[str] = None, isbn: Optional[str] = None) -> List[BookMetadata]:
        """Search OpenLibrary API"""
        self._respect_rate_limit()
        
        # Build search query
        if isbn:
            url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
        else:
            # Use search API
            params = {'title': title}
            if author:
                params['author'] = author
            params['limit'] = 10
            
            url = "https://openlibrary.org/search.json"
            
        # Check cache
        cache_key = hashlib.md5(f"openlibrary_{url}_{json.dumps(params if 'params' in locals() else {})}".encode()).hexdigest()
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        try:
            if isbn:
                response = requests.get(url, timeout=10)
            else:
                response = requests.get(url, params=params, timeout=10)
                
            response.raise_for_status()
            data = response.json()
            
            results = []
            
            if isbn and data:
                # ISBN lookup response
                for key, book_data in data.items():
                    metadata = self._parse_openlibrary_book(book_data, title, author)
                    if metadata:
                        results.append(metadata)
            else:
                # Search response
                for doc in data.get('docs', []):
                    metadata = self._parse_openlibrary_doc(doc, title, author)
                    if metadata:
                        results.append(metadata)
                        
            # Cache results
            self.cache[cache_key] = results
            return results
            
        except Exception as e:
            self.logger.error(f"OpenLibrary API error: {e}")
            return []
            
    def _parse_openlibrary_book(self, book_data: Dict, title: str, author: Optional[str]) -> Optional[BookMetadata]:
        """Parse OpenLibrary book data"""
        try:
            return BookMetadata(
                title=book_data.get('title', ''),
                authors=[a['name'] for a in book_data.get('authors', [])],
                isbn=self._extract_isbn_from_identifiers(book_data.get('identifiers', {})),
                publisher=book_data.get('publishers', [{}])[0].get('name') if book_data.get('publishers') else None,
                published_date=book_data.get('publish_date'),
                description=book_data.get('notes'),
                categories=book_data.get('subjects', []),
                language='en',  # OpenLibrary doesn't always provide language
                page_count=book_data.get('number_of_pages'),
                cover_url=self._get_openlibrary_cover(book_data),
                rating=None,  # OpenLibrary doesn't provide ratings
                ratings_count=None,
                source='openlibrary',
                confidence=self._calculate_confidence(book_data, title, author)
            )
        except Exception as e:
            self.logger.error(f"Error parsing OpenLibrary book data: {e}")
            return None
            
    def _parse_openlibrary_doc(self, doc: Dict, title: str, author: Optional[str]) -> Optional[BookMetadata]:
        """Parse OpenLibrary search document"""
        try:
            return BookMetadata(
                title=doc.get('title', ''),
                authors=doc.get('author_name', []),
                isbn=doc.get('isbn', [None])[0] if doc.get('isbn') else None,
                publisher=doc.get('publisher', [None])[0] if doc.get('publisher') else None,
                published_date=str(doc.get('first_publish_year')) if doc.get('first_publish_year') else None,
                description=None,  # Not available in search results
                categories=doc.get('subject', []),
                language=doc.get('language', ['en'])[0],
                page_count=None,  # Not available in search results
                cover_url=self._get_openlibrary_cover_from_doc(doc),
                rating=None,
                ratings_count=None,
                source='openlibrary',
                confidence=self._calculate_confidence(doc, title, author)
            )
        except Exception as e:
            self.logger.error(f"Error parsing OpenLibrary doc: {e}")
            return None
            
    def _extract_isbn(self, identifiers: List[Dict]) -> Optional[str]:
        """Extract ISBN from Google Books identifiers"""
        for identifier in identifiers:
            if identifier.get('type') in ['ISBN_13', 'ISBN_10']:
                return identifier.get('identifier')
        return None
        
    def _extract_isbn_from_identifiers(self, identifiers: Dict) -> Optional[str]:
        """Extract ISBN from OpenLibrary identifiers"""
        isbn_list = identifiers.get('isbn_13', identifiers.get('isbn_10', []))
        return isbn_list[0] if isbn_list else None
        
    def _extract_cover_url(self, image_links: Dict) -> Optional[str]:
        """Extract cover URL from Google Books image links"""
        for size in ['large', 'medium', 'small', 'thumbnail']:
            if size in image_links:
                return image_links[size]
        return None
        
    def _get_openlibrary_cover(self, book_data: Dict) -> Optional[str]:
        """Get cover URL from OpenLibrary book data"""
        if 'cover' in book_data:
            cover_id = book_data['cover'].get('large') or book_data['cover'].get('medium') or book_data['cover'].get('small')
            if cover_id:
                return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
        return None
        
    def _get_openlibrary_cover_from_doc(self, doc: Dict) -> Optional[str]:
        """Get cover URL from OpenLibrary search doc"""
        if 'cover_i' in doc:
            return f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-L.jpg"
        return None
        
    def _calculate_confidence(self, data: Dict, title: str, author: Optional[str]) -> float:
        """Calculate confidence score for metadata match"""
        confidence = 0.0
        
        # Title matching
        data_title = data.get('title', '').lower()
        if title.lower() in data_title or data_title in title.lower():
            confidence += 0.4
        elif self._fuzzy_match(title.lower(), data_title):
            confidence += 0.2
            
        # Author matching
        if author:
            data_authors = []
            if 'authors' in data:
                if isinstance(data['authors'], list):
                    data_authors = [a.get('name', a) if isinstance(a, dict) else str(a) for a in data['authors']]
            elif 'author_name' in data:
                data_authors = data['author_name']
                
            author_match = any(
                author.lower() in data_author.lower() or data_author.lower() in author.lower()
                for data_author in data_authors
            )
            if author_match:
                confidence += 0.3
                
        # Additional metadata presence
        if data.get('description') or data.get('notes'):
            confidence += 0.1
        if data.get('publisher') or data.get('publishers'):
            confidence += 0.1
        if data.get('publishedDate') or data.get('publish_date') or data.get('first_publish_year'):
            confidence += 0.1
            
        return min(1.0, confidence)
        
    def _fuzzy_match(self, str1: str, str2: str, threshold: float = 0.8) -> bool:
        """Simple fuzzy string matching"""
        if not str1 or not str2:
            return False
            
        # Simple Jaccard similarity
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 or not words2:
            return False
            
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union >= threshold
        
    def _deduplicate_results(self, results: List[BookMetadata]) -> List[BookMetadata]:
        """Remove duplicate results"""
        seen = set()
        deduplicated = []
        
        for result in results:
            # Create a key based on title and first author
            key = (
                result.title.lower().strip(),
                result.authors[0].lower().strip() if result.authors else ''
            )
            
            if key not in seen:
                seen.add(key)
                deduplicated.append(result)
                
        return deduplicated
        
    def _rank_results(self, results: List[BookMetadata], title: str, author: Optional[str]) -> List[BookMetadata]:
        """Rank results by relevance and confidence"""
        def ranking_score(metadata: BookMetadata) -> float:
            score = metadata.confidence
            
            # Boost score for exact title matches
            if metadata.title.lower().strip() == title.lower().strip():
                score += 0.2
                
            # Boost score for exact author matches
            if author and any(a.lower().strip() == author.lower().strip() for a in metadata.authors):
                score += 0.2
                
            # Boost score for more complete metadata
            completeness = sum([
                bool(metadata.description),
                bool(metadata.publisher),
                bool(metadata.published_date),
                bool(metadata.isbn),
                bool(metadata.cover_url),
                bool(metadata.categories),
            ]) / 6
            score += completeness * 0.1
            
            return score
            
        return sorted(results, key=ranking_score, reverse=True)
        
    def _respect_rate_limit(self):
        """Ensure rate limiting between API calls"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
        
    def get_book_details(self, isbn: str) -> Optional[BookMetadata]:
        """Get detailed book information by ISBN"""
        results = self.enrich_metadata("", isbn=isbn)
        return results[0] if results else None
        
    def search_by_title_author(self, title: str, author: str) -> List[BookMetadata]:
        """Search specifically by title and author"""
        return self.enrich_metadata(title, author)
        
    def bulk_enrich(self, books: List[Tuple[str, Optional[str], Optional[str]]]) -> List[List[BookMetadata]]:
        """Bulk enrich multiple books"""
        results = []
        for title, author, isbn in books:
            book_results = self.enrich_metadata(title, author, isbn)
            results.append(book_results)
            # Add delay between bulk requests
            time.sleep(self.rate_limit_delay)
        return results