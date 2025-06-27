"""
Universal RAG Architecture - Demonstration Implementation

This file demonstrates the proposed universal architecture working alongside
the existing rag_chunker.py implementation. It shows how the new system can
be gradually integrated while maintaining backward compatibility.

This is a working prototype that can be immediately tested and extended.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from enum import Enum
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# CORE ABSTRACTIONS
# ============================================================================

class DocumentType(Enum):
    """Supported document types"""
    SCRIPTURE = "scripture"
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    PLAIN_TEXT = "text"


@dataclass
class ContentUnit:
    """Universal content unit - atomic unit of all document processing"""
    id: str
    content: str
    content_type: str  # verse, paragraph, section, heading, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    position: int = 0
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.metadata.setdefault('content_length', len(self.content))
        self.metadata.setdefault('created_at', datetime.now().isoformat())


@dataclass
class Chunk:
    """Universal chunk representation"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_units: List[str] = field(default_factory=list)
    chunk_type: str = "standard"
    quality_score: float = 0.0


@dataclass
class ChunkConfig:
    """Configuration for chunking strategies"""
    strategy_name: str
    max_chunk_size: int = 1000
    min_chunk_size: int = 100
    overlap_ratio: float = 0.1
    preserve_boundaries: bool = True
    custom_params: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# ABSTRACT BASE CLASSES
# ============================================================================

class DocumentProcessor(ABC):
    """Abstract base class for all document processors"""
    
    def __init__(self, document_type: DocumentType):
        self.document_type = document_type
        self.metadata = {}
        self.content_units = []
        self.raw_data = None
    
    @abstractmethod
    def load(self, source: Union[str, Path]) -> Any:
        """Load document from source"""
        pass
    
    @abstractmethod
    def extract_content_units(self) -> List[ContentUnit]:
        """Extract content units from document"""
        pass
    
    @abstractmethod
    def get_document_metadata(self) -> Dict[str, Any]:
        """Get document-level metadata"""
        pass
    
    def validate_structure(self) -> List[str]:
        """Validate document structure and return error messages"""
        errors = []
        if not self.content_units:
            errors.append("No content units extracted")
        return errors
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get document statistics"""
        if not self.content_units:
            return {}
        
        return {
            'total_units': len(self.content_units),
            'content_types': list(set(unit.content_type for unit in self.content_units)),
            'total_characters': sum(len(unit.content) for unit in self.content_units),
            'average_unit_length': sum(len(unit.content) for unit in self.content_units) / len(self.content_units),
            'document_type': self.document_type.value
        }


class ChunkingStrategy(ABC):
    """Abstract base class for all chunking strategies"""
    
    @abstractmethod
    def get_name(self) -> str:
        """Return strategy name"""
        pass
    
    @abstractmethod
    def chunk(self, content_units: List[ContentUnit], config: ChunkConfig) -> List[Chunk]:
        """Apply chunking strategy to content units"""
        pass
    
    def validate_config(self, config: ChunkConfig) -> List[str]:
        """Validate configuration and return error messages"""
        errors = []
        if config.max_chunk_size <= config.min_chunk_size:
            errors.append("max_chunk_size must be greater than min_chunk_size")
        if not 0 <= config.overlap_ratio <= 1:
            errors.append("overlap_ratio must be between 0 and 1")
        return errors


# ============================================================================
# CONCRETE IMPLEMENTATIONS
# ============================================================================

class ScriptureProcessor(DocumentProcessor):
    """Enhanced scripture processor using universal base class"""
    
    def __init__(self, scripture_type: str):
        super().__init__(DocumentType.SCRIPTURE)
        self.scripture_type = scripture_type
        self.config = self._get_scripture_config()
    
    def _get_scripture_config(self) -> Dict[str, Any]:
        """Get configuration for specific scripture type"""
        configs = {
            'bhagavad_gita': {
                'title': 'Bhagavad-gītā As It Is',
                'author': 'A.C. Bhaktivedanta Swami Prabhupāda',
                'verse_key': 'verses',
                'container_key': 'chapters',
                'content_unit_type': 'verse'
            },
            'srimad_bhagavatam': {
                'title': 'Śrīmad-Bhāgavatam',
                'author': 'A.C. Bhaktivedanta Swami Prabhupāda',
                'verse_key': 'verses',
                'container_key': 'chapters',
                'content_unit_type': 'verse',
                'has_cantos': True
            },
            'sri_isopanisad': {
                'title': 'Śrī Īśopaniṣad',
                'author': 'A.C. Bhaktivedanta Swami Prabhupāda',
                'verse_key': 'mantras',
                'container_key': 'mantras',
                'content_unit_type': 'mantra'
            }
        }
        return configs.get(self.scripture_type, {})
    
    def load(self, source: Union[str, Path]) -> Dict[str, Any]:
        """Load scripture data from JSON file"""
        with open(source, 'r', encoding='utf-8') as f:
            self.raw_data = json.load(f)
        return self.raw_data
    
    def extract_content_units(self) -> List[ContentUnit]:
        """Extract verses/mantras as universal content units"""
        if not self.raw_data:
            raise ValueError("No data loaded. Call load() first.")
        
        if self.scripture_type == 'bhagavad_gita':
            return self._extract_bg_units()
        elif self.scripture_type == 'srimad_bhagavatam':
            return self._extract_sb_units()
        elif self.scripture_type == 'sri_isopanisad':
            return self._extract_iso_units()
        else:
            raise ValueError(f"Unknown scripture type: {self.scripture_type}")
    
    def _extract_bg_units(self) -> List[ContentUnit]:
        """Extract Bhagavad-gītā content units"""
        units = []
        position = 0
        
        for chapter_num, chapter_data in self.raw_data.get('chapters', {}).items():
            chapter_title = chapter_data.get('title', f'Chapter {chapter_num}')
            
            for verse_data in chapter_data.get('verses', []):
                unit = ContentUnit(
                    id=f"bg_{chapter_num}_{self._clean_verse_id(verse_data.get('verse_number', ''))}",
                    content=self._format_scripture_content(verse_data),
                    content_type=self.config['content_unit_type'],
                    metadata={
                        'scripture': self.config['title'],
                        'chapter': chapter_num,
                        'chapter_title': chapter_title,
                        'verse_number': verse_data.get('verse_number', ''),
                        'has_sanskrit': bool(verse_data.get('sanskrit')),
                        'has_translation': bool(verse_data.get('translation')),
                        'has_purport': bool(verse_data.get('purport')),
                        'has_synonyms': bool(verse_data.get('synonyms')),
                    },
                    position=position,
                    raw_data=verse_data
                )
                units.append(unit)
                position += 1
        
        self.content_units = units
        return units
    
    def _extract_sb_units(self) -> List[ContentUnit]:
        """Extract Śrīmad-Bhāgavatam content units"""
        units = []
        position = 0
        
        for canto_num, canto_data in self.raw_data.items():
            chapters = canto_data.get('chapters', {})
            
            for chapter_num, chapter_data in chapters.items():
                chapter_title = chapter_data.get('title', f'Canto {canto_num}, Chapter {chapter_num}')
                
                for verse_data in chapter_data.get('verses', []):
                    unit = ContentUnit(
                        id=f"sb_{canto_num}_{chapter_num}_{self._clean_verse_id(verse_data.get('verse_number', ''))}",
                        content=self._format_scripture_content(verse_data, use_verse_prefix=True),
                        content_type=self.config['content_unit_type'],
                        metadata={
                            'scripture': self.config['title'],
                            'canto': canto_num,
                            'chapter': chapter_num,
                            'chapter_title': chapter_title,
                            'verse_number': verse_data.get('verse_number', ''),
                            'has_sanskrit': bool(verse_data.get('sanskrit_verse')),
                            'has_translation': bool(verse_data.get('translation')),
                            'has_purport': bool(verse_data.get('purport')),
                            'has_synonyms': bool(verse_data.get('synonyms')),
                        },
                        position=position,
                        raw_data=verse_data
                    )
                    units.append(unit)
                    position += 1
        
        self.content_units = units
        return units
    
    def _extract_iso_units(self) -> List[ContentUnit]:
        """Extract Śrī Īśopaniṣad content units"""
        units = []
        position = 0
        
        for mantra_data in self.raw_data.get('mantras', []):
            unit = ContentUnit(
                id=f"iso_{self._clean_verse_id(mantra_data.get('mantra_number', ''))}",
                content=self._format_scripture_content(mantra_data, use_mantra_prefix=True),
                content_type=self.config['content_unit_type'],
                metadata={
                    'scripture': self.config['title'],
                    'mantra_number': mantra_data.get('mantra_number', ''),
                    'has_sanskrit': bool(mantra_data.get('sanskrit_mantra')),
                    'has_translation': bool(mantra_data.get('translation')),
                    'has_purport': bool(mantra_data.get('purport')),
                    'has_synonyms': bool(mantra_data.get('synonyms')),
                },
                position=position,
                raw_data=mantra_data
            )
            units.append(unit)
            position += 1
        
        self.content_units = units
        return units
    
    def _format_scripture_content(self, verse_data: Dict, use_verse_prefix: bool = False, use_mantra_prefix: bool = False) -> str:
        """Format scripture content for universal processing"""
        parts = []
        
        # Add verse/mantra number
        if use_verse_prefix and verse_data.get('verse_number'):
            parts.append(f"Verse {verse_data['verse_number']}")
        elif use_mantra_prefix and verse_data.get('mantra_number'):
            parts.append(f"Mantra {verse_data['mantra_number']}")
        
        # Sanskrit text (handle different field names)
        sanskrit_key = self._get_sanskrit_key(verse_data)
        if verse_data.get(sanskrit_key):
            parts.append(f"Sanskrit: {verse_data[sanskrit_key]}")
        
        # Transliteration (handle different field names)
        transliteration_key = self._get_transliteration_key(verse_data)
        if verse_data.get(transliteration_key):
            parts.append(f"Transliteration: {verse_data[transliteration_key]}")
        
        # Synonyms/word-for-word
        if verse_data.get('synonyms'):
            parts.append(f"Word-for-word: {verse_data['synonyms']}")
        
        # Translation
        if verse_data.get('translation'):
            parts.append(f"Translation: {verse_data['translation']}")
        
        # Purport
        if verse_data.get('purport'):
            parts.append(f"Purport: {verse_data['purport']}")
        
        return "\n".join(parts)
    
    def _get_sanskrit_key(self, verse_data: Dict) -> str:
        """Get the correct Sanskrit field name"""
        if 'sanskrit' in verse_data:
            return 'sanskrit'
        elif 'sanskrit_verse' in verse_data:
            return 'sanskrit_verse'
        elif 'sanskrit_mantra' in verse_data:
            return 'sanskrit_mantra'
        return 'sanskrit'
    
    def _get_transliteration_key(self, verse_data: Dict) -> str:
        """Get the correct transliteration field name"""
        if 'transliteration' in verse_data:
            return 'transliteration'
        elif 'sanskrit_transliteration' in verse_data:
            return 'sanskrit_transliteration'
        return 'transliteration'
    
    def _clean_verse_id(self, verse_number: str) -> str:
        """Clean verse number for use in IDs"""
        return verse_number.replace('Bg. ', '').replace('.', '_').replace(' ', '_').lower()
    
    def get_document_metadata(self) -> Dict[str, Any]:
        """Get scripture-specific metadata"""
        base_metadata = {
            'type': 'scripture',
            'scripture_type': self.scripture_type,
            'title': self.config.get('title', 'Unknown Scripture'),
            'author': self.config.get('author', 'Unknown Author'),
            'content_unit_type': self.config.get('content_unit_type', 'verse'),
            'processing_timestamp': datetime.now().isoformat()
        }
        
        if self.content_units:
            base_metadata.update(self.get_statistics())
        
        return base_metadata


class StandardChunker(ChunkingStrategy):
    """Standard chunking strategy - maintains current functionality"""
    
    def get_name(self) -> str:
        return "standard"
    
    def chunk(self, content_units: List[ContentUnit], config: ChunkConfig) -> List[Chunk]:
        """Apply standard chunking - individual content units"""
        chunks = []
        
        for unit in content_units:
            chunk = Chunk(
                id=f"{unit.id}_chunk",
                content=unit.content,
                metadata={
                    **unit.metadata,
                    'chunking_strategy': self.get_name(),
                    'chunk_type': 'individual_unit',
                    'source_content_type': unit.content_type
                },
                source_units=[unit.id],
                chunk_type='individual_unit'
            )
            chunks.append(chunk)
        
        return chunks


class SemanticChunker(ChunkingStrategy):
    """Semantic chunking strategy - groups by content similarity"""
    
    def get_name(self) -> str:
        return "semantic"
    
    def chunk(self, content_units: List[ContentUnit], config: ChunkConfig) -> List[Chunk]:
        """Apply semantic chunking based on content similarity"""
        chunks = []
        
        # Simple implementation: group by chapter/container
        # In a full implementation, this would use embeddings and similarity
        container_groups = self._group_by_container(content_units)
        
        for container_id, units in container_groups.items():
            if len(units) == 1:
                # Single unit - create individual chunk
                unit = units[0]
                chunk = Chunk(
                    id=f"{unit.id}_semantic_chunk",
                    content=unit.content,
                    metadata={
                        **unit.metadata,
                        'chunking_strategy': self.get_name(),
                        'chunk_type': 'single_unit_semantic',
                        'container': container_id
                    },
                    source_units=[unit.id],
                    chunk_type='semantic_single'
                )
                chunks.append(chunk)
            else:
                # Multiple units - create grouped chunk
                combined_content = self._combine_units(units)
                chunk = Chunk(
                    id=f"{container_id}_semantic_group_chunk",
                    content=combined_content,
                    metadata={
                        'chunking_strategy': self.get_name(),
                        'chunk_type': 'semantic_group',
                        'container': container_id,
                        'unit_count': len(units),
                        'scripture': units[0].metadata.get('scripture', 'Unknown')
                    },
                    source_units=[unit.id for unit in units],
                    chunk_type='semantic_group'
                )
                chunks.append(chunk)
        
        return chunks
    
    def _group_by_container(self, content_units: List[ContentUnit]) -> Dict[str, List[ContentUnit]]:
        """Group content units by container (chapter, canto, etc.)"""
        groups = {}
        
        for unit in content_units:
            # Create container ID based on metadata
            if 'canto' in unit.metadata and 'chapter' in unit.metadata:
                container_id = f"canto_{unit.metadata['canto']}_chapter_{unit.metadata['chapter']}"
            elif 'chapter' in unit.metadata:
                container_id = f"chapter_{unit.metadata['chapter']}"
            else:
                container_id = "complete"
            
            if container_id not in groups:
                groups[container_id] = []
            groups[container_id].append(unit)
        
        return groups
    
    def _combine_units(self, units: List[ContentUnit]) -> str:
        """Combine multiple content units into single chunk content"""
        parts = []
        
        # Add container header if available
        first_unit = units[0]
        if 'chapter_title' in first_unit.metadata:
            parts.append(f"Chapter: {first_unit.metadata['chapter_title']}\n")
        
        # Add individual unit content
        for unit in units:
            parts.append(unit.content)
        
        return "\n\n".join(parts)


# ============================================================================
# UNIVERSAL RAG EXPORTER
# ============================================================================

class UniversalRAGExporter:
    """Universal RAG exporter supporting multiple document types and strategies"""
    
    def __init__(self, document_type: DocumentType, **kwargs):
        self.document_type = document_type
        self.processor = self._create_processor(**kwargs)
        self.chunking_strategies = {}
        self.exported_results = {}
        
        # Register default chunking strategies
        self._register_default_strategies()
    
    def _create_processor(self, **kwargs) -> DocumentProcessor:
        """Factory method to create appropriate processor"""
        if self.document_type == DocumentType.SCRIPTURE:
            scripture_type = kwargs.get('scripture_type')
            if not scripture_type:
                raise ValueError("scripture_type required for SCRIPTURE document type")
            return ScriptureProcessor(scripture_type)
        else:
            raise NotImplementedError(f"Processor for {self.document_type} not yet implemented")
    
    def _register_default_strategies(self):
        """Register default chunking strategies"""
        self.register_strategy(StandardChunker())
        self.register_strategy(SemanticChunker())
    
    def register_strategy(self, strategy: ChunkingStrategy):
        """Register a chunking strategy"""
        self.chunking_strategies[strategy.get_name()] = strategy
        logger.info(f"Registered chunking strategy: {strategy.get_name()}")
    
    def load_document(self, source: Union[str, Path]) -> bool:
        """Load document using appropriate processor"""
        try:
            self.processor.load(source)
            content_units = self.processor.extract_content_units()
            logger.info(f"Loaded document with {len(content_units)} content units")
            return True
        except Exception as e:
            logger.error(f"Failed to load document: {e}")
            return False
    
    def export_with_strategy(self, strategy_name: str, config: ChunkConfig, 
                           output_dir: Optional[Path] = None) -> List[Chunk]:
        """Export using a specific chunking strategy"""
        if strategy_name not in self.chunking_strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}. Available: {list(self.chunking_strategies.keys())}")
        
        if not self.processor.content_units:
            raise ValueError("No content units loaded. Call load_document() first.")
        
        strategy = self.chunking_strategies[strategy_name]
        
        # Validate configuration
        config_errors = strategy.validate_config(config)
        if config_errors:
            raise ValueError(f"Invalid config: {config_errors}")
        
        # Apply chunking strategy
        chunks = strategy.chunk(self.processor.content_units, config)
        
        # Store results
        self.exported_results[strategy_name] = chunks
        
        # Export to files if output directory provided
        if output_dir:
            self._export_chunks_to_files(chunks, strategy_name, output_dir)
        
        logger.info(f"Exported {len(chunks)} chunks using {strategy_name} strategy")
        return chunks
    
    def export_all_strategies(self, configs: Optional[Dict[str, ChunkConfig]] = None, 
                            output_dir: Optional[Path] = None) -> Dict[str, List[Chunk]]:
        """Export using multiple strategies"""
        if configs is None:
            # Use default configurations
            configs = {
                'standard': ChunkConfig(strategy_name='standard'),
                'semantic': ChunkConfig(strategy_name='semantic')
            }
        
        results = {}
        
        for strategy_name, config in configs.items():
            try:
                chunks = self.export_with_strategy(strategy_name, config, output_dir)
                results[strategy_name] = chunks
            except Exception as e:
                logger.error(f"Failed to export with strategy {strategy_name}: {e}")
        
        return results
    
    def _export_chunks_to_files(self, chunks: List[Chunk], strategy_name: str, output_dir: Path):
        """Export chunks to JSON and JSONL files"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare chunk data for export
        chunk_data = []
        for chunk in chunks:
            chunk_dict = {
                'id': chunk.id,
                'content': chunk.content,
                'metadata': chunk.metadata,
                'source_units': chunk.source_units,
                'chunk_type': chunk.chunk_type,
                'quality_score': chunk.quality_score
            }
            chunk_data.append(chunk_dict)
        
        # Generate filename based on document
        doc_metadata = self.processor.get_document_metadata()
        scripture_type = doc_metadata.get('scripture_type', 'unknown')
        base_filename = f"{scripture_type}_{strategy_name}_chunks"
        
        # Export as JSON
        json_path = output_dir / f"{base_filename}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, indent=2, ensure_ascii=False)
        
        # Export as JSONL
        jsonl_path = output_dir / f"{base_filename}.jsonl"
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            for chunk_dict in chunk_data:
                json.dump(chunk_dict, f, ensure_ascii=False)
                f.write('\n')
        
        logger.info(f"Exported chunks to {json_path} and {jsonl_path}")
    
    def get_export_summary(self) -> Dict[str, Any]:
        """Get summary of all exports"""
        summary = {
            'document_type': self.document_type.value,
            'document_metadata': self.processor.get_document_metadata(),
            'strategies_used': list(self.exported_results.keys()),
            'total_chunks_by_strategy': {
                strategy: len(chunks) 
                for strategy, chunks in self.exported_results.items()
            },
            'available_strategies': list(self.chunking_strategies.keys()),
            'export_timestamp': datetime.now().isoformat()
        }
        return summary


# ============================================================================
# DEMONSTRATION AND TESTING
# ============================================================================

def demonstrate_universal_architecture():
    """Demonstrate the universal RAG architecture with scripture data"""
    print("🚀 Universal RAG Architecture Demonstration")
    print("=" * 60)
    
    # Test with Bhagavad-gita
    try:
        print("\n📖 Testing with Bhagavad-gītā")
        print("-" * 30)
        
        exporter = UniversalRAGExporter(
            DocumentType.SCRIPTURE,
            scripture_type='bhagavad_gita'
        )
        
        # Load document
        bg_path = Path('data_bg/raw/bhagavad_gita_complete.json')
        if bg_path.exists():
            success = exporter.load_document(bg_path)
            if success:
                print("✅ Loaded Bhagavad-gītā successfully")
                
                # Show document statistics
                stats = exporter.processor.get_statistics()
                print(f"📊 Statistics: {stats['total_units']} verses, {stats['total_characters']:,} characters")
                
                # Export with multiple strategies
                output_dir = Path('demo_output/bg')
                results = exporter.export_all_strategies(output_dir=output_dir)
                
                for strategy_name, chunks in results.items():
                    print(f"✅ {strategy_name}: {len(chunks)} chunks")
                    
                    # Show first chunk as example
                    if chunks:
                        first_chunk = chunks[0]
                        print(f"   Sample chunk ID: {first_chunk.id}")
                        print(f"   Content preview: {first_chunk.content[:100]}...")
                
            else:
                print("❌ Failed to load Bhagavad-gītā")
        else:
            print(f"⚠️  Bhagavad-gītā data file not found: {bg_path}")
    
    except Exception as e:
        print(f"❌ Error with Bhagavad-gītā: {e}")
    
    # Test with Srimad Bhagavatam
    try:
        print("\n📖 Testing with Śrīmad-Bhāgavatam")
        print("-" * 30)
        
        exporter = UniversalRAGExporter(
            DocumentType.SCRIPTURE,
            scripture_type='srimad_bhagavatam'
        )
        
        # Load document
        sb_path = Path('data_sb/raw/srimad_bhagavatam_complete.json')
        if sb_path.exists():
            success = exporter.load_document(sb_path)
            if success:
                print("✅ Loaded Śrīmad-Bhāgavatam successfully")
                
                # Show document statistics
                stats = exporter.processor.get_statistics()
                print(f"📊 Statistics: {stats['total_units']} verses, {stats['total_characters']:,} characters")
                
                # Export with limited strategies for large dataset
                configs = {
                    'standard': ChunkConfig(strategy_name='standard')
                }
                output_dir = Path('demo_output/sb')
                results = exporter.export_all_strategies(configs, output_dir=output_dir)
                
                for strategy_name, chunks in results.items():
                    print(f"✅ {strategy_name}: {len(chunks)} chunks")
            else:
                print("❌ Failed to load Śrīmad-Bhāgavatam")
        else:
            print(f"⚠️  Śrīmad-Bhāgavatam data file not found: {sb_path}")
    
    except Exception as e:
        print(f"❌ Error with Śrīmad-Bhāgavatam: {e}")
    
    # Test with Sri Isopanisad
    try:
        print("\n📖 Testing with Śrī Īśopaniṣad")
        print("-" * 30)
        
        exporter = UniversalRAGExporter(
            DocumentType.SCRIPTURE,
            scripture_type='sri_isopanisad'
        )
        
        # Load document
        iso_path = Path('data_iso/raw/sri_isopanisad_complete.json')
        if iso_path.exists():
            success = exporter.load_document(iso_path)
            if success:
                print("✅ Loaded Śrī Īśopaniṣad successfully")
                
                # Show document statistics
                stats = exporter.processor.get_statistics()
                print(f"📊 Statistics: {stats['total_units']} mantras, {stats['total_characters']:,} characters")
                
                # Export with all strategies
                output_dir = Path('demo_output/iso')
                results = exporter.export_all_strategies(output_dir=output_dir)
                
                for strategy_name, chunks in results.items():
                    print(f"✅ {strategy_name}: {len(chunks)} chunks")
            else:
                print("❌ Failed to load Śrī Īśopaniṣad")
        else:
            print(f"⚠️  Śrī Īśopaniṣad data file not found: {iso_path}")
    
    except Exception as e:
        print(f"❌ Error with Śrī Īśopaniṣad: {e}")
    
    print("\n🎯 Demonstration completed!")
    print("Check the 'demo_output' directory for exported chunks.")


def compare_with_existing():
    """Compare new architecture output with existing rag_chunker.py output"""
    print("\n🔍 Comparing with Existing Implementation")
    print("=" * 50)
    
    try:
        # Import existing implementation
        from rag_chunker import UnifiedRAGExporter as LegacyExporter, ScriptureType
        
        # Test with small dataset (Bhagavad-gita)
        bg_path = Path('data_bg/raw/bhagavad_gita_complete.json')
        if bg_path.exists():
            # Legacy implementation
            print("Testing legacy implementation...")
            legacy_exporter = LegacyExporter(ScriptureType.BHAGAVAD_GITA)
            legacy_success = legacy_exporter.export_all_formats()
            
            # New implementation  
            print("Testing new implementation...")
            new_exporter = UniversalRAGExporter(
                DocumentType.SCRIPTURE,
                scripture_type='bhagavad_gita'
            )
            new_success = new_exporter.load_document(bg_path)
            
            if new_success:
                new_results = new_exporter.export_all_strategies()
                
                print(f"✅ Legacy export: {'Success' if legacy_success else 'Failed'}")
                print(f"✅ New export: {'Success' if new_success else 'Failed'}")
                
                if legacy_success and new_success:
                    print("📊 Both implementations working!")
                    print(f"New implementation produced {len(new_results)} strategy outputs")
            
        else:
            print("⚠️  Cannot compare - test data not available")
    
    except ImportError:
        print("⚠️  Legacy rag_chunker.py not available for comparison")
    except Exception as e:
        print(f"❌ Comparison failed: {e}")


if __name__ == "__main__":
    # Run demonstration
    demonstrate_universal_architecture()
    
    # Compare with existing implementation
    compare_with_existing()
    
    print("\n✨ Universal RAG Architecture demonstration complete!")
    print("This prototype shows how the new architecture can work alongside existing code.")
    print("Next steps: Implement advanced features like semantic embeddings and quality assessment.")
