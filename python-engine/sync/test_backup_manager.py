#!/usr/bin/env python3
"""
Tests for Backup Manager System
"""

import pytest
import asyncio
import tempfile
import json
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

# Import the modules to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backup_manager import (
    BackupType, BackupStatus, BackupMetadata, BackupConfiguration,
    BackupManager, create_backup_manager
)

class TestBackupType:
    def test_backup_type_enum(self):
        """Test BackupType enum values"""
        assert BackupType.MANUAL.value == "manual"
        assert BackupType.AUTOMATIC.value == "automatic"
        assert BackupType.FULL.value == "full"
        assert BackupType.INCREMENTAL.value == "incremental"

class TestBackupStatus:
    def test_backup_status_enum(self):
        """Test BackupStatus enum values"""
        assert BackupStatus.PENDING.value == "pending"
        assert BackupStatus.IN_PROGRESS.value == "in_progress"
        assert BackupStatus.COMPLETED.value == "completed"
        assert BackupStatus.FAILED.value == "failed"
        assert BackupStatus.CORRUPTED.value == "corrupted"

class TestBackupConfiguration:
    def test_default_backup_configuration(self):
        """Test BackupConfiguration with default values"""
        config = BackupConfiguration()
        
        assert config.enabled is True
        assert config.automatic_interval == 3600
        assert config.max_backups == 30
        assert config.compress_backups is True
        assert config.encrypt_backups is False
        assert "*.db" in config.include_patterns
        assert "*.json" in config.include_patterns
        assert "*.tmp" in config.exclude_patterns
        assert "*.log" in config.exclude_patterns

    def test_custom_backup_configuration(self):
        """Test BackupConfiguration with custom values"""
        config = BackupConfiguration(
            enabled=False,
            automatic_interval=7200,
            max_backups=50,
            compress_backups=False,
            encrypt_backups=True,
            include_patterns=["*.custom"],
            exclude_patterns=["*.exclude"]
        )
        
        assert config.enabled is False
        assert config.automatic_interval == 7200
        assert config.max_backups == 50
        assert config.compress_backups is False
        assert config.encrypt_backups is True
        assert config.include_patterns == ["*.custom"]
        assert config.exclude_patterns == ["*.exclude"]

class TestBackupMetadata:
    def test_backup_metadata_creation(self):
        """Test BackupMetadata dataclass"""
        now = datetime.now(timezone.utc)
        metadata = BackupMetadata(
            backup_id="test-backup-001",
            backup_type=BackupType.MANUAL,
            timestamp=now,
            status=BackupStatus.COMPLETED,
            size_bytes=1024000,
            files_included=["file1.db", "file2.json"],
            description="Test backup",
            checksum="abc123"
        )
        
        assert metadata.backup_id == "test-backup-001"
        assert metadata.backup_type == BackupType.MANUAL
        assert metadata.status == BackupStatus.COMPLETED
        assert metadata.size_bytes == 1024000
        assert len(metadata.files_included) == 2
        assert metadata.description == "Test backup"
        assert metadata.checksum == "abc123"

class TestBackupManager:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def backup_config(self):
        """Create a test backup configuration"""
        return BackupConfiguration(
            include_patterns=["*.db", "*.json"],
            exclude_patterns=["*.tmp", "*.log"]
        )

    @pytest.fixture
    def backup_manager(self, temp_dir, backup_config):
        """Create a BackupManager instance for testing"""
        return BackupManager(backup_config, temp_dir)

    def test_backup_manager_initialization(self, backup_manager, backup_config):
        """Test BackupManager initialization"""
        assert backup_manager.config == backup_config
        assert isinstance(backup_manager.backup_dir, Path)
        assert backup_manager.backup_dir.exists()
        assert backup_manager.is_backing_up is False

    def test_should_include_file(self, backup_manager, temp_dir):
        """Test file inclusion pattern matching"""
        # Create test files
        db_file = temp_dir / "test.db"
        json_file = temp_dir / "config.json"
        tmp_file = temp_dir / "temp.tmp"
        log_file = temp_dir / "app.log"
        
        # Test inclusion patterns
        assert backup_manager._should_include_file(db_file)
        assert backup_manager._should_include_file(json_file)
        
        # Test exclusion patterns
        assert not backup_manager._should_include_file(tmp_file)
        assert not backup_manager._should_include_file(log_file)

    @pytest.mark.asyncio
    async def test_collect_files_for_backup(self, backup_manager, temp_dir):
        """Test collecting files for backup"""
        # Create test files
        db_file = temp_dir / "lexicon.db"
        db_file.write_text("test database content")
        
        json_file = temp_dir / "config.json"
        json_file.write_text('{"test": "config"}')
        
        tmp_file = temp_dir / "temp.tmp"
        tmp_file.write_text("temporary content")
        
        # Collect files
        files = await backup_manager.collect_files_for_backup()
        
        # Should find db and json files, but not tmp file
        file_names = [f.name for f in files]
        assert "lexicon.db" in file_names
        assert "config.json" in file_names
        assert "temp.tmp" not in file_names

    def test_generate_backup_id(self, backup_manager):
        """Test backup ID generation"""
        backup_id = backup_manager._generate_backup_id()
        
        # Should start with backup_
        assert backup_id.startswith("backup_")
        
        # Should be unique
        backup_id2 = backup_manager._generate_backup_id()
        assert backup_id != backup_id2

    def test_calculate_file_checksum(self, backup_manager, temp_dir):
        """Test file checksum calculation"""
        test_file = temp_dir / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)
        
        checksum = backup_manager._calculate_checksum(test_file)
        
        # Should return a SHA256 hash
        assert len(checksum) == 64
        assert isinstance(checksum, str)
        
        # Same content should produce same checksum
        checksum2 = backup_manager._calculate_checksum(test_file)
        assert checksum == checksum2

    @pytest.mark.asyncio
    async def test_create_manual_backup(self, backup_manager, temp_dir):
        """Test creating a manual backup"""
        # Create test files
        db_file = temp_dir / "test.db"
        db_file.write_text("test database")
        
        json_file = temp_dir / "metadata.json"
        json_file.write_text('{"test": true}')
        
        # Create backup
        backup_metadata = await backup_manager.create_backup(
            backup_type=BackupType.MANUAL,
            description="Test manual backup"
        )
        
        # Verify backup was created
        assert backup_metadata is not None
        assert backup_metadata.backup_type == BackupType.MANUAL
        assert backup_metadata.status == BackupStatus.COMPLETED
        assert backup_metadata.description == "Test manual backup"
        assert len(backup_metadata.files_included) >= 1
        
        # Verify backup file exists
        backup_file = Path(backup_metadata.file_path)
        assert backup_file.exists()

    @pytest.mark.asyncio
    async def test_verify_backup(self, backup_manager, temp_dir):
        """Test backup verification"""
        # Create test file and backup
        test_file = temp_dir / "verify_test.json"
        test_file.write_text('{"verify": true}')
        
        backup_metadata = await backup_manager.create_backup(
            backup_type=BackupType.MANUAL,
            description="Verification test backup"
        )
        
        # Verify the backup
        is_valid = await backup_manager.verify_backup(backup_metadata.backup_id)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_list_backups(self, backup_manager, temp_dir):
        """Test listing backups"""
        # Create test file
        test_file = temp_dir / "list_test.json"
        test_file.write_text('{"list": true}')
        
        # Create backup
        backup_metadata = await backup_manager.create_backup(
            backup_type=BackupType.MANUAL,
            description="List test backup"
        )
        
        # List backups
        backups = await backup_manager.list_backups()
        
        # Should have at least one backup
        assert len(backups) >= 1
        
        backup_ids = [b.backup_id for b in backups]
        assert backup_metadata.backup_id in backup_ids

    @pytest.mark.asyncio
    async def test_delete_backup(self, backup_manager, temp_dir):
        """Test deleting a backup"""
        # Create test file and backup
        test_file = temp_dir / "delete_test.json"
        test_file.write_text('{"delete": true}')
        
        backup_metadata = await backup_manager.create_backup(
            backup_type=BackupType.MANUAL,
            description="Deletion test backup"
        )
        
        # Verify backup exists
        backup_file = Path(backup_metadata.file_path)
        assert backup_file.exists()
        
        # Delete backup
        success = await backup_manager.delete_backup(backup_metadata.backup_id)
        assert success is True
        
        # Verify backup file is deleted
        assert not backup_file.exists()

class TestIntegration:
    """Integration tests for the backup system"""
    
    @pytest.mark.asyncio
    async def test_full_backup_workflow(self):
        """Test a complete backup workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test configuration
            config = BackupConfiguration(
                include_patterns=["*.db", "*.json"],
                max_backups=5
            )
            
            # Create manager
            manager = BackupManager(config, temp_path)
            
            # Create test files
            db_file = temp_path / "test.db"
            db_file.write_text("test database")
            
            json_file = temp_path / "metadata.json"
            json_file.write_text('{"test": true}')
            
            # Create backup
            backup_metadata = await manager.create_backup(
                backup_type=BackupType.FULL,
                description="Full workflow test"
            )
            
            # Verify backup
            assert backup_metadata is not None
            assert await manager.verify_backup(backup_metadata.backup_id)
            
            # List backups
            backups = await manager.list_backups()
            assert len(backups) >= 1
            
            # Verify backup ID is in the list
            backup_ids = [b.backup_id for b in backups]
            assert backup_metadata.backup_id in backup_ids

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in various scenarios"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config = BackupConfiguration()
            manager = BackupManager(config, temp_path)
            
            # Test verification of non-existent backup
            is_valid = await manager.verify_backup("non-existent-backup-id")
            assert is_valid is False
            
            # Test deletion of non-existent backup
            success = await manager.delete_backup("non-existent-backup-id")
            assert success is False

def test_create_backup_manager():
    """Test factory function for creating backup manager"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        manager = create_backup_manager(temp_path)
        
        assert isinstance(manager, BackupManager)
        assert isinstance(manager.config, BackupConfiguration)
        assert manager.data_dir == temp_path

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
