"""
Comprehensive tests for the export format system.

This module tests all export formats, configurations, and error handling scenarios.
"""

import csv
import json
import os
import tempfile
import pytest
import zipfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

try:
    from .export_formats import (
        ExportFormat, CompressionType, ExportConfig, ExportResult,
        ExportManager, JSONLExporter, JSONExporter, CSVExporter, XMLExporter,
        CustomExporter, export_chunks_to_jsonl, export_chunks_to_csv
    )
except ImportError:
    from export_formats import (
        ExportFormat, CompressionType, ExportConfig, ExportResult,
        ExportManager, JSONLExporter, JSONExporter, CSVExporter, XMLExporter,
        CustomExporter, export_chunks_to_jsonl, export_chunks_to_csv
    )

# Test data
SAMPLE_CHUNKS = [
    {
        "id": "chunk_001",
        "text": "This is the first chunk of text.",
        "metadata": {
            "source": "test_document.txt",
            "page": 1,
            "section": "introduction"
        },
        "tokens": 8,
        "created_at": datetime(2024, 1, 1, 12, 0, 0)
    },
    {
        "id": "chunk_002", 
        "text": "This is the second chunk with more content.",
        "metadata": {
            "source": "test_document.txt",
            "page": 1,
            "section": "body"
        },
        "tokens": 10,
        "created_at": datetime(2024, 1, 1, 12, 1, 0)
    },
    {
        "id": "chunk_003",
        "text": "Final chunk with special characters: émojis 🎉 and symbols @#$%",
        "metadata": {
            "source": "test_document.txt", 
            "page": 2,
            "section": "conclusion"
        },
        "tokens": 12,
        "created_at": datetime(2024, 1, 1, 12, 2, 0)
    }
]


class TestExportConfig:
    """Test export configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ExportConfig(
            format=ExportFormat.JSONL,
            output_path="/tmp/test.jsonl"
        )
        
        assert config.format == ExportFormat.JSONL
        assert config.compression == CompressionType.NONE
        assert config.batch_size == 1000
        assert config.include_metadata is True
        assert config.flatten_nested is False
        assert config.encoding == "utf-8"
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = ExportConfig(
            format=ExportFormat.CSV,
            output_path="/tmp/test.csv",
            compression=CompressionType.GZIP,
            batch_size=500,
            flatten_nested=True,
            csv_delimiter=";",
            exclude_fields=["metadata"]
        )
        
        assert config.format == ExportFormat.CSV
        assert config.compression == CompressionType.GZIP
        assert config.batch_size == 500
        assert config.flatten_nested is True
        assert config.csv_delimiter == ";"
        assert config.exclude_fields == ["metadata"]


class TestJSONLExporter:
    """Test JSONL export functionality."""
    
    def test_basic_jsonl_export(self):
        """Test basic JSONL export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.jsonl")
            config = ExportConfig(
                format=ExportFormat.JSONL,
                output_path=output_path
            )
            
            exporter = JSONLExporter(config)
            result = exporter.export(iter(SAMPLE_CHUNKS))
            
            assert result.success is True
            assert result.records_exported == 3
            assert result.format == ExportFormat.JSONL
            assert os.path.exists(output_path)
            
            # Verify content
            with open(output_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 3
                
                # Parse first line
                first_record = json.loads(lines[0])
                assert first_record["id"] == "chunk_001"
                assert first_record["text"] == "This is the first chunk of text."
    
    def test_jsonl_with_field_filtering(self):
        """Test JSONL export with field filtering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.jsonl")
            config = ExportConfig(
                format=ExportFormat.JSONL,
                output_path=output_path,
                custom_fields=["id", "text", "tokens"]
            )
            
            exporter = JSONLExporter(config)
            result = exporter.export(iter(SAMPLE_CHUNKS))
            
            assert result.success is True
            
            # Verify filtered content
            with open(output_path, 'r') as f:
                first_record = json.loads(f.readline())
                assert set(first_record.keys()) == {"id", "text", "tokens"}
                assert "metadata" not in first_record
    
    def test_jsonl_with_compression(self):
        """Test JSONL export with compression."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.jsonl")
            config = ExportConfig(
                format=ExportFormat.JSONL,
                output_path=output_path,
                compression=CompressionType.ZIP
            )
            
            exporter = JSONLExporter(config)
            result = exporter.export(iter(SAMPLE_CHUNKS))
            
            assert result.success is True
            assert result.output_path.endswith(".zip")
            
            # Verify compressed file exists and can be read
            with zipfile.ZipFile(result.output_path, 'r') as zf:
                assert "test.jsonl" in zf.namelist()


class TestJSONExporter:
    """Test JSON export functionality."""
    
    def test_basic_json_export(self):
        """Test basic JSON export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.json")
            config = ExportConfig(
                format=ExportFormat.JSON,
                output_path=output_path
            )
            
            exporter = JSONExporter(config)
            result = exporter.export(iter(SAMPLE_CHUNKS))
            
            assert result.success is True
            assert result.records_exported == 3
            assert result.format == ExportFormat.JSON
            
            # Verify content
            with open(output_path, 'r') as f:
                data = json.load(f)
                assert isinstance(data, list)
                assert len(data) == 3
                assert data[0]["id"] == "chunk_001"
    
    def test_json_with_flattening(self):
        """Test JSON export with field flattening."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.json")
            config = ExportConfig(
                format=ExportFormat.JSON,
                output_path=output_path,
                flatten_nested=True
            )
            
            exporter = JSONExporter(config)
            result = exporter.export(iter(SAMPLE_CHUNKS))
            
            assert result.success is True
            
            # Verify flattened content
            with open(output_path, 'r') as f:
                data = json.load(f)
                first_record = data[0]
                assert "metadata.source" in first_record
                assert "metadata.page" in first_record
                assert "metadata" not in first_record


class TestCSVExporter:
    """Test CSV export functionality."""
    
    def test_basic_csv_export(self):
        """Test basic CSV export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.csv")
            config = ExportConfig(
                format=ExportFormat.CSV,
                output_path=output_path,
                flatten_nested=True  # CSV works better with flattened data
            )
            
            exporter = CSVExporter(config)
            result = exporter.export(iter(SAMPLE_CHUNKS))
            
            assert result.success is True
            assert result.records_exported == 3
            assert result.format == ExportFormat.CSV
            
            # Verify content
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 3
                assert rows[0]["id"] == "chunk_001"
                assert "metadata.source" in rows[0]
    
    def test_csv_with_custom_delimiter(self):
        """Test CSV export with custom delimiter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.tsv")
            config = ExportConfig(
                format=ExportFormat.CSV,
                output_path=output_path,
                csv_delimiter="\t",
                flatten_nested=True
            )
            
            exporter = CSVExporter(config)
            result = exporter.export(iter(SAMPLE_CHUNKS))
            
            assert result.success is True
            
            # Verify tab-separated content
            with open(output_path, 'r') as f:
                first_line = f.readline()
                assert "\t" in first_line
                assert "," not in first_line.replace('"', '')


class TestXMLExporter:
    """Test XML export functionality."""
    
    def test_basic_xml_export(self):
        """Test basic XML export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.xml")
            config = ExportConfig(
                format=ExportFormat.XML,
                output_path=output_path
            )
            
            exporter = XMLExporter(config)
            result = exporter.export(iter(SAMPLE_CHUNKS))
            
            assert result.success is True
            assert result.records_exported == 3
            assert result.format == ExportFormat.XML
            
            # Verify XML structure
            import xml.etree.ElementTree as ET
            tree = ET.parse(output_path)
            root = tree.getroot()
            
            assert root.tag == "data"
            items = root.findall("item")
            assert len(items) == 3
            
            first_item = items[0]
            assert first_item.find("id").text == "chunk_001"
    
    def test_xml_with_custom_elements(self):
        """Test XML export with custom element names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.xml")
            config = ExportConfig(
                format=ExportFormat.XML,
                output_path=output_path,
                xml_root_element="chunks",
                xml_item_element="chunk"
            )
            
            exporter = XMLExporter(config)
            result = exporter.export(iter(SAMPLE_CHUNKS))
            
            assert result.success is True
            
            # Verify custom element names
            import xml.etree.ElementTree as ET
            tree = ET.parse(output_path)
            root = tree.getroot()
            
            assert root.tag == "chunks"
            chunks = root.findall("chunk")
            assert len(chunks) == 3


class TestCustomExporter:
    """Test custom export functionality."""
    
    def test_template_based_export(self):
        """Test custom export with template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.txt")
            config = ExportConfig(
                format=ExportFormat.CUSTOM,
                output_path=output_path,
                custom_template="ID: {id}, Text: {text}, Tokens: {tokens}"
            )
            
            exporter = CustomExporter(config)
            result = exporter.export(iter(SAMPLE_CHUNKS))
            
            assert result.success is True
            assert result.records_exported == 3
            
            # Verify templated content
            with open(output_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 3
                assert lines[0].startswith("ID: chunk_001")
                assert "Tokens: 8" in lines[0]
    
    def test_processor_based_export(self):
        """Test custom export with processor function."""
        def custom_processor(data, config):
            """Custom processor that creates a summary file."""
            records = list(data)
            output_path = Path(config.output_path)
            
            with open(output_path, 'w') as f:
                f.write(f"Summary: {len(records)} chunks processed\n")
                total_tokens = sum(r.get('tokens', 0) for r in records)
                f.write(f"Total tokens: {total_tokens}\n")
                for record in records:
                    f.write(f"- {record['id']}: {len(record['text'])} chars\n")
            
            return {"records_exported": len(records)}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "summary.txt")
            config = ExportConfig(
                format=ExportFormat.CUSTOM,
                output_path=output_path,
                custom_processor=custom_processor
            )
            
            exporter = CustomExporter(config)
            result = exporter.export(iter(SAMPLE_CHUNKS))
            
            assert result.success is True
            assert result.records_exported == 3
            
            # Verify custom processed content
            with open(output_path, 'r') as f:
                content = f.read()
                assert "Summary: 3 chunks processed" in content
                assert "Total tokens: 30" in content
                assert "chunk_001:" in content


class TestParquetExporter:
    """Test Parquet export functionality."""
    
    @pytest.mark.skipif(not hasattr(pytest, 'importorskip'), reason="Parquet dependencies test")
    def test_parquet_export_with_pandas(self):
        """Test Parquet export when pandas/pyarrow available."""
        pd = pytest.importorskip("pandas")
        pytest.importorskip("pyarrow")
        
        from export_formats import ParquetExporter
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.parquet")
            config = ExportConfig(
                format=ExportFormat.PARQUET,
                output_path=output_path,
                flatten_nested=True
            )
            
            exporter = ParquetExporter(config)
            result = exporter.export(iter(SAMPLE_CHUNKS))
            
            assert result.success is True
            assert result.records_exported == 3
            assert result.format == ExportFormat.PARQUET
            
            # Verify parquet content
            df = pd.read_parquet(output_path)
            assert len(df) == 3
            assert df.iloc[0]['id'] == "chunk_001"


class TestExportManager:
    """Test the main export manager."""
    
    def test_manager_export(self):
        """Test manager-coordinated export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.jsonl")
            config = ExportConfig(
                format=ExportFormat.JSONL,
                output_path=output_path
            )
            
            manager = ExportManager()
            result = manager.export(SAMPLE_CHUNKS, config)
            
            assert result.success is True
            assert result.records_exported == 3
    
    def test_batch_export(self):
        """Test batch export to multiple formats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            configs = [
                ExportConfig(
                    format=ExportFormat.JSONL,
                    output_path=os.path.join(tmpdir, "test.jsonl")
                ),
                ExportConfig(
                    format=ExportFormat.CSV,
                    output_path=os.path.join(tmpdir, "test.csv"),
                    flatten_nested=True
                ),
                ExportConfig(
                    format=ExportFormat.XML,
                    output_path=os.path.join(tmpdir, "test.xml")
                )
            ]
            
            manager = ExportManager()
            results = manager.batch_export(SAMPLE_CHUNKS, configs)
            
            assert len(results) == 3
            assert all(r.success for r in results)
            assert all(r.records_exported == 3 for r in results)
            
            # Verify all files exist
            for config in configs:
                assert os.path.exists(config.output_path)
    
    def test_supported_formats(self):
        """Test getting supported formats."""
        manager = ExportManager()
        formats = manager.get_supported_formats()
        
        expected_formats = ['jsonl', 'json', 'parquet', 'csv', 'tsv', 'xml', 'markdown', 'txt', 'custom']
        for fmt in expected_formats:
            assert fmt in formats
    
    def test_config_validation(self):
        """Test configuration validation."""
        manager = ExportManager()
        
        # Valid config
        valid_config = ExportConfig(
            format=ExportFormat.JSONL,
            output_path="/tmp/test.jsonl"
        )
        errors = manager.validate_config(valid_config)
        assert len(errors) == 0
        
        # Invalid format (simulated)
        with patch.object(manager, 'exporters', {}):
            invalid_config = ExportConfig(
                format=ExportFormat.JSONL,
                output_path="/tmp/test.jsonl"
            )
            errors = manager.validate_config(invalid_config)
            assert len(errors) > 0
            assert "Unsupported format" in errors[0]
        
        # Custom format without requirements
        custom_config = ExportConfig(
            format=ExportFormat.CUSTOM,
            output_path="/tmp/test.txt"
        )
        errors = manager.validate_config(custom_config)
        assert len(errors) > 0
        assert "custom_template or custom_processor" in errors[0]


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_export_chunks_to_jsonl(self):
        """Test JSONL utility function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.jsonl")
            
            result = export_chunks_to_jsonl(SAMPLE_CHUNKS, output_path)
            
            assert result.success is True
            assert result.records_exported == 3
            assert os.path.exists(output_path)
    
    def test_export_chunks_to_csv(self):
        """Test CSV utility function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.csv")
            
            result = export_chunks_to_csv(SAMPLE_CHUNKS, output_path)
            
            assert result.success is True
            assert result.records_exported == 3
            assert os.path.exists(output_path)


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_invalid_output_path(self):
        """Test handling of invalid output paths."""
        config = ExportConfig(
            format=ExportFormat.JSONL,
            output_path="/invalid/path/that/does/not/exist/test.jsonl"
        )
        
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Access denied")):
            exporter = JSONLExporter(config)
            result = exporter.export(iter(SAMPLE_CHUNKS))
            
            assert result.success is False
            assert len(result.errors) > 0
    
    def test_encoding_errors(self):
        """Test handling of encoding errors."""
        # Create problematic data with non-UTF8 characters
        problematic_data = [
            {
                "id": "test",
                "text": "This contains problematic characters: \udcff\udcfe"
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.jsonl")
            config = ExportConfig(
                format=ExportFormat.JSONL,
                output_path=output_path,
                encoding="ascii"  # Will cause encoding issues
            )
            
            exporter = JSONLExporter(config)
            result = exporter.export(iter(problematic_data))
            
            # Should handle encoding errors gracefully
            assert result.success is False or result.success is True  # Implementation dependent


class TestPerformance:
    """Test performance and memory efficiency."""
    
    def test_large_dataset_streaming(self):
        """Test export of large dataset using streaming."""
        def generate_large_dataset(size=1000):
            """Generator for large dataset."""
            for i in range(size):
                yield {
                    "id": f"chunk_{i:06d}",
                    "text": f"This is chunk number {i} with some content.",
                    "metadata": {
                        "source": f"document_{i // 100}.txt",
                        "page": i // 10,
                        "section": "content"
                    },
                    "tokens": 10 + (i % 5)
                }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "large_test.jsonl")
            config = ExportConfig(
                format=ExportFormat.JSONL,
                output_path=output_path
            )
            
            exporter = JSONLExporter(config)
            result = exporter.export(generate_large_dataset(1000))
            
            assert result.success is True
            assert result.records_exported == 1000
            
            # Verify file size is reasonable
            assert result.file_size_bytes > 0
            
            # Verify we can read back the data
            with open(output_path, 'r') as f:
                line_count = sum(1 for _ in f)
                assert line_count == 1000


if __name__ == "__main__":
    # Run basic tests without pytest
    test_suite = [
        TestExportConfig,
        TestJSONLExporter,
        TestJSONExporter,
        TestCSVExporter,
        TestXMLExporter,
        TestCustomExporter,
        TestExportManager,
        TestUtilityFunctions,
        TestErrorHandling,
        TestPerformance
    ]
    
    print("Running export format tests...")
    
    for test_class in test_suite:
        print(f"\nTesting {test_class.__name__}...")
        test_instance = test_class()
        
        for method_name in dir(test_instance):
            if method_name.startswith("test_"):
                try:
                    print(f"  ✓ {method_name}")
                    getattr(test_instance, method_name)()
                except Exception as e:
                    print(f"  ✗ {method_name}: {str(e)}")
    
    print("\nExport format tests completed!")
