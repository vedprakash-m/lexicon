"""
Core web scraping engine for Lexicon.

This module provides a robust, production-ready web scraping system with:
- HTTP client with retry logic and exponential backoff
- Rate limiting and politeness controls
- Comprehensive error handling and recovery
- Progress tracking and reporting
- Session management and cookie handling
- User-agent rotation and anti-detection measures
"""

import time
import asyncio
import logging
import hashlib
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Callable, Any
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
from pathlib import Path
import json

import aiohttp
import aiofiles
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ScrapingConfig:
    """Configuration settings for web scraping operations."""
    
    # Rate limiting
    request_delay: float = 1.0  # Seconds between requests
    max_requests_per_minute: int = 30
    burst_limit: int = 5  # Max concurrent requests
    
    # Retry settings
    max_retries: int = 3
    backoff_factor: float = 2.0  # Exponential backoff multiplier
    retry_statuses: List[int] = field(default_factory=lambda: [429, 502, 503, 504])
    
    # Timeout settings
    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    total_timeout: float = 60.0
    
    # User agent and headers
    user_agents: List[str] = field(default_factory=lambda: [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ])
    
    # Politeness settings
    respect_robots_txt: bool = True
    crawl_delay_override: Optional[float] = None
    
    # Cache settings
    enable_caching: bool = True
    cache_dir: Optional[str] = None
    cache_ttl: int = 3600  # Cache time-to-live in seconds
    
    # Output settings
    save_raw_html: bool = False
    raw_html_dir: Optional[str] = None


@dataclass
class ScrapingProgress:
    """Tracks progress of scraping operations."""
    
    total_urls: int = 0
    completed_urls: int = 0
    failed_urls: int = 0
    cached_urls: int = 0
    start_time: Optional[datetime] = None
    last_update: Optional[datetime] = None
    current_url: Optional[str] = None
    error_count: int = 0
    last_error: Optional[str] = None
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_urls == 0:
            return 0.0
        return (self.completed_urls / self.total_urls) * 100
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total_processed = self.completed_urls + self.failed_urls
        if total_processed == 0:
            return 0.0
        return (self.completed_urls / total_processed) * 100
    
    @property
    def elapsed_time(self) -> Optional[timedelta]:
        """Get elapsed time since start."""
        if self.start_time is None:
            return None
        return datetime.now() - self.start_time
    
    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        """Estimate remaining time based on current progress."""
        if self.start_time is None or self.completed_urls == 0:
            return None
        
        elapsed = self.elapsed_time
        remaining_urls = self.total_urls - self.completed_urls
        
        if remaining_urls <= 0:
            return timedelta(0)
        
        time_per_url = elapsed.total_seconds() / self.completed_urls
        return timedelta(seconds=time_per_url * remaining_urls)


class RateLimiter:
    """Rate limiter with token bucket algorithm."""
    
    def __init__(self, max_requests: int, time_window: float = 60.0):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds (default: 60 seconds)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire permission to make a request (async)."""
        async with self._lock:
            now = time.time()
            
            # Remove old requests outside the time window
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < self.time_window]
            
            # Check if we can make a request
            if len(self.requests) >= self.max_requests:
                # Calculate wait time
                oldest_request = min(self.requests)
                wait_time = self.time_window - (now - oldest_request)
                if wait_time > 0:
                    logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                    await asyncio.sleep(wait_time)
                    return await self.acquire()  # Retry after waiting
            
            # Record this request
            self.requests.append(now)


class ResponseCache:
    """Simple file-based response cache."""
    
    def __init__(self, cache_dir: str, ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl: Time-to-live in seconds
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl
    
    def _get_cache_key(self, url: str, headers: Optional[Dict] = None) -> str:
        """Generate cache key for URL and headers."""
        cache_string = url
        if headers:
            # Sort headers for consistent key generation
            sorted_headers = sorted(headers.items())
            cache_string += str(sorted_headers)
        
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache key."""
        return self.cache_dir / f"{cache_key}.json"
    
    async def get(self, url: str, headers: Optional[Dict] = None) -> Optional[Dict]:
        """Get cached response if available and not expired."""
        cache_key = self._get_cache_key(url, headers)
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
        
        try:
            async with aiofiles.open(cache_path, 'r') as f:
                cache_data = json.loads(await f.read())
            
            # Check if cache is expired
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cached_time > timedelta(seconds=self.ttl):
                # Remove expired cache
                cache_path.unlink()
                return None
            
            logger.debug(f"Cache hit for {url}")
            return cache_data['response']
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Invalid cache file {cache_path}: {e}")
            # Remove invalid cache file
            if cache_path.exists():
                cache_path.unlink()
            return None
    
    async def set(self, url: str, response_data: Dict, headers: Optional[Dict] = None) -> None:
        """Cache response data."""
        cache_key = self._get_cache_key(url, headers)
        cache_path = self._get_cache_path(cache_key)
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'url': url,
            'response': response_data
        }
        
        try:
            async with aiofiles.open(cache_path, 'w') as f:
                await f.write(json.dumps(cache_data, indent=2))
            logger.debug(f"Cached response for {url}")
        except Exception as e:
            logger.warning(f"Failed to cache response for {url}: {e}")


class WebScraper:
    """
    Robust web scraper with rate limiting, retry logic, and error handling.
    """
    
    def __init__(self, config: Optional[ScrapingConfig] = None):
        """Initialize the web scraper."""
        self.config = config or ScrapingConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = RateLimiter(
            self.config.max_requests_per_minute, 
            time_window=60.0
        )
        
        # Progress tracking
        self.progress = ScrapingProgress()
        self.progress_callbacks: List[Callable[[ScrapingProgress], None]] = []
        
        # Cache setup
        self.cache: Optional[ResponseCache] = None
        if self.config.enable_caching and self.config.cache_dir:
            self.cache = ResponseCache(self.config.cache_dir, self.config.cache_ttl)
        
        # Robots.txt cache
        self.robots_cache: Dict[str, RobotFileParser] = {}
        
        logger.info("WebScraper initialized with configuration")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_session()
    
    async def start_session(self) -> None:
        """Start the HTTP session."""
        if self.session is not None:
            return
        
        # Setup timeouts
        timeout = aiohttp.ClientTimeout(
            connect=self.config.connect_timeout,
            sock_read=self.config.read_timeout,
            total=self.config.total_timeout
        )
        
        # Setup session with default headers
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers,
            connector=aiohttp.TCPConnector(
                limit=self.config.burst_limit,
                limit_per_host=self.config.burst_limit
            )
        )
        
        logger.info("HTTP session started")
    
    async def close_session(self) -> None:
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("HTTP session closed")
    
    def add_progress_callback(self, callback: Callable[[ScrapingProgress], None]) -> None:
        """Add a progress callback function."""
        self.progress_callbacks.append(callback)
    
    def _notify_progress(self) -> None:
        """Notify all progress callbacks."""
        self.progress.last_update = datetime.now()
        for callback in self.progress_callbacks:
            try:
                callback(self.progress)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the configured list."""
        return random.choice(self.config.user_agents)
    
    async def _check_robots_txt(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        if not self.config.respect_robots_txt:
            return True
        
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        if base_url not in self.robots_cache:
            robots_url = urljoin(base_url, '/robots.txt')
            
            try:
                rp = RobotFileParser()
                rp.set_url(robots_url)
                rp.read()
                self.robots_cache[base_url] = rp
                logger.debug(f"Loaded robots.txt for {base_url}")
            except Exception as e:
                logger.warning(f"Could not load robots.txt for {base_url}: {e}")
                # Create permissive robots parser
                rp = RobotFileParser()
                rp.set_url(robots_url)
                self.robots_cache[base_url] = rp
        
        rp = self.robots_cache[base_url]
        user_agent = self._get_random_user_agent()
        
        return rp.can_fetch(user_agent, url)
    
    async def _make_request(self, url: str, headers: Optional[Dict] = None, 
                          method: str = 'GET', **kwargs) -> aiohttp.ClientResponse:
        """Make HTTP request with retry logic."""
        if self.session is None:
            await self.start_session()
        
        # Prepare headers
        request_headers = {'User-Agent': self._get_random_user_agent()}
        if headers:
            request_headers.update(headers)
        
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # Rate limiting
                await self.rate_limiter.acquire()
                
                # Request delay for politeness
                if self.config.request_delay > 0:
                    await asyncio.sleep(self.config.request_delay)
                
                # Make the request
                async with self.session.request(
                    method, url, headers=request_headers, **kwargs
                ) as response:
                    # Check if we should retry based on status
                    if response.status in self.config.retry_statuses and attempt < self.config.max_retries:
                        wait_time = self.config.backoff_factor ** attempt
                        logger.warning(f"Request failed with status {response.status}, retrying in {wait_time}s (attempt {attempt + 1})")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    # If successful or final attempt, return response
                    return response
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    wait_time = self.config.backoff_factor ** attempt
                    logger.warning(f"Request failed: {e}, retrying in {wait_time}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {self.config.max_retries} retries: {e}")
                    raise
        
        # This should never be reached, but just in case
        raise last_exception or Exception("Unknown error in request retry logic")
    
    async def fetch_page(self, url: str, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Fetch a single page and return structured data.
        
        Returns:
            Dictionary containing:
            - url: The requested URL
            - final_url: Final URL after redirects
            - status_code: HTTP status code
            - headers: Response headers
            - content: Page content (HTML/text)
            - soup: BeautifulSoup object (if HTML)
            - metadata: Additional metadata
            - cached: Whether response came from cache
        """
        logger.info(f"Fetching: {url}")
        self.progress.current_url = url
        
        # Check cache first
        cached_response = None
        if self.cache:
            cached_response = await self.cache.get(url, headers)
            if cached_response:
                self.progress.cached_urls += 1
                self._notify_progress()
                logger.info(f"Using cached response for: {url}")
                cached_response['cached'] = True
                return cached_response
        
        # Check robots.txt
        if not await self._check_robots_txt(url):
            error_msg = f"URL blocked by robots.txt: {url}"
            logger.warning(error_msg)
            self.progress.failed_urls += 1
            self.progress.error_count += 1
            self.progress.last_error = error_msg
            self._notify_progress()
            raise PermissionError(error_msg)
        
        try:
            # Make the request
            async with await self._make_request(url, headers) as response:
                # Read content
                content = await response.text()
                
                # Parse with BeautifulSoup if HTML
                soup = None
                content_type = response.headers.get('content-type', '').lower()
                if 'html' in content_type:
                    try:
                        soup = BeautifulSoup(content, 'html.parser')
                    except Exception as e:
                        logger.warning(f"Failed to parse HTML for {url}: {e}")
                
                # Build response data
                response_data = {
                    'url': url,
                    'final_url': str(response.url),
                    'status_code': response.status,
                    'headers': dict(response.headers),
                    'content': content,
                    'soup': soup,
                    'metadata': {
                        'content_type': content_type,
                        'content_length': len(content),
                        'encoding': response.charset or 'utf-8',
                        'timestamp': datetime.now().isoformat(),
                    },
                    'cached': False
                }
                
                # Save raw HTML if configured
                if self.config.save_raw_html and self.config.raw_html_dir:
                    await self._save_raw_html(url, content)
                
                # Cache the response
                if self.cache:
                    # Don't cache the soup object (not JSON serializable)
                    cache_data = response_data.copy()
                    cache_data['soup'] = None
                    await self.cache.set(url, cache_data, headers)
                
                self.progress.completed_urls += 1
                self._notify_progress()
                
                logger.info(f"Successfully fetched: {url} (status: {response.status})")
                return response_data
                
        except Exception as e:
            error_msg = f"Failed to fetch {url}: {str(e)}"
            logger.error(error_msg)
            self.progress.failed_urls += 1
            self.progress.error_count += 1
            self.progress.last_error = error_msg
            self._notify_progress()
            raise
    
    async def _save_raw_html(self, url: str, content: str) -> None:
        """Save raw HTML content to file."""
        if not self.config.raw_html_dir:
            return
        
        # Create safe filename from URL
        safe_filename = hashlib.md5(url.encode()).hexdigest()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{safe_filename}.html"
        
        raw_dir = Path(self.config.raw_html_dir)
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = raw_dir / filename
        
        try:
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            logger.debug(f"Saved raw HTML to: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to save raw HTML for {url}: {e}")
    
    async def fetch_multiple(self, urls: List[str], 
                           headers: Optional[Dict] = None,
                           concurrent_limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch multiple URLs concurrently.
        
        Args:
            urls: List of URLs to fetch
            headers: Optional headers to include with requests
            concurrent_limit: Override default concurrent request limit
        
        Returns:
            List of response dictionaries (successful requests only)
        """
        if not urls:
            return []
        
        # Initialize progress tracking
        self.progress = ScrapingProgress()
        self.progress.total_urls = len(urls)
        self.progress.start_time = datetime.now()
        self._notify_progress()
        
        # Use configured burst limit or override
        semaphore_limit = concurrent_limit or self.config.burst_limit
        semaphore = asyncio.Semaphore(semaphore_limit)
        
        async def fetch_with_semaphore(url: str) -> Optional[Dict[str, Any]]:
            async with semaphore:
                try:
                    return await self.fetch_page(url, headers)
                except Exception as e:
                    logger.error(f"Failed to fetch {url}: {e}")
                    return None
        
        # Execute all requests
        logger.info(f"Starting to fetch {len(urls)} URLs with concurrency limit {semaphore_limit}")
        
        tasks = [fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        successful_results = []
        for result in results:
            if isinstance(result, dict):
                successful_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Task failed with exception: {result}")
        
        logger.info(f"Completed fetching. Success: {len(successful_results)}, Failed: {self.progress.failed_urls}")
        return successful_results
    
    def get_progress(self) -> ScrapingProgress:
        """Get current progress information."""
        return self.progress


# Convenience functions for common use cases

async def scrape_url(url: str, config: Optional[ScrapingConfig] = None) -> Dict[str, Any]:
    """Scrape a single URL with default configuration."""
    async with WebScraper(config) as scraper:
        return await scraper.fetch_page(url)


async def scrape_urls(urls: List[str], config: Optional[ScrapingConfig] = None) -> List[Dict[str, Any]]:
    """Scrape multiple URLs with default configuration."""
    async with WebScraper(config) as scraper:
        return await scraper.fetch_multiple(urls)


# Example usage and testing
if __name__ == "__main__":
    async def example_usage():
        """Example of how to use the WebScraper."""
        
        # Configure scraper
        config = ScrapingConfig(
            request_delay=0.5,
            max_requests_per_minute=20,
            enable_caching=True,
            cache_dir="./cache",
            save_raw_html=True,
            raw_html_dir="./raw_html"
        )
        
        # Example URLs to scrape
        test_urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://example.com",
        ]
        
        # Progress callback
        def progress_callback(progress: ScrapingProgress):
            print(f"Progress: {progress.completion_percentage:.1f}% "
                  f"({progress.completed_urls}/{progress.total_urls})")
        
        # Scrape URLs
        async with WebScraper(config) as scraper:
            scraper.add_progress_callback(progress_callback)
            results = await scraper.fetch_multiple(test_urls)
            
            print(f"\nScraping completed!")
            print(f"Results: {len(results)}")
            
            for result in results:
                print(f"- {result['url']}: {result['status_code']}")
    
    # Run example
    asyncio.run(example_usage())
