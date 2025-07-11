"""
Comprehensive tests for the metadata enrichment engine.
"""

import asyncio
import json
import tempfile
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

try:
    from .metadata_enrichment import (
        MetadataSource, EnrichmentStatus, BookIdentifier, AuthorInfo,
        PublisherInfo, EnrichedMetadata, GoogleBooksEnricher, 
        OpenLibraryEnricher, MetadataEnrichmentEngine,
        enrich_book_metadata, batch_enrich_from_csv
    )
except ImportError:
    from metadata_enrichment import (
        MetadataSource, EnrichmentStatus, BookIdentifier, AuthorInfo,
        PublisherInfo, EnrichedMetadata, GoogleBooksEnricher, 
        OpenLibraryEnricher, MetadataEnrichmentEngine,
        enrich_book_metadata, batch_enrich_from_csv
    )


class TestBookIdentifier:
    """Test BookIdentifier functionality."""
    
    def test_search_terms_with_isbn(self):
        """Test search term generation with ISBN."""
        identifier = BookIdentifier(
            isbn_13="9780142437094",
            title="Bhagavad Gita",
            author="Anonymous"
        )
        
        terms = identifier.get_search_terms()
        assert "isbn:9780142437094" in terms
        assert 'intitle:"Bhagavad Gita" inauthor:"Anonymous"' in terms
    
    def test_search_terms_title_only(self):
        """Test search term generation with title only."""
        identifier = BookIdentifier(title="The Art of War")
        
        terms = identifier.get_search_terms()
        assert 'intitle:"The Art of War"' in terms
        assert len(terms) == 1
    
    def test_search_terms_empty(self):
        """Test search term generation with no data."""
        identifier = BookIdentifier()
        
        terms = identifier.get_search_terms()
        assert terms == []


class TestEnrichedMetadata:
    """Test EnrichedMetadata functionality."""
    
    def test_initialization_with_defaults(self):
        """Test metadata initialization with default values."""
        metadata = EnrichedMetadata(title="Test Book")
        
        assert metadata.title == "Test Book"
        assert metadata.authors == []
        assert metadata.categories == []
        assert metadata.enrichment_status == EnrichmentStatus.PENDING
    
    def test_initialization_with_data(self):
        """Test metadata initialization with provided data."""
        authors = [AuthorInfo(name="Test Author")]
        metadata = EnrichedMetadata(
            title="Test Book",
            authors=authors,
            page_count=300,
            enrichment_status=EnrichmentStatus.COMPLETED
        )
        
        assert metadata.title == "Test Book"
        assert len(metadata.authors) == 1
        assert metadata.authors[0].name == "Test Author"
        assert metadata.page_count == 300
        assert metadata.enrichment_status == EnrichmentStatus.COMPLETED


class TestGoogleBooksEnricher:
    """Test Google Books enrichment functionality."""
    
    @pytest.fixture
    def enricher(self):
        """Create GoogleBooksEnricher instance."""
        return GoogleBooksEnricher(api_key="test_key", rate_limit=0.1)
    
    @pytest.fixture
    def mock_google_response(self):
        """Mock Google Books API response."""
        return {
            "items": [
                {
                    "volumeInfo": {
                        "title": "Bhagavad Gita",
                        "subtitle": "As It Is",
                        "authors": ["A.C. Bhaktivedanta Swami Prabhupada"],
                        "publisher": "The Bhaktivedanta Book Trust",
                        "publishedDate": "1989",
                        "description": "The Bhagavad Gita is a sacred Hindu scripture...",
                        "pageCount": 912,
                        "categories": ["Religion", "Philosophy"],
                        "averageRating": 4.5,
                        "ratingsCount": 1250,
                        "language": "en",
                        "industryIdentifiers": [
                            {"type": "ISBN_13", "identifier": "9780892131945"},
                            {"type": "ISBN_10", "identifier": "0892131942"}
                        ],
                        "imageLinks": {
                            "thumbnail": "http://books.google.com/books/content?id=test&printsec=frontcover&img=1&zoom=1",
                            "small": "http://books.google.com/books/content?id=test&printsec=frontcover&img=1&zoom=2"
                        }
                    }
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_search_book_success(self, enricher, mock_google_response):
        """Test successful book search."""
        identifier = BookIdentifier(title="Bhagavad Gita", author="Prabhupada")
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_google_response)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            results = await enricher.search_book(identifier)
            
            assert len(results) == 1
            assert results[0]['volumeInfo']['title'] == "Bhagavad Gita"
    
    @pytest.mark.asyncio
    async def test_search_book_no_results(self, enricher):
        """Test book search with no results."""
        identifier = BookIdentifier(title="Nonexistent Book")
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"items": []})
            mock_get.return_value.__aenter__.return_value = mock_response
            
            results = await enricher.search_book(identifier)
            
            assert results == []
    
    def test_extract_metadata(self, enricher, mock_google_response):
        """Test metadata extraction from Google Books response."""
        volume_info = mock_google_response['items'][0]['volumeInfo']
        metadata = enricher._extract_metadata(volume_info)
        
        assert metadata.title == "Bhagavad Gita"
        assert metadata.subtitle == "As It Is"
        assert len(metadata.authors) == 1
        assert metadata.authors[0].name == "A.C. Bhaktivedanta Swami Prabhupada"
        assert metadata.publisher.name == "The Bhaktivedanta Book Trust"
        assert metadata.page_count == 912
        assert metadata.average_rating == 4.5
        assert metadata.isbn_13 == "9780892131945"
        assert metadata.isbn_10 == "0892131942"
        assert len(metadata.categories) == 2
        assert "Religion" in metadata.categories
        assert metadata.enrichment_sources == [MetadataSource.GOOGLE_BOOKS]
    
    @pytest.mark.asyncio
    async def test_enrich_success(self, enricher, mock_google_response):
        """Test complete enrichment process."""
        identifier = BookIdentifier(title="Bhagavad Gita")
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_google_response)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            metadata = await enricher.enrich(identifier)
            
            assert metadata is not None
            assert metadata.title == "Bhagavad Gita"
            assert len(metadata.authors) == 1


class TestOpenLibraryEnricher:
    """Test OpenLibrary enrichment functionality."""
    
    @pytest.fixture
    def enricher(self):
        """Create OpenLibraryEnricher instance."""
        return OpenLibraryEnricher(rate_limit=0.1)
    
    @pytest.fixture
    def mock_openlibrary_response(self):
        """Mock OpenLibrary API response."""
        return {
            "title": "Bhagavad Gita",
            "subtitle": "A New Translation",
            "authors": [{"name": "Barbara Stoler Miller"}],
            "publishers": ["Bantam Books"],
            "publish_date": "1986",
            "number_of_pages": 208,
            "subjects": ["Hindu philosophy", "Sanskrit literature", "Religious texts"],
            "isbn_13": ["9780553213652"],
            "isbn_10": ["0553213652"],
            "cover_i": 12345
        }
    
    @pytest.mark.asyncio
    async def test_search_book_by_isbn(self, enricher, mock_openlibrary_response):
        """Test book search by ISBN."""
        identifier = BookIdentifier(isbn_13="9780553213652")
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_openlibrary_response)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            results = await enricher.search_book(identifier)
            
            assert len(results) == 1
            assert results[0]['title'] == "Bhagavad Gita"
    
    @pytest.mark.asyncio
    async def test_search_book_by_title(self, enricher):
        """Test book search by title."""
        identifier = BookIdentifier(title="Bhagavad Gita", author="Miller")
        mock_response_data = {
            "docs": [
                {
                    "title": "Bhagavad Gita",
                    "author_name": ["Barbara Stoler Miller"],
                    "first_publish_year": 1986
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            results = await enricher.search_book(identifier)
            
            assert len(results) == 1
            assert results[0]['title'] == "Bhagavad Gita"
    
    def test_extract_metadata(self, enricher, mock_openlibrary_response):
        """Test metadata extraction from OpenLibrary response."""
        metadata = enricher._extract_metadata(mock_openlibrary_response)
        
        assert metadata.title == "Bhagavad Gita"
        assert metadata.subtitle == "A New Translation"
        assert len(metadata.authors) == 1
        assert metadata.authors[0].name == "Barbara Stoler Miller"
        assert metadata.publisher.name == "Bantam Books"
        assert metadata.page_count == 208
        assert metadata.isbn_13 == "9780553213652"
        assert metadata.isbn_10 == "0553213652"
        assert len(metadata.subjects) == 3
        assert "Hindu philosophy" in metadata.subjects
        assert metadata.enrichment_sources == [MetadataSource.OPENLIBRARY]
        assert "12345" in metadata.cover_image_url


class TestMetadataEnrichmentEngine:
    """Test the main enrichment engine."""
    
    @pytest.fixture
    def engine(self):
        """Create MetadataEnrichmentEngine instance."""
        return MetadataEnrichmentEngine(google_books_api_key="test_key")
    
    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata for testing."""
        return EnrichedMetadata(
            title="Test Book",
            authors=[AuthorInfo(name="Test Author")],
            publisher=PublisherInfo(name="Test Publisher"),
            page_count=200,
            enrichment_sources=[MetadataSource.GOOGLE_BOOKS],
            enrichment_timestamp=datetime.now()
        )
    
    def test_cache_key_generation(self, engine):
        """Test cache key generation."""
        identifier = BookIdentifier(
            isbn_13="9780142437094",
            title="Test Book",
            author="Test Author"
        )
        
        key = engine._generate_cache_key(identifier)
        assert "isbn13:9780142437094" in key
    
    def test_quality_score_calculation(self, engine, sample_metadata):
        """Test quality score calculation."""
        score = engine._calculate_quality_score(sample_metadata)
        
        assert 0.0 <= score <= 1.0
        assert score > 0  # Should have some score with basic metadata
    
    def test_metadata_merging(self, engine):
        """Test merging metadata from multiple sources."""
        metadata1 = EnrichedMetadata(
            title="Test Book",
            authors=[AuthorInfo(name="Author 1")],
            page_count=200,
            enrichment_sources=[MetadataSource.GOOGLE_BOOKS]
        )
        
        metadata2 = EnrichedMetadata(
            title="Test Book",
            authors=[AuthorInfo(name="Author 1"), AuthorInfo(name="Author 2")],
            description="Test description",
            enrichment_sources=[MetadataSource.OPENLIBRARY]
        )
        
        merged = engine._merge_metadata(metadata1, metadata2)
        
        assert merged.title == "Test Book"
        assert len(merged.authors) == 2  # Should merge unique authors
        assert merged.page_count == 200  # Should take from first metadata
        assert merged.description == "Test description"  # Should take from second
        assert len(merged.enrichment_sources) == 2  # Should combine sources
        assert merged.enrichment_quality_score is not None
    
    @pytest.mark.asyncio
    async def test_enrich_book_with_cache(self, engine):
        """Test book enrichment with caching."""
        identifier = BookIdentifier(title="Test Book", author="Test Author")
        
        # Mock the enrichers
        mock_metadata = EnrichedMetadata(
            title="Test Book",
            authors=[AuthorInfo(name="Test Author")],
            enrichment_sources=[MetadataSource.GOOGLE_BOOKS],
            enrichment_timestamp=datetime.now()
        )
        
        with patch.object(engine.enrichers[MetadataSource.GOOGLE_BOOKS], 'enrich') as mock_enrich:
            mock_enrich.return_value = mock_metadata
            
            # First call should hit the enricher
            result1 = await engine.enrich_book(identifier)
            assert mock_enrich.call_count == 1
            
            # Second call should use cache
            result2 = await engine.enrich_book(identifier)
            assert mock_enrich.call_count == 1  # Should not increase
            
            assert result1.title == result2.title
    
    @pytest.mark.asyncio
    async def test_batch_enrichment(self, engine):
        """Test batch enrichment."""
        identifiers = [
            BookIdentifier(title="Book 1", author="Author 1"),
            BookIdentifier(title="Book 2", author="Author 2"),
            BookIdentifier(title="Book 3", author="Author 3")
        ]
        
        mock_metadata = EnrichedMetadata(
            title="Test Book",
            enrichment_sources=[MetadataSource.GOOGLE_BOOKS],
            enrichment_timestamp=datetime.now()
        )
        
        with patch.object(engine, 'enrich_book') as mock_enrich:
            mock_enrich.return_value = mock_metadata
            
            results = await engine.batch_enrich(identifiers, batch_size=2)
            
            assert len(results) == 3
            assert mock_enrich.call_count == 3
    
    def test_cache_stats(self, engine):
        """Test cache statistics."""
        # Add some test entries to cache
        import time
        engine.cache['test1'] = {'metadata': {}, 'timestamp': time.time()}
        engine.cache['test2'] = {'metadata': {}, 'timestamp': time.time() - 25*60*60}  # Expired
        
        stats = engine.get_cache_stats()
        
        assert stats['total_entries'] == 2
        assert stats['valid_entries'] == 1
        assert stats['expired_entries'] == 1
        assert stats['cache_hit_rate'] == 0.5
    
    def test_clear_cache(self, engine):
        """Test cache clearing."""
        engine.cache['test'] = {'metadata': {}, 'timestamp': 12345}
        assert len(engine.cache) == 1
        
        engine.clear_cache()
        assert len(engine.cache) == 0


class TestUtilityFunctions:
    """Test utility functions."""
    
    @pytest.mark.asyncio
    async def test_enrich_book_metadata_function(self):
        """Test the convenience enrichment function."""
        with patch('metadata_enrichment.MetadataEnrichmentEngine') as MockEngine:
            mock_instance = MockEngine.return_value
            mock_metadata = EnrichedMetadata(
                title="Test Book",
                enrichment_timestamp=datetime.now()
            )
            mock_instance.enrich_book = AsyncMock(return_value=mock_metadata)
            
            result = await enrich_book_metadata("Test Book", "Test Author", "9781234567890")
            
            assert result.title == "Test Book"
            MockEngine.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_enrich_from_csv(self):
        """Test batch enrichment from CSV file."""
        # Create temporary CSV file
        import csv
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['title', 'author', 'isbn'])
            writer.writerow(['Book 1', 'Author 1', '9781234567890'])
            writer.writerow(['Book 2', 'Author 2', '9781234567891'])
            csv_path = f.name
        
        try:
            with patch('metadata_enrichment.MetadataEnrichmentEngine') as MockEngine:
                mock_instance = MockEngine.return_value
                mock_results = [
                    EnrichedMetadata(title="Book 1", enrichment_timestamp=datetime.now()),
                    EnrichedMetadata(title="Book 2", enrichment_timestamp=datetime.now())
                ]
                mock_instance.batch_enrich = AsyncMock(return_value=mock_results)
                
                results = await batch_enrich_from_csv(csv_path)
                
                assert len(results) == 2
                assert results[0].title == "Book 1"
                assert results[1].title == "Book 2"
        finally:
            import os
            os.unlink(csv_path)


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test handling of network errors."""
        enricher = GoogleBooksEnricher()
        identifier = BookIdentifier(title="Test Book")
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            result = await enricher.enrich(identifier)
            assert result is None
    
    @pytest.mark.asyncio
    async def test_api_error_response(self):
        """Test handling of API error responses."""
        enricher = GoogleBooksEnricher()
        identifier = BookIdentifier(title="Test Book")
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await enricher.search_book(identifier)
            assert result == []
    
    @pytest.mark.asyncio
    async def test_enrichment_engine_fallback(self):
        """Test engine fallback when enrichment fails."""
        engine = MetadataEnrichmentEngine()
        identifier = BookIdentifier(title="Test Book")
        
        # Mock all enrichers to fail
        for enricher in engine.enrichers.values():
            enricher.enrich = AsyncMock(return_value=None)
        
        result = await engine.enrich_book(identifier)
        
        assert result.title == "Test Book"
        assert result.enrichment_status == EnrichmentStatus.FAILED
        assert result.enrichment_quality_score == 0.0


if __name__ == "__main__":
    # Run basic tests without pytest
    import asyncio
    
    async def run_basic_tests():
        print("Running metadata enrichment tests...")
        
        # Test BookIdentifier
        print("✓ Testing BookIdentifier...")
        identifier = BookIdentifier(title="Bhagavad Gita", author="Prabhupada", isbn_13="9780892131945")
        terms = identifier.get_search_terms()
        assert len(terms) >= 2
        print(f"  Search terms: {terms}")
        
        # Test EnrichedMetadata
        print("✓ Testing EnrichedMetadata...")
        metadata = EnrichedMetadata(title="Test Book")
        assert metadata.authors == []
        assert metadata.enrichment_status == EnrichmentStatus.PENDING
        
        # Test MetadataEnrichmentEngine
        print("✓ Testing MetadataEnrichmentEngine...")
        engine = MetadataEnrichmentEngine()
        
        # Test cache functionality
        cache_key = engine._generate_cache_key(identifier)
        assert cache_key
        print(f"  Cache key: {cache_key}")
        
        # Test quality score calculation
        test_metadata = EnrichedMetadata(
            title="Test Book",
            authors=[AuthorInfo(name="Test Author")],
            description="Test description"
        )
        score = engine._calculate_quality_score(test_metadata)
        assert 0.0 <= score <= 1.0
        print(f"  Quality score: {score:.2f}")
        
        print("✅ Basic metadata enrichment tests completed!")
    
    asyncio.run(run_basic_tests())
