"""
Scraping Rules Engine

This module provides a flexible rule-based system for defining and applying
custom scraping rules. It allows users to create, validate, and share scraping
configurations for different websites and content types.

Features:
- JSON-based rule definition format
- Rule validation and error checking
- Dynamic rule application
- Custom selector support
- Rule composition and inheritance
- Import/export functionality

Author: Lexicon Development Team
"""

import json
import re
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field, asdict
from pathlib import Path
from bs4 import BeautifulSoup, Tag
import yaml

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class SelectorRule:
    """Defines a CSS/XPath selector rule for extracting content."""
    
    name: str
    selector: str
    selector_type: str = "css"  # "css" or "xpath"
    attribute: Optional[str] = None  # Extract attribute instead of text
    multiple: bool = False  # Extract multiple elements
    required: bool = True
    transform: Optional[str] = None  # Transformation function name
    fallback_selectors: List[str] = field(default_factory=list)
    description: str = ""
    
    def __post_init__(self):
        """Validate selector rule after initialization."""
        if self.selector_type not in ["css", "xpath"]:
            raise ValueError(f"Invalid selector_type: {self.selector_type}")
        
        if not self.selector.strip():
            raise ValueError("Selector cannot be empty")


@dataclass
class ScrapingRule:
    """Complete scraping rule for a specific content type or website."""
    
    name: str
    description: str
    domain_patterns: List[str]  # URL patterns this rule applies to
    selectors: Dict[str, SelectorRule]
    preprocessing: List[str] = field(default_factory=list)  # Preprocessing steps
    postprocessing: List[str] = field(default_factory=list)  # Postprocessing steps
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0"
    author: str = ""
    created_date: str = ""
    
    def __post_init__(self):
        """Validate scraping rule after initialization."""
        if not self.name.strip():
            raise ValueError("Rule name cannot be empty")
        
        if not self.domain_patterns:
            raise ValueError("At least one domain pattern must be specified")
        
        if not self.selectors:
            raise ValueError("At least one selector must be defined")


@dataclass
class ExtractionResult:
    """Result of applying a selector rule."""
    
    selector_name: str
    success: bool
    value: Any = None
    error: Optional[str] = None
    fallback_used: Optional[str] = None
    element_count: int = 0


@dataclass
class ScrapingResult:
    """Complete result of applying a scraping rule."""
    
    rule_name: str
    url: str
    success: bool
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    extraction_results: List[ExtractionResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class RuleTransformations:
    """Built-in transformation functions for extracted content."""
    
    @staticmethod
    def clean_whitespace(text: str) -> str:
        """Clean and normalize whitespace."""
        if not isinstance(text, str):
            return text
        return ' '.join(text.split())
    
    @staticmethod
    def extract_numbers(text: str) -> List[int]:
        """Extract all numbers from text."""
        if not isinstance(text, str):
            return []
        return [int(match) for match in re.findall(r'\d+', text)]
    
    @staticmethod
    def to_lowercase(text: str) -> str:
        """Convert text to lowercase."""
        if not isinstance(text, str):
            return text
        return text.lower()
    
    @staticmethod
    def to_uppercase(text: str) -> str:
        """Convert text to uppercase."""
        if not isinstance(text, str):
            return text
        return text.upper()
    
    @staticmethod
    def strip_html_tags(text: str) -> str:
        """Remove HTML tags from text."""
        if not isinstance(text, str):
            return text
        return re.sub(r'<[^>]+>', '', text)
    
    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract URLs from text."""
        if not isinstance(text, str):
            return []
        url_pattern = r'https?://[^\s<>"{}|\\^`[\]]+'
        return re.findall(url_pattern, text)
    
    @staticmethod
    def join_with_space(items: List[str]) -> str:
        """Join list items with spaces."""
        if not isinstance(items, list):
            return str(items)
        return ' '.join(str(item) for item in items)
    
    @staticmethod
    def join_with_newline(items: List[str]) -> str:
        """Join list items with newlines."""
        if not isinstance(items, list):
            return str(items)
        return '\n'.join(str(item) for item in items)


class RuleValidator:
    """Validates scraping rules for correctness and completeness."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_rule(self, rule: ScrapingRule) -> bool:
        """Validate a complete scraping rule."""
        self.errors.clear()
        self.warnings.clear()
        
        self._validate_basic_fields(rule)
        self._validate_domain_patterns(rule)
        self._validate_selectors(rule)
        self._validate_transformations(rule)
        
        return len(self.errors) == 0
    
    def _validate_basic_fields(self, rule: ScrapingRule):
        """Validate basic rule fields."""
        if not rule.name or not rule.name.strip():
            self.errors.append("Rule name is required")
        
        if not rule.description or not rule.description.strip():
            self.warnings.append("Rule description is recommended")
        
        if not rule.version or not rule.version.strip():
            self.warnings.append("Rule version is recommended")
    
    def _validate_domain_patterns(self, rule: ScrapingRule):
        """Validate domain patterns."""
        if not rule.domain_patterns:
            self.errors.append("At least one domain pattern is required")
        
        for pattern in rule.domain_patterns:
            if not pattern or not pattern.strip():
                self.errors.append("Empty domain pattern found")
            
            # Check if pattern is a valid regex
            try:
                re.compile(pattern)
            except re.error as e:
                self.errors.append(f"Invalid regex pattern '{pattern}': {e}")
    
    def _validate_selectors(self, rule: ScrapingRule):
        """Validate selector rules."""
        if not rule.selectors:
            self.errors.append("At least one selector is required")
        
        for name, selector_rule in rule.selectors.items():
            if not name or not name.strip():
                self.errors.append("Selector name cannot be empty")
            
            if not selector_rule.selector or not selector_rule.selector.strip():
                self.errors.append(f"Selector '{name}' cannot be empty")
            
            # Validate CSS selector syntax (basic check)
            if selector_rule.selector_type == "css":
                self._validate_css_selector(name, selector_rule.selector)
    
    def _validate_css_selector(self, name: str, selector: str):
        """Basic validation of CSS selector syntax."""
        # Check for obviously invalid selectors
        invalid_chars = ['<', '>', '{', '}']
        for char in invalid_chars:
            if char in selector:
                self.errors.append(f"Invalid character '{char}' in CSS selector '{name}'")
    
    def _validate_transformations(self, rule: ScrapingRule):
        """Validate transformation function references."""
        available_transformations = set(dir(RuleTransformations))
        
        for name, selector_rule in rule.selectors.items():
            if selector_rule.transform:
                if not hasattr(RuleTransformations, selector_rule.transform):
                    self.errors.append(f"Unknown transformation '{selector_rule.transform}' in selector '{name}'")
    
    def get_validation_report(self) -> Dict[str, List[str]]:
        """Get validation errors and warnings."""
        return {
            'errors': self.errors.copy(),
            'warnings': self.warnings.copy()
        }


class RuleEngine:
    """Main rule engine for applying scraping rules to web content."""
    
    def __init__(self):
        self.rules: Dict[str, ScrapingRule] = {}
        self.transformations = RuleTransformations()
        self.validator = RuleValidator()
    
    def load_rule_from_dict(self, rule_data: Dict[str, Any]) -> ScrapingRule:
        """Load a scraping rule from a dictionary."""
        # Convert selector dictionaries to SelectorRule objects
        selectors = {}
        for name, selector_data in rule_data.get('selectors', {}).items():
            selectors[name] = SelectorRule(**selector_data)
        
        # Create the main rule
        rule_data['selectors'] = selectors
        return ScrapingRule(**rule_data)
    
    def load_rule_from_json(self, json_path: Union[str, Path]) -> ScrapingRule:
        """Load a scraping rule from a JSON file."""
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"Rule file not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            rule_data = json.load(f)
        
        return self.load_rule_from_dict(rule_data)
    
    def load_rule_from_yaml(self, yaml_path: Union[str, Path]) -> ScrapingRule:
        """Load a scraping rule from a YAML file."""
        path = Path(yaml_path)
        if not path.exists():
            raise FileNotFoundError(f"Rule file not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            rule_data = yaml.safe_load(f)
        
        return self.load_rule_from_dict(rule_data)
    
    def save_rule_to_json(self, rule: ScrapingRule, json_path: Union[str, Path]):
        """Save a scraping rule to a JSON file."""
        path = Path(json_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert rule to dictionary
        rule_dict = asdict(rule)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(rule_dict, f, indent=2, ensure_ascii=False)
    
    def save_rule_to_yaml(self, rule: ScrapingRule, yaml_path: Union[str, Path]):
        """Save a scraping rule to a YAML file."""
        path = Path(yaml_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert rule to dictionary
        rule_dict = asdict(rule)
        
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(rule_dict, f, default_flow_style=False, allow_unicode=True)
    
    def register_rule(self, rule: ScrapingRule) -> bool:
        """Register a scraping rule with the engine."""
        # Validate the rule first
        if not self.validator.validate_rule(rule):
            validation_report = self.validator.get_validation_report()
            logger.error(f"Rule validation failed for '{rule.name}': {validation_report['errors']}")
            return False
        
        self.rules[rule.name] = rule
        logger.info(f"Registered scraping rule: {rule.name}")
        return True
    
    def find_matching_rules(self, url: str) -> List[ScrapingRule]:
        """Find all rules that match the given URL."""
        matching_rules = []
        
        for rule in self.rules.values():
            for pattern in rule.domain_patterns:
                if re.search(pattern, url):
                    matching_rules.append(rule)
                    break
        
        return matching_rules
    
    def apply_rule(self, rule: ScrapingRule, html_content: str, url: str = "") -> ScrapingResult:
        """Apply a scraping rule to HTML content."""
        import time
        start_time = time.time()
        
        result = ScrapingResult(
            rule_name=rule.name,
            url=url,
            success=False
        )
        
        try:
            # Parse HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Apply each selector rule
            for selector_name, selector_rule in rule.selectors.items():
                extraction_result = self._apply_selector_rule(
                    soup, selector_name, selector_rule
                )
                result.extraction_results.append(extraction_result)
                
                if extraction_result.success:
                    result.extracted_data[selector_name] = extraction_result.value
                elif selector_rule.required:
                    result.errors.append(f"Required selector '{selector_name}' failed: {extraction_result.error}")
            
            # Determine overall success
            required_selectors = [name for name, rule in rule.selectors.items() if rule.required]
            successful_required = [name for name in required_selectors if name in result.extracted_data]
            result.success = len(successful_required) == len(required_selectors)
            
        except Exception as e:
            result.errors.append(f"Error applying rule: {str(e)}")
            logger.exception(f"Error applying rule '{rule.name}' to URL '{url}'")
        
        result.processing_time = time.time() - start_time
        return result
    
    def _apply_selector_rule(self, soup: BeautifulSoup, name: str, rule: SelectorRule) -> ExtractionResult:
        """Apply a single selector rule to the parsed HTML."""
        result = ExtractionResult(selector_name=name, success=False)
        
        # Try the main selector first
        elements = self._find_elements(soup, rule.selector, rule.selector_type)
        
        # Try fallback selectors if main selector fails
        if not elements and rule.fallback_selectors:
            for fallback_selector in rule.fallback_selectors:
                elements = self._find_elements(soup, fallback_selector, rule.selector_type)
                if elements:
                    result.fallback_used = fallback_selector
                    break
        
        if not elements:
            result.error = f"No elements found for selector: {rule.selector}"
            return result
        
        result.element_count = len(elements)
        
        try:
            # Extract content based on rule configuration
            if rule.multiple:
                # Extract from all matching elements
                extracted_values = []
                for element in elements:
                    value = self._extract_value_from_element(element, rule)
                    if value is not None:
                        extracted_values.append(value)
                
                result.value = extracted_values
            else:
                # Extract from first matching element
                result.value = self._extract_value_from_element(elements[0], rule)
            
            # Apply transformation if specified
            if rule.transform and result.value is not None:
                transform_func = getattr(self.transformations, rule.transform, None)
                if transform_func:
                    result.value = transform_func(result.value)
                else:
                    result.error = f"Unknown transformation: {rule.transform}"
                    return result
            
            result.success = True
            
        except Exception as e:
            result.error = f"Error extracting value: {str(e)}"
        
        return result
    
    def _find_elements(self, soup: BeautifulSoup, selector: str, selector_type: str) -> List[Tag]:
        """Find elements using CSS or XPath selector."""
        if selector_type == "css":
            return soup.select(selector)
        elif selector_type == "xpath":
            # Note: BeautifulSoup doesn't natively support XPath
            # This would require lxml or another library
            raise NotImplementedError("XPath selectors not yet implemented")
        else:
            raise ValueError(f"Unsupported selector type: {selector_type}")
    
    def _extract_value_from_element(self, element: Tag, rule: SelectorRule) -> Any:
        """Extract value from a BeautifulSoup element."""
        if rule.attribute:
            # Extract attribute value
            return element.get(rule.attribute)
        else:
            # Extract text content
            return element.get_text(strip=True)
    
    def get_rule_summary(self) -> Dict[str, Any]:
        """Get summary information about loaded rules."""
        return {
            'total_rules': len(self.rules),
            'rule_names': list(self.rules.keys()),
            'domain_coverage': self._get_domain_coverage()
        }
    
    def _get_domain_coverage(self) -> Dict[str, List[str]]:
        """Get mapping of domain patterns to rule names."""
        coverage = {}
        for rule_name, rule in self.rules.items():
            for pattern in rule.domain_patterns:
                if pattern not in coverage:
                    coverage[pattern] = []
                coverage[pattern].append(rule_name)
        return coverage


# Example usage and testing
if __name__ == "__main__":
    # Example rule for Bhagavad Gita verses
    bg_rule_data = {
        "name": "bhagavad_gita_verse",
        "description": "Extract Bhagavad Gita verse content from Vedabase",
        "domain_patterns": [
            r"vedabase\.io/en/library/bg",
            r"vedabase\.com/en/library/bg"
        ],
        "selectors": {
            "verse_number": {
                "name": "verse_number",
                "selector": ".verse-number, .r-verse-number",
                "description": "Extract verse number"
            },
            "sanskrit_text": {
                "name": "sanskrit_text", 
                "selector": ".verse-text, .sanskrit",
                "description": "Extract Sanskrit verse text"
            },
            "translation": {
                "name": "translation",
                "selector": ".translation, .r-translation",
                "description": "Extract English translation"
            },
            "synonyms": {
                "name": "synonyms",
                "selector": ".synonyms, .r-synonyms",
                "required": False,
                "description": "Extract word-for-word synonyms"
            },
            "purport": {
                "name": "purport",
                "selector": ".purport, .r-purport",
                "required": False,
                "description": "Extract purport/commentary"
            }
        },
        "version": "1.0",
        "author": "Lexicon Development Team"
    }
    
    # Test the rule engine
    engine = RuleEngine()
    
    try:
        bg_rule = engine.load_rule_from_dict(bg_rule_data)
        success = engine.register_rule(bg_rule)
        
        if success:
            print("✓ Successfully created and registered Bhagavad Gita rule")
            print(f"Rule summary: {engine.get_rule_summary()}")
        else:
            print("✗ Failed to register rule")
            
    except Exception as e:
        print(f"Error: {e}")
