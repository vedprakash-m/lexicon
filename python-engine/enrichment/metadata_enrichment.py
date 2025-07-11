"""
Metadata Enrichment Engine for Lexicon.

This module provides comprehensive book metadata enrichment capabilities using
external APIs like Google Books, OpenLibrary, and custom enrichment sources.
"""

import asyncio
import aiohttp
import json
import logging
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from urllib.parse import quote

# Configure logging
logger = logging.getLogger(__name__)


class MetadataSource(Enum):
    """Available metadata sources."""
    GOOGLE_BOOKS = "google_books"
    OPENLIBRARY = "openlibrary"
    WORLDCAT = "worldcat"
    GOODREADS = "goodreads"
    MANUAL = "manual"


class EnrichmentStatus(Enum):
    """Status of metadata enrichment."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class BookIdentifier:
    """Book identification information."""
    isbn_10: Optional[str] = None
    isbn_13: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    google_books_id: Optional[str] = None
    openlibrary_id: Optional[str] = None
    worldcat_oclc: Optional[str] = None
    
    def get_search_terms(self) -> List[str]:
        """Get search terms for metadata lookup."""
        terms = []
        if self.isbn_13:
            terms.append(f"isbn:{self.isbn_13}")
        if self.isbn_10:
            terms.append(f"isbn:{self.isbn_10}")
        if self.title and self.author:
            terms.append(f'intitle:"{self.title}" inauthor:"{self.author}"')
        elif self.title:
            terms.append(f'intitle:"{self.title}"')
        return terms


@dataclass
class AuthorInfo:
    """Author information."""
    name: str
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    biography: Optional[str] = None
    photo_url: Optional[str] = None
    wikipedia_url: Optional[str] = None
    website_url: Optional[str] = None
    nationality: Optional[str] = None
    other_works: List[str] = None
    
    def __post_init__(self):
        if self.other_works is None:
            self.other_works = []
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        if not isinstance(other, AuthorInfo):
            return False
        return self.name == other.name


@dataclass
class PublisherInfo:
    """Publisher information."""
    name: str
    founded_year: Optional[int] = None
    location: Optional[str] = None
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None


@dataclass
class EnrichedMetadata:
    """Enriched book metadata."""
    # Basic identification
    title: str
    subtitle: Optional[str] = None
    authors: List[AuthorInfo] = None
    publisher: Optional[PublisherInfo] = None
    published_date: Optional[str] = None
    
    # Classification
    categories: List[str] = None
    subjects: List[str] = None
    genre: Optional[str] = None
    language: Optional[str] = None
    country_of_publication: Optional[str] = None
    
    # Physical properties
    page_count: Optional[int] = None
    dimensions: Optional[Dict[str, float]] = None  # width, height, thickness in cm
    weight_grams: Optional[float] = None
    format: Optional[str] = None  # hardcover, paperback, ebook, etc.
    
    # Content description
    description: Optional[str] = None
    summary: Optional[str] = None
    table_of_contents: List[str] = None
    
    # Ratings and reviews
    average_rating: Optional[float] = None
    ratings_count: Optional[int] = None
    review_count: Optional[int] = None
    
    # Visual assets
    cover_image_url: Optional[str] = None
    cover_image_thumbnail_url: Optional[str] = None
    cover_image_small_url: Optional[str] = None
    
    # Related works
    series: Optional[str] = None
    series_number: Optional[int] = None
    related_books: List[str] = None
    translations: List[Dict[str, str]] = None
    editions: List[Dict[str, str]] = None
    
    # Technical metadata
    isbn_10: Optional[str] = None
    isbn_13: Optional[str] = None
    oclc_number: Optional[str] = None
    lccn: Optional[str] = None
    dewey_decimal: Optional[str] = None
    lc_classification: Optional[str] = None
    
    # Enrichment tracking
    enrichment_sources: List[MetadataSource] = None
    enrichment_timestamp: Optional[datetime] = None
    enrichment_quality_score: Optional[float] = None
    enrichment_status: EnrichmentStatus = EnrichmentStatus.PENDING
    
    def __post_init__(self):
        """Initialize lists if None."""
        if self.authors is None:
            self.authors = []
        if self.categories is None:
            self.categories = []
        if self.subjects is None:
            self.subjects = []
        if self.table_of_contents is None:
            self.table_of_contents = []
        if self.related_books is None:
            self.related_books = []
        if self.translations is None:
            self.translations = []
        if self.editions is None:
            self.editions = []
        if self.enrichment_sources is None:
            self.enrichment_sources = []


class GoogleBooksEnricher:
    """Google Books API enrichment provider."""
    
    def __init__(self, api_key: Optional[str] = None, rate_limit: float = 1.0):
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.base_url = "https://www.googleapis.com/books/v1/volumes"
    
    async def _rate_limit(self):
        """Enforce rate limiting."""
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.rate_limit:
            await asyncio.sleep(self.rate_limit - time_since_last)
        self.last_request_time = time.time()
    
    async def search_book(self, identifier: BookIdentifier) -> List[Dict[str, Any]]:
        """Search for book using Google Books API."""
        await self._rate_limit()
        
        search_terms = identifier.get_search_terms()
        if not search_terms:
            return []
        
        async with aiohttp.ClientSession() as session:
            for term in search_terms:
                try:
                    params = {
                        'q': term,
                        'maxResults': 5
                    }
                    if self.api_key:
                        params['key'] = self.api_key
                    
                    async with session.get(self.base_url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('items'):
                                return data['items']
                except Exception as e:
                    logger.warning(f"Google Books search failed for '{term}': {str(e)}")
                    continue
        
        return []
    
    def _extract_metadata(self, volume_info: Dict[str, Any]) -> EnrichedMetadata:
        """Extract metadata from Google Books volume info."""
        metadata = EnrichedMetadata(
            title=volume_info.get('title', ''),
            subtitle=volume_info.get('subtitle'),
            description=volume_info.get('description'),
            published_date=volume_info.get('publishedDate'),
            page_count=volume_info.get('pageCount'),
            language=volume_info.get('language'),
            average_rating=volume_info.get('averageRating'),
            ratings_count=volume_info.get('ratingsCount'),
            enrichment_sources=[MetadataSource.GOOGLE_BOOKS],
            enrichment_timestamp=datetime.now()
        )
        
        # Authors
        if 'authors' in volume_info:
            metadata.authors = [
                AuthorInfo(name=author) for author in volume_info['authors']
            ]
        
        # Publisher
        if 'publisher' in volume_info:
            metadata.publisher = PublisherInfo(name=volume_info['publisher'])
        
        # Categories
        if 'categories' in volume_info:
            metadata.categories = volume_info['categories']
        
        # Industry identifiers (ISBN)
        if 'industryIdentifiers' in volume_info:
            for identifier in volume_info['industryIdentifiers']:
                if identifier['type'] == 'ISBN_10':
                    metadata.isbn_10 = identifier['identifier']
                elif identifier['type'] == 'ISBN_13':
                    metadata.isbn_13 = identifier['identifier']
        
        # Images
        if 'imageLinks' in volume_info:
            image_links = volume_info['imageLinks']
            metadata.cover_image_thumbnail_url = image_links.get('thumbnail')
            metadata.cover_image_small_url = image_links.get('small')
            # Try to get higher resolution image
            if 'thumbnail' in image_links:
                metadata.cover_image_url = image_links['thumbnail'].replace('&zoom=1', '&zoom=0')
        
        return metadata
    
    async def enrich(self, identifier: BookIdentifier) -> Optional[EnrichedMetadata]:
        """Enrich book metadata using Google Books."""
        try:
            volumes = await self.search_book(identifier)
            if volumes:
                # Take the first (best) match
                volume = volumes[0]
                if 'volumeInfo' in volume:
                    return self._extract_metadata(volume['volumeInfo'])
        except Exception as e:
            logger.error(f"Google Books enrichment failed: {str(e)}")
        
        return None


class OpenLibraryEnricher:
    """OpenLibrary API enrichment provider."""
    
    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.base_url = "https://openlibrary.org"
    
    async def _rate_limit(self):
        """Enforce rate limiting."""
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.rate_limit:
            await asyncio.sleep(self.rate_limit - time_since_last)
        self.last_request_time = time.time()
    
    async def search_book(self, identifier: BookIdentifier) -> List[Dict[str, Any]]:
        """Search for book using OpenLibrary API."""
        await self._rate_limit()
        
        async with aiohttp.ClientSession() as session:
            # Try ISBN search first
            if identifier.isbn_13 or identifier.isbn_10:
                isbn = identifier.isbn_13 or identifier.isbn_10
                try:
                    url = f"{self.base_url}/isbn/{isbn}.json"
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            return [data]
                except Exception as e:
                    logger.warning(f"OpenLibrary ISBN search failed: {str(e)}")
            
            # Fallback to general search
            if identifier.title:
                try:
                    params = {
                        'title': identifier.title,
                        'limit': 5
                    }
                    if identifier.author:
                        params['author'] = identifier.author
                    
                    url = f"{self.base_url}/search.json"
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('docs'):
                                return data['docs']
                except Exception as e:
                    logger.warning(f"OpenLibrary search failed: {str(e)}")
        
        return []
    
    def _extract_metadata(self, book_data: Dict[str, Any]) -> EnrichedMetadata:
        """Extract metadata from OpenLibrary book data."""
        metadata = EnrichedMetadata(
            title=book_data.get('title', ''),
            subtitle=book_data.get('subtitle'),
            published_date=str(book_data.get('publish_date', '')),
            page_count=book_data.get('number_of_pages'),
            enrichment_sources=[MetadataSource.OPENLIBRARY],
            enrichment_timestamp=datetime.now()
        )
        
        # Authors
        if 'authors' in book_data:
            author_names = []
            for author in book_data['authors']:
                if isinstance(author, dict) and 'name' in author:
                    author_names.append(author['name'])
                elif isinstance(author, str):
                    author_names.append(author)
            metadata.authors = [AuthorInfo(name=name) for name in author_names]
        elif 'author_name' in book_data:
            metadata.authors = [AuthorInfo(name=name) for name in book_data['author_name']]
        
        # Publisher
        if 'publishers' in book_data and book_data['publishers']:
            metadata.publisher = PublisherInfo(name=book_data['publishers'][0])
        elif 'publisher' in book_data:
            metadata.publisher = PublisherInfo(name=book_data['publisher'])
        
        # Subjects/Categories
        if 'subjects' in book_data:
            metadata.subjects = book_data['subjects'][:10]  # Limit to avoid too many
        
        # ISBN
        if 'isbn_13' in book_data and book_data['isbn_13']:
            metadata.isbn_13 = book_data['isbn_13'][0]
        if 'isbn_10' in book_data and book_data['isbn_10']:
            metadata.isbn_10 = book_data['isbn_10'][0]
        
        # Cover image
        if 'cover_i' in book_data:
            cover_id = book_data['cover_i']
            metadata.cover_image_thumbnail_url = f"https://covers.openlibrary.org/b/id/{cover_id}-S.jpg"
            metadata.cover_image_small_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
            metadata.cover_image_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
        
        return metadata
    
    async def enrich(self, identifier: BookIdentifier) -> Optional[EnrichedMetadata]:
        """Enrich book metadata using OpenLibrary."""
        try:
            books = await self.search_book(identifier)
            if books:
                return self._extract_metadata(books[0])
        except Exception as e:
            logger.error(f"OpenLibrary enrichment failed: {str(e)}")
        
        return None


class MetadataEnrichmentEngine:
    """Main metadata enrichment engine that coordinates multiple sources."""
    
    def __init__(self, google_books_api_key: Optional[str] = None):
        self.enrichers = {
            MetadataSource.GOOGLE_BOOKS: GoogleBooksEnricher(api_key=google_books_api_key),
            MetadataSource.OPENLIBRARY: OpenLibraryEnricher()
        }
        self.cache = {}
        self.cache_ttl = 24 * 60 * 60  # 24 hours
    
    def _generate_cache_key(self, identifier: BookIdentifier) -> str:
        """Generate cache key for book identifier."""
        parts = []
        if identifier.isbn_13:
            parts.append(f"isbn13:{identifier.isbn_13}")
        elif identifier.isbn_10:
            parts.append(f"isbn10:{identifier.isbn_10}")
        elif identifier.title and identifier.author:
            parts.append(f"title:{identifier.title[:50]}:author:{identifier.author[:30]}")
        elif identifier.title:
            parts.append(f"title:{identifier.title[:50]}")
        return "|".join(parts)
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        if 'timestamp' not in cache_entry:
            return False
        return (time.time() - cache_entry['timestamp']) < self.cache_ttl
    
    def _merge_metadata(self, *metadata_list: EnrichedMetadata) -> EnrichedMetadata:
        """Merge metadata from multiple sources, preferring non-empty values."""
        if not metadata_list:
            return EnrichedMetadata(title="")
        
        # Start with first metadata as base
        result = EnrichedMetadata(title="")
        for field_name in result.__dataclass_fields__:
            values = []
            for metadata in metadata_list:
                value = getattr(metadata, field_name, None)
                if value is not None and value != "" and value != []:
                    values.append(value)
            
            if values:
                # For lists, merge them
                if isinstance(values[0], list):
                    merged_list = []
                    for value_list in values:
                        merged_list.extend(value_list)
                    # Remove duplicates while preserving order
                    setattr(result, field_name, list(dict.fromkeys(merged_list)))
                # For other types, take first non-empty value
                else:
                    setattr(result, field_name, values[0])
        
        # Merge enrichment sources
        all_sources = []
        for metadata in metadata_list:
            if metadata.enrichment_sources:
                all_sources.extend(metadata.enrichment_sources)
        result.enrichment_sources = list(set(all_sources))
        result.enrichment_timestamp = datetime.now()
        
        # Calculate quality score based on completeness
        result.enrichment_quality_score = self._calculate_quality_score(result)
        result.enrichment_status = EnrichmentStatus.COMPLETED
        
        return result
    
    def _calculate_quality_score(self, metadata: EnrichedMetadata) -> float:
        """Calculate quality score based on metadata completeness."""
        score = 0.0
        max_score = 0.0
        
        # Essential fields (higher weight)
        essential_fields = [
            ('title', 10),
            ('authors', 8),
            ('publisher', 6),
            ('published_date', 6),
            ('description', 8)
        ]
        
        # Important fields (medium weight)
        important_fields = [
            ('categories', 4),
            ('isbn_13', 4),
            ('page_count', 3),
            ('cover_image_url', 5),
            ('language', 2)
        ]
        
        # Nice-to-have fields (lower weight)
        optional_fields = [
            ('subtitle', 2),
            ('subjects', 3),
            ('average_rating', 2),
            ('table_of_contents', 3),
            ('series', 2)
        ]
        
        all_fields = essential_fields + important_fields + optional_fields
        
        for field_name, weight in all_fields:
            max_score += weight
            value = getattr(metadata, field_name, None)
            if value is not None and value != "" and value != []:
                score += weight
        
        return min(1.0, score / max_score) if max_score > 0 else 0.0
    
    async def enrich_book(self, identifier: BookIdentifier, sources: Optional[List[MetadataSource]] = None) -> EnrichedMetadata:
        """Enrich book metadata using specified sources."""
        if sources is None:
            sources = [MetadataSource.GOOGLE_BOOKS, MetadataSource.OPENLIBRARY]
        
        # Check cache first
        cache_key = self._generate_cache_key(identifier)
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            logger.info(f"Using cached metadata for: {cache_key}")
            return EnrichedMetadata(**self.cache[cache_key]['metadata'])
        
        # Gather metadata from all requested sources
        metadata_results = []
        
        for source in sources:
            if source in self.enrichers:
                try:
                    logger.info(f"Enriching from {source.value}")
                    enricher = self.enrichers[source]
                    metadata = await enricher.enrich(identifier)
                    if metadata:
                        metadata_results.append(metadata)
                        logger.info(f"Successfully enriched from {source.value}")
                    else:
                        logger.warning(f"No metadata found from {source.value}")
                except Exception as e:
                    logger.error(f"Enrichment from {source.value} failed: {str(e)}")
        
        # Merge results
        if metadata_results:
            merged_metadata = self._merge_metadata(*metadata_results)
            
            # Cache the result
            self.cache[cache_key] = {
                'metadata': asdict(merged_metadata),
                'timestamp': time.time()
            }
            
            logger.info(f"Enrichment completed with quality score: {merged_metadata.enrichment_quality_score:.2f}")
            return merged_metadata
        
        # Return minimal metadata if no enrichment succeeded
        logger.warning("No metadata could be enriched")
        return EnrichedMetadata(
            title=identifier.title or "Unknown Title",
            enrichment_status=EnrichmentStatus.FAILED,
            enrichment_timestamp=datetime.now(),
            enrichment_quality_score=0.0
        )
    
    async def batch_enrich(self, identifiers: List[BookIdentifier], 
                          sources: Optional[List[MetadataSource]] = None,
                          batch_size: int = 5) -> List[EnrichedMetadata]:
        """Enrich multiple books in batches."""
        results = []
        
        for i in range(0, len(identifiers), batch_size):
            batch = identifiers[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} books)")
            
            # Process batch concurrently
            tasks = [self.enrich_book(identifier, sources) for identifier in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch enrichment error: {str(result)}")
                    results.append(EnrichedMetadata(
                        title="Error",
                        enrichment_status=EnrichmentStatus.FAILED,
                        enrichment_timestamp=datetime.now()
                    ))
                else:
                    results.append(result)
            
            # Small delay between batches to be respectful to APIs
            if i + batch_size < len(identifiers):
                await asyncio.sleep(2)
        
        return results
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.cache)
        valid_entries = sum(1 for entry in self.cache.values() if self._is_cache_valid(entry))
        
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'expired_entries': total_entries - valid_entries,
            'cache_hit_rate': valid_entries / total_entries if total_entries > 0 else 0.0
        }
    
    def clear_cache(self):
        """Clear all cached metadata."""
        self.cache.clear()
        logger.info("Metadata cache cleared")


# Utility functions for common use cases
async def enrich_book_metadata(title: str, author: Optional[str] = None, 
                             isbn: Optional[str] = None,
                             google_books_api_key: Optional[str] = None) -> EnrichedMetadata:
    """Convenience function to enrich a single book."""
    identifier = BookIdentifier(
        title=title,
        author=author,
        isbn_13=isbn if isbn and len(isbn) == 13 else None,
        isbn_10=isbn if isbn and len(isbn) == 10 else None
    )
    
    engine = MetadataEnrichmentEngine(google_books_api_key=google_books_api_key)
    return await engine.enrich_book(identifier)


async def batch_enrich_from_csv(csv_path: str, 
                               google_books_api_key: Optional[str] = None) -> List[EnrichedMetadata]:
    """Enrich books from a CSV file with columns: title, author, isbn."""
    import csv
    
    identifiers = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            identifier = BookIdentifier(
                title=row.get('title'),
                author=row.get('author'),
                isbn_13=row.get('isbn') if row.get('isbn') and len(row.get('isbn', '')) == 13 else None,
                isbn_10=row.get('isbn') if row.get('isbn') and len(row.get('isbn', '')) == 10 else None
            )
            identifiers.append(identifier)
    
    engine = MetadataEnrichmentEngine(google_books_api_key=google_books_api_key)
    return await engine.batch_enrich(identifiers)
