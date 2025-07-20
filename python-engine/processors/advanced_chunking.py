import re
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging
from .content_categorizer import ContentDomain

class ChunkingStrategy(Enum):
    STANDARD = "standard"
    SECTION_BASED = "section_based"
    CHAPTER_BASED = "chapter_based"
    VERSE_BASED = "verse_based"
    PARAGRAPH_BASED = "paragraph_based"
    SENTENCE_BASED = "sentence_based"
    HYBRID = "hybrid"

@dataclass
class ChunkConfig:
    strategy: ChunkingStrategy
    chunk_size: int
    overlap: int
    preserve_boundaries: bool = True
    min_chunk_size: int = 50
    max_chunk_size: Optional[int] = None
    boundary_patterns: List[str] = None
    metadata_extraction: bool = True

@dataclass
class TextChunk:
    id: str
    text: str
    start_pos: int
    end_pos: int
    metadata: Dict
    summary: Optional[str] = None
    keywords: List[str] = None
    quality_score: float = 0.0
    source_citation: Optional[str] = None
    relationships: List[str] = None

class AdvancedChunker:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Domain-specific chunking configurations
        self.domain_configs = {
            ContentDomain.TECHNICAL: ChunkConfig(
                strategy=ChunkingStrategy.SECTION_BASED,
                chunk_size=1000,
                overlap=100,
                boundary_patterns=[r'^#{1,6}\s+', r'^\d+\.\s+', r'^```', r'^class\s+', r'^def\s+']
            ),
            ContentDomain.ACADEMIC: ChunkConfig(
                strategy=ChunkingStrategy.SECTION_BASED,
                chunk_size=1500,
                overlap=150,
                boundary_patterns=[r'^\d+\.\s+', r'^Abstract', r'^Introduction', r'^Conclusion', r'^References']
            ),
            ContentDomain.LITERATURE: ChunkConfig(
                strategy=ChunkingStrategy.CHAPTER_BASED,
                chunk_size=2000,
                overlap=200,
                boundary_patterns=[r'^Chapter\s+\d+', r'^CHAPTER\s+\d+', r'^\d+$']
            ),
            ContentDomain.LEGAL: ChunkConfig(
                strategy=ChunkingStrategy.SECTION_BASED,
                chunk_size=1200,
                overlap=120,
                boundary_patterns=[r'^§\s*\d+', r'^\([a-z]\)', r'^\d+\.\s+', r'^Article\s+\d+']
            ),
            ContentDomain.RELIGIOUS: ChunkConfig(
                strategy=ChunkingStrategy.VERSE_BASED,
                chunk_size=800,
                overlap=80,
                boundary_patterns=[r'^\d+:\d+', r'^Chapter\s+\d+', r'^Verse\s+\d+']
            ),
            ContentDomain.MEDICAL: ChunkConfig(
                strategy=ChunkingStrategy.SECTION_BASED,
                chunk_size=1000,
                overlap=100,
                boundary_patterns=[r'^Symptoms?', r'^Treatment', r'^Diagnosis', r'^Procedure']
            ),
            ContentDomain.BUSINESS: ChunkConfig(
                strategy=ChunkingStrategy.SECTION_BASED,
                chunk_size=1200,
                overlap=120,
                boundary_patterns=[r'^Executive Summary', r'^Q[1-4]\s+\d{4}', r'^Financial']
            )
        }
        
    def chunk_text(self, text: str, domain: ContentDomain = ContentDomain.UNKNOWN, 
                   custom_config: Optional[ChunkConfig] = None) -> List[TextChunk]:
        """Main chunking method with domain-aware strategies"""
        if not text:
            return []
            
        # Get configuration
        config = custom_config or self.domain_configs.get(domain, ChunkConfig(
            strategy=ChunkingStrategy.STANDARD,
            chunk_size=1000,
            overlap=100
        ))
        
        # Apply chunking strategy
        if config.strategy == ChunkingStrategy.STANDARD:
            chunks = self._standard_chunking(text, config)
        elif config.strategy == ChunkingStrategy.SECTION_BASED:
            chunks = self._section_based_chunking(text, config)
        elif config.strategy == ChunkingStrategy.CHAPTER_BASED:
            chunks = self._chapter_based_chunking(text, config)
        elif config.strategy == ChunkingStrategy.VERSE_BASED:
            chunks = self._verse_based_chunking(text, config)
        elif config.strategy == ChunkingStrategy.PARAGRAPH_BASED:
            chunks = self._paragraph_based_chunking(text, config)
        elif config.strategy == ChunkingStrategy.SENTENCE_BASED:
            chunks = self._sentence_based_chunking(text, config)
        elif config.strategy == ChunkingStrategy.HYBRID:
            chunks = self._hybrid_chunking(text, config, domain)
        else:
            chunks = self._standard_chunking(text, config)
            
        # Post-process chunks
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            processed_chunk = self._post_process_chunk(chunk, i, config)
            processed_chunks.append(processed_chunk)
            
        return processed_chunks
        
    def _standard_chunking(self, text: str, config: ChunkConfig) -> List[TextChunk]:
        """Standard size-based chunking with smart overlap"""
        chunks = []
        words = text.split()
        
        if not words:
            return chunks
            
        current_pos = 0
        chunk_id = 0
        
        while current_pos < len(words):
            # Calculate chunk end
            chunk_end = min(current_pos + config.chunk_size, len(words))
            
            # Find smart boundary if preserve_boundaries is True
            if config.preserve_boundaries and chunk_end < len(words):
                chunk_end = self._find_smart_boundary(words, current_pos, chunk_end)
                
            # Extract chunk text
            chunk_words = words[current_pos:chunk_end]
            chunk_text = ' '.join(chunk_words)
            
            # Calculate positions in original text
            start_char = len(' '.join(words[:current_pos])) + (1 if current_pos > 0 else 0)
            end_char = start_char + len(chunk_text)
            
            # Create chunk
            chunk = TextChunk(
                id=f"chunk_{chunk_id}",
                text=chunk_text,
                start_pos=start_char,
                end_pos=end_char,
                metadata={
                    'chunk_index': chunk_id,
                    'word_count': len(chunk_words),
                    'strategy': 'standard'
                }
            )
            chunks.append(chunk)
            
            # Move to next chunk with overlap
            overlap_words = min(config.overlap, len(chunk_words) // 2)
            current_pos = chunk_end - overlap_words
            chunk_id += 1
            
        return chunks
        
    def _section_based_chunking(self, text: str, config: ChunkConfig) -> List[TextChunk]:
        """Section-based chunking preserving document structure"""
        chunks = []
        
        # Find section boundaries
        sections = self._find_sections(text, config.boundary_patterns or [])
        
        if not sections:
            # Fallback to standard chunking
            return self._standard_chunking(text, config)
            
        chunk_id = 0
        for section in sections:
            section_text = section['text']
            
            # If section is too large, split it
            if len(section_text.split()) > config.chunk_size:
                sub_chunks = self._split_large_section(section_text, config)
                for sub_chunk in sub_chunks:
                    sub_chunk.id = f"section_{chunk_id}"
                    sub_chunk.metadata.update({
                        'section_title': section.get('title', ''),
                        'section_level': section.get('level', 0),
                        'strategy': 'section_based'
                    })
                    chunks.append(sub_chunk)
                    chunk_id += 1
            else:
                # Use entire section as chunk
                chunk = TextChunk(
                    id=f"section_{chunk_id}",
                    text=section_text,
                    start_pos=section['start_pos'],
                    end_pos=section['end_pos'],
                    metadata={
                        'section_title': section.get('title', ''),
                        'section_level': section.get('level', 0),
                        'word_count': len(section_text.split()),
                        'strategy': 'section_based'
                    }
                )
                chunks.append(chunk)
                chunk_id += 1
                
        return chunks
        
    def _chapter_based_chunking(self, text: str, config: ChunkConfig) -> List[TextChunk]:
        """Chapter-based chunking for literature"""
        chunks = []
        
        # Find chapter boundaries
        chapter_patterns = config.boundary_patterns or [
            r'^Chapter\s+\d+',
            r'^CHAPTER\s+\d+',
            r'^\d+$',
            r'^Ch\.\s*\d+'
        ]
        
        chapters = self._find_chapters(text, chapter_patterns)
        
        if not chapters:
            return self._standard_chunking(text, config)
            
        chunk_id = 0
        for chapter in chapters:
            chapter_text = chapter['text']
            
            # If chapter is too large, split by paragraphs
            if len(chapter_text.split()) > config.chunk_size:
                paragraphs = chapter_text.split('\n\n')
                current_chunk = ""
                current_start = chapter['start_pos']
                
                for paragraph in paragraphs:
                    if len((current_chunk + paragraph).split()) > config.chunk_size and current_chunk:
                        # Save current chunk
                        chunk = TextChunk(
                            id=f"chapter_{chunk_id}",
                            text=current_chunk.strip(),
                            start_pos=current_start,
                            end_pos=current_start + len(current_chunk),
                            metadata={
                                'chapter_title': chapter.get('title', ''),
                                'chapter_number': chapter.get('number'),
                                'word_count': len(current_chunk.split()),
                                'strategy': 'chapter_based'
                            }
                        )
                        chunks.append(chunk)
                        chunk_id += 1
                        
                        # Start new chunk with overlap
                        overlap_text = ' '.join(current_chunk.split()[-config.overlap:])
                        current_chunk = overlap_text + ' ' + paragraph
                        current_start = current_start + len(current_chunk) - len(paragraph) - 1
                    else:
                        current_chunk += ('\n\n' if current_chunk else '') + paragraph
                        
                # Add final chunk
                if current_chunk.strip():
                    chunk = TextChunk(
                        id=f"chapter_{chunk_id}",
                        text=current_chunk.strip(),
                        start_pos=current_start,
                        end_pos=current_start + len(current_chunk),
                        metadata={
                            'chapter_title': chapter.get('title', ''),
                            'chapter_number': chapter.get('number'),
                            'word_count': len(current_chunk.split()),
                            'strategy': 'chapter_based'
                        }
                    )
                    chunks.append(chunk)
                    chunk_id += 1
            else:
                # Use entire chapter as chunk
                chunk = TextChunk(
                    id=f"chapter_{chunk_id}",
                    text=chapter_text,
                    start_pos=chapter['start_pos'],
                    end_pos=chapter['end_pos'],
                    metadata={
                        'chapter_title': chapter.get('title', ''),
                        'chapter_number': chapter.get('number'),
                        'word_count': len(chapter_text.split()),
                        'strategy': 'chapter_based'
                    }
                )
                chunks.append(chunk)
                chunk_id += 1
                
        return chunks
        
    def _verse_based_chunking(self, text: str, config: ChunkConfig) -> List[TextChunk]:
        """Verse-based chunking for religious texts"""
        chunks = []
        
        # Find verses
        verse_pattern = r'(\d+:\d+)\s*([^0-9:]*?)(?=\d+:\d+|$)'
        verses = re.finditer(verse_pattern, text, re.MULTILINE | re.DOTALL)
        
        current_chunk_verses = []
        current_chunk_text = ""
        chunk_id = 0
        
        for verse_match in verses:
            verse_ref = verse_match.group(1)
            verse_text = verse_match.group(2).strip()
            
            # Check if adding this verse would exceed chunk size
            test_text = current_chunk_text + f"{verse_ref} {verse_text}\n"
            if len(test_text.split()) > config.chunk_size and current_chunk_text:
                # Save current chunk
                chunk = TextChunk(
                    id=f"verses_{chunk_id}",
                    text=current_chunk_text.strip(),
                    start_pos=0,  # Would need to calculate properly
                    end_pos=len(current_chunk_text),
                    metadata={
                        'verses': current_chunk_verses,
                        'verse_count': len(current_chunk_verses),
                        'word_count': len(current_chunk_text.split()),
                        'strategy': 'verse_based'
                    }
                )
                chunks.append(chunk)
                chunk_id += 1
                
                # Start new chunk with overlap (last few verses)
                overlap_verses = current_chunk_verses[-min(config.overlap // 50, len(current_chunk_verses)):]
                current_chunk_verses = overlap_verses + [verse_ref]
                current_chunk_text = '\n'.join([f"{v} {text}" for v, text in [(verse_ref, verse_text)]])
            else:
                current_chunk_verses.append(verse_ref)
                current_chunk_text = test_text
                
        # Add final chunk
        if current_chunk_text.strip():
            chunk = TextChunk(
                id=f"verses_{chunk_id}",
                text=current_chunk_text.strip(),
                start_pos=0,
                end_pos=len(current_chunk_text),
                metadata={
                    'verses': current_chunk_verses,
                    'verse_count': len(current_chunk_verses),
                    'word_count': len(current_chunk_text.split()),
                    'strategy': 'verse_based'
                }
            )
            chunks.append(chunk)
            
        return chunks
        
    def _paragraph_based_chunking(self, text: str, config: ChunkConfig) -> List[TextChunk]:
        """Paragraph-based chunking"""
        chunks = []
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        current_chunk = ""
        chunk_id = 0
        
        for paragraph in paragraphs:
            test_chunk = current_chunk + ('\n\n' if current_chunk else '') + paragraph
            
            if len(test_chunk.split()) > config.chunk_size and current_chunk:
                # Save current chunk
                chunk = TextChunk(
                    id=f"para_{chunk_id}",
                    text=current_chunk,
                    start_pos=0,
                    end_pos=len(current_chunk),
                    metadata={
                        'paragraph_count': current_chunk.count('\n\n') + 1,
                        'word_count': len(current_chunk.split()),
                        'strategy': 'paragraph_based'
                    }
                )
                chunks.append(chunk)
                chunk_id += 1
                current_chunk = paragraph
            else:
                current_chunk = test_chunk
                
        # Add final chunk
        if current_chunk:
            chunk = TextChunk(
                id=f"para_{chunk_id}",
                text=current_chunk,
                start_pos=0,
                end_pos=len(current_chunk),
                metadata={
                    'paragraph_count': current_chunk.count('\n\n') + 1,
                    'word_count': len(current_chunk.split()),
                    'strategy': 'paragraph_based'
                }
            )
            chunks.append(chunk)
            
        return chunks
        
    def _sentence_based_chunking(self, text: str, config: ChunkConfig) -> List[TextChunk]:
        """Sentence-based chunking for fine-grained analysis"""
        chunks = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        current_chunk = ""
        chunk_id = 0
        
        for sentence in sentences:
            test_chunk = current_chunk + (' ' if current_chunk else '') + sentence + '.'
            
            if len(test_chunk.split()) > config.chunk_size and current_chunk:
                chunk = TextChunk(
                    id=f"sent_{chunk_id}",
                    text=current_chunk,
                    start_pos=0,
                    end_pos=len(current_chunk),
                    metadata={
                        'sentence_count': current_chunk.count('.') + current_chunk.count('!') + current_chunk.count('?'),
                        'word_count': len(current_chunk.split()),
                        'strategy': 'sentence_based'
                    }
                )
                chunks.append(chunk)
                chunk_id += 1
                current_chunk = sentence + '.'
            else:
                current_chunk = test_chunk
                
        if current_chunk:
            chunk = TextChunk(
                id=f"sent_{chunk_id}",
                text=current_chunk,
                start_pos=0,
                end_pos=len(current_chunk),
                metadata={
                    'sentence_count': current_chunk.count('.') + current_chunk.count('!') + current_chunk.count('?'),
                    'word_count': len(current_chunk.split()),
                    'strategy': 'sentence_based'
                }
            )
            chunks.append(chunk)
            
        return chunks
        
    def _hybrid_chunking(self, text: str, config: ChunkConfig, domain: ContentDomain) -> List[TextChunk]:
        """Hybrid chunking combining multiple strategies"""
        # First try structure-based chunking
        if domain in [ContentDomain.TECHNICAL, ContentDomain.ACADEMIC]:
            chunks = self._section_based_chunking(text, config)
        elif domain == ContentDomain.LITERATURE:
            chunks = self._chapter_based_chunking(text, config)
        elif domain == ContentDomain.RELIGIOUS:
            chunks = self._verse_based_chunking(text, config)
        else:
            chunks = self._paragraph_based_chunking(text, config)
            
        # If structure-based chunking didn't work well, fall back to standard
        if not chunks or len(chunks) < 2:
            chunks = self._standard_chunking(text, config)
            
        return chunks
        
    def _find_smart_boundary(self, words: List[str], start: int, end: int) -> int:
        """Find a smart boundary near the target end position"""
        # Look for sentence endings near the target position
        search_range = min(50, (end - start) // 4)  # Search within 25% of chunk size
        
        for i in range(end - 1, max(start, end - search_range), -1):
            if i < len(words) and words[i].endswith(('.', '!', '?')):
                return i + 1
                
        # Look for paragraph breaks
        for i in range(end - 1, max(start, end - search_range), -1):
            if i < len(words) and '\n\n' in words[i]:
                return i + 1
                
        return end
        
    def _find_sections(self, text: str, patterns: List[str]) -> List[Dict]:
        """Find sections based on patterns"""
        sections = []
        lines = text.split('\n')
        current_section = {'text': '', 'start_pos': 0, 'title': '', 'level': 0}
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check if line matches any section pattern
            section_match = None
            for pattern in patterns:
                match = re.match(pattern, line_stripped)
                if match:
                    section_match = match
                    break
                    
            if section_match:
                # Save previous section
                if current_section['text'].strip():
                    current_section['end_pos'] = current_section['start_pos'] + len(current_section['text'])
                    sections.append(current_section.copy())
                    
                # Start new section
                current_section = {
                    'text': line + '\n',
                    'start_pos': sum(len(l) + 1 for l in lines[:i]),
                    'title': line_stripped,
                    'level': self._get_section_level(line_stripped)
                }
            else:
                current_section['text'] += line + '\n'
                
        # Add final section
        if current_section['text'].strip():
            current_section['end_pos'] = current_section['start_pos'] + len(current_section['text'])
            sections.append(current_section)
            
        return sections
        
    def _find_chapters(self, text: str, patterns: List[str]) -> List[Dict]:
        """Find chapters based on patterns"""
        chapters = []
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE))
            
            for i, match in enumerate(matches):
                start_pos = match.start()
                
                # Find end position (start of next chapter or end of text)
                if i + 1 < len(matches):
                    end_pos = matches[i + 1].start()
                else:
                    end_pos = len(text)
                    
                chapter_text = text[start_pos:end_pos].strip()
                chapter_title = match.group(0)
                
                # Extract chapter number if possible
                number_match = re.search(r'\d+', chapter_title)
                chapter_number = int(number_match.group()) if number_match else None
                
                chapters.append({
                    'text': chapter_text,
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'title': chapter_title,
                    'number': chapter_number
                })
                
            if chapters:  # If we found chapters with this pattern, use them
                break
                
        return sorted(chapters, key=lambda x: x['start_pos'])
        
    def _split_large_section(self, text: str, config: ChunkConfig) -> List[TextChunk]:
        """Split a large section into smaller chunks"""
        # Use standard chunking for large sections
        temp_config = ChunkConfig(
            strategy=ChunkingStrategy.STANDARD,
            chunk_size=config.chunk_size,
            overlap=config.overlap
        )
        return self._standard_chunking(text, temp_config)
        
    def _get_section_level(self, title: str) -> int:
        """Determine section level from title"""
        if title.startswith('#'):
            return title.count('#')
        elif re.match(r'^\d+\.', title):
            return title.count('.') + 1
        else:
            return 1
            
    def _post_process_chunk(self, chunk: TextChunk, index: int, config: ChunkConfig) -> TextChunk:
        """Post-process chunk to add metadata and quality scoring"""
        if config.metadata_extraction:
            # Generate summary
            chunk.summary = self._generate_summary(chunk.text)
            
            # Extract keywords
            chunk.keywords = self._extract_keywords(chunk.text)
            
            # Calculate quality score
            chunk.quality_score = self._calculate_chunk_quality(chunk)
            
            # Generate source citation
            chunk.source_citation = f"Chunk {index + 1}"
            
        return chunk
        
    def _generate_summary(self, text: str) -> str:
        """Generate a simple rule-based summary"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.split()) > 3]
        
        if not sentences:
            return text[:100] + "..." if len(text) > 100 else text
            
        # Take first sentence as summary
        return sentences[0] + "."
        
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords using simple frequency analysis"""
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_freq = {}
        
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
                
        # Return top 5 most frequent words
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:5]]
        
    def _calculate_chunk_quality(self, chunk: TextChunk) -> float:
        """Calculate quality score for a chunk"""
        text = chunk.text
        
        # Basic quality metrics
        word_count = len(text.split())
        sentence_count = len(re.split(r'[.!?]+', text))
        
        # Quality factors
        quality = 1.0
        
        # Penalize very short chunks
        if word_count < 20:
            quality -= 0.3
            
        # Penalize chunks with very long or very short sentences
        if sentence_count > 0:
            avg_sentence_length = word_count / sentence_count
            if avg_sentence_length > 50 or avg_sentence_length < 5:
                quality -= 0.2
                
        # Reward chunks with good structure
        if '\n' in text:  # Has line breaks
            quality += 0.1
            
        # Check for incomplete sentences
        if not text.strip().endswith(('.', '!', '?')):
            quality -= 0.1
            
        return max(0.0, min(1.0, quality))