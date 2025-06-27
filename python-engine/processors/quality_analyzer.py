"""
Advanced Text Quality Analysis System

This module provides comprehensive quality assessment for text documents and chunks,
building on the basic quality metrics to provide detailed analysis, anomaly detection,
completeness checking, and quality reporting for RAG dataset creation.

Features:
- Multi-dimensional quality scoring
- Anomaly detection algorithms
- Completeness assessment
- Quality trend analysis
- Batch quality reporting
- Quality improvement recommendations

Author: Lexicon Development Team
"""

import re
import logging
import statistics
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import json

# Import our existing quality system
try:
    from .text_processor import TextQualityMetrics, QualityAssessor, ProcessingConfig
except ImportError:
    from text_processor import TextQualityMetrics, QualityAssessor, ProcessingConfig

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class QualityIssue:
    """Represents a quality issue found in text."""
    
    issue_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    location: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class QualityAnomalyReport:
    """Report for detected quality anomalies."""
    
    document_id: str
    total_issues: int
    critical_issues: int
    high_priority_issues: int
    medium_priority_issues: int
    low_priority_issues: int
    overall_score: float
    anomaly_detected: bool
    issues: List[QualityIssue] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CompletenessMetrics:
    """Metrics for document completeness assessment."""
    
    # Structure completeness
    has_title: bool = False
    has_content: bool = False
    has_conclusion: bool = False
    section_count: int = 0
    expected_sections: List[str] = field(default_factory=list)
    missing_sections: List[str] = field(default_factory=list)
    
    # Content completeness
    minimum_length_met: bool = False
    minimum_words_met: bool = False
    content_coherence_score: float = 0.0
    
    # Domain-specific completeness (for spiritual texts)
    has_verse_text: bool = False
    has_translation: bool = False
    has_purport: bool = False
    verse_completeness: float = 0.0
    
    # Overall completeness
    completeness_score: float = 0.0
    completeness_percentage: int = 0


@dataclass
class QualityTrend:
    """Quality trend analysis over time."""
    
    metric_name: str
    values: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)
    trend_direction: str = "stable"  # 'improving', 'declining', 'stable'
    trend_strength: float = 0.0
    average_value: float = 0.0
    variance: float = 0.0


class QualityThresholds:
    """Configurable quality thresholds for different metrics."""
    
    def __init__(self):
        self.thresholds = {
            # Basic text quality
            'min_length': 50,
            'max_length': 10000,
            'min_words': 10,
            'max_words': 2000,
            'min_sentences': 1,
            'max_sentences': 200,
            
            # Content quality
            'min_readability': 0.3,
            'max_noise_ratio': 0.2,
            'min_coherence': 0.5,
            'min_information_density': 0.3,
            
            # Technical quality
            'max_encoding_errors': 0.01,
            'max_formatting_issues': 0.05,
            'min_language_confidence': 0.8,
            
            # Spiritual text specific
            'min_verse_completeness': 0.8,
            'min_sanskrit_accuracy': 0.9,
            
            # Anomaly detection
            'anomaly_z_score_threshold': 2.0,
            'critical_issue_threshold': 5,
            'overall_quality_threshold': 0.7
        }
    
    def get_threshold(self, metric: str) -> float:
        """Get threshold for a specific metric."""
        return self.thresholds.get(metric, 0.0)
    
    def set_threshold(self, metric: str, value: float):
        """Set threshold for a specific metric."""
        self.thresholds[metric] = value


class AnomalyDetector:
    """Detect quality anomalies in text using statistical methods."""
    
    def __init__(self, thresholds: QualityThresholds):
        self.thresholds = thresholds
        self.baseline_metrics: Dict[str, List[float]] = {}
    
    def add_baseline_metrics(self, metrics: TextQualityMetrics):
        """Add metrics to baseline for anomaly detection."""
        metric_dict = metrics.to_dict()
        
        for key, value in metric_dict.items():
            if isinstance(value, (int, float)):
                if key not in self.baseline_metrics:
                    self.baseline_metrics[key] = []
                self.baseline_metrics[key].append(float(value))
    
    def detect_anomalies(self, metrics: TextQualityMetrics) -> List[QualityIssue]:
        """Detect anomalies in quality metrics."""
        issues = []
        metric_dict = metrics.to_dict()
        
        for metric_name, value in metric_dict.items():
            if not isinstance(value, (int, float)):
                continue
            
            # Check against baseline using z-score
            if metric_name in self.baseline_metrics and len(self.baseline_metrics[metric_name]) >= 3:
                baseline_values = self.baseline_metrics[metric_name]
                mean_val = statistics.mean(baseline_values)
                std_val = statistics.stdev(baseline_values) if len(baseline_values) > 1 else 1
                
                if std_val > 0:
                    z_score = abs((value - mean_val) / std_val)
                    threshold = self.thresholds.get_threshold('anomaly_z_score_threshold')
                    
                    if z_score > threshold:
                        severity = 'high' if z_score > threshold * 1.5 else 'medium'
                        issues.append(QualityIssue(
                            issue_type='statistical_anomaly',
                            severity=severity,
                            message=f'{metric_name} value {value:.3f} deviates significantly from baseline (z-score: {z_score:.2f})',
                            confidence=min(z_score / threshold, 1.0)
                        ))
            
            # Check against absolute thresholds
            anomaly_issue = self._check_absolute_thresholds(metric_name, value)
            if anomaly_issue:
                issues.append(anomaly_issue)
        
        return issues
    
    def _check_absolute_thresholds(self, metric_name: str, value: float) -> Optional[QualityIssue]:
        """Check metric against absolute thresholds."""
        # Length checks
        if metric_name == 'character_count':
            min_len = self.thresholds.get_threshold('min_length')
            max_len = self.thresholds.get_threshold('max_length')
            if value < min_len:
                return QualityIssue('length_issue', 'medium', f'Text too short: {value} < {min_len}')
            elif value > max_len:
                return QualityIssue('length_issue', 'low', f'Text very long: {value} > {max_len}')
        
        # Word count checks
        elif metric_name == 'word_count':
            min_words = self.thresholds.get_threshold('min_words')
            max_words = self.thresholds.get_threshold('max_words')
            if value < min_words:
                return QualityIssue('word_count_issue', 'medium', f'Too few words: {value} < {min_words}')
            elif value > max_words:
                return QualityIssue('word_count_issue', 'low', f'Very high word count: {value} > {max_words}')
        
        # Noise ratio checks
        elif metric_name == 'noise_level' and value > self.thresholds.get_threshold('max_noise_ratio'):
            return QualityIssue('noise_issue', 'high', f'High noise level: {value:.2%}')
        
        # Encoding error checks
        elif metric_name == 'encoding_issues' and value > self.thresholds.get_threshold('max_encoding_errors') * 100:
            return QualityIssue('encoding_issue', 'critical', f'Encoding errors detected: {value} issues')
        
        return None


class CompletenessAssessor:
    """Assess document completeness."""
    
    def __init__(self, thresholds: QualityThresholds):
        self.thresholds = thresholds
    
    def assess_completeness(self, text: str, expected_sections: List[str] = None, 
                          document_type: str = "general") -> CompletenessMetrics:
        """Assess document completeness."""
        metrics = CompletenessMetrics()
        
        if expected_sections:
            metrics.expected_sections = expected_sections
        
        # Basic structure assessment
        metrics.has_title = self._has_title(text)
        metrics.has_content = len(text.strip()) > 0
        metrics.has_conclusion = self._has_conclusion(text)
        metrics.section_count = self._count_sections(text)
        
        # Find missing sections
        if expected_sections:
            found_sections = self._find_sections(text, expected_sections)
            metrics.missing_sections = [s for s in expected_sections if s not in found_sections]
        
        # Content completeness
        word_count = len(text.split())
        min_words = self.thresholds.get_threshold('min_words')
        metrics.minimum_words_met = word_count >= min_words
        metrics.minimum_length_met = len(text) >= self.thresholds.get_threshold('min_length')
        metrics.content_coherence_score = self._assess_coherence(text)
        
        # Domain-specific assessment
        if document_type == "spiritual" or "verse" in text.lower():
            metrics = self._assess_spiritual_completeness(text, metrics)
        
        # Calculate overall completeness
        metrics.completeness_score = self._calculate_completeness_score(metrics)
        metrics.completeness_percentage = int(metrics.completeness_score * 100)
        
        return metrics
    
    def _has_title(self, text: str) -> bool:
        """Check if text has a title."""
        lines = text.strip().split('\n')
        if not lines:
            return False
        
        first_line = lines[0].strip()
        # Simple heuristics for title detection
        return (len(first_line) > 0 and 
                len(first_line) < 100 and
                not first_line.endswith('.') and
                first_line[0].isupper())
    
    def _has_conclusion(self, text: str) -> bool:
        """Check if text has a conclusion."""
        conclusion_patterns = [
            r'\bconclusion\b', r'\bin conclusion\b', r'\bfinally\b',
            r'\bto summarize\b', r'\bin summary\b', r'\btherefore\b'
        ]
        
        # Check last few sentences
        sentences = re.split(r'[.!?]+', text)
        last_sentences = ' '.join(sentences[-3:]).lower()
        
        return any(re.search(pattern, last_sentences, re.IGNORECASE) 
                  for pattern in conclusion_patterns)
    
    def _count_sections(self, text: str) -> int:
        """Count sections in text."""
        # Look for headers (lines that start with #, are ALL_CAPS, or are numbered)
        lines = text.split('\n')
        section_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if (line.startswith('#') or  # Markdown headers
                (line.isupper() and len(line) > 5 and len(line) < 50 and 
                 not line.endswith('.') and ' ' in line) or  # ALL CAPS headers (multi-word)
                re.match(r'^\d+\.?\s+[A-Z]', line) or  # Numbered sections
                (len(line) < 50 and line[0].isupper() and 
                 line.count(' ') <= 4 and not line.endswith('.') and 
                 line == line.strip())):  # Short title-like lines
                section_count += 1
        
        return section_count
    
    def _find_sections(self, text: str, expected_sections: List[str]) -> List[str]:
        """Find which expected sections are present."""
        found_sections = []
        text_lower = text.lower()
        
        for section in expected_sections:
            if section.lower() in text_lower:
                found_sections.append(section)
        
        return found_sections
    
    def _assess_coherence(self, text: str) -> float:
        """Assess content coherence (simplified implementation)."""
        sentences = re.split(r'[.!?]+', text)
        if len(sentences) < 2:
            return 1.0
        
        # Simple coherence heuristics
        score = 0.0
        factors = 0
        
        # Check for transition words
        transition_words = ['however', 'therefore', 'furthermore', 'moreover', 'additionally']
        transition_count = sum(1 for word in transition_words if word in text.lower())
        score += min(transition_count / len(sentences), 0.3)
        factors += 1
        
        # Check for repeated key terms
        words = text.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 4:  # Only consider longer words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        repeated_terms = sum(1 for freq in word_freq.values() if freq > 1)
        score += min(repeated_terms / len(sentences), 0.4)
        factors += 1
        
        # Check sentence length variance (coherent text has varied sentence lengths)
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        if len(sentence_lengths) > 1:
            avg_length = statistics.mean(sentence_lengths)
            variance = statistics.variance(sentence_lengths)
            normalized_variance = variance / (avg_length ** 2) if avg_length > 0 else 0
            score += min(normalized_variance, 0.3)
            factors += 1
        
        return score / factors if factors > 0 else 0.5
    
    def _assess_spiritual_completeness(self, text: str, metrics: CompletenessMetrics) -> CompletenessMetrics:
        """Assess completeness specific to spiritual texts."""
        text_lower = text.lower()
        
        # Check for verse components
        metrics.has_verse_text = bool(re.search(r'\d+\.\d+|\bverse\b', text_lower))
        metrics.has_translation = 'translation' in text_lower or 'meaning' in text_lower
        metrics.has_purport = 'purport' in text_lower or 'commentary' in text_lower
        
        # Calculate verse completeness
        components = [metrics.has_verse_text, metrics.has_translation, metrics.has_purport]
        metrics.verse_completeness = sum(components) / len(components)
        
        return metrics
    
    def _calculate_completeness_score(self, metrics: CompletenessMetrics) -> float:
        """Calculate overall completeness score."""
        score = 0.0
        factors = 0
        
        # Basic structure (40% weight)
        structure_score = 0.0
        if metrics.has_title:
            structure_score += 0.3
        if metrics.has_content:
            structure_score += 0.5
        if metrics.has_conclusion:
            structure_score += 0.2
        score += structure_score * 0.4
        factors += 0.4
        
        # Content completeness (30% weight)
        content_score = 0.0
        if metrics.minimum_length_met:
            content_score += 0.3
        if metrics.minimum_words_met:
            content_score += 0.3
        content_score += metrics.content_coherence_score * 0.4
        score += content_score * 0.3
        factors += 0.3
        
        # Section completeness (20% weight)
        if metrics.expected_sections:
            section_score = 1.0 - (len(metrics.missing_sections) / len(metrics.expected_sections))
            score += section_score * 0.2
            factors += 0.2
        
        # Spiritual completeness (10% weight)
        if metrics.verse_completeness > 0:
            score += metrics.verse_completeness * 0.1
            factors += 0.1
        
        return score / factors if factors > 0 else 0.0


class QualityReporter:
    """Generate quality reports and recommendations."""
    
    def __init__(self):
        self.trends: Dict[str, QualityTrend] = {}
    
    def generate_quality_report(self, metrics_list: List[TextQualityMetrics], 
                              anomaly_reports: List[QualityAnomalyReport],
                              completeness_metrics: List[CompletenessMetrics]) -> Dict[str, Any]:
        """Generate comprehensive quality report."""
        report = {
            'summary': self._generate_summary(metrics_list, anomaly_reports, completeness_metrics),
            'metrics_analysis': self._analyze_metrics(metrics_list),
            'anomaly_analysis': self._analyze_anomalies(anomaly_reports),
            'completeness_analysis': self._analyze_completeness(completeness_metrics),
            'recommendations': self._generate_recommendations(metrics_list, anomaly_reports, completeness_metrics),
            'trends': self._analyze_trends(),
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def _generate_summary(self, metrics_list: List[TextQualityMetrics], 
                         anomaly_reports: List[QualityAnomalyReport],
                         completeness_metrics: List[CompletenessMetrics]) -> Dict[str, Any]:
        """Generate summary statistics."""
        if not metrics_list:
            return {'error': 'No metrics provided'}
        
        # Calculate average quality scores
        quality_scores = []
        for metrics in metrics_list:
            # Simple quality score calculation
            score = (
                min(metrics.readability_score, 1.0) * 0.3 +
                (1.0 - min(metrics.noise_level, 1.0)) * 0.3 +
                min(metrics.language_confidence, 1.0) * 0.2 +
                (1.0 - min(metrics.encoding_issues / 100.0, 1.0)) * 0.2  # Normalize encoding issues
            )
            quality_scores.append(score)
        
        total_documents = len(metrics_list)
        total_anomalies = sum(report.total_issues for report in anomaly_reports)
        critical_issues = sum(report.critical_issues for report in anomaly_reports)
        
        avg_completeness = (
            statistics.mean([cm.completeness_score for cm in completeness_metrics])
            if completeness_metrics else 0.0
        )
        
        return {
            'total_documents': total_documents,
            'average_quality_score': statistics.mean(quality_scores),
            'quality_score_std': statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0,
            'total_anomalies': total_anomalies,
            'critical_issues': critical_issues,
            'average_completeness': avg_completeness,
            'documents_with_issues': len([r for r in anomaly_reports if r.total_issues > 0]),
            'quality_grade': self._calculate_quality_grade(statistics.mean(quality_scores))
        }
    
    def _analyze_metrics(self, metrics_list: List[TextQualityMetrics]) -> Dict[str, Any]:
        """Analyze quality metrics distribution."""
        if not metrics_list:
            return {}
        
        # Aggregate metrics
        aggregated = {}
        for metrics in metrics_list:
            metric_dict = metrics.to_dict()
            for key, value in metric_dict.items():
                if isinstance(value, (int, float)):
                    if key not in aggregated:
                        aggregated[key] = []
                    aggregated[key].append(value)
        
        # Calculate statistics for each metric
        analysis = {}
        for metric_name, values in aggregated.items():
            analysis[metric_name] = {
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'std': statistics.stdev(values) if len(values) > 1 else 0,
                'min': min(values),
                'max': max(values),
                'count': len(values)
            }
        
        return analysis
    
    def _analyze_anomalies(self, anomaly_reports: List[QualityAnomalyReport]) -> Dict[str, Any]:
        """Analyze anomaly patterns."""
        if not anomaly_reports:
            return {}
        
        # Count issues by type and severity
        issue_types = {}
        severity_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        
        for report in anomaly_reports:
            for issue in report.issues:
                issue_types[issue.issue_type] = issue_types.get(issue.issue_type, 0) + 1
                severity_counts[issue.severity] += 1
        
        return {
            'total_reports': len(anomaly_reports),
            'reports_with_anomalies': len([r for r in anomaly_reports if r.anomaly_detected]),
            'issue_types': issue_types,
            'severity_distribution': severity_counts,
            'most_common_issues': sorted(issue_types.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def _analyze_completeness(self, completeness_metrics: List[CompletenessMetrics]) -> Dict[str, Any]:
        """Analyze completeness patterns."""
        if not completeness_metrics:
            return {}
        
        scores = [cm.completeness_score for cm in completeness_metrics]
        percentages = [cm.completeness_percentage for cm in completeness_metrics]
        
        # Count missing sections
        all_missing = []
        for cm in completeness_metrics:
            all_missing.extend(cm.missing_sections)
        
        missing_counts = {}
        for section in all_missing:
            missing_counts[section] = missing_counts.get(section, 0) + 1
        
        return {
            'average_completeness': statistics.mean(scores),
            'completeness_std': statistics.stdev(scores) if len(scores) > 1 else 0,
            'average_percentage': statistics.mean(percentages),
            'documents_fully_complete': len([cm for cm in completeness_metrics if cm.completeness_score >= 0.95]),
            'most_missing_sections': sorted(missing_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'structural_completeness': {
                'has_title': sum(1 for cm in completeness_metrics if cm.has_title),
                'has_content': sum(1 for cm in completeness_metrics if cm.has_content),
                'has_conclusion': sum(1 for cm in completeness_metrics if cm.has_conclusion)
            }
        }
    
    def _generate_recommendations(self, metrics_list: List[TextQualityMetrics], 
                                anomaly_reports: List[QualityAnomalyReport],
                                completeness_metrics: List[CompletenessMetrics]) -> List[str]:
        """Generate quality improvement recommendations."""
        recommendations = []
        
        if not metrics_list:
            return ['No data available for recommendations']
        
        # Analyze common issues
        avg_noise = statistics.mean([m.noise_level for m in metrics_list])
        avg_readability = statistics.mean([m.readability_score for m in metrics_list])
        avg_encoding_issues = statistics.mean([m.encoding_issues for m in metrics_list])
        
        # Generate recommendations based on analysis
        if avg_noise > 0.15:
            recommendations.append("Consider improving text cleaning to reduce noise levels")
        
        if avg_readability < 0.5:
            recommendations.append("Focus on improving text readability and coherence")
        
        if avg_encoding_issues > 1:  # More than 1 encoding issue on average
            recommendations.append("Review encoding handling to reduce character encoding errors")
        
        # Anomaly-based recommendations
        critical_issues = sum(report.critical_issues for report in anomaly_reports)
        if critical_issues > 0:
            recommendations.append(f"Address {critical_issues} critical quality issues immediately")
        
        # Completeness recommendations
        if completeness_metrics:
            avg_completeness = statistics.mean([cm.completeness_score for cm in completeness_metrics])
            if avg_completeness < 0.7:
                recommendations.append("Improve document completeness by ensuring all required sections are present")
            
            missing_titles = sum(1 for cm in completeness_metrics if not cm.has_title)
            if missing_titles > len(completeness_metrics) * 0.2:
                recommendations.append("Add proper titles to documents missing them")
        
        if not recommendations:
            recommendations.append("Quality levels are acceptable - continue current practices")
        
        return recommendations
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze quality trends over time."""
        trend_analysis = {}
        
        for metric_name, trend in self.trends.items():
            if len(trend.values) >= 3:
                # Simple trend analysis
                recent_avg = statistics.mean(trend.values[-3:])
                older_avg = statistics.mean(trend.values[:-3]) if len(trend.values) > 3 else recent_avg
                
                trend_direction = "stable"
                if recent_avg > older_avg * 1.05:
                    trend_direction = "improving"
                elif recent_avg < older_avg * 0.95:
                    trend_direction = "declining"
                
                trend_analysis[metric_name] = {
                    'direction': trend_direction,
                    'recent_average': recent_avg,
                    'overall_average': trend.average_value,
                    'variance': trend.variance,
                    'data_points': len(trend.values)
                }
        
        return trend_analysis
    
    def _calculate_quality_grade(self, score: float) -> str:
        """Calculate quality grade from score."""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"


class QualityAnalysisEngine:
    """Main engine for comprehensive quality analysis."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.thresholds = QualityThresholds()
        self.anomaly_detector = AnomalyDetector(self.thresholds)
        self.completeness_assessor = CompletenessAssessor(self.thresholds)
        
        # Create ProcessingConfig for QualityAssessor
        processing_config = ProcessingConfig()
        if 'processing' in self.config:
            # Apply any processing config overrides
            for key, value in self.config['processing'].items():
                if hasattr(processing_config, key):
                    setattr(processing_config, key, value)
        
        self.quality_assessor = QualityAssessor(processing_config)
        self.reporter = QualityReporter()
        
        # Apply custom thresholds from config
        if 'thresholds' in self.config:
            for metric, value in self.config['thresholds'].items():
                self.thresholds.set_threshold(metric, value)
    
    def analyze_document(self, text: str, document_id: str = "", 
                        expected_sections: List[str] = None,
                        document_type: str = "general") -> Dict[str, Any]:
        """Perform comprehensive quality analysis on a single document."""
        try:
            # Basic quality assessment
            quality_metrics = self.quality_assessor.assess_quality(text)
            
            # Anomaly detection
            anomalies = self.anomaly_detector.detect_anomalies(quality_metrics)
            anomaly_report = QualityAnomalyReport(
                document_id=document_id,
                total_issues=len(anomalies),
                critical_issues=len([a for a in anomalies if a.severity == 'critical']),
                high_priority_issues=len([a for a in anomalies if a.severity == 'high']),
                medium_priority_issues=len([a for a in anomalies if a.severity == 'medium']),
                low_priority_issues=len([a for a in anomalies if a.severity == 'low']),
                overall_score=self._calculate_overall_score(quality_metrics, anomalies),
                anomaly_detected=len(anomalies) > 0,
                issues=anomalies
            )
            
            # Completeness assessment
            completeness = self.completeness_assessor.assess_completeness(
                text, expected_sections, document_type
            )
            
            # Add to baseline for future anomaly detection
            self.anomaly_detector.add_baseline_metrics(quality_metrics)
            
            return {
                'document_id': document_id,
                'quality_metrics': quality_metrics.to_dict(),
                'anomaly_report': {
                    'total_issues': anomaly_report.total_issues,
                    'critical_issues': anomaly_report.critical_issues,
                    'overall_score': anomaly_report.overall_score,
                    'anomaly_detected': anomaly_report.anomaly_detected,
                    'issues': [
                        {
                            'type': issue.issue_type,
                            'severity': issue.severity,
                            'message': issue.message,
                            'confidence': issue.confidence
                        }
                        for issue in anomaly_report.issues
                    ]
                },
                'completeness_metrics': {
                    'score': completeness.completeness_score,
                    'percentage': completeness.completeness_percentage,
                    'has_title': completeness.has_title,
                    'has_content': completeness.has_content,
                    'has_conclusion': completeness.has_conclusion,
                    'missing_sections': completeness.missing_sections,
                    'verse_completeness': completeness.verse_completeness
                },
                'recommendations': self._generate_document_recommendations(
                    quality_metrics, anomaly_report, completeness
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing document {document_id}: {e}")
            return {
                'document_id': document_id,
                'error': str(e),
                'analysis_failed': True
            }
    
    def analyze_batch(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a batch of documents and generate comprehensive report."""
        results = []
        metrics_list = []
        anomaly_reports = []
        completeness_metrics = []
        
        for doc in documents:
            doc_id = doc.get('id', f'doc_{len(results)}')
            text = doc.get('text', '')
            expected_sections = doc.get('expected_sections', [])
            doc_type = doc.get('type', 'general')
            
            result = self.analyze_document(text, doc_id, expected_sections, doc_type)
            results.append(result)
            
            if not result.get('analysis_failed'):
                # Extract metrics for batch analysis
                quality_metrics = self.quality_assessor.assess_quality(text)
                metrics_list.append(quality_metrics)
                
                # Reconstruct objects for reporting
                anomaly_report = QualityAnomalyReport(
                    document_id=doc_id,
                    total_issues=result['anomaly_report']['total_issues'],
                    critical_issues=result['anomaly_report']['critical_issues'],
                    high_priority_issues=0,
                    medium_priority_issues=0,
                    low_priority_issues=0,
                    overall_score=result['anomaly_report']['overall_score'],
                    anomaly_detected=result['anomaly_report']['anomaly_detected']
                )
                anomaly_reports.append(anomaly_report)
                
                completeness = CompletenessMetrics()
                completeness.completeness_score = result['completeness_metrics']['score']
                completeness.completeness_percentage = result['completeness_metrics']['percentage']
                completeness.has_title = result['completeness_metrics']['has_title']
                completeness.has_content = result['completeness_metrics']['has_content']
                completeness.has_conclusion = result['completeness_metrics']['has_conclusion']
                completeness.missing_sections = result['completeness_metrics']['missing_sections']
                completeness.verse_completeness = result['completeness_metrics']['verse_completeness']
                completeness_metrics.append(completeness)
        
        # Generate comprehensive report
        quality_report = self.reporter.generate_quality_report(
            metrics_list, anomaly_reports, completeness_metrics
        )
        
        return {
            'individual_results': results,
            'batch_report': quality_report,
            'processed_count': len(results),
            'failed_count': len([r for r in results if r.get('analysis_failed')])
        }
    
    def _calculate_overall_score(self, metrics: TextQualityMetrics, 
                               anomalies: List[QualityIssue]) -> float:
        """Calculate overall quality score considering anomalies."""
        # Start with base quality score
        base_score = (
            min(metrics.readability_score, 1.0) * 0.3 +
            (1.0 - min(metrics.noise_level, 1.0)) * 0.3 +
            min(metrics.language_confidence, 1.0) * 0.2 +
            (1.0 - min(metrics.encoding_issues / 100.0, 1.0)) * 0.2  # Normalize encoding issues
        )
        
        # Apply penalties for anomalies
        penalty = 0.0
        for anomaly in anomalies:
            if anomaly.severity == 'critical':
                penalty += 0.3
            elif anomaly.severity == 'high':
                penalty += 0.2
            elif anomaly.severity == 'medium':
                penalty += 0.1
            elif anomaly.severity == 'low':
                penalty += 0.05
        
        return max(0.0, base_score - penalty)
    
    def _generate_document_recommendations(self, metrics: TextQualityMetrics, 
                                         anomaly_report: QualityAnomalyReport,
                                         completeness: CompletenessMetrics) -> List[str]:
        """Generate recommendations for a specific document."""
        recommendations = []
        
        # Quality-based recommendations
        if metrics.noise_level > 0.2:
            recommendations.append("Clean up formatting and remove excessive whitespace/noise")
        
        if metrics.readability_score < 0.5:
            recommendations.append("Improve text readability and sentence structure")
        
        if metrics.encoding_issues > 1:
            recommendations.append("Fix character encoding issues")
        
        # Anomaly-based recommendations
        if anomaly_report.critical_issues > 0:
            recommendations.append("Address critical quality issues immediately")
        
        if anomaly_report.total_issues > 5:
            recommendations.append("Consider manual review due to multiple quality issues")
        
        # Completeness recommendations
        if not completeness.has_title:
            recommendations.append("Add a descriptive title")
        
        if not completeness.has_conclusion:
            recommendations.append("Consider adding a conclusion or summary")
        
        if completeness.missing_sections:
            recommendations.append(f"Add missing sections: {', '.join(completeness.missing_sections)}")
        
        if completeness.completeness_score < 0.7:
            recommendations.append("Improve document structure and completeness")
        
        if not recommendations:
            recommendations.append("Document quality is acceptable")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], output_path: str):
        """Save quality report to file."""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Quality report saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving quality report: {e}")
            raise


# Convenience function for quick analysis
def analyze_text_quality(text: str, document_id: str = "", config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convenience function for quick text quality analysis."""
    engine = QualityAnalysisEngine(config)
    return engine.analyze_document(text, document_id)


if __name__ == "__main__":
    # Example usage and testing
    sample_text = """
    The Bhagavad Gita: Chapter 2, Verse 47
    
    karmaṇy evādhikāras te mā phaleṣu kadācana
    mā karma-phala-hetur bhūr mā te saṅgo 'stv akarmaṇi
    
    Translation:
    You have a right to perform your prescribed duty, but do not claim 
    entitlement to the fruits of action. Never consider yourself the cause 
    of the results of your activities, and never be attached to not doing your duty.
    
    Purport:
    This verse establishes one of the fundamental principles of karma-yoga - 
    the yoga of action. The Supreme Lord Krishna instructs Arjuna about the 
    proper attitude one should maintain while performing one's duties.
    """
    
    # Analyze the sample text
    result = analyze_text_quality(sample_text, "bg_2_47", {
        'thresholds': {
            'min_length': 100,
            'min_words': 20
        }
    })
    
    print("Quality Analysis Result:")
    print(f"Overall Score: {result['anomaly_report']['overall_score']:.2f}")
    print(f"Completeness: {result['completeness_metrics']['percentage']}%")
    print(f"Issues Found: {result['anomaly_report']['total_issues']}")
    
    if result['recommendations']:
        print("\nRecommendations:")
        for rec in result['recommendations']:
            print(f"- {rec}")
