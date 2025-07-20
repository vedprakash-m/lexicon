import re
import string
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
import statistics

@dataclass
class QualityMetrics:
    completeness_score: float
    readability_score: float
    structure_score: float
    corruption_score: float
    overall_score: float
    issues: List[str]
    recommendations: List[str]

class QualityAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def analyze_content_quality(self, text: str, metadata: Optional[Dict] = None) -> QualityMetrics:
        """Comprehensive quality analysis of extracted content"""
        if not text:
            return QualityMetrics(0.0, 0.0, 0.0, 1.0, 0.0, ["Empty content"], ["Add content to analyze"])
            
        # Run all quality checks
        completeness = self._assess_completeness(text, metadata)
        readability = self._assess_readability(text)
        structure = self._assess_structure(text)
        corruption = self._detect_corruption(text)
        
        # Calculate overall score
        overall = (completeness + readability + structure + (1 - corruption)) / 4
        
        # Collect issues and recommendations
        issues = []
        recommendations = []
        
        if completeness < 0.7:
            issues.append("Content appears incomplete")
            recommendations.append("Check source document for missing sections")
            
        if readability < 0.6:
            issues.append("Poor readability detected")
            recommendations.append("Review text extraction method")
            
        if structure < 0.5:
            issues.append("Poor document structure")
            recommendations.append("Use structure-aware processing")
            
        if corruption > 0.3:
            issues.append("Text corruption detected")
            recommendations.append("Try alternative extraction method or OCR")
            
        return QualityMetrics(
            completeness_score=completeness,
            readability_score=readability,
            structure_score=structure,
            corruption_score=corruption,
            overall_score=overall,
            issues=issues,
            recommendations=recommendations
        )
        
    def _assess_completeness(self, text: str, metadata: Optional[Dict] = None) -> float:
        """Assess if content appears complete"""
        score = 1.0
        
        # Check for minimum content length
        word_count = len(text.split())
        if word_count < 50:
            score -= 0.5
        elif word_count < 200:
            score -= 0.2
            
        # Check for abrupt endings
        if not text.strip().endswith(('.', '!', '?', '"', "'", ')', ']', '}')):
            score -= 0.2
            
        # Check for incomplete sentences
        sentences = re.split(r'[.!?]+', text)
        incomplete_sentences = sum(1 for s in sentences if len(s.strip().split()) < 3)
        if incomplete_sentences > len(sentences) * 0.3:
            score -= 0.3
            
        # Check metadata consistency
        if metadata:
            if 'page_count' in metadata and metadata['page_count'] > 10:
                # For longer documents, expect more content
                expected_words = metadata['page_count'] * 200  # ~200 words per page
                if word_count < expected_words * 0.3:
                    score -= 0.4
                    
        return max(0.0, score)
        
    def _assess_readability(self, text: str) -> float:
        """Assess text readability and coherence"""
        if not text:
            return 0.0
            
        # Basic readability metrics
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
            
        words = text.split()
        
        # Average sentence length
        avg_sentence_length = len(words) / len(sentences)
        sentence_length_score = 1.0
        if avg_sentence_length > 30:
            sentence_length_score -= 0.3
        elif avg_sentence_length < 5:
            sentence_length_score -= 0.4
            
        # Word complexity (average word length)
        avg_word_length = sum(len(word.strip(string.punctuation)) for word in words) / len(words)
        word_complexity_score = 1.0
        if avg_word_length > 8:
            word_complexity_score -= 0.2
        elif avg_word_length < 3:
            word_complexity_score -= 0.3
            
        # Vocabulary diversity (unique words / total words)
        unique_words = set(word.lower().strip(string.punctuation) for word in words)
        diversity_ratio = len(unique_words) / len(words)
        diversity_score = min(1.0, diversity_ratio * 2)  # Scale to 0-1
        
        # Coherence indicators
        coherence_score = self._assess_coherence(text)
        
        # Combine scores
        readability = (sentence_length_score + word_complexity_score + diversity_score + coherence_score) / 4
        return max(0.0, min(1.0, readability))
        
    def _assess_coherence(self, text: str) -> float:
        """Assess text coherence through various indicators"""
        score = 1.0
        
        # Check for transition words
        transition_words = ['however', 'therefore', 'furthermore', 'moreover', 'consequently', 
                          'additionally', 'meanwhile', 'subsequently', 'nevertheless', 'thus']
        transition_count = sum(1 for word in transition_words if word in text.lower())
        
        # Normalize by text length
        words_count = len(text.split())
        transition_ratio = transition_count / max(words_count / 100, 1)  # Per 100 words
        
        if transition_ratio < 0.5:
            score -= 0.2
            
        # Check for repeated phrases (may indicate poor extraction)
        sentences = re.split(r'[.!?]+', text)
        sentence_similarities = 0
        for i, sent1 in enumerate(sentences):
            for sent2 in sentences[i+1:]:
                if len(sent1) > 20 and len(sent2) > 20:
                    # Simple similarity check
                    words1 = set(sent1.lower().split())
                    words2 = set(sent2.lower().split())
                    if len(words1 & words2) / len(words1 | words2) > 0.7:
                        sentence_similarities += 1
                        
        if sentence_similarities > len(sentences) * 0.1:
            score -= 0.3
            
        return max(0.0, score)
        
    def _assess_structure(self, text: str) -> float:
        """Assess document structure quality"""
        score = 0.0
        
        # Check for headings
        heading_patterns = [
            r'^#{1,6}\s+.+$',  # Markdown headings
            r'^\d+\.\s+.+$',   # Numbered sections
            r'^[A-Z][A-Z\s]+$', # ALL CAPS headings
            r'^.{1,50}:$',     # Colon-ended headings
        ]
        
        lines = text.split('\n')
        heading_count = 0
        
        for line in lines:
            line = line.strip()
            if any(re.match(pattern, line, re.MULTILINE) for pattern in heading_patterns):
                heading_count += 1
                
        if heading_count > 0:
            score += 0.3
            
        # Check for paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if len(paragraphs) > 1:
            score += 0.2
            
        # Check for lists
        list_items = len(re.findall(r'^\s*[-*+•]\s+', text, re.MULTILINE))
        numbered_items = len(re.findall(r'^\s*\d+\.\s+', text, re.MULTILINE))
        
        if list_items > 0 or numbered_items > 0:
            score += 0.2
            
        # Check for consistent formatting
        if self._has_consistent_formatting(text):
            score += 0.3
            
        return min(1.0, score)
        
    def _has_consistent_formatting(self, text: str) -> bool:
        """Check for consistent formatting patterns"""
        lines = text.split('\n')
        
        # Check for consistent indentation
        indented_lines = [line for line in lines if line.startswith('    ') or line.startswith('\t')]
        if len(indented_lines) > len(lines) * 0.1:  # At least 10% indented
            return True
            
        # Check for consistent bullet points
        bullet_lines = [line for line in lines if re.match(r'^\s*[-*+•]\s+', line)]
        if len(bullet_lines) > 3:
            return True
            
        return False
        
    def _detect_corruption(self, text: str) -> float:
        """Detect text corruption and extraction artifacts"""
        corruption_score = 0.0
        
        # Check for excessive special characters
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text)
        if special_char_ratio > 0.3:
            corruption_score += 0.4
            
        # Check for repeated characters
        repeated_char_patterns = [
            r'(.)\1{5,}',  # Same character repeated 5+ times
            r'[^\w\s]{3,}',  # 3+ consecutive special characters
        ]
        
        for pattern in repeated_char_patterns:
            if re.search(pattern, text):
                corruption_score += 0.2
                
        # Check for garbled text (high ratio of non-ASCII characters)
        non_ascii_ratio = sum(1 for c in text if ord(c) > 127) / len(text)
        if non_ascii_ratio > 0.2:
            corruption_score += 0.3
            
        # Check for extraction artifacts
        artifacts = [
            r'\b[A-Za-z]{1,2}\b',  # Too many single/double letter words
            r'\d{10,}',  # Very long numbers
            r'[A-Z]{10,}',  # Very long uppercase sequences
        ]
        
        for pattern in artifacts:
            matches = len(re.findall(pattern, text))
            if matches > len(text.split()) * 0.1:
                corruption_score += 0.2
                
        # Check for incomplete words (words ending with hyphens)
        hyphen_words = len(re.findall(r'\w+-\s', text))
        if hyphen_words > len(text.split()) * 0.05:
            corruption_score += 0.1
            
        return min(1.0, corruption_score)
        
    def suggest_improvements(self, metrics: QualityMetrics, extraction_method: str) -> List[str]:
        """Suggest specific improvements based on quality analysis"""
        suggestions = []
        
        if metrics.corruption_score > 0.3:
            if extraction_method == 'pdf':
                suggestions.append("Try OCR extraction for scanned PDF")
                suggestions.append("Use different PDF extraction engine")
            elif extraction_method == 'html':
                suggestions.append("Use custom extraction rules for this website")
                suggestions.append("Check for JavaScript-rendered content")
                
        if metrics.completeness_score < 0.7:
            suggestions.append("Verify source document is complete")
            suggestions.append("Check extraction parameters")
            
        if metrics.readability_score < 0.6:
            suggestions.append("Apply text cleaning and normalization")
            suggestions.append("Use language-specific processing")
            
        if metrics.structure_score < 0.5:
            suggestions.append("Use structure-aware chunking")
            suggestions.append("Preserve document formatting")
            
        return suggestions
        
    def get_quality_report(self, metrics: QualityMetrics) -> str:
        """Generate a human-readable quality report"""
        report = f"""
Content Quality Report
=====================

Overall Score: {metrics.overall_score:.2f}/1.00

Detailed Metrics:
- Completeness: {metrics.completeness_score:.2f}/1.00
- Readability: {metrics.readability_score:.2f}/1.00
- Structure: {metrics.structure_score:.2f}/1.00
- Corruption: {metrics.corruption_score:.2f}/1.00 (lower is better)

Issues Found:
{chr(10).join(f"- {issue}" for issue in metrics.issues)}

Recommendations:
{chr(10).join(f"- {rec}" for rec in metrics.recommendations)}
"""
        return report.strip()