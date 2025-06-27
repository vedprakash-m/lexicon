"""
Srimad-Bhagavatam Text Scraper

This script scrapes the complete text of the Srimad-Bhagavatam from vedabase.io
for use in an AI agent application. It extracts all verses, translations,
and purports from all 12 cantos.

Author: Ved Mishra
Date: June 24, 2025
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
import logging
from typing import Dict, List, Optional
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('srimad_bhagavatam_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SrimadBhagavatamScraper:
    """Scraper for extracting Srimad-Bhagavatam text from vedabase.io"""
    
    def __init__(self, enable_parallel=True, max_workers=4):
        self.base_url = "https://vedabase.io/en/library/sb/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.cantos_data = {}
        self.delay = 1  # Delay between requests in seconds
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delays = [2, 5, 10]  # Progressive delays in seconds
        
        # Threading configuration
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers
        self.rate_limiter_lock = threading.Lock()
        self.last_request_time = 0
        
        # Tracking and validation
        self.expected_cantos = 12
        # Approximate chapter counts for each canto (will be discovered dynamically)
        self.expected_chapter_counts = {
            1: 19, 2: 10, 3: 33, 4: 31, 5: 26, 6: 19, 
            7: 15, 8: 24, 9: 24, 10: 90, 11: 31, 12: 13
        }
        self.scraped_urls = set()  # Track what we've scraped
        self.failed_urls = set()   # Track failed URLs
        self.validation_errors = []  # Track validation issues
        
        # Progress tracking
        self.progress_lock = threading.Lock()
        self.total_progress = {'chapters': 0, 'verses': 0}
        self.completed_progress = {'chapters': 0, 'verses': 0}
    
    def get_page_content(self, url: str, is_verse_check: bool = False) -> Optional[BeautifulSoup]:
        """Fetch and parse a webpage with retry mechanism and thread-safe rate limiting"""
        
        # Thread-safe rate limiting
        with self.rate_limiter_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.delay:
                sleep_time = self.delay - time_since_last + random.uniform(0.1, 0.3)  # Add small random delay
                time.sleep(sleep_time)
            self.last_request_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching: {url} (attempt {attempt + 1}/{self.max_retries})")
                response = self.session.get(url, timeout=15)
                
                # For verse checks, don't retry on 404 - the verse simply doesn't exist
                if response.status_code == 404 and is_verse_check:
                    logger.debug(f"Verse not found (404): {url}")
                    return None
                
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Quick sanity check - ensure we got actual content
                if soup.find('body') and len(soup.get_text(strip=True)) > 100:
                    return soup
                else:
                    raise requests.RequestException(f"Page appears to be empty or invalid: {len(soup.get_text())}")
                    
            except requests.RequestException as e:
                # Don't retry 404s for verse checks
                if "404" in str(e) and is_verse_check:
                    logger.debug(f"Verse not found: {url}")
                    return None
                
                if attempt < self.max_retries - 1:
                    retry_delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    logger.warning(f"Error fetching {url} (attempt {attempt + 1}): {e}")
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts: {e}")
        
        return None
    
    def discover_cantos(self) -> List[Dict]:
        """Discover all cantos from the main Srimad-Bhagavatam page"""
        logger.info("Discovering cantos from main page")
        
        soup = self.get_page_content(self.base_url)
        if not soup:
            logger.error("Failed to load main Srimad-Bhagavatam page")
            return []
        
        cantos = []
        
        # Look for canto links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Check if this is a canto link
            if '/library/sb/' in href and '/library/sb/' in href and text.startswith('Canto'):
                # Extract canto number and title
                if 'Canto' in text:
                    try:
                        # Parse "Canto 1: Creation" format
                        parts = text.split(':', 1)
                        if len(parts) == 2:
                            canto_part = parts[0].strip()
                            title_part = parts[1].strip()
                            canto_num = int(canto_part.replace('Canto', '').strip())
                            
                            full_url = f"https://vedabase.io{href}" if href.startswith('/') else href
                            
                            cantos.append({
                                'number': canto_num,
                                'title': text,
                                'short_title': title_part,
                                'url': full_url
                            })
                    except (ValueError, IndexError):
                        logger.warning(f"Could not parse canto from: {text}")
                        continue
        
        # Sort by canto number
        cantos.sort(key=lambda x: x['number'])
        
        logger.info(f"Discovered {len(cantos)} cantos")
        for canto in cantos:
            logger.info(f"  - Canto {canto['number']}: {canto['short_title']}")
        
        return cantos
    
    def discover_chapters(self, canto_num: int, canto_url: str) -> List[Dict]:
        """Discover all chapters in a canto"""
        logger.info(f"Discovering chapters for Canto {canto_num}")
        
        soup = self.get_page_content(canto_url)
        if not soup:
            logger.error(f"Failed to load canto {canto_num} page")
            return []
        
        chapters = []
        
        # Look for chapter links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Check if this is a chapter link for this canto
            # The pattern should be /library/sb/{canto_num}/{chapter_num}/
            if f'/library/sb/{canto_num}/' in href and href.count('/') >= 5:
                # Extract the chapter number from the URL
                url_parts = href.rstrip('/').split('/')
                
                try:
                    # Find the canto number index and get the next part (chapter number)
                    canto_index = url_parts.index(str(canto_num))
                    if canto_index + 1 < len(url_parts):
                        chapter_part = url_parts[canto_index + 1]
                        
                        # Try to parse as a number (for numeric chapters like "1", "2", etc.)
                        try:
                            chapter_num = int(chapter_part)
                            
                            # Extract title from link text
                            chapter_title = text if text else f"Chapter {chapter_num}"
                            
                            full_url = f"https://vedabase.io{href}" if href.startswith('/') else href
                            
                            # Only add if we haven't seen this chapter number before
                            if not any(ch['number'] == chapter_num for ch in chapters):
                                chapters.append({
                                    'number': chapter_num,
                                    'title': chapter_title,
                                    'short_title': chapter_title,
                                    'url': full_url,
                                    'canto': canto_num
                                })
                            
                        except ValueError:
                            # For non-numeric chapters like "preface", "introduction", skip them for now
                            # We're focused on the numbered chapters with verses
                            if chapter_part.lower() in ['preface', 'introduction', 'dedication']:
                                logger.info(f"Skipping non-verse chapter: {chapter_part}")
                                continue
                            else:
                                logger.debug(f"Skipping non-numeric chapter: {chapter_part}")
                                continue
                                
                except (ValueError, IndexError):
                    continue
        
        # If no chapters found using links, try to construct them manually
        if not chapters:
            logger.info(f"No chapters found via links for Canto {canto_num}, trying manual construction")
            expected_count = self.expected_chapter_counts.get(canto_num, 20)
            
            for chapter_num in range(1, min(expected_count + 1, 25)):  # Limit to avoid too many requests
                chapter_url = f"https://vedabase.io/en/library/sb/{canto_num}/{chapter_num}/"
                
                # Test if this chapter exists by trying to fetch it
                test_soup = self.get_page_content(chapter_url)
                if test_soup and test_soup.find('h1'):
                    chapters.append({
                        'number': chapter_num,
                        'title': f"Canto {canto_num}, Chapter {chapter_num}",
                        'short_title': f"Chapter {chapter_num}",
                        'url': chapter_url,
                        'canto': canto_num
                    })
                    logger.info(f"Found chapter {canto_num}.{chapter_num} via manual construction")
                else:
                    # If we hit a non-existent chapter, we're probably done
                    logger.info(f"Chapter {canto_num}.{chapter_num} not found, stopping manual discovery")
                    break
        
        # Sort by chapter number
        chapters.sort(key=lambda x: x['number'])
        
        logger.info(f"Discovered {len(chapters)} chapters in Canto {canto_num}")
        
        return chapters
    
    def discover_verse_urls(self, canto_num: int, chapter_num: int, chapter_url: str) -> List[str]:
        """Discover all verse URLs for a chapter"""
        logger.info(f"Discovering verse URLs for Canto {canto_num}, Chapter {chapter_num}")
        
        soup = self.get_page_content(chapter_url)
        if not soup:
            logger.error(f"Failed to load chapter {canto_num}.{chapter_num}")
            return []
        
        verse_urls = []
        
        # Look for verse links - these should be 3-level deep
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            
            # Check if this is a verse link for this chapter
            # Pattern should be: /library/sb/{canto_num}/{chapter_num}/{verse_num}/
            if f'/library/sb/{canto_num}/{chapter_num}/' in href and href.endswith('/'):
                # Extract the verse part from the URL
                url_parts = href.split('/')
                
                try:
                    # Find the chapter number index and get the next part (verse number)
                    chapter_index = None
                    for i, part in enumerate(url_parts):
                        if part == str(chapter_num) and i > 0 and url_parts[i-1] == str(canto_num):
                            chapter_index = i
                            break
                    
                    if chapter_index is not None and chapter_index + 1 < len(url_parts):
                        verse_part = url_parts[chapter_index + 1]
                        
                        # Skip empty parts and non-verse parts
                        if verse_part and verse_part != '' and not verse_part.startswith('advanced'):
                            # Verify this looks like a verse number (number or number range)
                            if verse_part.replace('-', '').isdigit() or verse_part.isdigit():
                                full_url = f"https://vedabase.io{href}"
                                if full_url not in verse_urls:
                                    verse_urls.append(full_url)
                except (ValueError, IndexError):
                    continue
        
        # Remove duplicates and sort
        verse_urls = list(set(verse_urls))
        verse_urls.sort(key=lambda x: self._extract_verse_sort_key(x))
        
        logger.info(f"Found {len(verse_urls)} verse URLs for Canto {canto_num}, Chapter {chapter_num}")
        
        # If no verse URLs found, try manual construction
        if not verse_urls:
            logger.info("No verse URLs found via links, trying manual construction")
            for verse_num in range(1, 50):  # Try first 50 verses
                test_url = f"https://vedabase.io/en/library/sb/{canto_num}/{chapter_num}/{verse_num}/"
                
                # Quick test to see if this URL exists (just check if we get a valid response)
                try:
                    test_response = self.session.head(test_url, timeout=5)
                    if test_response.status_code == 200:
                        verse_urls.append(test_url)
                        logger.debug(f"Found verse {canto_num}.{chapter_num}.{verse_num} via manual check")
                    elif test_response.status_code == 404:
                        # If we get 404, this verse doesn't exist, stop trying
                        break
                except Exception:
                    # If we get any error, stop trying
                    break
        
        return verse_urls
    
    def _extract_verse_sort_key(self, url: str):
        """Extract a sort key from verse URL for proper ordering"""
        try:
            # Extract verse part from URL like .../sb/1/1/ or .../sb/1/1/1-2/
            parts = url.rstrip('/').split('/')
            verse_part = parts[-1]
            
            if '-' in verse_part:
                # For grouped verses like "1-2", use the first number
                return int(verse_part.split('-')[0])
            else:
                return int(verse_part)
        except (ValueError, IndexError):
            return 999  # Put unparseable URLs at the end
    
    def extract_verse_content(self, soup: BeautifulSoup) -> Dict:
        """Extract verse content from a page"""
        content = {
            'verse_number': '',
            'verse_numbers': [],  # For grouped verses like 1-2
            'sanskrit_verse': '',           # Part 1: Sanskrit text
            'sanskrit_transliteration': '', # Part 1: Roman transliteration 
            'synonyms': '',                 # Part 2: Word-by-word meanings
            'translation': '',              # Part 3: Complete translation
            'purport': ''                   # Part 4: Commentary/explanation
        }
        
        try:
            # Extract verse number from h1 tag (e.g., "SB 1.1.1" or "SB 1.1.1-2")
            title = soup.find('h1')
            if title:
                verse_title = title.get_text(strip=True)
                content['verse_number'] = verse_title
                
                # Parse individual verse numbers from grouped verses
                if 'SB' in verse_title:
                    # Extract the verse part (e.g., "1.1.1-2" from "SB 1.1.1-2")
                    verse_part = verse_title.replace('SB', '').strip()
                    if '-' in verse_part:
                        # Handle grouped verses like "1.1.1-2"
                        parts = verse_part.split('.')
                        if len(parts) == 3:
                            canto_num = parts[0]
                            chapter_num = parts[1]
                            verse_range = parts[2]
                            if '-' in verse_range:
                                start_verse, end_verse = verse_range.split('-')
                                try:
                                    start = int(start_verse)
                                    end = int(end_verse)
                                    content['verse_numbers'] = [f"{canto_num}.{chapter_num}.{i}" for i in range(start, end + 1)]
                                except ValueError:
                                    content['verse_numbers'] = [verse_part]
                            else:
                                content['verse_numbers'] = [verse_part]
                    else:
                        # Single verse
                        content['verse_numbers'] = [verse_part]
            
            # Extract Sanskrit verse and transliteration
            sanskrit_text = ""
            transliteration_text = ""
            
            # Look for Sanskrit (Devanagari) and Roman transliteration
            for element in soup.find_all(['p', 'div', 'span']):
                text = element.get_text(strip=True)
                
                # Check if text contains Devanagari characters (Sanskrit)
                if any('\u0900' <= char <= '\u097F' for char in text) and len(text) > 20:
                    sanskrit_text = text
                # Check for Roman transliteration
                elif len(text) > 20 and any(char in text for char in ['ā', 'ī', 'ū', 'ṛ', 'ṅ', 'ñ', 'ṭ', 'ḍ', 'ṇ', 'ś', 'ṣ']):
                    if not sanskrit_text or sanskrit_text not in text:
                        transliteration_text = text
            
            content['sanskrit_verse'] = sanskrit_text
            content['sanskrit_transliteration'] = transliteration_text
            
            # Extract sections based on h2/h3 headings
            current_section = ""
            sections = {'synonyms': '', 'translation': '', 'purport': ''}
            
            for element in soup.find_all(['h2', 'h3', 'p', 'div']):
                if element.name in ['h2', 'h3']:
                    section_title = element.get_text(strip=True).lower()
                    if 'synonym' in section_title or 'word for word' in section_title:
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
            
            content['synonyms'] = sections['synonyms']
            content['translation'] = sections['translation']
            content['purport'] = sections['purport']
            
            # Fallback method if sections are empty
            if not any([content['translation'], content['purport']]):
                # Look for longer paragraphs that might contain the content
                paragraphs = soup.find_all('p')
                long_paragraphs = [p.get_text(strip=True) for p in paragraphs 
                                 if len(p.get_text(strip=True)) > 100]
                
                if long_paragraphs:
                    # First long paragraph is likely translation
                    if len(long_paragraphs) >= 1:
                        content['translation'] = long_paragraphs[0]
                    # Subsequent paragraphs are likely purport
                    if len(long_paragraphs) >= 2:
                        content['purport'] = " ".join(long_paragraphs[1:])
                        
        except Exception as e:
            logger.error(f"Error extracting verse content: {e}")
        
        return content
    
    def scrape_chapter(self, canto_num: int, chapter_num: int, chapter_url: str) -> Dict:
        """Scrape all verses from a chapter"""
        logger.info(f"Scraping Canto {canto_num}, Chapter {chapter_num}")
        
        chapter_data = {
            'canto_number': canto_num,
            'chapter_number': chapter_num,
            'title': f"Canto {canto_num}, Chapter {chapter_num}",
            'verses': []
        }
        
        # Get the chapter page to extract the title
        soup = self.get_page_content(chapter_url)
        
        if not soup:
            logger.error(f"Failed to load chapter {canto_num}.{chapter_num}")
            return chapter_data
        
        # Extract chapter title if available
        title_elem = soup.find('h1') or soup.find('title')
        if title_elem:
            chapter_data['title'] = title_elem.get_text(strip=True)
        
        # Discover all verse URLs for this chapter
        verse_urls = self.discover_verse_urls(canto_num, chapter_num, chapter_url)
        
        if not verse_urls:
            logger.warning(f"No verse URLs found for Canto {canto_num}, Chapter {chapter_num}")
            
            # Try manual construction of verse URLs
            logger.info(f"Attempting manual verse URL construction for Canto {canto_num}, Chapter {chapter_num}")
            consecutive_failures = 0
            max_failures = 10  # Allow gaps in verse numbering
            
            for verse_num in range(1, 100):  # Try up to 100 verses
                verse_url = f"https://vedabase.io/en/library/sb/{canto_num}/{chapter_num}/{verse_num}/"
                
                verse_soup = self.get_page_content(verse_url, is_verse_check=True)
                if verse_soup and verse_soup.find('h1'):
                    verse_urls.append(verse_url)
                    consecutive_failures = 0  # Reset on success
                    logger.info(f"Found verse {canto_num}.{chapter_num}.{verse_num} via manual construction")
                else:
                    consecutive_failures += 1
                    # If we hit too many consecutive non-existent verses, we're probably done
                    if consecutive_failures >= max_failures:
                        logger.info(f"Stopped after {max_failures} consecutive missing verses")
                        break
            
            if not verse_urls:
                logger.warning(f"No verses found for Canto {canto_num}, Chapter {chapter_num}")
                return chapter_data
        
        # Scrape each verse URL
        for verse_url in verse_urls:
            try:
                verse_soup = self.get_page_content(verse_url)
                
                if verse_soup:
                    verse_content = self.extract_verse_content(verse_soup)
                    
                    # Validate the content
                    if self.validate_verse_content(verse_content, verse_url):
                        chapter_data['verses'].append(verse_content)
                        self.scraped_urls.add(verse_url)
                        
                        if verse_content['verse_numbers']:
                            verse_desc = ", ".join(verse_content['verse_numbers'])
                        else:
                            verse_desc = verse_content['verse_number']
                        
                        logger.info(f"Scraped verse(s) {verse_desc}")
                    else:
                        logger.warning(f"Validation failed for {verse_url}")
                        self.failed_urls.add(verse_url)
                else:
                    logger.warning(f"Failed to scrape verse from {verse_url}")
                    self.failed_urls.add(verse_url)
            except Exception as e:
                logger.error(f"Error scraping {verse_url}: {e}")
                self.failed_urls.add(verse_url)
        
        logger.info(f"Completed Canto {canto_num}, Chapter {chapter_num} - {len(chapter_data['verses'])} verses")
        
        return chapter_data
    
    def scrape_chapter_parallel(self, chapter_info: Dict) -> Dict:
        """Scrape a single chapter - designed for parallel execution"""
        canto_num = chapter_info['canto']
        chapter_num = chapter_info['number']
        chapter_url = chapter_info['url']
        start_verse = chapter_info.get('start_verse', 1)
        
        try:
            logger.info(f"[Thread] Starting Canto {canto_num}, Chapter {chapter_num}")
            
            chapter_data = {
                'canto_number': canto_num,
                'chapter_number': chapter_num,
                'title': f"Canto {canto_num}, Chapter {chapter_num}",
                'verses': []
            }
            
            # Get the chapter page to extract the title
            soup = self.get_page_content(chapter_url)
            
            if soup:
                title_elem = soup.find('h1') or soup.find('title')
                if title_elem:
                    chapter_data['title'] = title_elem.get_text(strip=True)
            
            # Scrape verses with parallel capability
            if self.enable_parallel and self.max_workers > 1:
                verses = self.scrape_verses_parallel(canto_num, chapter_num, start_verse)
            else:
                verses = self.scrape_verses_sequential(canto_num, chapter_num, start_verse)
            
            chapter_data['verses'] = verses
            
            # Update progress
            with self.progress_lock:
                self.completed_progress['chapters'] += 1
                self.completed_progress['verses'] += len(verses)
            
            logger.info(f"[Thread] Completed Canto {canto_num}, Chapter {chapter_num} - {len(verses)} verses")
            return chapter_data
            
        except Exception as e:
            logger.error(f"[Thread] Error scraping canto {canto_num}, chapter {chapter_num}: {e}")
            return {
                'canto_number': canto_num,
                'chapter_number': chapter_num,
                'title': f"Canto {canto_num}, Chapter {chapter_num}",
                'verses': []
            }
    
    def scrape_verses_parallel(self, canto_num: int, chapter_num: int, start_verse: int = 1) -> List[Dict]:
        """Scrape verses in parallel for a chapter"""
        verses = []
        
        # First, determine the range of verses that might exist
        verse_urls = []
        consecutive_failures = 0
        max_failures = 10
        
        # Build list of potential verse URLs
        for verse_num in range(start_verse, start_verse + 50):  # Try up to 50 verses from start
            verse_url = f"https://vedabase.io/en/library/sb/{canto_num}/{chapter_num}/{verse_num}/"
            verse_urls.append((verse_num, verse_url))
        
        # Use ThreadPoolExecutor to scrape verses in parallel
        with ThreadPoolExecutor(max_workers=min(3, self.max_workers)) as executor:
            # Submit all verse scraping tasks
            future_to_verse = {
                executor.submit(self.scrape_verse_url, url, verse_num): (verse_num, url)
                for verse_num, url in verse_urls
            }
            
            # Collect results as they complete
            verse_results = {}
            for future in as_completed(future_to_verse):
                verse_num, url = future_to_verse[future]
                try:
                    verse_content = future.result()
                    if verse_content:
                        verse_results[verse_num] = verse_content
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= max_failures:
                            # Cancel remaining futures
                            for remaining_future in future_to_verse:
                                if not remaining_future.done():
                                    remaining_future.cancel()
                            break
                except Exception as e:
                    logger.error(f"Error scraping verse {verse_num}: {e}")
                    consecutive_failures += 1
        
        # Sort verses by verse number and return
        for verse_num in sorted(verse_results.keys()):
            verses.append(verse_results[verse_num])
        
        return verses
    
    def scrape_verses_sequential(self, canto_num: int, chapter_num: int, start_verse: int = 1) -> List[Dict]:
        """Scrape verses sequentially for a chapter (fallback method)"""
        verses = []
        verse_num = start_verse
        consecutive_failures = 0
        max_failures = 10
        
        while consecutive_failures < max_failures:
            verse_url = f"https://vedabase.io/en/library/sb/{canto_num}/{chapter_num}/{verse_num}/"
            verse_content = self.scrape_verse_url(verse_url, verse_num)
            
            if verse_content:
                verses.append(verse_content)
                consecutive_failures = 0
            else:
                consecutive_failures += 1
            
            verse_num += 1
        
        return verses
    
    def scrape_canto(self, canto_num: int, canto_url: str) -> Dict:
        """Scrape all chapters from a canto"""
        logger.info(f"Scraping Canto {canto_num}")
        
        canto_data = {
            'canto_number': canto_num,
            'title': f"Canto {canto_num}",
            'chapters': {}
        }
        
        # Discover all chapters in this canto
        chapters = self.discover_chapters(canto_num, canto_url)
        
        if not chapters:
            logger.warning(f"No chapters found for Canto {canto_num}")
            return canto_data
        
        # Extract canto title from first chapter if available
        if chapters:
            first_chapter = chapters[0]
            soup = self.get_page_content(first_chapter['url'])
            if soup:
                # Look for canto title
                for element in soup.find_all(['h1', 'h2', 'title']):
                    text = element.get_text(strip=True)
                    if f'Canto {canto_num}' in text:
                        canto_data['title'] = text
                        break
        
        # Update total progress
        with self.progress_lock:
            self.total_progress['chapters'] += len(chapters)
        
        logger.info(f"Found {len(chapters)} chapters in Canto {canto_num}, processing in parallel...")
        
        # Always use parallel processing for this method
        if len(chapters) > 1:
            # Scrape chapters in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all chapter scraping tasks
                future_to_chapter = {
                    executor.submit(self.scrape_chapter_parallel, chapter): chapter
                    for chapter in chapters
                }
                
                # Collect results as they complete
                completed_chapters = 0
                for future in as_completed(future_to_chapter):
                    chapter = future_to_chapter[future]
                    try:
                        chapter_data = future.result()
                        canto_data['chapters'][chapter_data['chapter_number']] = chapter_data
                        completed_chapters += 1
                        
                        logger.info(f"Completed chapter {chapter_data['chapter_number']} ({completed_chapters}/{len(chapters)})")
                        
                        # Save progress incrementally
                        self.save_individual_canto(canto_num, canto_data)
                        
                    except Exception as e:
                        logger.error(f"Error in parallel chapter scraping for {chapter['number']}: {e}")
        else:
            # Single chapter - still use the parallel chapter method for consistency
            chapter = chapters[0]
            try:
                chapter_info = dict(chapter)
                chapter_data = self.scrape_chapter_parallel(chapter_info)
                canto_data['chapters'][chapter_data['chapter_number']] = chapter_data
                
                # Save progress incrementally
                self.save_individual_canto(canto_num, canto_data)
                
            except Exception as e:
                logger.error(f"Error scraping chapter {chapter['number']}: {e}")
        
        logger.info(f"Completed Canto {canto_num} (parallel) - {len(canto_data['chapters'])} chapters")
        return canto_data

    def scrape_canto_parallel(self, canto_num: int, canto_url: str) -> Dict:
        """Alias for scrape_canto method which is already parallel-enabled"""
        return self.scrape_canto(canto_num, canto_url)

    def load_existing_data(self):
        """Load existing scraped data to enable resume functionality"""
        logger.info("Loading existing data for resume functionality")
        
        try:
            # Try to load the complete file first
            complete_file = 'data_sb/raw/srimad_bhagavatam_complete.json'
            if os.path.exists(complete_file):
                with open(complete_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert string keys back to integers
                    self.cantos_data = {int(k): v for k, v in data.items()}
                    logger.info(f"Loaded complete data with {len(self.cantos_data)} cantos")
                    return
            
            # If complete file doesn't exist, load individual canto files
            cantos_dir = 'data_sb/raw/cantos'
            if os.path.exists(cantos_dir):
                for filename in os.listdir(cantos_dir):
                    if filename.startswith('canto_') and filename.endswith('.json'):
                        try:
                            canto_num = int(filename.replace('canto_', '').replace('.json', ''))
                            with open(os.path.join(cantos_dir, filename), 'r', encoding='utf-8') as f:
                                self.cantos_data[canto_num] = json.load(f)
                            logger.info(f"Loaded Canto {canto_num} from {filename}")
                        except (ValueError, json.JSONDecodeError) as e:
                            logger.warning(f"Failed to load {filename}: {e}")
                
                logger.info(f"Loaded {len(self.cantos_data)} cantos from individual files")
            else:
                logger.info("No existing data found - starting fresh")
                
        except Exception as e:
            logger.error(f"Error loading existing data: {e}")
            logger.info("Starting fresh due to loading error")
    
    def get_resume_point(self) -> tuple:
        """Determine where to resume scraping from"""
        if not self.cantos_data:
            logger.info("No existing data - starting from Canto 1")
            return (1, 1, 1)  # canto, chapter, verse
        
        # Check if we have cantos 1-9 complete, then start from Canto 10
        # Since Canto 10 data was not saved when interrupted, we need to start from Canto 10
        if len(self.cantos_data) == 9 and max(self.cantos_data.keys()) == 9:
            logger.info("Cantos 1-9 complete - Canto 10 data was not saved, starting Canto 10 from the beginning")
            return (10, 1, 1)
        
        # If we have fewer than 9 cantos, continue from where we left off
        if len(self.cantos_data) < 9:
            # Find the last completed canto
            max_canto = max(self.cantos_data.keys())
            last_canto = self.cantos_data[max_canto]
            
            # Check if the last canto is completely finished
            max_chapter = max(int(k) for k in last_canto['chapters'].keys()) if last_canto['chapters'] else 0
            last_chapter = last_canto['chapters'].get(str(max_chapter), {})
            
            # If the last chapter has verses, check the last verse
            if last_chapter.get('verses'):
                last_verse = last_chapter['verses'][-1]
                last_verse_num = last_verse.get('verse_number', '')
                
                # Extract verse number for continuing
                if last_verse_num:
                    try:
                        # Parse something like "SB 10.19.5" or "ŚB 10.19.5" to get the verse number
                        clean_verse = last_verse_num.replace('SB', '').replace('ŚB', '').strip()
                        parts = clean_verse.split('.')
                        if len(parts) >= 3:
                            last_verse_int = int(parts[2].split('-')[0])  # Handle grouped verses like "1-2"
                            resume_point = (max_canto, max_chapter, last_verse_int + 1)
                            logger.info(f"Resume point determined: Canto {max_canto}, Chapter {max_chapter}, Verse {last_verse_int + 1}")
                            return resume_point
                    except ValueError:
                        pass
            
            # If we can't determine exact verse, start from next chapter or canto
            if max_chapter < self.expected_chapter_counts.get(max_canto, 100):
                resume_point = (max_canto, max_chapter + 1, 1)
                logger.info(f"Resume point determined: Canto {max_canto}, Chapter {max_chapter + 1}, Verse 1")
            else:
                resume_point = (max_canto + 1, 1, 1)
                logger.info(f"Resume point determined: Canto {max_canto + 1}, Chapter 1, Verse 1")
            
            return resume_point
        
        # If we have more than 9 cantos, continue from the next incomplete canto
        max_canto = max(self.cantos_data.keys())
        resume_point = (max_canto + 1, 1, 1)
        logger.info(f"Resume point determined: Canto {max_canto + 1}, Chapter 1, Verse 1")
        return resume_point
    
    def scrape_verse_url(self, verse_url: str, expected_verse_num: int = None) -> Optional[Dict]:
        """Scrape a single verse URL and return the content"""
        try:
            verse_soup = self.get_page_content(verse_url, is_verse_check=True)
            
            if verse_soup:
                verse_content = self.extract_verse_content(verse_soup)
                
                # Validate the content
                if self.validate_verse_content(verse_content, verse_url):
                    self.scraped_urls.add(verse_url)
                    
                    if verse_content['verse_numbers']:
                        verse_desc = ", ".join(verse_content['verse_numbers'])
                    else:
                        verse_desc = verse_content['verse_number']
                    
                    logger.info(f"Scraped verse(s) {verse_desc}")
                    return verse_content
                else:
                    logger.warning(f"Validation failed for {verse_url}")
                    self.failed_urls.add(verse_url)
            else:
                # Don't log as failure for 404s - verse simply doesn't exist
                logger.debug(f"Verse does not exist: {verse_url}")
                
        except Exception as e:
            logger.error(f"Error scraping {verse_url}: {e}")
            self.failed_urls.add(verse_url)
        
        return None
    
    def scrape_chapter_from_verse(self, canto_num: int, chapter_num: int, start_verse: int = 1) -> Dict:
        """Scrape a chapter starting from a specific verse number"""
        logger.info(f"Scraping Canto {canto_num}, Chapter {chapter_num} starting from verse {start_verse}")
        
        chapter_data = {
            'canto_number': canto_num,
            'chapter_number': chapter_num,
            'title': f"Canto {canto_num}, Chapter {chapter_num}",
            'verses': []
        }
        
        # Get the chapter page to extract the title
        chapter_url = f"https://vedabase.io/en/library/sb/{canto_num}/{chapter_num}/"
        soup = self.get_page_content(chapter_url)
        
        if soup:
            title_elem = soup.find('h1') or soup.find('title')
            if title_elem:
                chapter_data['title'] = title_elem.get_text(strip=True)
        
        # If we're loading existing data and this chapter exists, merge with existing verses
        if (canto_num in self.cantos_data and 
            chapter_num in self.cantos_data[canto_num]['chapters'] and
            start_verse > 1):
            
            existing_chapter = self.cantos_data[canto_num]['chapters'][chapter_num]
            chapter_data['title'] = existing_chapter.get('title', chapter_data['title'])
            
            # Add existing verses that come before our start_verse
            for verse in existing_chapter['verses']:
                verse_num_str = verse.get('verse_number', '')
                try:
                    # Extract verse number from something like "SB 10.19.5"
                    parts = verse_num_str.replace('SB', '').strip().split('.')
                    if len(parts) >= 3:
                        verse_num = int(parts[2].split('-')[0])
                        if verse_num < start_verse:
                            chapter_data['verses'].append(verse)
                except (ValueError, IndexError):
                    # If we can't parse the verse number, add it anyway
                    chapter_data['verses'].append(verse)
        
        # Try to scrape verses starting from start_verse
        verse_num = start_verse
        consecutive_failures = 0
        max_failures = 10  # Allow more gaps in verse numbering
        total_attempts = 0
        max_attempts = 100  # Safety limit
        
        while consecutive_failures < max_failures and total_attempts < max_attempts:
            verse_url = f"https://vedabase.io/en/library/sb/{canto_num}/{chapter_num}/{verse_num}/"
            
            verse_content = self.scrape_verse_url(verse_url, verse_num)
            
            if verse_content:
                chapter_data['verses'].append(verse_content)
                consecutive_failures = 0  # Reset failure counter on success
                logger.info(f"Successfully scraped verse {canto_num}.{chapter_num}.{verse_num}")
            else:
                consecutive_failures += 1
                logger.debug(f"Verse {canto_num}.{chapter_num}.{verse_num} not found (gap {consecutive_failures}/{max_failures})")
            
            verse_num += 1
            total_attempts += 1
        
        if consecutive_failures >= max_failures:
            logger.info(f"Stopped after {max_failures} consecutive missing verses - chapter likely complete")
        elif total_attempts >= max_attempts:
            logger.warning(f"Stopped at safety limit of {max_attempts} attempts")
        
        logger.info(f"Completed Canto {canto_num}, Chapter {chapter_num} - {len(chapter_data['verses'])} verses total")
        return chapter_data
    
    def resume_scraping(self, max_cantos: Optional[int] = None):
        """Resume scraping from where we left off"""
        logger.info("Starting resume scraping process")
        
        # Load existing data
        self.load_existing_data()
        
        # Determine resume point
        resume_canto, resume_chapter, resume_verse = self.get_resume_point()
        
        logger.info(f"Resuming from Canto {resume_canto}, Chapter {resume_chapter}, Verse {resume_verse}")
        
        # Discover all cantos if we don't know them already
        if resume_canto == 1 and not self.cantos_data:
            cantos = self.discover_cantos()
        else:
            # Create canto info for the remaining cantos
            cantos = []
            for canto_num in range(resume_canto, self.expected_cantos + 1):
                cantos.append({
                    'number': canto_num,
                    'title': f'Canto {canto_num}',
                    'url': f"https://vedabase.io/en/library/sb/{canto_num}/"
                })
        
        if max_cantos:
            cantos = [c for c in cantos if c['number'] <= max_cantos]
            logger.info(f"Limited to cantos up to {max_cantos}")
        
        # Process each canto
        for canto in cantos:
            canto_num = canto['number']
            
            try:
                # If this is the resume canto and we already have some data, merge it
                if canto_num == resume_canto and canto_num in self.cantos_data:
                    canto_data = self.cantos_data[canto_num]
                    logger.info(f"Continuing existing Canto {canto_num}")
                else:
                    # Create new canto data
                    canto_data = {
                        'canto_number': canto_num,
                        'title': canto['title'],
                        'chapters': {}
                    }
                    logger.info(f"Starting new Canto {canto_num}")
                
                # Discover chapters for this canto
                chapters = self.discover_chapters(canto_num, canto['url'])
                
                if not chapters:
                    logger.warning(f"No chapters found for Canto {canto_num}")
                    continue
                
                # Process each chapter
                for chapter in chapters:
                    chapter_num = chapter['number']
                    
                    # Determine starting verse for this chapter
                    if canto_num == resume_canto and chapter_num == resume_chapter:
                        start_verse = resume_verse
                    elif canto_num == resume_canto and chapter_num > resume_chapter:
                        start_verse = 1
                    elif canto_num > resume_canto:
                        start_verse = 1
                    else:
                        # This chapter was already completed, skip it
                        continue
                    
                    try:
                        chapter_data = self.scrape_chapter_from_verse(canto_num, chapter_num, start_verse)
                        canto_data['chapters'][chapter_num] = chapter_data
                        
                        # Save progress after each chapter
                        self.cantos_data[canto_num] = canto_data
                        self.save_individual_canto(canto_num, canto_data)
                        
                        logger.info(f"Completed Canto {canto_num}, Chapter {chapter_num} - {len(chapter_data['verses'])} verses")
                        
                    except Exception as e:
                        logger.error(f"Error scraping canto {canto_num}, chapter {chapter_num}: {e}")
                        continue
                
                # Update the main data structure
                self.cantos_data[canto_num] = canto_data
                logger.info(f"Completed Canto {canto_num} - {len(canto_data['chapters'])} chapters")
                
            except Exception as e:
                logger.error(f"Error scraping canto {canto_num}: {e}")
                continue
        
        logger.info("Resume scraping completed")
    
    def save_individual_canto(self, canto_num: int, canto_data: Dict):
        """Save a single canto to file for incremental progress"""
        try:
            os.makedirs('data_sb/raw/cantos', exist_ok=True)
            
            filename = f'data_sb/raw/cantos/canto_{canto_num:02d}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(canto_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved Canto {canto_num} to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save Canto {canto_num}: {e}")

    def scrape_all_cantos(self, max_cantos: Optional[int] = None):
        """Scrape all cantos of the Srimad-Bhagavatam"""
        logger.info("Starting to scrape all cantos of Srimad-Bhagavatam")
        
        # Discover all cantos
        cantos = self.discover_cantos()
        
        if not cantos:
            logger.error("No cantos found")
            return
        
        # Limit cantos if specified (useful for testing)
        if max_cantos:
            cantos = cantos[:max_cantos]
            logger.info(f"Limited to first {max_cantos} cantos for testing")
        
        for canto in cantos:
            try:
                canto_data = self.scrape_canto(canto['number'], canto['url'])
                self.cantos_data[canto['number']] = canto_data
                
                total_verses = sum(len(chapter['verses']) for chapter in canto_data['chapters'].values())
                logger.info(f"Completed Canto {canto['number']} - {len(canto_data['chapters'])} chapters, {total_verses} verses")
            except Exception as e:
                logger.error(f"Error scraping canto {canto['number']}: {e}")
                continue
        
        logger.info("Completed scraping all cantos")

    def save_data(self):
        """Save all scraped data to files"""
        try:
            # Create directories
            os.makedirs('data_sb/raw', exist_ok=True)
            os.makedirs('data_sb/processed', exist_ok=True)
            
            # Save complete JSON
            with open('data_sb/raw/srimad_bhagavatam_complete.json', 'w', encoding='utf-8') as f:
                json.dump(self.cantos_data, f, indent=2, ensure_ascii=False)
            
            logger.info("Saved complete data to data_sb/raw/srimad_bhagavatam_complete.json")
            
            # Save text format
            text_content = self.generate_text_format()
            with open('data_sb/processed/srimad_bhagavatam_complete.txt', 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            logger.info("Saved text format to data_sb/processed/srimad_bhagavatam_complete.txt")
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def generate_text_format(self) -> str:
        """Generate text format of all scraped data"""
        text_lines = []
        text_lines.append("SRIMAD-BHAGAVATAM")
        text_lines.append("=" * 50)
        text_lines.append("")
        
        for canto_num in sorted(self.cantos_data.keys()):
            canto = self.cantos_data[canto_num]
            text_lines.append(f"CANTO {canto_num}: {canto.get('title', '')}")
            text_lines.append("-" * 40)
            text_lines.append("")
            
            for chapter_num in sorted(canto['chapters'].keys()):
                chapter = canto['chapters'][chapter_num]
                text_lines.append(f"Chapter {chapter_num}: {chapter.get('title', '')}")
                text_lines.append("")
                
                for verse in chapter['verses']:
                    text_lines.append(f"VERSE {verse.get('verse_number', '')}")
                    
                    if verse.get('sanskrit_verse'):
                        text_lines.append(f"Sanskrit: {verse['sanskrit_verse']}")
                    
                    if verse.get('translation'):
                        text_lines.append(f"Translation: {verse['translation']}")
                    
                    if verse.get('purport'):
                        text_lines.append(f"Purport: {verse['purport']}")
                    
                    text_lines.append("")
                
                text_lines.append("")
        
        return "\n".join(text_lines)
    
    def get_stats(self) -> str:
        """Get statistics about scraped data"""
        if not self.cantos_data:
            return "No data scraped yet."
        
        total_cantos = len(self.cantos_data)
        total_chapters = 0
        total_verses = 0
        
        for canto_data in self.cantos_data.values():
            total_chapters += len(canto_data['chapters'])
            for chapter_data in canto_data['chapters'].values():
                total_verses += len(chapter_data['verses'])
        
        stats = f"""
Srimad-Bhagavatam Scraping Statistics:
- Total Cantos: {total_cantos}
- Total Chapters: {total_chapters}  
- Total Verses: {total_verses}
- Scraped URLs: {len(self.scraped_urls)}
- Failed URLs: {len(self.failed_urls)}
- Validation Errors: {len(self.validation_errors)}

Canto breakdown:
"""
        
        for canto_num in sorted(self.cantos_data.keys()):
            canto_data = self.cantos_data[canto_num]
            chapter_count = len(canto_data['chapters'])
            verse_count = sum(len(chapter['verses']) for chapter in canto_data['chapters'].values())
            stats += f"- Canto {canto_num}: {chapter_count} chapters, {verse_count} verses\n"
        
        return stats

    def validate_verse_content(self, verse_content: Dict, url: str) -> bool:
        """Validate that verse content has minimum required data"""
        try:
            # Check if we have a verse number
            if not verse_content.get('verse_number'):
                self.validation_errors.append(f"Missing verse number for {url}")
                return False
            
            # Check if we have at least translation or purport
            if not verse_content.get('translation') and not verse_content.get('purport'):
                self.validation_errors.append(f"Missing translation and purport for {url}")
                return False
            
            # Check for minimum content length
            translation_len = len(verse_content.get('translation', ''))
            purport_len = len(verse_content.get('purport', ''))
            
            if translation_len < 10 and purport_len < 10:
                self.validation_errors.append(f"Content too short for {url}")
                return False
            
            return True
            
        except Exception as e:
            self.validation_errors.append(f"Validation error for {url}: {e}")
            return False

    def validate_existing_data(self) -> bool:
        """Validate that we have complete cantos 1-9 before resuming from Canto 10"""
        logger.info("Validating existing data...")
        
        if not self.cantos_data:
            logger.info("No existing data found")
            return False
        
        # Check if we have exactly cantos 1-9
        expected_cantos = set(range(1, 10))  # 1 through 9
        actual_cantos = set(self.cantos_data.keys())
        
        if actual_cantos != expected_cantos:
            missing_cantos = expected_cantos - actual_cantos
            extra_cantos = actual_cantos - expected_cantos
            
            if missing_cantos:
                logger.warning(f"Missing cantos: {sorted(missing_cantos)}")
            if extra_cantos:
                logger.info(f"Found extra cantos: {sorted(extra_cantos)}")
            
            if missing_cantos:
                logger.info("Cannot resume from Canto 10 due to missing earlier cantos")
                return False
        
        # Validate that each canto has reasonable content
        for canto_num in range(1, 10):
            canto_data = self.cantos_data[canto_num]
            chapters = canto_data.get('chapters', {})
            
            if not chapters:
                logger.warning(f"Canto {canto_num} has no chapters")
                return False
            
            total_verses = sum(len(chapter.get('verses', [])) for chapter in chapters.values())
            if total_verses == 0:
                logger.warning(f"Canto {canto_num} has no verses")
                return False
            
            logger.info(f"Canto {canto_num}: {len(chapters)} chapters, {total_verses} verses [VALID]")
        
        logger.info("Existing data validation successful - ready to resume from Canto 10")
        return True

    def resume_from_canto_10(self):
        """Special method to resume scraping specifically from Canto 10"""
        logger.info("=== RESUMING FROM CANTO 10 ===")
        logger.info("Previous session was interrupted during Canto 10 at verse 10.19.5")
        logger.info("Canto 10 data was not saved, so starting fresh from Canto 10")
        
        # Validate existing data first
        if not self.validate_existing_data():
            logger.error("Existing data validation failed. Please check your data files.")
            return
        
        # Start from Canto 10 and continue through Canto 12
        remaining_cantos = []
        for canto_num in range(10, self.expected_cantos + 1):
            remaining_cantos.append({
                'number': canto_num,
                'title': f'Canto {canto_num}',
                'url': f"https://vedabase.io/en/library/sb/{canto_num}/"
            })
        
        logger.info(f"Will scrape {len(remaining_cantos)} remaining cantos: 10-12")
        
        # Process each remaining canto
        for canto in remaining_cantos:
            canto_num = canto['number']
            
            try:
                logger.info(f"Starting Canto {canto_num}")
                
                # Create new canto data
                canto_data = {
                    'canto_number': canto_num,
                    'title': canto['title'],
                    'chapters': {}
                }
                
                # Discover chapters for this canto
                chapters = self.discover_chapters(canto_num, canto['url'])
                
                if not chapters:
                    logger.warning(f"No chapters found for Canto {canto_num}")
                    continue
                
                logger.info(f"Found {len(chapters)} chapters in Canto {canto_num}")
                
                # Process each chapter
                for chapter in chapters:
                    chapter_num = chapter['number']
                    
                    try:
                        chapter_data = self.scrape_chapter_from_verse(canto_num, chapter_num, 1)
                        canto_data['chapters'][chapter_num] = chapter_data
                        
                        # Save progress after each chapter
                        self.cantos_data[canto_num] = canto_data
                        self.save_individual_canto(canto_num, canto_data)
                        
                        logger.info(f"[SUCCESS] Completed Canto {canto_num}, Chapter {chapter_num} - {len(chapter_data['verses'])} verses")
                        
                    except Exception as e:
                        logger.error(f"Error scraping canto {canto_num}, chapter {chapter_num}: {e}")
                        continue
                
                # Update the main data structure
                self.cantos_data[canto_num] = canto_data
                total_verses = sum(len(chapter['verses']) for chapter in canto_data['chapters'].values())
                logger.info(f"[SUCCESS] Completed Canto {canto_num} - {len(canto_data['chapters'])} chapters, {total_verses} verses")
                
            except Exception as e:
                logger.error(f"Error scraping canto {canto_num}: {e}")
                continue
        
        logger.info("=== RESUME FROM CANTO 10 COMPLETED ===")

    def get_scraping_progress(self) -> str:
        """Get current scraping progress"""
        with self.progress_lock:
            total_chapters = self.total_progress['chapters']
            completed_chapters = self.completed_progress['chapters']
            completed_verses = self.completed_progress['verses']
            
            if total_chapters > 0:
                chapter_progress = (completed_chapters / total_chapters) * 100
                progress_msg = f"Chapters: {completed_chapters}/{total_chapters} ({chapter_progress:.1f}%)"
            else:
                progress_msg = f"Chapters: {completed_chapters}"
            
            if completed_verses > 0:
                progress_msg += f", Verses: {completed_verses}"
            
            return progress_msg
    
    def print_progress_report(self):
        """Print a detailed progress report"""
        logger.info("=== SCRAPING PROGRESS REPORT ===")
        logger.info(self.get_scraping_progress())
        
        if self.cantos_data:
            logger.info("Completed cantos:")
            for canto_num in sorted(self.cantos_data.keys()):
                canto_data = self.cantos_data[canto_num]
                chapters = len(canto_data.get('chapters', {}))
                verses = sum(len(ch.get('verses', [])) for ch in canto_data['chapters'].values())
                logger.info(f"  Canto {canto_num}: {chapters} chapters, {verses} verses")
        
        logger.info("=== END PROGRESS REPORT ===")
        

    def resume_from_canto_10_parallel(self):
        """Resume scraping from Canto 10 with parallel processing"""
        logger.info("=== RESUMING FROM CANTO 10 WITH PARALLEL PROCESSING ===")
        logger.info("Previous session was interrupted during Canto 10 at verse 10.19.5")
        logger.info("Canto 10 data was not saved, so starting fresh from Canto 10")
        
        # Load existing data
        self.load_existing_data()
        
        # Validate existing data first
        if not self.validate_existing_data():
            logger.error("Existing data validation failed. Please check your data files.")
            return
        
        # Configure for parallel processing
        logger.info(f"Parallel processing: {'Enabled' if self.enable_parallel else 'Disabled'}")
        logger.info(f"Max workers: {self.max_workers}")
        
        # Start from Canto 10 and continue through Canto 12
        remaining_cantos = []
        for canto_num in range(10, self.expected_cantos + 1):
            remaining_cantos.append({
                'number': canto_num,
                'title': f'Canto {canto_num}',
                'url': f"https://vedabase.io/en/library/sb/{canto_num}/"
            })
        
        logger.info(f"Will scrape {len(remaining_cantos)} remaining cantos: 10-12")
        
        # Process each remaining canto
        for canto in remaining_cantos:
            canto_num = canto['number']
            
            try:
                logger.info(f"Starting Canto {canto_num}")
                start_time = time.time()
                
                # Use parallel canto scraping
                canto_data = self.scrape_canto_parallel(canto_num, canto['url'])
                
                # Update the main data structure
                self.cantos_data[canto_num] = canto_data
                
                # Save individual canto file
                self.save_individual_canto(canto_num, canto_data)
                
                # Calculate time taken
                elapsed_time = time.time() - start_time
                total_verses = sum(len(ch.get('verses', [])) for ch in canto_data['chapters'].values())
                
                logger.info(f"Completed Canto {canto_num} in {elapsed_time:.1f} seconds")
                logger.info(f"  - {len(canto_data['chapters'])} chapters, {total_verses} verses")
                
                # Print progress report
                self.print_progress_report()
                
            except Exception as e:
                logger.error(f"Error scraping canto {canto_num}: {e}")
                continue
        
        # Save final complete data
        try:
            self.save_data()
            logger.info("All remaining cantos completed successfully!")
            logger.info("Final data saved to data_sb/raw/srimad_bhagavatam_complete.json")
        except Exception as e:
            logger.error(f"Error saving final data: {e}")
        
        # Final statistics
        logger.info("\n" + self.get_stats())

    def export_for_rag(self, chunk_size='verse', include_metadata=True):
        """Export data optimized for RAG (Retrieval Augmented Generation) systems"""
        if not self.cantos_data:
            logger.error("No data to export. Please scrape data first.")
            return
        
        # Create organized RAG export directory structure
        os.makedirs('data_sb/rag/standard', exist_ok=True)
        
        if chunk_size == 'verse':
            self._export_verse_chunks(include_metadata)
        elif chunk_size == 'chapter':
            self._export_chapter_chunks(include_metadata)
        elif chunk_size == 'canto':
            self._export_canto_chunks(include_metadata)
        elif chunk_size == 'complete':
            self._export_complete_chunks(include_metadata)
        else:
            logger.error(f"Unknown chunk_size: {chunk_size}")
            return
            
        logger.info(f"RAG export completed with {chunk_size}-level chunking")

    def _export_verse_chunks(self, include_metadata=True):
        """Export individual verses as RAG chunks"""
        chunks = []
        
        for canto_num, canto_data in sorted(self.cantos_data.items()):
            for chapter_num, chapter_data in canto_data.get('chapters', {}).items():
                chapter_title = chapter_data.get('title', f"Chapter {chapter_num}")
                
                for verse in chapter_data.get('verses', []):
                    verse_num = verse.get('verse_number', '')
                    
                    # Build comprehensive content
                    content_parts = []
                    content_parts.append(f"Verse SB {canto_num}.{chapter_num}.{verse_num}")
                    
                    if verse.get('sanskrit_verse'):
                        content_parts.append(f"\nSanskrit: {verse['sanskrit_verse']}")
                    
                    if verse.get('transliteration'):
                        content_parts.append(f"\nTransliteration: {verse['transliteration']}")
                    
                    if verse.get('synonyms'):
                        content_parts.append(f"\nWord-for-word meaning: {verse['synonyms']}")
                    
                    if verse.get('translation'):
                        content_parts.append(f"\nTranslation: {verse['translation']}")
                    
                    if verse.get('purport'):
                        content_parts.append(f"\nPurport: {verse['purport']}")
                    
                    chunk = {
                        "id": f"sb_{canto_num}_{chapter_num}_{verse_num}",
                        "content": "".join(content_parts),
                        "verse_number": f"SB {canto_num}.{chapter_num}.{verse_num}",
                        "source": "Śrīmad-Bhāgavatam by A.C. Bhaktivedanta Swami Prabhupāda",
                        "parts": {
                            "sanskrit_verse": verse.get('sanskrit_verse', ''),
                            "transliteration": verse.get('transliteration', ''),
                            "synonyms": verse.get('synonyms', ''),
                            "translation": verse.get('translation', ''),
                            "purport": verse.get('purport', '')
                        }
                    }
                    
                    if include_metadata:
                        chunk["metadata"] = {
                            "has_sanskrit": bool(verse.get('sanskrit_verse')),
                            "has_transliteration": bool(verse.get('transliteration')),
                            "has_synonyms": bool(verse.get('synonyms')),
                            "has_translation": bool(verse.get('translation')),
                            "has_purport": bool(verse.get('purport')),
                            "content_length": len(chunk["content"]),
                            "canto": canto_num,
                            "chapter": chapter_num,
                            "chapter_title": chapter_title,
                            "scripture": "Śrīmad-Bhāgavatam"
                        }
                    
                    chunks.append(chunk)
        
        # Save as JSONL (one JSON object per line)
        with open('data_sb/rag/standard/srimad_bhagavatam_rag_verses.jsonl', 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
        
        # Save as JSON array
        with open('data_sb/rag/standard/srimad_bhagavatam_rag_verses.json', 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported {len(chunks)} verse chunks for RAG")

    def _export_chapter_chunks(self, include_metadata=True):
        """Export chapters as RAG chunks"""
        chunks = []
        
        for canto_num, canto_data in sorted(self.cantos_data.items()):
            for chapter_num, chapter_data in canto_data.get('chapters', {}).items():
                chapter_title = chapter_data.get('title', f"Chapter {chapter_num}")
                
                # Combine all verses in the chapter
                content_parts = []
                content_parts.append(f"Chapter SB {canto_num}.{chapter_num}: {chapter_title}")
                
                verse_count = 0
                for verse in chapter_data.get('verses', []):
                    verse_num = verse.get('verse_number', '')
                    content_parts.append(f"\n\nVerse {verse_num}:")
                    
                    if verse.get('sanskrit_verse'):
                        content_parts.append(f"\nSanskrit: {verse['sanskrit_verse']}")
                    
                    if verse.get('translation'):
                        content_parts.append(f"\nTranslation: {verse['translation']}")
                    
                    if verse.get('purport'):
                        content_parts.append(f"\nPurport: {verse['purport']}")
                    
                    verse_count += 1
                
                chunk = {
                    "id": f"sb_{canto_num}_{chapter_num}",
                    "content": "".join(content_parts),
                    "chapter": f"SB {canto_num}.{chapter_num}",
                    "title": chapter_title,
                    "source": "Śrīmad-Bhāgavatam by A.C. Bhaktivedanta Swami Prabhupāda"
                }
                
                if include_metadata:
                    chunk["metadata"] = {
                        "canto": canto_num,
                        "chapter": chapter_num,
                        "verse_count": verse_count,
                        "content_length": len(chunk["content"]),
                        "scripture": "Śrīmad-Bhāgavatam"
                    }
                
                chunks.append(chunk)
        
        # Save as JSONL and JSON
        with open('data_sb/rag/standard/srimad_bhagavatam_rag_chapters.jsonl', 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
        
        with open('data_sb/rag/standard/srimad_bhagavatam_rag_chapters.json', 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported {len(chunks)} chapter chunks for RAG")

    def _export_canto_chunks(self, include_metadata=True):
        """Export cantos as RAG chunks"""
        chunks = []
        
        for canto_num, canto_data in sorted(self.cantos_data.items()):
            canto_title = canto_data.get('title', f"Canto {canto_num}")
            
            # Combine all chapters in the canto
            content_parts = []
            content_parts.append(f"Canto {canto_num}: {canto_title}")
            
            chapter_count = 0
            verse_count = 0
            
            for chapter_num, chapter_data in canto_data.get('chapters', {}).items():
                chapter_title = chapter_data.get('title', f"Chapter {chapter_num}")
                content_parts.append(f"\n\nChapter {chapter_num}: {chapter_title}")
                chapter_count += 1
                
                for verse in chapter_data.get('verses', []):
                    verse_num = verse.get('verse_number', '')
                    if verse.get('translation'):
                        content_parts.append(f"\n{verse_num}: {verse['translation']}")
                    verse_count += 1
            
            chunk = {
                "id": f"sb_canto_{canto_num}",
                "content": "".join(content_parts),
                "canto": f"SB Canto {canto_num}",
                "title": canto_title,
                "source": "Śrīmad-Bhāgavatam by A.C. Bhaktivedanta Swami Prabhupāda"
            }
            
            if include_metadata:
                chunk["metadata"] = {
                    "canto": canto_num,
                    "chapter_count": chapter_count,
                    "verse_count": verse_count,
                    "content_length": len(chunk["content"]),
                    "scripture": "Śrīmad-Bhāgavatam"
                }
            
            chunks.append(chunk)
        
        # Save as JSONL and JSON
        with open('data_sb/rag/standard/srimad_bhagavatam_rag_cantos.jsonl', 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
        
        with open('data_sb/rag/standard/srimad_bhagavatam_rag_cantos.json', 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported {len(chunks)} canto chunks for RAG")

    def _export_complete_chunks(self, include_metadata=True):
        """Export complete Śrīmad-Bhāgavatam as a single RAG chunk"""
        # Build complete content
        content_parts = []
        content_parts.append("Śrīmad-Bhāgavatam (Complete)")
        content_parts.append("\nThe Bhāgavata Purāṇa by A.C. Bhaktivedanta Swami Prabhupāda")
        
        total_verses = 0
        total_chapters = 0
        
        for canto_num, canto_data in sorted(self.cantos_data.items()):
            canto_title = canto_data.get('title', f"Canto {canto_num}")
            content_parts.append(f"\n\n--- CANTO {canto_num}: {canto_title} ---")
            
            for chapter_num, chapter_data in canto_data.get('chapters', {}).items():
                chapter_title = chapter_data.get('title', f"Chapter {chapter_num}")
                content_parts.append(f"\n\nChapter {chapter_num}: {chapter_title}")
                total_chapters += 1
                
                for verse in chapter_data.get('verses', []):
                    if verse.get('translation'):
                        verse_num = verse.get('verse_number', '')
                        content_parts.append(f"\n{verse_num}: {verse['translation']}")
                    total_verses += 1
        
        chunk = {
            "id": "sb_complete",
            "content": "".join(content_parts),
            "title": "Śrīmad-Bhāgavatam (Complete)",
            "source": "Śrīmad-Bhāgavatam by A.C. Bhaktivedanta Swami Prabhupāda"
        }
        
        if include_metadata:
            chunk["metadata"] = {
                "canto_count": len(self.cantos_data),
                "chapter_count": total_chapters,
                "verse_count": total_verses,
                "content_length": len(chunk["content"]),
                "scripture": "Śrīmad-Bhāgavatam",
                "is_complete": True
            }
        
        # Save as JSON
        with open('data_sb/rag/standard/srimad_bhagavatam_rag_complete.json', 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)
        
        logger.info("Exported complete Śrīmad-Bhāgavatam chunk for RAG")
    
def main():
    """Main function to run the scraper"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('srimad_bhagavatam_scraper.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create scraper instance with parallel processing enabled
    scraper = SrimadBhagavatamScraper(enable_parallel=True, max_workers=4)
    
    try:
        # Load existing data first
        scraper.load_existing_data()
        
        # Check if we have cantos 1-9 and need to resume from Canto 10
        if (len(scraper.cantos_data) == 9 and 
            max(scraper.cantos_data.keys()) == 9 and 
            10 not in scraper.cantos_data):
            
            logger.info("Detected cantos 1-9 complete, Canto 10 missing - using parallel resume method")
            scraper.resume_from_canto_10_parallel()
        else:
            # Use general resume functionality
            logger.info("Using general resume functionality")
            scraper.resume_scraping()
        
        logger.info("Scraping completed successfully!")
        
        # Export RAG formats
        try:
            logger.info("Exporting RAG formats...")
            scraper.export_for_rag('verse')
            scraper.export_for_rag('chapter')
            scraper.export_for_rag('canto')
            scraper.export_for_rag('complete')
            logger.info("RAG export completed successfully!")
        except Exception as e:
            logger.error(f"RAG export failed: {e}")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        logger.info("Progress has been saved. You can resume later.")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        logger.info("Check the log for details. You can try resuming later.")

if __name__ == "__main__":
    main()
