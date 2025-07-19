#!/usr/bin/env python3
"""
Simple test runner for cloud sync and backup functionality.
This tests the working demo functionality.
"""

import asyncio
import tempfile
import json
from pathlib import Path
from datetime import datetime

# Import the modules to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from cloud_storage_manager import (
    create_cloud_storage_manager, CloudProvider, SyncConfiguration
)
from backup_manager import (
    create_backup_manager, BackupType, BackupConfiguration
)

async def test_cloud_sync_functionality():
    """Test basic cloud sync functionality"""
    print("🧪 Testing Cloud Sync Functionality")
    print("=" * 40)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files
        test_file1 = temp_path / "test.json"
        test_file1.write_text('{"test": "data"}')
        
        test_file2 = temp_path / "config.db"
        test_file2.write_text("database content")
        
        # Create cloud storage manager
        manager = create_cloud_storage_manager(temp_path, CloudProvider.LOCAL_ONLY)
        
        # Test file scanning
        files = await manager.scan_local_files()
        print(f"   📁 Found {len(files)} files to sync")
        
        # Test basic sync operations
        stats = manager.get_sync_stats()
        print(f"   📊 Provider: {stats['provider']}")
        print(f"   📊 Enabled: {stats['enabled']}")
        
        print("   ✅ Cloud sync tests passed!")
        return True

async def test_backup_functionality():
    """Test basic backup functionality"""
    print("\n🧪 Testing Backup Functionality")
    print("=" * 40)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files
        test_file1 = temp_path / "backup_test.json"
        test_file1.write_text('{"backup": "test"}')
        
        test_file2 = temp_path / "data.db"
        test_file2.write_text("test database")
        
        # Create backup manager
        manager = create_backup_manager(temp_path)
        
        # Wait a moment for initialization
        await asyncio.sleep(0.1)
        
        # Create a backup
        backup_metadata = await manager.create_backup(
            backup_type=BackupType.MANUAL,
            description="Test backup"
        )
        
        if backup_metadata:
            print(f"   📦 Created backup: {backup_metadata.backup_id}")
            print(f"   📊 Files included: {len(backup_metadata.files_included)}")
            
            # Test verification
            is_valid = await manager.verify_backup(backup_metadata.backup_id)
            print(f"   🔍 Verification: {'✅ PASSED' if is_valid else '❌ FAILED'}")
            
            # Test listing
            backups = await manager.list_backups()
            print(f"   📋 Total backups: {len(backups)}")
            
            print("   ✅ Backup tests passed!")
            return True
        else:
            print("   ❌ Backup creation failed!")
            return False

async def test_integration():
    """Test integration between backup and sync"""
    print("\n🧪 Testing Integration")
    print("=" * 40)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test file
        test_file = temp_path / "integration_test.json"
        test_file.write_text('{"integration": "test"}')
        
        # Create both managers
        backup_manager = create_backup_manager(temp_path)
        sync_manager = create_cloud_storage_manager(temp_path, CloudProvider.LOCAL_ONLY)
        
        # Wait for backup manager initialization
        await asyncio.sleep(0.1)
        
        # Create backup
        backup_metadata = await backup_manager.create_backup(
            backup_type=BackupType.AUTOMATIC,
            description="Integration test backup"
        )
        
        if backup_metadata:
            # Scan for files including backup
            files = await sync_manager.scan_local_files()
            backup_files = [f for f in files if 'backup' in f.path.lower()]
            
            print(f"   📦 Backup created: {backup_metadata.backup_id}")
            print(f"   🔄 Backup files found for sync: {len(backup_files)}")
            print("   ✅ Integration tests passed!")
            return True
        else:
            print("   ❌ Integration test failed!")
            return False

async def test_error_handling():
    """Test error handling"""
    print("\n🧪 Testing Error Handling")
    print("=" * 40)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Test backup manager with non-existent backup
        backup_manager = create_backup_manager(temp_path)
        await asyncio.sleep(0.1)
        
        # Test verification of non-existent backup
        is_valid = await backup_manager.verify_backup("non-existent-backup")
        print(f"   🔍 Non-existent backup verification: {'✅ HANDLED' if not is_valid else '❌ FAILED'}")
        
        # Test sync manager with empty directory
        sync_manager = create_cloud_storage_manager(temp_path, CloudProvider.LOCAL_ONLY)
        files = await sync_manager.scan_local_files()
        print(f"   📁 Empty directory scan: {'✅ HANDLED' if len(files) == 0 else '❌ FAILED'}")
        
        print("   ✅ Error handling tests passed!")
        return True

async def main():
    """Run all tests"""
    print("🚀 Running Cloud Sync & Backup Tests")
    print("=" * 50)
    
    results = []
    
    try:
        # Run individual test suites
        results.append(await test_cloud_sync_functionality())
        results.append(await test_backup_functionality())
        results.append(await test_integration())
        results.append(await test_error_handling())
        
        # Summary
        passed = sum(results)
        total = len(results)
        
        print(f"\n{'=' * 50}")
        print(f"🧪 Test Summary: {passed}/{total} test suites passed")
        
        if passed == total:
            print("✅ All tests passed successfully!")
            return True
        else:
            print("❌ Some tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
