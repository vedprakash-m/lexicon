"""
RAG Dataset Management Frontend - Stage 1: Registry & Tracking
=============================================================

Frontend management layer for the 3-stage RAG dataset pipeline:
- Book catalog and metadata management
- Progress tracking across processing stages
- Quality control and validation
- Dashboard interface for dataset management

This is the control center for managing your growing RAG dataset.

Author: RAG Dataset Architecture Project
"""

import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone, timedelta
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND DATA STRUCTURES
# ============================================================================

class BookStatus(Enum):
    """Book processing status for pipeline tracking"""
    BACKLOG = "backlog"           # Added to catalog, not started
    IN_PROGRESS = "in_progress"   # Currently being processed
    COMPLETED = "completed"       # All stages complete
    FAILED = "failed"            # Processing failed
    ON_HOLD = "on_hold"          # Temporarily paused
    NEEDS_REVIEW = "needs_review" # Quality issues found


class ProcessingStage(Enum):
    """Processing pipeline stages"""
    REGISTRY = "registry"         # Added to catalog
    INGESTION = "ingestion"      # Content extraction
    VALIDATION = "validation"    # Quality control
    CHUNKING = "chunking"        # RAG chunk generation
    EXPORT = "export"            # Final output creation


class Priority(Enum):
    """Processing priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class SourceType(Enum):
    """Supported content source types"""
    WEB_SCRAPING = "web_scraping"
    PDF = "pdf"
    EPUB = "epub"
    MOBI = "mobi"
    TXT = "txt"
    DOCX = "docx"
    API = "api"
    MANUAL = "manual"


@dataclass
class StageInfo:
    """Information about a processing stage"""
    status: str = "pending"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    quality_score: Optional[float] = None
    notes: str = ""


@dataclass
class QualityReport:
    """Quality assessment report for a book"""
    book_id: str
    overall_score: float
    content_completeness: float
    extraction_accuracy: float
    chunk_quality: float
    issues_found: List[str]
    recommendations: List[str]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class Priority(Enum):
    """Priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ProcessingStage(Enum):
    """Processing stages"""
    REGISTRY = "registry"
    INGESTION = "ingestion"
    CHUNKING = "chunking"


class ChunkingStrategy(Enum):
    """Available chunking strategies"""
    STANDARD = "standard"
    SEMANTIC = "semantic"
    QUALITY_OPTIMIZED = "quality_optimized"
    DOMAIN_AWARE = "domain_aware"
    RETRIEVAL_OPTIMIZED = "retrieval_optimized"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class StageStatus:
    """Status of a processing stage"""
    status: BookStatus
    date: Optional[str] = None
    error_message: Optional[str] = None
    quality_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status.value,
            'date': self.date,
            'error_message': self.error_message,
            'quality_score': self.quality_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StageStatus':
        return cls(
            status=BookStatus(data['status']),
            date=data.get('date'),
            error_message=data.get('error_message'),
            quality_score=data.get('quality_score')
        )


@dataclass
class BookEntry:
    """Complete book entry in the registry"""
    id: str
    title: str
    author: str
    category: str
    status: BookStatus
    source_type: SourceType
    priority: Priority
    language: str = "english"
    source_url: Optional[str] = None
    estimated_pages: Optional[int] = None
    estimated_words: Optional[int] = None
    added_date: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    stages: Dict[str, StageStatus] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize stages if not provided"""
        if not self.stages:
            self.stages = {
                ProcessingStage.REGISTRY.value: StageStatus(BookStatus.COMPLETED, self.added_date),
                ProcessingStage.INGESTION.value: StageStatus(BookStatus.TODO),
                ProcessingStage.CHUNKING.value: StageStatus(BookStatus.TODO)
            }
    
    def update_stage(self, stage: ProcessingStage, status: BookStatus, 
                    error_message: Optional[str] = None, quality_score: Optional[float] = None):
        """Update status of a processing stage"""
        self.stages[stage.value] = StageStatus(
            status=status,
            date=datetime.now(timezone.utc).isoformat(),
            error_message=error_message,
            quality_score=quality_score
        )
        self.last_updated = datetime.now(timezone.utc).isoformat()
        
        # Update overall status based on stages
        self._update_overall_status()
    
    def _update_overall_status(self):
        """Update overall book status based on stage statuses"""
        stage_statuses = [stage.status for stage in self.stages.values()]
        
        if BookStatus.FAILED in stage_statuses:
            self.status = BookStatus.FAILED
        elif BookStatus.IN_PROGRESS in stage_statuses:
            self.status = BookStatus.IN_PROGRESS
        elif all(status == BookStatus.COMPLETED for status in stage_statuses):
            self.status = BookStatus.COMPLETED
        else:
            self.status = BookStatus.TODO
    
    def get_progress_percentage(self) -> float:
        """Calculate completion percentage"""
        completed_stages = sum(1 for stage in self.stages.values() 
                             if stage.status == BookStatus.COMPLETED)
        return (completed_stages / len(self.stages)) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'category': self.category,
            'status': self.status.value,
            'source_type': self.source_type.value,
            'priority': self.priority.value,
            'language': self.language,
            'source_url': self.source_url,
            'estimated_pages': self.estimated_pages,
            'estimated_words': self.estimated_words,
            'added_date': self.added_date,
            'last_updated': self.last_updated,
            'stages': {k: v.to_dict() for k, v in self.stages.items()},
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BookEntry':
        """Create BookEntry from dictionary"""
        book = cls(
            id=data['id'],
            title=data['title'],
            author=data['author'],
            category=data['category'],
            status=BookStatus(data['status']),
            source_type=SourceType(data['source_type']),
            priority=Priority(data['priority']),
            language=data.get('language', 'english'),
            source_url=data.get('source_url'),
            estimated_pages=data.get('estimated_pages'),
            estimated_words=data.get('estimated_words'),
            added_date=data.get('added_date', datetime.now(timezone.utc).isoformat()),
            last_updated=data.get('last_updated', datetime.now(timezone.utc).isoformat()),
            metadata=data.get('metadata', {})
        )
        
        # Load stages
        if 'stages' in data:
            book.stages = {k: StageStatus.from_dict(v) for k, v in data['stages'].items()}
        
        return book


@dataclass
class ProcessingResult:
    """Result of a processing operation"""
    book_id: str
    stage: ProcessingStage
    success: bool
    quality_score: Optional[float] = None
    error_message: Optional[str] = None
    output_paths: List[str] = field(default_factory=list)
    processing_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# BOOK REGISTRY MANAGER
# ============================================================================

class BookRegistryManager:
    """Manages the book catalog and processing status tracking"""
    
    def __init__(self, catalog_path: str = "book_catalog.json"):
        self.catalog_path = Path(catalog_path)
        self.catalog_data = self._load_catalog()
        self.books: Dict[str, BookEntry] = self._load_books()
    
    def _load_catalog(self) -> Dict[str, Any]:
        """Load catalog from JSON file"""
        if self.catalog_path.exists():
            try:
                with open(self.catalog_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load catalog: {e}")
                return self._create_empty_catalog()
        else:
            return self._create_empty_catalog()
    
    def _create_empty_catalog(self) -> Dict[str, Any]:
        """Create empty catalog structure"""
        return {
            "catalog_version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "total_books": 0,
            "books": {},
            "categories": [
                "vedic_literature", "spiritual_classics", "philosophy", 
                "ai_ml_books", "self_help", "science", "history", "fiction"
            ],
            "source_types": [st.value for st in SourceType],
            "status_types": [bs.value for bs in BookStatus],
            "priority_levels": [p.value for p in Priority],
            "processing_stages": [ps.value for ps in ProcessingStage]
        }
    
    def _load_books(self) -> Dict[str, BookEntry]:
        """Load books from catalog data"""
        books = {}
        for category, category_books in self.catalog_data.get('books', {}).items():
            for book_key, book_data in category_books.items():
                book_data['category'] = category
                book = BookEntry.from_dict(book_data)
                books[book.id] = book
        return books
    
    def save_catalog(self):
        """Save catalog to JSON file"""
        # Organize books by category for saving
        organized_books = {}
        for book in self.books.values():
            category = book.category
            if category not in organized_books:
                organized_books[category] = {}
            
            # Use a clean key for the book (derived from title)
            book_key = self._generate_book_key(book.title)
            organized_books[category][book_key] = book.to_dict()
        
        # Update catalog metadata
        self.catalog_data['books'] = organized_books
        self.catalog_data['total_books'] = len(self.books)
        self.catalog_data['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        # Save to file
        with open(self.catalog_path, 'w', encoding='utf-8') as f:
            json.dump(self.catalog_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Catalog saved with {len(self.books)} books")
    
    def _generate_book_key(self, title: str) -> str:
        """Generate a clean key from book title"""
        return title.lower().replace(' ', '_').replace('-', '_').replace(':', '').replace(',', '')
    
    def _generate_book_id(self, title: str, author: str) -> str:
        """Generate unique book ID"""
        combined = f"{title}_{author}".lower()
        hash_object = hashlib.md5(combined.encode())
        return hash_object.hexdigest()[:8]
    
    def add_book(self, title: str, author: str, category: str, source_type: SourceType,
                priority: Priority = Priority.MEDIUM, **kwargs) -> str:
        """Add new book to registry"""
        book_id = self._generate_book_id(title, author)
        
        # Check if book already exists
        if book_id in self.books:
            logger.warning(f"Book {title} by {author} already exists with ID {book_id}")
            return book_id
        
        # Create new book entry
        book = BookEntry(
            id=book_id,
            title=title,
            author=author,
            category=category,
            status=BookStatus.TODO,
            source_type=source_type,
            priority=priority,
            **kwargs
        )
        
        self.books[book_id] = book
        logger.info(f"Added book: {title} by {author} (ID: {book_id})")
        
        return book_id
    
    def update_book_stage(self, book_id: str, stage: ProcessingStage, status: BookStatus,
                         error_message: Optional[str] = None, quality_score: Optional[float] = None) -> bool:
        """Update book processing stage status"""
        if book_id not in self.books:
            logger.error(f"Book ID {book_id} not found")
            return False
        
        self.books[book_id].update_stage(stage, status, error_message, quality_score)
        logger.info(f"Updated {book_id} stage {stage.value} to {status.value}")
        return True
    
    def get_book(self, book_id: str) -> Optional[BookEntry]:
        """Get book by ID"""
        return self.books.get(book_id)
    
    def get_books_by_status(self, status: BookStatus) -> List[BookEntry]:
        """Get all books with specific status"""
        return [book for book in self.books.values() if book.status == status]
    
    def get_books_by_category(self, category: str) -> List[BookEntry]:
        """Get all books in specific category"""
        return [book for book in self.books.values() if book.category == category]
    
    def get_priority_queue(self) -> List[BookEntry]:
        """Get books ordered by priority and status for processing"""
        # Priority order: urgent > high > medium > low
        priority_order = {Priority.URGENT: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}
        
        # Filter books that need processing (not completed or failed)
        processable_books = [
            book for book in self.books.values() 
            if book.status in [BookStatus.TODO, BookStatus.IN_PROGRESS]
        ]
        
        # Sort by priority, then by added date
        return sorted(
            processable_books,
            key=lambda b: (priority_order[b.priority], b.added_date)
        )
    
    def get_next_book_for_stage(self, stage: ProcessingStage) -> Optional[BookEntry]:
        """Get next book that needs processing for a specific stage"""
        for book in self.get_priority_queue():
            stage_status = book.stages.get(stage.value)
            if stage_status and stage_status.status == BookStatus.TODO:
                return book
        return None
    
    def generate_progress_report(self) -> Dict[str, Any]:
        """Generate comprehensive progress report"""
        total_books = len(self.books)
        if total_books == 0:
            return {"error": "No books in catalog"}
        
        # Status distribution
        status_counts = {}
        for status in BookStatus:
            status_counts[status.value] = len(self.get_books_by_status(status))
        
        # Category distribution
        category_counts = {}
        for category in self.catalog_data['categories']:
            category_counts[category] = len(self.get_books_by_category(category))
        
        # Stage progress
        stage_progress = {}
        for stage in ProcessingStage:
            completed = sum(1 for book in self.books.values() 
                          if book.stages.get(stage.value, StageStatus(BookStatus.TODO)).status == BookStatus.COMPLETED)
            stage_progress[stage.value] = {
                'completed': completed,
                'percentage': (completed / total_books) * 100
            }
        
        # Overall progress
        overall_completed = status_counts.get(BookStatus.COMPLETED.value, 0)
        overall_progress = (overall_completed / total_books) * 100
        
        return {
            'total_books': total_books,
            'overall_progress': overall_progress,
            'status_distribution': status_counts,
            'category_distribution': category_counts,
            'stage_progress': stage_progress,
            'next_priority_books': [
                {'id': book.id, 'title': book.title, 'priority': book.priority.value}
                for book in self.get_priority_queue()[:10]
            ]
        }
    
    def add_sample_books(self):
        """Add sample books for testing and demonstration"""
        sample_books = [
            # Completed books (already in system)
            {
                'title': 'Bhagavad-gītā As It Is',
                'author': 'A.C. Bhaktivedanta Swami Prabhupāda',
                'category': 'vedic_literature',
                'source_type': SourceType.WEB_SCRAPING,
                'priority': Priority.HIGH,
                'source_url': 'https://vedabase.io/en/library/bg/',
                'estimated_pages': 800,
                'status_override': BookStatus.COMPLETED
            },
            {
                'title': 'Śrīmad-Bhāgavatam',
                'author': 'A.C. Bhaktivedanta Swami Prabhupāda',
                'category': 'vedic_literature',
                'source_type': SourceType.WEB_SCRAPING,
                'priority': Priority.HIGH,
                'source_url': 'https://vedabase.io/en/library/sb/',
                'estimated_pages': 15000,
                'status_override': BookStatus.COMPLETED
            },
            {
                'title': 'Śrī Īśopaniṣad',
                'author': 'A.C. Bhaktivedanta Swami Prabhupāda',
                'category': 'vedic_literature',
                'source_type': SourceType.WEB_SCRAPING,
                'priority': Priority.HIGH,
                'source_url': 'https://vedabase.io/en/library/iso/',
                'estimated_pages': 200,
                'status_override': BookStatus.COMPLETED
            },
            
            # High priority books to add
            {
                'title': 'Autobiography of a Yogi',
                'author': 'Paramahansa Yogananda',
                'category': 'spiritual_classics',
                'source_type': SourceType.PDF,
                'priority': Priority.HIGH,
                'source_url': 'https://archive.org/details/AutobiographyOfAYogi',
                'estimated_pages': 500
            },
            {
                'title': 'The Power of Now',
                'author': 'Eckhart Tolle',
                'category': 'spiritual_classics',
                'source_type': SourceType.PDF,
                'priority': Priority.HIGH,
                'estimated_pages': 300
            },
            {
                'title': 'Meditations',
                'author': 'Marcus Aurelius',
                'category': 'philosophy',
                'source_type': SourceType.EPUB,
                'priority': Priority.MEDIUM,
                'source_url': 'https://www.gutenberg.org/ebooks/2680',
                'estimated_pages': 250
            },
            {
                'title': 'The Bhagavad Gita (Eknath Easwaran)',
                'author': 'Eknath Easwaran',
                'category': 'vedic_literature',
                'source_type': SourceType.PDF,
                'priority': Priority.MEDIUM,
                'estimated_pages': 400
            },
            {
                'title': 'Hands-On Machine Learning',
                'author': 'Aurélien Géron',
                'category': 'ai_ml_books',
                'source_type': SourceType.PDF,
                'priority': Priority.HIGH,
                'estimated_pages': 800
            },
            {
                'title': 'The Art of Happiness',
                'author': 'Dalai Lama',
                'category': 'self_help',
                'source_type': SourceType.PDF,
                'priority': Priority.MEDIUM,
                'estimated_pages': 350
            },
            {
                'title': 'Be Here Now',
                'author': 'Ram Dass',
                'category': 'spiritual_classics',
                'source_type': SourceType.PDF,
                'priority': Priority.HIGH,
                'estimated_pages': 400
            }
        ]
        
        for book_data in sample_books:
            status_override = book_data.pop('status_override', None)
            book_id = self.add_book(**book_data)
            
            # Set status for completed books
            if status_override == BookStatus.COMPLETED:
                book = self.get_book(book_id)
                if book:
                    for stage in ProcessingStage:
                        book.update_stage(stage, BookStatus.COMPLETED, quality_score=0.95)


def main():
    """Demonstrate the Book Registry Manager"""
    registry = BookRegistryManager("book_catalog.json")
    
    # Add sample books
    print("Adding sample books...")
    registry.add_sample_books()
    
    # Save catalog
    registry.save_catalog()
    
    # Generate progress report
    print("\n📊 Progress Report:")
    report = registry.generate_progress_report()
    
    print(f"Total Books: {report['total_books']}")
    print(f"Overall Progress: {report['overall_progress']:.1f}%")
    
    print("\n📈 Status Distribution:")
    for status, count in report['status_distribution'].items():
        print(f"  {status}: {count}")
    
    print("\n📚 Category Distribution:")
    for category, count in report['category_distribution'].items():
        if count > 0:
            print(f"  {category}: {count}")
    
    print("\n🎯 Next Priority Books:")
    for book_info in report['next_priority_books']:
        print(f"  {book_info['title']} (Priority: {book_info['priority']})")
    
    print(f"\n💾 Catalog saved to: {registry.catalog_path}")


if __name__ == "__main__":
    main()
