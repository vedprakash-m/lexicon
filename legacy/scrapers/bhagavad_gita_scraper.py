"""
Bhagavad Gita Text Scraper

This script scrapes the complete text of the Bhagavad Gita from vedabase.io
for use in an AI agent application. It extracts all verses, translations,
and purports from all 18 chapters.

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
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BhagavadGitaScraper:
    """Scraper for extracting Bhagavad Gita text from vedabase.io"""
    
    def __init__(self):
        self.base_url = "https://vedabase.io/en/library/bg/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.chapters_data = {}
        self.delay = 1  # Delay between requests in seconds
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delays = [2, 5, 10]  # Progressive delays in seconds
        
        # Tracking and validation
        self.expected_chapters = 18
        self.expected_verse_counts = {
            1: 47, 2: 72, 3: 43, 4: 42, 5: 29, 6: 47, 7: 30, 8: 28,
            9: 34, 10: 42, 11: 55, 12: 20, 13: 35, 14: 27, 15: 20,
            16: 24, 17: 28, 18: 78
        }
        self.scraped_urls = set()  # Track what we've scraped
        self.failed_urls = set()   # Track failed URLs
        self.validation_errors = []  # Track validation issues
    
    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a webpage with retry mechanism"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching: {url} (attempt {attempt + 1}/{self.max_retries})")
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                # Add delay to be respectful to the server
                time.sleep(self.delay)
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Quick sanity check - ensure we got actual content
                if soup.find('body') and len(soup.get_text(strip=True)) > 100:
                    return soup
                else:
                    raise requests.RequestException(f"Page appears to be empty or invalid: {len(soup.get_text())}")
                    
            except requests.RequestException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    retry_delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    logger.warning(f"Error fetching {url} (attempt {attempt + 1}): {e}")
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts: {e}")
        
        return None
    
    def extract_verse_content(self, soup: BeautifulSoup) -> Dict:
        """Extract verse content from a page"""
        content = {
            'verse_number': '',
            'verse_numbers': [],  # For grouped verses like 16-18
            'sanskrit_verse': '',           # Part 1: Sanskrit text
            'sanskrit_transliteration': '', # Part 1: Roman transliteration 
            'synonyms': '',                 # Part 2: Word-by-word meanings
            'translation': '',              # Part 3: Complete translation
            'purport': ''                   # Part 4: Commentary/explanation
        }
        
        try:
            # Extract verse number from h1 tag (e.g., "Bg. 1.1" or "Bg. 1.16-18")
            title = soup.find('h1')
            if title:
                verse_title = title.get_text(strip=True)
                content['verse_number'] = verse_title
                
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
                                    content['verse_numbers'] = [f"{chapter_num}.{i}" for i in range(start, end + 1)]
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
                # Check for Roman transliteration (usually follows Sanskrit)
                elif (not sanskrit_text or sanskrit_text in text) and len(text) > 20:
                    # Look for transliteration patterns (Sanskrit words in Roman script)
                    if any(word in text.lower() for word in ['dhṛtarāṣṭra', 'uvāca', 'dharma', 'kṣetre']):
                        transliteration_text = text
            
            content['sanskrit_verse'] = sanskrit_text
            content['sanskrit_transliteration'] = transliteration_text
            
            # Extract sections based on h2 headings
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
    
    def discover_verse_urls(self, chapter_num: int) -> List[str]:
        """Discover all verse URLs for a chapter by parsing the chapter index"""
        logger.info(f"Discovering verse URLs for Chapter {chapter_num}")
        
        chapter_url = f"{self.base_url}{chapter_num}/"
        soup = self.get_page_content(chapter_url)
        
        if not soup:
            logger.error(f"Failed to load chapter {chapter_num} index")
            return []
        
        verse_urls = []
        
        # Look for links that match the pattern /bg/{chapter_num}/{verse}/
        # These can be individual verses or grouped verses
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            
            # Check if this is a verse link for this chapter
            if f'/library/bg/{chapter_num}/' in href and href.endswith('/'):
                # Extract the verse part from the URL
                url_parts = href.split('/')
                
                # Find the part after the chapter number
                try:
                    chapter_index = url_parts.index(str(chapter_num))
                    if chapter_index + 1 < len(url_parts):
                        verse_part = url_parts[chapter_index + 1]
                        
                        # Skip empty parts and non-verse parts
                        if verse_part and verse_part != '' and not verse_part.startswith('advanced'):
                            full_url = f"https://vedabase.io{href}"
                            if full_url not in verse_urls:
                                verse_urls.append(full_url)
                except (ValueError, IndexError):
                    continue
        
        # Remove duplicates and sort
        verse_urls = list(set(verse_urls))
        verse_urls.sort(key=lambda x: self._extract_verse_sort_key(x))
        
        logger.info(f"Found {len(verse_urls)} verse URLs for Chapter {chapter_num}")
        for url in verse_urls:
            logger.debug(f"  - {url}")
        
        return verse_urls
    
    def _extract_verse_sort_key(self, url: str):
        """Extract a sort key from verse URL for proper ordering"""
        try:
            # Extract verse part from URL like .../bg/1/16-18/ or .../bg/1/1/
            parts = url.rstrip('/').split('/')
            verse_part = parts[-1]
            
            if '-' in verse_part:
                # For grouped verses like "16-18", use the first number
                return int(verse_part.split('-')[0])
            else:
                return int(verse_part)
        except (ValueError, IndexError):
            return 999  # Put unparseable URLs at the end
        """Scrape all verses from a chapter"""
    def scrape_chapter(self, chapter_num: int) -> Dict:
        """Scrape all verses from a chapter using the new URL discovery method"""
        logger.info(f"Scraping Chapter {chapter_num}")
        
        chapter_data = {
            'chapter_number': chapter_num,
            'title': f"Chapter {chapter_num}",
            'verses': []
        }
        
        # First, get the chapter page to extract the title
        chapter_url = f"{self.base_url}{chapter_num}/"
        soup = self.get_page_content(chapter_url)
        
        if not soup:
            logger.error(f"Failed to load chapter {chapter_num}")
            return chapter_data
        
        # Extract chapter title if available
        title_elem = soup.find('h1') or soup.find('title')
        if title_elem:
            chapter_data['title'] = title_elem.get_text(strip=True)
        
        # Discover all verse URLs for this chapter
        verse_urls = self.discover_verse_urls(chapter_num)
        
        if not verse_urls:
            logger.warning(f"No verse URLs found for Chapter {chapter_num}")
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
        
        # Validate chapter completeness
        self.validate_chapter_completeness(chapter_num, chapter_data)
        
        return chapter_data
    
    def scrape_all_chapters(self):
        """Scrape all 18 chapters of the Bhagavad Gita"""
        logger.info("Starting to scrape all chapters of Bhagavad Gita")
        
        for chapter_num in range(1, 19):  # 18 chapters
            try:
                chapter_data = self.scrape_chapter(chapter_num)
                self.chapters_data[chapter_num] = chapter_data
                logger.info(f"Completed Chapter {chapter_num} - {len(chapter_data['verses'])} verses")
            except Exception as e:
                logger.error(f"Error scraping chapter {chapter_num}: {e}")
                continue
        
        logger.info("Completed scraping all chapters")
    
    def save_data(self, output_format='json'):
        """Save the scraped data to files"""
        if not self.chapters_data:
            logger.error("No data to save")
            return
        
        # Create organized output directory structure
        os.makedirs('data_bg/raw', exist_ok=True)
        os.makedirs('data_bg/processed', exist_ok=True)
        
        if output_format == 'json':
            # Save as JSON in raw data directory
            with open('data_bg/raw/bhagavad_gita_complete.json', 'w', encoding='utf-8') as f:
                json.dump(self.chapters_data, f, indent=2, ensure_ascii=False)
            
            # Save each chapter separately in chapters subdirectory
            os.makedirs('data_bg/raw/chapters', exist_ok=True)
            for chapter_num, chapter_data in self.chapters_data.items():
                with open(f'data_bg/raw/chapters/chapter_{chapter_num:02d}.json', 'w', encoding='utf-8') as f:
                    json.dump(chapter_data, f, indent=2, ensure_ascii=False)
        
        # Also save as plain text for easy reading in processed directory
        with open('data_bg/processed/bhagavad_gita_complete.txt', 'w', encoding='utf-8') as f:
            f.write("BHAGAVAD GITA AS IT IS\n")
            f.write("By His Divine Grace A.C. Bhaktivedanta Swami Prabhupada\n\n")
            
            for chapter_num in sorted(self.chapters_data.keys()):
                chapter_data = self.chapters_data[chapter_num]
                f.write(f"\n{'='*60}\n")
                f.write(f"{chapter_data['title']}\n")
                f.write(f"{'='*60}\n\n")
                
                for verse in chapter_data['verses']:
                    # Handle both single and grouped verses
                    if verse['verse_numbers']:
                        verse_display = ", ".join(verse['verse_numbers'])
                    else:
                        verse_display = verse['verse_number']
                    
                    f.write(f"VERSE {verse_display}\n")
                    f.write("-" * 40 + "\n")
                    
                    if verse['sanskrit_verse']:
                        f.write(f"Sanskrit: {verse['sanskrit_verse']}\n\n")
                    
                    if verse['synonyms']:
                        f.write(f"Synonyms: {verse['synonyms']}\n\n")
                    
                    if verse['translation']:
                        f.write(f"Translation: {verse['translation']}\n\n")
                    
                    if verse['purport']:
                        f.write(f"Purport: {verse['purport']}\n\n")
                    
                    f.write("\n" + "="*60 + "\n\n")
        
        logger.info("Data saved successfully")
    
    def get_stats(self):
        """Get statistics about the scraped data"""
        if not self.chapters_data:
            return "No data available"
        
        total_verses = sum(len(chapter['verses']) for chapter in self.chapters_data.values())
        total_chapters = len(self.chapters_data)
        
        stats = f"""
Bhagavad Gita Scraping Statistics:
- Total Chapters: {total_chapters}
- Total Verses: {total_verses}
- Average verses per chapter: {total_verses/total_chapters:.1f}

Chapter breakdown:
"""
        for chapter_num in sorted(self.chapters_data.keys()):
            verse_count = len(self.chapters_data[chapter_num]['verses'])
            stats += f"- Chapter {chapter_num}: {verse_count} verses\n"
        
        return stats
    
    def validate_verse_content(self, verse_content: Dict, url: str) -> bool:
        """Validate that a verse has meaningful content"""
        errors = []
        
        # Check if verse has basic required fields
        if not verse_content.get('verse_number'):
            errors.append("Missing verse number")
        
        # Translation is essential - every verse should have this
        if not verse_content.get('translation'):
            errors.append("Missing translation")
        elif len(verse_content['translation']) < 20:
            errors.append(f"Translation too short ({len(verse_content['translation'])} chars)")
        
        # Purport is preferred but not always required (some verses are introductory)
        has_purport = bool(verse_content.get('purport'))
        if has_purport and len(verse_content['purport']) < 50:
            errors.append(f"Purport too short ({len(verse_content['purport'])} chars)")
        
        # At least one substantial content field should exist
        substantial_content = any([
            verse_content.get('translation') and len(verse_content['translation']) >= 20,
            verse_content.get('purport') and len(verse_content['purport']) >= 50,
            verse_content.get('synonyms') and len(verse_content['synonyms']) >= 20
        ])
        
        if not substantial_content:
            errors.append("No substantial content found")
        
        if errors:
            error_msg = f"Validation errors for {url}: {'; '.join(errors)}"
            logger.warning(error_msg)
            self.validation_errors.append(error_msg)
            return False
        
        # Log if verse lacks purport (for info, not error)
        if not has_purport:
            logger.info(f"Note: {url} has no purport (may be introductory verse)")
        
        return True
    
    def validate_chapter_completeness(self, chapter_num: int, chapter_data: Dict) -> bool:
        """Validate that a chapter has all expected verses"""
        expected_count = self.expected_verse_counts.get(chapter_num, 0)
        actual_count = len(chapter_data['verses'])
        
        # Count individual verses (accounting for grouped verses)
        total_individual_verses = 0
        for verse in chapter_data['verses']:
            if verse.get('verse_numbers'):
                total_individual_verses += len(verse['verse_numbers'])
            else:
                total_individual_verses += 1
        
        if expected_count > 0 and total_individual_verses != expected_count:
            error_msg = f"Chapter {chapter_num}: Expected {expected_count} verses, got {total_individual_verses} individual verses in {actual_count} entries"
            logger.error(error_msg)
            self.validation_errors.append(error_msg)
            return False
        
        logger.info(f"Chapter {chapter_num}: Validation passed - {total_individual_verses} verses in {actual_count} entries")
        return True
    
    def get_validation_report(self) -> str:
        """Generate a comprehensive validation report"""
        if not self.chapters_data:
            return "No data to validate"
        
        report = ["VALIDATION REPORT", "=" * 50]
        
        # Overall statistics
        total_chapters = len(self.chapters_data)
        total_entries = sum(len(chapter['verses']) for chapter in self.chapters_data.values())
        total_individual_verses = 0
        
        for chapter in self.chapters_data.values():
            for verse in chapter['verses']:
                if verse.get('verse_numbers'):
                    total_individual_verses += len(verse['verse_numbers'])
                else:
                    total_individual_verses += 1
        
        report.extend([
            f"Total Chapters: {total_chapters}/{self.expected_chapters}",
            f"Total Verse Entries: {total_entries}",
            f"Total Individual Verses: {total_individual_verses}",
            f"Successfully Scraped URLs: {len(self.scraped_urls)}",
            f"Failed URLs: {len(self.failed_urls)}",
            "",
            "CHAPTER BREAKDOWN:",
            "-" * 30
        ])
        
        # Chapter-by-chapter validation
        for chapter_num in range(1, self.expected_chapters + 1):
            if chapter_num in self.chapters_data:
                chapter_data = self.chapters_data[chapter_num]
                entries = len(chapter_data['verses'])
                
                individual_verses = 0
                for verse in chapter_data['verses']:
                    if verse.get('verse_numbers'):
                        individual_verses += len(verse['verse_numbers'])
                    else:
                        individual_verses += 1
                
                expected = self.expected_verse_counts.get(chapter_num, 0)
                status = "✓ COMPLETE" if individual_verses == expected else "✗ INCOMPLETE"
                
                report.append(f"Chapter {chapter_num:2d}: {entries:2d} entries, {individual_verses:2d}/{expected:2d} verses {status}")
            else:
                report.append(f"Chapter {chapter_num:2d}: MISSING")
        
        # Validation errors
        if self.validation_errors:
            report.extend(["", "VALIDATION ERRORS:", "-" * 20])
            report.extend(self.validation_errors)
        
        # Failed URLs
        if self.failed_urls:
            report.extend(["", "FAILED URLS:", "-" * 15])
            report.extend(list(self.failed_urls))
        
        return "\n".join(report)
    
    def export_for_rag(self, chunk_size='verse', include_metadata=True):
        """Export data optimized for RAG (Retrieval Augmented Generation) systems"""
        if not self.chapters_data:
            logger.error("No data to export")
            return
        
        # Create organized RAG export directory structure
        os.makedirs('data_bg/rag/standard', exist_ok=True)
        
        # Option 1: Verse-level chunks (recommended for precise retrieval)
        if chunk_size == 'verse':
            self._export_verse_chunks(include_metadata)
        
        # Option 2: Section-level chunks (for broader context)
        elif chunk_size == 'section':
            self._export_section_chunks(include_metadata)
        
        # Option 3: Chapter-level chunks (for complete context)
        elif chunk_size == 'chapter':
            self._export_chapter_chunks(include_metadata)
        
        logger.info(f"RAG export completed with {chunk_size}-level chunking")
    
    def _export_verse_chunks(self, include_metadata=True):
        """Export individual verses as separate chunks"""
        chunks = []
        
        for chapter_num, chapter_data in self.chapters_data.items():
            chapter_title = chapter_data.get('title', f'Chapter {chapter_num}')
            
            for verse in chapter_data['verses']:
                # Handle both single and grouped verses
                verse_numbers = verse.get('verse_numbers', [verse.get('verse_number', '')])
                
                # For grouped verses, create separate chunks for each verse number
                if len(verse_numbers) > 1:
                    # Split grouped content (if possible) or duplicate it
                    for verse_num in verse_numbers:
                        chunk = self._create_verse_chunk(
                            verse, verse_num, chapter_num, chapter_title, include_metadata
                        )
                        chunks.append(chunk)
                else:
                    # Single verse
                    verse_num = verse_numbers[0] if verse_numbers else verse.get('verse_number', '')
                    chunk = self._create_verse_chunk(
                        verse, verse_num, chapter_num, chapter_title, include_metadata
                    )
                    chunks.append(chunk)
        
        # Save as JSON Lines format (efficient for vector DB ingestion)
        with open('data_bg/rag/standard/bhagavad_gita_rag_verses.jsonl', 'w', encoding='utf-8') as f:
            for chunk in chunks:
                json.dump(chunk, f, ensure_ascii=False)
                f.write('\n')
        
        # Also save as regular JSON
        with open('data_bg/rag/standard/bhagavad_gita_rag_verses.json', 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(chunks)} verse chunks for RAG")
    
    def _create_verse_chunk(self, verse, verse_number, chapter_num, chapter_title, include_metadata):
        """Create a single verse chunk optimized for RAG"""
        # Use the new combined content method
        full_content = self.get_combined_content(verse, format_type='rag')
        
        # Add verse reference at the beginning
        if verse_number:
            full_content = f"Verse {verse_number}\n\n{full_content}"
        
        chunk = {
            'id': f"bg_{chapter_num}_{verse_number.replace('.', '_')}",
            'content': full_content,
            'verse_number': verse_number,
            'chapter_number': chapter_num,
            'source': 'Bhagavad Gita As It Is by A.C. Bhaktivedanta Swami Prabhupada',
            
            # Include separate parts for flexibility
            'parts': {
                'sanskrit_devanagari': verse.get('sanskrit_verse', ''),
                'sanskrit_transliteration': verse.get('sanskrit_transliteration', ''),
                'synonyms': verse.get('synonyms', ''),
                'translation': verse.get('translation', ''),
                'purport': verse.get('purport', '')
            }
        }
        
        if include_metadata:
            verse_parts = self.get_verse_parts(verse)
            chunk['metadata'] = {
                'chapter_title': chapter_title,
                'book': 'Bhagavad Gita',
                'author': 'A.C. Bhaktivedanta Swami Prabhupada',
                'verse_type': 'grouped' if len(verse.get('verse_numbers', [])) > 1 else 'single',
                'completeness': verse_parts['completeness'],
                'content_length': len(full_content),
                'part_lengths': {
                    'sanskrit_length': len(verse.get('sanskrit_verse', '')),
                    'transliteration_length': len(verse.get('sanskrit_transliteration', '')),
                    'synonyms_length': len(verse.get('synonyms', '')),
                    'translation_length': len(verse.get('translation', '')),
                    'purport_length': len(verse.get('purport', ''))
                }
            }
        
        return chunk
    
    def _export_section_chunks(self, include_metadata=True):
        """Export verses grouped by natural sections (every 5-10 verses)"""
        chunks = []
        section_size = 5  # Adjust based on needs
        
        for chapter_num, chapter_data in self.chapters_data.items():
            chapter_title = chapter_data.get('title', f'Chapter {chapter_num}')
            verses = chapter_data['verses']
            
            # Group verses into sections
            for i in range(0, len(verses), section_size):
                section_verses = verses[i:i + section_size]
                
                # Create section content
                section_content = []
                verse_numbers = []
                
                for verse in section_verses:
                    verse_nums = verse.get('verse_numbers', [verse.get('verse_number', '')])
                    verse_numbers.extend(verse_nums)
                    
                    # Add verse content
                    if verse.get('translation'):
                        section_content.append(f"Verse {verse_nums[0] if verse_nums else 'Unknown'}: {verse['translation']}")
                    
                    if verse.get('purport'):
                        section_content.append(f"Commentary: {verse['purport']}")
                
                chunk = {
                    'id': f"bg_{chapter_num}_section_{i//section_size + 1}",
                    'content': "\n\n".join(section_content),
                    'verse_range': f"{verse_numbers[0]} - {verse_numbers[-1]}" if verse_numbers else "",
                    'chapter_number': chapter_num,
                    'section_number': i//section_size + 1,
                    'source': 'Bhagavad Gita As It Is by A.C. Bhaktivedanta Swami Prabhupada'
                }
                
                if include_metadata:
                    chunk['metadata'] = {
                        'chapter_title': chapter_title,
                        'verse_count': len(section_verses),
                        'content_length': len(chunk['content'])
                    }
                
                chunks.append(chunk)
        
        with open('data_bg/rag/standard/bhagavad_gita_rag_sections.jsonl', 'w', encoding='utf-8') as f:
            for chunk in chunks:
                json.dump(chunk, f, ensure_ascii=False)
                f.write('\n')
        
        logger.info(f"Exported {len(chunks)} section chunks for RAG")
    
    def _export_chapter_chunks(self, include_metadata=True):
        """Export complete chapters as chunks"""
        chunks = []
        
        for chapter_num, chapter_data in self.chapters_data.items():
            chapter_title = chapter_data.get('title', f'Chapter {chapter_num}')
            
            # Create chapter summary
            content_parts = [f"Chapter {chapter_num}: {chapter_title}"]
            
            for verse in chapter_data['verses']:
                verse_nums = verse.get('verse_numbers', [verse.get('verse_number', '')])
                
                if verse.get('translation'):
                    content_parts.append(f"Verse {verse_nums[0] if verse_nums else 'Unknown'}: {verse['translation']}")
                
                if verse.get('purport'):
                    content_parts.append(f"Commentary: {verse['purport']}")
            
            chunk = {
                'id': f"bg_chapter_{chapter_num}",
                'content': "\n\n".join(content_parts),
                'chapter_number': chapter_num,
                'chapter_title': chapter_title,
                'source': 'Bhagavad Gita As It Is by A.C. Bhaktivedanta Swami Prabhupada'
            }
            
            if include_metadata:
                chunk['metadata'] = {
                    'verse_count': len(chapter_data['verses']),
                    'content_length': len(chunk['content'])
                }
            
            chunks.append(chunk)
        
        with open('data_bg/rag/standard/bhagavad_gita_rag_chapters.jsonl', 'w', encoding='utf-8') as f:
            for chunk in chunks:
                json.dump(chunk, f, ensure_ascii=False)
                f.write('\n')
        
        logger.info(f"Exported {len(chunks)} chapter chunks for RAG")
    
    def export_flexible_format(self):
        """Export in a flexible format that provides both separate and combined options"""
        if not self.chapters_data:
            logger.error("No data to export")
            return
        
        # Create flexible format directory
        os.makedirs('data_bg/rag/flexible', exist_ok=True)
        
        flexible_data = {
            'metadata': {
                'book': 'Bhagavad Gita As It Is',
                'author': 'A.C. Bhaktivedanta Swami Prabhupada',
                'total_chapters': len(self.chapters_data),
                'export_date': '2025-06-24',
                'structure': {
                    'separate_parts': 'Each verse has separate fields for sanskrit, synonyms, translation, purport',
                    'combined_formats': 'Multiple combined format options available',
                    'usage': 'Use separate parts for targeted search, combined for RAG'
                }
            },
            'chapters': []
        }
        
        for chapter_num, chapter_data in sorted(self.chapters_data.items()):
            chapter_export = {
                'chapter_number': chapter_num,
                'title': chapter_data.get('title', f'Chapter {chapter_num}'),
                'verses': []
            }
            
            for verse in chapter_data['verses']:
                verse_numbers = verse.get('verse_numbers', [verse.get('verse_number', '')])
                
                # For each individual verse number in grouped verses
                for verse_num in verse_numbers:
                    verse_export = {
                        'verse_number': verse_num,
                        'is_grouped': len(verse_numbers) > 1,
                        
                        # Separate parts (original structure)
                        'parts_separate': {
                            'sanskrit_devanagari': verse.get('sanskrit_verse', ''),
                            'sanskrit_transliteration': verse.get('sanskrit_transliteration', ''),
                            'synonyms': verse.get('synonyms', ''),
                            'translation': verse.get('translation', ''),
                            'purport': verse.get('purport', '')
                        },
                        
                        # Combined formats for different use cases
                        'combined_formats': {
                            'rag_optimized': self.get_combined_content(verse, 'rag'),
                            'structured_reading': self.get_combined_content(verse, 'structured'),
                            'minimal_ai': self.get_combined_content(verse, 'minimal')
                        },
                        
                        # Analysis data
                        'analysis': self.get_verse_parts(verse)
                    }
                    
                    chapter_export['verses'].append(verse_export)
            
            flexible_data['chapters'].append(chapter_export)
        
        # Save the flexible format
        with open('data_bg/rag/flexible/bhagavad_gita_flexible.json', 'w', encoding='utf-8') as f:
            json.dump(flexible_data, f, indent=2, ensure_ascii=False)
        
        logger.info("Exported flexible format with both separate parts and combined options")
    
    def get_verse_parts(self, verse: Dict) -> Dict:
        """Get verse parts in a structured format for analysis"""
        return {
            'part_1_sanskrit': {
                'devanagari': verse.get('sanskrit_verse', ''),
                'transliteration': verse.get('sanskrit_transliteration', '')
            },
            'part_2_synonyms': verse.get('synonyms', ''),
            'part_3_translation': verse.get('translation', ''),
            'part_4_purport': verse.get('purport', ''),
            'completeness': {
                'has_sanskrit': bool(verse.get('sanskrit_verse')),
                'has_transliteration': bool(verse.get('sanskrit_transliteration')),
                'has_synonyms': bool(verse.get('synonyms')),
                'has_translation': bool(verse.get('translation')),
                'has_purport': bool(verse.get('purport')),
                'complete_verse': all([
                    verse.get('sanskrit_verse'),
                    verse.get('synonyms'), 
                    verse.get('translation'),
                    verse.get('purport')
                ])
            }
        }
    
    def get_combined_content(self, verse: Dict, format_type='rag') -> str:
        """Get verse content combined in different formats"""
        parts = []
        
        if format_type == 'rag':
            # Optimized for RAG/AI consumption
            if verse.get('sanskrit_verse'):
                parts.append(f"Sanskrit: {verse['sanskrit_verse']}")
            
            if verse.get('sanskrit_transliteration'):
                parts.append(f"Transliteration: {verse['sanskrit_transliteration']}")
            
            if verse.get('synonyms'):
                parts.append(f"Word Meanings: {verse['synonyms']}")
            
            if verse.get('translation'):
                parts.append(f"Translation: {verse['translation']}")
            
            if verse.get('purport'):
                parts.append(f"Commentary: {verse['purport']}")
        
        elif format_type == 'structured':
            # Clearly labeled sections
            parts.append("=== VERSE ===")
            if verse.get('sanskrit_verse'):
                parts.append(f"Sanskrit (Devanagari): {verse['sanskrit_verse']}")
            if verse.get('sanskrit_transliteration'):
                parts.append(f"Sanskrit (Roman): {verse['sanskrit_transliteration']}")
            
            if verse.get('synonyms'):
                parts.append("\n=== WORD MEANINGS ===")
                parts.append(verse['synonyms'])
            
            if verse.get('translation'):
                parts.append("\n=== TRANSLATION ===")
                parts.append(verse['translation'])
            
            if verse.get('purport'):
                parts.append("\n=== PURPORT ===")
                parts.append(verse['purport'])
        
        elif format_type == 'minimal':
            # Just essential content for AI
            if verse.get('translation'):
                parts.append(verse['translation'])
            if verse.get('purport'):
                parts.append(verse['purport'])
        
        return "\n\n".join(parts)
    
    def export_weighted_rag(self, weighting_strategy='balanced'):
        """Export RAG data with different field weighting strategies"""
        if not self.chapters_data:
            logger.error("No data to export")
            return
        
        # Create weighted RAG directory
        os.makedirs('data_bg/rag/weighted', exist_ok=True)
        
        chunks = []
        
        for chapter_num, chapter_data in self.chapters_data.items():
            chapter_title = chapter_data.get('title', f'Chapter {chapter_num}')
            
            for verse in chapter_data['verses']:
                verse_numbers = verse.get('verse_numbers', [verse.get('verse_number', '')])
                
                for verse_num in verse_numbers:
                    chunk = self._create_weighted_verse_chunk(
                        verse, verse_num, chapter_num, chapter_title, weighting_strategy
                    )
                    chunks.append(chunk)
        
        # Save with strategy name
        filename = f'data_bg/rag/weighted/bhagavad_gita_rag_weighted_{weighting_strategy}.jsonl'
        with open(filename, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                json.dump(chunk, f, ensure_ascii=False)
                f.write('\n')
        
        logger.info(f"Exported {len(chunks)} weighted chunks using '{weighting_strategy}' strategy")
    
    def _create_weighted_verse_chunk(self, verse, verse_number, chapter_num, chapter_title, strategy):
        """Create verse chunk with different weighting strategies"""
        
        if strategy == 'translation_first':
            # Translation gets highest priority, then purport, then others
            parts = []
            
            # Primary content (highest weight)
            if verse.get('translation'):
                parts.append(f"TRANSLATION: {verse['translation']}")
            
            # Secondary content (medium weight)  
            if verse.get('purport'):
                parts.append(f"COMMENTARY: {verse['purport']}")
            
            # Supporting content (lower weight)
            if verse.get('sanskrit_verse'):
                parts.append(f"Sanskrit: {verse['sanskrit_verse']}")
            if verse.get('synonyms'):
                parts.append(f"Word meanings: {verse['synonyms']}")
                
        elif strategy == 'commentary_focused':
            # Purport gets highest priority for deeper understanding
            parts = []
            
            if verse.get('purport'):
                parts.append(f"COMMENTARY: {verse['purport']}")
            if verse.get('translation'):
                parts.append(f"Translation: {verse['translation']}")
            if verse.get('synonyms'):
                parts.append(f"Word meanings: {verse['synonyms']}")
            if verse.get('sanskrit_verse'):
                parts.append(f"Sanskrit: {verse['sanskrit_verse']}")
                
        elif strategy == 'essential_only':
            # Only translation and purport for concise retrieval
            parts = []
            
            if verse.get('translation'):
                parts.append(verse['translation'])
            if verse.get('purport'):
                parts.append(verse['purport'])
                
        elif strategy == 'balanced':
            # Balanced approach with clear sections
            parts = []
            
            if verse.get('translation'):
                parts.append(f"Translation: {verse['translation']}")
            if verse.get('purport'):
                parts.append(f"Commentary: {verse['purport']}")
            if verse.get('synonyms'):
                parts.append(f"Word meanings: {verse['synonyms']}")
            if verse.get('sanskrit_verse'):
                parts.append(f"Sanskrit: {verse['sanskrit_verse']}")
        
        content = f"Verse {verse_number}\n\n" + "\n\n".join(parts)
        
        return {
            'id': f"bg_{chapter_num}_{verse_number.replace('.', '_')}_{strategy}",
            'content': content,
            'verse_number': verse_number,
            'chapter_number': chapter_num,
            'weighting_strategy': strategy,
            'source': 'Bhagavad Gita As It Is by A.C. Bhaktivedanta Swami Prabhupada',
            'metadata': {
                'chapter_title': chapter_title,
                'strategy': strategy,
                'content_priority': self._get_content_priority(strategy),
                'field_weights': self._get_field_weights(verse, strategy),
                'has_all_parts': all([
                    verse.get('sanskrit_verse'),
                    verse.get('synonyms'),
                    verse.get('translation'),
                    verse.get('purport')
                ])
            }
        }
    
    def _get_content_priority(self, strategy):
        """Get content priority order for different strategies"""
        priorities = {
            'translation_first': ['translation', 'purport', 'sanskrit', 'synonyms'],
            'commentary_focused': ['purport', 'translation', 'synonyms', 'sanskrit'],
            'essential_only': ['translation', 'purport'],
            'balanced': ['translation', 'purport', 'synonyms', 'sanskrit']
        }
        return priorities.get(strategy, [])
    
    def _get_field_weights(self, verse, strategy):
        """Calculate field weights based on strategy and content availability"""
        weights = {}
        
        if strategy == 'translation_first':
            weights = {
                'translation': 1.0,
                'purport': 0.8,
                'sanskrit': 0.4,
                'synonyms': 0.6
            }
        elif strategy == 'commentary_focused':
            weights = {
                'purport': 1.0,
                'translation': 0.9,
                'synonyms': 0.7,
                'sanskrit': 0.5
            }
        elif strategy == 'essential_only':
            weights = {
                'translation': 1.0,
                'purport': 0.9,
                'sanskrit': 0.0,
                'synonyms': 0.0
            }
        else:  # balanced
            weights = {
                'translation': 1.0,
                'purport': 0.9,
                'synonyms': 0.7,
                'sanskrit': 0.6
            }
        
        # Adjust weights based on content availability
        for field in weights:
            field_map = {
                'translation': 'translation',
                'purport': 'purport', 
                'sanskrit': 'sanskrit_verse',
                'synonyms': 'synonyms'
            }
            if not verse.get(field_map[field]):
                weights[field] = 0.0
        
        return weights

    def create_output_documentation(self):
        """Create documentation explaining the output directory structure"""
        os.makedirs('data', exist_ok=True)
        
        readme_content = """# Bhagavad Gita Data Export Structure

This directory contains the scraped and processed data from the Bhagavad Gita in various formats optimized for different use cases.

## Directory Structure

```
data/
├── raw/                     # Original scraped data
│   ├── bhagavad_gita_complete.json    # Complete dataset (all chapters)
│   └── chapters/                       # Individual chapter files
│       ├── chapter_01.json
│       ├── chapter_02.json
│       └── ...
├── processed/               # Human-readable formats
│   └── bhagavad_gita_complete.txt     # Formatted text for reading
└── rag/                     # RAG-optimized formats
    ├── standard/            # Standard RAG chunking strategies
    │   ├── bhagavad_gita_rag_verses.jsonl    # Individual verses (recommended)
    │   ├── bhagavad_gita_rag_verses.json     # Same as above, pretty-printed
    │   ├── bhagavad_gita_rag_sections.jsonl  # Grouped verses (5 per chunk)
    │   └── bhagavad_gita_rag_chapters.jsonl  # Complete chapters
    ├── weighted/            # Weighted content for different AI use cases
    │   ├── bhagavad_gita_rag_weighted_translation_first.jsonl
    │   ├── bhagavad_gita_rag_weighted_commentary_focused.jsonl
    │   ├── bhagavad_gita_rag_weighted_essential_only.jsonl
    │   └── bhagavad_gita_rag_weighted_balanced.jsonl
    └── flexible/            # Flexible format with all options
        └── bhagavad_gita_flexible.json       # Both separate & combined formats
```

## File Format Descriptions

### Raw Data (`data/raw/`)
- **Complete Dataset**: Full scraped data maintaining original structure
- **Individual Chapters**: Separate files for each of the 18 chapters
- **Use Case**: Backup, debugging, custom processing

### Processed Data (`data/processed/`)
- **Readable Text**: Human-formatted version for study and reading
- **Use Case**: Direct reading, documentation, verification

### RAG Formats (`data_bg/rag/`)

#### Standard RAG (`data_bg/rag/standard/`)
- **Verses (.jsonl)**: Individual verses as separate chunks - **RECOMMENDED for most RAG applications**
- **Sections (.jsonl)**: Verses grouped in sections of 5 for broader context
- **Chapters (.jsonl)**: Complete chapters for comprehensive context
- **Use Case**: Vector databases, semantic search, AI assistants

#### Weighted RAG (`data_bg/rag/weighted/`)
Different prioritization strategies for specialized AI use cases:

- **translation_first**: Prioritizes verse translations over commentary
  - Best for: General Q&A, introductory spiritual guidance
  
- **commentary_focused**: Prioritizes Prabhupada's purports (commentary)
  - Best for: Deep spiritual analysis, advanced study
  
- **essential_only**: Only translation + purport, no Sanskrit/synonyms
  - Best for: Concise responses, mobile apps, token-limited scenarios
  
- **balanced**: Equal weight to all parts
  - Best for: Comprehensive spiritual guidance, academic study

#### Flexible Format (`data_bg/rag/flexible/`)
- **Comprehensive Structure**: Includes both separate fields AND pre-combined formats
- **Multiple Content Formats**: RAG-optimized, structured reading, minimal AI
- **Rich Metadata**: Completeness analysis, content lengths, verse types
- **Use Case**: Custom applications, research, advanced AI systems

## Recommended Usage

### For Vector Databases / Semantic Search
Use: `data_bg/rag/standard/bhagavad_gita_rag_verses.jsonl`

### For AI Chatbots (General Purpose)
Use: `data_bg/rag/weighted/bhagavad_gita_rag_weighted_translation_first.jsonl`

### For Deep Spiritual AI Assistant
Use: `data_bg/rag/weighted/bhagavad_gita_rag_weighted_commentary_focused.jsonl`

### For Mobile/Limited Resources
Use: `data_bg/rag/weighted/bhagavad_gita_rag_weighted_essential_only.jsonl`

### For Custom Applications
Use: `data_bg/rag/flexible/bhagavad_gita_flexible.json`

## Data Quality & Validation

All exports include validation and completeness checking:
- Verse count verification against expected totals
- Content validation (minimum lengths, required fields)
- Failed URL tracking and reporting
- Metadata about data completeness and quality

## File Formats

- **.jsonl**: JSON Lines format (one JSON object per line) - optimal for streaming and vector DB ingestion
- **.json**: Pretty-printed JSON - easier for human inspection and debugging
- **.txt**: Plain text format - human-readable

## Source Information

- **Source**: Bhagavad Gita As It Is by A.C. Bhaktivedanta Swami Prabhupada
- **Website**: vedabase.io
- **Chapters**: 18 total chapters
- **Total Verses**: 700 individual verses
- **Content Parts**: Sanskrit (Devanagari), Transliteration, Synonyms, Translation, Purport

Generated on: {export_date}
"""
        
        with open('data/README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content.format(export_date='2025-06-24'))
        
        logger.info("Created output documentation: data/README.md")
def main():
    """Main function to run the scraper"""
    scraper = BhagavadGitaScraper()
    
    try:
        # Test with one chapter first
        print("Testing with Chapter 1...")
        test_chapter = scraper.scrape_chapter(1)
        
        if test_chapter['verses']:
            print(f"Test successful! Found {len(test_chapter['verses'])} verse entries in Chapter 1")
            print("\nValidation Report for Chapter 1:")
            print("-" * 40)
            
            # Show validation for test chapter
            scraper.chapters_data[1] = test_chapter
            print(scraper.get_validation_report())
            
            # Ask user if they want to proceed with all chapters
            proceed = input("\nDo you want to scrape all 18 chapters? (y/n): ").lower().strip()
            
            if proceed == 'y':
                # Create output documentation first
                scraper.create_output_documentation()
                
                scraper.scrape_all_chapters()
                scraper.save_data()
                
                # Show complete validation report
                print("\n" + "="*60)
                print("FINAL VALIDATION REPORT")
                print("="*60)
                print(scraper.get_validation_report())
                
                # Export for RAG
                print("\nExporting data for RAG applications...")
                scraper.export_for_rag(chunk_size='verse', include_metadata=True)
                scraper.export_for_rag(chunk_size='section', include_metadata=True)
                scraper.export_for_rag(chunk_size='chapter', include_metadata=True)
                
                # Export weighted versions for different use cases
                print("Exporting weighted RAG formats...")
                scraper.export_weighted_rag('translation_first')  # For general AI responses
                scraper.export_weighted_rag('commentary_focused')  # For deep spiritual guidance
                scraper.export_weighted_rag('essential_only')     # For concise answers
                scraper.export_weighted_rag('balanced')           # For comprehensive responses
                
                # Export flexible format
                print("Exporting flexible format...")
                scraper.export_flexible_format()
                
                # Create output documentation
                print("Creating output documentation...")
                scraper.create_output_documentation()
                
                print("\nExport completed! Files created:")
                print("\n📁 RAW DATA (data/raw/):")
                print("- bhagavad_gita_complete.json (complete dataset)")
                print("- chapters/chapter_XX.json (individual chapters)")
                print("\n📁 PROCESSED DATA (data/processed/):")
                print("- bhagavad_gita_complete.txt (human-readable format)")
                print("\n📁 RAG FORMATS (data_bg/rag/):")
                print("  📂 Standard RAG (data_bg/rag/standard/):")
                print("  - bhagavad_gita_rag_verses.jsonl (individual verses for vector DB)")
                print("  - bhagavad_gita_rag_verses.json     (same as above, pretty-printed)")
                print("  - bhagavad_gita_rag_sections.jsonl  (grouped verses)")  
                print("  - bhagavad_gita_rag_chapters.jsonl  (complete chapters)")
                print("  📂 Weighted RAG (data_bg/rag/weighted/):")
                print("  - bhagavad_gita_rag_weighted_translation_first.jsonl (translation priority)")
                print("  - bhagavad_gita_rag_weighted_commentary_focused.jsonl (purport priority)")
                print("  - bhagavad_gita_rag_weighted_essential_only.jsonl     (translation + purport only)")
                print("  - bhagavad_gita_rag_weighted_balanced.jsonl           (balanced approach)")
                print("  📂 Flexible Format (data_bg/rag/flexible/):")
                print("  - bhagavad_gita_flexible.json (both separate parts & combined formats)")
                print("\n📖 DOCUMENTATION:")
                print("- data/README.md (detailed explanation of all formats and usage)")
                
                print(scraper.get_stats())
            else:
                # Save just the test chapter
                scraper.create_output_documentation()
                scraper.save_data()
                scraper.export_for_rag(chunk_size='verse', include_metadata=True)
                print("Saved test chapter only.")
        else:
            print("Test failed. Please check the website structure and update the scraper.")
            print("\nValidation Report:")
            print(scraper.get_validation_report())
            
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        if scraper.chapters_data:
            scraper.save_data()
            print("Saved partial data")
            print("\nValidation Report:")
            print(scraper.get_validation_report())
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if scraper.chapters_data:
            scraper.save_data()
            print("Saved partial data due to error")
            print("\nValidation Report:")
            print(scraper.get_validation_report())

if __name__ == "__main__":
    main()
