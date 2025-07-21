"""
Comprehensive Backup and Restore System for Lexicon
Provides automated backups, data safety, and disaster recovery capabilities
"""

import asyncio
import json
import shutil
import sqlite3
import zipfile
import logging
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
import schedule

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupType(Enum):
    """Types of backups"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"

class BackupStatus(Enum):
    """Backup operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RestoreStatus(Enum):
    """Restore operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class BackupConfig:
    """Configuration for backup operations"""
    backup_id: str
    backup_type: BackupType
    source_paths: List[str]
    destination_path: str
    compression_level: int = 6  # 0-9, higher is more compression
    encryption_enabled: bool = False
    encryption_key: Optional[str] = None
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    verify_backup: bool = True
    retention_days: int = 30
    schedule_expression: Optional[str] = None  # Cron-like expression
    
    def __post_init__(self):
        if not self.include_patterns:
            self.include_patterns = ["*"]

@dataclass
class BackupMetadata:
    """Metadata for a backup"""
    backup_id: str
    backup_type: BackupType
    created_at: datetime
    completed_at: Optional[datetime] = None
    status: BackupStatus = BackupStatus.PENDING
    source_paths: List[str] = field(default_factory=list)
    backup_path: str = ""
    file_count: int = 0
    total_size: int = 0
    compressed_size: int = 0
    checksum: str = ""
    version: str = "1.0"
    parent_backup_id: Optional[str] = None  # For incremental backups
    error_message: Optional[str] = None
    verification_passed: bool = False
    retention_until: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)

@dataclass
class RestoreConfig:
    """Configuration for restore operations"""
    restore_id: str
    backup_id: str
    backup_path: str
    destination_path: str
    selective_restore: bool = False
    selected_files: List[str] = field(default_factory=list)
    overwrite_existing: bool = False
    verify_restore: bool = True
    restore_permissions: bool = True

@dataclass
class RestoreResult:
    """Result of a restore operation"""
    restore_id: str
    backup_id: str
    status: RestoreStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    restored_files: int = 0
    total_files: int = 0
    restored_size: int = 0
    error_message: Optional[str] = None
    verification_passed: bool = False
    warnings: List[str] = field(default_factory=list)

class BackupScheduler:
    """Handles scheduled backup operations"""
    
    def __init__(self, backup_manager):
        self.backup_manager = backup_manager
        self.scheduled_jobs = {}
        self.scheduler_running = False
        self.scheduler_thread = None
    
    def add_scheduled_backup(self, config: BackupConfig):
        """Add a scheduled backup job"""
        if not config.schedule_expression:
            return
        
        job_id = f"scheduled_{config.backup_id}"
        
        # Parse simple schedule expressions (for demo - extend for full cron support)
        if config.schedule_expression.startswith("every "):
            parts = config.schedule_expression.split()
            if len(parts) >= 2:
                interval = parts[1]
                if interval.endswith("h"):
                    hours = int(interval[:-1])
                    schedule.every(hours).hours.do(self._run_scheduled_backup, config)
                elif interval.endswith("d"):
                    days = int(interval[:-1])
                    schedule.every(days).days.do(self._run_scheduled_backup, config)
        
        self.scheduled_jobs[job_id] = config
        logger.info(f"Scheduled backup job added: {job_id}")
    
    def _run_scheduled_backup(self, config: BackupConfig):
        """Run a scheduled backup"""
        try:
            asyncio.create_task(self.backup_manager.create_backup(config))
        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")
    
    def start_scheduler(self):
        """Start the backup scheduler"""
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Backup scheduler started")
    
    def stop_scheduler(self):
        """Stop the backup scheduler"""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logger.info("Backup scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

class BackupManager:
    """Comprehensive backup and restore manager"""
    
    def __init__(self, base_backup_dir: Path = Path("backups")):
        self.base_backup_dir = Path(base_backup_dir)
        self.base_backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Database for backup metadata
        self.metadata_db_path = self.base_backup_dir / "backup_metadata.db"
        self._init_metadata_database()
        
        # Active operations tracking
        self.active_backups: Dict[str, BackupMetadata] = {}
        self.active_restores: Dict[str, RestoreResult] = {}
        
        # Progress callbacks
        self.backup_callbacks: Dict[str, List[Callable]] = {}
        self.restore_callbacks: Dict[str, List[Callable]] = {}
        
        # Thread pool for concurrent operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Scheduler
        self.scheduler = BackupScheduler(self)
        
        # Statistics
        self.stats = {
            "total_backups_created": 0,
            "total_restores_performed": 0,
            "total_data_backed_up": 0,
            "average_backup_time": 0,
            "success_rate": 0.0
        }
        
        logger.info("Backup manager initialized")
    
    def _init_metadata_database(self):
        """Initialize SQLite database for backup metadata"""
        try:
            with sqlite3.connect(self.metadata_db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS backup_metadata (
                        backup_id TEXT PRIMARY KEY,
                        backup_type TEXT,
                        created_at TEXT,
                        completed_at TEXT,
                        status TEXT,
                        source_paths TEXT,
                        backup_path TEXT,
                        file_count INTEGER,
                        total_size INTEGER,
                        compressed_size INTEGER,
                        checksum TEXT,
                        version TEXT,
                        parent_backup_id TEXT,
                        error_message TEXT,
                        verification_passed BOOLEAN,
                        retention_until TEXT,
                        tags TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS restore_history (
                        restore_id TEXT PRIMARY KEY,
                        backup_id TEXT,
                        status TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        restored_files INTEGER,
                        total_files INTEGER,
                        restored_size INTEGER,
                        error_message TEXT,
                        verification_passed BOOLEAN,
                        warnings TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_backup_created_at ON backup_metadata(created_at)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_backup_type ON backup_metadata(backup_type)
                """)
                
        except Exception as e:
            logger.error(f"Failed to initialize metadata database: {e}")
    
    async def create_backup(self, config: BackupConfig) -> BackupMetadata:
        """Create a new backup"""
        backup_metadata = BackupMetadata(
            backup_id=config.backup_id,
            backup_type=config.backup_type,
            created_at=datetime.now(),
            source_paths=config.source_paths,
            backup_path=str(self.base_backup_dir / f"{config.backup_id}.zip"),
            retention_until=datetime.now() + timedelta(days=config.retention_days)
        )
        
        self.active_backups[config.backup_id] = backup_metadata
        
        try:
            backup_metadata.status = BackupStatus.IN_PROGRESS
            await self._persist_backup_metadata(backup_metadata)
            
            # Perform the backup operation
            await self._execute_backup(config, backup_metadata)
            
            # Verify backup if requested
            if config.verify_backup:
                backup_metadata.verification_passed = await self._verify_backup(backup_metadata.backup_path)
            
            backup_metadata.status = BackupStatus.COMPLETED
            backup_metadata.completed_at = datetime.now()
            
            # Update statistics
            self.stats["total_backups_created"] += 1
            self.stats["total_data_backed_up"] += backup_metadata.total_size
            
            logger.info(f"Backup {config.backup_id} completed successfully")
            
        except Exception as e:
            backup_metadata.status = BackupStatus.FAILED
            backup_metadata.error_message = str(e)
            logger.error(f"Backup {config.backup_id} failed: {e}")
        
        finally:
            await self._persist_backup_metadata(backup_metadata)
            # Keep in active backups for monitoring, will be cleaned up later
        
        return backup_metadata
    
    async def _execute_backup(self, config: BackupConfig, metadata: BackupMetadata):
        """Execute the actual backup operation"""
        backup_path = Path(metadata.backup_path)
        temp_backup_path = backup_path.with_suffix('.tmp')
        
        file_count = 0
        total_size = 0
        
        with zipfile.ZipFile(temp_backup_path, 'w', 
                           compression=zipfile.ZIP_DEFLATED,
                           compresslevel=config.compression_level) as zipf:
            
            for source_path in config.source_paths:
                source = Path(source_path)
                
                if source.is_file():
                    if self._should_include_file(source, config):
                        zipf.write(source, source.name)
                        file_count += 1
                        total_size += source.stat().st_size
                        
                elif source.is_dir():
                    for file_path in source.rglob('*'):
                        if file_path.is_file() and self._should_include_file(file_path, config):
                            # Calculate relative path
                            rel_path = file_path.relative_to(source.parent)
                            zipf.write(file_path, str(rel_path))
                            file_count += 1
                            total_size += file_path.stat().st_size
                            
                            # Notify progress
                            await self._notify_backup_progress(config.backup_id, file_count, total_size)
        
        # Move temp file to final location
        temp_backup_path.rename(backup_path)
        
        # Calculate checksums
        metadata.checksum = self._calculate_file_checksum(backup_path)
        metadata.file_count = file_count
        metadata.total_size = total_size
        metadata.compressed_size = backup_path.stat().st_size
        
        logger.info(f"Backup created: {file_count} files, {total_size} bytes -> {metadata.compressed_size} bytes")
    
    def _should_include_file(self, file_path: Path, config: BackupConfig) -> bool:
        """Determine if a file should be included in the backup"""
        # Check file size limit
        if file_path.stat().st_size > config.max_file_size:
            return False
        
        # Check include patterns
        included = False
        for pattern in config.include_patterns:
            if file_path.match(pattern):
                included = True
                break
        
        if not included:
            return False
        
        # Check exclude patterns
        for pattern in config.exclude_patterns:
            if file_path.match(pattern):
                return False
        
        return True
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    async def _verify_backup(self, backup_path: str) -> bool:
        """Verify the integrity of a backup"""
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Test the ZIP file
                result = zipf.testzip()
                if result is not None:
                    logger.error(f"Backup verification failed: corrupt file {result}")
                    return False
                
                # Verify all files can be read
                for info in zipf.filelist:
                    try:
                        with zipf.open(info) as f:
                            # Read first 1KB to verify readability
                            f.read(1024)
                    except Exception as e:
                        logger.error(f"Backup verification failed: cannot read {info.filename}: {e}")
                        return False
                
                logger.info(f"Backup verification passed: {backup_path}")
                return True
                
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False
    
    async def restore_backup(self, config: RestoreConfig) -> RestoreResult:
        """Restore from a backup"""
        restore_result = RestoreResult(
            restore_id=config.restore_id,
            backup_id=config.backup_id,
            status=RestoreStatus.PENDING,
            start_time=datetime.now()
        )
        
        self.active_restores[config.restore_id] = restore_result
        
        try:
            restore_result.status = RestoreStatus.IN_PROGRESS
            await self._persist_restore_history(restore_result)
            
            # Perform the restore operation
            await self._execute_restore(config, restore_result)
            
            # Verify restore if requested
            if config.verify_restore:
                restore_result.verification_passed = await self._verify_restore(config, restore_result)
            
            restore_result.status = RestoreStatus.COMPLETED
            restore_result.end_time = datetime.now()
            
            # Update statistics
            self.stats["total_restores_performed"] += 1
            
            logger.info(f"Restore {config.restore_id} completed successfully")
            
        except Exception as e:
            restore_result.status = RestoreStatus.FAILED
            restore_result.error_message = str(e)
            logger.error(f"Restore {config.restore_id} failed: {e}")
        
        finally:
            await self._persist_restore_history(restore_result)
        
        return restore_result
    
    async def _execute_restore(self, config: RestoreConfig, result: RestoreResult):
        """Execute the actual restore operation"""
        backup_path = Path(config.backup_path)
        destination = Path(config.destination_path)
        
        # Ensure destination exists
        destination.mkdir(parents=True, exist_ok=True)
        
        restored_files = 0
        restored_size = 0
        
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            # Get list of files to restore
            files_to_restore = zipf.filelist
            if config.selective_restore and config.selected_files:
                files_to_restore = [f for f in files_to_restore if f.filename in config.selected_files]
            
            result.total_files = len(files_to_restore)
            
            for file_info in files_to_restore:
                target_path = destination / file_info.filename
                
                # Check if file exists and handle overwrite
                if target_path.exists() and not config.overwrite_existing:
                    result.warnings.append(f"Skipped existing file: {file_info.filename}")
                    continue
                
                # Create parent directories
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Extract file
                with zipf.open(file_info) as source, open(target_path, 'wb') as target:
                    shutil.copyfileobj(source, target)
                
                # Restore permissions if requested
                if config.restore_permissions:
                    # Note: ZIP format has limited permission info
                    pass
                
                restored_files += 1
                restored_size += file_info.file_size
                
                # Notify progress
                await self._notify_restore_progress(config.restore_id, restored_files, result.total_files)
        
        result.restored_files = restored_files
        result.restored_size = restored_size
        
        logger.info(f"Restore completed: {restored_files} files, {restored_size} bytes")
    
    async def _verify_restore(self, config: RestoreConfig, result: RestoreResult) -> bool:
        """Verify the restored files"""
        try:
            destination = Path(config.destination_path)
            
            # Check if all files were restored
            with zipfile.ZipFile(config.backup_path, 'r') as zipf:
                for file_info in zipf.filelist:
                    if config.selective_restore and file_info.filename not in config.selected_files:
                        continue
                    
                    restored_file = destination / file_info.filename
                    if not restored_file.exists():
                        logger.error(f"Restore verification failed: missing file {file_info.filename}")
                        return False
                    
                    # Check file size
                    if restored_file.stat().st_size != file_info.file_size:
                        logger.error(f"Restore verification failed: size mismatch for {file_info.filename}")
                        return False
            
            logger.info("Restore verification passed")
            return True
            
        except Exception as e:
            logger.error(f"Restore verification failed: {e}")
            return False
    
    async def _persist_backup_metadata(self, metadata: BackupMetadata):
        """Persist backup metadata to database"""
        try:
            with sqlite3.connect(self.metadata_db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO backup_metadata (
                        backup_id, backup_type, created_at, completed_at, status,
                        source_paths, backup_path, file_count, total_size, compressed_size,
                        checksum, version, parent_backup_id, error_message,
                        verification_passed, retention_until, tags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metadata.backup_id,
                    metadata.backup_type.value,
                    metadata.created_at.isoformat(),
                    metadata.completed_at.isoformat() if metadata.completed_at else None,
                    metadata.status.value,
                    json.dumps(metadata.source_paths),
                    metadata.backup_path,
                    metadata.file_count,
                    metadata.total_size,
                    metadata.compressed_size,
                    metadata.checksum,
                    metadata.version,
                    metadata.parent_backup_id,
                    metadata.error_message,
                    metadata.verification_passed,
                    metadata.retention_until.isoformat() if metadata.retention_until else None,
                    json.dumps(metadata.tags)
                ))
        except Exception as e:
            logger.error(f"Failed to persist backup metadata: {e}")
    
    async def _persist_restore_history(self, result: RestoreResult):
        """Persist restore history to database"""
        try:
            with sqlite3.connect(self.metadata_db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO restore_history (
                        restore_id, backup_id, status, start_time, end_time,
                        restored_files, total_files, restored_size, error_message,
                        verification_passed, warnings
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.restore_id,
                    result.backup_id,
                    result.status.value,
                    result.start_time.isoformat(),
                    result.end_time.isoformat() if result.end_time else None,
                    result.restored_files,
                    result.total_files,
                    result.restored_size,
                    result.error_message,
                    result.verification_passed,
                    json.dumps(result.warnings)
                ))
        except Exception as e:
            logger.error(f"Failed to persist restore history: {e}")
    
    async def _notify_backup_progress(self, backup_id: str, files_processed: int, bytes_processed: int):
        """Notify backup progress callbacks"""
        if backup_id in self.backup_callbacks:
            for callback in self.backup_callbacks[backup_id]:
                try:
                    callback(backup_id, files_processed, bytes_processed)
                except Exception as e:
                    logger.error(f"Backup progress callback error: {e}")
    
    async def _notify_restore_progress(self, restore_id: str, files_restored: int, total_files: int):
        """Notify restore progress callbacks"""
        if restore_id in self.restore_callbacks:
            for callback in self.restore_callbacks[restore_id]:
                try:
                    callback(restore_id, files_restored, total_files)
                except Exception as e:
                    logger.error(f"Restore progress callback error: {e}")
    
    def add_backup_progress_callback(self, backup_id: str, callback: Callable):
        """Add a progress callback for a backup"""
        if backup_id not in self.backup_callbacks:
            self.backup_callbacks[backup_id] = []
        self.backup_callbacks[backup_id].append(callback)
    
    def add_restore_progress_callback(self, restore_id: str, callback: Callable):
        """Add a progress callback for a restore"""
        if restore_id not in self.restore_callbacks:
            self.restore_callbacks[restore_id] = []
        self.restore_callbacks[restore_id].append(callback)
    
    def list_backups(self, backup_type: Optional[BackupType] = None) -> List[BackupMetadata]:
        """List all available backups"""
        backups = []
        
        try:
            with sqlite3.connect(self.metadata_db_path) as conn:
                query = "SELECT * FROM backup_metadata"
                params = []
                
                if backup_type:
                    query += " WHERE backup_type = ?"
                    params.append(backup_type.value)
                
                query += " ORDER BY created_at DESC"
                
                cursor = conn.execute(query, params)
                for row in cursor.fetchall():
                    backup = BackupMetadata(
                        backup_id=row[0],
                        backup_type=BackupType(row[1]),
                        created_at=datetime.fromisoformat(row[2]),
                        completed_at=datetime.fromisoformat(row[3]) if row[3] else None,
                        status=BackupStatus(row[4]),
                        source_paths=json.loads(row[5]),
                        backup_path=row[6],
                        file_count=row[7],
                        total_size=row[8],
                        compressed_size=row[9],
                        checksum=row[10],
                        version=row[11],
                        parent_backup_id=row[12],
                        error_message=row[13],
                        verification_passed=bool(row[14]),
                        retention_until=datetime.fromisoformat(row[15]) if row[15] else None,
                        tags=json.loads(row[16])
                    )
                    backups.append(backup)
        
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
        
        return backups
    
    def get_backup_metadata(self, backup_id: str) -> Optional[BackupMetadata]:
        """Get metadata for a specific backup"""
        backups = self.list_backups()
        for backup in backups:
            if backup.backup_id == backup_id:
                return backup
        return None
    
    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup and its metadata"""
        try:
            metadata = self.get_backup_metadata(backup_id)
            if not metadata:
                return False
            
            # Delete backup file
            backup_path = Path(metadata.backup_path)
            if backup_path.exists():
                backup_path.unlink()
            
            # Delete metadata
            with sqlite3.connect(self.metadata_db_path) as conn:
                conn.execute("DELETE FROM backup_metadata WHERE backup_id = ?", (backup_id,))
            
            logger.info(f"Deleted backup {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete backup {backup_id}: {e}")
            return False
    
    def cleanup_expired_backups(self) -> int:
        """Clean up expired backups based on retention policy"""
        now = datetime.now()
        deleted_count = 0
        
        backups = self.list_backups()
        for backup in backups:
            if backup.retention_until and backup.retention_until < now:
                if self.delete_backup(backup.backup_id):
                    deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} expired backups")
        return deleted_count
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """Get comprehensive backup statistics"""
        backups = self.list_backups()
        
        stats = {
            "total_backups": len(backups),
            "successful_backups": len([b for b in backups if b.status == BackupStatus.COMPLETED]),
            "failed_backups": len([b for b in backups if b.status == BackupStatus.FAILED]),
            "total_backup_size": sum(b.compressed_size for b in backups),
            "average_compression_ratio": 0.0,
            "backups_by_type": {},
            "oldest_backup": None,
            "newest_backup": None,
            "retention_compliance": 0.0
        }
        
        if backups:
            # Compression ratio
            total_original = sum(b.total_size for b in backups if b.total_size > 0)
            total_compressed = sum(b.compressed_size for b in backups if b.compressed_size > 0)
            if total_original > 0:
                stats["average_compression_ratio"] = total_compressed / total_original
            
            # By type
            for backup in backups:
                backup_type = backup.backup_type.value
                stats["backups_by_type"][backup_type] = stats["backups_by_type"].get(backup_type, 0) + 1
            
            # Oldest and newest
            sorted_backups = sorted(backups, key=lambda x: x.created_at)
            stats["oldest_backup"] = sorted_backups[0].created_at.isoformat()
            stats["newest_backup"] = sorted_backups[-1].created_at.isoformat()
            
            # Retention compliance
            now = datetime.now()
            within_retention = len([b for b in backups if not b.retention_until or b.retention_until >= now])
            stats["retention_compliance"] = within_retention / len(backups)
        
        return stats
    
    def start_scheduler(self):
        """Start the backup scheduler"""
        self.scheduler.start_scheduler()
    
    def stop_scheduler(self):
        """Stop the backup scheduler"""
        self.scheduler.stop_scheduler()
    
    def schedule_backup(self, config: BackupConfig):
        """Schedule a recurring backup"""
        self.scheduler.add_scheduled_backup(config)

# Global backup manager instance
_backup_manager: Optional[BackupManager] = None

def get_backup_manager() -> BackupManager:
    """Get or create the global backup manager instance"""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager

# Demo function
async def demo_backup_system():
    """Demonstrate the backup and restore system"""
    print("=== Backup and Restore System Demo ===")
    
    backup_manager = get_backup_manager()
    
    # Create a test backup configuration
    backup_config = BackupConfig(
        backup_id="demo_backup_001",
        backup_type=BackupType.FULL,
        source_paths=["data/sample"],
        destination_path="backups",
        compression_level=6,
        include_patterns=["*.txt", "*.json"],
        exclude_patterns=["*.tmp"],
        retention_days=7
    )
    
    print(f"Creating backup: {backup_config.backup_id}")
    
    # Add progress callback
    def backup_progress(backup_id: str, files: int, bytes_processed: int):
        print(f"Backup progress: {files} files, {bytes_processed} bytes")
    
    backup_manager.add_backup_progress_callback(backup_config.backup_id, backup_progress)
    
    # Create backup
    backup_metadata = await backup_manager.create_backup(backup_config)
    
    print(f"Backup status: {backup_metadata.status}")
    print(f"Files backed up: {backup_metadata.file_count}")
    print(f"Original size: {backup_metadata.total_size} bytes")
    print(f"Compressed size: {backup_metadata.compressed_size} bytes")
    print(f"Compression ratio: {backup_metadata.compressed_size / backup_metadata.total_size:.2%}")
    
    # List all backups
    backups = backup_manager.list_backups()
    print(f"\nTotal backups: {len(backups)}")
    
    # Test restore
    if backup_metadata.status == BackupStatus.COMPLETED:
        restore_config = RestoreConfig(
            restore_id="demo_restore_001",
            backup_id=backup_metadata.backup_id,
            backup_path=backup_metadata.backup_path,
            destination_path="restored_data",
            overwrite_existing=True,
            verify_restore=True
        )
        
        print(f"\nRestoring backup: {restore_config.backup_id}")
        
        # Add progress callback
        def restore_progress(restore_id: str, files: int, total: int):
            print(f"Restore progress: {files}/{total} files")
        
        backup_manager.add_restore_progress_callback(restore_config.restore_id, restore_progress)
        
        # Perform restore
        restore_result = await backup_manager.restore_backup(restore_config)
        
        print(f"Restore status: {restore_result.status}")
        print(f"Files restored: {restore_result.restored_files}")
        print(f"Verification passed: {restore_result.verification_passed}")
    
    # Show statistics
    stats = backup_manager.get_backup_statistics()
    print(f"\nBackup Statistics:")
    print(f"Total backups: {stats['total_backups']}")
    print(f"Success rate: {stats['successful_backups'] / stats['total_backups']:.2%}")
    print(f"Average compression: {stats['average_compression_ratio']:.2%}")

if __name__ == "__main__":
    asyncio.run(demo_backup_system())
