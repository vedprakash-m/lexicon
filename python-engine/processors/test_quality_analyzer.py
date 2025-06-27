"""
Test Suite for Quality Analysis System

This module contains comprehensive tests for the quality analysis system,
including anomaly detection, completeness assessment, and quality reporting.

Test categories:
- Quality threshold configuration
- Anomaly detection algorithms  
- Completeness assessment
- Quality reporting and trends
- Batch analysis functionality
- Edge cases and error handling

Author: Lexicon Development Team
"""

import unittest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Import the modules to test
from processors.quality_analyzer import (
    QualityAnalysisEngine, QualityThresholds, AnomalyDetector,
    CompletenessAssessor, QualityReporter, QualityIssue,
    QualityAnomalyReport, CompletenessMetrics, analyze_text_quality
)
from processors.text_processor import TextQualityMetrics


class TestQualityThresholds(unittest.TestCase):
    """Test quality threshold configuration."""
    
    def setUp(self):
        self.thresholds = QualityThresholds()
    
    def test_default_thresholds(self):
        """Test default threshold values."""
        self.assertEqual(self.thresholds.get_threshold('min_length'), 50)
        self.assertEqual(self.thresholds.get_threshold('max_length'), 10000)
        self.assertEqual(self.thresholds.get_threshold('min_words'), 10)
        self.assertTrue(self.thresholds.get_threshold('anomaly_z_score_threshold') > 0)
    
    def test_threshold_modification(self):
        """Test setting custom thresholds."""
        self.thresholds.set_threshold('min_length', 100)
        self.assertEqual(self.thresholds.get_threshold('min_length'), 100)
        
        self.thresholds.set_threshold('custom_metric', 0.75)
        self.assertEqual(self.thresholds.get_threshold('custom_metric'), 0.75)
    
    def test_unknown_threshold(self):
        """Test handling of unknown threshold names."""
        result = self.thresholds.get_threshold('nonexistent_metric')
        self.assertEqual(result, 0.0)


class TestAnomalyDetector(unittest.TestCase):
    """Test anomaly detection functionality."""
    
    def setUp(self):
        self.thresholds = QualityThresholds()
        self.detector = AnomalyDetector(self.thresholds)
    
    def test_baseline_metrics_addition(self):
        """Test adding baseline metrics for anomaly detection."""
        metrics = TextQualityMetrics()
        metrics.character_count = 500
        metrics.word_count = 100
        metrics.noise_level = 0.1
        
        self.detector.add_baseline_metrics(metrics)
        
        self.assertIn('character_count', self.detector.baseline_metrics)
        self.assertIn('word_count', self.detector.baseline_metrics)
        self.assertIn('noise_level', self.detector.baseline_metrics)
    
    def test_statistical_anomaly_detection(self):
        """Test statistical anomaly detection using z-scores."""
        # Add baseline metrics
        for i in range(5):
            metrics = TextQualityMetrics()
            metrics.character_count = 500 + i * 10  # Normal range: 500-540
            metrics.word_count = 100 + i * 2       # Normal range: 100-108
            self.detector.add_baseline_metrics(metrics)
        
        # Test anomalous metrics
        anomalous_metrics = TextQualityMetrics()
        anomalous_metrics.character_count = 1000  # Way above normal
        anomalous_metrics.word_count = 50         # Way below normal
        
        anomalies = self.detector.detect_anomalies(anomalous_metrics)
        
        # Should detect anomalies in both metrics
        anomaly_types = [a.issue_type for a in anomalies]
        self.assertTrue(any('statistical_anomaly' in t for t in anomaly_types))
    
    def test_absolute_threshold_detection(self):
        """Test anomaly detection against absolute thresholds."""
        # Test text that's too short
        short_metrics = TextQualityMetrics()
        short_metrics.character_count = 10  # Below min_length threshold
        short_metrics.word_count = 2        # Below min_words threshold
        
        anomalies = self.detector.detect_anomalies(short_metrics)
        
        # Should detect length and word count issues
        issue_types = [a.issue_type for a in anomalies]
        self.assertIn('length_issue', issue_types)
        self.assertIn('word_count_issue', issue_types)
    
    def test_noise_level_detection(self):
        """Test detection of high noise levels."""
        noisy_metrics = TextQualityMetrics()
        noisy_metrics.noise_level = 0.5  # High noise level
        
        anomalies = self.detector.detect_anomalies(noisy_metrics)
        
        # Should detect noise issue
        issue_types = [a.issue_type for a in anomalies]
        self.assertIn('noise_issue', issue_types)
    
    def test_encoding_error_detection(self):
        """Test detection of encoding errors."""
        error_metrics = TextQualityMetrics()
        error_metrics.encoding_issues = 5  # High encoding error count
        
        anomalies = self.detector.detect_anomalies(error_metrics)
        
        # Should detect encoding issue
        issue_types = [a.issue_type for a in anomalies]
        self.assertIn('encoding_issue', issue_types)
        
        # Should be marked as critical
        critical_issues = [a for a in anomalies if a.severity == 'critical']
        self.assertTrue(len(critical_issues) > 0)


class TestCompletenessAssessor(unittest.TestCase):
    """Test document completeness assessment."""
    
    def setUp(self):
        self.thresholds = QualityThresholds()
        self.assessor = CompletenessAssessor(self.thresholds)
    
    def test_basic_structure_assessment(self):
        """Test basic document structure assessment."""
        complete_text = """Title: Sample Document
        
        This is the main content of the document. It contains multiple sentences
        and provides detailed information about the topic.
        
        In conclusion, this document demonstrates proper structure."""
        
        metrics = self.assessor.assess_completeness(complete_text)
        
        self.assertTrue(metrics.has_title)
        self.assertTrue(metrics.has_content)
        self.assertTrue(metrics.has_conclusion)
        self.assertGreater(metrics.completeness_score, 0.7)
    
    def test_incomplete_document(self):
        """Test assessment of incomplete document."""
        incomplete_text = "Just a short piece of text without proper structure."
        
        metrics = self.assessor.assess_completeness(incomplete_text)
        
        self.assertFalse(metrics.has_title)
        self.assertTrue(metrics.has_content)
        self.assertFalse(metrics.has_conclusion)
        self.assertLess(metrics.completeness_score, 0.7)
    
    def test_expected_sections_checking(self):
        """Test checking for expected sections."""
        text_with_sections = """
        Introduction
        This is the introduction section.
        
        Methodology
        This explains the methodology used.
        
        Results
        Here are the results obtained.
        """
        
        expected_sections = ['Introduction', 'Methodology', 'Results', 'Conclusion']
        
        metrics = self.assessor.assess_completeness(
            text_with_sections, expected_sections
        )
        
        self.assertEqual(len(metrics.missing_sections), 1)
        self.assertIn('Conclusion', metrics.missing_sections)
        self.assertEqual(metrics.section_count, 3)
    
    def test_spiritual_text_assessment(self):
        """Test spiritual text specific assessment."""
        spiritual_text = """
        Bhagavad Gita 2.47
        
        karmaṇy evādhikāras te mā phaleṣu kadācana
        
        Translation:
        You have a right to perform your prescribed duty, but do not claim 
        entitlement to the fruits of action.
        
        Purport:
        This verse establishes the fundamental principles of karma-yoga.
        """
        
        metrics = self.assessor.assess_completeness(
            spiritual_text, document_type="spiritual"
        )
        
        self.assertTrue(metrics.has_verse_text)
        self.assertTrue(metrics.has_translation)
        self.assertTrue(metrics.has_purport)
        self.assertEqual(metrics.verse_completeness, 1.0)
    
    def test_minimum_requirements_checking(self):
        """Test minimum length and word count requirements."""
        # Test text that meets requirements
        adequate_text = " ".join(["word"] * 50)  # 50 words
        metrics = self.assessor.assess_completeness(adequate_text)
        self.assertTrue(metrics.minimum_words_met)
        
        # Test text that doesn't meet requirements
        short_text = "too short"
        metrics = self.assessor.assess_completeness(short_text)
        self.assertFalse(metrics.minimum_words_met)


class TestQualityReporter(unittest.TestCase):
    """Test quality reporting functionality."""
    
    def setUp(self):
        self.reporter = QualityReporter()
    
    def test_summary_generation(self):
        """Test generation of quality summary."""
        # Create sample metrics
        metrics_list = []
        for i in range(3):
            metrics = TextQualityMetrics()
            metrics.readability_score = 0.8 + i * 0.05
            metrics.noise_level = 0.1 - i * 0.02
            metrics.language_confidence = 0.9
            metrics.encoding_errors = 0.0
            metrics_list.append(metrics)
        
        # Create sample anomaly reports
        anomaly_reports = [
            QualityAnomalyReport(
                document_id="doc1",
                total_issues=2,
                critical_issues=0,
                high_priority_issues=1,
                medium_priority_issues=1,
                low_priority_issues=0,
                overall_score=0.8,
                anomaly_detected=True
            )
        ]
        
        # Create sample completeness metrics
        completeness_metrics = [
            CompletenessMetrics(
                has_title=True,
                has_content=True,
                has_conclusion=True,
                completeness_score=0.9
            )
        ]
        
        report = self.reporter.generate_quality_report(
            metrics_list, anomaly_reports, completeness_metrics
        )
        
        # Verify report structure
        self.assertIn('summary', report)
        self.assertIn('metrics_analysis', report)
        self.assertIn('anomaly_analysis', report)
        self.assertIn('completeness_analysis', report)
        self.assertIn('recommendations', report)
        
        # Verify summary content
        summary = report['summary']
        self.assertEqual(summary['total_documents'], 3)
        self.assertGreater(summary['average_quality_score'], 0.8)
        self.assertEqual(summary['total_anomalies'], 2)
    
    def test_recommendations_generation(self):
        """Test generation of quality recommendations."""
        # Create metrics with issues
        metrics_list = []
        metrics = TextQualityMetrics()
        metrics.readability_score = 0.3  # Low readability
        metrics.noise_level = 0.3        # High noise
        metrics.language_confidence = 0.9
        metrics.encoding_issues = 2      # High encoding issues
        metrics_list.append(metrics)
        
        anomaly_reports = [
            QualityAnomalyReport(
                document_id="doc1",
                total_issues=1,
                critical_issues=1,
                high_priority_issues=0,
                medium_priority_issues=0,
                low_priority_issues=0,
                overall_score=0.5,
                anomaly_detected=True
            )
        ]
        
        completeness_metrics = [
            CompletenessMetrics(
                has_title=False,
                has_content=True,
                has_conclusion=False,
                completeness_score=0.4
            )
        ]
        
        report = self.reporter.generate_quality_report(
            metrics_list, anomaly_reports, completeness_metrics
        )
        
        recommendations = report['recommendations']
        
        # Should recommend improvements for identified issues
        self.assertTrue(any('noise' in rec.lower() for rec in recommendations))
        self.assertTrue(any('readability' in rec.lower() for rec in recommendations))
        self.assertTrue(any('encoding' in rec.lower() for rec in recommendations))
        self.assertTrue(any('critical' in rec.lower() for rec in recommendations))
        self.assertTrue(any('completeness' in rec.lower() for rec in recommendations))
    
    def test_quality_grade_calculation(self):
        """Test quality grade calculation."""
        # Test different score ranges
        self.assertEqual(self.reporter._calculate_quality_grade(0.95), "A")
        self.assertEqual(self.reporter._calculate_quality_grade(0.85), "B")
        self.assertEqual(self.reporter._calculate_quality_grade(0.75), "C")
        self.assertEqual(self.reporter._calculate_quality_grade(0.65), "D")
        self.assertEqual(self.reporter._calculate_quality_grade(0.45), "F")


class TestQualityAnalysisEngine(unittest.TestCase):
    """Test the main quality analysis engine."""
    
    def setUp(self):
        self.engine = QualityAnalysisEngine()
    
    def test_single_document_analysis(self):
        """Test analysis of a single document."""
        sample_text = """
        Sample Document Title
        
        This is a sample document with sufficient content to demonstrate
        the quality analysis functionality. It contains multiple sentences
        and has a reasonable structure.
        
        The document includes various elements that should be analyzed
        for quality metrics, completeness, and potential anomalies.
        
        In conclusion, this document serves as a good test case.
        """
        
        result = self.engine.analyze_document(sample_text, "test_doc")
        
        # Verify result structure
        self.assertIn('document_id', result)
        self.assertIn('quality_metrics', result)
        self.assertIn('anomaly_report', result)
        self.assertIn('completeness_metrics', result)
        self.assertIn('recommendations', result)
        
        # Verify content
        self.assertEqual(result['document_id'], 'test_doc')
        self.assertIsInstance(result['quality_metrics'], dict)
        self.assertIsInstance(result['anomaly_report'], dict)
        self.assertIsInstance(result['completeness_metrics'], dict)
        self.assertIsInstance(result['recommendations'], list)
    
    def test_batch_analysis(self):
        """Test batch analysis of multiple documents."""
        documents = [
            {
                'id': 'doc1',
                'text': 'Short document without much content.',
                'type': 'general'
            },
            {
                'id': 'doc2', 
                'text': """
                Complete Document Title
                
                This is a complete document with proper structure and sufficient
                content to meet quality standards. It demonstrates good writing
                practices and includes all necessary elements.
                
                The content is well-organized and provides valuable information
                to the reader in a clear and coherent manner.
                
                In conclusion, this document exemplifies quality standards.
                """,
                'type': 'general'
            },
            {
                'id': 'doc3',
                'text': """
                Bhagavad Gita 2.20
                
                na jāyate mriyate vā kadācin
                nāyaṁ bhūtvā bhavitā vā na bhūyaḥ
                
                Translation:
                For the soul there is neither birth nor death.
                
                Purport:
                This verse explains the eternal nature of the soul.
                """,
                'type': 'spiritual'
            }
        ]
        
        result = self.engine.analyze_batch(documents)
        
        # Verify batch result structure
        self.assertIn('individual_results', result)
        self.assertIn('batch_report', result)
        self.assertIn('processed_count', result)
        
        # Verify individual results
        individual_results = result['individual_results']
        self.assertEqual(len(individual_results), 3)
        
        # Verify batch report
        batch_report = result['batch_report']
        self.assertIn('summary', batch_report)
        self.assertIn('recommendations', batch_report)
        
        # Verify processing counts
        self.assertEqual(result['processed_count'], 3)
        self.assertEqual(result['failed_count'], 0)
    
    def test_custom_configuration(self):
        """Test engine with custom configuration."""
        custom_config = {
            'thresholds': {
                'min_length': 200,
                'min_words': 50,
                'max_noise_ratio': 0.1
            }
        }
        
        engine = QualityAnalysisEngine(custom_config)
        
        # Verify custom thresholds are applied
        self.assertEqual(engine.thresholds.get_threshold('min_length'), 200)
        self.assertEqual(engine.thresholds.get_threshold('min_words'), 50)
        self.assertEqual(engine.thresholds.get_threshold('max_noise_ratio'), 0.1)
    
    def test_error_handling(self):
        """Test error handling in analysis."""
        # Test with empty text
        result = self.engine.analyze_document("", "empty_doc")
        
        # Should not fail, but may have quality issues
        self.assertIn('document_id', result)
        self.assertEqual(result['document_id'], 'empty_doc')
        
        # Test with very problematic text (None)
        try:
            result = self.engine.analyze_document(None, "none_doc")
            # Should handle gracefully
            self.assertIn('document_id', result)
        except Exception:
            # Acceptable to raise exception for None input
            pass
    
    def test_spiritual_text_analysis(self):
        """Test analysis specifically for spiritual texts."""
        spiritual_text = """
        Bhagavad Gita Chapter 18, Verse 66
        
        sarva-dharmān parityajya mām ekaṁ śaraṇaṁ vraja
        ahaṁ tvāṁ sarva-pāpebhyo mokṣayiṣyāmi mā śucaḥ
        
        Translation:
        Abandon all varieties of religion and just surrender unto Me. 
        I shall deliver you from all sinful reactions. Do not fear.
        
        Purport:
        This is the most confidential part of Vedic wisdom. The Lord 
        instructs to give up all other processes and simply surrender 
        unto Him. This surrender is not passive but active engagement 
        in devotional service.
        """
        
        result = self.engine.analyze_document(
            spiritual_text, "bg_18_66", document_type="spiritual"
        )
        
        # Verify spiritual text specific metrics
        completeness = result['completeness_metrics']
        self.assertGreater(completeness['verse_completeness'], 0.8)
        
        # Should have reasonable quality for complete spiritual text
        self.assertGreater(result['anomaly_report']['overall_score'], 0.6)


class TestConvenienceFunction(unittest.TestCase):
    """Test the convenience function for quick analysis."""
    
    def test_analyze_text_quality(self):
        """Test the convenience function."""
        sample_text = """
        Test Document
        
        This is a test document for the convenience function.
        It has adequate content and structure for testing purposes.
        """
        
        result = analyze_text_quality(sample_text, "test_conv")
        
        # Should return same structure as engine method
        self.assertIn('document_id', result)
        self.assertIn('quality_metrics', result)
        self.assertIn('anomaly_report', result)
        self.assertIn('completeness_metrics', result)
        self.assertEqual(result['document_id'], 'test_conv')
    
    def test_convenience_with_config(self):
        """Test convenience function with custom config."""
        sample_text = "Short text for testing."
        
        config = {
            'thresholds': {
                'min_length': 10,  # Very low threshold for this test
                'min_words': 3
            }
        }
        
        result = analyze_text_quality(sample_text, config=config)
        
        # Should not report length issues with custom thresholds
        issues = result['anomaly_report']['issues']
        length_issues = [i for i in issues if i['type'] == 'length_issue']
        self.assertEqual(len(length_issues), 0)


class TestReportSaving(unittest.TestCase):
    """Test quality report saving functionality."""
    
    def setUp(self):
        self.engine = QualityAnalysisEngine()
        self.temp_dir = tempfile.mkdtemp()
    
    def test_save_report(self):
        """Test saving quality report to file."""
        # Generate a sample report
        documents = [
            {
                'id': 'sample_doc',
                'text': """
                Sample Document for Report Testing
                
                This document is used to test the report saving functionality.
                It contains adequate content and structure to generate meaningful
                quality metrics and analysis results.
                
                The report should be saved successfully to the specified location.
                """,
                'type': 'general'
            }
        ]
        
        result = self.engine.analyze_batch(documents)
        report = result['batch_report']
        
        # Save report
        output_path = Path(self.temp_dir) / "test_quality_report.json"
        self.engine.save_report(report, str(output_path))
        
        # Verify file was created
        self.assertTrue(output_path.exists())
        
        # Verify content can be loaded
        with open(output_path, 'r', encoding='utf-8') as f:
            loaded_report = json.load(f)
        
        self.assertIn('summary', loaded_report)
        self.assertIn('timestamp', loaded_report)


def run_quality_analysis_tests():
    """Run all quality analysis tests."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestQualityThresholds,
        TestAnomalyDetector,
        TestCompletenessAssessor,
        TestQualityReporter,
        TestQualityAnalysisEngine,
        TestConvenienceFunction,
        TestReportSaving
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return success status
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running Quality Analysis System Tests...")
    print("=" * 50)
    
    success = run_quality_analysis_tests()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All quality analysis tests passed!")
    else:
        print("❌ Some quality analysis tests failed!")
    
    print(f"Test run completed at {datetime.now()}")
