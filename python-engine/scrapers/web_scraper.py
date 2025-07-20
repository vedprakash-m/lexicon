import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
import time
import logging
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import re
import threading
from enum import Enum

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ScrapingResult:
    url: str
    title: str
    text: str
    metadata: Dict
    links: List[str]
    images: List[str]
    extraction_method: str
    quality_score: float
    response_time: float

class WebScraper:
    def __init__(self, rate_limit: float = 1.0, timeout: int = 30):
        self.rate_limit = rate_limit  # seconds between requests
        self.timeout = timeout
        self.last_request_time = 0
        self.logger = logging.getLogger(__name__)
        self._is_paused = False
        self._is_cancelled = False
        self._pause_event = threading.Event()
        self._pause_event.set()  # Start unpaused
        
        # Common headers to appear more like a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def pause(self):
        """Pause the scraping operation"""
        self._is_paused = True
        self._pause_event.clear()
        self.logger.info("Scraping paused")
    
    def resume(self):
        """Resume the scraping operation"""
        self._is_paused = False
        self._pause_event.set()
        self.logger.info("Scraping resumed")
    
    def cancel(self):
        """Cancel the scraping operation"""
        self._is_cancelled = True
        self._pause_event.set()  # Wake up any waiting threads
        self.logger.info("Scraping cancelled")
    
    def _check_pause_cancel(self):
        """Check if job should be paused or cancelled"""
        if self._is_cancelled:
            raise asyncio.CancelledError("Scraping job was cancelled")
        
        if self._is_paused:
            self.logger.info("Scraping paused, waiting to resume...")
            self._pause_event.wait()  # Block until resumed
        
        if self._is_cancelled:  # Check again after pause
            raise asyncio.CancelledError("Scraping job was cancelled")
        
    @property
    def status(self) -> JobStatus:
        """Get current job status"""
        if self._is_cancelled:
            return JobStatus.CANCELLED
        elif self._is_paused:
            return JobStatus.PAUSED
        else:
            return JobStatus.RUNNING
        
    def scrape_url(self, url: str, custom_rules: Optional[Dict] = None) -> ScrapingResult:
        """Scrape a single URL with rate limiting"""
        self._check_pause_cancel()
        self._respect_rate_limit()
        
        start_time = time.time()
        
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            self._check_pause_cancel()  # Check again after request
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Apply custom extraction rules if provided
            if custom_rules:
                result = self._apply_custom_rules(soup, url, custom_rules)
            else:
                result = self._extract_generic_content(soup, url)
                
            result.response_time = time.time() - start_time
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to scrape {url}: {e}")
            raise
            
    async def scrape_urls_async(self, urls: List[str], custom_rules: Optional[Dict] = None) -> List[ScrapingResult]:
        """Scrape multiple URLs asynchronously"""
        async with aiohttp.ClientSession(headers=self.headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            tasks = []
            for url in urls:
                task = self._scrape_url_async(session, url, custom_rules)
                tasks.append(task)
                
                # Add delay between starting requests to respect rate limiting
                if len(tasks) > 1:
                    await asyncio.sleep(self.rate_limit)
                    
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and return successful results
            successful_results = []
            for result in results:
                if isinstance(result, ScrapingResult):
                    successful_results.append(result)
                else:
                    self.logger.error(f"Async scraping failed: {result}")
                    
            return successful_results
            
    async def _scrape_url_async(self, session: aiohttp.ClientSession, url: str, custom_rules: Optional[Dict] = None) -> ScrapingResult:
        """Async version of URL scraping"""
        start_time = time.time()
        
        async with session.get(url) as response:
            content = await response.read()
            soup = BeautifulSoup(content, 'html.parser')
            
            if custom_rules:
                result = self._apply_custom_rules(soup, url, custom_rules)
            else:
                result = self._extract_generic_content(soup, url)
                
            result.response_time = time.time() - start_time
            return result
            
    def _extract_generic_content(self, soup: BeautifulSoup, url: str) -> ScrapingResult:
        """Generic content extraction for any website"""
        
        # Extract title
        title = ""
        if soup.title:
            title = soup.title.string.strip()
        elif soup.find('h1'):
            title = soup.find('h1').get_text().strip()
            
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
            
        # Extract main content
        main_content = None
        
        # Try to find main content area
        for selector in ['main', 'article', '.content', '.post', '.entry', '#content']:
            main_content = soup.select_one(selector)
            if main_content:
                break
                
        if not main_content:
            main_content = soup.find('body') or soup
            
        # Extract text
        text = main_content.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Extract metadata
        metadata = self._extract_metadata(soup)
        
        # Extract links
        links = []
        for link in soup.find_all('a', href=True):
            absolute_url = urljoin(url, link['href'])
            links.append(absolute_url)
            
        # Extract images
        images = []
        for img in soup.find_all('img', src=True):
            absolute_url = urljoin(url, img['src'])
            images.append(absolute_url)
            
        # Calculate quality score
        word_count = len(clean_text.split())
        quality_score = min(1.0, word_count / 200)  # Assume good quality if >200 words
        
        return ScrapingResult(
            url=url,
            title=title,
            text=clean_text,
            metadata=metadata,
            links=links[:50],  # Limit to first 50 links
            images=images[:20],  # Limit to first 20 images
            extraction_method='generic',
            quality_score=quality_score,
            response_time=0  # Will be set by caller
        )
        
    def _apply_custom_rules(self, soup: BeautifulSoup, url: str, rules: Dict) -> ScrapingResult:
        """Apply custom extraction rules for specific sites"""
        
        # Extract title using custom selector
        title = ""
        if 'title_selector' in rules:
            title_elem = soup.select_one(rules['title_selector'])
            if title_elem:
                title = title_elem.get_text().strip()
                
        # Extract content using custom selector
        text = ""
        if 'content_selector' in rules:
            content_elem = soup.select_one(rules['content_selector'])
            if content_elem:
                # Remove unwanted elements
                if 'remove_selectors' in rules:
                    for remove_selector in rules['remove_selectors']:
                        for elem in content_elem.select(remove_selector):
                            elem.decompose()
                            
                text = content_elem.get_text()
                
                # Clean up text
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)
                
        # Extract metadata
        metadata = self._extract_metadata(soup)
        
        # Add custom metadata
        if 'metadata_selectors' in rules:
            for key, selector in rules['metadata_selectors'].items():
                elem = soup.select_one(selector)
                if elem:
                    metadata[key] = elem.get_text().strip()
                    
        # Extract links and images (generic approach)
        links = [urljoin(url, link['href']) for link in soup.find_all('a', href=True)]
        images = [urljoin(url, img['src']) for img in soup.find_all('img', src=True)]
        
        word_count = len(text.split())
        quality_score = min(1.0, word_count / 200)
        
        return ScrapingResult(
            url=url,
            title=title,
            text=text,
            metadata=metadata,
            links=links[:50],
            images=images[:20],
            extraction_method='custom_rules',
            quality_score=quality_score,
            response_time=0
        )
        
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict:
        """Extract metadata from HTML"""
        metadata = {}
        
        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property') or meta.get('itemprop')
            content = meta.get('content')
            if name and content:
                metadata[name] = content
                
        # Open Graph tags
        for meta in soup.find_all('meta', property=re.compile(r'^og:')):
            property_name = meta.get('property')
            content = meta.get('content')
            if property_name and content:
                metadata[property_name] = content
                
        # Twitter Card tags
        for meta in soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')}):
            name = meta.get('name')
            content = meta.get('content')
            if name and content:
                metadata[name] = content
                
        # JSON-LD structured data
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                import json
                structured_data = json.loads(script.string)
                metadata['structured_data'] = structured_data
            except:
                pass
                
        return metadata
        
    def _respect_rate_limit(self):
        """Ensure rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
        
    def create_site_rules(self, domain: str, title_selector: str, content_selector: str, 
                         remove_selectors: Optional[List[str]] = None,
                         metadata_selectors: Optional[Dict[str, str]] = None) -> Dict:
        """Helper to create custom extraction rules for a site"""
        rules = {
            'domain': domain,
            'title_selector': title_selector,
            'content_selector': content_selector,
        }
        
        if remove_selectors:
            rules['remove_selectors'] = remove_selectors
            
        if metadata_selectors:
            rules['metadata_selectors'] = metadata_selectors
            
        return rules