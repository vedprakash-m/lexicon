"""
Core web scraping engine for Lexicon.

This module provides a robust, polite, and extensible web scraping system
that forms the foundation for all content extraction operations.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import aiohttp
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ScrapingConfig:
    """Configuration for web scraping operations."""
    
    # Rate limiting
    requests_per_second: float = 0.5  # Default: 2 seconds between requests
    max_concurrent_requests: int = 1   # Conservative default
    
    # Request configuration
    timeout: int = 30
    max_retries: int = 3
    backoff_factor: float = 1.0
    
    # User agent and headers
    user_agent: str = "Lexicon RAG Dataset Tool 1.0 (Educational Use)"
    custom_headers: Dict[str, str] = field(default_factory=dict)
    
    # Politeness settings
    respect_robots_txt: bool = True
    cache_robots_txt: bool = True
    
    # Progress tracking
    progress_callback: Optional[Callable[[str, int, int], None]] = None
    
    # Content filtering
    max_content_size: int = 50 * 1024 * 1024  # 50MB limit
    allowed_content_types: List[str] = field(default_factory=lambda: [
        'text/html', 'text/plain', 'application/json', 'application/xml'
    ])


@dataclass
class ScrapingResult:
    """Result of a web scraping operation."""
    
    url: str
    status_code: int
    content: str
    headers: Dict[str, str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    @property
    def is_success(self) -> bool:
        """Check if the scraping was successful."""
        return self.status_code == 200 and self.error is None
    
    @property
    def soup(self) -> BeautifulSoup:
        """Get BeautifulSoup object for HTML content."""
        if not hasattr(self, '_soup'):
            self._soup = BeautifulSoup(self.content, 'lxml')
        return self._soup


class RateLimiter:
    """Thread-safe rate limiter for web requests."""
    
    def __init__(self, requests_per_second: float):
        self.min_interval = 1.0 / requests_per_second if requests_per_second > 0 else 0
        self.last_request_time = 0
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make a request, respecting rate limits."""
        async with self._lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
            
            self.last_request_time = time.time()


class RobotsTxtChecker:
    """Check robots.txt compliance for polite scraping."""
    
    def __init__(self, cache_enabled: bool = True):
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, RobotFileParser] = {}
    
    def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """Check if the URL can be fetched according to robots.txt."""
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            if self.cache_enabled and robots_url in self._cache:
                rp = self._cache[robots_url]
            else:
                rp = RobotFileParser()
                rp.set_url(robots_url)
                rp.read()
                
                if self.cache_enabled:
                    self._cache[robots_url] = rp
            
            return rp.can_fetch(user_agent, url)
        
        except Exception as e:
            logger.warning(f"Could not check robots.txt for {url}: {e}")
            return True  # Allow by default if robots.txt is inaccessible


class WebScraper:
    """
    Robust web scraping engine with built-in politeness, rate limiting,
    error handling, and progress tracking.
    """
    
    def __init__(self, config: Optional[ScrapingConfig] = None):
        self.config = config or ScrapingConfig()
        self.rate_limiter = RateLimiter(self.config.requests_per_second)
        self.robots_checker = RobotsTxtChecker(self.config.cache_robots_txt)
        self.session = self._create_session()
        
        # Statistics tracking
        self.stats = {
            'requests_made': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'bytes_downloaded': 0,
            'start_time': time.time()
        }
    
    def _create_session(self) -> requests.Session:
        """Create a configured requests session with retry logic."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        headers = {
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        headers.update(self.config.custom_headers)
        session.headers.update(headers)
        
        return session
    
    def _report_progress(self, message: str, current: int, total: int):
        """Report progress to the configured callback."""
        if self.config.progress_callback:
            self.config.progress_callback(message, current, total)
    
    def _validate_content(self, response: requests.Response) -> bool:
        """Validate response content before processing."""
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        if not any(allowed in content_type for allowed in self.config.allowed_content_types):
            logger.warning(f"Unsupported content type: {content_type}")
            return False
        
        # Check content size
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > self.config.max_content_size:
            logger.warning(f"Content too large: {content_length} bytes")
            return False
        
        return True
    
    async def scrape_url(self, url: str) -> ScrapingResult:
        """
        Scrape a single URL with full error handling and politeness checks.
        
        Args:
            url: The URL to scrape
            
        Returns:
            ScrapingResult with content and metadata
        """
        logger.info(f"Scraping URL: {url}")
        
        # Check robots.txt if enabled
        if self.config.respect_robots_txt:
            if not self.robots_checker.can_fetch(url, self.config.user_agent):
                error_msg = f"Robots.txt disallows scraping of {url}"
                logger.warning(error_msg)
                return ScrapingResult(
                    url=url,
                    status_code=403,
                    content="",
                    headers={},
                    error=error_msg
                )
        
        # Apply rate limiting
        await self.rate_limiter.acquire()
        
        try:
            self.stats['requests_made'] += 1
            
            # Make the request
            response = self.session.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            
            # Validate content
            if not self._validate_content(response):
                return ScrapingResult(
                    url=url,
                    status_code=response.status_code,
                    content="",
                    headers=dict(response.headers),
                    error="Content validation failed"
                )
            
            # Update statistics
            self.stats['successful_requests'] += 1
            self.stats['bytes_downloaded'] += len(response.content)
            
            # Extract metadata
            metadata = {
                'content_type': response.headers.get('content-type', ''),
                'content_length': len(response.content),
                'encoding': response.encoding,
                'final_url': response.url,  # After redirects
            }
            
            logger.debug(f"Successfully scraped {url}: {len(response.content)} bytes")
            
            return ScrapingResult(
                url=url,
                status_code=response.status_code,
                content=response.text,
                headers=dict(response.headers),
                metadata=metadata
            )
            
        except requests.exceptions.RequestException as e:
            self.stats['failed_requests'] += 1
            error_msg = f"Request failed for {url}: {str(e)}"
            logger.error(error_msg)
            
            return ScrapingResult(
                url=url,
                status_code=getattr(e.response, 'status_code', 0) if hasattr(e, 'response') else 0,
                content="",
                headers={},
                error=error_msg
            )
        
        except Exception as e:
            self.stats['failed_requests'] += 1
            error_msg = f"Unexpected error scraping {url}: {str(e)}"
            logger.error(error_msg)
            
            return ScrapingResult(
                url=url,
                status_code=0,
                content="",
                headers={},
                error=error_msg
            )
    
    async def scrape_urls(self, urls: List[str]) -> List[ScrapingResult]:
        """
        Scrape multiple URLs with concurrent processing and progress tracking.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of ScrapingResult objects
        """
        total_urls = len(urls)
        logger.info(f"Starting batch scraping of {total_urls} URLs")
        
        results = []
        semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
        async def scrape_with_semaphore(url: str, index: int) -> ScrapingResult:
            async with semaphore:
                self._report_progress(f"Scraping {url}", index + 1, total_urls)
                return await self.scrape_url(url)
        
        # Create tasks for concurrent execution
        tasks = [
            scrape_with_semaphore(url, i) 
            for i, url in enumerate(urls)
        ]
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions that occurred
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = ScrapingResult(
                    url=urls[i],
                    status_code=0,
                    content="",
                    headers={},
                    error=f"Task execution failed: {str(result)}"
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        logger.info(f"Batch scraping completed: {len(processed_results)} results")
        return processed_results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        current_time = time.time()
        duration = current_time - self.stats['start_time']
        
        return {
            **self.stats,
            'duration_seconds': duration,
            'success_rate': (
                self.stats['successful_requests'] / max(1, self.stats['requests_made'])
            ),
            'average_request_time': duration / max(1, self.stats['requests_made']),
            'bytes_per_second': self.stats['bytes_downloaded'] / max(1, duration),
        }
    
    def close(self):
        """Clean up resources."""
        if hasattr(self, 'session'):
            self.session.close()


# Convenience functions for simple use cases

async def scrape_single_url(
    url: str, 
    config: Optional[ScrapingConfig] = None
) -> ScrapingResult:
    """Convenience function to scrape a single URL."""
    scraper = WebScraper(config)
    try:
        return await scraper.scrape_url(url)
    finally:
        scraper.close()


async def scrape_multiple_urls(
    urls: List[str], 
    config: Optional[ScrapingConfig] = None
) -> List[ScrapingResult]:
    """Convenience function to scrape multiple URLs."""
    scraper = WebScraper(config)
    try:
        return await scraper.scrape_urls(urls)
    finally:
        scraper.close()


# Example usage and testing
if __name__ == "__main__":
    async def main():
        # Test configuration
        config = ScrapingConfig(
            requests_per_second=1.0,
            timeout=10,
            progress_callback=lambda msg, curr, total: print(f"{msg} ({curr}/{total})")
        )
        
        # Test URLs
        test_urls = [
            "https://httpbin.org/get",
            "https://httpbin.org/user-agent",
            "https://httpbin.org/headers"
        ]
        
        # Test scraping
        results = await scrape_multiple_urls(test_urls, config)
        
        for result in results:
            print(f"URL: {result.url}")
            print(f"Status: {result.status_code}")
            print(f"Success: {result.is_success}")
            if result.error:
                print(f"Error: {result.error}")
            print("---")
    
    # Run the test
    asyncio.run(main())
