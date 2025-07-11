#!/usr/bin/env python3
"""
Demo script for Visual Asset Manager

This script demonstrates the capabilities of the visual asset management system,
including downloading book covers, author photos, optimization, caching, and batch processing.
"""

import asyncio
import json
import tempfile
from datetime import datetime
from pathlib import Path

from visual_asset_manager import (
    VisualAssetManager, AssetType, AssetQuality, OptimizationConfig, 
    OptimizationFormat, download_book_cover, download_author_photo, 
    get_book_cover_path
)


# Sample book data with cover images and author photos
SAMPLE_BOOKS = [
    {
        "id": "bhagavad_gita",
        "title": "Bhagavad Gita As It Is",
        "author": "A.C. Bhaktivedanta Swami Prabhupada",
        "cover_url": "https://covers.openlibrary.org/b/id/240726-L.jpg",
        "author_photo": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/A._C._Bhaktivedanta_Swami_Prabhupada.jpg/256px-A._C._Bhaktivedanta_Swami_Prabhupada.jpg"
    },
    {
        "id": "art_of_war",
        "title": "The Art of War",
        "author": "Sun Tzu",
        "cover_url": "https://covers.openlibrary.org/b/id/8737734-L.jpg",
        "author_photo": None  # No photo available
    },
    {
        "id": "thinking_fast_slow",
        "title": "Thinking, Fast and Slow",
        "author": "Daniel Kahneman",
        "cover_url": "https://covers.openlibrary.org/b/id/8482081-L.jpg",
        "author_photo": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Daniel_Kahneman_Nobel_Prize.jpg/256px-Daniel_Kahneman_Nobel_Prize.jpg"
    },
    {
        "id": "invalid_book",
        "title": "Book with Invalid URLs",
        "author": "Unknown Author",
        "cover_url": "https://invalid-url-that-will-fail.com/cover.jpg",
        "author_photo": "https://another-invalid-url.com/author.jpg"
    }
]


async def test_single_asset_download(manager: VisualAssetManager):
    """Test downloading a single asset."""
    print("📚 Testing single asset download...")
    
    book = SAMPLE_BOOKS[0]  # Bhagavad Gita
    
    # Download cover image
    cover_result = await download_book_cover(
        manager, 
        book["cover_url"], 
        book["id"]
    )
    
    if cover_result and not cover_result.fallback_used:
        print(f"   ✓ Cover downloaded: {book['title']}")
        print(f"     Dimensions: {cover_result.width}x{cover_result.height}")
        print(f"     Format: {cover_result.format}")
        print(f"     Size: {cover_result.file_size} bytes")
        print(f"     Local path: {cover_result.local_path}")
    else:
        print(f"   ❌ Cover download failed: {cover_result.last_error if cover_result else 'Unknown error'}")
    
    # Download author photo if available
    if book["author_photo"]:
        author_result = await download_author_photo(
            manager,
            book["author_photo"],
            f"author_{book['id']}"
        )
        
        if author_result and not author_result.fallback_used:
            print(f"   ✓ Author photo downloaded: {book['author']}")
            print(f"     Dimensions: {author_result.width}x{author_result.height}")
            print(f"     Local path: {author_result.local_path}")
        else:
            print(f"   ❌ Author photo download failed: {author_result.last_error if author_result else 'Unknown error'}")
    
    return cover_result


async def test_batch_download(manager: VisualAssetManager):
    """Test batch downloading of multiple assets."""
    print("\n📚 Testing batch asset download...")
    
    # Prepare batch requests
    requests = []
    for book in SAMPLE_BOOKS:
        # Add cover image request
        requests.append((
            book["cover_url"],
            AssetType.COVER_IMAGE,
            book["id"],
            "book"
        ))
        
        # Add author photo request if available
        if book["author_photo"]:
            requests.append((
                book["author_photo"],
                AssetType.AUTHOR_PHOTO,
                f"author_{book['id']}",
                "author"
            ))
    
    print(f"   Downloading {len(requests)} assets...")
    
    # Progress callback
    def progress_callback(completed, total, result):
        if result:
            status = "✓" if not result.fallback_used else "❌"
            print(f"   {status} Progress: {completed}/{total} - {result.asset_type.value}")
    
    # Download in batch
    results = await manager.batch_download_assets(requests, progress_callback)
    
    # Analyze results
    successful = sum(1 for r in results if r and not r.fallback_used)
    failed = len(results) - successful
    
    print(f"   ✓ Batch download completed")
    print(f"     Successful: {successful}")
    print(f"     Failed: {failed}")
    
    return results


async def test_asset_retrieval(manager: VisualAssetManager):
    """Test asset retrieval and quality selection."""
    print("\n📚 Testing asset retrieval...")
    
    book_id = SAMPLE_BOOKS[0]["id"]
    
    # Test different quality levels
    qualities = [AssetQuality.THUMBNAIL, AssetQuality.SMALL, AssetQuality.MEDIUM, AssetQuality.LARGE]
    
    for quality in qualities:
        cover_path = get_book_cover_path(manager, book_id, quality)
        if cover_path and Path(cover_path).exists():
            file_size = Path(cover_path).stat().st_size
            print(f"   ✓ {quality.value}: {cover_path} ({file_size} bytes)")
        else:
            print(f"   ❌ {quality.value}: Not available (using fallback)")


def test_optimization_config():
    """Test different optimization configurations."""
    print("\n📚 Testing optimization configurations...")
    
    # Default config
    default_config = OptimizationConfig()
    print(f"   Default format: {default_config.target_format.value}")
    print(f"   Quality levels: {[q.value for q in default_config.quality_levels]}")
    print(f"   JPEG quality: {default_config.jpeg_quality}")
    print(f"   WebP quality: {default_config.webp_quality}")
    
    # Custom config for high-quality archival
    archive_config = OptimizationConfig(
        target_format=OptimizationFormat.PNG,
        quality_levels=[AssetQuality.MEDIUM, AssetQuality.LARGE, AssetQuality.ORIGINAL],
        preserve_metadata=True,
        max_file_size=10 * 1024 * 1024  # 10MB
    )
    print(f"   Archive format: {archive_config.target_format.value}")
    print(f"   Archive levels: {[q.value for q in archive_config.quality_levels]}")
    print(f"   Preserve metadata: {archive_config.preserve_metadata}")
    
    # Performance config for web display
    web_config = OptimizationConfig(
        target_format=OptimizationFormat.WEBP,
        quality_levels=[AssetQuality.THUMBNAIL, AssetQuality.SMALL],
        webp_quality=60,
        max_file_size=500 * 1024  # 500KB
    )
    print(f"   Web format: {web_config.target_format.value}")
    print(f"   Web levels: {[q.value for q in web_config.quality_levels]}")
    print(f"   Web quality: {web_config.webp_quality}")


async def test_error_handling(manager: VisualAssetManager):
    """Test error handling and fallback mechanisms."""
    print("\n📚 Testing error handling...")
    
    invalid_book = SAMPLE_BOOKS[3]  # Book with invalid URLs
    
    # Try to download invalid cover
    cover_result = await manager.download_asset(
        invalid_book["cover_url"],
        AssetType.COVER_IMAGE,
        invalid_book["id"]
    )
    
    if cover_result:
        print(f"   ✓ Error handling working")
        print(f"     Fallback used: {cover_result.fallback_used}")
        print(f"     Error count: {cover_result.error_count}")
        print(f"     Last error: {cover_result.last_error}")
        
        # Test fallback retrieval
        fallback_path = manager.get_asset_url(invalid_book["id"], AssetType.COVER_IMAGE)
        print(f"     Fallback path: {fallback_path}")
    else:
        print("   ❌ Error handling failed")


def test_cache_management(manager: VisualAssetManager):
    """Test cache management and statistics."""
    print("\n📚 Testing cache management...")
    
    # Get cache statistics
    stats = manager.get_cache_stats()
    print(f"   Cache statistics:")
    print(f"     Total assets: {stats['total_assets']}")
    print(f"     Total size: {stats['total_size_mb']} MB")
    print(f"     Cache directory: {stats['cache_dir']}")
    print(f"     Registry entities: {stats['registry_entities']}")
    
    # Asset type breakdown
    for asset_type, count in stats['asset_type_counts'].items():
        if count > 0:
            print(f"     {asset_type}: {count} assets")
    
    # Test cleanup (in real usage, this would remove expired assets)
    print("   Testing cleanup functionality...")
    manager.cleanup_expired_assets()
    print("   ✓ Cleanup completed")


async def export_results_to_json(manager: VisualAssetManager, filename: str):
    """Export asset registry to JSON for inspection."""
    print(f"\n💾 Exporting asset registry to {filename}...")
    
    # Convert registry to serializable format
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "cache_stats": manager.get_cache_stats(),
        "entities": {}
    }
    
    for entity_id, collection in manager.asset_registry.items():
        entity_data = {
            "entity_type": collection.entity_type,
            "primary_cover": collection.primary_cover,
            "primary_author_photo": collection.primary_author_photo,
            "created_date": collection.created_date.isoformat(),
            "updated_date": collection.updated_date.isoformat(),
            "assets": {}
        }
        
        for asset_type, assets in collection.assets.items():
            asset_list = []
            for asset in assets:
                asset_data = {
                    "asset_id": asset.asset_id,
                    "source_url": asset.source_url,
                    "local_path": asset.local_path,
                    "width": asset.width,
                    "height": asset.height,
                    "file_size": asset.file_size,
                    "format": asset.format,
                    "quality": asset.quality.value if asset.quality else None,
                    "checksum": asset.checksum,
                    "download_date": asset.download_date.isoformat() if asset.download_date else None,
                    "fallback_used": asset.fallback_used,
                    "error_count": asset.error_count,
                    "last_error": asset.last_error
                }
                asset_list.append(asset_data)
            
            entity_data["assets"][asset_type.value] = asset_list
        
        export_data["entities"][entity_id] = entity_data
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Exported registry for {len(export_data['entities'])} entities")


async def main():
    """Run all visual asset manager demos."""
    print("🚀 Testing Lexicon Visual Asset Management System")
    print("=" * 60)
    
    # Create temporary cache directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir) / "asset_cache"
        
        # Create manager with custom optimization config
        optimization_config = OptimizationConfig(
            target_format=OptimizationFormat.WEBP,
            quality_levels=[AssetQuality.THUMBNAIL, AssetQuality.SMALL, AssetQuality.MEDIUM],
            webp_quality=80,
            enable_compression=True
        )
        
        try:
            async with VisualAssetManager(
                cache_dir=cache_dir,
                optimization_config=optimization_config,
                max_concurrent_downloads=3,
                cache_expiry_days=7
            ) as manager:
                
                # Run demos
                await test_single_asset_download(manager)
                await test_batch_download(manager)
                await test_asset_retrieval(manager)
                test_optimization_config()
                await test_error_handling(manager)
                test_cache_management(manager)
                
                # Export results
                await export_results_to_json(manager, 'visual_asset_demo_results.json')
            
            print("\n" + "=" * 60)
            print("✅ All visual asset management tests completed successfully!")
            
            print("\nNote: This demo uses real URLs from OpenLibrary and Wikipedia.")
            print("Asset files are cached locally and optimized automatically.")
            print("The system gracefully handles failed downloads with fallback assets.")
            
        except Exception as e:
            print(f"\n❌ Demo failed with error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
