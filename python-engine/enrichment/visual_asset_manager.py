import requests
import hashlib
import os
from PIL import Image, ImageOps
import io
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
import time

@dataclass
class VisualAsset:
    id: str
    url: str
    local_path: str
    asset_type: str  # 'cover', 'author_photo', 'publisher_logo'
    width: int
    height: int
    file_size: int
    format: str
    checksum: str
    book_id: Optional[str] = None
    author_name: Optional[str] = None
    publisher_name: Optional[str] = None

@dataclass
class BookRelationship:
    book_id: str
    related_book_id: str
    relationship_type: str  # 'translation', 'edition', 'series', 'author', 'similar'
    confidence: float
    metadata: Dict

class VisualAssetManager:
    def __init__(self, assets_dir: str = "assets"):
        self.assets_dir = Path(assets_dir)
        self.assets_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.assets_dir / "covers").mkdir(exist_ok=True)
        (self.assets_dir / "authors").mkdir(exist_ok=True)
        (self.assets_dir / "publishers").mkdir(exist_ok=True)
        (self.assets_dir / "thumbnails").mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self.cache_file = self.assets_dir / "asset_cache.json"
        self.relationships_file = self.assets_dir / "relationships.json"
        
        # Load existing cache
        self.asset_cache = self._load_cache()
        self.relationships = self._load_relationships()
        
        # Rate limiting
        self.last_download_time = 0
        self.download_delay = 0.5  # seconds between downloads
        
    def download_cover_image(self, url: str, book_id: str, book_title: str) -> Optional[VisualAsset]:
        """Download and process book cover image"""
        if not url:
            return None
            
        # Check if already cached
        url_hash = hashlib.md5(url.encode()).hexdigest()
        if url_hash in self.asset_cache:
            cached_asset = self.asset_cache[url_hash]
            if Path(cached_asset['local_path']).exists():
                return VisualAsset(**cached_asset)
                
        self._respect_rate_limit()
        
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            # Process image
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            
            # Generate filename
            safe_title = "".join(c for c in book_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title[:50]  # Limit length
            filename = f"{book_id}_{safe_title}.{image.format.lower()}"
            local_path = self.assets_dir / "covers" / filename
            
            # Save original
            with open(local_path, 'wb') as f:
                f.write(image_data)
                
            # Create thumbnail
            thumbnail = self._create_thumbnail(image, (300, 400))
            thumbnail_path = self.assets_dir / "thumbnails" / f"thumb_{filename}"
            thumbnail.save(thumbnail_path, optimize=True, quality=85)
            
            # Calculate checksum
            checksum = hashlib.md5(image_data).hexdigest()
            
            # Create asset record
            asset = VisualAsset(
                id=url_hash,
                url=url,
                local_path=str(local_path),
                asset_type='cover',
                width=image.width,
                height=image.height,
                file_size=len(image_data),
                format=image.format,
                checksum=checksum,
                book_id=book_id
            )
            
            # Cache the asset
            self.asset_cache[url_hash] = asset.__dict__
            self._save_cache()
            
            self.logger.info(f"Downloaded cover image for {book_title}")
            return asset
            
        except Exception as e:
            self.logger.error(f"Failed to download cover image from {url}: {e}")
            return None
            
    def download_author_photo(self, url: str, author_name: str) -> Optional[VisualAsset]:
        """Download and process author photo"""
        if not url:
            return None
            
        url_hash = hashlib.md5(url.encode()).hexdigest()
        if url_hash in self.asset_cache:
            cached_asset = self.asset_cache[url_hash]
            if Path(cached_asset['local_path']).exists():
                return VisualAsset(**cached_asset)
                
        self._respect_rate_limit()
        
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            
            # Generate filename
            safe_name = "".join(c for c in author_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name[:50]
            filename = f"{safe_name}.{image.format.lower()}"
            local_path = self.assets_dir / "authors" / filename
            
            # Save image
            with open(local_path, 'wb') as f:
                f.write(image_data)
                
            # Create thumbnail
            thumbnail = self._create_thumbnail(image, (150, 150), crop_to_square=True)
            thumbnail_path = self.assets_dir / "thumbnails" / f"author_thumb_{filename}"
            thumbnail.save(thumbnail_path, optimize=True, quality=85)
            
            checksum = hashlib.md5(image_data).hexdigest()
            
            asset = VisualAsset(
                id=url_hash,
                url=url,
                local_path=str(local_path),
                asset_type='author_photo',
                width=image.width,
                height=image.height,
                file_size=len(image_data),
                format=image.format,
                checksum=checksum,
                author_name=author_name
            )
            
            self.asset_cache[url_hash] = asset.__dict__
            self._save_cache()
            
            self.logger.info(f"Downloaded author photo for {author_name}")
            return asset
            
        except Exception as e:
            self.logger.error(f"Failed to download author photo from {url}: {e}")
            return None
            
    def _create_thumbnail(self, image: Image.Image, size: Tuple[int, int], crop_to_square: bool = False) -> Image.Image:
        """Create optimized thumbnail"""
        if crop_to_square:
            # Crop to square first
            min_dimension = min(image.width, image.height)
            left = (image.width - min_dimension) // 2
            top = (image.height - min_dimension) // 2
            right = left + min_dimension
            bottom = top + min_dimension
            image = image.crop((left, top, right, bottom))
            
        # Resize maintaining aspect ratio
        image.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
            
        return image
        
    def optimize_image(self, asset: VisualAsset, max_size: Tuple[int, int] = (800, 1200), quality: int = 85) -> bool:
        """Optimize existing image"""
        try:
            image_path = Path(asset.local_path)
            if not image_path.exists():
                return False
                
            image = Image.open(image_path)
            
            # Check if optimization is needed
            if image.width <= max_size[0] and image.height <= max_size[1]:
                return True  # Already optimized
                
            # Resize if too large
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save optimized version
            if image.format == 'PNG' and asset.asset_type == 'cover':
                # Convert PNG covers to JPEG for better compression
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                    
                # Change extension to jpg
                new_path = image_path.with_suffix('.jpg')
                image.save(new_path, 'JPEG', optimize=True, quality=quality)
                
                # Remove old PNG file
                image_path.unlink()
                
                # Update asset record
                asset.local_path = str(new_path)
                asset.format = 'JPEG'
                
            else:
                image.save(image_path, optimize=True, quality=quality)
                
            self.logger.info(f"Optimized image: {asset.local_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to optimize image {asset.local_path}: {e}")
            return False
            
    def detect_book_relationships(self, books_metadata: List[Dict]) -> List[BookRelationship]:
        """Detect relationships between books"""
        relationships = []
        
        for i, book1 in enumerate(books_metadata):
            for book2 in books_metadata[i+1:]:
                relationship = self._analyze_book_relationship(book1, book2)
                if relationship:
                    relationships.append(relationship)
                    
        # Save relationships
        self.relationships.extend(relationships)
        self._save_relationships()
        
        return relationships
        
    def _analyze_book_relationship(self, book1: Dict, book2: Dict) -> Optional[BookRelationship]:
        """Analyze relationship between two books"""
        relationships = []
        
        # Same author relationship
        authors1 = set(book1.get('authors', []))
        authors2 = set(book2.get('authors', []))
        if authors1 & authors2:  # Common authors
            confidence = len(authors1 & authors2) / len(authors1 | authors2)
            relationships.append(('author', confidence))
            
        # Title similarity (possible translations/editions)
        title1 = book1.get('title', '').lower()
        title2 = book2.get('title', '').lower()
        title_similarity = self._calculate_title_similarity(title1, title2)
        if title_similarity > 0.7:
            relationships.append(('edition', title_similarity))
        elif title_similarity > 0.5:
            relationships.append(('similar', title_similarity))
            
        # Series detection
        if self._detect_series_relationship(book1, book2):
            relationships.append(('series', 0.9))
            
        # ISBN relationship (different editions)
        isbn1 = book1.get('isbn', '')
        isbn2 = book2.get('isbn', '')
        if isbn1 and isbn2 and isbn1[:10] == isbn2[:10]:  # Same base ISBN
            relationships.append(('edition', 0.95))
            
        # Return strongest relationship
        if relationships:
            relationship_type, confidence = max(relationships, key=lambda x: x[1])
            return BookRelationship(
                book_id=book1.get('id', ''),
                related_book_id=book2.get('id', ''),
                relationship_type=relationship_type,
                confidence=confidence,
                metadata={
                    'book1_title': book1.get('title', ''),
                    'book2_title': book2.get('title', ''),
                    'common_authors': list(authors1 & authors2),
                }
            )
            
        return None
        
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles"""
        if not title1 or not title2:
            return 0.0
            
        # Remove common words and punctuation
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        words1 = set(word.strip('.,!?;:"()[]{}') for word in title1.split() if word.lower() not in stop_words)
        words2 = set(word.strip('.,!?;:"()[]{}') for word in title2.split() if word.lower() not in stop_words)
        
        if not words1 or not words2:
            return 0.0
            
        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
        
    def _detect_series_relationship(self, book1: Dict, book2: Dict) -> bool:
        """Detect if books are part of the same series"""
        title1 = book1.get('title', '').lower()
        title2 = book2.get('title', '').lower()
        
        # Look for volume/book numbers
        import re
        volume_patterns = [
            r'volume\s+(\d+)',
            r'vol\.\s*(\d+)',
            r'book\s+(\d+)',
            r'part\s+(\d+)',
            r'#(\d+)',
        ]
        
        for pattern in volume_patterns:
            match1 = re.search(pattern, title1)
            match2 = re.search(pattern, title2)
            
            if match1 and match2:
                # Same series if base titles are similar and different volumes
                base1 = re.sub(pattern, '', title1).strip()
                base2 = re.sub(pattern, '', title2).strip()
                
                if self._calculate_title_similarity(base1, base2) > 0.8:
                    return True
                    
        return False
        
    def get_asset_by_book_id(self, book_id: str, asset_type: str = 'cover') -> Optional[VisualAsset]:
        """Get asset for a specific book"""
        for asset_data in self.asset_cache.values():
            if asset_data.get('book_id') == book_id and asset_data.get('asset_type') == asset_type:
                return VisualAsset(**asset_data)
        return None
        
    def get_relationships_for_book(self, book_id: str) -> List[BookRelationship]:
        """Get all relationships for a specific book"""
        return [
            rel for rel in self.relationships
            if rel.book_id == book_id or rel.related_book_id == book_id
        ]
        
    def cleanup_orphaned_assets(self, valid_book_ids: List[str]) -> int:
        """Remove assets for books that no longer exist"""
        removed_count = 0
        
        for asset_id, asset_data in list(self.asset_cache.items()):
            book_id = asset_data.get('book_id')
            if book_id and book_id not in valid_book_ids:
                # Remove file
                asset_path = Path(asset_data['local_path'])
                if asset_path.exists():
                    asset_path.unlink()
                    
                # Remove from cache
                del self.asset_cache[asset_id]
                removed_count += 1
                
        if removed_count > 0:
            self._save_cache()
            self.logger.info(f"Cleaned up {removed_count} orphaned assets")
            
        return removed_count
        
    def _respect_rate_limit(self):
        """Ensure rate limiting between downloads"""
        current_time = time.time()
        time_since_last = current_time - self.last_download_time
        
        if time_since_last < self.download_delay:
            sleep_time = self.download_delay - time_since_last
            time.sleep(sleep_time)
            
        self.last_download_time = time.time()
        
    def _load_cache(self) -> Dict:
        """Load asset cache from file"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load asset cache: {e}")
        return {}
        
    def _save_cache(self):
        """Save asset cache to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.asset_cache, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save asset cache: {e}")
            
    def _load_relationships(self) -> List[BookRelationship]:
        """Load relationships from file"""
        if self.relationships_file.exists():
            try:
                with open(self.relationships_file, 'r') as f:
                    data = json.load(f)
                    return [BookRelationship(**rel) for rel in data]
            except Exception as e:
                self.logger.error(f"Failed to load relationships: {e}")
        return []
        
    def _save_relationships(self):
        """Save relationships to file"""
        try:
            data = [rel.__dict__ for rel in self.relationships]
            with open(self.relationships_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save relationships: {e}")
            
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(self.assets_dir):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    total_size += file_path.stat().st_size
                    file_count += 1
                    
        return {
            'total_size_mb': total_size / (1024 * 1024),
            'file_count': file_count,
            'cached_assets': len(self.asset_cache),
            'relationships': len(self.relationships)
        }