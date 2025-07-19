#!/usr/bin/env python3
"""
Tests for Cloud Storage Integration System
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

# Import the modules to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from cloud_storage_manager import (
    CloudProvider, SyncStatus, ConflictResolution,
    SyncFile, SyncConfiguration, SyncState, CloudStorageManager
)

class TestCloudProvider:
    def test_cloud_provider_enum(self):
        """Test CloudProvider enum values"""
        assert CloudProvider.ICLOUD.value == "icloud"
        assert CloudProvider.GOOGLE_DRIVE.value == "google_drive"
        assert CloudProvider.DROPBOX.value == "dropbox"
        assert CloudProvider.ONEDRIVE.value == "onedrive"
        assert CloudProvider.LOCAL_ONLY.value == "local_only"

class TestSyncConfiguration:
    def test_default_sync_configuration(self):
        """Test SyncConfiguration with default values"""
        config = SyncConfiguration()
        
        assert config.enabled is True
        assert config.provider == CloudProvider.ICLOUD
        assert config.auto_sync_interval == 300
        assert config.conflict_resolution == ConflictResolution.ASK_USER
        assert config.encrypt_data is True
        assert config.max_file_size == 100 * 1024 * 1024
        
        # Check default patterns
        assert "*.db" in config.sync_patterns
        assert "*.json" in config.sync_patterns
        assert "enrichment_*.json" in config.sync_patterns
        
        assert "*.tmp" in config.exclude_patterns
        assert "*.log" in config.exclude_patterns
        assert "cache_*" in config.exclude_patterns

    def test_custom_sync_configuration(self):
        """Test SyncConfiguration with custom values"""
        config = SyncConfiguration(
            enabled=False,
            provider=CloudProvider.GOOGLE_DRIVE,
            auto_sync_interval=600,
            conflict_resolution=ConflictResolution.KEEP_LOCAL,
            encrypt_data=False,
            sync_patterns=["*.custom"],
            exclude_patterns=["*.exclude"]
        )
        
        assert config.enabled is False
        assert config.provider == CloudProvider.GOOGLE_DRIVE
        assert config.auto_sync_interval == 600
        assert config.conflict_resolution == ConflictResolution.KEEP_LOCAL
        assert config.encrypt_data is False
        assert config.sync_patterns == ["*.custom"]
        assert config.exclude_patterns == ["*.exclude"]

class TestSyncFile:
    def test_sync_file_creation(self):
        """Test SyncFile dataclass"""
        now = datetime.now(timezone.utc)
        sync_file = SyncFile(
            path="test/file.db",
            checksum="abc123",
            size=1024,
            modified_time=now,
            sync_status=SyncStatus.SYNCED,
            cloud_path="cloud/test/file.db",
            provider=CloudProvider.ICLOUD
        )
        
        assert sync_file.path == "test/file.db"
        assert sync_file.checksum == "abc123"
        assert sync_file.size == 1024
        assert sync_file.sync_status == SyncStatus.SYNCED
        assert sync_file.cloud_path == "cloud/test/file.db"
        assert sync_file.provider == CloudProvider.ICLOUD

class TestCloudStorageManager:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def sync_config(self):
        """Create a test sync configuration"""
        return SyncConfiguration(
            provider=CloudProvider.ICLOUD,
            sync_patterns=["*.db", "*.json"],
            exclude_patterns=["*.tmp", "*.log"]
        )

    @pytest.fixture
    def cloud_manager(self, temp_dir, sync_config):
        """Create a CloudStorageManager instance for testing"""
        return CloudStorageManager(sync_config, temp_dir)

    def test_cloud_manager_initialization(self, cloud_manager, sync_config):
        """Test CloudStorageManager initialization"""
        assert cloud_manager.config == sync_config
        assert isinstance(cloud_manager.sync_state, SyncState)
        assert cloud_manager.files == {}
        assert not cloud_manager.is_syncing

    @patch('platform.system')
    def test_get_cloud_paths_macos(self, mock_system, cloud_manager):
        """Test cloud path detection on macOS"""
        mock_system.return_value = "Darwin"
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            with patch('pathlib.Path.home') as mock_home:
                mock_home.return_value = Path("/Users/testuser")
                
                paths = cloud_manager._get_cloud_paths()
                
                assert CloudProvider.ICLOUD in paths
                expected_icloud = Path("/Users/testuser/Library/Mobile Documents/com~apple~CloudDocs/Lexicon")
                assert paths[CloudProvider.ICLOUD] == expected_icloud

    @patch('platform.system')
    def test_get_cloud_paths_windows(self, mock_system, cloud_manager):
        """Test cloud path detection on Windows"""
        mock_system.return_value = "Windows"
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            with patch('pathlib.Path.home') as mock_home:
                mock_home.return_value = Path("C:/Users/testuser")
                with patch.dict(os.environ, {'OneDrive': 'C:/Users/testuser/OneDrive'}):
                    
                    paths = cloud_manager._get_cloud_paths()
                    
                    assert CloudProvider.ONEDRIVE in paths

    def test_should_sync_file(self, cloud_manager, temp_dir):
        """Test file sync pattern matching"""
        # Create test files
        db_file = temp_dir / "test.db"
        json_file = temp_dir / "config.json"
        tmp_file = temp_dir / "temp.tmp"
        log_file = temp_dir / "app.log"
        
        # Test inclusion patterns
        assert cloud_manager._should_sync_file(db_file)
        assert cloud_manager._should_sync_file(json_file)
        
        # Test exclusion patterns
        assert not cloud_manager._should_sync_file(tmp_file)
        assert not cloud_manager._should_sync_file(log_file)

    @pytest.mark.asyncio
    async def test_scan_local_files(self, cloud_manager, temp_dir):
        """Test scanning local files for sync"""
        # Create test files
        db_file = temp_dir / "lexicon.db"
        db_file.write_text("test database content")
        
        json_file = temp_dir / "config.json"
        json_file.write_text('{"test": "config"}')
        
        tmp_file = temp_dir / "temp.tmp"
        tmp_file.write_text("temporary content")
        
        # Scan files
        files = await cloud_manager.scan_local_files()
        
        # Should find db and json files, but not tmp file
        assert len(files) == 2
        
        paths = [f.path for f in files]
        assert "lexicon.db" in paths
        assert "config.json" in paths
        assert "temp.tmp" not in paths

    def test_calculate_checksum(self, cloud_manager, temp_dir):
        """Test checksum calculation"""
        test_file = temp_dir / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)
        
        checksum = cloud_manager._calculate_checksum(test_file)
        
        # Should return a SHA256 hash
        assert len(checksum) == 64
        assert isinstance(checksum, str)
        
        # Same content should produce same checksum
        checksum2 = cloud_manager._calculate_checksum(test_file)
        assert checksum == checksum2

    @pytest.mark.asyncio
    async def test_get_cloud_path(self, cloud_manager):
        """Test getting cloud path for current provider"""
        # Mock the cloud paths
        with patch.object(cloud_manager, 'cloud_paths', {CloudProvider.ICLOUD: Path("/test/icloud")}):
            cloud_path = await cloud_manager.get_cloud_path()
            assert cloud_path == Path("/test/icloud")

    def test_encryption_initialization(self, temp_dir, sync_config):
        """Test encryption key initialization"""
        # Test with encryption enabled
        manager_with_encryption = CloudStorageManager(sync_config, temp_dir)
        assert manager_with_encryption.encryption_key is not None
        
        # Key file should be created
        key_file = temp_dir / ".sync_key"
        assert key_file.exists()
        
        # Test loading existing key
        manager2 = CloudStorageManager(sync_config, temp_dir)
        assert manager2.encryption_key == manager_with_encryption.encryption_key

    def test_encrypt_decrypt_data(self, cloud_manager):
        """Test data encryption and decryption"""
        if not cloud_manager.config.encrypt_data:
            pytest.skip("Encryption not enabled in config")
        
        test_data = b"This is test data to encrypt"
        
        # Encrypt data
        encrypted = cloud_manager._encrypt_data(test_data)
        assert encrypted != test_data
        
        # Decrypt data
        decrypted = cloud_manager._decrypt_data(encrypted)
        assert decrypted == test_data

class TestIntegration:
    """Integration tests for the cloud storage system"""
    
    @pytest.mark.asyncio
    async def test_full_sync_workflow(self):
        """Test a complete sync workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test configuration
            config = SyncConfiguration(
                provider=CloudProvider.ICLOUD,
                encrypt_data=True,
                sync_patterns=["*.db", "*.json"]
            )
            
            # Create manager
            manager = CloudStorageManager(config, temp_path)
            
            # Create test files
            db_file = temp_path / "test.db"
            db_file.write_text("test database")
            
            json_file = temp_path / "metadata.json"
            json_file.write_text('{"test": true}')
            
            # Scan files
            local_files = await manager.scan_local_files()
            
            # Verify files were found
            assert len(local_files) == 2
            
            # Check file properties
            for sync_file in local_files:
                assert sync_file.checksum is not None
                assert sync_file.size > 0
                assert sync_file.sync_status == SyncStatus.NOT_SYNCED

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in various scenarios"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config = SyncConfiguration()
            manager = CloudStorageManager(config, temp_path)
            
            # Test with non-existent file
            non_existent = temp_path / "does_not_exist.db"
            try:
                manager._calculate_checksum(non_existent)
                assert False, "Should have raised an exception"
            except (FileNotFoundError, OSError):
                pass  # Expected
            
            # Test upload without cloud path
            sync_file = SyncFile(
                path="test.db",
                checksum="abc123",
                size=1024,
                modified_time=datetime.now(timezone.utc),
                sync_status=SyncStatus.NOT_SYNCED
            )
            
            # Mock get_cloud_path to return None
            with patch.object(manager, 'get_cloud_path', return_value=None):
                result = await manager.upload_file(sync_file)
                assert not result

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
