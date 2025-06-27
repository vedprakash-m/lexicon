#!/usr/bin/env python3

"""
Test script for the Scraping Rules Engine

This script tests all functionality of the rules engine including:
- Rule creation and validation
- Rule loading/saving (JSON and YAML)
- Rule application to HTML content
- Error handling and validation

Author: Lexicon Development Team
"""

import sys
sys.path.append('.')

from scrapers.rules_engine import *
import tempfile
import os


def test_rule_creation():
    """Test creating and validating scraping rules."""
    print("\nTesting rule creation and validation...")
    
    # Test valid rule creation
    try:
        selector_rule = SelectorRule(
            name="test_selector",
            selector=".content",
            description="Test selector for content"
        )
        
        scraping_rule = ScrapingRule(
            name="test_rule",
            description="Test scraping rule", 
            domain_patterns=["example.com"],
            selectors={"content": selector_rule}
        )
        
        print("✓ Valid rule creation successful")
        
    except Exception as e:
        print(f"✗ Valid rule creation failed: {e}")
        return False
    
    # Test invalid rule creation
    try:
        invalid_rule = ScrapingRule(
            name="",  # Invalid empty name
            description="Test",
            domain_patterns=[],  # Invalid empty patterns
            selectors={}  # Invalid empty selectors
        )
        print("✗ Should have failed for invalid rule")
        return False
        
    except ValueError:
        print("✓ Invalid rule correctly rejected")
    
    return True


def test_rule_validation():
    """Test rule validation functionality."""
    print("\nTesting rule validation...")
    
    validator = RuleValidator()
    
    # Create a valid rule
    valid_rule = ScrapingRule(
        name="valid_test",
        description="A valid test rule",
        domain_patterns=["test\\.com"],
        selectors={
            "title": SelectorRule(
                name="title",
                selector="h1.title",
                description="Page title"
            )
        }
    )
    
    # Test valid rule
    is_valid = validator.validate_rule(valid_rule)
    if is_valid:
        print("✓ Valid rule passed validation")
    else:
        print(f"✗ Valid rule failed validation: {validator.get_validation_report()}")
        return False
    
    # Test invalid rule validation
    # Create a rule that will have validation issues
    valid_selector = SelectorRule(
        name="valid_selector",
        selector="div",
        description="A valid selector"
    )
    
    # Create a rule that passes basic construction but has validation issues
    test_rule = ScrapingRule(
        name="test_rule",  # Valid for construction
        description="Test rule",
        domain_patterns=["test.com"],  # Valid for construction  
        selectors={"valid": valid_selector}
    )
    
    # Modify the rule to introduce validation errors
    test_rule.name = ""  # Empty name - validation error
    test_rule.domain_patterns = ["[invalid regex"]  # Invalid regex
    test_rule.description = ""  # Empty description - validation warning
    
    # Test invalid rule
    is_valid = validator.validate_rule(test_rule)
    report = validator.get_validation_report()
    
    if not is_valid and report['errors']:
        print("✓ Invalid rule correctly failed validation")
        print(f"  Errors found: {len(report['errors'])}")
        print(f"  Warnings found: {len(report['warnings'])}")
    else:
        print("✗ Invalid rule should have failed validation")
        return False
    
    return True


def test_rule_serialization():
    """Test saving and loading rules to/from files."""
    print("\nTesting rule serialization...")
    
    engine = RuleEngine()
    
    # Create a test rule
    test_rule = ScrapingRule(
        name="serialization_test",
        description="Test rule for serialization",
        domain_patterns=["test\\.example\\.com"],
        selectors={
            "title": SelectorRule(
                name="title",
                selector="h1",
                transform="clean_whitespace",
                description="Page title"
            ),
            "content": SelectorRule(
                name="content",
                selector=".content p",
                multiple=True,
                required=False,
                fallback_selectors=[".main p", "p"],
                description="Page content paragraphs"
            )
        },
        version="1.0",
        author="Test Author"
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = os.path.join(tmpdir, "test_rule.json")
        yaml_path = os.path.join(tmpdir, "test_rule.yaml")
        
        try:
            # Test JSON serialization
            engine.save_rule_to_json(test_rule, json_path)
            loaded_json_rule = engine.load_rule_from_json(json_path)
            
            if loaded_json_rule.name == test_rule.name and loaded_json_rule.description == test_rule.description:
                print("✓ JSON serialization successful")
            else:
                print("✗ JSON serialization failed - data mismatch")
                return False
            
            # Test YAML serialization  
            engine.save_rule_to_yaml(test_rule, yaml_path)
            loaded_yaml_rule = engine.load_rule_from_yaml(yaml_path)
            
            if loaded_yaml_rule.name == test_rule.name and loaded_yaml_rule.description == test_rule.description:
                print("✓ YAML serialization successful")
            else:
                print("✗ YAML serialization failed - data mismatch")
                return False
            
        except Exception as e:
            print(f"✗ Serialization failed: {e}")
            return False
    
    return True


def test_rule_application():
    """Test applying rules to HTML content."""
    print("\nTesting rule application...")
    
    # Create a test rule for extracting content
    test_rule = ScrapingRule(
        name="html_test",
        description="Test rule for HTML content",
        domain_patterns=[".*"],
        selectors={
            "title": SelectorRule(
                name="title",
                selector="h1",
                description="Page title"
            ),
            "paragraphs": SelectorRule(
                name="paragraphs", 
                selector="p",
                multiple=True,
                description="All paragraphs"
            ),
            "link_url": SelectorRule(
                name="link_url",
                selector="a",
                attribute="href",
                required=False,
                description="First link URL"
            ),
            "missing_element": SelectorRule(
                name="missing_element",
                selector=".nonexistent",
                required=False,
                description="Element that doesn't exist"
            )
        }
    )
    
    # Test HTML content
    test_html = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Main Title</h1>
            <p>First paragraph content.</p>
            <p>Second paragraph content.</p>
            <a href="https://example.com">Test Link</a>
        </body>
    </html>
    """
    
    engine = RuleEngine()
    
    try:
        # Register and apply the rule
        if not engine.register_rule(test_rule):
            print("✗ Failed to register test rule")
            return False
        
        result = engine.apply_rule(test_rule, test_html, "http://test.com")
        
        # Check results
        if not result.success:
            print(f"✗ Rule application failed: {result.errors}")
            return False
        
        expected_data = {
            "title": "Main Title",
            "paragraphs": ["First paragraph content.", "Second paragraph content."],
            "link_url": "https://example.com"
        }
        
        for key, expected_value in expected_data.items():
            if key not in result.extracted_data:
                print(f"✗ Missing expected data: {key}")
                return False
            
            if result.extracted_data[key] != expected_value:
                print(f"✗ Data mismatch for {key}: expected {expected_value}, got {result.extracted_data[key]}")
                return False
        
        print("✓ Rule application successful")
        print(f"  Extracted {len(result.extracted_data)} fields")
        print(f"  Processing time: {result.processing_time:.3f}s")
        
    except Exception as e:
        print(f"✗ Rule application failed: {e}")
        return False
    
    return True


def test_transformations():
    """Test built-in transformation functions."""
    print("\nTesting transformations...")
    
    transformations = RuleTransformations()
    
    # Test cases for transformations
    test_cases = [
        ("clean_whitespace", "  hello   world  ", "hello world"),
        ("to_lowercase", "HELLO WORLD", "hello world"),
        ("to_uppercase", "hello world", "HELLO WORLD"),
        ("strip_html_tags", "<p>Hello <b>world</b></p>", "Hello world"),
        ("extract_numbers", "I have 5 apples and 10 oranges", [5, 10]),
        ("join_with_space", ["hello", "world"], "hello world"),
        ("join_with_newline", ["line1", "line2"], "line1\nline2"),
    ]
    
    for func_name, input_value, expected_output in test_cases:
        try:
            func = getattr(transformations, func_name)
            result = func(input_value)
            
            if result == expected_output:
                print(f"✓ {func_name} transformation successful")
            else:
                print(f"✗ {func_name} transformation failed: expected {expected_output}, got {result}")
                return False
                
        except Exception as e:
            print(f"✗ {func_name} transformation error: {e}")
            return False
    
    return True


def test_rule_matching():
    """Test finding rules that match URLs."""
    print("\nTesting rule matching...")
    
    engine = RuleEngine()
    
    # Create test rules with different domain patterns
    rules = [
        ScrapingRule(
            name="vedabase_bg",
            description="Bhagavad Gita rule",
            domain_patterns=[r"vedabase\.io/en/library/bg"],
            selectors={"title": SelectorRule(name="title", selector="h1")}
        ),
        ScrapingRule(
            name="vedabase_sb", 
            description="Srimad Bhagavatam rule",
            domain_patterns=[r"vedabase\.io/en/library/sb"],
            selectors={"title": SelectorRule(name="title", selector="h1")}
        ),
        ScrapingRule(
            name="general_vedabase",
            description="General Vedabase rule",
            domain_patterns=[r"vedabase\.(io|com)"],
            selectors={"title": SelectorRule(name="title", selector="h1")}
        )
    ]
    
    # Register all rules
    for rule in rules:
        if not engine.register_rule(rule):
            print(f"✗ Failed to register rule: {rule.name}")
            return False
    
    # Test URL matching
    test_cases = [
        ("https://vedabase.io/en/library/bg/2/47", ["vedabase_bg", "general_vedabase"]),
        ("https://vedabase.io/en/library/sb/1/1/1", ["vedabase_sb", "general_vedabase"]),
        ("https://vedabase.com/en/library/cc/adi/1/1", ["general_vedabase"]),
        ("https://example.com", []),
    ]
    
    for url, expected_rule_names in test_cases:
        matching_rules = engine.find_matching_rules(url)
        actual_rule_names = [rule.name for rule in matching_rules]
        
        if set(actual_rule_names) == set(expected_rule_names):
            print(f"✓ URL matching successful for {url}")
        else:
            print(f"✗ URL matching failed for {url}: expected {expected_rule_names}, got {actual_rule_names}")
            return False
    
    return True


def test_vedabase_example():
    """Test with a realistic Vedabase example."""
    print("\nTesting Vedabase example rule...")
    
    # Create Vedabase rule
    vedabase_rule = ScrapingRule(
        name="vedabase_verse",
        description="Extract verse content from Vedabase",
        domain_patterns=[r"vedabase\.(io|com)"],
        selectors={
            "verse_reference": SelectorRule(
                name="verse_reference",
                selector=".r-verse-number, .verse-number",
                fallback_selectors=["h1", ".title"],
                transform="clean_whitespace",
                description="Verse reference (e.g., BG 2.47)"
            ),
            "sanskrit_text": SelectorRule(
                name="sanskrit_text",
                selector=".r-verse-text, .verse-text, .sanskrit",
                fallback_selectors=[".devanagari"],
                transform="clean_whitespace",
                description="Sanskrit verse text"
            ),
            "translation": SelectorRule(
                name="translation", 
                selector=".r-translation, .translation",
                transform="clean_whitespace",
                description="English translation"
            ),
            "synonyms": SelectorRule(
                name="synonyms",
                selector=".r-synonyms, .synonyms",
                required=False,
                transform="clean_whitespace",
                description="Word-for-word synonyms"
            )
        },
        metadata={"content_type": "spiritual_text", "language": "multilingual"}
    )
    
    # Sample HTML (simplified Vedabase structure)
    sample_html = """
    <html>
        <body>
            <div class="verse-container">
                <h1 class="r-verse-number">Bg. 2.47</h1>
                <div class="r-verse-text">
                    कर्मण्येवाधिकारस्ते मा फलेषु कदाचन ।<br>
                    मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि ॥ ४७ ॥
                </div>
                <div class="r-translation">
                    You have a right to perform your prescribed duty, but you are not 
                    entitled to the fruits of action. Never consider yourself the cause 
                    of the results of your activities, and never be attached to not 
                    doing your duty.
                </div>
                <div class="r-synonyms">
                    karmaṇi — in prescribed duties; eva — certainly; adhikāraḥ — right; 
                    te — of you; mā — never; phaleṣu — in the fruits; kadācana — at any time
                </div>
            </div>
        </body>
    </html>
    """
    
    engine = RuleEngine()
    
    try:
        # Register and apply rule
        if not engine.register_rule(vedabase_rule):
            print("✗ Failed to register Vedabase rule")
            return False
        
        result = engine.apply_rule(vedabase_rule, sample_html, "https://vedabase.io/en/library/bg/2/47")
        
        if not result.success:
            print(f"✗ Vedabase rule application failed: {result.errors}")
            return False
        
        # Check that we extracted the expected content
        required_fields = ["verse_reference", "sanskrit_text", "translation"]
        for field in required_fields:
            if field not in result.extracted_data:
                print(f"✗ Missing required field: {field}")
                return False
        
        print("✓ Vedabase example successful")
        print(f"  Verse: {result.extracted_data['verse_reference']}")
        print(f"  Sanskrit: {result.extracted_data['sanskrit_text'][:50]}...")
        print(f"  Translation: {result.extracted_data['translation'][:50]}...")
        
        if "synonyms" in result.extracted_data:
            print(f"  Synonyms: {result.extracted_data['synonyms'][:50]}...")
        
    except Exception as e:
        print(f"✗ Vedabase example failed: {e}")
        return False
    
    return True


def run_all_tests():
    """Run all tests and report results."""
    print("🧪 Testing Lexicon Scraping Rules Engine")
    print("=" * 60)
    
    tests = [
        ("Rule Creation", test_rule_creation),
        ("Rule Validation", test_rule_validation),
        ("Rule Serialization", test_rule_serialization),
        ("Rule Application", test_rule_application),
        ("Transformations", test_transformations),
        ("Rule Matching", test_rule_matching),
        ("Vedabase Example", test_vedabase_example),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Scraping Rules Engine is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
