#!/usr/bin/env python3
"""
Demo script to test export format functionality.
"""

import json
import tempfile
import os
from datetime import datetime
from pathlib import Path

# Import our export system
from export_formats import (
    ExportFormat, CompressionType, ExportConfig, ExportManager,
    export_chunks_to_jsonl, export_chunks_to_csv
)

# Sample data
sample_chunks = [
    {
        "id": "chunk_001",
        "text": "This is the first chunk of text from the Bhagavad Gita.",
        "metadata": {
            "source": "bhagavad_gita.txt",
            "chapter": 1,
            "verse": "1-5",
            "speaker": "Sanjaya"
        },
        "tokens": 12,
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
        "relationships": ["sequential", "thematic"],
        "quality_score": 0.92
    },
    {
        "id": "chunk_002", 
        "text": "Krishna's response to Arjuna's dilemma about fighting in battle.",
        "metadata": {
            "source": "bhagavad_gita.txt",
            "chapter": 2,
            "verse": "11-13",
            "speaker": "Krishna"
        },
        "tokens": 15,
        "created_at": datetime(2024, 1, 1, 12, 1, 0),
        "relationships": ["sequential", "semantic"],
        "quality_score": 0.95
    },
    {
        "id": "chunk_003",
        "text": "The eternal nature of the soul and principles of dharma.",
        "metadata": {
            "source": "bhagavad_gita.txt",
            "chapter": 2,
            "verse": "20-25",
            "speaker": "Krishna"
        },
        "tokens": 18,
        "created_at": datetime(2024, 1, 1, 12, 2, 0),
        "relationships": ["sequential", "entity"],
        "quality_score": 0.98
    }
]

def test_jsonl_export():
    """Test JSONL export functionality."""
    print("Testing JSONL export...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "chunks.jsonl")
        
        result = export_chunks_to_jsonl(sample_chunks, output_path)
        
        print(f"  ✓ Export successful: {result.success}")
        print(f"  ✓ Records exported: {result.records_exported}")
        print(f"  ✓ File size: {result.file_size_bytes} bytes")
        print(f"  ✓ Export time: {result.export_time_seconds:.3f} seconds")
        
        # Verify content
        with open(output_path, 'r') as f:
            lines = f.readlines()
            print(f"  ✓ Lines in file: {len(lines)}")
            
            # Check first record
            first_record = json.loads(lines[0])
            print(f"  ✓ First record ID: {first_record['id']}")

def test_csv_export():
    """Test CSV export functionality."""
    print("\nTesting CSV export...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "chunks.csv")
        
        result = export_chunks_to_csv(
            sample_chunks, 
            output_path,
            flatten_nested=True  # Better for CSV
        )
        
        print(f"  ✓ Export successful: {result.success}")
        print(f"  ✓ Records exported: {result.records_exported}")
        print(f"  ✓ File size: {result.file_size_bytes} bytes")
        
        # Verify content
        with open(output_path, 'r') as f:
            lines = f.readlines()
            print(f"  ✓ Lines in file (including header): {len(lines)}")
            print(f"  ✓ Header: {lines[0].strip()[:100]}...")

def test_multiple_formats():
    """Test exporting to multiple formats simultaneously."""
    print("\nTesting batch export to multiple formats...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        configs = [
            ExportConfig(
                format=ExportFormat.JSONL,
                output_path=os.path.join(tmpdir, "chunks.jsonl")
            ),
            ExportConfig(
                format=ExportFormat.JSON,
                output_path=os.path.join(tmpdir, "chunks.json"),
                json_indent=2
            ),
            ExportConfig(
                format=ExportFormat.CSV,
                output_path=os.path.join(tmpdir, "chunks.csv"),
                flatten_nested=True
            ),
            ExportConfig(
                format=ExportFormat.XML,
                output_path=os.path.join(tmpdir, "chunks.xml"),
                xml_root_element="chunks",
                xml_item_element="chunk"
            )
        ]
        
        manager = ExportManager()
        results = manager.batch_export(sample_chunks, configs)
        
        print(f"  ✓ Exported to {len(results)} formats")
        
        for i, result in enumerate(results):
            format_name = configs[i].format.value
            print(f"  ✓ {format_name}: {result.records_exported} records, {result.file_size_bytes} bytes")

def test_compression():
    """Test export with compression."""
    print("\nTesting export with compression...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ExportConfig(
            format=ExportFormat.JSONL,
            output_path=os.path.join(tmpdir, "chunks.jsonl"),
            compression=CompressionType.ZIP
        )
        
        manager = ExportManager()
        result = manager.export(sample_chunks, config)
        
        print(f"  ✓ Compressed export successful: {result.success}")
        print(f"  ✓ Output file: {Path(result.output_path).name}")
        print(f"  ✓ Compressed size: {result.file_size_bytes} bytes")

def test_custom_format():
    """Test custom format export."""
    print("\nTesting custom format export...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        template = "ID: {id} | Text: {text} | Chapter: {metadata[chapter]} | Quality: {quality_score}"
        
        config = ExportConfig(
            format=ExportFormat.CUSTOM,
            output_path=os.path.join(tmpdir, "chunks.txt"),
            custom_template=template
        )
        
        manager = ExportManager()
        result = manager.export(sample_chunks, config)
        
        print(f"  ✓ Custom export successful: {result.success}")
        print(f"  ✓ Records exported: {result.records_exported}")
        
        # Show sample output
        with open(result.output_path, 'r') as f:
            first_line = f.readline().strip()
            print(f"  ✓ Sample line: {first_line[:80]}...")

def test_parquet_export():
    """Test Parquet export if available."""
    print("\nTesting Parquet export...")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ExportConfig(
                format=ExportFormat.PARQUET,
                output_path=os.path.join(tmpdir, "chunks.parquet"),
                flatten_nested=True
            )
            
            manager = ExportManager()
            result = manager.export(sample_chunks, config)
            
            print(f"  ✓ Parquet export successful: {result.success}")
            print(f"  ✓ Records exported: {result.records_exported}")
            print(f"  ✓ File size: {result.file_size_bytes} bytes")
            
    except Exception as e:
        print(f"  ⚠ Parquet export failed (dependencies may be missing): {str(e)}")

def main():
    """Run all export format tests."""
    print("🚀 Testing Lexicon Export Format System")
    print("=" * 50)
    
    try:
        test_jsonl_export()
        test_csv_export()
        test_multiple_formats()
        test_compression()
        test_custom_format()
        test_parquet_export()
        
        print("\n" + "=" * 50)
        print("✅ All export format tests completed successfully!")
        
        # Show supported formats
        manager = ExportManager()
        formats = manager.get_supported_formats()
        print(f"\n📋 Supported formats: {', '.join(formats)}")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
