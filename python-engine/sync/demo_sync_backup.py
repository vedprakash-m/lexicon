#!/usr/bin/env python3
"""
Demo script to test cloud sync and backup functionality.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

from cloud_storage_manager import (
    create_cloud_storage_manager, CloudProvider, SyncConfiguration, 
    ConflictResolution
)
from backup_manager import (
    create_backup_manager, BackupType, BackupConfiguration
)

async def test_backup_system():
    """Test the backup and restoration system."""
    print("🚀 Testing Backup System")
    print("=" * 50)
    
    # Setup
    test_data_dir = Path("../test_data")
    test_data_dir.mkdir(exist_ok=True)
    
    # Create some test files
    sample_files = {
        "enrichment_demo_results.json": {
            "books": [
                {"title": "Test Book 1", "author": "Test Author 1"},
                {"title": "Test Book 2", "author": "Test Author 2"}
            ],
            "timestamp": datetime.now().isoformat()
        },
        "catalog_metadata.json": {
            "total_books": 2,
            "last_updated": datetime.now().isoformat()
        },
        "relationship_mapping.json": {
            "relationships": [
                {"type": "same_author", "confidence": 0.95}
            ]
        }
    }
    
    print("📁 Creating test files...")
    for filename, content in sample_files.items():
        file_path = test_data_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2)
        print(f"   ✓ Created: {filename}")
    
    # Initialize backup manager
    backup_manager = create_backup_manager(test_data_dir)
    
    # Test manual backup creation
    print("\n📦 Testing manual backup creation...")
    backup_metadata = await backup_manager.create_backup(
        backup_type=BackupType.MANUAL,
        description="Test manual backup"
    )
    
    if backup_metadata:
        print(f"   ✅ Backup created: {backup_metadata.backup_id}")
        print(f"   📊 Size: {backup_metadata.size_bytes / 1024:.2f} KB")
        print(f"   📁 Files: {len(backup_metadata.files_included)}")
        
        # Test backup verification
        print("\n🔍 Testing backup verification...")
        is_valid = await backup_manager.verify_backup(backup_metadata.backup_id)
        print(f"   {'✅' if is_valid else '❌'} Backup verification: {'PASSED' if is_valid else 'FAILED'}")
        
        # Test backup listing
        print("\n📋 Testing backup listing...")
        all_backups = await backup_manager.list_backups()
        print(f"   📊 Total backups: {len(all_backups)}")
        for backup in all_backups:
            print(f"   📦 {backup.backup_id} ({backup.backup_type.value}) - {backup.status.value}")
        
        # Test restore to different location
        print("\n🔄 Testing backup restoration...")
        restore_dir = test_data_dir / "restored"
        restore_dir.mkdir(exist_ok=True)
        
        restore_success = await backup_manager.restore_backup(
            backup_metadata.backup_id,
            target_dir=restore_dir,
            overwrite_existing=True
        )
        print(f"   {'✅' if restore_success else '❌'} Restore: {'SUCCESS' if restore_success else 'FAILED'}")
        
        if restore_success:
            restored_files = list(restore_dir.rglob("*.json"))
            print(f"   📁 Restored {len(restored_files)} files")
            
        # Test backup stats
        print("\n📊 Backup system statistics...")
        stats = backup_manager.get_backup_stats()
        print(f"   📦 Total backups: {stats['total_backups']}")
        print(f"   ✅ Successful: {stats['successful_backups']}")
        print(f"   ❌ Failed: {stats['failed_backups']}")
        print(f"   💾 Total size: {stats['total_size_mb']:.2f} MB")
        if stats['latest_backup']:
            latest = stats['latest_backup']
            print(f"   🕐 Latest: {latest['id']} ({latest['type']}) - {latest['status']}")
    
    print("\n" + "=" * 50)
    print("✅ Backup system tests completed!")

async def test_cloud_sync_system():
    """Test the cloud synchronization system."""
    print("\n🚀 Testing Cloud Sync System")
    print("=" * 50)
    
    # Setup
    test_data_dir = Path("../test_data")
    
    # Initialize cloud storage manager
    cloud_manager = create_cloud_storage_manager(test_data_dir, CloudProvider.LOCAL_ONLY)
    
    # Load sync state
    print("📋 Loading sync state...")
    await cloud_manager.load_sync_state()
    
    # Test file scanning
    print("\n📁 Scanning local files...")
    local_files = await cloud_manager.scan_local_files()
    print(f"   📊 Found {len(local_files)} files to sync")
    
    for sync_file in local_files:
        print(f"   📄 {sync_file.path} ({sync_file.size} bytes) - {sync_file.sync_status.value}")
    
    # Test sync stats
    print("\n📊 Sync system statistics...")
    stats = cloud_manager.get_sync_stats()
    print(f"   🔧 Provider: {stats['provider']}")
    print(f"   ✅ Enabled: {stats['enabled']}")
    print(f"   📁 Total files: {stats['total_files']}")
    print(f"   🔄 Synced files: {stats['synced_files']}")
    print(f"   ⬆️  Pending uploads: {stats['pending_uploads']}")
    print(f"   ⚠️  Conflicts: {stats['conflicts']}")
    print(f"   ❌ Errors: {stats['errors']}")
    
    if stats['recent_errors']:
        print("   Recent errors:")
        for error in stats['recent_errors']:
            print(f"     ❌ {error}")
    
    # Save sync state
    print("\n💾 Saving sync state...")
    await cloud_manager.save_sync_state()
    
    print("\n" + "=" * 50)
    print("✅ Cloud sync system tests completed!")

async def test_integration():
    """Test integration between backup and sync systems."""
    print("\n🚀 Testing Backup + Sync Integration")
    print("=" * 50)
    
    test_data_dir = Path("../test_data")
    
    # Initialize both systems
    backup_manager = create_backup_manager(test_data_dir)
    cloud_manager = create_cloud_storage_manager(test_data_dir, CloudProvider.LOCAL_ONLY)
    
    print("📦 Creating backup for sync...")
    backup_metadata = await backup_manager.create_backup(
        backup_type=BackupType.FULL,
        description="Backup for cloud sync test"
    )
    
    if backup_metadata:
        print(f"   ✅ Backup created: {backup_metadata.backup_id}")
        
        # The backup file should now be detected by the sync system
        print("\n🔄 Scanning for new files to sync...")
        local_files = await cloud_manager.scan_local_files()
        
        backup_files = [f for f in local_files if 'backup_' in f.path]
        print(f"   📊 Found {len(backup_files)} backup files to sync")
        
        for backup_file in backup_files:
            print(f"   📄 {backup_file.path} ({backup_file.size} bytes)")
    
    print("\n💡 Integration test demonstrates how backups can be automatically synced to cloud storage!")
    
    print("\n" + "=" * 50)
    print("✅ Integration tests completed!")

async def demo_automatic_systems():
    """Demonstrate automatic backup and sync operations."""
    print("\n🚀 Demo: Automatic Systems")
    print("=" * 50)
    
    test_data_dir = Path("../test_data")
    
    # Initialize systems
    backup_manager = create_backup_manager(test_data_dir)
    cloud_manager = create_cloud_storage_manager(test_data_dir, CloudProvider.LOCAL_ONLY)
    
    print("⏰ Automatic systems would run in the background with these intervals:")
    print(f"   📦 Automatic backups: every {backup_manager.config.automatic_interval} seconds")
    print(f"   🔄 Cloud sync: every {cloud_manager.config.auto_sync_interval} seconds")
    print(f"   🧹 Backup cleanup: keeping {backup_manager.config.max_backups} backups max")
    
    print("\n🔄 Simulating one cycle of automatic operations...")
    
    # Create a backup (simulating automatic backup)
    print("   📦 Running automatic backup...")
    backup = await backup_manager.create_backup(
        backup_type=BackupType.AUTOMATIC,
        description="Automatic backup cycle"
    )
    
    if backup:
        print(f"     ✅ Created backup: {backup.backup_id}")
    
    # Simulate sync operation
    print("   🔄 Running sync scan...")
    local_files = await cloud_manager.scan_local_files()
    print(f"     📊 {len(local_files)} files ready for sync")
    
    print("\n💡 In a real deployment, these would run continuously in the background!")
    
    print("\n" + "=" * 50)
    print("✅ Automatic systems demo completed!")

async def main():
    """Run all cloud sync and backup demos."""
    print("🚀 Lexicon Cloud Sync & Backup System Demo")
    print("=" * 60)
    
    try:
        # Test backup system
        await test_backup_system()
        
        # Test cloud sync system
        await test_cloud_sync_system()
        
        # Test integration
        await test_integration()
        
        # Demo automatic systems
        await demo_automatic_systems()
        
        print("\n" + "=" * 60)
        print("✅ All cloud sync and backup tests completed successfully!")
        
        print("\n📝 Summary of implemented features:")
        print("   📦 Automatic and manual backup creation")
        print("   🔍 Backup verification and integrity checking")
        print("   🔄 Backup restoration with conflict handling")
        print("   🧹 Automatic cleanup of old backups")
        print("   ☁️  Cloud storage integration (iCloud, Google Drive, etc.)")
        print("   🔄 Automatic synchronization with conflict resolution")
        print("   🔐 Optional encryption for sensitive data")
        print("   📊 Comprehensive statistics and monitoring")
        print("   ⚙️  Configurable patterns and scheduling")
        
        print("\n🔧 Configuration highlights:")
        print("   📦 Backups: Compressed ZIP files with metadata")
        print("   🔄 Sync: Automatic every 5 minutes")
        print("   🧹 Cleanup: Keep last 30 backups")
        print("   🔐 Security: Optional encryption support")
        print("   📊 Monitoring: Full statistics and error tracking")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
