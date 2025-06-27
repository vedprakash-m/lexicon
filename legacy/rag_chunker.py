"""
Unified RAG Export Utility for Vedic Scriptures

This module provides a common interface for exporting scraped Vedic scripture data
into various RAG-optimized formats. It handles data from all three scriptures:
- Śrīmad-Bhāgavatam
- Bhagavad-gītā  
- Śrī Īśopaniṣad

Author: Vedic Scriptures Web Scraper Project
"""

import json
import logging
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScriptureType(Enum):
    """Enum for different scripture types"""
    BHAGAVAD_GITA = "bg"
    SRIMAD_BHAGAVATAM = "sb" 
    SRI_ISOPANISAD = "iso"


class ChunkSize(Enum):
    """Enum for different chunking strategies"""
    VERSE = "verse"          # Individual verses/mantras
    SECTION = "section"      # Small groups (5 verses)
    CHAPTER = "chapter"      # Complete chapters/mantras
    CANTO = "canto"         # Complete cantos (SB only)
    COMPLETE = "complete"    # Entire scripture


class ExportStrategy(Enum):
    """Enum for different export strategies"""
    STANDARD = "standard"    # Standard chunking with all content
    WEIGHTED = "weighted"    # Weighted chunking with different priorities
    FLEXIBLE = "flexible"    # Flexible chunking with adaptive sizes


@dataclass
class ScriptureConfig:
    """Configuration for each scripture type"""
    scripture_type: ScriptureType
    data_dir: str
    raw_file: str
    title: str
    author: str
    verse_key: str          # Key for individual content units
    container_key: str      # Key for containers (chapters/cantos)


# Scripture configurations
SCRIPTURE_CONFIGS = {
    ScriptureType.BHAGAVAD_GITA: ScriptureConfig(
        scripture_type=ScriptureType.BHAGAVAD_GITA,
        data_dir="data_bg",
        raw_file="bhagavad_gita_complete.json",
        title="Bhagavad-gītā As It Is",
        author="A.C. Bhaktivedanta Swami Prabhupāda",
        verse_key="verses",
        container_key="chapters"
    ),
    ScriptureType.    SRIMAD_BHAGAVATAM: ScriptureConfig(
        scripture_type=ScriptureType.SRIMAD_BHAGAVATAM,
        data_dir="data_sb", 
        raw_file="srimad_bhagavatam_complete.json",
        title="Śrīmad-Bhāgavatam",
        author="A.C. Bhaktivedanta Swami Prabhupāda",
        verse_key="verses",
        container_key="chapters"  # Changed from "cantos" to "chapters"
    ),
    ScriptureType.SRI_ISOPANISAD: ScriptureConfig(
        scripture_type=ScriptureType.SRI_ISOPANISAD,
        data_dir="data_iso",
        raw_file="sri_isopanisad_complete.json", 
        title="Śrī Īśopaniṣad",
        author="A.C. Bhaktivedanta Swami Prabhupāda",
        verse_key="mantras",
        container_key="mantras"
    )
}


class UnifiedRAGExporter:
    """
    Unified RAG exporter that works with all three scripture types.
    Provides consistent export formats across different scriptures.
    """
    
    def __init__(self, scripture_type: ScriptureType):
        """Initialize exporter for specific scripture type"""
        self.config = SCRIPTURE_CONFIGS[scripture_type]
        self.scripture_type = scripture_type
        self.data = None
        self._ensure_rag_directories()
    
    def _ensure_rag_directories(self):
        """Create RAG export directories if they don't exist"""
        for strategy in ExportStrategy:
            rag_dir = Path(self.config.data_dir) / "rag" / strategy.value
            rag_dir.mkdir(parents=True, exist_ok=True)
    
    def load_data(self) -> bool:
        """Load the scripture data from raw JSON file"""
        try:
            data_path = Path(self.config.data_dir) / "raw" / self.config.raw_file
            
            if not data_path.exists():
                logger.error(f"Data file not found: {data_path}")
                return False
            
            with open(data_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            logger.info(f"Loaded {self.config.title} data successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return False
    
    def export_all_formats(self):
        """Export all RAG formats for the scripture"""
        if not self.data:
            if not self.load_data():
                return False
        
        try:
            logger.info(f"Starting RAG export for {self.config.title}")
            
            # Export all strategies
            for strategy in ExportStrategy:
                self._export_strategy(strategy)
            
            logger.info(f"RAG export completed for {self.config.title}")
            return True
            
        except Exception as e:
            logger.error(f"RAG export failed: {e}")
            return False
    
    def _export_strategy(self, strategy: ExportStrategy):
        """Export all chunk sizes for a specific strategy"""
        if strategy == ExportStrategy.STANDARD:
            self._export_standard_chunks()
        elif strategy == ExportStrategy.WEIGHTED:
            self._export_weighted_chunks()
        elif strategy == ExportStrategy.FLEXIBLE:
            self._export_flexible_chunks()
    
    def _export_standard_chunks(self):
        """Export standard chunks (original format)"""
        # Export different chunk sizes
        if self.scripture_type == ScriptureType.SRIMAD_BHAGAVATAM:
            self.export_chunks(ChunkSize.VERSE)
            self.export_chunks(ChunkSize.CHAPTER) 
            self.export_chunks(ChunkSize.CANTO)
            self.export_chunks(ChunkSize.COMPLETE)
        else:
            self.export_chunks(ChunkSize.VERSE)
            self.export_chunks(ChunkSize.CHAPTER)
            self.export_chunks(ChunkSize.COMPLETE)
    
    def export_chunks(self, chunk_size: ChunkSize):
        """Export chunks for specific chunk size"""
        if chunk_size == ChunkSize.VERSE:
            self._export_verse_chunks()
        elif chunk_size == ChunkSize.CHAPTER:
            self._export_chapter_chunks()
        elif chunk_size == ChunkSize.CANTO and self.scripture_type == ScriptureType.SRIMAD_BHAGAVATAM:
            self._export_canto_chunks()
        elif chunk_size == ChunkSize.COMPLETE:
            self._export_complete_chunks()
    
    def _export_verse_chunks(self):
        """Export individual verses/mantras as RAG chunks"""
        chunks = []
        prefix = self.config.scripture_type.value
        
        if self.scripture_type == ScriptureType.SRI_ISOPANISAD:
            # Handle Īśopaniṣad mantras
            mantras = self.data.get('mantras', [])
            for mantra in mantras:
                chunk_id = f"{prefix}_{mantra.get('mantra_number', '').replace(' ', '_').lower()}"
                
                content_parts = [f"Mantra {mantra.get('mantra_number', '')}"]
                
                if mantra.get('sanskrit_mantra'):
                    content_parts.append(f"\nSanskrit: {mantra['sanskrit_mantra']}")
                if mantra.get('sanskrit_transliteration'):
                    content_parts.append(f"\nTransliteration: {mantra['sanskrit_transliteration']}")
                if mantra.get('synonyms'):
                    content_parts.append(f"\nWord-for-word meaning: {mantra['synonyms']}")
                if mantra.get('translation'):
                    content_parts.append(f"\nTranslation: {mantra['translation']}")
                if mantra.get('purport'):
                    content_parts.append(f"\nPurport: {mantra['purport']}")
                
                chunk = {
                    "id": chunk_id,
                    "content": "".join(content_parts),
                    "mantra_number": mantra.get('mantra_number', ''),
                    "source": self.config.title,
                    "parts": {
                        "sanskrit_mantra": mantra.get('sanskrit_mantra', ''),
                        "sanskrit_transliteration": mantra.get('sanskrit_transliteration', ''),
                        "synonyms": mantra.get('synonyms', ''),
                        "translation": mantra.get('translation', ''),
                        "purport": mantra.get('purport', '')
                    },
                    "metadata": {
                        "has_sanskrit": bool(mantra.get('sanskrit_mantra')),
                        "has_transliteration": bool(mantra.get('sanskrit_transliteration')),
                        "has_synonyms": bool(mantra.get('synonyms')),
                        "has_translation": bool(mantra.get('translation')),
                        "has_purport": bool(mantra.get('purport')),
                        "content_length": len("".join(content_parts)),
                        "scripture": self.config.title
                    }
                }
                chunks.append(chunk)
        
        else:
            # Handle Bhagavad-gītā and Śrīmad-Bhāgavatam
            if self.scripture_type == ScriptureType.SRIMAD_BHAGAVATAM:
                # Handle Śrīmad-Bhāgavatam structure: cantos -> chapters -> verses (list)
                for canto_num, canto_data in self.data.items():
                    chapters = canto_data.get('chapters', {})
                    
                    for chapter_num, chapter_data in chapters.items():
                        verses = chapter_data.get(self.config.verse_key, [])
                        
                        for verse_data in verses:
                            verse_number = verse_data.get('verse_number', '')
                            chunk_id = f"{prefix}_{canto_num}_{chapter_num}_{verse_number.replace('.', '_').replace(' ', '_')}"
                            
                            content_parts = [f"{verse_number}"]
                            
                            if verse_data.get('sanskrit_verse'):
                                content_parts.append(f"\nSanskrit: {verse_data['sanskrit_verse']}")
                            if verse_data.get('sanskrit_transliteration'):
                                content_parts.append(f"\nTransliteration: {verse_data['sanskrit_transliteration']}")
                            if verse_data.get('synonyms'):
                                content_parts.append(f"\nWord-for-word: {verse_data['synonyms']}")
                            if verse_data.get('translation'):
                                content_parts.append(f"\nTranslation: {verse_data['translation']}")
                            if verse_data.get('purport'):
                                content_parts.append(f"\nPurport: {verse_data['purport']}")
                            
                            chunk = {
                                "id": chunk_id,
                                "content": "".join(content_parts),
                                "verse_number": verse_number,
                                "chapter": chapter_num,
                                "canto": canto_num,
                                "source": self.config.title,
                                "parts": {
                                    "sanskrit": verse_data.get('sanskrit_verse', ''),
                                    "transliteration": verse_data.get('sanskrit_transliteration', ''),
                                    "synonyms": verse_data.get('synonyms', ''),
                                    "translation": verse_data.get('translation', ''),
                                    "purport": verse_data.get('purport', '')
                                },
                                "metadata": {
                                    "has_sanskrit": bool(verse_data.get('sanskrit_verse')),
                                    "has_transliteration": bool(verse_data.get('sanskrit_transliteration')),
                                    "has_synonyms": bool(verse_data.get('synonyms')),
                                    "has_translation": bool(verse_data.get('translation')),
                                    "has_purport": bool(verse_data.get('purport')),
                                    "content_length": len("".join(content_parts)),
                                    "scripture": self.config.title
                                }
                            }
                            chunks.append(chunk)
            
            else:
                # Handle Bhagavad-gītā structure: chapters -> verses (list)
                container_key = self.config.container_key
                
                for container_num, container_data in self.data.get(container_key, {}).items():
                    verses = container_data.get(self.config.verse_key, [])
                    
                    for verse_data in verses:
                        verse_id = verse_data.get('verse_number', '').replace('Bg. ', '').replace('.', '_')
                        chunk_id = f"{prefix}_{container_num}_{verse_id}"
                        
                        content_parts = [f"Verse {verse_data.get('verse_number', '')}"]
                        
                        if verse_data.get('sanskrit'):
                            content_parts.append(f"\nSanskrit: {verse_data['sanskrit']}")
                        if verse_data.get('transliteration'):
                            content_parts.append(f"\nTransliteration: {verse_data['transliteration']}")
                        if verse_data.get('synonyms'):
                            content_parts.append(f"\nWord-for-word: {verse_data['synonyms']}")
                        if verse_data.get('translation'):
                            content_parts.append(f"\nTranslation: {verse_data['translation']}")
                        if verse_data.get('purport'):
                            content_parts.append(f"\nPurport: {verse_data['purport']}")
                        
                        chunk = {
                            "id": chunk_id,
                            "content": "".join(content_parts),
                            "verse_id": verse_data.get('verse_number', ''),
                            "container": container_num,
                            "source": self.config.title,
                            "parts": {
                                "sanskrit": verse_data.get('sanskrit', ''),
                                "transliteration": verse_data.get('transliteration', ''),
                                "synonyms": verse_data.get('synonyms', ''),
                                "translation": verse_data.get('translation', ''),
                                "purport": verse_data.get('purport', '')
                            },
                            "metadata": {
                                "has_sanskrit": bool(verse_data.get('sanskrit')),
                                "has_transliteration": bool(verse_data.get('transliteration')),
                                "has_synonyms": bool(verse_data.get('synonyms')),
                                "has_translation": bool(verse_data.get('translation')),
                                "has_purport": bool(verse_data.get('purport')),
                                "content_length": len("".join(content_parts)),
                                "scripture": self.config.title
                            }
                        }
                        chunks.append(chunk)
        
        # Save files
        base_name = f"{self.config.raw_file.split('_complete.json')[0]}_rag_{self.config.verse_key}"
        self._save_chunks(chunks, base_name)
        logger.info(f"Exported {len(chunks)} verse chunks")
    
    def _export_chapter_chunks(self):
        """Export chapters/mantras as RAG chunks"""
        chunks = []
        prefix = self.config.scripture_type.value
        
        if self.scripture_type == ScriptureType.SRI_ISOPANISAD:
            # For Īśopaniṣad, export as single complete chunk since it's small
            mantras = self.data.get('mantras', [])
            
            content_parts = [f"{self.config.title}\n"]
            content_parts.append(f"by {self.config.author}\n")
            
            for mantra in mantras:
                content_parts.append(f"\nMantra {mantra.get('mantra_number', '')}\n")
                if mantra.get('sanskrit_mantra'):
                    content_parts.append(f"Sanskrit: {mantra['sanskrit_mantra']}\n")
                if mantra.get('translation'):
                    content_parts.append(f"Translation: {mantra['translation']}\n")
                if mantra.get('purport'):
                    content_parts.append(f"Purport: {mantra['purport']}\n")
            
            chunk = {
                "id": f"{prefix}_complete",
                "content": "".join(content_parts),
                "title": self.config.title,
                "source": f"{self.config.title} by {self.config.author}",
                "metadata": {
                    "total_mantras": len(mantras),
                    "content_length": len("".join(content_parts)),
                    "scripture": self.config.title
                }
            }
            chunks.append(chunk)
        
        else:
            # Handle Bhagavad-gītā and Śrīmad-Bhāgavatam chapters
            if self.scripture_type == ScriptureType.SRIMAD_BHAGAVATAM:
                # Handle Śrīmad-Bhāgavatam structure: cantos -> chapters (list verses)
                for canto_num, canto_data in self.data.items():
                    chapters = canto_data.get('chapters', {})
                    
                    for chapter_num, chapter_data in chapters.items():
                        chapter_title = chapter_data.get('title', f"Canto {canto_num}, Chapter {chapter_num}")
                        
                        content_parts = [f"SB {canto_num}.{chapter_num}: {chapter_title}\n"]
                        
                        verses = chapter_data.get(self.config.verse_key, [])
                        for verse_data in verses:
                            verse_number = verse_data.get('verse_number', '')
                            content_parts.append(f"\n{verse_number}")
                            if verse_data.get('sanskrit_verse'):
                                content_parts.append(f"\nSanskrit: {verse_data['sanskrit_verse']}")
                            if verse_data.get('translation'):
                                content_parts.append(f"\nTranslation: {verse_data['translation']}")
                            if verse_data.get('purport'):
                                content_parts.append(f"\nPurport: {verse_data['purport']}")
                            content_parts.append("\n")
                        
                        chunk = {
                            "id": f"{prefix}_{canto_num}_{chapter_num}",
                            "content": "".join(content_parts),
                            "title": chapter_title,
                            "chapter_number": chapter_num,
                            "canto_number": canto_num,
                            "source": self.config.title,
                            "metadata": {
                                "verse_count": len(verses),
                                "content_length": len("".join(content_parts)),
                                "scripture": self.config.title
                            }
                        }
                        chunks.append(chunk)
            
            else:
                # Handle Bhagavad-gītā structure
                container_key = self.config.container_key
                
                for container_num, container_data in self.data.get(container_key, {}).items():
                    container_title = container_data.get('title', f"{container_key.title()} {container_num}")
                    
                    content_parts = [f"{container_title}\n"]
                    
                    verses = container_data.get(self.config.verse_key, [])
                    for verse_data in verses:
                        verse_number = verse_data.get('verse_number', '')
                        content_parts.append(f"\nVerse {verse_number}")
                        if verse_data.get('sanskrit'):
                            content_parts.append(f"\nSanskrit: {verse_data['sanskrit']}")
                        if verse_data.get('translation'):
                            content_parts.append(f"\nTranslation: {verse_data['translation']}")
                        if verse_data.get('purport'):
                            content_parts.append(f"\nPurport: {verse_data['purport']}")
                        content_parts.append("\n")
                    
                    chunk = {
                        "id": f"{prefix}_{container_num}",
                        "content": "".join(content_parts),
                        "title": container_title,
                        "container_number": container_num,
                        "source": self.config.title,
                        "metadata": {
                            "verse_count": len(verses),
                            "content_length": len("".join(content_parts)),
                            "scripture": self.config.title
                        }
                    }
                    chunks.append(chunk)
        
        # Save files
        base_name = f"{self.config.raw_file.split('_complete.json')[0]}_rag_{self.config.container_key}"
        self._save_chunks(chunks, base_name)
        logger.info(f"Exported {len(chunks)} container chunks")
    
    def _export_canto_chunks(self):
        """Export cantos as RAG chunks (Śrīmad-Bhāgavatam only)"""
        if self.scripture_type != ScriptureType.SRIMAD_BHAGAVATAM:
            return
        
        chunks = []
        prefix = self.config.scripture_type.value
        
        for canto_num, canto_data in self.data.items():
            canto_title = canto_data.get('title', f"Canto {canto_num}")
            
            content_parts = [f"Canto {canto_num}: {canto_title}\n"]
            
            # Add chapter summaries
            chapters = canto_data.get('chapters', {})
            for chapter_num, chapter_data in chapters.items():
                chapter_title = chapter_data.get('title', f"Chapter {chapter_num}")
                content_parts.append(f"\nChapter {chapter_num}: {chapter_title}")
                
                # Add first few verses as preview
                verses = chapter_data.get('verses', [])
                verse_count = 0
                for verse_data in verses:
                    if verse_count >= 3:  # Limit preview
                        break
                    if verse_data.get('translation'):
                        verse_number = verse_data.get('verse_number', f"Verse {verse_count + 1}")
                        content_parts.append(f"\n{verse_number}: {verse_data['translation']}")
                    verse_count += 1
                
                if len(verses) > 3:
                    content_parts.append(f"\n... and {len(verses) - 3} more verses")
                content_parts.append("\n")
            
            chunk = {
                "id": f"{prefix}_canto_{canto_num}",
                "content": "".join(content_parts),
                "title": canto_title,                    "canto_number": canto_num,
                    "source": self.config.title,
                    "metadata": {
                        "chapter_count": len(chapters),
                        "total_verses": sum(len(ch.get('verses', [])) for ch in chapters.values()),
                        "content_length": len("".join(content_parts)),
                        "scripture": self.config.title
                    }
            }
            chunks.append(chunk)
        
        # Save files
        base_name = f"{self.config.raw_file.split('_complete.json')[0]}_rag_cantos"
        self._save_chunks(chunks, base_name)
        logger.info(f"Exported {len(chunks)} canto chunks")
    
    def _export_complete_chunks(self):
        """Export complete scripture as single RAG chunk"""
        content_parts = [f"{self.config.title}\n"]
        content_parts.append(f"by {self.config.author}\n\n")
        
        total_content_units = 0
        
        if self.scripture_type == ScriptureType.SRI_ISOPANISAD:
            mantras = self.data.get('mantras', [])
            total_content_units = len(mantras)
            
            for mantra in mantras:
                content_parts.append(f"Mantra {mantra.get('mantra_number', '')}\n")
                if mantra.get('translation'):
                    content_parts.append(f"{mantra['translation']}\n\n")
        
        else:
            if self.scripture_type == ScriptureType.SRIMAD_BHAGAVATAM:
                # Handle Śrīmad-Bhāgavatam structure
                for canto_num, canto_data in self.data.items():
                    canto_title = canto_data.get('title', f"Canto {canto_num}")
                    content_parts.append(f"Canto {canto_num}: {canto_title}\n\n")
                    
                    chapters = canto_data.get('chapters', {})
                    for chapter_num, chapter_data in chapters.items():
                        chapter_title = chapter_data.get('title', f"Chapter {chapter_num}")
                        content_parts.append(f"Chapter {chapter_num}: {chapter_title}\n")
                        
                        verses = chapter_data.get(self.config.verse_key, [])
                        total_content_units += len(verses)
                        
                        for verse_data in verses:
                            if verse_data.get('translation'):
                                verse_number = verse_data.get('verse_number', '')
                                content_parts.append(f"{verse_number}: {verse_data['translation']}\n")
                        content_parts.append("\n")
            
            else:
                # Handle Bhagavad-gītā structure
                container_key = self.config.container_key
                containers = self.data.get(container_key, {})
                
                for container_num, container_data in containers.items():
                    container_title = container_data.get('title', f"{container_key.title()} {container_num}")
                    content_parts.append(f"{container_title}\n\n")
                    
                    verses = container_data.get(self.config.verse_key, [])
                    total_content_units += len(verses)
                    
                    for verse_data in verses:
                        verse_number = verse_data.get('verse_number', '')
                        if verse_data.get('translation'):
                            content_parts.append(f"Verse {verse_number}: {verse_data['translation']}\n")
                    content_parts.append("\n")
        
        chunk = {
            "id": f"{self.config.scripture_type.value}_complete",
            "content": "".join(content_parts),
            "title": self.config.title,
            "source": f"{self.config.title} by {self.config.author}",
            "metadata": {
                "total_content_units": total_content_units,
                "content_length": len("".join(content_parts)),
                "scripture": self.config.title
            }
        }
        
        # Save file
        base_name = f"{self.config.raw_file.split('_complete.json')[0]}_rag_complete"
        self._save_chunks([chunk], base_name, ExportStrategy.STANDARD)
        
        logger.info(f"Exported complete {self.config.title} chunk")
    
    def _save_chunks(self, chunks: List[Dict], base_name: str, strategy: ExportStrategy = ExportStrategy.STANDARD):
        """Save chunks in both JSONL and JSON formats"""
        rag_dir = Path(self.config.data_dir) / "rag" / strategy.value
        
        # Save as JSONL
        jsonl_path = rag_dir / f"{base_name}.jsonl"
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                json.dump(chunk, f, ensure_ascii=False)
                f.write('\n')
        
        # Save as JSON
        json_path = rag_dir / f"{base_name}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)

    def _export_weighted_chunks(self):
        """Export weighted chunks with different priorities"""
        logger.info(f"Generating weighted chunks for {self.config.title}")
        
        # Get all verses/mantras for weighted processing
        all_content = self._extract_all_content()
        
        # Generate different weighted versions
        weighted_versions = {
            "translation_first": self._create_weighted_chunks(all_content, "translation_first"),
            "commentary_focused": self._create_weighted_chunks(all_content, "commentary_focused"), 
            "balanced": self._create_weighted_chunks(all_content, "balanced"),
            "essential_only": self._create_weighted_chunks(all_content, "essential_only")
        }
        
        # Save each weighted version
        for version_name, chunks in weighted_versions.items():
            base_name = f"{self.config.raw_file.split('_complete.json')[0]}_rag_weighted_{version_name}"
            rag_dir = Path(self.config.data_dir) / "rag" / "weighted"
            
            # Save as JSONL only for weighted versions
            jsonl_path = rag_dir / f"{base_name}.jsonl"
            with open(jsonl_path, 'w', encoding='utf-8') as f:
                for chunk in chunks:
                    json.dump(chunk, f, ensure_ascii=False)
                    f.write('\n')
            
            logger.info(f"Exported {len(chunks)} {version_name} weighted chunks")
    
    def _export_flexible_chunks(self):
        """Export flexible chunks with adaptive sizes"""
        logger.info(f"Generating flexible chunks for {self.config.title}")
        
        # Get all content for flexible processing
        all_content = self._extract_all_content()
        
        # Create adaptive chunks based on content complexity
        flexible_chunks = self._create_flexible_chunks(all_content)
        
        # Save flexible chunks
        base_name = f"{self.config.raw_file.split('_complete.json')[0]}_flexible"
        rag_dir = Path(self.config.data_dir) / "rag" / "flexible"
        
        json_path = rag_dir / f"{base_name}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(flexible_chunks, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported flexible chunks with {len(flexible_chunks['chunks'])} adaptive chunks")
    
    def _extract_all_content(self):
        """Extract all content from the scripture for processing"""
        all_content = []
        
        if self.scripture_type == ScriptureType.SRI_ISOPANISAD:
            # Handle Īśopaniṣad mantras
            mantras = self.data.get('mantras', [])
            for mantra in mantras:
                content_item = {
                    "id": f"iso_{mantra.get('mantra_number', '').replace(' ', '_').lower()}",
                    "type": "mantra",
                    "number": mantra.get('mantra_number', ''),
                    "sanskrit": mantra.get('sanskrit_mantra', ''),
                    "transliteration": mantra.get('sanskrit_transliteration', ''),
                    "synonyms": mantra.get('synonyms', ''),
                    "translation": mantra.get('translation', ''),
                    "purport": mantra.get('purport', ''),
                    "container": "complete"
                }
                all_content.append(content_item)
        
        elif self.scripture_type == ScriptureType.SRIMAD_BHAGAVATAM:
            # Handle Śrīmad-Bhāgavatam structure
            for canto_num, canto_data in self.data.items():
                chapters = canto_data.get('chapters', {})
                
                for chapter_num, chapter_data in chapters.items():
                    verses = chapter_data.get(self.config.verse_key, [])
                    
                    for verse_data in verses:
                        content_item = {
                            "id": f"sb_{canto_num}_{chapter_num}_{verse_data.get('verse_number', '').replace('.', '_').replace(' ', '_')}",
                            "type": "verse",
                            "number": verse_data.get('verse_number', ''),
                            "sanskrit": verse_data.get('sanskrit_verse', ''),
                            "transliteration": verse_data.get('sanskrit_transliteration', ''),
                            "synonyms": verse_data.get('synonyms', ''),
                            "translation": verse_data.get('translation', ''),
                            "purport": verse_data.get('purport', ''),
                            "container": f"canto_{canto_num}_chapter_{chapter_num}",
                            "canto": canto_num,
                            "chapter": chapter_num
                        }
                        all_content.append(content_item)
        
        else:  # Bhagavad-gītā
            # Handle Bhagavad-gītā structure
            container_key = self.config.container_key
            
            for container_num, container_data in self.data.get(container_key, {}).items():
                verses = container_data.get(self.config.verse_key, [])
                
                for verse_data in verses:
                    content_item = {
                        "id": f"bg_{container_num}_{verse_data.get('verse_number', '')}",
                        "type": "verse",
                        "number": verse_data.get('verse_number', ''),
                        "sanskrit": verse_data.get('sanskrit', ''),
                        "transliteration": verse_data.get('transliteration', ''),
                        "synonyms": verse_data.get('synonyms', ''),
                        "translation": verse_data.get('translation', ''),
                        "purport": verse_data.get('purport', ''),
                        "container": f"chapter_{container_num}",
                        "chapter": container_num
                    }
                    all_content.append(content_item)
        
        return all_content
    
    def _create_weighted_chunks(self, all_content: List[Dict], weight_type: str):
        """Create weighted chunks based on priority type"""
        chunks = []
        
        for content in all_content:
            content_parts = []
            
            if weight_type == "translation_first":
                # Prioritize translation over other content
                if content.get('translation'):
                    content_parts.append(f"Translation: {content['translation']}")
                if content.get('sanskrit'):
                    content_parts.append(f"Sanskrit: {content['sanskrit']}")
                if content.get('synonyms'):
                    content_parts.append(f"Word-for-word: {content['synonyms']}")
                if content.get('purport'):
                    # Truncate purport for translation-first approach
                    purport = content['purport'][:500] + "..." if len(content['purport']) > 500 else content['purport']
                    content_parts.append(f"Purport: {purport}")
            
            elif weight_type == "commentary_focused":
                # Prioritize purport and detailed explanation
                if content.get('purport'):
                    content_parts.append(f"Purport: {content['purport']}")
                if content.get('translation'):
                    content_parts.append(f"Translation: {content['translation']}")
                if content.get('synonyms'):
                    content_parts.append(f"Word-for-word: {content['synonyms']}")
                if content.get('sanskrit'):
                    content_parts.append(f"Sanskrit: {content['sanskrit']}")
            
            elif weight_type == "balanced":
                # Equal weight to all content
                if content.get('sanskrit'):
                    content_parts.append(f"Sanskrit: {content['sanskrit']}")
                if content.get('translation'):
                    content_parts.append(f"Translation: {content['translation']}")
                if content.get('synonyms'):
                    content_parts.append(f"Word-for-word: {content['synonyms']}")
                if content.get('purport'):
                    content_parts.append(f"Purport: {content['purport']}")
            
            elif weight_type == "essential_only":
                # Only core translation without detailed commentary
                if content.get('translation'):
                    content_parts.append(f"Translation: {content['translation']}")
                if content.get('sanskrit'):
                    content_parts.append(f"Sanskrit: {content['sanskrit']}")
                # Skip purport and synonyms for essential-only
            
            if content_parts:
                chunk = {
                    "id": content['id'],
                    "content": "\n".join(content_parts),
                    "number": content['number'],
                    "container": content['container'],
                    "source": self.config.title,
                    "weight_type": weight_type,
                    "metadata": {
                        "content_length": len("\n".join(content_parts)),
                        "has_sanskrit": bool(content.get('sanskrit')),
                        "has_translation": bool(content.get('translation')),
                        "has_purport": bool(content.get('purport')),
                        "scripture": self.config.title,
                        "weight_strategy": weight_type
                    }
                }
                
                # Add scripture-specific metadata
                if 'canto' in content:
                    chunk['canto'] = content['canto']
                    chunk['chapter'] = content['chapter']
                elif 'chapter' in content:
                    chunk['chapter'] = content['chapter']
                
                chunks.append(chunk)
        
        return chunks
    
    def _create_flexible_chunks(self, all_content: List[Dict]):
        """Create flexible chunks with adaptive sizes"""
        chunks = []
        current_chunk = []
        current_size = 0
        target_size = 1000  # Target characters per chunk
        
        for content in all_content:
            # Calculate content size
            content_text = ""
            if content.get('translation'):
                content_text += content['translation']
            if content.get('purport'):
                content_text += " " + content['purport']
            
            content_size = len(content_text)
            
            # Adaptive logic: if content is very long, make it its own chunk
            if content_size > target_size * 1.5:
                # Save current chunk if it has content
                if current_chunk:
                    chunks.append(self._finalize_flexible_chunk(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Make the long content its own chunk
                chunks.append(self._finalize_flexible_chunk([content]))
            
            # If adding this content would exceed target, finalize current chunk
            elif current_size + content_size > target_size and current_chunk:
                chunks.append(self._finalize_flexible_chunk(current_chunk))
                current_chunk = [content]
                current_size = content_size
            
            else:
                # Add to current chunk
                current_chunk.append(content)
                current_size += content_size
        
        # Finalize last chunk
        if current_chunk:
            chunks.append(self._finalize_flexible_chunk(current_chunk))
        
        return {
            "title": f"{self.config.title} - Flexible Chunks",
            "source": f"{self.config.title} by {self.config.author}",
            "chunking_strategy": "flexible_adaptive",
            "metadata": {
                "total_chunks": len(chunks),
                "average_chunk_size": sum(chunk["metadata"]["content_length"] for chunk in chunks) // len(chunks) if chunks else 0,
                "scripture": self.config.title,
                "target_chunk_size": target_size
            },
            "chunks": chunks
        }
    
    def _finalize_flexible_chunk(self, content_list: List[Dict]):
        """Finalize a flexible chunk from a list of content items"""
        if not content_list:
            return None
        
        # Combine content
        combined_parts = []
        container_info = []
        
        for content in content_list:
            content_part = f"{content['type'].title()} {content['number']}"
            if content.get('translation'):
                content_part += f": {content['translation']}"
            if content.get('purport'):
                content_part += f"\nPurport: {content['purport']}"
            
            combined_parts.append(content_part)
            container_info.append(content['container'])
        
        # Create chunk ID
        if len(content_list) == 1:
            chunk_id = content_list[0]['id']
        else:
            first_id = content_list[0]['id']
            last_id = content_list[-1]['id']
            chunk_id = f"{first_id}_to_{last_id}"
        
        chunk = {
            "id": chunk_id,
            "content": "\n\n".join(combined_parts),
            "containers": list(set(container_info)),
            "content_count": len(content_list),
            "source": self.config.title,
            "metadata": {
                "content_length": len("\n\n".join(combined_parts)),
                "content_items": len(content_list),
                "scripture": self.config.title,
                "chunking_type": "flexible_adaptive"
            }
        }
        
        return chunk


def export_all_scriptures():
    """Export RAG formats for all scriptures"""
    logger.info("Starting unified RAG export for all scriptures")
    
    results = {}
    
    for scripture_type in ScriptureType:
        try:
            logger.info(f"Exporting {scripture_type.name}")
            exporter = UnifiedRAGExporter(scripture_type)
            success = exporter.export_all_formats()
            results[scripture_type.name] = success
            
        except Exception as e:
            logger.error(f"Failed to export {scripture_type.name}: {e}")
            results[scripture_type.name] = False
    
    # Summary
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    
    logger.info(f"RAG export completed: {successful}/{total} scriptures successful")
    for scripture, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logger.info(f"  {scripture}: {status}")
    
    return results


def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Export RAG formats for Vedic scriptures")
    parser.add_argument(
        '--scripture',
        choices=['bg', 'sb', 'iso', 'all'],
        default='all',
        help='Scripture to export (bg=Bhagavad-gītā, sb=Śrīmad-Bhāgavatam, iso=Śrī Īśopaniṣad, all=all scriptures)'
    )
    
    args = parser.parse_args()
    
    if args.scripture == 'all':
        export_all_scriptures()
    else:
        scripture_map = {
            'bg': ScriptureType.BHAGAVAD_GITA,
            'sb': ScriptureType.SRIMAD_BHAGAVATAM, 
            'iso': ScriptureType.SRI_ISOPANISAD
        }
        
        scripture_type = scripture_map[args.scripture]
        exporter = UnifiedRAGExporter(scripture_type)
        success = exporter.export_all_formats()
        
        if success:
            logger.info(f"✅ Successfully exported {scripture_type.name}")
        else:
            logger.error(f"❌ Failed to export {scripture_type.name}")


if __name__ == "__main__":
    main()
