#!/usr/bin/env python3
"""
Test script for the text processing pipeline.

This script tests all components of the text processing system including
HTML cleaning, text normalization, language detection, and quality assessment.
"""

import sys
import os
from pathlib import Path

# Add the processors directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from processors.text_processor import (
    TextProcessor,
    ProcessingConfig,
    HTMLCleaner,
    TextNormalizer,
    LanguageDetector,
    QualityAssessor,
    process_single_text,
    clean_spiritual_text
)


def test_html_cleaning():
    """Test HTML cleaning functionality."""
    print("Testing HTML cleaning...")
    
    config = ProcessingConfig()
    cleaner = HTMLCleaner(config)
    
    # Test with complex HTML
    html_content = """
    <html>
    <head><title>Test</title><script>alert('test');</script></head>
    <body>
        <nav>Navigation menu</nav>
        <div class="content">
            <h1>Chapter 1</h1>
            <p>This is the first paragraph with <strong>bold text</strong>.</p>
            <p>This is the second paragraph with <em>italic text</em>.</p>
            <!-- This is a comment -->
            <ul>
                <li>First item</li>
                <li>Second item</li>
            </ul>
        </div>
        <footer>Copyright notice</footer>
    </body>
    </html>
    """
    
    cleaned = cleaner.clean_html(html_content)
    
    # Check that content is preserved but formatting is cleaned
    if ("Chapter 1" in cleaned and 
        "first paragraph" in cleaned and 
        "bold text" in cleaned and
        "First item" in cleaned and
        "script" not in cleaned and
        "Navigation menu" not in cleaned):
        print("✓ HTML cleaning working correctly")
        return True
    else:
        print("✗ HTML cleaning failed")
        print(f"Cleaned content: {cleaned[:200]}...")
        return False


def test_text_normalization():
    """Test text normalization functionality."""
    print("\nTesting text normalization...")
    
    config = ProcessingConfig()
    normalizer = TextNormalizer(config)
    
    # Test with various problematic text
    problematic_text = """
    "Curly quotes"  and  'single quotes'   with    multiple   spaces.
    Em—dash and en–dash should be normalized.
    Multiple!!!!! exclamation  marks…… and ellipsis….
    \u00a0Non-breaking\u2000spaces\u2003and\u2009other\u202fwhitespace.
    Lines\r\nwith\rdifferent\nline\nbreaks.
    """
    
    normalized = normalizer.normalize_text(problematic_text)
    
    # Check that normalization worked
    if ('"Curly quotes"' in normalized and
        'Em-dash and en-dash' in normalized and
        'Multiple!' in normalized and not 'Multiple!!!!!' in normalized and
        '...' in normalized and
        'Non-breaking spaces' in normalized):
        print("✓ Text normalization working correctly")
        return True
    else:
        print("✗ Text normalization failed")
        print(f"Normalized text: {normalized}")
        return False


def test_language_detection():
    """Test language detection functionality."""
    print("\nTesting language detection...")
    
    config = ProcessingConfig()
    detector = LanguageDetector(config)
    
    # Test with English text
    english_text = "This is a sample English text for language detection testing."
    lang, confidence = detector.detect_language(english_text)
    
    print(f"English text detected as: {lang} (confidence: {confidence:.2f})")
    
    # Test Sanskrit detection
    sanskrit_text = "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन । मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि ॥"
    is_sanskrit = detector.is_sanskrit(sanskrit_text)
    
    # Test transliteration detection
    transliteration_text = "karmaṇy evādhikāras te mā phaleṣu kadācana"
    is_transliteration = detector.is_transliteration(transliteration_text)
    
    if (lang in ['en', 'unknown'] and  # Language detection may vary
        is_sanskrit and 
        is_transliteration):
        print("✓ Language detection working correctly")
        return True
    else:
        print("✗ Language detection failed")
        print(f"Sanskrit detection: {is_sanskrit}")
        print(f"Transliteration detection: {is_transliteration}")
        return False


def test_quality_assessment():
    """Test quality assessment functionality."""
    print("\nTesting quality assessment...")
    
    config = ProcessingConfig()
    assessor = QualityAssessor(config)
    
    # Test with good quality text
    good_text = """
    This is a well-structured text with proper sentences. It contains meaningful content
    with appropriate paragraph breaks and clear structure.
    
    The text has good readability and content density. It demonstrates the kind of
    quality that we expect from processed structured scriptures.
    """
    
    # Test with poor quality text
    poor_text = "txt   w/  lots   of    noise!!! &&& formatting#### issues..."
    
    good_metrics = assessor.assess_quality(good_text)
    poor_metrics = assessor.assess_quality(poor_text)
    
    # Check that quality assessment distinguishes between good and poor text
    if (good_metrics.content_density > poor_metrics.content_density and
        good_metrics.noise_level < poor_metrics.noise_level and
        good_metrics.word_count > 0 and
        good_metrics.sentence_count > 0):
        print("✓ Quality assessment working correctly")
        print(f"Good text - density: {good_metrics.content_density:.2f}, noise: {good_metrics.noise_level:.2f}")
        print(f"Poor text - density: {poor_metrics.content_density:.2f}, noise: {poor_metrics.noise_level:.2f}")
        return True
    else:
        print("✗ Quality assessment failed")
        return False


def test_structured_scripture_processing():
    """Test processing of structured scripture content."""
    print("\nTesting structured scripture processing...")
    
    # Sample Bhagavad Gita verse with HTML
    scripture_html = """
    <div class="verse">
        <h2>Bg. 2.47</h2>
        <div class="sanskrit">
            कर्मण्येवाधिकारस्ते मा फलेषु कदाचन ।<br>
            मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि ॥ ४७ ॥
        </div>
        
        <h3>Synonyms</h3>
        <p>karmaṇi — in prescribed duties; eva — certainly; adhikāraḥ — right; te — of you...</p>
        
        <h3>Translation</h3>
        <p>You have a right to perform your prescribed duty, but you are not entitled 
        to the fruits of action. Never consider yourself the cause of the results of 
        your activities, and never be attached to not doing your duty.</p>
        
        <h3>Purport</h3>
        <p>There are three considerations here: prescribed duties, capricious work, 
        and inaction. Prescribed duties refer to activities performed according to 
        one's position in the material world.</p>
    </div>
    """
    
    # Test with scripture-specific configuration
    result = process_single_text(scripture_html, "html")
    processed_text = result['processed_text']
    metrics = result['quality_metrics']
    
    # Check that scripture content is preserved
    if ("कर्मण्येवाधिकारस्ते" in processed_text and  # Sanskrit preserved
        "karmaṇi" in processed_text and  # Transliteration preserved
        "You have a right" in processed_text and  # Translation preserved
        "Purport" in processed_text and  # Structure preserved
        metrics and metrics['sanskrit_verse_count'] > 0):
        print("✓ Structured scripture processing working correctly")
        print(f"Sanskrit verses detected: {metrics['sanskrit_verse_count']}")
        print(f"Has structured content: {metrics['has_structured_content']}")
        return True
    else:
        print("✗ Structured scripture processing failed")
        print(f"Processed text sample: {processed_text[:200]}...")
        return False


def test_convenience_functions():
    """Test convenience functions."""
    print("\nTesting convenience functions...")
    
    # Test clean_spiritual_text function
    messy_spiritual_text = """
    <html><body>
    <div>
        श्रीभगवानुवाच ॥<br/>
        कर्मण्येवाधिकारस्ते मा फलेषु कदाचन ।<br/>
        Copyright © ISKCON Foundation
    </div>
    </body></html>
    """
    
    cleaned = clean_spiritual_text(messy_spiritual_text)
    
    if ("श्रीभगवानुवाच" in cleaned and 
        "कर्मण्येवाधिकारस्ते" in cleaned and
        "Copyright" not in cleaned and
        "<html>" not in cleaned):
        print("✓ Convenience functions working correctly")
        return True
    else:
        print("✗ Convenience functions failed")
        print(f"Cleaned text: {cleaned}")
        return False


def test_batch_processing():
    """Test batch processing functionality."""
    print("\nTesting batch processing...")
    
    processor = TextProcessor()
    
    texts = [
        "This is the first text for batch processing.",
        "<p>This is <strong>HTML</strong> content.</p>",
        "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन ।",
        "This   has    formatting     issues..."
    ]
    
    content_types = ["plain", "html", "plain", "plain"]
    
    results = processor.process_batch(texts, content_types)
    
    if (len(results) == len(texts) and
        all('processed_text' in result for result in results) and
        all(result['processed_length'] > 0 for result in results if result['original_length'] > 0)):
        print("✓ Batch processing working correctly")
        print(f"Processed {len(results)} texts")
        return True
    else:
        print("✗ Batch processing failed")
        return False


def test_statistics_tracking():
    """Test processing statistics tracking."""
    print("\nTesting statistics tracking...")
    
    processor = TextProcessor()
    
    # Process several texts
    texts = [
        "First test text for statistics.",
        "<p>HTML content for testing.</p>",
        "Another plain text sample."
    ]
    
    for i, text in enumerate(texts):
        content_type = "html" if "<" in text else "plain"
        processor.process_text(text, content_type)
    
    stats = processor.get_statistics()
    
    if (stats['texts_processed'] == len(texts) and
        stats['total_input_chars'] > 0 and
        stats['total_output_chars'] > 0 and
        stats['html_cleaned'] >= 1):  # At least one HTML text
        print("✓ Statistics tracking working correctly")
        print(f"Texts processed: {stats['texts_processed']}")
        print(f"HTML cleaned: {stats['html_cleaned']}")
        print(f"Average compression: {stats['average_compression']:.2f}")
        return True
    else:
        print("✗ Statistics tracking failed")
        print(f"Stats: {stats}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing Lexicon Text Processing Pipeline")
    print("=" * 60)
    
    tests = [
        test_html_cleaning,
        test_text_normalization,
        test_language_detection,
        test_quality_assessment,
        test_structured_scripture_processing,
        test_convenience_functions,
        test_batch_processing,
        test_statistics_tracking
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Text processing pipeline is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
