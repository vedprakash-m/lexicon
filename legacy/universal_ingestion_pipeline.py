"""
Universal Ingestion Pipeline - Stage 2: Content Extraction & Processing
======================================================================

This module provides the universal ingestion system that can handle multiple
content sources and formats. It serves as a wrapper around existing specialized
scrapers while extending support to new formats like PDF, EPUB, etc.

Key Features:
- Wrapper around existing BG, SB, ISO scrapers (keeps them as specialized solutions)
- PDF extraction with multiple fallback methods
- EPUB/MOBI/DOCX support
- Web scraping for various sites
- Quality validation and metadata extraction
- Standardized output format

Author: RAG Dataset Architecture Project
"""

import json
import logging
import requests
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from abc import ABC, abstractmethod

# Third-party imports (install as needed)
try:
    import PyPDF2
    import fitz  # PyMuPDF
    HAS_PDF_SUPPORT = True
except ImportError:
    HAS_PDF_SUPPORT = False
    
try:
    import ebooklib
    from ebooklib import epub
    HAS_EPUB_SUPPORT = True
except ImportError:
    HAS_EPUB_SUPPORT = False

try:
    from bs4 import BeautifulSoup
    HAS_WEB_SCRAPING = True
except ImportError:
    HAS_WEB_SCRAPING = False

# Import existing scrapers as specialized solutions
try:
    from bhagavad_gita_scraper import BhagavadGitaScraper
    from srimad_bhagavatam_scraper import SrimadBhagavatamScraper  
    from sri_isopanisad_scraper import SriIsopanisadScraper
    HAS_SCRIPTURE_SCRAPERS = True
except ImportError:
    HAS_SCRIPTURE_SCRAPERS = False

from book_registry_manager import BookRegistryManager, ProcessingStage, BookStatus, QualityReport

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ContentUnit:
    """Universal content unit structure"""
    id: str
    content: str
    content_type: str  # chapter, section, verse, paragraph, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    position: int = 0


@dataclass
class ProcessedContent:
    """Processed content with metadata"""
    book_id: str
    title: str
    author: str
    content_units: List[ContentUnit]
    metadata: Dict[str, Any]
    quality_metrics: Dict[str, float]
    extraction_notes: List[str] = field(default_factory=list)


@dataclass
class IngestionResult:
    """Result of content ingestion process"""
    book_id: str
    success: bool
    content: Optional[ProcessedContent] = None
    error_message: Optional[str] = None
    quality_score: float = 0.0
    extraction_time_seconds: float = 0.0


# ============================================================================
# CONTENT PROCESSORS (Abstract Base)
# ============================================================================

class ContentProcessor(ABC):
    """Abstract base class for all content processors"""
    
    @abstractmethod
    def can_process(self, source_info: Dict[str, Any]) -> bool:
        """Check if this processor can handle the given source"""
        pass
    
    @abstractmethod
    def extract_content(self, source_info: Dict[str, Any]) -> ProcessedContent:
        """Extract content from the source"""
        pass
    
    def validate_extraction(self, content: ProcessedContent) -> QualityReport:
        """Validate the extracted content quality"""
        issues = []
        recommendations = []
        
        # Basic validation checks
        content_completeness = 1.0
        extraction_accuracy = 1.0
        chunk_quality = 1.0
        
        if not content.content_units:
            issues.append("No content units extracted")
            content_completeness = 0.0
        elif len(content.content_units) < 5:
            issues.append("Very few content units extracted")
            content_completeness = 0.5
            recommendations.append("Check extraction parameters or source quality")
        
        # Check for empty content
        empty_units = [unit for unit in content.content_units if not unit.content.strip()]
        if empty_units:
            issues.append(f"{len(empty_units)} empty content units found")
            extraction_accuracy -= 0.2
            recommendations.append("Review extraction logic to avoid empty units")
        
        # Check content length distribution
        lengths = [len(unit.content) for unit in content.content_units]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            if avg_length < 50:
                issues.append("Content units are very short")
                chunk_quality -= 0.3
                recommendations.append("Consider different chunking strategy")
        
        overall_score = (content_completeness + extraction_accuracy + chunk_quality) / 3
        
        return QualityReport(
            book_id=content.book_id,
            overall_score=max(0.0, overall_score),
            content_completeness=content_completeness,
            extraction_accuracy=extraction_accuracy,
            chunk_quality=chunk_quality,
            issues_found=issues,
            recommendations=recommendations
        )


# ============================================================================
# SPECIALIZED SCRIPTURE PROCESSOR (Wrapper)
# ============================================================================

class ScriptureProcessor(ContentProcessor):
    """Wrapper around existing scripture scrapers (BG, SB, ISO)"""
    
    def __init__(self):
        self.scrapers = {}
        if HAS_SCRIPTURE_SCRAPERS:
            self.scrapers = {
                'bhagavad_gita': BhagavadGitaScraper(),
                'srimad_bhagavatam': SrimadBhagavatamScraper(),
                'sri_isopanisad': SriIsopanisadScraper()
            }
    
    def can_process(self, source_info: Dict[str, Any]) -> bool:
        """Check if this is a supported Vedabase scripture"""
        source_type = source_info.get('source_type', '')
        source_url = source_info.get('source_url', '')
        
        if source_type != 'web_scraping':
            return False
        
        # Check if it's a Vedabase URL for supported scriptures
        supported_patterns = [
            'vedabase.io/en/library/bg/',
            'vedabase.io/en/library/sb/',
            'vedabase.io/en/library/iso/'
        ]
        
        return any(pattern in source_url for pattern in supported_patterns)
    
    def extract_content(self, source_info: Dict[str, Any]) -> ProcessedContent:
        """Use existing specialized scrapers"""
        source_url = source_info.get('source_url', '')
        book_id = source_info.get('id', 'unknown')
        title = source_info.get('title', 'Unknown')
        author = source_info.get('author', 'Unknown')
        
        # Determine which scraper to use
        if 'bg/' in source_url:
            scripture_type = 'bhagavad_gita'
        elif 'sb/' in source_url:
            scripture_type = 'srimad_bhagavatam'
        elif 'iso/' in source_url:
            scripture_type = 'sri_isopanisad'
        else:
            raise ValueError(f"Unsupported scripture URL: {source_url}")
        
        if scripture_type not in self.scrapers:
            raise ValueError(f"Scraper not available for {scripture_type}")
        
        # Use existing scraper (they already save to their respective directories)
        scraper = self.scrapers[scripture_type]
        
        try:
            # For existing scrapers, we assume they work as before
            # and we read their output to create our unified format
            result = self._load_existing_scripture_data(scripture_type, book_id, title, author)
            return result
            
        except Exception as e:
            logger.error(f"Scripture extraction failed: {e}")
            # Return empty result for now
            return ProcessedContent(
                book_id=book_id,
                title=title,
                author=author,
                content_units=[],
                metadata={"extraction_error": str(e)},
                quality_metrics={"overall": 0.0},
                extraction_notes=[f"Extraction failed: {e}"]
            )
    
    def _load_existing_scripture_data(self, scripture_type: str, book_id: str, 
                                    title: str, author: str) -> ProcessedContent:
        """Load data from existing scripture files"""
        
        # Map scripture types to data directories
        data_dirs = {
            'bhagavad_gita': 'data_bg',
            'srimad_bhagavatam': 'data_sb', 
            'sri_isopanisad': 'data_iso'
        }
        
        data_dir = Path(data_dirs[scripture_type])
        raw_file = data_dir / "raw" / f"{scripture_type.replace('_', '_')}_complete.json"
        
        if not raw_file.exists():
            raise FileNotFoundError(f"Raw scripture data not found: {raw_file}")
        
        # Load the raw data
        with open(raw_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # Convert to universal content units
        content_units = self._convert_scripture_to_units(raw_data, scripture_type)
        
        return ProcessedContent(
            book_id=book_id,
            title=title,
            author=author,
            content_units=content_units,
            metadata={
                "source_type": "vedabase_scraping",
                "scripture_type": scripture_type,
                "total_units": len(content_units)
            },
            quality_metrics={"overall": 0.95},  # High quality for existing data
            extraction_notes=["Loaded from existing scripture data"]
        )
    
    def _convert_scripture_to_units(self, raw_data: Dict, scripture_type: str) -> List[ContentUnit]:
        """Convert scripture data to universal content units"""
        units = []
        
        if scripture_type == 'sri_isopanisad':
            # Handle mantras
            mantras = raw_data.get('mantras', [])
            for i, mantra in enumerate(mantras):
                unit = ContentUnit(
                    id=f"iso_mantra_{i+1}",
                    content=self._combine_mantra_content(mantra),
                    content_type="mantra",
                    metadata={
                        "mantra_number": mantra.get('mantra_number', ''),
                        "sanskrit": mantra.get('sanskrit_mantra', ''),
                        "translation": mantra.get('translation', ''),
                        "purport": mantra.get('purport', '')
                    },
                    position=i
                )
                units.append(unit)
        
        elif scripture_type == 'bhagavad_gita':
            # Handle chapters and verses
            chapters = raw_data.get('chapters', {})
            for chapter_num, chapter_data in chapters.items():
                verses = chapter_data.get('verses', [])
                for i, verse in enumerate(verses):
                    unit = ContentUnit(
                        id=f"bg_ch{chapter_num}_v{i+1}",
                        content=self._combine_verse_content(verse),
                        content_type="verse",
                        metadata={
                            "chapter": chapter_num,
                            "verse_number": verse.get('verse_number', ''),
                            "sanskrit": verse.get('sanskrit', ''),
                            "translation": verse.get('translation', ''),
                            "purport": verse.get('purport', '')
                        },
                        parent_id=f"bg_chapter_{chapter_num}",
                        position=i
                    )
                    units.append(unit)
        
        elif scripture_type == 'srimad_bhagavatam':
            # Handle cantos, chapters, and verses
            for canto_num, canto_data in raw_data.items():
                chapters = canto_data.get('chapters', {})
                for chapter_num, chapter_data in chapters.items():
                    verses = chapter_data.get('verses', [])
                    for i, verse in enumerate(verses):
                        unit = ContentUnit(
                            id=f"sb_c{canto_num}_ch{chapter_num}_v{i+1}",
                            content=self._combine_verse_content(verse),
                            content_type="verse",
                            metadata={
                                "canto": canto_num,
                                "chapter": chapter_num,
                                "verse_number": verse.get('verse_number', ''),
                                "sanskrit": verse.get('sanskrit_verse', ''),
                                "translation": verse.get('translation', ''),
                                "purport": verse.get('purport', '')
                            },
                            parent_id=f"sb_canto_{canto_num}_chapter_{chapter_num}",
                            position=i
                        )
                        units.append(unit)
        
        return units
    
    def _combine_mantra_content(self, mantra: Dict) -> str:
        """Combine mantra parts into unified content"""
        parts = []
        if mantra.get('sanskrit_mantra'):
            parts.append(f"Sanskrit: {mantra['sanskrit_mantra']}")
        if mantra.get('translation'):
            parts.append(f"Translation: {mantra['translation']}")
        if mantra.get('purport'):
            parts.append(f"Purport: {mantra['purport']}")
        return "\n\n".join(parts)
    
    def _combine_verse_content(self, verse: Dict) -> str:
        """Combine verse parts into unified content"""
        parts = []
        if verse.get('sanskrit') or verse.get('sanskrit_verse'):
            sanskrit = verse.get('sanskrit') or verse.get('sanskrit_verse')
            parts.append(f"Sanskrit: {sanskrit}")
        if verse.get('translation'):
            parts.append(f"Translation: {verse['translation']}")
        if verse.get('purport'):
            parts.append(f"Purport: {verse['purport']}")
        return "\n\n".join(parts)


# ============================================================================
# PDF PROCESSOR
# ============================================================================

class PDFProcessor(ContentProcessor):
    """Enhanced PDF processor with multiple extraction methods"""
    
    def can_process(self, source_info: Dict[str, Any]) -> bool:
        """Check if this is a PDF source"""
        source_type = source_info.get('source_type', '')
        source_url = source_info.get('source_url', '')
        source_path = source_info.get('source_path', '')
        
        return (source_type == 'pdf' or 
                source_url.lower().endswith('.pdf') or
                source_path.lower().endswith('.pdf'))
    
    def extract_content(self, source_info: Dict[str, Any]) -> ProcessedContent:
        """Extract content from PDF using multiple methods"""
        book_id = source_info.get('id', 'unknown')
        title = source_info.get('title', 'Unknown')
        author = source_info.get('author', 'Unknown')
        
        if not HAS_PDF_SUPPORT:
            raise ImportError("PDF support not available. Install PyPDF2 and PyMuPDF")
        
        # Download PDF if URL provided
        pdf_path = self._get_pdf_path(source_info)
        
        # Try multiple extraction methods
        extraction_methods = [
            ('PyMuPDF', self._extract_with_pymupdf),
            ('PyPDF2', self._extract_with_pypdf2)
        ]
        
        content_units = []
        extraction_notes = []
        
        for method_name, extract_func in extraction_methods:
            try:
                logger.info(f"Trying PDF extraction with {method_name}")
                text = extract_func(pdf_path)
                
                if text and len(text.strip()) > 100:  # Minimum viable content
                    content_units = self._create_pdf_content_units(text, book_id)
                    extraction_notes.append(f"Successfully extracted with {method_name}")
                    break
                else:
                    extraction_notes.append(f"{method_name} extracted insufficient content")
                    
            except Exception as e:
                extraction_notes.append(f"{method_name} failed: {str(e)}")
                logger.warning(f"PDF extraction with {method_name} failed: {e}")
        
        if not content_units:
            raise ValueError("All PDF extraction methods failed")
        
        return ProcessedContent(
            book_id=book_id,
            title=title,
            author=author,
            content_units=content_units,
            metadata={
                "source_type": "pdf",
                "pdf_path": str(pdf_path),
                "total_units": len(content_units)
            },
            quality_metrics={"overall": 0.8},  # PDF extraction typically has good quality
            extraction_notes=extraction_notes
        )
    
    def _get_pdf_path(self, source_info: Dict[str, Any]) -> Path:
        """Get local PDF path, downloading if necessary"""
        source_path = source_info.get('source_path')
        source_url = source_info.get('source_url')
        
        if source_path and Path(source_path).exists():
            return Path(source_path)
        
        if source_url:
            # Download PDF
            downloads_dir = Path("downloads")
            downloads_dir.mkdir(exist_ok=True)
            
            filename = source_url.split('/')[-1]
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            local_path = downloads_dir / filename
            
            if not local_path.exists():
                logger.info(f"Downloading PDF from {source_url}")
                response = requests.get(source_url, stream=True)
                response.raise_for_status()
                
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            return local_path
        
        raise ValueError("No valid PDF path or URL provided")
    
    def _extract_with_pymupdf(self, pdf_path: Path) -> str:
        """Extract text using PyMuPDF (fitz)"""
        doc = fitz.open(str(pdf_path))
        text_parts = []
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                text_parts.append(text)
        
        doc.close()
        return "\n\n".join(text_parts)
    
    def _extract_with_pypdf2(self, pdf_path: Path) -> str:
        """Extract text using PyPDF2"""
        text_parts = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text.strip():
                    text_parts.append(text)
        
        return "\n\n".join(text_parts)
    
    def _create_pdf_content_units(self, text: str, book_id: str) -> List[ContentUnit]:
        """Create content units from PDF text"""
        # Simple paragraph-based chunking for PDFs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        content_units = []
        for i, paragraph in enumerate(paragraphs):
            if len(paragraph) > 50:  # Skip very short paragraphs
                unit = ContentUnit(
                    id=f"{book_id}_p{i+1}",
                    content=paragraph,
                    content_type="paragraph",
                    metadata={
                        "source": "pdf_extraction",
                        "length": len(paragraph)
                    },
                    position=i
                )
                content_units.append(unit)
        
        return content_units


# ============================================================================
# EPUB PROCESSOR
# ============================================================================

class EPUBProcessor(ContentProcessor):
    """EPUB/MOBI processor"""
    
    def can_process(self, source_info: Dict[str, Any]) -> bool:
        """Check if this is an EPUB source"""
        source_type = source_info.get('source_type', '')
        source_url = source_info.get('source_url', '')
        source_path = source_info.get('source_path', '')
        
        return (source_type in ['epub', 'mobi'] or 
                any(source_url.lower().endswith(ext) for ext in ['.epub', '.mobi']) or
                any(source_path.lower().endswith(ext) for ext in ['.epub', '.mobi']))
    
    def extract_content(self, source_info: Dict[str, Any]) -> ProcessedContent:
        """Extract content from EPUB"""
        if not HAS_EPUB_SUPPORT:
            raise ImportError("EPUB support not available. Install ebooklib")
        
        book_id = source_info.get('id', 'unknown')
        title = source_info.get('title', 'Unknown')
        author = source_info.get('author', 'Unknown')
        
        # Get EPUB path
        epub_path = self._get_epub_path(source_info)
        
        # Extract content
        book = epub.read_epub(str(epub_path))
        content_units = []
        
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content()
                if content:
                    # Parse HTML content
                    soup = BeautifulSoup(content, 'html.parser')
                    text = soup.get_text()
                    
                    if text.strip():
                        unit = ContentUnit(
                            id=f"{book_id}_{item.get_id()}",
                            content=text.strip(),
                            content_type="chapter",
                            metadata={
                                "source": "epub_extraction",
                                "item_id": item.get_id(),
                                "length": len(text)
                            },
                            position=len(content_units)
                        )
                        content_units.append(unit)
        
        return ProcessedContent(
            book_id=book_id,
            title=title,
            author=author,
            content_units=content_units,
            metadata={
                "source_type": "epub",
                "epub_path": str(epub_path),
                "total_units": len(content_units)
            },
            quality_metrics={"overall": 0.85},
            extraction_notes=["EPUB extraction completed"]
        )
    
    def _get_epub_path(self, source_info: Dict[str, Any]) -> Path:
        """Get local EPUB path, downloading if necessary"""
        # Similar to PDF path logic
        source_path = source_info.get('source_path')
        if source_path and Path(source_path).exists():
            return Path(source_path)
        
        # Download logic would go here
        raise ValueError("EPUB download not implemented yet")


# ============================================================================
# UNIVERSAL INGESTION PIPELINE
# ============================================================================

class UniversalIngestionPipeline:
    """Main ingestion pipeline that coordinates all processors"""
    
    def __init__(self, registry_manager: BookRegistryManager):
        self.registry = registry_manager
        self.processors = [
            ScriptureProcessor(),
            PDFProcessor(),
            EPUBProcessor()
        ]
    
    def ingest_book(self, book_id: str) -> IngestionResult:
        """Main ingestion entry point"""
        start_time = datetime.now()
        
        try:
            # Get book info from registry
            book_info = self._get_book_info(book_id)
            
            # Update status to in progress
            self.registry.update_stage_status(
                book_id, ProcessingStage.INGESTION, "started",
                notes="Starting content extraction"
            )
            
            # Find appropriate processor
            processor = self._find_processor(book_info)
            if not processor:
                raise ValueError(f"No processor found for book {book_id}")
            
            # Extract content
            logger.info(f"Extracting content for {book_id} using {processor.__class__.__name__}")
            content = processor.extract_content(book_info)
            
            # Validate quality
            quality_report = processor.validate_extraction(content)
            
            # Save raw and processed content
            self._save_content(content, quality_report)
            
            # Update registry with results
            self.registry.update_stage_status(
                book_id, ProcessingStage.INGESTION, "completed",
                quality_score=quality_report.overall_score,
                notes=f"Extracted {len(content.content_units)} content units"
            )
            
            # Add quality report
            self.registry.add_quality_report(book_id, quality_report)
            
            extraction_time = (datetime.now() - start_time).total_seconds()
            
            return IngestionResult(
                book_id=book_id,
                success=True,
                content=content,
                quality_score=quality_report.overall_score,
                extraction_time_seconds=extraction_time
            )
            
        except Exception as e:
            logger.error(f"Ingestion failed for {book_id}: {e}")
            
            # Update registry with failure
            self.registry.update_stage_status(
                book_id, ProcessingStage.INGESTION, "failed",
                error_message=str(e),
                notes="Content extraction failed"
            )
            
            extraction_time = (datetime.now() - start_time).total_seconds()
            
            return IngestionResult(
                book_id=book_id,
                success=False,
                error_message=str(e),
                extraction_time_seconds=extraction_time
            )
    
    def _get_book_info(self, book_id: str) -> Dict[str, Any]:
        """Get book information from registry"""
        if book_id not in self.registry.catalog["books"]:
            raise ValueError(f"Book {book_id} not found in registry")
        
        return self.registry.catalog["books"][book_id]
    
    def _find_processor(self, book_info: Dict[str, Any]) -> Optional[ContentProcessor]:
        """Find appropriate processor for the book"""
        for processor in self.processors:
            if processor.can_process(book_info):
                return processor
        return None
    
    def _save_content(self, content: ProcessedContent, quality_report: QualityReport):
        """Save extracted content to standardized locations"""
        
        # Create data directories
        data_dir = Path(f"data_{content.book_id}")
        raw_dir = data_dir / "raw"
        processed_dir = data_dir / "processed"
        
        raw_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Save raw content units
        raw_path = raw_dir / f"{content.book_id}_raw_content.json"
        with open(raw_path, 'w', encoding='utf-8') as f:
            content_data = {
                "book_id": content.book_id,
                "title": content.title,
                "author": content.author,
                "metadata": content.metadata,
                "content_units": [
                    {
                        "id": unit.id,
                        "content": unit.content,
                        "content_type": unit.content_type,
                        "metadata": unit.metadata,
                        "parent_id": unit.parent_id,
                        "position": unit.position
                    }
                    for unit in content.content_units
                ],
                "extraction_notes": content.extraction_notes
            }
            json.dump(content_data, f, indent=2, ensure_ascii=False)
        
        # Save processed text file
        processed_path = processed_dir / f"{content.book_id}_complete.txt"
        with open(processed_path, 'w', encoding='utf-8') as f:
            f.write(f"{content.title}\n")
            f.write(f"by {content.author}\n\n")
            
            for unit in content.content_units:
                f.write(f"=== {unit.content_type.title()} {unit.position + 1} ===\n")
                f.write(unit.content)
                f.write("\n\n")
        
        # Save quality report
        quality_path = data_dir / "quality_report.json"
        with open(quality_path, 'w', encoding='utf-8') as f:
            quality_data = {
                "book_id": quality_report.book_id,
                "overall_score": quality_report.overall_score,
                "content_completeness": quality_report.content_completeness,
                "extraction_accuracy": quality_report.extraction_accuracy,
                "chunk_quality": quality_report.chunk_quality,
                "issues_found": quality_report.issues_found,
                "recommendations": quality_report.recommendations,
                "generated_at": quality_report.generated_at
            }
            json.dump(quality_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved content for {content.book_id} to {data_dir}")


def process_backlog(registry: BookRegistryManager, limit: int = 5):
    """Process books from backlog"""
    pipeline = UniversalIngestionPipeline(registry)
    
    # Get priority queue
    priority_books = registry.get_priority_queue()
    backlog_books = [book for book in priority_books if book["status"] == "backlog"]
    
    print(f"📋 Processing {min(limit, len(backlog_books))} books from backlog...")
    
    for i, book in enumerate(backlog_books[:limit]):
        book_id = book["id"]
        print(f"\n📖 Processing {i+1}/{min(limit, len(backlog_books))}: {book['title']}")
        
        result = pipeline.ingest_book(book_id)
        
        if result.success:
            print(f"   ✅ Success! Quality score: {result.quality_score:.2f}")
            print(f"   📊 Extracted {len(result.content.content_units)} content units")
        else:
            print(f"   ❌ Failed: {result.error_message}")


if __name__ == "__main__":
    # Example usage
    from book_registry_manager import BookRegistryManager
    
    # Load registry
    registry = BookRegistryManager()
    
    # Process some books from backlog
    process_backlog(registry, limit=2)
    
    # Show updated progress
    report = registry.generate_progress_report()
    print(f"\n📊 Updated Progress:")
    print(f"   Completed: {report['summary']['completed']}")
    print(f"   In Progress: {report['summary']['in_progress']}")
    print(f"   Failed: {report['summary']['failed']}")
