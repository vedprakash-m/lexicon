import ebooklib
from ebooklib import epub
import zipfile
from bs4 import BeautifulSoup
from PIL import Image
import io
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re

@dataclass
class EbookExtractionResult:
    text: str
    metadata: Dict
    chapters: List[Dict]
    images: List[Dict]
    toc: List[Dict]
    extraction_method: str
    quality_score: float

class EbookProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def process_ebook(self, file_path: str) -> EbookExtractionResult:
        """Process EPUB/MOBI files"""
        if file_path.lower().endswith('.epub'):
            return self._process_epub(file_path)
        elif file_path.lower().endswith('.mobi'):
            return self._process_mobi(file_path)
        else:
            raise ValueError(f"Unsupported ebook format: {file_path}")
            
    def _process_epub(self, file_path: str) -> EbookExtractionResult:
        """Process EPUB files"""
        try:
            book = epub.read_epub(file_path)
        except Exception as e:
            self.logger.error(f"Failed to read EPUB: {e}")
            raise
            
        # Extract metadata
        metadata = {
            'title': book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else '',
            'creator': book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else '',
            'language': book.get_metadata('DC', 'language')[0][0] if book.get_metadata('DC', 'language') else '',
            'publisher': book.get_metadata('DC', 'publisher')[0][0] if book.get_metadata('DC', 'publisher') else '',
            'date': book.get_metadata('DC', 'date')[0][0] if book.get_metadata('DC', 'date') else '',
            'identifier': book.get_metadata('DC', 'identifier')[0][0] if book.get_metadata('DC', 'identifier') else '',
            'subject': book.get_metadata('DC', 'subject')[0][0] if book.get_metadata('DC', 'subject') else '',
            'description': book.get_metadata('DC', 'description')[0][0] if book.get_metadata('DC', 'description') else '',
            'rights': book.get_metadata('DC', 'rights')[0][0] if book.get_metadata('DC', 'rights') else '',
        }
        
        # Extract chapters
        chapters = []
        text_parts = []
        
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                
                # Extract chapter title
                title_elem = soup.find(['h1', 'h2', 'h3', 'title'])
                chapter_title = title_elem.get_text().strip() if title_elem else f"Chapter {len(chapters) + 1}"
                
                # Extract text
                chapter_text = soup.get_text()
                
                # Clean up text
                lines = (line.strip() for line in chapter_text.splitlines())
                chapter_text = '\n'.join(line for line in lines if line)
                
                chapters.append({
                    'title': chapter_title,
                    'text': chapter_text,
                    'word_count': len(chapter_text.split()),
                    'id': item.get_id(),
                    'file_name': item.get_name(),
                })
                
                text_parts.append(chapter_text)
                
        full_text = '\n\n'.join(text_parts)
        
        # Extract images
        images = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_IMAGE:
                try:
                    img_data = item.get_content()
                    img = Image.open(io.BytesIO(img_data))
                    
                    images.append({
                        'id': item.get_id(),
                        'file_name': item.get_name(),
                        'media_type': item.get_media_type(),
                        'size': len(img_data),
                        'dimensions': img.size,
                        'format': img.format,
                    })
                except Exception as e:
                    self.logger.warning(f"Failed to process image {item.get_name()}: {e}")
                    
        # Extract table of contents
        toc = self._extract_toc(book)
        
        # Calculate quality score
        total_words = sum(chapter['word_count'] for chapter in chapters)
        quality_score = min(1.0, total_words / 1000)  # Assume good quality if >1000 words
        
        return EbookExtractionResult(
            text=full_text,
            metadata=metadata,
            chapters=chapters,
            images=images,
            toc=toc,
            extraction_method='epub',
            quality_score=quality_score
        )
        
    def _process_mobi(self, file_path: str) -> EbookExtractionResult:
        """Process MOBI files (basic support)"""
        # Note: Full MOBI support requires additional libraries like mobidedrm
        # This is a basic implementation that treats MOBI as a zip-like format
        
        try:
            with zipfile.ZipFile(file_path, 'r') as mobi_file:
                # Try to extract HTML content
                html_files = [f for f in mobi_file.namelist() if f.endswith('.html') or f.endswith('.htm')]
                
                chapters = []
                text_parts = []
                
                for html_file in html_files:
                    content = mobi_file.read(html_file).decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Extract chapter title
                    title_elem = soup.find(['h1', 'h2', 'h3', 'title'])
                    chapter_title = title_elem.get_text().strip() if title_elem else f"Chapter {len(chapters) + 1}"
                    
                    # Extract text
                    chapter_text = soup.get_text()
                    lines = (line.strip() for line in chapter_text.splitlines())
                    chapter_text = '\n'.join(line for line in lines if line)
                    
                    chapters.append({
                        'title': chapter_title,
                        'text': chapter_text,
                        'word_count': len(chapter_text.split()),
                        'file_name': html_file,
                    })
                    
                    text_parts.append(chapter_text)
                    
                full_text = '\n\n'.join(text_parts)
                
                # Basic metadata extraction
                metadata = {
                    'title': 'Unknown MOBI Book',
                    'creator': 'Unknown',
                    'format': 'MOBI',
                }
                
                # Try to extract metadata from OPF file if present
                opf_files = [f for f in mobi_file.namelist() if f.endswith('.opf')]
                if opf_files:
                    opf_content = mobi_file.read(opf_files[0]).decode('utf-8', errors='ignore')
                    opf_soup = BeautifulSoup(opf_content, 'xml')
                    
                    title_elem = opf_soup.find('dc:title')
                    if title_elem:
                        metadata['title'] = title_elem.get_text().strip()
                        
                    creator_elem = opf_soup.find('dc:creator')
                    if creator_elem:
                        metadata['creator'] = creator_elem.get_text().strip()
                        
                total_words = sum(chapter['word_count'] for chapter in chapters)
                quality_score = min(1.0, total_words / 1000)
                
                return EbookExtractionResult(
                    text=full_text,
                    metadata=metadata,
                    chapters=chapters,
                    images=[],  # Image extraction not implemented for MOBI
                    toc=[],     # TOC extraction not implemented for MOBI
                    extraction_method='mobi',
                    quality_score=quality_score
                )
                
        except zipfile.BadZipFile:
            # MOBI files are not always zip files, need specialized parser
            self.logger.error("MOBI file is not in zip format, specialized parser needed")
            raise ValueError("MOBI format not fully supported - requires specialized parser")
            
    def _extract_toc(self, book) -> List[Dict]:
        """Extract table of contents from EPUB"""
        toc_items = []
        
        def process_toc_item(item, level=0):
            if isinstance(item, tuple):
                # (Section, [children])
                section, children = item
                toc_items.append({
                    'title': section.title,
                    'href': section.href,
                    'level': level,
                })
                for child in children:
                    process_toc_item(child, level + 1)
            elif hasattr(item, 'title'):
                # Simple section
                toc_items.append({
                    'title': item.title,
                    'href': getattr(item, 'href', ''),
                    'level': level,
                })
                
        for item in book.toc:
            process_toc_item(item)
            
        return toc_items
        
    def extract_cover_image(self, file_path: str) -> Optional[bytes]:
        """Extract cover image from ebook"""
        if file_path.lower().endswith('.epub'):
            try:
                book = epub.read_epub(file_path)
                
                # Look for cover image
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_IMAGE:
                        if 'cover' in item.get_name().lower():
                            return item.get_content()
                            
                # If no explicit cover, try first image
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_IMAGE:
                        return item.get_content()
                        
            except Exception as e:
                self.logger.error(f"Failed to extract cover: {e}")
                
        return None