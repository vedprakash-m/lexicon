#!/usr/bin/env python3
"""
Backup and Restoration System for Lexicon
Handles automatic backups, manual backups, and restoration of catalog data
"""

import asyncio
import json
import zipfile
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles
import sqlite3
import hashlib

class BackupType(Enum):
    """Types of backups."""
    FULL = "full"
    INCREMENTAL = "incremental"
    MANUAL = "manual"
    AUTOMATIC = "automatic"

class BackupStatus(Enum):
    """Backup operation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRUPTED = "corrupted"

@dataclass
class BackupMetadata:
    """Metadata for a backup."""
    backup_id: str
    timestamp: datetime
    backup_type: BackupType
    status: BackupStatus
    file_path: str
    size_bytes: int
    checksum: str
    description: str
    files_included: List[str]
    version: str = "1.0"
    compressed: bool = True
    encrypted: bool = False

@dataclass
class BackupConfiguration:
    """Configuration for backup system."""
    enabled: bool = True
    automatic_interval: int = 3600  # seconds (1 hour)
    max_backups: int = 30
    backup_location: str = "backups"
    compress_backups: bool = True
    encrypt_backups: bool = False
    include_patterns: List[str] = None
    exclude_patterns: List[str] = None
    full_backup_interval: int = 86400  # seconds (24 hours)
    
    def __post_init__(self):
        if self.include_patterns is None:
            self.include_patterns = [
                "*.json",
                "*.db",
                "enrichment_*.json",
                "catalog_*.json",
                "relationship_*.json",
                "visual_asset_*.json"
            ]
        if self.exclude_patterns is None:
            self.exclude_patterns = [
                "temp_*",
                "cache_*",
                "*.tmp",
                "*.log",
                ".sync_*"
            ]

class BackupManager:
    """Manages backup and restoration operations."""
    
    def __init__(self, config: BackupConfiguration, data_dir: Path):
        self.config = config
        self.data_dir = Path(data_dir)
        self.backup_dir = self.data_dir / self.config.backup_location
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.backup_registry: Dict[str, BackupMetadata] = {}
        self.is_backing_up = False
        
        # Load existing backup registry
        asyncio.create_task(self.load_backup_registry())
    
    def _generate_backup_id(self) -> str:
        """Generate a unique backup ID."""
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"backup_{timestamp}"
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _should_include_file(self, file_path: Path) -> bool:
        """Check if a file should be included in backup."""
        relative_path = file_path.relative_to(self.data_dir)
        file_name = file_path.name
        
        # Check exclusion patterns first
        for pattern in self.config.exclude_patterns:
            if file_path.match(pattern) or relative_path.match(pattern):
                return False
        
        # Check inclusion patterns
        for pattern in self.config.include_patterns:
            if file_path.match(pattern) or relative_path.match(pattern):
                return True
        
        return False
    
    async def collect_files_for_backup(self) -> List[Path]:
        """Collect all files that should be included in backup."""
        files_to_backup = []
        
        for file_path in self.data_dir.rglob("*"):
            if file_path.is_file() and self._should_include_file(file_path):
                # Skip if it's in the backup directory
                if self.backup_dir in file_path.parents:
                    continue
                
                files_to_backup.append(file_path)
        
        return files_to_backup
    
    async def create_backup(
        self,
        backup_type: BackupType = BackupType.AUTOMATIC,
        description: str = "",
        files_to_include: Optional[List[Path]] = None
    ) -> Optional[BackupMetadata]:
        """Create a new backup."""
        
        if self.is_backing_up:
            print("⚠️  Backup already in progress")
            return None
        
        self.is_backing_up = True
        backup_id = self._generate_backup_id()
        
        try:
            print(f"📦 Creating {backup_type.value} backup: {backup_id}")
            
            # Collect files
            if files_to_include is None:
                files_to_backup = await self.collect_files_for_backup()
            else:
                files_to_backup = files_to_include
            
            if not files_to_backup:
                print("⚠️  No files to backup")
                return None
            
            # Create backup file path
            backup_filename = f"{backup_id}.zip" if self.config.compress_backups else backup_id
            backup_file_path = self.backup_dir / backup_filename
            
            # Create backup metadata
            backup_metadata = BackupMetadata(
                backup_id=backup_id,
                timestamp=datetime.now(tz=timezone.utc),
                backup_type=backup_type,
                status=BackupStatus.IN_PROGRESS,
                file_path=str(backup_file_path),
                size_bytes=0,
                checksum="",
                description=description or f"{backup_type.value.title()} backup",
                files_included=[str(f.relative_to(self.data_dir)) for f in files_to_backup],
                compressed=self.config.compress_backups,
                encrypted=self.config.encrypt_backups
            )
            
            # Create the backup
            if self.config.compress_backups:
                await self._create_zip_backup(files_to_backup, backup_file_path)
            else:
                await self._create_directory_backup(files_to_backup, backup_file_path)
            
            # Calculate final metadata
            backup_metadata.size_bytes = backup_file_path.stat().st_size
            backup_metadata.checksum = self._calculate_checksum(backup_file_path)
            backup_metadata.status = BackupStatus.COMPLETED
            
            # Add to registry
            self.backup_registry[backup_id] = backup_metadata
            await self.save_backup_registry()
            
            print(f"✅ Backup created successfully: {backup_id}")
            print(f"   📁 Files: {len(files_to_backup)}")
            print(f"   💾 Size: {backup_metadata.size_bytes / 1024 / 1024:.2f} MB")
            
            # Cleanup old backups
            await self.cleanup_old_backups()
            
            return backup_metadata
            
        except Exception as e:
            print(f"❌ Backup failed: {str(e)}")
            if backup_id in self.backup_registry:
                self.backup_registry[backup_id].status = BackupStatus.FAILED
                await self.save_backup_registry()
            return None
        
        finally:
            self.is_backing_up = False
    
    async def _create_zip_backup(self, files: List[Path], backup_path: Path):
        """Create a compressed ZIP backup."""
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files:
                relative_path = file_path.relative_to(self.data_dir)
                zipf.write(file_path, relative_path)
                print(f"   📄 Added: {relative_path}")
    
    async def _create_directory_backup(self, files: List[Path], backup_path: Path):
        """Create an uncompressed directory backup."""
        backup_path.mkdir(parents=True, exist_ok=True)
        
        for file_path in files:
            relative_path = file_path.relative_to(self.data_dir)
            target_path = backup_path / relative_path
            
            # Ensure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(file_path, target_path)
            print(f"   📄 Copied: {relative_path}")
    
    async def restore_backup(
        self,
        backup_id: str,
        target_dir: Optional[Path] = None,
        overwrite_existing: bool = False
    ) -> bool:
        """Restore a backup."""
        
        if backup_id not in self.backup_registry:
            print(f"❌ Backup not found: {backup_id}")
            return False
        
        backup_metadata = self.backup_registry[backup_id]
        backup_path = Path(backup_metadata.file_path)
        
        if not backup_path.exists():
            print(f"❌ Backup file missing: {backup_path}")
            backup_metadata.status = BackupStatus.CORRUPTED
            await self.save_backup_registry()
            return False
        
        # Verify backup integrity
        if not await self.verify_backup(backup_id):
            print(f"❌ Backup integrity check failed: {backup_id}")
            return False
        
        target_directory = target_dir or self.data_dir
        target_directory = Path(target_directory)
        
        try:
            print(f"🔄 Restoring backup: {backup_id}")
            print(f"   📁 Target: {target_directory}")
            
            if backup_metadata.compressed:
                await self._restore_zip_backup(backup_path, target_directory, overwrite_existing)
            else:
                await self._restore_directory_backup(backup_path, target_directory, overwrite_existing)
            
            print(f"✅ Backup restored successfully: {backup_id}")
            return True
            
        except Exception as e:
            print(f"❌ Restore failed: {str(e)}")
            return False
    
    async def _restore_zip_backup(self, backup_path: Path, target_dir: Path, overwrite: bool):
        """Restore from a ZIP backup."""
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            for file_info in zipf.filelist:
                target_file = target_dir / file_info.filename
                
                if target_file.exists() and not overwrite:
                    print(f"   ⏭️  Skipped (exists): {file_info.filename}")
                    continue
                
                # Ensure target directory exists
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Extract file
                zipf.extract(file_info, target_dir)
                print(f"   📄 Restored: {file_info.filename}")
    
    async def _restore_directory_backup(self, backup_path: Path, target_dir: Path, overwrite: bool):
        """Restore from a directory backup."""
        for file_path in backup_path.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(backup_path)
                target_file = target_dir / relative_path
                
                if target_file.exists() and not overwrite:
                    print(f"   ⏭️  Skipped (exists): {relative_path}")
                    continue
                
                # Ensure target directory exists
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(file_path, target_file)
                print(f"   📄 Restored: {relative_path}")
    
    async def verify_backup(self, backup_id: str) -> bool:
        """Verify backup integrity."""
        if backup_id not in self.backup_registry:
            return False
        
        backup_metadata = self.backup_registry[backup_id]
        backup_path = Path(backup_metadata.file_path)
        
        if not backup_path.exists():
            return False
        
        # Check file size
        current_size = backup_path.stat().st_size
        if current_size != backup_metadata.size_bytes:
            print(f"⚠️  Size mismatch for backup {backup_id}")
            return False
        
        # Check checksum
        current_checksum = self._calculate_checksum(backup_path)
        if current_checksum != backup_metadata.checksum:
            print(f"⚠️  Checksum mismatch for backup {backup_id}")
            return False
        
        return True
    
    async def list_backups(self) -> List[BackupMetadata]:
        """List all available backups."""
        return list(self.backup_registry.values())
    
    async def get_backup_info(self, backup_id: str) -> Optional[BackupMetadata]:
        """Get detailed information about a backup."""
        return self.backup_registry.get(backup_id)
    
    async def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup."""
        if backup_id not in self.backup_registry:
            return False
        
        backup_metadata = self.backup_registry[backup_id]
        backup_path = Path(backup_metadata.file_path)
        
        try:
            if backup_path.exists():
                if backup_path.is_file():
                    backup_path.unlink()
                else:
                    shutil.rmtree(backup_path)
            
            del self.backup_registry[backup_id]
            await self.save_backup_registry()
            
            print(f"🗑️  Deleted backup: {backup_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete backup {backup_id}: {str(e)}")
            return False
    
    async def cleanup_old_backups(self):
        """Remove old backups to maintain max_backups limit."""
        if len(self.backup_registry) <= self.config.max_backups:
            return
        
        # Sort backups by timestamp (oldest first)
        sorted_backups = sorted(
            self.backup_registry.values(),
            key=lambda b: b.timestamp
        )
        
        # Delete oldest backups
        backups_to_delete = len(sorted_backups) - self.config.max_backups
        for i in range(backups_to_delete):
            backup_to_delete = sorted_backups[i]
            await self.delete_backup(backup_to_delete.backup_id)
            print(f"🧹 Cleaned up old backup: {backup_to_delete.backup_id}")
    
    async def save_backup_registry(self):
        """Save backup registry to disk."""
        registry_file = self.backup_dir / "backup_registry.json"
        
        registry_data = {}
        for backup_id, metadata in self.backup_registry.items():
            registry_data[backup_id] = asdict(metadata)
        
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, Enum):
                return obj.value
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        async with aiofiles.open(registry_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(registry_data, indent=2, default=json_serializer))
    
    async def load_backup_registry(self):
        """Load backup registry from disk."""
        registry_file = self.backup_dir / "backup_registry.json"
        
        if not registry_file.exists():
            return
        
        try:
            async with aiofiles.open(registry_file, 'r', encoding='utf-8') as f:
                registry_data = json.loads(await f.read())
            
            for backup_id, metadata_dict in registry_data.items():
                # Convert datetime strings back to datetime objects
                if 'timestamp' in metadata_dict:
                    metadata_dict['timestamp'] = datetime.fromisoformat(metadata_dict['timestamp'])
                
                # Convert enum strings back to enum objects
                if 'backup_type' in metadata_dict:
                    metadata_dict['backup_type'] = BackupType(metadata_dict['backup_type'])
                if 'status' in metadata_dict:
                    metadata_dict['status'] = BackupStatus(metadata_dict['status'])
                
                self.backup_registry[backup_id] = BackupMetadata(**metadata_dict)
            
            print(f"📚 Loaded {len(self.backup_registry)} backup records")
            
        except Exception as e:
            print(f"⚠️  Failed to load backup registry: {str(e)}")
    
    async def start_automatic_backups(self):
        """Start automatic backup background task."""
        if not self.config.enabled:
            return
        
        print(f"⏰ Starting automatic backups every {self.config.automatic_interval} seconds...")
        
        last_full_backup = None
        
        while self.config.enabled:
            try:
                await asyncio.sleep(self.config.automatic_interval)
                
                # Determine backup type
                now = datetime.now(tz=timezone.utc)
                
                if (last_full_backup is None or 
                    (now - last_full_backup).total_seconds() >= self.config.full_backup_interval):
                    backup_type = BackupType.FULL
                    last_full_backup = now
                else:
                    backup_type = BackupType.INCREMENTAL
                
                # Create backup
                await self.create_backup(
                    backup_type=backup_type,
                    description=f"Automatic {backup_type.value} backup"
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️  Automatic backup error: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """Get backup system statistics."""
        backups = list(self.backup_registry.values())
        
        total_size = sum(b.size_bytes for b in backups)
        successful_backups = [b for b in backups if b.status == BackupStatus.COMPLETED]
        failed_backups = [b for b in backups if b.status == BackupStatus.FAILED]
        
        latest_backup = max(backups, key=lambda b: b.timestamp) if backups else None
        
        return {
            'enabled': self.config.enabled,
            'total_backups': len(backups),
            'successful_backups': len(successful_backups),
            'failed_backups': len(failed_backups),
            'total_size_mb': total_size / 1024 / 1024,
            'latest_backup': {
                'id': latest_backup.backup_id,
                'timestamp': latest_backup.timestamp.isoformat(),
                'type': latest_backup.backup_type.value,
                'status': latest_backup.status.value,
                'size_mb': latest_backup.size_bytes / 1024 / 1024
            } if latest_backup else None,
            'backup_types': {
                backup_type.value: len([b for b in backups if b.backup_type == backup_type])
                for backup_type in BackupType
            }
        }

# Factory function for creating backup manager
def create_backup_manager(data_dir: Path) -> BackupManager:
    """Create a configured backup manager."""
    config = BackupConfiguration(
        enabled=True,
        automatic_interval=3600,  # 1 hour
        max_backups=30,
        compress_backups=True,
        encrypt_backups=False
    )
    
    return BackupManager(config, data_dir)
