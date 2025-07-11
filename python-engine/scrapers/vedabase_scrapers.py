"""
Vedabase.io Specialized Scrapers

This module provides specialized scrapers for extracting structured scriptures from vedabase.io,
integrating with the core web scraping engine while preserving domain-specific knowledge
of text structure and metadata.

Supported texts:
- Bhagavad Gita (BG) - 18 chapters, 700 verses
- Srimad Bhagavatam (SB) - 12 cantos, 332 chapters, 18,000 verses  
- Sri Isopanisad (ISO) - 18 mantras + invocation

Author: Lexicon Development Team
"""

import asyncio
import logging
import json
import re
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlparse
from datetime import datetime

from web_scraper import WebScraper, ScrapingConfig, ScrapingResult
from bs4 import BeautifulSoup

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class VerseContent:
    """Structured verse content from Vedabase texts."""
    
    # Identification
    verse_reference: str  # e.g., "BG 2.47", "SB 1.1.1", "ISO 1"
    verse_numbers: List[str] = field(default_factory=list)  # For grouped verses
    
    # Text content
    sanskrit_verse: str = ""
    sanskrit_transliteration: str = ""
    synonyms: str = ""  # Word-by-word meanings
    translation: str = ""
    purport: str = ""  # Commentary/explanation
    
    # Metadata
    chapter_title: str = ""
    chapter_number: Optional[int] = None
    canto_number: Optional[int] = None  # For SB only
    url: str = ""
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'verse_reference': self.verse_reference,
            'verse_numbers': self.verse_numbers,
            'sanskrit_verse': self.sanskrit_verse,
            'sanskrit_transliteration': self.sanskrit_transliteration,
            'synonyms': self.synonyms,
            'translation': self.translation,
            'purport': self.purport,
            'chapter_title': self.chapter_title,
            'chapter_number': self.chapter_number,
            'canto_number': self.canto_number,
            'url': self.url,
            'scraped_at': self.scraped_at
        }


@dataclass
class TextMetadata:
    """Metadata for complete structured scriptures."""
    
    text_name: str
    text_abbreviation: str  # BG, SB, ISO
    total_chapters: int
    total_verses: int
    language: str = "Sanskrit"
    translator: str = "A.C. Bhaktivedanta Swami Prabhupada"
    source_url: str = ""
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'text_name': self.text_name,
            'text_abbreviation': self.text_abbreviation,
            'total_chapters': self.total_chapters,
            'total_verses': self.total_verses,
            'language': self.language,
            'translator': self.translator,
            'source_url': self.source_url,
            'scraped_at': self.scraped_at
        }


class VedabaseScraperBase:
    """Base class for Vedabase-specific scrapers."""
    
    def __init__(self, config: Optional[ScrapingConfig] = None):
        # Configure for polite Vedabase scraping
        self.config = config or ScrapingConfig(
            requests_per_second=0.5,  # Very conservative for respect
            timeout=30,
            max_retries=3,
            user_agent="Lexicon Educational RAG Dataset Tool 1.0",
            respect_robots_txt=True
        )
        
        self.scraper = WebScraper(self.config)
        self.base_url = "https://vedabase.io/en/library/"
        self.scraped_verses: List[VerseContent] = []
        self.failed_urls: List[str] = []
        
        # Text-specific configuration (to be overridden)
        self.text_abbreviation = ""
        self.text_name = ""
        self.expected_chapters = 0
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if hasattr(self.scraper, 'close'):
            self.scraper.close()
    
    def _extract_verse_content(self, soup: BeautifulSoup, url: str) -> VerseContent:
        """Extract verse content from BeautifulSoup object. To be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement _extract_verse_content")
    
    def _discover_verse_urls(self, chapter_url: str) -> List[str]:
        """Discover verse URLs for a chapter. To be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement _discover_verse_urls")
    
    async def scrape_verse(self, url: str) -> Optional[VerseContent]:
        """Scrape a single verse from URL."""
        try:
            result = await self.scraper.scrape_url(url)
            
            if not result.is_success:
                logger.error(f"Failed to scrape {url}: {result.error}")
                self.failed_urls.append(url)
                return None
            
            # Parse the content
            soup = result.soup
            verse_content = self._extract_verse_content(soup, url)
            verse_content.url = url
            
            logger.info(f"Successfully scraped verse: {verse_content.verse_reference}")
            return verse_content
            
        except Exception as e:
            logger.error(f"Error scraping verse {url}: {e}")
            self.failed_urls.append(url)
            return None
    
    async def scrape_chapter(self, chapter_url: str, chapter_num: int) -> List[VerseContent]:
        """Scrape all verses from a chapter."""
        logger.info(f"Scraping chapter {chapter_num} from {chapter_url}")
        
        # Discover verse URLs for this chapter
        verse_urls = await self._discover_verse_urls_async(chapter_url)
        
        if not verse_urls:
            logger.warning(f"No verses found for chapter {chapter_num}")
            return []
        
        logger.info(f"Found {len(verse_urls)} verses in chapter {chapter_num}")
        
        # Scrape all verses
        chapter_verses = []
        for i, verse_url in enumerate(verse_urls):
            if self.config.progress_callback:
                self.config.progress_callback(
                    f"Scraping chapter {chapter_num}, verse {i+1}",
                    i + 1,
                    len(verse_urls)
                )
            
            verse_content = await self.scrape_verse(verse_url)
            if verse_content:
                verse_content.chapter_number = chapter_num
                chapter_verses.append(verse_content)
        
        return chapter_verses
    
    async def _discover_verse_urls_async(self, chapter_url: str) -> List[str]:
        """Async wrapper for discovering verse URLs."""
        # First get the chapter page to find verse links
        result = await self.scraper.scrape_url(chapter_url)
        
        if not result.is_success:
            logger.error(f"Failed to load chapter page {chapter_url}: {result.error}")
            return []
        
        # Extract verse URLs from the chapter page
        soup = result.soup
        verse_urls = []
        
        # Look for verse links in the chapter page
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            
            # Check if this looks like a verse link
            if self._is_verse_link(href, chapter_url):
                full_url = urljoin("https://vedabase.io", href)
                if full_url not in verse_urls:
                    verse_urls.append(full_url)
        
        # Sort URLs to ensure proper verse order
        verse_urls.sort(key=self._verse_sort_key)
        
        return verse_urls
    
    def _is_verse_link(self, href: str, chapter_url: str) -> bool:
        """Check if href is a verse link. To be overridden by subclasses."""
        return False
    
    def _verse_sort_key(self, url: str) -> tuple:
        """Generate sort key for verse URLs. To be overridden by subclasses."""
        return (0,)
    
    def get_metadata(self) -> TextMetadata:
        """Get metadata for the scraped text."""
        return TextMetadata(
            text_name=self.text_name,
            text_abbreviation=self.text_abbreviation,
            total_chapters=self.expected_chapters,
            total_verses=len(self.scraped_verses),
            source_url=self.base_url + self.text_abbreviation.lower() + "/"
        )
    
    def save_results(self, output_file: str):
        """Save scraped results to JSON file."""
        results = {
            'metadata': self.get_metadata().to_dict(),
            'verses': [verse.to_dict() for verse in self.scraped_verses],
            'failed_urls': self.failed_urls,
            'stats': {
                'total_verses_scraped': len(self.scraped_verses),
                'total_failed': len(self.failed_urls),
                'success_rate': len(self.scraped_verses) / (len(self.scraped_verses) + len(self.failed_urls)) if (len(self.scraped_verses) + len(self.failed_urls)) > 0 else 0
            }
        }
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {output_path}")


class BhagavadGitaScraper(VedabaseScraperBase):
    """Specialized scraper for Bhagavad Gita from vedabase.io."""
    
    def __init__(self, config: Optional[ScrapingConfig] = None):
        super().__init__(config)
        self.text_abbreviation = "BG"
        self.text_name = "Bhagavad Gita As It Is"
        self.expected_chapters = 18
        
        # Expected verse counts per chapter for validation
        self.expected_verse_counts = {
            1: 47, 2: 72, 3: 43, 4: 42, 5: 29, 6: 47, 7: 30, 8: 28,
            9: 34, 10: 42, 11: 55, 12: 20, 13: 35, 14: 27, 15: 20,
            16: 24, 17: 28, 18: 78
        }
    
    def _extract_verse_content(self, soup: BeautifulSoup, url: str) -> VerseContent:
        """Extract Bhagavad Gita verse content."""
        content = VerseContent(verse_reference="")  # Initialize with empty reference
        
        try:
            # Extract verse number from h1 tag (e.g., "Bg. 1.1" or "Bg. 1.16-18")
            title = soup.find('h1')
            if title:
                verse_title = title.get_text(strip=True)
                content.verse_reference = verse_title
                
                # Parse individual verse numbers from grouped verses
                if 'Bg.' in verse_title:
                    # Extract the verse part (e.g., "1.16-18" from "Bg. 1.16-18")
                    verse_part = verse_title.replace('Bg.', '').strip()
                    if '-' in verse_part:
                        # Handle grouped verses like "1.16-18"
                        chapter_verse = verse_part.split('.')
                        if len(chapter_verse) == 2:
                            chapter_num = chapter_verse[0]
                            verse_range = chapter_verse[1]
                            if '-' in verse_range:
                                start_verse, end_verse = verse_range.split('-')
                                try:
                                    start = int(start_verse)
                                    end = int(end_verse)
                                    content.verse_numbers = [f"{chapter_num}.{i}" for i in range(start, end + 1)]
                                except ValueError:
                                    content.verse_numbers = [verse_part]
                            else:
                                content.verse_numbers = [verse_part]
                    else:
                        # Single verse
                        content.verse_numbers = [verse_part]
            
            # Extract Sanskrit verse and transliteration
            sanskrit_text = ""
            transliteration_text = ""
            
            # Look for Sanskrit (Devanagari) and Roman transliteration
            for element in soup.find_all(['p', 'div', 'span']):
                text = element.get_text(strip=True)
                
                # Check if text contains Devanagari characters (Sanskrit)
                if any('\u0900' <= char <= '\u097F' for char in text) and len(text) > 20:
                    sanskrit_text = text
                # Check for Roman transliteration (usually follows Sanskrit)
                elif len(text) > 20 and any(word in text.lower() for word in ['dhṛtarāṣṭra', 'uvāca', 'dharma', 'kṣetre', 'kurukṣetre']):
                    transliteration_text = text
            
            content.sanskrit_verse = sanskrit_text
            content.sanskrit_transliteration = transliteration_text
            
            # Extract sections based on headings
            current_section = ""
            sections = {'synonyms': '', 'translation': '', 'purport': ''}
            
            for element in soup.find_all(['h2', 'h3', 'p', 'div']):
                if element.name in ['h2', 'h3']:
                    section_title = element.get_text(strip=True).lower()
                    if 'synonym' in section_title:
                        current_section = 'synonyms'
                    elif 'translation' in section_title:
                        current_section = 'translation'
                    elif 'purport' in section_title:
                        current_section = 'purport'
                    else:
                        current_section = ""
                elif current_section and element.name in ['p', 'div']:
                    text = element.get_text(strip=True)
                    if text and len(text) > 10:  # Avoid empty or very short text
                        if sections[current_section]:
                            sections[current_section] += " " + text
                        else:
                            sections[current_section] = text
            
            content.synonyms = sections['synonyms']
            content.translation = sections['translation']
            content.purport = sections['purport']
            
            # Fallback method if sections are empty
            if not any([content.translation, content.purport]):
                # Look for longer paragraphs that might contain the content
                paragraphs = soup.find_all('p')
                long_paragraphs = [p.get_text(strip=True) for p in paragraphs 
                                 if len(p.get_text(strip=True)) > 100]
                
                if long_paragraphs:
                    # First long paragraph is likely translation
                    if len(long_paragraphs) >= 1:
                        content.translation = long_paragraphs[0]
                    # Subsequent paragraphs are likely purport
                    if len(long_paragraphs) >= 2:
                        content.purport = " ".join(long_paragraphs[1:])
                        
        except Exception as e:
            logger.error(f"Error extracting BG verse content: {e}")
        
        return content
    
    def _is_verse_link(self, href: str, chapter_url: str) -> bool:
        """Check if href is a BG verse link."""
        # Extract chapter number from chapter_url
        chapter_match = re.search(r'/bg/(\d+)/', chapter_url)
        if not chapter_match:
            return False
        
        chapter_num = chapter_match.group(1)
        
        # Check if this is a verse link for this chapter
        return f'/library/bg/{chapter_num}/' in href and href.endswith('/') and '/advanced' not in href
    
    def _verse_sort_key(self, url: str) -> tuple:
        """Generate sort key for BG verse URLs."""
        # Extract verse numbers from URL for sorting
        match = re.search(r'/bg/(\d+)/(\d+(?:-\d+)?)', url)
        if match:
            chapter = int(match.group(1))
            verse_part = match.group(2)
            if '-' in verse_part:
                verse_start = int(verse_part.split('-')[0])
            else:
                verse_start = int(verse_part)
            return (chapter, verse_start)
        return (0, 0)
    
    async def scrape_all_chapters(self) -> List[VerseContent]:
        """Scrape all 18 chapters of Bhagavad Gita."""
        logger.info("Starting Bhagavad Gita scraping")
        all_verses = []
        
        for chapter_num in range(1, self.expected_chapters + 1):
            chapter_url = f"{self.base_url}bg/{chapter_num}/"
            
            if self.config.progress_callback:
                self.config.progress_callback(
                    f"Scraping Bhagavad Gita Chapter {chapter_num}",
                    chapter_num,
                    self.expected_chapters
                )
            
            chapter_verses = await self.scrape_chapter(chapter_url, chapter_num)
            all_verses.extend(chapter_verses)
            
            # Validate verse count
            expected_count = self.expected_verse_counts.get(chapter_num, 0)
            actual_count = len(chapter_verses)
            
            if actual_count != expected_count:
                logger.warning(f"Chapter {chapter_num}: Expected {expected_count} verses, got {actual_count}")
            else:
                logger.info(f"Chapter {chapter_num}: Successfully scraped {actual_count} verses")
        
        self.scraped_verses = all_verses
        logger.info(f"Bhagavad Gita scraping complete: {len(all_verses)} verses total")
        return all_verses


class SriIsopanisadScraper(VedabaseScraperBase):
    """Specialized scraper for Sri Isopanisad from vedabase.io."""
    
    def __init__(self, config: Optional[ScrapingConfig] = None):
        super().__init__(config)
        self.text_abbreviation = "ISO"
        self.text_name = "Sri Isopanisad"
        self.expected_chapters = 1  # Single text with mantras
        self.expected_mantras = 19  # 1 invocation + 18 mantras
    
    def _extract_verse_content(self, soup: BeautifulSoup, url: str) -> VerseContent:
        """Extract Sri Isopanisad mantra content."""
        content = VerseContent(verse_reference="")  # Initialize with empty reference
        
        try:
            # Extract mantra number from h1 tag (e.g., "Iso 1" or "Iso Invocation")
            title = soup.find('h1')
            if title:
                title_text = title.get_text(strip=True)
                content.verse_reference = title_text
                
                # Parse mantra number
                if 'Iso' in title_text:
                    mantra_part = title_text.replace('Iso', '').strip()
                    if mantra_part.isdigit():
                        content.verse_numbers = [mantra_part]
                    elif 'Invocation' in mantra_part:
                        content.verse_numbers = ['Invocation']
                    else:
                        content.verse_numbers = [mantra_part]
            
            # Extract Sanskrit mantra and transliteration
            sanskrit_text = ""
            transliteration_text = ""
            
            # Look for Sanskrit (Devanagari) and Roman transliteration
            for element in soup.find_all(['p', 'div', 'span']):
                text = element.get_text(strip=True)
                
                # Check if text contains Devanagari characters (Sanskrit)
                if any('\u0900' <= char <= '\u097F' for char in text) and len(text) > 10:
                    sanskrit_text = text
                # Check for Roman transliteration patterns
                elif len(text) > 10 and any(word in text.lower() for word in ['īśāvāsyam', 'oṁ', 'śānti', 'pūrṇam']):
                    transliteration_text = text
            
            content.sanskrit_verse = sanskrit_text
            content.sanskrit_transliteration = transliteration_text
            
            # Extract sections
            current_section = ""
            sections = {'synonyms': '', 'translation': '', 'purport': ''}
            
            for element in soup.find_all(['h2', 'h3', 'p', 'div']):
                if element.name in ['h2', 'h3']:
                    section_title = element.get_text(strip=True).lower()
                    if 'synonym' in section_title:
                        current_section = 'synonyms'
                    elif 'translation' in section_title:
                        current_section = 'translation'
                    elif 'purport' in section_title:
                        current_section = 'purport'
                    else:
                        current_section = ""
                elif current_section and element.name in ['p', 'div']:
                    text = element.get_text(strip=True)
                    if text and len(text) > 10:
                        if sections[current_section]:
                            sections[current_section] += " " + text
                        else:
                            sections[current_section] = text
            
            content.synonyms = sections['synonyms']
            content.translation = sections['translation']
            content.purport = sections['purport']
            
        except Exception as e:
            logger.error(f"Error extracting ISO mantra content: {e}")
        
        return content
    
    def _is_verse_link(self, href: str, chapter_url: str) -> bool:
        """Check if href is an ISO mantra link."""
        return '/library/iso/' in href and href.endswith('/') and '/advanced' not in href
    
    def _verse_sort_key(self, url: str) -> tuple:
        """Generate sort key for ISO mantra URLs."""
        # Handle invocation first, then numbered mantras
        if 'invocation' in url.lower():
            return (0, 0)
        
        match = re.search(r'/iso/(\d+)', url)
        if match:
            mantra_num = int(match.group(1))
            return (1, mantra_num)
        return (2, 0)
    
    async def scrape_all_mantras(self) -> List[VerseContent]:
        """Scrape all mantras of Sri Isopanisad."""
        logger.info("Starting Sri Isopanisad scraping")
        
        base_iso_url = f"{self.base_url}iso/"
        all_mantras = await self.scrape_chapter(base_iso_url, 1)
        
        # Validate mantra count
        actual_count = len(all_mantras)
        if actual_count != self.expected_mantras:
            logger.warning(f"Expected {self.expected_mantras} mantras, got {actual_count}")
        else:
            logger.info(f"Successfully scraped {actual_count} mantras")
        
        self.scraped_verses = all_mantras
        logger.info(f"Sri Isopanisad scraping complete: {len(all_mantras)} mantras total")
        return all_mantras


# Convenience functions for direct usage

async def scrape_bhagavad_gita(
    output_file: str = "bhagavad_gita_scraped.json",
    config: Optional[ScrapingConfig] = None,
    progress_callback: Optional[callable] = None
) -> List[VerseContent]:
    """
    Convenience function to scrape complete Bhagavad Gita.
    
    Args:
        output_file: Path to save JSON results
        config: Custom scraping configuration
        progress_callback: Optional progress callback function
        
    Returns:
        List of scraped verse content
    """
    if config and progress_callback:
        config.progress_callback = progress_callback
    
    async with BhagavadGitaScraper(config) as scraper:
        verses = await scraper.scrape_all_chapters()
        scraper.save_results(output_file)
        return verses


async def scrape_sri_isopanisad(
    output_file: str = "sri_isopanisad_scraped.json",
    config: Optional[ScrapingConfig] = None,
    progress_callback: Optional[callable] = None
) -> List[VerseContent]:
    """
    Convenience function to scrape complete Sri Isopanisad.
    
    Args:
        output_file: Path to save JSON results
        config: Custom scraping configuration
        progress_callback: Optional progress callback function
        
    Returns:
        List of scraped mantra content
    """
    if config and progress_callback:
        config.progress_callback = progress_callback
    
    async with SriIsopanisadScraper(config) as scraper:
        mantras = await scraper.scrape_all_mantras()
        scraper.save_results(output_file)
        return mantras


# Example usage
if __name__ == "__main__":
    async def main():
        # Configure for testing
        config = ScrapingConfig(
            requests_per_second=1.0,
            timeout=15,
            progress_callback=lambda msg, curr, total: print(f"{msg} ({curr}/{total})")
        )
        
        # Test Bhagavad Gita scraping (just first chapter for testing)
        print("Testing Bhagavad Gita scraper...")
        bg_scraper = BhagavadGitaScraper(config)
        async with bg_scraper:
            # Test scraping just chapter 1
            chapter_1_url = f"{bg_scraper.base_url}bg/1/"
            chapter_verses = await bg_scraper.scrape_chapter(chapter_1_url, 1)
            print(f"Chapter 1 scraped: {len(chapter_verses)} verses")
            
            if chapter_verses:
                # Show first verse as example
                first_verse = chapter_verses[0]
                print(f"First verse: {first_verse.verse_reference}")
                print(f"Translation length: {len(first_verse.translation)}")
        
        print("\nTesting Sri Isopanisad scraper...")
        iso_scraper = SriIsopanisadScraper(config)
        async with iso_scraper:
            # Test scraping invocation
            iso_url = f"{iso_scraper.base_url}iso/invocation/"
            invocation = await iso_scraper.scrape_verse(iso_url)
            if invocation:
                print(f"Invocation scraped: {invocation.verse_reference}")
                print(f"Translation length: {len(invocation.translation)}")
    
    # Run the test
    asyncio.run(main())
