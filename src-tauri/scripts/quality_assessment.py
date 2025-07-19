#!/usr/bin/env python3
"""
Quality Assessment Script
ML-based quality assessment for RAG chunks and content
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import math

# Optional ML dependencies
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False


class QualityAssessmentEngine:
    """ML-based quality assessment for chunks and content"""
    
    def __init__(self):
        self.nlp = None
        self.sentence_model = None
        self.tfidf_vectorizer = None
        
        # Initialize models if available
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models if dependencies are available"""
        try:
            if HAS_SPACY:
                self.nlp = spacy.load('en_core_web_sm')
        except OSError:
            self.nlp = None
            
        try:
            if HAS_SENTENCE_TRANSFORMERS:
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception:
            self.sentence_model = None
            
        if HAS_SKLEARN:
            self.tfidf_vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
    
    def assess_chunk_quality(self, chunk_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Assess the quality of a single chunk
        
        Args:
            chunk_text: The text content of the chunk
            context: Additional context information
            
        Returns:
            Quality assessment results
        """
        context = context or {}
        
        assessment = {
            "overall_score": 0.0,
            "metrics": {
                "readability": self._assess_readability(chunk_text),
                "coherence": self._assess_coherence(chunk_text),
                "informativeness": self._assess_informativeness(chunk_text),
                "completeness": self._assess_completeness(chunk_text),
                "linguistic_quality": self._assess_linguistic_quality(chunk_text)
            },
            "suggestions": [],
            "issues": []
        }
        
        # Calculate overall score
        metrics = assessment["metrics"]
        weights = {
            "readability": 0.2,
            "coherence": 0.25,
            "informativeness": 0.25,
            "completeness": 0.15,
            "linguistic_quality": 0.15
        }
        
        overall_score = sum(metrics[metric] * weights[metric] for metric in weights)
        assessment["overall_score"] = round(overall_score, 3)
        
        # Add suggestions based on scores
        self._generate_suggestions(assessment)
        
        return assessment
    
    def _assess_readability(self, text: str) -> float:
        """Assess text readability using multiple metrics"""
        if not text.strip():
            return 0.0
        
        # Basic readability metrics
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        words = text.split()
        if not words:
            return 0.0
        
        # Average sentence length
        avg_sentence_length = len(words) / len(sentences)
        sentence_score = max(0, min(1, 1 - (avg_sentence_length - 15) / 20))
        
        # Syllable complexity (simplified)
        syllable_count = sum(self._count_syllables(word) for word in words)
        avg_syllables = syllable_count / len(words)
        syllable_score = max(0, min(1, 1 - (avg_syllables - 1.5) / 2))
        
        # Word complexity
        complex_words = sum(1 for word in words if len(word) > 6)
        complexity_ratio = complex_words / len(words)
        complexity_score = max(0, min(1, 1 - complexity_ratio))
        
        return round((sentence_score + syllable_score + complexity_score) / 3, 3)
    
    def _assess_coherence(self, text: str) -> float:
        """Assess text coherence and flow"""
        if not text.strip():
            return 0.0
        
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 2:
            return 0.8  # Single sentence can be coherent
        
        # Coherence indicators
        coherence_score = 0.5  # Base score
        
        # Transition words and phrases
        transitions = [
            'however', 'therefore', 'furthermore', 'moreover', 'additionally',
            'consequently', 'meanwhile', 'subsequently', 'nevertheless', 'thus',
            'for example', 'in addition', 'on the other hand', 'as a result'
        ]
        
        transition_count = sum(1 for word in transitions if word in text.lower())
        transition_score = min(0.3, transition_count * 0.1)
        coherence_score += transition_score
        
        # Pronoun references (basic check)
        pronouns = ['it', 'they', 'this', 'that', 'these', 'those']
        pronoun_count = sum(1 for word in text.lower().split() if word in pronouns)
        if pronoun_count > 0:
            coherence_score += min(0.2, pronoun_count * 0.05)
        
        return round(min(1.0, coherence_score), 3)
    
    def _assess_informativeness(self, text: str) -> float:
        """Assess how informative the text is"""
        if not text.strip():
            return 0.0
        
        words = text.lower().split()
        if not words:
            return 0.0
        
        # Stop words ratio
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
        
        content_words = [word for word in words if word not in stop_words]
        if not words:
            return 0.0
        
        content_ratio = len(content_words) / len(words)
        
        # Named entities and numbers (indicators of factual content)
        entities = re.findall(r'\b[A-Z][a-z]+\b', text)
        numbers = re.findall(r'\b\d+\b', text)
        
        entity_score = min(0.3, len(entities) * 0.05)
        number_score = min(0.2, len(numbers) * 0.1)
        
        informativeness = content_ratio * 0.5 + entity_score + number_score
        return round(min(1.0, informativeness), 3)
    
    def _assess_completeness(self, text: str) -> float:
        """Assess if the chunk appears complete"""
        if not text.strip():
            return 0.0
        
        completeness_score = 0.5  # Base score
        
        # Sentence completeness
        sentences = re.split(r'[.!?]+', text)
        complete_sentences = [s for s in sentences if s.strip() and not s.strip().endswith(('...', ',', ';'))]
        
        if sentences:
            sentence_completeness = len(complete_sentences) / len(sentences)
            completeness_score += sentence_completeness * 0.3
        
        # Starts and ends properly
        text_stripped = text.strip()
        if text_stripped and text_stripped[0].isupper():
            completeness_score += 0.1
        
        if text_stripped and text_stripped[-1] in '.!?':
            completeness_score += 0.1
        
        return round(min(1.0, completeness_score), 3)
    
    def _assess_linguistic_quality(self, text: str) -> float:
        """Assess linguistic quality using available NLP tools"""
        if not text.strip():
            return 0.0
        
        quality_score = 0.7  # Base score for basic text
        
        if self.nlp:
            try:
                doc = self.nlp(text)
                
                # Grammar and syntax quality (simplified)
                tokens = [token for token in doc if not token.is_space]
                if tokens:
                    # Check for proper sentence structure
                    has_verbs = any(token.pos_ == 'VERB' for token in tokens)
                    has_nouns = any(token.pos_ in ['NOUN', 'PROPN'] for token in tokens)
                    
                    if has_verbs and has_nouns:
                        quality_score += 0.2
                    
                    # Check for balanced word types
                    pos_counts = {}
                    for token in tokens:
                        pos_counts[token.pos_] = pos_counts.get(token.pos_, 0) + 1
                    
                    if len(pos_counts) >= 3:  # Good variety of word types
                        quality_score += 0.1
            except Exception:
                pass
        
        return round(min(1.0, quality_score), 3)
    
    def _count_syllables(self, word: str) -> int:
        """Simple syllable counting heuristic"""
        word = word.lower()
        syllables = 0
        vowels = "aeiouy"
        
        if word[0] in vowels:
            syllables += 1
        
        for i in range(1, len(word)):
            if word[i] in vowels and word[i-1] not in vowels:
                syllables += 1
        
        if word.endswith("e"):
            syllables -= 1
        
        return max(1, syllables)
    
    def _generate_suggestions(self, assessment: Dict[str, Any]):
        """Generate improvement suggestions based on assessment"""
        metrics = assessment["metrics"]
        suggestions = assessment["suggestions"]
        issues = assessment["issues"]
        
        if metrics["readability"] < 0.6:
            suggestions.append("Consider breaking down complex sentences for better readability")
            issues.append("Low readability score")
        
        if metrics["coherence"] < 0.6:
            suggestions.append("Add transition words or phrases to improve flow")
            issues.append("Poor text coherence")
        
        if metrics["informativeness"] < 0.5:
            suggestions.append("Include more specific details or factual information")
            issues.append("Low information density")
        
        if metrics["completeness"] < 0.6:
            suggestions.append("Ensure sentences are complete and well-formed")
            issues.append("Incomplete content structure")
        
        if metrics["linguistic_quality"] < 0.6:
            suggestions.append("Review grammar and sentence structure")
            issues.append("Linguistic quality concerns")
    
    def assess_chunk_relationships(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Assess relationships between chunks"""
        if not chunks or len(chunks) < 2:
            return []
        
        relationships = []
        
        for i, chunk1 in enumerate(chunks):
            for j, chunk2 in enumerate(chunks[i+1:], i+1):
                relationship = self._assess_chunk_pair(chunk1, chunk2)
                if relationship["strength"] > 0.3:  # Only include significant relationships
                    relationship["source_id"] = chunk1.get("id", str(i))
                    relationship["target_id"] = chunk2.get("id", str(j))
                    relationships.append(relationship)
        
        return relationships
    
    def _assess_chunk_pair(self, chunk1: Dict[str, Any], chunk2: Dict[str, Any]) -> Dict[str, Any]:
        """Assess relationship between two chunks"""
        text1 = chunk1.get("text", "")
        text2 = chunk2.get("text", "")
        
        relationship = {
            "type": "semantic",
            "strength": 0.0,
            "description": ""
        }
        
        if not text1 or not text2:
            return relationship
        
        # Lexical similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if words1 and words2:
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            jaccard_similarity = len(intersection) / len(union)
            relationship["strength"] = jaccard_similarity
        
        # Enhanced similarity with ML models if available
        if self.sentence_model and HAS_SENTENCE_TRANSFORMERS:
            try:
                embeddings1 = self.sentence_model.encode([text1])
                embeddings2 = self.sentence_model.encode([text2])
                semantic_similarity = cosine_similarity(embeddings1, embeddings2)[0][0]
                
                # Combine lexical and semantic similarity
                relationship["strength"] = (relationship["strength"] + semantic_similarity) / 2
            except Exception:
                pass
        
        # Determine relationship type and description
        if relationship["strength"] > 0.7:
            relationship["description"] = "Strong semantic similarity"
        elif relationship["strength"] > 0.5:
            relationship["description"] = "Moderate semantic similarity"
        elif relationship["strength"] > 0.3:
            relationship["description"] = "Weak semantic similarity"
        
        return relationship


def main():
    """Main quality assessment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Assess quality of text chunks")
    parser.add_argument("--text", help="Text to assess")
    parser.add_argument("--chunks", help="JSON string of chunks to assess")
    parser.add_argument("--assess-relationships", action="store_true", help="Assess chunk relationships")
    
    args = parser.parse_args()
    
    try:
        engine = QualityAssessmentEngine()
        
        if args.chunks:
            chunks_data = json.loads(args.chunks)
            
            if args.assess_relationships:
                relationships = engine.assess_chunk_relationships(chunks_data)
                result = {"relationships": relationships}
            else:
                assessments = []
                for chunk in chunks_data:
                    chunk_text = chunk.get("text", "")
                    assessment = engine.assess_chunk_quality(chunk_text)
                    assessment["chunk_id"] = chunk.get("id", "")
                    assessments.append(assessment)
                result = {"assessments": assessments}
        
        elif args.text:
            result = engine.assess_chunk_quality(args.text)
        
        else:
            result = {"error": "No text or chunks provided"}
        
        print(json.dumps(result, indent=2))
    
    except Exception as e:
        print(json.dumps({
            "error": f"Quality assessment failed: {str(e)}"
        }, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
