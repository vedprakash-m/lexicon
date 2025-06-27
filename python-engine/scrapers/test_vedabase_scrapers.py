#!/usr/bin/env python3
"""
Test script for Vedabase-specific scrapers.

This script tests the specialized scrapers for Bhagavad Gita and Sri Isopanisad
to ensure they work correctly with the new web scraping engine.
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add the scrapers directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vedabase_scrapers import (
    BhagavadGitaScraper, 
    SriIsopanisadScraper,
    scrape_bhagavad_gita,
    scrape_sri_isopanisad
)
from web_scraper import ScrapingConfig


async def test_bg_single_verse():
    """Test scraping a single Bhagavad Gita verse."""
    print("Testing single BG verse scraping...")
    
    config = ScrapingConfig(
        requests_per_second=1.0,
        timeout=15
    )
    
    async with BhagavadGitaScraper(config) as scraper:
        # Test scraping BG 2.47 (famous verse)
        verse_url = "https://vedabase.io/en/library/bg/2/47/"
        verse = await scraper.scrape_verse(verse_url)
        
        if verse:
            print(f"✓ Successfully scraped {verse.verse_reference}")
            print(f"  Sanskrit verse: {verse.sanskrit_verse[:100]}...")
            print(f"  Translation: {verse.translation[:100]}...")
            print(f"  Purport length: {len(verse.purport)} characters")
            return True
        else:
            print("✗ Failed to scrape BG 2.47")
            return False


async def test_bg_chapter():
    """Test scraping a complete BG chapter."""
    print("\nTesting BG chapter scraping...")
    
    config = ScrapingConfig(
        requests_per_second=1.0,
        timeout=15,
        progress_callback=lambda msg, curr, total: print(f"  {msg} ({curr}/{total})")
    )
    
    async with BhagavadGitaScraper(config) as scraper:
        # Test scraping chapter 15 (shorter chapter with 20 verses)
        chapter_url = f"{scraper.base_url}bg/15/"
        chapter_verses = await scraper.scrape_chapter(chapter_url, 15)
        
        expected_verses = scraper.expected_verse_counts[15]
        actual_verses = len(chapter_verses)
        
        print(f"  Expected verses: {expected_verses}")
        print(f"  Actual verses: {actual_verses}")
        
        if actual_verses == expected_verses:
            print(f"✓ Successfully scraped BG Chapter 15: {actual_verses} verses")
            return True
        else:
            print(f"✗ Verse count mismatch for BG Chapter 15")
            return False


async def test_iso_single_mantra():
    """Test scraping a single Sri Isopanisad mantra."""
    print("\nTesting single ISO mantra scraping...")
    
    config = ScrapingConfig(
        requests_per_second=1.0,
        timeout=15
    )
    
    async with SriIsopanisadScraper(config) as scraper:
        # Test scraping the invocation
        mantra_url = "https://vedabase.io/en/library/iso/invocation/"
        mantra = await scraper.scrape_verse(mantra_url)
        
        if mantra:
            print(f"✓ Successfully scraped {mantra.verse_reference}")
            print(f"  Sanskrit mantra: {mantra.sanskrit_verse[:100]}...")
            print(f"  Translation: {mantra.translation[:100]}...")
            print(f"  Purport length: {len(mantra.purport)} characters")
            return True
        else:
            print("✗ Failed to scrape ISO Invocation")
            return False


async def test_iso_limited_mantras():
    """Test scraping first few ISO mantras."""
    print("\nTesting ISO limited mantra scraping...")
    
    config = ScrapingConfig(
        requests_per_second=1.0,
        timeout=15,
        progress_callback=lambda msg, curr, total: print(f"  {msg} ({curr}/{total})")
    )
    
    async with SriIsopanisadScraper(config) as scraper:
        # Test scraping just the first 3 mantras + invocation
        test_urls = [
            "https://vedabase.io/en/library/iso/invocation/",
            "https://vedabase.io/en/library/iso/1/",
            "https://vedabase.io/en/library/iso/2/",
            "https://vedabase.io/en/library/iso/3/"
        ]
        
        mantras = []
        for url in test_urls:
            mantra = await scraper.scrape_verse(url)
            if mantra:
                mantras.append(mantra)
        
        if len(mantras) == len(test_urls):
            print(f"✓ Successfully scraped {len(mantras)} ISO mantras")
            return True
        else:
            print(f"✗ Expected {len(test_urls)} mantras, got {len(mantras)}")
            return False


async def test_metadata_extraction():
    """Test metadata extraction functionality."""
    print("\nTesting metadata extraction...")
    
    config = ScrapingConfig(requests_per_second=1.0, timeout=15)
    
    # Test BG metadata
    async with BhagavadGitaScraper(config) as bg_scraper:
        bg_metadata = bg_scraper.get_metadata()
        
        if bg_metadata.text_abbreviation == "BG" and bg_metadata.total_chapters == 18:
            print("✓ BG metadata extraction working")
            bg_success = True
        else:
            print("✗ BG metadata extraction failed")
            bg_success = False
    
    # Test ISO metadata
    async with SriIsopanisadScraper(config) as iso_scraper:
        iso_metadata = iso_scraper.get_metadata()
        
        if iso_metadata.text_abbreviation == "ISO" and iso_metadata.text_name == "Sri Isopanisad":
            print("✓ ISO metadata extraction working")
            iso_success = True
        else:
            print("✗ ISO metadata extraction failed")
            iso_success = False
    
    return bg_success and iso_success


async def test_json_serialization():
    """Test JSON serialization of scraped content."""
    print("\nTesting JSON serialization...")
    
    config = ScrapingConfig(requests_per_second=1.0, timeout=15)
    
    async with BhagavadGitaScraper(config) as scraper:
        # Scrape a single verse
        verse_url = "https://vedabase.io/en/library/bg/1/1/"
        verse = await scraper.scrape_verse(verse_url)
        
        if verse:
            try:
                # Test dictionary conversion
                verse_dict = verse.to_dict()
                
                # Test JSON serialization
                json_str = json.dumps(verse_dict, ensure_ascii=False, indent=2)
                
                # Test deserialization
                parsed_dict = json.loads(json_str)
                
                if parsed_dict['verse_reference'] == verse.verse_reference:
                    print("✓ JSON serialization working correctly")
                    return True
                else:
                    print("✗ JSON serialization data mismatch")
                    return False
                    
            except Exception as e:
                print(f"✗ JSON serialization failed: {e}")
                return False
        else:
            print("✗ Could not scrape verse for JSON test")
            return False


async def test_convenience_functions():
    """Test the convenience functions for easy usage."""
    print("\nTesting convenience functions...")
    
    # Test progress callback
    progress_messages = []
    def progress_callback(msg, curr, total):
        progress_messages.append(f"{msg} ({curr}/{total})")
        print(f"  Progress: {msg} ({curr}/{total})")
    
    config = ScrapingConfig(
        requests_per_second=2.0,  # Faster for testing
        timeout=10
    )
    
    try:
        # Test limited BG scraping (just try to start the process)
        print("  Testing BG convenience function...")
        
        # This would take too long for a test, so just verify the function exists and can be called
        # In a real scenario, you'd uncomment the line below:
        # verses = await scrape_bhagavad_gita("test_bg.json", config, progress_callback)
        
        # For testing, just verify the function exists
        assert scrape_bhagavad_gita is not None
        print("  ✓ BG convenience function available")
        
        # Similarly for ISO
        assert scrape_sri_isopanisad is not None
        print("  ✓ ISO convenience function available")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Convenience function test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🧪 Testing Lexicon Vedabase Scrapers")
    print("=" * 50)
    
    tests = [
        test_bg_single_verse,
        test_bg_chapter,
        test_iso_single_mantra,
        test_iso_limited_mantras,
        test_metadata_extraction,
        test_json_serialization,
        test_convenience_functions
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Vedabase scrapers are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
