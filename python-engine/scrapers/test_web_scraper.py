#!/usr/bin/env python3
"""
Test script for the web scraping engine.
"""

import asyncio
import sys
import os

# Add the scrapers directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_scraper import WebScraper, ScrapingConfig, scrape_single_url


async def test_basic_scraping():
    """Test basic scraping functionality."""
    print("Testing basic web scraping...")
    
    # Test with a simple HTTP endpoint
    result = await scrape_single_url("https://httpbin.org/get")
    
    if result.is_success:
        print(f"✓ Successfully scraped {result.url}")
        print(f"  Status: {result.status_code}")
        print(f"  Content length: {len(result.content)} bytes")
        print(f"  Content type: {result.metadata.get('content_type', 'unknown')}")
    else:
        print(f"✗ Failed to scrape {result.url}: {result.error}")
    
    return result.is_success


async def test_rate_limiting():
    """Test rate limiting functionality."""
    print("\nTesting rate limiting...")
    
    config = ScrapingConfig(
        requests_per_second=2.0,  # 2 requests per second
        progress_callback=lambda msg, curr, total: print(f"  {msg} ({curr}/{total})")
    )
    
    urls = [
        "https://httpbin.org/get",
        "https://httpbin.org/user-agent",
        "https://httpbin.org/headers"
    ]
    
    scraper = WebScraper(config)
    start_time = asyncio.get_event_loop().time()
    
    try:
        results = await scraper.scrape_urls(urls)
        end_time = asyncio.get_event_loop().time()
        
        duration = end_time - start_time
        expected_min_duration = (len(urls) - 1) / config.requests_per_second
        
        print(f"  Duration: {duration:.2f} seconds")
        print(f"  Expected minimum: {expected_min_duration:.2f} seconds")
        
        if duration >= expected_min_duration * 0.8:  # Allow some tolerance
            print("✓ Rate limiting working correctly")
            return True
        else:
            print("✗ Rate limiting may not be working")
            return False
            
    finally:
        scraper.close()


async def test_error_handling():
    """Test error handling for invalid URLs."""
    print("\nTesting error handling...")
    
    # Test with an invalid URL
    result = await scrape_single_url("https://this-domain-should-not-exist-12345.com")
    
    if not result.is_success and result.error:
        print(f"✓ Error handling working: {result.error}")
        return True
    else:
        print("✗ Error handling not working as expected")
        return False


async def test_content_validation():
    """Test content validation features."""
    print("\nTesting content validation...")
    
    config = ScrapingConfig(
        max_content_size=1000,  # Very small limit for testing
        allowed_content_types=['text/html', 'application/json']
    )
    
    result = await scrape_single_url("https://httpbin.org/get", config)
    
    # This should work as httpbin returns JSON
    if result.is_success:
        print("✓ Content validation allows appropriate content")
        return True
    else:
        print(f"✗ Content validation failed unexpectedly: {result.error}")
        return False


async def main():
    """Run all tests."""
    print("🧪 Testing Lexicon Web Scraper")
    print("=" * 50)
    
    tests = [
        test_basic_scraping,
        test_rate_limiting,
        test_error_handling,
        test_content_validation
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
        print("🎉 All tests passed! Web scraper is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
