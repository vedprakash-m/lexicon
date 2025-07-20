import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

class ContentDomain(Enum):
    TECHNICAL = "technical"
    ACADEMIC = "academic"
    BUSINESS = "business"
    LITERATURE = "literature"
    LEGAL = "legal"
    MEDICAL = "medical"
    EDUCATIONAL = "educational"
    WEB = "web"
    RELIGIOUS = "religious"
    PHILOSOPHY = "philosophy"
    UNKNOWN = "unknown"

@dataclass
class CategoryResult:
    domain: ContentDomain
    confidence: float
    indicators: List[str]
    metadata: Dict

class ContentCategorizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Domain-specific keywords and patterns
        self.domain_patterns = {
            ContentDomain.TECHNICAL: {
                'keywords': ['api', 'algorithm', 'database', 'software', 'programming', 'code', 'function', 'class', 'method', 'variable', 'framework', 'library', 'documentation', 'tutorial', 'guide', 'implementation', 'architecture', 'system', 'development', 'engineering'],
                'patterns': [r'\b(def|class|function|import|return|if|else|for|while)\b', r'\b\w+\(\)', r'[A-Z][a-zA-Z]*[A-Z][a-zA-Z]*', r'[a-z_]+\.[a-z_]+'],
                'file_extensions': ['.py', '.js', '.java', '.cpp', '.c', '.h', '.md', '.rst'],
                'structure_indicators': ['code blocks', 'function definitions', 'class definitions', 'import statements']
            },
            ContentDomain.ACADEMIC: {
                'keywords': ['research', 'study', 'analysis', 'methodology', 'hypothesis', 'conclusion', 'abstract', 'introduction', 'literature review', 'results', 'discussion', 'references', 'citation', 'journal', 'paper', 'thesis', 'dissertation', 'university', 'professor', 'scholar'],
                'patterns': [r'\b(et al\.|ibid\.|op\. cit\.)', r'\([12][0-9]{3}\)', r'\b[A-Z][a-z]+ et al\.', r'Figure \d+', r'Table \d+'],
                'structure_indicators': ['abstract', 'references section', 'numbered sections', 'citations', 'figures and tables']
            },
            ContentDomain.BUSINESS: {
                'keywords': ['revenue', 'profit', 'market', 'strategy', 'management', 'finance', 'investment', 'customer', 'sales', 'marketing', 'business', 'company', 'corporate', 'executive', 'board', 'shareholder', 'quarterly', 'annual', 'report', 'analysis'],
                'patterns': [r'\$[\d,]+', r'\b\d+%', r'\bQ[1-4]\b', r'\bFY\d{4}\b', r'\b[A-Z]{2,5}\b'],
                'structure_indicators': ['financial data', 'quarterly reports', 'executive summary', 'market analysis']
            },
            ContentDomain.LITERATURE: {
                'keywords': ['character', 'plot', 'story', 'narrative', 'chapter', 'novel', 'poetry', 'poem', 'verse', 'author', 'protagonist', 'antagonist', 'theme', 'metaphor', 'symbolism', 'fiction', 'non-fiction', 'literary', 'prose'],
                'patterns': [r'Chapter \d+', r'"[^"]*"', r''[^']*'', r'\b(he|she|they) (said|thought|felt|wondered)'],
                'structure_indicators': ['chapters', 'dialogue', 'narrative structure', 'character development']
            },
            ContentDomain.LEGAL: {
                'keywords': ['law', 'legal', 'court', 'judge', 'attorney', 'lawyer', 'case', 'statute', 'regulation', 'contract', 'agreement', 'clause', 'section', 'subsection', 'plaintiff', 'defendant', 'jurisdiction', 'precedent', 'ruling', 'verdict'],
                'patterns': [r'\b\d+\s+U\.S\.C\.\s+§\s+\d+', r'\bv\.\b', r'\b[A-Z][a-z]+ v\. [A-Z][a-z]+', r'§\s*\d+'],
                'structure_indicators': ['legal citations', 'section numbers', 'case references', 'statutory language']
            },
            ContentDomain.MEDICAL: {
                'keywords': ['patient', 'diagnosis', 'treatment', 'symptom', 'disease', 'medicine', 'medical', 'clinical', 'therapy', 'surgery', 'doctor', 'physician', 'hospital', 'health', 'healthcare', 'pharmaceutical', 'drug', 'medication', 'procedure'],
                'patterns': [r'\b[A-Z]{3,}\b', r'\bmg\b', r'\bml\b', r'\bdose\b', r'\bICD-\d+'],
                'structure_indicators': ['medical terminology', 'dosage information', 'clinical procedures', 'diagnostic codes']
            },
            ContentDomain.EDUCATIONAL: {
                'keywords': ['student', 'teacher', 'lesson', 'curriculum', 'education', 'learning', 'school', 'university', 'course', 'assignment', 'homework', 'exam', 'test', 'grade', 'classroom', 'instruction', 'pedagogy', 'textbook'],
                'patterns': [r'Chapter \d+', r'Exercise \d+', r'Question \d+', r'\bGrade \d+'],
                'structure_indicators': ['lesson plans', 'exercises', 'questions and answers', 'educational objectives']
            },
            ContentDomain.WEB: {
                'keywords': ['website', 'blog', 'post', 'comment', 'user', 'online', 'internet', 'web', 'digital', 'social', 'media', 'platform', 'app', 'mobile', 'responsive', 'seo', 'analytics'],
                'patterns': [r'https?://[^\s]+', r'www\.[^\s]+', r'@[a-zA-Z0-9_]+', r'#[a-zA-Z0-9_]+'],
                'structure_indicators': ['urls', 'hyperlinks', 'social media references', 'web terminology']
            },
            ContentDomain.RELIGIOUS: {
                'keywords': ['god', 'lord', 'divine', 'sacred', 'holy', 'prayer', 'worship', 'faith', 'belief', 'scripture', 'bible', 'quran', 'torah', 'verse', 'chapter', 'psalm', 'gospel', 'prophet', 'angel', 'heaven'],
                'patterns': [r'\b\d+:\d+\b', r'Chapter \d+', r'Verse \d+', r'\b[A-Z][a-z]+ \d+:\d+'],
                'structure_indicators': ['verse numbers', 'chapter divisions', 'scriptural references', 'religious terminology']
            },
            ContentDomain.PHILOSOPHY: {
                'keywords': ['philosophy', 'philosophical', 'ethics', 'morality', 'existence', 'reality', 'truth', 'knowledge', 'consciousness', 'being', 'metaphysics', 'epistemology', 'logic', 'reason', 'argument', 'premise', 'conclusion', 'theory'],
                'patterns': [r'\b(therefore|thus|hence|consequently)\b', r'\b(if|then|because|since)\b'],
                'structure_indicators': ['logical arguments', 'philosophical terminology', 'abstract concepts', 'theoretical discussions']
            }
        }
        
    def categorize_content(self, text: str, metadata: Optional[Dict] = None) -> CategoryResult:
        """Categorize content into domain"""
        if not text:
            return CategoryResult(ContentDomain.UNKNOWN, 0.0, [], {})
            
        # Calculate scores for each domain
        domain_scores = {}
        all_indicators = {}
        
        for domain, patterns in self.domain_patterns.items():
            score, indicators = self._calculate_domain_score(text, patterns)
            domain_scores[domain] = score
            all_indicators[domain] = indicators
            
        # Include metadata-based scoring
        if metadata:
            metadata_scores = self._score_from_metadata(metadata)
            for domain, score in metadata_scores.items():
                domain_scores[domain] = domain_scores.get(domain, 0) + score
                
        # Find best match
        if not any(domain_scores.values()):
            return CategoryResult(ContentDomain.UNKNOWN, 0.0, [], {})
            
        best_domain = max(domain_scores, key=domain_scores.get)
        confidence = min(1.0, domain_scores[best_domain] / 10)  # Normalize to 0-1
        
        return CategoryResult(
            domain=best_domain,
            confidence=confidence,
            indicators=all_indicators[best_domain],
            metadata={'scores': domain_scores}
        )
        
    def _calculate_domain_score(self, text: str, patterns: Dict) -> Tuple[float, List[str]]:
        """Calculate score for a specific domain"""
        score = 0.0
        indicators = []
        text_lower = text.lower()
        
        # Keyword matching
        keyword_matches = 0
        for keyword in patterns['keywords']:
            if keyword.lower() in text_lower:
                keyword_matches += 1
                indicators.append(f"keyword: {keyword}")
                
        score += keyword_matches * 0.5
        
        # Pattern matching
        pattern_matches = 0
        for pattern in patterns['patterns']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                pattern_matches += len(matches)
                indicators.append(f"pattern: {pattern}")
                
        score += pattern_matches * 0.3
        
        # Structure indicators
        structure_matches = 0
        for indicator in patterns['structure_indicators']:
            if self._check_structure_indicator(text, indicator):
                structure_matches += 1
                indicators.append(f"structure: {indicator}")
                
        score += structure_matches * 1.0
        
        return score, indicators[:10]  # Limit indicators
        
    def _check_structure_indicator(self, text: str, indicator: str) -> bool:
        """Check for structural indicators in text"""
        text_lower = text.lower()
        
        if indicator == 'code blocks':
            return '```' in text or '    ' in text  # Markdown code blocks or indented code
        elif indicator == 'function definitions':
            return bool(re.search(r'\bdef\s+\w+\s*\(', text))
        elif indicator == 'class definitions':
            return bool(re.search(r'\bclass\s+\w+', text))
        elif indicator == 'import statements':
            return bool(re.search(r'\b(import|from)\s+\w+', text))
        elif indicator == 'abstract':
            return 'abstract' in text_lower and len(text.split()) > 50
        elif indicator == 'references section':
            return bool(re.search(r'\b(references|bibliography)\b', text_lower))
        elif indicator == 'numbered sections':
            return bool(re.search(r'^\d+\.', text, re.MULTILINE))
        elif indicator == 'citations':
            return bool(re.search(r'\([12][0-9]{3}\)', text))
        elif indicator == 'figures and tables':
            return bool(re.search(r'\b(figure|table)\s+\d+', text_lower))
        elif indicator == 'chapters':
            return bool(re.search(r'\bchapter\s+\d+', text_lower))
        elif indicator == 'dialogue':
            return '"' in text and text.count('"') > 4
        elif indicator == 'verse numbers':
            return bool(re.search(r'\b\d+:\d+\b', text))
        elif indicator == 'legal citations':
            return bool(re.search(r'\b\d+\s+U\.S\.C\.\s+§\s+\d+', text))
        elif indicator == 'medical terminology':
            return bool(re.search(r'\b(mg|ml|dose|patient|diagnosis)\b', text_lower))
        elif indicator == 'urls':
            return bool(re.search(r'https?://[^\s]+', text))
        elif indicator == 'logical arguments':
            return bool(re.search(r'\b(therefore|thus|hence|consequently)\b', text_lower))
            
        return False
        
    def _score_from_metadata(self, metadata: Dict) -> Dict[ContentDomain, float]:
        """Score domains based on metadata"""
        scores = {}
        
        # Check file extension
        if 'file_extension' in metadata:
            ext = metadata['file_extension'].lower()
            for domain, patterns in self.domain_patterns.items():
                if ext in patterns.get('file_extensions', []):
                    scores[domain] = scores.get(domain, 0) + 2.0
                    
        # Check title/subject
        title_text = ""
        if 'title' in metadata:
            title_text += metadata['title'].lower()
        if 'subject' in metadata:
            title_text += " " + metadata['subject'].lower()
            
        if title_text:
            for domain, patterns in self.domain_patterns.items():
                for keyword in patterns['keywords']:
                    if keyword.lower() in title_text:
                        scores[domain] = scores.get(domain, 0) + 1.0
                        
        return scores
        
    def get_processing_strategy(self, domain: ContentDomain) -> Dict:
        """Get domain-specific processing strategy"""
        strategies = {
            ContentDomain.TECHNICAL: {
                'preserve_code_blocks': True,
                'preserve_formatting': True,
                'extract_code_snippets': True,
                'chunking_strategy': 'section_based',
                'chunk_size': 1000,
                'overlap': 100
            },
            ContentDomain.ACADEMIC: {
                'preserve_citations': True,
                'extract_references': True,
                'preserve_figures': True,
                'chunking_strategy': 'section_based',
                'chunk_size': 1500,
                'overlap': 150
            },
            ContentDomain.LITERATURE: {
                'preserve_dialogue': True,
                'preserve_paragraphs': True,
                'chunking_strategy': 'chapter_based',
                'chunk_size': 2000,
                'overlap': 200
            },
            ContentDomain.LEGAL: {
                'preserve_sections': True,
                'preserve_citations': True,
                'chunking_strategy': 'section_based',
                'chunk_size': 1200,
                'overlap': 120
            },
            ContentDomain.RELIGIOUS: {
                'preserve_verses': True,
                'preserve_chapters': True,
                'chunking_strategy': 'verse_based',
                'chunk_size': 800,
                'overlap': 80
            }
        }
        
        return strategies.get(domain, {
            'chunking_strategy': 'standard',
            'chunk_size': 1000,
            'overlap': 100
        })