#!/usr/bin/env python3
"""
Visual Asset Management System for Lexicon

This module provides comprehensive visual asset management for book metadata,
including cover images, author photos, publisher logos, and other visual content.
Features include high-resolution downloads, caching, optimization, and fallback handling.
"""

import asyncio
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse

import aiohttp
from PIL import Image, ImageOps


class AssetType(Enum):
    """Types of visual assets."""
    COVER_IMAGE = "cover_image"
    AUTHOR_PHOTO = "author_photo" 
    PUBLISHER_LOGO = "publisher_logo"
    SERIES_BANNER = "series_banner"
    GENRE_ICON = "genre_icon"


class AssetQuality(Enum):
    """Quality levels for visual assets."""
    THUMBNAIL = "thumbnail"      # 150x150
    SMALL = "small"             # 300x300
    MEDIUM = "medium"           # 600x600
    LARGE = "large"             # 1200x1200
    ORIGINAL = "original"       # Original size


class OptimizationFormat(Enum):
    """Supported optimization formats."""
    WEBP = "webp"
    JPEG = "jpeg"
    PNG = "png"
    AVIF = "avif"


@dataclass
class AssetMetadata:
    """Metadata for a visual asset."""
    asset_id: str
    asset_type: AssetType
    source_url: str
    local_path: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    format: Optional[str] = None
    quality: Optional[AssetQuality] = None
    checksum: Optional[str] = None
    download_date: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    cache_expires: Optional[datetime] = None
    optimization_level: Optional[int] = None
    fallback_used: bool = False
    error_count: int = 0
    last_error: Optional[str] = None


@dataclass
class AssetCollection:
    """Collection of assets for a single entity (book, author, etc.)."""
    entity_id: str
    entity_type: str  # "book", "author", "publisher"
    assets: Dict[AssetType, List[AssetMetadata]] = field(default_factory=dict)
    primary_cover: Optional[str] = None
    primary_author_photo: Optional[str] = None
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)


@dataclass
class OptimizationConfig:
    """Configuration for asset optimization."""
    target_format: OptimizationFormat = OptimizationFormat.WEBP
    quality_levels: List[AssetQuality] = field(default_factory=lambda: [
        AssetQuality.THUMBNAIL, AssetQuality.SMALL, AssetQuality.MEDIUM
    ])
    jpeg_quality: int = 85
    webp_quality: int = 80
    progressive: bool = True
    preserve_metadata: bool = False
    max_file_size: int = 2 * 1024 * 1024  # 2MB
    enable_compression: bool = True


class VisualAssetManager:
    """
    Comprehensive visual asset management system.
    
    Handles downloading, caching, optimization, and serving of visual assets
    for books, authors, publishers, and other entities in the Lexicon system.
    """
    
    def __init__(
        self,
        cache_dir: Union[str, Path],
        optimization_config: Optional[OptimizationConfig] = None,
        max_concurrent_downloads: int = 10,
        cache_expiry_days: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize the visual asset manager.
        
        Args:
            cache_dir: Directory for caching assets
            optimization_config: Configuration for asset optimization
            max_concurrent_downloads: Maximum concurrent downloads
            cache_expiry_days: Days before cached assets expire
            max_retries: Maximum retry attempts for downloads
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.optimization_config = optimization_config or OptimizationConfig()
        self.max_concurrent_downloads = max_concurrent_downloads
        self.cache_expiry_days = cache_expiry_days
        self.max_retries = max_retries
        
        # Initialize cache directories
        self._init_cache_structure()
        
        # Load existing asset registry
        self.registry_file = self.cache_dir / "asset_registry.json"
        self.asset_registry: Dict[str, AssetCollection] = self._load_registry()
        
        # Session for HTTP requests
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Download semaphore
        self._download_semaphore = asyncio.Semaphore(max_concurrent_downloads)
        
        # Fallback assets
        self._fallback_assets = {
            AssetType.COVER_IMAGE: self._get_fallback_cover_path(),
            AssetType.AUTHOR_PHOTO: self._get_fallback_author_path(),
            AssetType.PUBLISHER_LOGO: self._get_fallback_publisher_path(),
        }
    
    def _init_cache_structure(self):
        """Initialize cache directory structure."""
        subdirs = [
            "covers", "authors", "publishers", "series", "genres",
            "optimized", "thumbnails", "fallbacks", "temp"
        ]
        for subdir in subdirs:
            (self.cache_dir / subdir).mkdir(exist_ok=True)
    
    def _load_registry(self) -> Dict[str, AssetCollection]:
        """Load asset registry from disk."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    registry = {}
                    for entity_id, collection_data in data.items():
                        # Convert dict back to AssetCollection
                        assets = {}
                        for asset_type_str, asset_list in collection_data.get('assets', {}).items():
                            asset_type = AssetType(asset_type_str)
                            assets[asset_type] = [
                                AssetMetadata(**asset_data) for asset_data in asset_list
                            ]
                        
                        collection = AssetCollection(
                            entity_id=collection_data['entity_id'],
                            entity_type=collection_data['entity_type'],
                            assets=assets,
                            primary_cover=collection_data.get('primary_cover'),
                            primary_author_photo=collection_data.get('primary_author_photo'),
                            created_date=datetime.fromisoformat(collection_data['created_date']),
                            updated_date=datetime.fromisoformat(collection_data['updated_date'])
                        )
                        registry[entity_id] = collection
                    return registry
            except Exception as e:
                print(f"Warning: Could not load asset registry: {e}")
        return {}
    
    def _save_registry(self):
        """Save asset registry to disk."""
        try:
            # Convert to serializable format
            data = {}
            for entity_id, collection in self.asset_registry.items():
                assets_dict = {}
                for asset_type, asset_list in collection.assets.items():
                    assets_dict[asset_type.value] = [
                        {k: (v.isoformat() if isinstance(v, datetime) else 
                             v.value if hasattr(v, 'value') else v)
                         for k, v in asset.__dict__.items()}
                        for asset in asset_list
                    ]
                
                data[entity_id] = {
                    'entity_id': collection.entity_id,
                    'entity_type': collection.entity_type,
                    'assets': assets_dict,
                    'primary_cover': collection.primary_cover,
                    'primary_author_photo': collection.primary_author_photo,
                    'created_date': collection.created_date.isoformat(),
                    'updated_date': collection.updated_date.isoformat()
                }
            
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save asset registry: {e}")
    
    def _get_fallback_cover_path(self) -> Path:
        """Get path to fallback cover image."""
        return self.cache_dir / "fallbacks" / "default_cover.png"
    
    def _get_fallback_author_path(self) -> Path:
        """Get path to fallback author photo."""
        return self.cache_dir / "fallbacks" / "default_author.png"
    
    def _get_fallback_publisher_path(self) -> Path:
        """Get path to fallback publisher logo."""
        return self.cache_dir / "fallbacks" / "default_publisher.png"
    
    def _create_fallback_assets(self):
        """Create default fallback assets if they don't exist."""
        for asset_type, fallback_path in self._fallback_assets.items():
            if not fallback_path.exists():
                self._create_placeholder_image(fallback_path, asset_type)
    
    def _create_placeholder_image(self, path: Path, asset_type: AssetType):
        """Create a placeholder image for fallback use."""
        size = (300, 400) if asset_type == AssetType.COVER_IMAGE else (300, 300)
        
        # Create simple colored placeholder
        color_map = {
            AssetType.COVER_IMAGE: "#4A90E2",  # Blue
            AssetType.AUTHOR_PHOTO: "#7ED321",  # Green
            AssetType.PUBLISHER_LOGO: "#F5A623",  # Orange
        }
        
        try:
            img = Image.new('RGB', size, color_map.get(asset_type, "#CCCCCC"))
            img.save(path, 'PNG')
        except Exception as e:
            print(f"Warning: Could not create placeholder image: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30, connect=10),
            headers={'User-Agent': 'Lexicon-AssetManager/1.0'}
        )
        self._create_fallback_assets()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
        self._save_registry()
    
    def _generate_asset_id(self, url: str, asset_type: AssetType) -> str:
        """Generate unique asset ID from URL and type."""
        content = f"{url}:{asset_type.value}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_asset_path(
        self, 
        asset_id: str, 
        asset_type: AssetType, 
        quality: AssetQuality = AssetQuality.ORIGINAL
    ) -> Path:
        """Get the local path for an asset."""
        subdir_map = {
            AssetType.COVER_IMAGE: "covers",
            AssetType.AUTHOR_PHOTO: "authors",
            AssetType.PUBLISHER_LOGO: "publishers",
            AssetType.SERIES_BANNER: "series",
            AssetType.GENRE_ICON: "genres"
        }
        
        subdir = subdir_map.get(asset_type, "other")
        if quality != AssetQuality.ORIGINAL:
            subdir = "optimized"
        
        filename = f"{asset_id}_{quality.value}.{self.optimization_config.target_format.value}"
        return self.cache_dir / subdir / filename
    
    async def download_asset(
        self,
        url: str,
        asset_type: AssetType,
        entity_id: str,
        entity_type: str = "book",
        force_refresh: bool = False
    ) -> Optional[AssetMetadata]:
        """
        Download and cache a visual asset.
        
        Args:
            url: URL of the asset to download
            asset_type: Type of asset (cover, author photo, etc.)
            entity_id: ID of the entity this asset belongs to
            entity_type: Type of entity (book, author, publisher)
            force_refresh: Force re-download even if cached
            
        Returns:
            AssetMetadata object if successful, None otherwise
        """
        async with self._download_semaphore:
            return await self._download_asset_impl(
                url, asset_type, entity_id, entity_type, force_refresh
            )
    
    async def _download_asset_impl(
        self,
        url: str,
        asset_type: AssetType,
        entity_id: str,
        entity_type: str,
        force_refresh: bool
    ) -> Optional[AssetMetadata]:
        """Implementation of asset download."""
        asset_id = self._generate_asset_id(url, asset_type)
        
        # Check if asset already exists and is valid
        if not force_refresh:
            existing_asset = self._get_existing_asset(entity_id, asset_type, asset_id)
            if existing_asset and self._is_asset_valid(existing_asset):
                existing_asset.last_accessed = datetime.now()
                return existing_asset
        
        # Download the asset
        for attempt in range(self.max_retries):
            try:
                if not self.session:
                    raise RuntimeError("Session not initialized")
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Save original asset
                        original_path = self._get_asset_path(asset_id, asset_type)
                        original_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(original_path, 'wb') as f:
                            f.write(content)
                        
                        # Get image metadata
                        metadata = self._extract_image_metadata(original_path)
                        
                        # Create asset metadata
                        asset_metadata = AssetMetadata(
                            asset_id=asset_id,
                            asset_type=asset_type,
                            source_url=url,
                            local_path=str(original_path),
                            width=metadata.get('width'),
                            height=metadata.get('height'),
                            file_size=metadata.get('file_size'),
                            format=metadata.get('format'),
                            quality=AssetQuality.ORIGINAL,
                            checksum=self._calculate_checksum(content),
                            download_date=datetime.now(),
                            last_accessed=datetime.now(),
                            cache_expires=datetime.now() + timedelta(days=self.cache_expiry_days),
                            error_count=0
                        )
                        
                        # Generate optimized versions
                        await self._generate_optimized_versions(asset_metadata)
                        
                        # Add to registry
                        self._add_to_registry(entity_id, entity_type, asset_metadata)
                        
                        return asset_metadata
                    
                    else:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status
                        )
            
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"Failed to download asset after {self.max_retries} attempts: {e}")
                    # Create error asset metadata
                    asset_metadata = AssetMetadata(
                        asset_id=asset_id,
                        asset_type=asset_type,
                        source_url=url,
                        error_count=self.max_retries,
                        last_error=str(e),
                        fallback_used=True
                    )
                    return asset_metadata
                else:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def _get_existing_asset(
        self, 
        entity_id: str, 
        asset_type: AssetType, 
        asset_id: str
    ) -> Optional[AssetMetadata]:
        """Get existing asset from registry."""
        collection = self.asset_registry.get(entity_id)
        if not collection:
            return None
        
        assets = collection.assets.get(asset_type, [])
        for asset in assets:
            if asset.asset_id == asset_id:
                return asset
        
        return None
    
    def _is_asset_valid(self, asset: AssetMetadata) -> bool:
        """Check if cached asset is still valid."""
        if asset.fallback_used:
            return False
        
        if asset.cache_expires and datetime.now() > asset.cache_expires:
            return False
        
        if asset.local_path and not Path(asset.local_path).exists():
            return False
        
        return True
    
    def _extract_image_metadata(self, image_path: Path) -> Dict:
        """Extract metadata from an image file."""
        try:
            with Image.open(image_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format.lower() if img.format else None,
                    'file_size': image_path.stat().st_size,
                    'mode': img.mode
                }
        except Exception as e:
            print(f"Warning: Could not extract image metadata: {e}")
            return {'file_size': image_path.stat().st_size}
    
    def _calculate_checksum(self, content: bytes) -> str:
        """Calculate MD5 checksum of content."""
        return hashlib.md5(content).hexdigest()
    
    async def _generate_optimized_versions(self, asset: AssetMetadata):
        """Generate optimized versions of an asset."""
        if not asset.local_path or asset.fallback_used:
            return
        
        try:
            original_path = Path(asset.local_path)
            
            for quality in self.optimization_config.quality_levels:
                optimized_path = self._get_asset_path(
                    asset.asset_id, 
                    asset.asset_type, 
                    quality
                )
                optimized_path.parent.mkdir(parents=True, exist_ok=True)
                
                await self._create_optimized_version(
                    original_path, 
                    optimized_path, 
                    quality
                )
        
        except Exception as e:
            print(f"Warning: Could not generate optimized versions: {e}")
    
    async def _create_optimized_version(
        self, 
        source_path: Path, 
        target_path: Path, 
        quality: AssetQuality
    ):
        """Create an optimized version of an image."""
        try:
            with Image.open(source_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    if self.optimization_config.target_format in [
                        OptimizationFormat.JPEG
                    ]:
                        # Create white background for JPEG
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                        img = rgb_img
                
                # Resize based on quality
                target_size = self._get_target_size(quality)
                if target_size:
                    img = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)
                
                # Save with optimization
                save_kwargs = {
                    'optimize': True,
                    'progressive': self.optimization_config.progressive
                }
                
                if self.optimization_config.target_format == OptimizationFormat.JPEG:
                    save_kwargs['quality'] = self.optimization_config.jpeg_quality
                elif self.optimization_config.target_format == OptimizationFormat.WEBP:
                    save_kwargs['quality'] = self.optimization_config.webp_quality
                
                img.save(target_path, self.optimization_config.target_format.value.upper(), **save_kwargs)
        
        except Exception as e:
            print(f"Warning: Could not create optimized version: {e}")
    
    def _get_target_size(self, quality: AssetQuality) -> Optional[Tuple[int, int]]:
        """Get target size for a quality level."""
        size_map = {
            AssetQuality.THUMBNAIL: (150, 150),
            AssetQuality.SMALL: (300, 300),
            AssetQuality.MEDIUM: (600, 600),
            AssetQuality.LARGE: (1200, 1200)
        }
        return size_map.get(quality)
    
    def _add_to_registry(
        self, 
        entity_id: str, 
        entity_type: str, 
        asset: AssetMetadata
    ):
        """Add asset to registry."""
        if entity_id not in self.asset_registry:
            self.asset_registry[entity_id] = AssetCollection(
                entity_id=entity_id,
                entity_type=entity_type
            )
        
        collection = self.asset_registry[entity_id]
        
        if asset.asset_type not in collection.assets:
            collection.assets[asset.asset_type] = []
        
        # Replace existing asset with same ID or add new one
        assets = collection.assets[asset.asset_type]
        for i, existing_asset in enumerate(assets):
            if existing_asset.asset_id == asset.asset_id:
                assets[i] = asset
                break
        else:
            assets.append(asset)
        
        # Update primary assets
        if asset.asset_type == AssetType.COVER_IMAGE and not collection.primary_cover:
            collection.primary_cover = asset.asset_id
        elif asset.asset_type == AssetType.AUTHOR_PHOTO and not collection.primary_author_photo:
            collection.primary_author_photo = asset.asset_id
        
        collection.updated_date = datetime.now()
    
    async def batch_download_assets(
        self,
        asset_requests: List[Tuple[str, AssetType, str, str]],
        progress_callback: Optional[callable] = None
    ) -> List[Optional[AssetMetadata]]:
        """
        Download multiple assets in batch.
        
        Args:
            asset_requests: List of (url, asset_type, entity_id, entity_type) tuples
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of AssetMetadata objects (None for failed downloads)
        """
        tasks = []
        for url, asset_type, entity_id, entity_type in asset_requests:
            task = self.download_asset(url, asset_type, entity_id, entity_type)
            tasks.append(task)
        
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)
            
            if progress_callback:
                progress_callback(i + 1, len(tasks), result)
        
        return results
    
    def get_asset_url(
        self,
        entity_id: str,
        asset_type: AssetType,
        quality: AssetQuality = AssetQuality.MEDIUM
    ) -> Optional[str]:
        """
        Get local URL for an asset.
        
        Args:
            entity_id: ID of the entity
            asset_type: Type of asset
            quality: Quality level desired
            
        Returns:
            Local file path as string, or fallback path
        """
        collection = self.asset_registry.get(entity_id)
        if not collection:
            return str(self._fallback_assets.get(asset_type, ""))
        
        assets = collection.assets.get(asset_type, [])
        if not assets:
            return str(self._fallback_assets.get(asset_type, ""))
        
        # Find the best quality asset
        for asset in assets:
            if not asset.fallback_used and asset.local_path:
                # Check for optimized version
                optimized_path = self._get_asset_path(
                    asset.asset_id, 
                    asset_type, 
                    quality
                )
                if optimized_path.exists():
                    return str(optimized_path)
                elif Path(asset.local_path).exists():
                    return asset.local_path
        
        return str(self._fallback_assets.get(asset_type, ""))
    
    def cleanup_expired_assets(self):
        """Clean up expired assets from cache."""
        now = datetime.now()
        cleaned_count = 0
        
        for entity_id, collection in list(self.asset_registry.items()):
            for asset_type, assets in list(collection.assets.items()):
                valid_assets = []
                
                for asset in assets:
                    if (asset.cache_expires and now > asset.cache_expires) or \
                       (asset.local_path and not Path(asset.local_path).exists()):
                        # Remove expired/missing asset
                        if asset.local_path:
                            try:
                                Path(asset.local_path).unlink(missing_ok=True)
                            except Exception:
                                pass
                        cleaned_count += 1
                    else:
                        valid_assets.append(asset)
                
                if valid_assets:
                    collection.assets[asset_type] = valid_assets
                else:
                    del collection.assets[asset_type]
            
            # Remove empty collections
            if not collection.assets:
                del self.asset_registry[entity_id]
        
        print(f"Cleaned up {cleaned_count} expired assets")
        self._save_registry()
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        total_assets = 0
        total_size = 0
        asset_type_counts = {asset_type: 0 for asset_type in AssetType}
        
        for collection in self.asset_registry.values():
            for asset_type, assets in collection.assets.items():
                for asset in assets:
                    total_assets += 1
                    asset_type_counts[asset_type] += 1
                    
                    if asset.local_path and Path(asset.local_path).exists():
                        total_size += Path(asset.local_path).stat().st_size
        
        return {
            'total_assets': total_assets,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'asset_type_counts': {k.value: v for k, v in asset_type_counts.items()},
            'cache_dir': str(self.cache_dir),
            'registry_entities': len(self.asset_registry)
        }


# Convenience functions
async def download_book_cover(
    manager: VisualAssetManager,
    cover_url: str,
    book_id: str
) -> Optional[AssetMetadata]:
    """Download a book cover image."""
    return await manager.download_asset(
        cover_url, 
        AssetType.COVER_IMAGE, 
        book_id, 
        "book"
    )


async def download_author_photo(
    manager: VisualAssetManager,
    photo_url: str,
    author_id: str
) -> Optional[AssetMetadata]:
    """Download an author photo."""
    return await manager.download_asset(
        photo_url, 
        AssetType.AUTHOR_PHOTO, 
        author_id, 
        "author"
    )


def get_book_cover_path(
    manager: VisualAssetManager,
    book_id: str,
    quality: AssetQuality = AssetQuality.MEDIUM
) -> Optional[str]:
    """Get the local path for a book cover."""
    return manager.get_asset_url(book_id, AssetType.COVER_IMAGE, quality)
