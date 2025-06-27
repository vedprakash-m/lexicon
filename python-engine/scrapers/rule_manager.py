#!/usr/bin/env python3

"""
Rule Management Utility

Command-line utility for managing scraping rules in the Lexicon project.
Provides functionality to validate, test, and manage rule files.

Usage:
    python rule_manager.py validate <rule_file>
    python rule_manager.py test <rule_file> <html_file>
    python rule_manager.py list [rules_directory]
    python rule_manager.py convert <input_file> <output_file>

Author: Lexicon Development Team
"""

import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

sys.path.append('.')
from scrapers.rules_engine import RuleEngine, RuleValidator


def validate_rule_file(rule_path: str) -> bool:
    """Validate a rule file and show results."""
    print(f"🔍 Validating rule file: {rule_path}")
    
    try:
        engine = RuleEngine()
        
        # Load the rule
        if rule_path.endswith('.yaml') or rule_path.endswith('.yml'):
            rule = engine.load_rule_from_yaml(rule_path)
        else:
            rule = engine.load_rule_from_json(rule_path)
        
        print(f"✓ Rule loaded successfully: {rule.name}")
        print(f"  Description: {rule.description}")
        print(f"  Domain patterns: {len(rule.domain_patterns)}")
        print(f"  Selectors: {len(rule.selectors)}")
        
        # Validate the rule
        validator = RuleValidator()
        is_valid = validator.validate_rule(rule)
        report = validator.get_validation_report()
        
        if is_valid:
            print("✅ Rule validation passed!")
        else:
            print("❌ Rule validation failed!")
            
        if report['errors']:
            print(f"\nErrors ({len(report['errors'])}):")
            for error in report['errors']:
                print(f"  ❌ {error}")
        
        if report['warnings']:
            print(f"\nWarnings ({len(report['warnings'])}):")
            for warning in report['warnings']:
                print(f"  ⚠️  {warning}")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Error validating rule: {e}")
        return False


def test_rule_with_html(rule_path: str, html_path: str) -> bool:
    """Test a rule against an HTML file."""
    print(f"🧪 Testing rule {rule_path} with HTML {html_path}")
    
    try:
        engine = RuleEngine()
        
        # Load the rule
        if rule_path.endswith('.yaml') or rule_path.endswith('.yml'):
            rule = engine.load_rule_from_yaml(rule_path)
        else:
            rule = engine.load_rule_from_json(rule_path)
        
        # Load HTML content
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Apply the rule
        result = engine.apply_rule(rule, html_content, "test://example.com")
        
        print(f"Rule: {rule.name}")
        print(f"Success: {result.success}")
        print(f"Processing time: {result.processing_time:.3f}s")
        
        if result.errors:
            print(f"\nErrors ({len(result.errors)}):")
            for error in result.errors:
                print(f"  ❌ {error}")
        
        if result.warnings:
            print(f"\nWarnings ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"  ⚠️  {warning}")
        
        print(f"\nExtracted data ({len(result.extracted_data)} fields):")
        for field, value in result.extracted_data.items():
            if isinstance(value, str) and len(value) > 100:
                preview = value[:100] + "..."
            else:
                preview = str(value)
            print(f"  {field}: {preview}")
        
        print(f"\nExtraction results:")
        for extraction in result.extraction_results:
            status = "✓" if extraction.success else "✗"
            fallback = f" (fallback: {extraction.fallback_used})" if extraction.fallback_used else ""
            print(f"  {status} {extraction.selector_name}: {extraction.element_count} elements{fallback}")
            if extraction.error:
                print(f"    Error: {extraction.error}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Error testing rule: {e}")
        return False


def list_rules(rules_directory: str = "scrapers/rules") -> List[Dict[str, Any]]:
    """List all available rules in a directory."""
    print(f"📋 Listing rules in: {rules_directory}")
    
    rules_path = Path(rules_directory)
    if not rules_path.exists():
        print(f"❌ Rules directory not found: {rules_directory}")
        return []
    
    rules = []
    engine = RuleEngine()
    
    for rule_file in rules_path.glob("*.json"):
        try:
            rule = engine.load_rule_from_json(rule_file)
            rules.append({
                'file': str(rule_file),
                'name': rule.name,
                'description': rule.description,
                'domains': len(rule.domain_patterns),
                'selectors': len(rule.selectors),
                'version': rule.version
            })
        except Exception as e:
            print(f"⚠️  Error loading {rule_file}: {e}")
    
    for rule_file in rules_path.glob("*.yaml"):
        try:
            rule = engine.load_rule_from_yaml(rule_file)
            rules.append({
                'file': str(rule_file),
                'name': rule.name,
                'description': rule.description,
                'domains': len(rule.domain_patterns),
                'selectors': len(rule.selectors),
                'version': rule.version
            })
        except Exception as e:
            print(f"⚠️  Error loading {rule_file}: {e}")
    
    if not rules:
        print("No valid rules found.")
        return []
    
    print(f"\nFound {len(rules)} rules:")
    print("-" * 80)
    for rule in rules:
        print(f"📄 {rule['name']} (v{rule['version']})")
        print(f"   File: {rule['file']}")
        print(f"   Description: {rule['description']}")
        print(f"   Domains: {rule['domains']}, Selectors: {rule['selectors']}")
        print()
    
    return rules


def convert_rule_format(input_path: str, output_path: str) -> bool:
    """Convert a rule between JSON and YAML formats."""
    print(f"🔄 Converting {input_path} to {output_path}")
    
    try:
        engine = RuleEngine()
        
        # Load the rule
        if input_path.endswith('.yaml') or input_path.endswith('.yml'):
            rule = engine.load_rule_from_yaml(input_path)
        else:
            rule = engine.load_rule_from_json(input_path)
        
        # Save in new format
        if output_path.endswith('.yaml') or output_path.endswith('.yml'):
            engine.save_rule_to_yaml(rule, output_path)
        else:
            engine.save_rule_to_json(rule, output_path)
        
        print(f"✅ Successfully converted rule to {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error converting rule: {e}")
        return False


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Lexicon Scraping Rules Management Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python rule_manager.py validate scrapers/rules/vedabase_bhagavad_gita.json
  python rule_manager.py test my_rule.json sample.html
  python rule_manager.py list
  python rule_manager.py convert rule.json rule.yaml
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a rule file')
    validate_parser.add_argument('rule_file', help='Path to rule file')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test a rule with HTML')
    test_parser.add_argument('rule_file', help='Path to rule file')
    test_parser.add_argument('html_file', help='Path to HTML file')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available rules')
    list_parser.add_argument('directory', nargs='?', default='scrapers/rules',
                           help='Rules directory (default: scrapers/rules)')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert rule format')
    convert_parser.add_argument('input_file', help='Input rule file')
    convert_parser.add_argument('output_file', help='Output rule file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == 'validate':
        success = validate_rule_file(args.rule_file)
        sys.exit(0 if success else 1)
    
    elif args.command == 'test':
        success = test_rule_with_html(args.rule_file, args.html_file)
        sys.exit(0 if success else 1)
    
    elif args.command == 'list':
        list_rules(args.directory)
    
    elif args.command == 'convert':
        success = convert_rule_format(args.input_file, args.output_file)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
