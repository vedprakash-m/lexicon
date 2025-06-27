"""
Text Processing Pipeline

This module provides comprehensive text cleaning, normalization, and preprocessing
for creating high-quality RAG datasets, with special focus on spiritual texts
and multi-language content.

Features:
- HTML cleaning and extraction
- Text normalization and standardization
- Language detection and encoding handling
- Domain-aware cleaning for spiritual texts
- Quality assessment and validation

Author: Lexicon Development Team
"""

import re
import html
import logging
import unicodedata
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
import hashlib

try:
    import ftfy
    HAS_FTFY = True
except ImportError:
    HAS_FTFY = False

try:
    import langdetect
    from langdetect import detect_langs
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False
except Exception as e:
    # Sometimes langdetect has initialization issues
    logger.warning(f"langdetect available but failed to initialize: {e}")
    HAS_LANGDETECT = False

try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False

from bs4 import BeautifulSoup, Comment

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class TextQualityMetrics:
    """Metrics for assessing text quality."""
    
    # Basic metrics
    character_count: int = 0
    word_count: int = 0
    sentence_count: int = 0
    paragraph_count: int = 0
    
    # Language and encoding
    detected_language: str = "unknown"
    language_confidence: float = 0.0
    encoding_issues: int = 0
    
    # Content quality
    readability_score: float = 0.0
    content_density: float = 0.0  # Ratio of meaningful content
    repetition_score: float = 0.0
    
    # Domain-specific (spiritual texts)
    sanskrit_verse_count: int = 0
    transliteration_count: int = 0
    has_structured_content: bool = False
    
    # Technical quality
    html_artifacts: int = 0
    formatting_artifacts: int = 0
    noise_level: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'character_count': self.character_count,
            'word_count': self.word_count,
            'sentence_count': self.sentence_count,
            'paragraph_count': self.paragraph_count,
            'detected_language': self.detected_language,
            'language_confidence': self.language_confidence,
            'encoding_issues': self.encoding_issues,
            'readability_score': self.readability_score,
            'content_density': self.content_density,
            'repetition_score': self.repetition_score,
            'sanskrit_verse_count': self.sanskrit_verse_count,
            'transliteration_count': self.transliteration_count,
            'has_structured_content': self.has_structured_content,
            'html_artifacts': self.html_artifacts,
            'formatting_artifacts': self.formatting_artifacts,
            'noise_level': self.noise_level
        }


@dataclass
class ProcessingConfig:
    """Configuration for text processing operations."""
    
    # HTML cleaning
    strip_html: bool = True
    preserve_structure: bool = True  # Keep paragraph breaks, etc.
    remove_comments: bool = True
    remove_scripts: bool = True
    remove_styles: bool = True
    
    # Text normalization
    normalize_unicode: bool = True
    normalize_whitespace: bool = True
    normalize_quotes: bool = True
    normalize_punctuation: bool = True
    fix_encoding: bool = True
    
    # Language processing
    detect_language: bool = True
    language_threshold: float = 0.7  # Minimum confidence for language detection
    
    # Domain-specific processing
    preserve_sanskrit: bool = True
    preserve_transliteration: bool = True
    preserve_verse_numbers: bool = True
    clean_spiritual_formatting: bool = True
    
    # Quality control
    min_content_length: int = 50
    max_repetition_ratio: float = 0.5
    remove_boilerplate: bool = True
    
    # Output control
    include_quality_metrics: bool = True
    debug_mode: bool = False


class HTMLCleaner:
    """Specialized HTML cleaning for various content types."""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
    
    def clean_html(self, html_content: str) -> str:
        """Clean HTML content while preserving important structure."""
        if not html_content.strip():
            return ""
        
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            self._remove_unwanted_elements(soup)
            
            # Convert to text while preserving structure
            text = self._extract_structured_text(soup)
            
            return text
            
        except Exception as e:
            logger.warning(f"HTML cleaning failed, using fallback: {e}")
            return self._fallback_html_clean(html_content)
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup):
        """Remove scripts, styles, comments, and other unwanted elements."""
        
        # Remove scripts and styles
        if self.config.remove_scripts:
            for element in soup(['script', 'noscript']):
                element.decompose()
        
        if self.config.remove_styles:
            for element in soup(['style', 'link']):
                element.decompose()
        
        # Remove comments
        if self.config.remove_comments:
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()
        
        # Remove navigation and boilerplate elements
        if self.config.remove_boilerplate:
            for element in soup(['nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Remove common boilerplate classes/ids
            boilerplate_selectors = [
                '[class*="nav"]', '[class*="menu"]', '[class*="sidebar"]',
                '[class*="footer"]', '[class*="header"]', '[class*="ad"]',
                '[id*="nav"]', '[id*="menu"]', '[id*="sidebar"]'
            ]
            
            for selector in boilerplate_selectors:
                for element in soup.select(selector):
                    element.decompose()
    
    def _extract_structured_text(self, soup: BeautifulSoup) -> str:
        """Extract text while preserving logical structure."""
        text_parts = []
        
        # Process each element in document order
        for element in soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'br']):
            element_text = element.get_text(strip=True)
            
            if element_text:
                # Preserve paragraph breaks for block elements
                if element.name in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    text_parts.append(element_text + '\n\n')
                elif element.name == 'li':
                    text_parts.append('• ' + element_text + '\n')
                elif element.name == 'br':
                    text_parts.append('\n')
        
        # If no structured content found, get all text with proper spacing
        if not text_parts:
            # Get all text elements and join with spaces
            all_text = soup.get_text(separator=' ', strip=True)
            text_parts = [all_text]
        
        result = ''.join(text_parts)
        
        # Clean up excessive whitespace while preserving structure
        result = re.sub(r' +', ' ', result)  # Multiple spaces to single
        result = re.sub(r'\n +', '\n', result)  # Remove leading spaces on lines
        
        return result
    
    def _fallback_html_clean(self, html_content: str) -> str:
        """Fallback HTML cleaning using regex."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html_content)
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Basic whitespace normalization
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()


class TextNormalizer:
    """Comprehensive text normalization and standardization."""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
    
    def normalize_text(self, text: str) -> str:
        """Apply comprehensive text normalization."""
        if not text.strip():
            return ""
        
        # Fix encoding issues first
        if self.config.fix_encoding:
            text = self._fix_encoding(text)
        
        # Normalize Unicode
        if self.config.normalize_unicode:
            text = self._normalize_unicode(text)
        
        # Normalize quotes and punctuation
        if self.config.normalize_quotes:
            text = self._normalize_quotes(text)
        
        if self.config.normalize_punctuation:
            text = self._normalize_punctuation(text)
        
        # Normalize whitespace
        if self.config.normalize_whitespace:
            text = self._normalize_whitespace(text)
        
        # Domain-specific normalization
        if self.config.clean_spiritual_formatting:
            text = self._clean_spiritual_formatting(text)
        
        return text
    
    def _fix_encoding(self, text: str) -> str:
        """Fix common encoding issues."""
        if not HAS_FTFY:
            logger.debug("ftfy not available, skipping encoding fix")
            return text
        
        try:
            # ftfy fixes various encoding issues
            fixed_text = ftfy.fix_text(text)
            return fixed_text
        except Exception as e:
            logger.warning(f"Encoding fix failed: {e}")
            return text
    
    def _normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters."""
        # Use NFC normalization to combine characters
        text = unicodedata.normalize('NFC', text)
        
        # Remove non-printing characters except basic whitespace
        text = ''.join(char for char in text 
                      if unicodedata.category(char)[0] != 'C' 
                      or char in '\n\r\t ')
        
        return text
    
    def _normalize_quotes(self, text: str) -> str:
        """Normalize various quote characters."""
        # Normalize curly quotes to straight quotes
        quote_map = {
            '"': '"', '"': '"',  # Left/right double quotes
            ''': "'", ''': "'",  # Left/right single quotes
            '‚': "'", '„': '"',  # Low quotes
            '‹': "'", '›': "'",  # Single angle quotes
            '«': '"', '»': '"',  # Double angle quotes
        }
        
        for old, new in quote_map.items():
            text = text.replace(old, new)
        
        return text
    
    def _normalize_punctuation(self, text: str) -> str:
        """Normalize punctuation marks."""
        # Normalize dashes
        text = re.sub(r'[–—]', '-', text)  # Em/en dash to hyphen
        
        # Normalize ellipsis
        text = re.sub(r'…', '...', text)
        text = re.sub(r'\.{4,}', '...', text)  # Multiple dots to ellipsis
        
        # Remove excessive punctuation
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace characters."""
        # Replace various whitespace chars with regular space
        text = re.sub(r'[\xa0\u2000-\u200a\u202f\u205f\u3000]', ' ', text)
        
        # Normalize line breaks
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\r', '\n', text)
        
        # Reduce multiple spaces to single space
        text = re.sub(r' +', ' ', text)
        
        # Reduce multiple line breaks but preserve paragraph structure
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Trim trailing spaces from lines
        text = '\n'.join(line.rstrip() for line in text.split('\n'))
        
        return text.strip()
    
    def _clean_spiritual_formatting(self, text: str) -> str:
        """Clean formatting specific to spiritual texts."""
        # Preserve Sanskrit verse numbers (e.g., "॥ 47 ॥")
        if not self.config.preserve_verse_numbers:
            text = re.sub(r'॥\s*\d+\s*॥', '', text)
        
        # Clean repetitive headers/footers common in spiritual texts
        text = re.sub(r'^(Chapter \d+|Bhagavad[- ]Gita|Srimad[- ]Bhagavatam).*$', '', text, flags=re.MULTILINE)
        
        # Remove page numbers and references
        text = re.sub(r'\[Page \d+\]', '', text)
        text = re.sub(r'Page \d+', '', text)
        
        # Remove common copyright and reference text
        text = re.sub(r'Copyright.*?Foundation', '', text, flags=re.IGNORECASE)
        text = re.sub(r'All rights reserved', '', text, flags=re.IGNORECASE)
        
        return text


class LanguageDetector:
    """Language detection and handling."""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """Detect the primary language of the text."""
        if not HAS_LANGDETECT:
            logger.debug("langdetect not available, defaulting to English")
            return "en", 0.5
        
        if not text.strip() or len(text) < 20:
            return "unknown", 0.0
        
        try:
            # Get multiple language predictions
            predictions = detect_langs(text)
            
            if predictions:
                # Return the most confident prediction
                top_prediction = predictions[0]
                return top_prediction.lang, top_prediction.prob
            else:
                return "unknown", 0.0
                
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return "unknown", 0.0
    
    def is_sanskrit(self, text: str) -> bool:
        """Check if text contains significant Sanskrit content."""
        if not text:
            return False
        
        # Count Devanagari characters
        devanagari_count = sum(1 for char in text if '\u0900' <= char <= '\u097F')
        total_chars = len(text.replace(' ', '').replace('\n', ''))
        
        if total_chars == 0:
            return False
        
        # If more than 30% Devanagari, consider it Sanskrit
        return (devanagari_count / total_chars) > 0.3
    
    def is_transliteration(self, text: str) -> bool:
        """Check if text appears to be Sanskrit transliteration."""
        if not text:
            return False
        
        # Common Sanskrit transliteration patterns
        sanskrit_patterns = [
            r'[aāiīuūeorṛ]',  # Sanskrit vowels with diacritics
            r'[kgcjṭḍtnpbmy]h',  # Aspirated consonants
            r'[ṭḍṅñṇṃ]',  # Retroflex and nasal consonants
            r'[śṣ]',  # Sibilants
            r'ṛ|ḷ',  # Vocalic r/l
        ]
        
        text_sample = text.lower()[:500]  # Check first 500 chars
        
        # Count matches
        matches = sum(1 for pattern in sanskrit_patterns 
                     if re.search(pattern, text_sample))
        
        # If multiple patterns match, likely transliteration
        return matches >= 3


class QualityAssessor:
    """Assess text quality and generate metrics."""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.lang_detector = LanguageDetector(config)
    
    def assess_quality(self, text: str, original_text: str = "") -> TextQualityMetrics:
        """Generate comprehensive quality metrics for text."""
        metrics = TextQualityMetrics()
        
        if not text.strip():
            return metrics
        
        # Basic metrics
        metrics.character_count = len(text)
        metrics.word_count = len(text.split())
        metrics.sentence_count = len(re.findall(r'[.!?]+', text))
        metrics.paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
        
        # Language detection
        if self.config.detect_language:
            lang, confidence = self.lang_detector.detect_language(text)
            metrics.detected_language = lang
            metrics.language_confidence = confidence
        
        # Content quality
        metrics.readability_score = self._calculate_readability(text)
        metrics.content_density = self._calculate_content_density(text)
        metrics.repetition_score = self._calculate_repetition_score(text)
        
        # Domain-specific analysis
        # Always check for Sanskrit verses (even in mixed content)
        metrics.sanskrit_verse_count = self._count_sanskrit_verses(text)
        
        if self.lang_detector.is_sanskrit(text):
            # Additional Sanskrit-specific processing can go here
            pass
        
        if self.lang_detector.is_transliteration(text):
            metrics.transliteration_count = 1
        
        metrics.has_structured_content = self._has_structured_content(text)
        
        # Technical quality
        if original_text:
            metrics.html_artifacts = self._count_html_artifacts(original_text)
            metrics.formatting_artifacts = self._count_formatting_artifacts(text)
        
        metrics.noise_level = self._calculate_noise_level(text)
        
        return metrics
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate basic readability score."""
        if not text.strip():
            return 0.0
        
        # Simple readability based on average sentence/word length
        words = text.split()
        sentences = re.findall(r'[.!?]+', text)
        
        if not sentences:
            return 0.5  # Neutral score for text without clear sentences
        
        avg_words_per_sentence = len(words) / len(sentences)
        avg_chars_per_word = sum(len(word) for word in words) / len(words) if words else 0
        
        # Normalize to 0-1 scale (ideal: 15-20 words/sentence, 4-6 chars/word)
        sentence_score = max(0, min(1, 1 - abs(avg_words_per_sentence - 17.5) / 17.5))
        word_score = max(0, min(1, 1 - abs(avg_chars_per_word - 5) / 5))
        
        return (sentence_score + word_score) / 2
    
    def _calculate_content_density(self, text: str) -> float:
        """Calculate ratio of meaningful content vs. formatting."""
        if not text.strip():
            return 0.0
        
        # Count meaningful characters (letters, numbers, basic punctuation)
        meaningful_chars = len(re.findall(r'[a-zA-Z0-9.!?,:;]', text))
        total_chars = len(text.replace(' ', '').replace('\n', ''))
        
        if total_chars == 0:
            return 0.0
        
        return meaningful_chars / total_chars
    
    def _calculate_repetition_score(self, text: str) -> float:
        """Calculate how repetitive the text is."""
        if not text.strip():
            return 0.0
        
        words = text.lower().split()
        if len(words) < 10:
            return 0.0
        
        # Count unique words vs. total words
        unique_words = len(set(words))
        total_words = len(words)
        
        repetition_ratio = 1 - (unique_words / total_words)
        return repetition_ratio
    
    def _count_sanskrit_verses(self, text: str) -> int:
        """Count Sanskrit verses marked with traditional markers."""
        # Look for verse markers like ॥ number ॥ (with Devanagari or ASCII numerals)
        # Support both ASCII digits and Devanagari numerals
        verse_markers = re.findall(r'॥\s*[\d०-९]+\s*॥', text)
        return len(verse_markers)
    
    def _has_structured_content(self, text: str) -> bool:
        """Check if text has clear structural elements."""
        structure_indicators = [
            r'^Chapter \d+',     # Chapters
            r'^\d+\.\d+',        # Numbered sections
            r'^[A-Z][^.]+:',     # Headers with colons
            r'^\s*•',            # Bullet points
            r'^\s*\d+\.',        # Numbered lists
            r'^Bg\.\s*\d+',      # Bhagavad Gita verse references
            r'^Translation$',    # Translation headers
            r'^Synonyms$',       # Synonyms headers
            r'^Purport$',        # Purport headers
            r'^Commentary$',     # Commentary headers
            r'॥\s*\d+\s*॥',     # Sanskrit verse numbers
        ]
        
        for pattern in structure_indicators:
            if re.search(pattern, text, re.MULTILINE):
                return True
        
        return False
    
    def _count_html_artifacts(self, text: str) -> int:
        """Count HTML artifacts in original text."""
        html_patterns = [
            r'<[^>]+>',       # HTML tags
            r'&[a-zA-Z]+;',   # HTML entities
            r'&#\d+;',        # Numeric entities
        ]
        
        count = 0
        for pattern in html_patterns:
            count += len(re.findall(pattern, text))
        
        return count
    
    def _count_formatting_artifacts(self, text: str) -> int:
        """Count formatting artifacts in processed text."""
        artifacts = [
            r'\s{3,}',        # Excessive spaces
            r'\n{4,}',        # Excessive line breaks
            r'[_*]{3,}',      # Markdown-style formatting
            r'[=]{3,}',       # Separator lines
        ]
        
        count = 0
        for pattern in artifacts:
            count += len(re.findall(pattern, text))
        
        return count
    
    def _calculate_noise_level(self, text: str) -> float:
        """Calculate overall noise level in text."""
        if not text.strip():
            return 1.0
        
        # Various noise indicators
        noise_indicators = [
            len(re.findall(r'[^\w\s.,!?;:\'"()[\]{}\-]', text)),  # Special chars
            len(re.findall(r'\s{3,}', text)),                    # Excessive spaces
            len(re.findall(r'(.)\1{4,}', text)),                 # Repeated chars
            len(re.findall(r'http[s]?://', text)),               # URLs
        ]
        
        total_noise = sum(noise_indicators)
        text_length = len(text)
        
        if text_length == 0:
            return 1.0
        
        # Normalize noise level to 0-1 scale
        # Use a reasonable threshold where 5% noise = 0.5, 10% noise = 1.0
        noise_ratio = total_noise / text_length
        return min(1.0, noise_ratio * 10)


class TextProcessor:
    """Main text processing pipeline."""
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        self.config = config or ProcessingConfig()
        self.html_cleaner = HTMLCleaner(self.config)
        self.normalizer = TextNormalizer(self.config)
        self.quality_assessor = QualityAssessor(self.config)
        
        # Processing statistics
        self.stats = {
            'texts_processed': 0,
            'total_input_chars': 0,
            'total_output_chars': 0,
            'html_cleaned': 0,
            'encoding_fixed': 0,
            'quality_issues': 0
        }
    
    def process_text(self, text: str, content_type: str = "plain") -> Dict[str, Any]:
        """
        Process text through the complete pipeline.
        
        Args:
            text: Raw text to process
            content_type: Type of content ("html", "plain", "markdown")
            
        Returns:
            Dictionary containing processed text and metadata
        """
        if not text.strip():
            return {
                'processed_text': '',
                'original_length': 0,
                'processed_length': 0,
                'quality_metrics': TextQualityMetrics().to_dict(),
                'processing_steps': []
            }
        
        original_text = text
        processing_steps = []
        
        # Update statistics
        self.stats['texts_processed'] += 1
        self.stats['total_input_chars'] += len(text)
        
        # Step 1: HTML cleaning if needed
        if content_type == "html" or self._looks_like_html(text):
            text = self.html_cleaner.clean_html(text)
            processing_steps.append("html_cleaning")
            self.stats['html_cleaned'] += 1
        
        # Step 2: Text normalization
        text = self.normalizer.normalize_text(text)
        processing_steps.append("normalization")
        
        # Step 3: Quality assessment
        quality_metrics = None
        if self.config.include_quality_metrics:
            quality_metrics = self.quality_assessor.assess_quality(text, original_text)
            processing_steps.append("quality_assessment")
        
        # Update output statistics
        self.stats['total_output_chars'] += len(text)
        
        # Quality checks
        if quality_metrics and (
            quality_metrics.noise_level > 0.3 or 
            quality_metrics.content_density < 0.5 or
            len(text) < self.config.min_content_length
        ):
            self.stats['quality_issues'] += 1
        
        return {
            'processed_text': text,
            'original_length': len(original_text),
            'processed_length': len(text),
            'quality_metrics': quality_metrics.to_dict() if quality_metrics else None,
            'processing_steps': processing_steps,
            'compression_ratio': len(text) / len(original_text) if original_text else 0
        }
    
    def _looks_like_html(self, text: str) -> bool:
        """Check if text appears to contain HTML."""
        # Look for HTML tags
        html_indicators = [
            r'<\s*[a-zA-Z][^>]*>',  # Opening tags
            r'<\s*/\s*[a-zA-Z][^>]*>',  # Closing tags
            r'&[a-zA-Z]+;',  # HTML entities
        ]
        
        for pattern in html_indicators:
            if re.search(pattern, text):
                return True
        
        return False
    
    def process_batch(self, texts: List[str], content_types: List[str] = None) -> List[Dict[str, Any]]:
        """Process multiple texts efficiently."""
        if content_types is None:
            content_types = ["plain"] * len(texts)
        
        results = []
        for i, text in enumerate(texts):
            content_type = content_types[i] if i < len(content_types) else "plain"
            result = self.process_text(text, content_type)
            results.append(result)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        total_input = self.stats['total_input_chars']
        total_output = self.stats['total_output_chars']
        
        return {
            **self.stats,
            'average_compression': total_output / total_input if total_input > 0 else 0,
            'quality_issue_rate': self.stats['quality_issues'] / max(1, self.stats['texts_processed']),
            'html_cleaning_rate': self.stats['html_cleaned'] / max(1, self.stats['texts_processed'])
        }


# Convenience functions

def process_single_text(
    text: str, 
    content_type: str = "plain",
    config: Optional[ProcessingConfig] = None
) -> Dict[str, Any]:
    """
    Convenience function to process a single text.
    
    Args:
        text: Text to process
        content_type: Type of content
        config: Processing configuration
        
    Returns:
        Processing result dictionary
    """
    processor = TextProcessor(config)
    return processor.process_text(text, content_type)


def clean_spiritual_text(text: str) -> str:
    """
    Convenience function to clean spiritual text with optimal settings.
    
    Args:
        text: Raw spiritual text
        
    Returns:
        Cleaned text
    """
    config = ProcessingConfig(
        preserve_sanskrit=True,
        preserve_transliteration=True,
        preserve_verse_numbers=True,
        clean_spiritual_formatting=True,
        normalize_unicode=True
    )
    
    processor = TextProcessor(config)
    result = processor.process_text(text, "html")
    return result['processed_text']


# Example usage
if __name__ == "__main__":
    # Simple test to avoid hanging during import
    try:
        # Test with sample spiritual text
        sample_html = """
        <div>
            <h2>Bg. 2.47</h2>
            <p>कर्मण्येवाधिकारस्ते मा फलेषु कदाचन ।<br>
            मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि ॥ ४७ ॥</p>
            
            <h3>Translation</h3>
            <p>You have a right to perform your prescribed duty, but you are not 
            entitled to the fruits of action. Never consider yourself the cause 
            of the results of your activities, and never be attached to not doing 
            your duty.</p>
            
            <h3>Purport</h3>
            <p>There are three considerations here: prescribed duties, capricious 
            work, and inaction...</p>
        </div>
        """
        
        # Process the sample
        result = process_single_text(sample_html, "html")
        
        print("Text processor test successful!")
        print("Original length:", result['original_length'])
        print("Processed length:", result['processed_length'])
        print("Processing steps:", result['processing_steps'])
        
        if result['quality_metrics']:
            metrics = result['quality_metrics']
            print(f"Language: {metrics['detected_language']} ({metrics['language_confidence']:.2f})")
            print(f"Content density: {metrics['content_density']:.2f}")
    
    except Exception as e:
        print(f"Error in text processor test: {e}")
        import traceback
        traceback.print_exc()
