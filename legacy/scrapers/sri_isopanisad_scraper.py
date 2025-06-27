#!/usr/bin/env python3
"""
Śrī Īśopaniṣad Text Scraper

This script scrapes the complete text of Śrī Īśopaniṣad from vedabase.io
for use in an AI agent application. It extracts all mantras (verses), translations,
and purports.

Author: Ved Mishra
Date: June 25, 2025
"""

import requests
import json
import os
import time
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sri_isopanisad_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SriIsopanisadScraper:
    """Scraper for extracting Śrī Īśopaniṣad text from vedabase.io"""
    
    def __init__(self):
        self.base_url = "https://vedabase.io/en/library/iso/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.isopanisad_data = {}
        self.delay = 1  # Delay between requests in seconds
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delays = [2, 5, 10]  # Progressive delays in seconds
        
        # Tracking and validation
        self.expected_mantras = 19  # Śrī Īśopaniṣad has 1 invocation + 18 mantras
        self.scraped_urls = set()  # Track what we've scraped
        self.failed_urls = set()   # Track failed URLs
        self.validation_errors = []  # Track validation issues
    
    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a webpage with retry mechanism"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching: {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                self.scraped_urls.add(url)
                
                # Add delay to be respectful to the server
                time.sleep(self.delay)
                return soup
                
            except requests.RequestException as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[attempt]
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
        
        logger.error(f"All attempts failed for {url}: {last_exception}")
        self.failed_urls.add(url)
        return None
    
    def extract_mantra_content(self, soup: BeautifulSoup) -> Dict:
        """Extract mantra content from a page"""
        content = {
            'mantra_number': '',
            'mantra_numbers': [],  # For grouped mantras if any
            'sanskrit_mantra': '',           # Part 1: Sanskrit text
            'sanskrit_transliteration': '', # Part 1: Roman transliteration 
            'synonyms': '',                 # Part 2: Word-by-word meanings
            'translation': '',              # Part 3: Complete translation
            'purport': ''                   # Part 4: Commentary/explanation
        }
        
        try:
            # Extract mantra number from h1 tag (e.g., "Iso 1" or "Iso Invocation")
            title = soup.find('h1')
            if title:
                title_text = title.get_text(strip=True)
                content['mantra_number'] = title_text
                
                # Extract individual mantra numbers for tracking
                if 'Iso' in title_text:
                    if 'Invocation' in title_text:
                        content['mantra_numbers'] = ['invocation']
                    else:
                        try:
                            # Extract number from "Iso 1" format
                            mantra_num = title_text.replace('Iso', '').strip()
                            if mantra_num.isdigit():
                                content['mantra_numbers'] = [mantra_num]
                            elif '-' in mantra_num:
                                # Handle ranges like "1-3"
                                start, end = mantra_num.split('-')
                                content['mantra_numbers'] = [str(i) for i in range(int(start), int(end) + 1)]
                        except (ValueError, IndexError):
                            content['mantra_numbers'] = []
            
            # Find the main Sanskrit text (usually the first paragraph after h1, before any h2)
            # Look for the text that contains Devanagari script
            first_content = None
            h1_element = soup.find('h1')
            if h1_element:
                # Find the next element after h1 that contains substantial text
                current = h1_element.find_next()
                while current:
                    if current.name == 'h2':
                        break  # Stop if we hit a section heading
                    if current.name == 'p' and current.get_text(strip=True):
                        text = current.get_text(strip=True)
                        # Check if this contains Devanagari (Sanskrit) or transliteration
                        if any('\u0900' <= char <= '\u097F' for char in text) and len(text) > 10:
                            content['sanskrit_mantra'] = text
                        elif not content['sanskrit_mantra'] and any(char in text for char in ['ā', 'ī', 'ū', 'ṛ', 'ṁ', 'ḥ']) and len(text) > 10:
                            content['sanskrit_transliteration'] = text
                        elif not first_content:
                            first_content = text
                        break
                    current = current.find_next()
            
            # If we didn't find Sanskrit in Devanagari, use the transliteration we found or the first content
            if not content['sanskrit_mantra'] and content['sanskrit_transliteration']:
                # Move transliteration to sanskrit_mantra if no Devanagari was found
                content['sanskrit_mantra'] = content['sanskrit_transliteration']
                content['sanskrit_transliteration'] = ''
            elif not content['sanskrit_mantra'] and first_content:
                content['sanskrit_mantra'] = first_content
            
            # Extract sections based on h2 headings - look for the content after each h2
            sections_of_interest = ['verse text', 'synonyms', 'translation', 'purport']
            
            for section in sections_of_interest:
                section_h2 = soup.find('h2', string=lambda text: text and section.lower() in text.lower())
                
                if section_h2:
                    # Get the content after this h2
                    content_elem = section_h2.find_next_sibling()
                    section_content = []
                    
                    while content_elem and content_elem.name != 'h2':
                        if content_elem.name in ['div', 'p']:
                            text = content_elem.get_text(strip=True)
                            if text and len(text) > 10:  # Avoid empty or very short text
                                section_content.append(text)
                        content_elem = content_elem.find_next_sibling()
                    
                    # Process the extracted content based on section type
                    if section_content:
                        if section == 'verse text':
                            # First item is usually the main verse text (Sanskrit/transliteration)
                            if section_content[0]:
                                # Check if it contains Devanagari characters
                                if any('\u0900' <= char <= '\u097F' for char in section_content[0]):
                                    content['sanskrit_mantra'] = section_content[0]
                                else:
                                    # It's transliterated Sanskrit - assign to both fields for completeness
                                    content['sanskrit_transliteration'] = section_content[0]
                                    # For Īśopaniṣad, the transliteration IS the Sanskrit text provided
                                    content['sanskrit_mantra'] = section_content[0]
                        elif section == 'synonyms':
                            content['synonyms'] = ' '.join(section_content)
                        elif section == 'translation':
                            content['translation'] = ' '.join(section_content)
                        elif section == 'purport':
                            content['purport'] = ' '.join(section_content)
            
            # Clean up the extracted content
            for key in ['synonyms', 'translation', 'purport']:
                if content[key]:
                    # Remove extra whitespace and normalize
                    content[key] = ' '.join(content[key].split())
                        
        except Exception as e:
            logger.error(f"Error extracting mantra content: {e}")
        
        return content
    
    def discover_mantra_urls(self) -> List[str]:
        """Discover all mantra URLs by parsing the main index"""
        logger.info("Discovering mantra URLs for Śrī Īśopaniṣad")
        
        soup = self.get_page_content(self.base_url)
        
        if not soup:
            logger.error("Failed to fetch main Īśopaniṣad page")
            return []
        
        mantra_urls = []
        
        # Manually add the invocation URL since it's essential
        invocation_url = "https://vedabase.io/en/library/iso/invocation/"
        mantra_urls.append(invocation_url)
        
        # Look for links that match mantra patterns
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                href = urljoin("https://vedabase.io", href)
            
            # Look for mantra-specific links (numbered 1-18)
            if '/iso/' in href and href.endswith('/'):
                # Check if this is a numbered mantra (1 through 18)
                url_parts = href.rstrip('/').split('/')
                if url_parts:
                    last_part = url_parts[-1]
                    if last_part.isdigit() and 1 <= int(last_part) <= 18:
                        mantra_urls.append(href)
        
        # Remove duplicates and sort
        mantra_urls = list(set(mantra_urls))
        mantra_urls.sort(key=lambda x: self._extract_mantra_sort_key(x))
        
        logger.info(f"Found {len(mantra_urls)} mantra URLs")
        for url in mantra_urls:
            logger.info(f"  - {url}")
        
        return mantra_urls
    
    def _extract_mantra_sort_key(self, url: str):
        """Extract a sort key from mantra URL for proper ordering"""
        try:
            # Extract number from URL
            if 'invocation' in url.lower():
                return 0  # Invocation comes first
            else:
                # Try to extract mantra number
                parts = url.split('/')
                for part in reversed(parts):
                    if part.isdigit():
                        return int(part)
            return 999  # Unknown, put at end
        except (ValueError, IndexError):
            return 999
    
    def scrape_all_mantras(self):
        """Scrape all mantras of Śrī Īśopaniṣad"""
        logger.info("Starting to scrape all mantras of Śrī Īśopaniṣad")
        
        # Discover all mantra URLs
        mantra_urls = self.discover_mantra_urls()
        
        if not mantra_urls:
            logger.error("No mantra URLs found")
            return
        
        mantras = []
        
        # Scrape each mantra URL
        for mantra_url in mantra_urls:
            logger.info(f"Scraping: {mantra_url}")
            
            soup = self.get_page_content(mantra_url)
            if not soup:
                logger.error(f"Failed to scrape: {mantra_url}")
                continue
            
            mantra_content = self.extract_mantra_content(soup)
            
            # Validate content
            if self.validate_mantra_content(mantra_content, mantra_url):
                mantras.append(mantra_content)
                logger.info(f"Successfully scraped: {mantra_content.get('mantra_number', 'Unknown')}")
            else:
                logger.warning(f"Poor quality content for: {mantra_url}")
        
        # Store the data
        self.isopanisad_data = {
            'title': 'Śrī Īśopaniṣad',
            'subtitle': 'The knowledge that brings one nearer to the Supreme Personality of Godhead',
            'author': 'A.C. Bhaktivedanta Swami Prabhupāda',
            'total_mantras': len(mantras),
            'mantras': mantras
        }
        
        logger.info(f"Completed scraping. Total mantras: {len(mantras)}")
    
    def validate_mantra_content(self, mantra_content: Dict, url: str) -> bool:
        """Validate that a mantra has meaningful content"""
        errors = []
        
        # Check if mantra has basic required fields
        if not mantra_content.get('mantra_number'):
            errors.append("Missing mantra number")
        
        # Translation is essential - every mantra should have this
        if not mantra_content.get('translation'):
            errors.append("Missing translation")
        elif len(mantra_content['translation']) < 20:
            errors.append("Translation too short")
        
        # At least one substantial content field should exist
        substantial_content = any([
            mantra_content.get('translation') and len(mantra_content['translation']) >= 20,
            mantra_content.get('purport') and len(mantra_content['purport']) >= 50,
            mantra_content.get('synonyms') and len(mantra_content['synonyms']) >= 20
        ])
        
        if not substantial_content:
            errors.append("No substantial content found")
        
        if errors:
            error_msg = f"Validation failed for {url}: {'; '.join(errors)}"
            logger.warning(error_msg)
            self.validation_errors.append(error_msg)
            return False
        
        # Log if mantra lacks purport (for info, not error)
        if not mantra_content.get('purport'):
            logger.info(f"Mantra {mantra_content.get('mantra_number')} lacks purport")
        
        return True
    
    def save_data(self, output_format='json'):
        """Save the scraped data to files"""
        if not self.isopanisad_data:
            logger.error("No data to save")
            return
        
        # Create organized output directory structure
        os.makedirs('data_iso/raw', exist_ok=True)
        os.makedirs('data_iso/processed', exist_ok=True)
        
        if output_format == 'json':
            # Save complete data as JSON
            with open('data_iso/raw/sri_isopanisad_complete.json', 'w', encoding='utf-8') as f:
                json.dump(self.isopanisad_data, f, ensure_ascii=False, indent=2)
        
        # Also save as plain text for easy reading
        with open('data_iso/processed/sri_isopanisad_complete.txt', 'w', encoding='utf-8') as f:
            f.write(f"{self.isopanisad_data['title']}\n")
            f.write(f"{self.isopanisad_data['subtitle']}\n")
            f.write(f"by {self.isopanisad_data['author']}\n")
            f.write("=" * 80 + "\n\n")
            
            for mantra in self.isopanisad_data['mantras']:
                f.write(f"MANTRA: {mantra.get('mantra_number', 'Unknown')}\n")
                f.write("-" * 40 + "\n")
                
                if mantra.get('sanskrit_mantra'):
                    f.write(f"Sanskrit:\n{mantra['sanskrit_mantra']}\n\n")
                
                if mantra.get('sanskrit_transliteration'):
                    f.write(f"Transliteration:\n{mantra['sanskrit_transliteration']}\n\n")
                
                if mantra.get('synonyms'):
                    f.write(f"Synonyms:\n{mantra['synonyms']}\n\n")
                
                if mantra.get('translation'):
                    f.write(f"Translation:\n{mantra['translation']}\n\n")
                
                if mantra.get('purport'):
                    f.write(f"Purport:\n{mantra['purport']}\n\n")
                
                f.write("=" * 80 + "\n\n")
        
        logger.info("Data saved successfully")
    
    def get_stats(self):
        """Get statistics about the scraped data"""
        if not self.isopanisad_data:
            return "No data available"
        
        total_mantras = len(self.isopanisad_data['mantras'])
        
        # Count content quality
        mantras_with_sanskrit = 0
        mantras_with_translation = 0
        mantras_with_purport = 0
        mantras_with_synonyms = 0
        
        for mantra in self.isopanisad_data['mantras']:
            if mantra.get('sanskrit_mantra'):
                mantras_with_sanskrit += 1
            if mantra.get('translation'):
                mantras_with_translation += 1
            if mantra.get('purport'):
                mantras_with_purport += 1
            if mantra.get('synonyms'):
                mantras_with_synonyms += 1
        
        stats = f"""
Śrī Īśopaniṣad Scraping Statistics:
- Total Mantras: {total_mantras}
- Expected Mantras: {self.expected_mantras}
- Completion: {total_mantras/self.expected_mantras*100:.1f}%

Content Quality:
- Mantras with Sanskrit: {mantras_with_sanskrit} ({mantras_with_sanskrit/total_mantras*100:.1f}%)
- Mantras with Translation: {mantras_with_translation} ({mantras_with_translation/total_mantras*100:.1f}%)
- Mantras with Purport: {mantras_with_purport} ({mantras_with_purport/total_mantras*100:.1f}%)
- Mantras with Synonyms: {mantras_with_synonyms} ({mantras_with_synonyms/total_mantras*100:.1f}%)

URLs:
- Successfully scraped: {len(self.scraped_urls)}
- Failed URLs: {len(self.failed_urls)}
- Validation errors: {len(self.validation_errors)}
"""
        return stats
    
    def export_for_rag(self, chunk_size='mantra', include_metadata=True):
        """Export data optimized for RAG (Retrieval Augmented Generation) systems"""
        if not self.isopanisad_data:
            logger.error("No data to export")
            return
        
        # Create organized RAG export directory structure
        os.makedirs('data_iso/rag/standard', exist_ok=True)
        
        if chunk_size == 'mantra':
            self._export_mantra_chunks(include_metadata)
        elif chunk_size == 'complete':
            self._export_complete_chunks(include_metadata)
        
        logger.info(f"RAG export completed with {chunk_size}-level chunking")
    
    def _export_mantra_chunks(self, include_metadata=True):
        """Export individual mantras as separate chunks"""
        chunks = []
        
        for mantra in self.isopanisad_data['mantras']:
            mantra_number = mantra.get('mantra_number', 'Unknown')
            
            # Create combined content
            content_parts = []
            
            if mantra.get('sanskrit_mantra'):
                content_parts.append(f"Sanskrit: {mantra['sanskrit_mantra']}")
            
            if mantra.get('sanskrit_transliteration'):
                content_parts.append(f"Transliteration: {mantra['sanskrit_transliteration']}")
            
            if mantra.get('synonyms'):
                content_parts.append(f"Word-for-word meaning: {mantra['synonyms']}")
            
            if mantra.get('translation'):
                content_parts.append(f"Translation: {mantra['translation']}")
            
            if mantra.get('purport'):
                content_parts.append(f"Purport: {mantra['purport']}")
            
            full_content = f"Mantra {mantra_number}\n\n" + "\n\n".join(content_parts)
            
            chunk = {
                'id': f"iso_{mantra_number.replace('.', '_').replace(' ', '_').lower()}",
                'content': full_content,
                'mantra_number': mantra_number,
                'source': 'Śrī Īśopaniṣad by A.C. Bhaktivedanta Swami Prabhupāda',
                'parts': {
                    'sanskrit_mantra': mantra.get('sanskrit_mantra', ''),
                    'sanskrit_transliteration': mantra.get('sanskrit_transliteration', ''),
                    'synonyms': mantra.get('synonyms', ''),
                    'translation': mantra.get('translation', ''),
                    'purport': mantra.get('purport', '')
                }
            }
            
            if include_metadata:
                chunk['metadata'] = {
                    'has_sanskrit': bool(mantra.get('sanskrit_mantra')),
                    'has_transliteration': bool(mantra.get('sanskrit_transliteration')),
                    'has_synonyms': bool(mantra.get('synonyms')),
                    'has_translation': bool(mantra.get('translation')),
                    'has_purport': bool(mantra.get('purport')),
                    'content_length': len(full_content),
                    'scripture': 'Śrī Īśopaniṣad'
                }
            
            chunks.append(chunk)
        
        # Save as JSON Lines format
        with open('data_iso/rag/standard/sri_isopanisad_rag_mantras.jsonl', 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
        
        # Also save as regular JSON
        with open('data_iso/rag/standard/sri_isopanisad_rag_mantras.json', 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported {len(chunks)} mantra chunks for RAG")
    
    def _export_complete_chunks(self, include_metadata=True):
        """Export complete Īśopaniṣad as a single chunk"""
        # Create combined content for entire Īśopaniṣad
        content_parts = [
            f"{self.isopanisad_data['title']}",
            f"{self.isopanisad_data['subtitle']}",
            f"by {self.isopanisad_data['author']}",
            ""
        ]
        
        for mantra in self.isopanisad_data['mantras']:
            mantra_content = []
            mantra_number = mantra.get('mantra_number', 'Unknown')
            
            mantra_content.append(f"Mantra {mantra_number}")
            
            if mantra.get('sanskrit_mantra'):
                mantra_content.append(f"Sanskrit: {mantra['sanskrit_mantra']}")
            
            if mantra.get('translation'):
                mantra_content.append(f"Translation: {mantra['translation']}")
            
            if mantra.get('purport'):
                mantra_content.append(f"Purport: {mantra['purport']}")
            
            content_parts.append("\n".join(mantra_content))
        
        full_content = "\n\n".join(content_parts)
        
        chunk = {
            'id': 'iso_complete',
            'content': full_content,
            'source': 'Śrī Īśopaniṣad by A.C. Bhaktivedanta Swami Prabhupāda',
            'total_mantras': len(self.isopanisad_data['mantras'])
        }
        
        if include_metadata:
            chunk['metadata'] = {
                'scripture': 'Śrī Īśopaniṣad',
                'content_length': len(full_content),
                'total_mantras': len(self.isopanisad_data['mantras']),
                'chunk_type': 'complete_scripture'
            }
        
        # Save as JSON
        with open('data_iso/rag/standard/sri_isopanisad_rag_complete.json', 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)
        
        logger.info("Exported complete Īśopaniṣad chunk for RAG")
    
    def get_validation_report(self) -> str:
        """Generate a comprehensive validation report"""
        if not self.isopanisad_data:
            return "No data available for validation"
        
        report = ["VALIDATION REPORT - ŚRĪ ĪŚOPANIṢAD", "=" * 50]
        
        total_mantras = len(self.isopanisad_data['mantras'])
        
        report.extend([
            f"Total Mantras: {total_mantras}/{self.expected_mantras}",
            f"Completion: {total_mantras/self.expected_mantras*100:.1f}%",
            f"Successfully Scraped URLs: {len(self.scraped_urls)}",
            f"Failed URLs: {len(self.failed_urls)}",
            "",
            "MANTRA BREAKDOWN:",
            "-" * 30
        ])
        
        # Mantra-by-mantra validation
        for i, mantra in enumerate(self.isopanisad_data['mantras'], 1):
            mantra_number = mantra.get('mantra_number', f'Mantra {i}')
            has_sanskrit = bool(mantra.get('sanskrit_mantra'))
            has_translation = bool(mantra.get('translation'))
            has_purport = bool(mantra.get('purport'))
            has_synonyms = bool(mantra.get('synonyms'))
            
            status = "✅ COMPLETE" if all([has_translation, has_purport]) else "⚠️ INCOMPLETE"
            
            report.append(f"{mantra_number}: {status}")
            report.append(f"  Sanskrit: {'✓' if has_sanskrit else '✗'}")
            report.append(f"  Translation: {'✓' if has_translation else '✗'}")
            report.append(f"  Purport: {'✓' if has_purport else '✗'}")
            report.append(f"  Synonyms: {'✓' if has_synonyms else '✗'}")
            report.append("")
        
        # Validation errors
        if self.validation_errors:
            report.extend([
                "VALIDATION ERRORS:",
                "-" * 20
            ])
            for error in self.validation_errors:
                report.append(f"• {error}")
            report.append("")
        
        # Failed URLs
        if self.failed_urls:
            report.extend([
                "FAILED URLS:",
                "-" * 15
            ])
            for url in self.failed_urls:
                report.append(f"• {url}")
        
        return "\n".join(report)

def main():
    """Main function to run the scraper"""
    scraper = SriIsopanisadScraper()
    
    try:
        print("Starting Śrī Īśopaniṣad scraping...")
        scraper.scrape_all_mantras()
        
        if scraper.isopanisad_data:
            print("\n" + scraper.get_stats())
            
            # Save data
            scraper.save_data()
            
            # Export for RAG
            scraper.export_for_rag('mantra')
            scraper.export_for_rag('complete')
            
            # Show validation report
            print("\n" + scraper.get_validation_report())
            
            print("\n🎉 Śrī Īśopaniṣad scraping completed successfully!")
        else:
            print("❌ No data was scraped")
            
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        if scraper.isopanisad_data:
            print("Saving partial data...")
            scraper.save_data()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if scraper.isopanisad_data:
            print("Saving partial data...")
            scraper.save_data()

if __name__ == "__main__":
    main()
