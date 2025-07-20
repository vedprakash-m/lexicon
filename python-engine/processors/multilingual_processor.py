import chardet
import unicodedata
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

@dataclass
class LanguageDetectionResult:
    language: str
    confidence: float
    script: str
    encoding: str
    is_rtl: bool

class MultilingualProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Script ranges for different writing systems
        self.script_ranges = {
            'Latin': [(0x0000, 0x007F), (0x0080, 0x00FF), (0x0100, 0x017F), (0x0180, 0x024F)],
            'Cyrillic': [(0x0400, 0x04FF), (0x0500, 0x052F), (0x2DE0, 0x2DFF), (0xA640, 0xA69F)],
            'Arabic': [(0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
            'Chinese': [(0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0x20000, 0x2A6DF)],
            'Devanagari': [(0x0900, 0x097F), (0xA8E0, 0xA8FF)],
            'Japanese': [(0x3040, 0x309F), (0x30A0, 0x30FF), (0x31F0, 0x31FF)],
            'Korean': [(0xAC00, 0xD7AF), (0x1100, 0x11FF), (0x3130, 0x318F)],
            'Thai': [(0x0E00, 0x0E7F)],
            'Hebrew': [(0x0590, 0x05FF), (0xFB1D, 0xFB4F)],
        }
        
        # RTL scripts
        self.rtl_scripts = {'Arabic', 'Hebrew'}
        
    def detect_language_and_script(self, text: str) -> LanguageDetectionResult:
        """Detect language, script, and text direction"""
        
        # Detect encoding if text is bytes
        if isinstance(text, bytes):
            encoding_result = chardet.detect(text)
            encoding = encoding_result['encoding'] or 'utf-8'
            text = text.decode(encoding, errors='ignore')
        else:
            encoding = 'utf-8'
            
        # Detect script
        script = self._detect_script(text)
        
        # Simple language detection based on script and common patterns
        language = self._detect_language(text, script)
        
        # Determine if RTL
        is_rtl = script in self.rtl_scripts
        
        # Calculate confidence based on script consistency
        confidence = self._calculate_confidence(text, script)
        
        return LanguageDetectionResult(
            language=language,
            confidence=confidence,
            script=script,
            encoding=encoding,
            is_rtl=is_rtl
        )
        
    def _detect_script(self, text: str) -> str:
        """Detect the primary script used in text"""
        script_counts = {script: 0 for script in self.script_ranges.keys()}
        
        for char in text:
            char_code = ord(char)
            for script, ranges in self.script_ranges.items():
                for start, end in ranges:
                    if start <= char_code <= end:
                        script_counts[script] += 1
                        break
                        
        # Return script with highest count
        if any(script_counts.values()):
            return max(script_counts, key=script_counts.get)
        else:
            return 'Latin'  # Default fallback
            
    def _detect_language(self, text: str, script: str) -> str:
        """Simple language detection based on script and patterns"""
        
        # Common language patterns
        patterns = {
            'English': [r'\b(the|and|or|but|in|on|at|to|for|of|with|by)\b'],
            'Spanish': [r'\b(el|la|los|las|de|en|un|una|con|por|para)\b'],
            'French': [r'\b(le|la|les|de|du|des|un|une|avec|pour|dans)\b'],
            'German': [r'\b(der|die|das|den|dem|des|ein|eine|und|oder|mit)\b'],
            'Russian': [r'\b(и|в|на|с|по|для|от|до|при|за)\b'],
            'Arabic': [r'\b(في|من|إلى|على|عن|مع|هذا|هذه|التي|الذي)\b'],
            'Chinese': [r'[的|了|是|在|有|我|你|他|她|它]'],
            'Japanese': [r'[です|ます|した|する|ある|いる|この|その]'],
        }
        
        # Count pattern matches
        language_scores = {}
        text_lower = text.lower()
        
        for language, lang_patterns in patterns.items():
            score = 0
            for pattern in lang_patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                score += len(matches)
            language_scores[language] = score
            
        # Return language with highest score, or fallback based on script
        if any(language_scores.values()):
            detected_lang = max(language_scores, key=language_scores.get)
            if language_scores[detected_lang] > 0:
                return detected_lang
                
        # Fallback based on script
        script_to_language = {
            'Latin': 'English',
            'Cyrillic': 'Russian',
            'Arabic': 'Arabic',
            'Chinese': 'Chinese',
            'Devanagari': 'Hindi',
            'Japanese': 'Japanese',
            'Korean': 'Korean',
            'Thai': 'Thai',
            'Hebrew': 'Hebrew',
        }
        
        return script_to_language.get(script, 'Unknown')
        
    def _calculate_confidence(self, text: str, script: str) -> float:
        """Calculate confidence in script detection"""
        if not text:
            return 0.0
            
        script_chars = 0
        total_chars = 0
        
        for char in text:
            if char.isalpha():
                total_chars += 1
                char_code = ord(char)
                
                if script in self.script_ranges:
                    for start, end in self.script_ranges[script]:
                        if start <= char_code <= end:
                            script_chars += 1
                            break
                            
        if total_chars == 0:
            return 0.0
            
        return script_chars / total_chars
        
    def normalize_text(self, text: str, language: str, script: str) -> str:
        """Normalize text based on language and script"""
        
        # Unicode normalization
        text = unicodedata.normalize('NFC', text)
        
        # Language-specific normalization
        if language == 'Arabic':
            text = self._normalize_arabic(text)
        elif language == 'Chinese':
            text = self._normalize_chinese(text)
        elif script == 'Devanagari':
            text = self._normalize_devanagari(text)
            
        return text
        
    def _normalize_arabic(self, text: str) -> str:
        """Normalize Arabic text"""
        # Remove diacritics (optional)
        arabic_diacritics = re.compile(r'[\u064B-\u0652\u0670\u0640]')
        # text = arabic_diacritics.sub('', text)  # Uncomment to remove diacritics
        
        # Normalize different forms of letters
        replacements = {
            'ي': 'ي',  # Normalize different forms of yeh
            'ك': 'ك',  # Normalize different forms of kaf
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
            
        return text
        
    def _normalize_chinese(self, text: str) -> str:
        """Normalize Chinese text"""
        # Convert traditional to simplified (basic)
        # This is a simplified approach - full conversion requires comprehensive mapping
        
        # Remove extra whitespace between Chinese characters
        text = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', text)
        
        return text
        
    def _normalize_devanagari(self, text: str) -> str:
        """Normalize Devanagari text"""
        # Normalize different forms of characters
        # This is a basic implementation
        
        return text
        
    def split_by_language(self, text: str) -> List[Tuple[str, LanguageDetectionResult]]:
        """Split mixed-language text into segments"""
        segments = []
        current_segment = ""
        current_script = None
        
        for char in text:
            char_script = self._detect_script(char)
            
            if current_script is None:
                current_script = char_script
                current_segment = char
            elif char_script == current_script or not char.isalpha():
                current_segment += char
            else:
                # Script changed, save current segment
                if current_segment.strip():
                    lang_result = self.detect_language_and_script(current_segment)
                    segments.append((current_segment, lang_result))
                
                # Start new segment
                current_script = char_script
                current_segment = char
                
        # Add final segment
        if current_segment.strip():
            lang_result = self.detect_language_and_script(current_segment)
            segments.append((current_segment, lang_result))
            
        return segments
        
    def get_text_direction_markers(self, text: str, is_rtl: bool) -> str:
        """Add text direction markers for proper display"""
        if is_rtl:
            # Add RTL markers
            return f"\u202E{text}\u202C"  # RLE + text + PDF
        else:
            # Add LTR markers
            return f"\u202D{text}\u202C"  # LRE + text + PDF
            
    def clean_mixed_direction_text(self, text: str) -> str:
        """Clean text with mixed LTR/RTL content"""
        # Remove existing direction markers
        text = re.sub(r'[\u202A-\u202E\u2066-\u2069]', '', text)
        
        # Split into segments and add appropriate markers
        segments = self.split_by_language(text)
        cleaned_segments = []
        
        for segment_text, lang_result in segments:
            if lang_result.is_rtl:
                cleaned_segments.append(self.get_text_direction_markers(segment_text, True))
            else:
                cleaned_segments.append(segment_text)
                
        return ''.join(cleaned_segments)