#!/usr/bin/env python3
"""
Cloud Storage Integration System for Lexicon
Handles synchronization with cloud storage providers (iCloud, Google Drive, Dropbox)
"""

import asyncio
import json
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles
import aiohttp
from cryptography.fernet import Fernet
import platform

class CloudProvider(Enum):
    """Supported cloud storage providers."""
    ICLOUD = "icloud"
    GOOGLE_DRIVE = "google_drive"
    DROPBOX = "dropbox"
    ONEDRIVE = "onedrive"
    LOCAL_ONLY = "local_only"

class SyncStatus(Enum):
    """Synchronization status."""
    SYNCED = "synced"
    PENDING = "pending"
    CONFLICT = "conflict"
    ERROR = "error"
    NOT_SYNCED = "not_synced"

class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    KEEP_LOCAL = "keep_local"
    KEEP_REMOTE = "keep_remote"
    MERGE = "merge"
    ASK_USER = "ask_user"

@dataclass
class SyncFile:
    """Represents a file in the sync system."""
    path: str
    checksum: str
    size: int
    modified_time: datetime
    sync_status: SyncStatus
    cloud_path: Optional[str] = None
    last_sync_time: Optional[datetime] = None
    provider: Optional[CloudProvider] = None

@dataclass
class SyncConfiguration:
    """Cloud sync configuration."""
    enabled: bool = True
    provider: CloudProvider = CloudProvider.ICLOUD
    auto_sync_interval: int = 300  # seconds
    conflict_resolution: ConflictResolution = ConflictResolution.ASK_USER
    encrypt_data: bool = True
    sync_patterns: List[str] = None
    exclude_patterns: List[str] = None
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    def __post_init__(self):
        if self.sync_patterns is None:
            self.sync_patterns = [
                "*.json",
                "*.db",
                "enrichment_*.json",
                "catalog_*.json",
                "backup_*.json"
            ]
        if self.exclude_patterns is None:
            self.exclude_patterns = [
                "temp_*",
                "cache_*",
                "*.tmp",
                "*.log"
            ]

@dataclass
class SyncState:
    """Current state of synchronization."""
    last_full_sync: Optional[datetime] = None
    pending_uploads: int = 0
    pending_downloads: int = 0
    total_files: int = 0
    synced_files: int = 0
    conflicts: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class CloudStorageManager:
    """Manages cloud storage synchronization."""
    
    def __init__(self, config: SyncConfiguration, data_dir: Path):
        self.config = config
        self.data_dir = Path(data_dir)
        self.sync_state = SyncState()
        self.files: Dict[str, SyncFile] = {}
        self.encryption_key = None
        self.is_syncing = False
        
        # Platform-specific cloud paths
        self.cloud_paths = self._get_cloud_paths()
        
        # Initialize encryption if enabled
        if self.config.encrypt_data:
            self._initialize_encryption()
    
    def _get_cloud_paths(self) -> Dict[CloudProvider, Optional[Path]]:
        """Get platform-specific cloud storage paths."""
        system = platform.system()
        home = Path.home()
        
        paths = {}
        
        if system == "Darwin":  # macOS
            # iCloud Drive path
            icloud_path = home / "Library/Mobile Documents/com~apple~CloudDocs"
            if icloud_path.exists():
                paths[CloudProvider.ICLOUD] = icloud_path / "Lexicon"
            
            # Google Drive path (common locations)
            google_paths = [
                home / "Google Drive" / "Lexicon",
                home / "GoogleDrive" / "Lexicon"
            ]
            for path in google_paths:
                if path.parent.exists():
                    paths[CloudProvider.GOOGLE_DRIVE] = path
                    break
            
            # OneDrive path for macOS
            onedrive_paths = [
                home / "OneDrive" / "Lexicon",
                home / "Library/CloudStorage/OneDrive-Personal" / "Lexicon",
                home / "Library/CloudStorage/OneDrive-Commercial" / "Lexicon"
            ]
            for path in onedrive_paths:
                if path.parent.exists():
                    paths[CloudProvider.ONEDRIVE] = path
                    break
        
        elif system == "Windows":
            # OneDrive paths for Windows
            onedrive_paths = [
                home / "OneDrive" / "Lexicon",
                home / "OneDrive - Personal" / "Lexicon",
                Path(os.environ.get("OneDrive", "")) / "Lexicon" if os.environ.get("OneDrive") else None
            ]
            for path in onedrive_paths:
                if path and path.parent.exists():
                    paths[CloudProvider.ONEDRIVE] = path
                    break
            
            # Google Drive path for Windows
            google_paths = [
                home / "Google Drive" / "Lexicon",
                home / "GoogleDrive" / "Lexicon"
            ]
            for path in google_paths:
                if path.parent.exists():
                    paths[CloudProvider.GOOGLE_DRIVE] = path
                    break
        
        elif system == "Linux":
            # Common Linux cloud sync paths
            google_path = home / "GoogleDrive" / "Lexicon"
            if google_path.parent.exists():
                paths[CloudProvider.GOOGLE_DRIVE] = google_path
            
            # OneDrive via rclone or insync
            onedrive_paths = [
                home / "OneDrive" / "Lexicon",
                home / "Cloud/OneDrive" / "Lexicon"
            ]
            for path in onedrive_paths:
                if path.parent.exists():
                    paths[CloudProvider.ONEDRIVE] = path
                    break
        
        return paths
    
    def _initialize_encryption(self):
        """Initialize encryption for sensitive data."""
        key_file = self.data_dir / ".sync_key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                self.encryption_key = f.read()
        else:
            # Generate new encryption key
            self.encryption_key = Fernet.generate_key()
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(self.encryption_key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
    
    def _encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data if encryption is enabled."""
        if not self.config.encrypt_data or not self.encryption_key:
            return data
        
        fernet = Fernet(self.encryption_key)
        return fernet.encrypt(data)
    
    def _decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt data if encryption is enabled."""
        if not self.config.encrypt_data or not self.encryption_key:
            return encrypted_data
        
        fernet = Fernet(self.encryption_key)
        return fernet.decrypt(encrypted_data)
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _should_sync_file(self, file_path: Path) -> bool:
        """Check if a file should be synced based on patterns."""
        relative_path = file_path.relative_to(self.data_dir)
        file_name = file_path.name
        
        # Check exclusion patterns first
        for pattern in self.config.exclude_patterns:
            if file_path.match(pattern) or relative_path.match(pattern):
                return False
        
        # Check inclusion patterns
        for pattern in self.config.sync_patterns:
            if file_path.match(pattern) or relative_path.match(pattern):
                return True
        
        return False
    
    async def scan_local_files(self) -> List[SyncFile]:
        """Scan local directory for files to sync."""
        local_files = []
        
        for file_path in self.data_dir.rglob("*"):
            if file_path.is_file() and self._should_sync_file(file_path):
                try:
                    stat = file_path.stat()
                    if stat.st_size > self.config.max_file_size:
                        continue
                    
                    relative_path = str(file_path.relative_to(self.data_dir))
                    checksum = self._calculate_checksum(file_path)
                    modified_time = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                    
                    sync_file = SyncFile(
                        path=relative_path,
                        checksum=checksum,
                        size=stat.st_size,
                        modified_time=modified_time,
                        sync_status=SyncStatus.NOT_SYNCED
                    )
                    
                    local_files.append(sync_file)
                    
                except (OSError, PermissionError) as e:
                    self.sync_state.errors.append(f"Error reading {file_path}: {str(e)}")
        
        return local_files
    
    async def get_cloud_path(self) -> Optional[Path]:
        """Get the appropriate cloud storage path."""
        return self.cloud_paths.get(self.config.provider)
    
    async def upload_file(self, sync_file: SyncFile) -> bool:
        """Upload a file to cloud storage."""
        try:
            cloud_path = await self.get_cloud_path()
            if not cloud_path:
                self.sync_state.errors.append(f"Cloud path not available for {self.config.provider.value}")
                return False
            
            local_file_path = self.data_dir / sync_file.path
            cloud_file_path = cloud_path / sync_file.path
            
            # Ensure cloud directory exists
            cloud_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read and potentially encrypt file data
            async with aiofiles.open(local_file_path, 'rb') as f:
                data = await f.read()
            
            if self.config.encrypt_data:
                data = self._encrypt_data(data)
            
            # Write to cloud storage
            async with aiofiles.open(cloud_file_path, 'wb') as f:
                await f.write(data)
            
            # Update sync file info
            sync_file.cloud_path = str(cloud_file_path)
            sync_file.sync_status = SyncStatus.SYNCED
            sync_file.last_sync_time = datetime.now(tz=timezone.utc)
            sync_file.provider = self.config.provider
            
            return True
            
        except Exception as e:
            self.sync_state.errors.append(f"Failed to upload {sync_file.path}: {str(e)}")
            sync_file.sync_status = SyncStatus.ERROR
            return False
    
    async def download_file(self, sync_file: SyncFile) -> bool:
        """Download a file from cloud storage."""
        try:
            if not sync_file.cloud_path:
                return False
            
            cloud_file_path = Path(sync_file.cloud_path)
            local_file_path = self.data_dir / sync_file.path
            
            # Ensure local directory exists
            local_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read from cloud storage
            async with aiofiles.open(cloud_file_path, 'rb') as f:
                data = await f.read()
            
            if self.config.encrypt_data:
                data = self._decrypt_data(data)
            
            # Write to local storage
            async with aiofiles.open(local_file_path, 'wb') as f:
                await f.write(data)
            
            # Update sync file info
            sync_file.sync_status = SyncStatus.SYNCED
            sync_file.last_sync_time = datetime.now(tz=timezone.utc)
            
            return True
            
        except Exception as e:
            self.sync_state.errors.append(f"Failed to download {sync_file.path}: {str(e)}")
            sync_file.sync_status = SyncStatus.ERROR
            return False
    
    async def detect_conflicts(self, local_files: List[SyncFile]) -> List[SyncFile]:
        """Detect conflicts between local and cloud files."""
        conflicts = []
        cloud_path = await self.get_cloud_path()
        
        if not cloud_path or not cloud_path.exists():
            return conflicts
        
        for local_file in local_files:
            cloud_file_path = cloud_path / local_file.path
            
            if cloud_file_path.exists():
                try:
                    cloud_stat = cloud_file_path.stat()
                    cloud_modified = datetime.fromtimestamp(cloud_stat.st_mtime, tz=timezone.utc)
                    
                    # Check if files are different
                    if cloud_modified > local_file.modified_time:
                        # Read cloud file and compare checksum
                        cloud_checksum = self._calculate_checksum(cloud_file_path)
                        if cloud_checksum != local_file.checksum:
                            local_file.sync_status = SyncStatus.CONFLICT
                            conflicts.append(local_file)
                    
                except (OSError, PermissionError) as e:
                    self.sync_state.errors.append(f"Error checking cloud file {cloud_file_path}: {str(e)}")
        
        return conflicts
    
    async def resolve_conflict(self, sync_file: SyncFile, resolution: ConflictResolution) -> bool:
        """Resolve a sync conflict."""
        try:
            if resolution == ConflictResolution.KEEP_LOCAL:
                return await self.upload_file(sync_file)
            
            elif resolution == ConflictResolution.KEEP_REMOTE:
                return await self.download_file(sync_file)
            
            elif resolution == ConflictResolution.MERGE:
                # For JSON files, attempt to merge
                if sync_file.path.endswith('.json'):
                    return await self._merge_json_files(sync_file)
                else:
                    # For non-JSON files, default to keeping remote
                    return await self.download_file(sync_file)
            
            elif resolution == ConflictResolution.ASK_USER:
                # This would typically involve UI interaction
                # For now, default to keeping local
                return await self.upload_file(sync_file)
            
            return False
            
        except Exception as e:
            self.sync_state.errors.append(f"Failed to resolve conflict for {sync_file.path}: {str(e)}")
            return False
    
    async def _merge_json_files(self, sync_file: SyncFile) -> bool:
        """Merge JSON files intelligently."""
        try:
            local_path = self.data_dir / sync_file.path
            cloud_path = Path(sync_file.cloud_path) if sync_file.cloud_path else None
            
            if not cloud_path or not cloud_path.exists():
                return False
            
            # Load both JSON files
            async with aiofiles.open(local_path, 'r', encoding='utf-8') as f:
                local_data = json.loads(await f.read())
            
            async with aiofiles.open(cloud_path, 'r', encoding='utf-8') as f:
                cloud_data = json.loads(await f.read())
            
            # Merge based on data structure
            if isinstance(local_data, list) and isinstance(cloud_data, list):
                # Merge lists by combining unique items
                merged_data = local_data.copy()
                for item in cloud_data:
                    if item not in merged_data:
                        merged_data.append(item)
            
            elif isinstance(local_data, dict) and isinstance(cloud_data, dict):
                # Merge dictionaries, keeping newer values
                merged_data = cloud_data.copy()
                merged_data.update(local_data)
            
            else:
                # Can't merge, keep local
                return await self.upload_file(sync_file)
            
            # Write merged data back to local file
            async with aiofiles.open(local_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(merged_data, indent=2, ensure_ascii=False))
            
            # Upload merged file
            return await self.upload_file(sync_file)
            
        except Exception as e:
            self.sync_state.errors.append(f"Failed to merge JSON file {sync_file.path}: {str(e)}")
            return False
    
    async def full_sync(self) -> SyncState:
        """Perform a full synchronization."""
        if self.is_syncing:
            return self.sync_state
        
        self.is_syncing = True
        self.sync_state = SyncState()
        
        try:
            print("🔄 Starting full synchronization...")
            
            # Scan local files
            print("📁 Scanning local files...")
            local_files = await self.scan_local_files()
            self.sync_state.total_files = len(local_files)
            
            # Detect conflicts
            print("⚠️  Detecting conflicts...")
            conflicts = await self.detect_conflicts(local_files)
            self.sync_state.conflicts = len(conflicts)
            
            # Resolve conflicts
            if conflicts:
                print(f"🔧 Resolving {len(conflicts)} conflicts...")
                for conflict_file in conflicts:
                    await self.resolve_conflict(conflict_file, self.config.conflict_resolution)
            
            # Upload pending files
            pending_uploads = [f for f in local_files if f.sync_status in [SyncStatus.NOT_SYNCED, SyncStatus.PENDING]]
            self.sync_state.pending_uploads = len(pending_uploads)
            
            if pending_uploads:
                print(f"⬆️  Uploading {len(pending_uploads)} files...")
                for sync_file in pending_uploads:
                    success = await self.upload_file(sync_file)
                    if success:
                        self.sync_state.synced_files += 1
            
            # Update sync state
            self.sync_state.last_full_sync = datetime.now(tz=timezone.utc)
            self.sync_state.synced_files = len([f for f in local_files if f.sync_status == SyncStatus.SYNCED])
            
            # Save sync state
            await self.save_sync_state()
            
            print(f"✅ Synchronization completed!")
            print(f"   📊 {self.sync_state.synced_files}/{self.sync_state.total_files} files synced")
            print(f"   ⚠️  {self.sync_state.conflicts} conflicts resolved")
            print(f"   ❌ {len(self.sync_state.errors)} errors")
            
        except Exception as e:
            self.sync_state.errors.append(f"Full sync failed: {str(e)}")
            print(f"❌ Synchronization failed: {str(e)}")
        
        finally:
            self.is_syncing = False
        
        return self.sync_state
    
    async def save_sync_state(self):
        """Save current sync state to disk."""
        state_file = self.data_dir / ".sync_state.json"
        
        state_data = {
            'sync_state': asdict(self.sync_state),
            'files': {path: asdict(sync_file) for path, sync_file in self.files.items()},
            'config': asdict(self.config)
        }
        
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, Enum):
                return obj.value
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        async with aiofiles.open(state_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(state_data, indent=2, default=json_serializer))
    
    async def load_sync_state(self):
        """Load sync state from disk."""
        state_file = self.data_dir / ".sync_state.json"
        
        if not state_file.exists():
            return
        
        try:
            async with aiofiles.open(state_file, 'r', encoding='utf-8') as f:
                state_data = json.loads(await f.read())
            
            # Restore sync state
            if 'sync_state' in state_data:
                sync_state_dict = state_data['sync_state']
                if 'last_full_sync' in sync_state_dict and sync_state_dict['last_full_sync']:
                    sync_state_dict['last_full_sync'] = datetime.fromisoformat(sync_state_dict['last_full_sync'])
                self.sync_state = SyncState(**sync_state_dict)
            
            # Restore file states
            if 'files' in state_data:
                for path, file_dict in state_data['files'].items():
                    if 'modified_time' in file_dict:
                        file_dict['modified_time'] = datetime.fromisoformat(file_dict['modified_time'])
                    if 'last_sync_time' in file_dict and file_dict['last_sync_time']:
                        file_dict['last_sync_time'] = datetime.fromisoformat(file_dict['last_sync_time'])
                    if 'sync_status' in file_dict:
                        file_dict['sync_status'] = SyncStatus(file_dict['sync_status'])
                    if 'provider' in file_dict and file_dict['provider']:
                        file_dict['provider'] = CloudProvider(file_dict['provider'])
                    
                    self.files[path] = SyncFile(**file_dict)
            
        except Exception as e:
            print(f"⚠️  Failed to load sync state: {str(e)}")
    
    async def start_auto_sync(self):
        """Start automatic synchronization background task."""
        if not self.config.enabled:
            return
        
        print(f"🔄 Starting auto-sync every {self.config.auto_sync_interval} seconds...")
        
        while self.config.enabled:
            try:
                await asyncio.sleep(self.config.auto_sync_interval)
                await self.full_sync()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️  Auto-sync error: {str(e)}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    def get_sync_stats(self) -> Dict[str, Any]:
        """Get current synchronization statistics."""
        return {
            'enabled': self.config.enabled,
            'provider': self.config.provider.value,
            'last_sync': self.sync_state.last_full_sync.isoformat() if self.sync_state.last_full_sync else None,
            'total_files': self.sync_state.total_files,
            'synced_files': self.sync_state.synced_files,
            'pending_uploads': self.sync_state.pending_uploads,
            'pending_downloads': self.sync_state.pending_downloads,
            'conflicts': self.sync_state.conflicts,
            'errors': len(self.sync_state.errors),
            'recent_errors': self.sync_state.errors[-5:] if self.sync_state.errors else []
        }

# Factory function for creating cloud storage manager
def create_cloud_storage_manager(data_dir: Path, provider: CloudProvider = CloudProvider.ICLOUD) -> CloudStorageManager:
    """Create a configured cloud storage manager."""
    config = SyncConfiguration(
        enabled=True,
        provider=provider,
        auto_sync_interval=300,  # 5 minutes
        conflict_resolution=ConflictResolution.ASK_USER,
        encrypt_data=True
    )
    
    return CloudStorageManager(config, data_dir)
