"""
Export Format System for Lexicon.

This module provides comprehensive export capabilities for processed data in multiple formats
including JSONL, Parquet, CSV, and custom formats with configurable options.
"""

import csv
import json
import logging
import os
import pandas as pd
import time
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Iterator, Callable
import xml.etree.ElementTree as ET

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Supported export formats."""
    JSONL = "jsonl"
    JSON = "json"
    PARQUET = "parquet"
    CSV = "csv"
    TSV = "tsv"
    XML = "xml"
    MARKDOWN = "markdown"
    TXT = "txt"
    CUSTOM = "custom"


class CompressionType(Enum):
    """Supported compression types."""
    NONE = "none"
    GZIP = "gzip"
    BZIP2 = "bzip2"
    XZ = "xz"
    ZIP = "zip"


@dataclass
class ExportConfig:
    """Configuration for export operations."""
    format: ExportFormat
    output_path: str
    compression: CompressionType = CompressionType.NONE
    batch_size: int = 1000
    include_metadata: bool = True
    flatten_nested: bool = False
    custom_fields: Optional[List[str]] = None
    exclude_fields: Optional[List[str]] = None
    date_format: str = "%Y-%m-%d %H:%M:%S"
    encoding: str = "utf-8"
    
    # Format-specific options
    csv_delimiter: str = ","
    csv_quoting: int = csv.QUOTE_MINIMAL
    json_indent: Optional[int] = 2
    parquet_compression: str = "snappy"
    xml_root_element: str = "data"
    xml_item_element: str = "item"
    
    # Custom format options
    custom_template: Optional[str] = None
    custom_processor: Optional[Callable] = None


@dataclass
class ExportResult:
    """Result of an export operation."""
    success: bool
    output_path: str
    records_exported: int
    file_size_bytes: int
    export_time_seconds: float
    format: ExportFormat
    compression: CompressionType
    errors: List[str] = None
    metadata: Dict[str, Any] = None


class BaseExporter(ABC):
    """Abstract base class for all exporters."""
    
    def __init__(self, config: ExportConfig):
        self.config = config
        self.errors = []
        
    @abstractmethod
    def export(self, data: Iterator[Dict[str, Any]]) -> ExportResult:
        """Export data to the specified format."""
        pass
    
    def _prepare_output_path(self) -> Path:
        """Prepare the output path and create directories if needed."""
        output_path = Path(self.config.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path
    
    def _filter_fields(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Filter fields based on include/exclude configuration."""
        if self.config.exclude_fields:
            record = {k: v for k, v in record.items() if k not in self.config.exclude_fields}
        
        if self.config.custom_fields:
            record = {k: v for k, v in record.items() if k in self.config.custom_fields}
        
        return record
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionaries."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                # Handle list of dictionaries
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item, f"{new_key}_{i}", sep=sep).items())
                    else:
                        items.append((f"{new_key}_{i}", item))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _process_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single record before export."""
        # Filter fields
        record = self._filter_fields(record)
        
        # Flatten if requested
        if self.config.flatten_nested:
            record = self._flatten_dict(record)
        
        # Format dates
        for key, value in record.items():
            if isinstance(value, datetime):
                record[key] = value.strftime(self.config.date_format)
        
        return record
    
    def _add_compression(self, file_path: Path) -> Path:
        """Add compression to the output file."""
        if self.config.compression == CompressionType.NONE:
            return file_path
        
        compressed_path = file_path.with_suffix(f"{file_path.suffix}.{self.config.compression.value}")
        
        try:
            if self.config.compression == CompressionType.ZIP:
                with zipfile.ZipFile(compressed_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(file_path, file_path.name)
                os.remove(file_path)
            else:
                import gzip
                import bz2
                import lzma
                
                compression_modules = {
                    CompressionType.GZIP: gzip,
                    CompressionType.BZIP2: bz2,
                    CompressionType.XZ: lzma
                }
                
                module = compression_modules[self.config.compression]
                with open(file_path, 'rb') as f_in:
                    with module.open(compressed_path, 'wb') as f_out:
                        f_out.write(f_in.read())
                os.remove(file_path)
            
            return compressed_path
        except Exception as e:
            self.errors.append(f"Compression failed: {str(e)}")
            return file_path


class JSONLExporter(BaseExporter):
    """Exporter for JSONL format (JSON Lines)."""
    
    def export(self, data: Iterator[Dict[str, Any]]) -> ExportResult:
        start_time = time.time()
        output_path = self._prepare_output_path()
        records_exported = 0
        
        try:
            with open(output_path, 'w', encoding=self.config.encoding) as f:
                for record in data:
                    processed_record = self._process_record(record)
                    json.dump(processed_record, f, ensure_ascii=False, default=str)
                    f.write('\n')
                    records_exported += 1
            
            # Apply compression if requested
            final_path = self._add_compression(output_path)
            file_size = final_path.stat().st_size
            
            return ExportResult(
                success=True,
                output_path=str(final_path),
                records_exported=records_exported,
                file_size_bytes=file_size,
                export_time_seconds=time.time() - start_time,
                format=ExportFormat.JSONL,
                compression=self.config.compression,
                errors=self.errors.copy() if self.errors else None
            )
            
        except Exception as e:
            logger.error(f"JSONL export failed: {str(e)}")
            return ExportResult(
                success=False,
                output_path=str(output_path),
                records_exported=records_exported,
                file_size_bytes=0,
                export_time_seconds=time.time() - start_time,
                format=ExportFormat.JSONL,
                compression=self.config.compression,
                errors=[str(e)]
            )


class JSONExporter(BaseExporter):
    """Exporter for JSON format."""
    
    def export(self, data: Iterator[Dict[str, Any]]) -> ExportResult:
        start_time = time.time()
        output_path = self._prepare_output_path()
        records_exported = 0
        
        try:
            # Collect all records
            records = []
            for record in data:
                processed_record = self._process_record(record)
                records.append(processed_record)
                records_exported += 1
            
            # Write as JSON array
            with open(output_path, 'w', encoding=self.config.encoding) as f:
                json.dump(records, f, ensure_ascii=False, indent=self.config.json_indent, default=str)
            
            # Apply compression if requested
            final_path = self._add_compression(output_path)
            file_size = final_path.stat().st_size
            
            return ExportResult(
                success=True,
                output_path=str(final_path),
                records_exported=records_exported,
                file_size_bytes=file_size,
                export_time_seconds=time.time() - start_time,
                format=ExportFormat.JSON,
                compression=self.config.compression,
                errors=self.errors.copy() if self.errors else None
            )
            
        except Exception as e:
            logger.error(f"JSON export failed: {str(e)}")
            return ExportResult(
                success=False,
                output_path=str(output_path),
                records_exported=records_exported,
                file_size_bytes=0,
                export_time_seconds=time.time() - start_time,
                format=ExportFormat.JSON,
                compression=self.config.compression,
                errors=[str(e)]
            )


class ParquetExporter(BaseExporter):
    """Exporter for Parquet format."""
    
    def export(self, data: Iterator[Dict[str, Any]]) -> ExportResult:
        if not PARQUET_AVAILABLE:
            raise ImportError("PyArrow is required for Parquet export. Install with: pip install pyarrow")
        
        start_time = time.time()
        output_path = self._prepare_output_path()
        records_exported = 0
        
        try:
            # Collect records and convert to DataFrame
            records = []
            for record in data:
                processed_record = self._process_record(record)
                records.append(processed_record)
                records_exported += 1
            
            if records:
                df = pd.DataFrame(records)
                # Convert to Parquet
                df.to_parquet(
                    output_path,
                    compression=self.config.parquet_compression,
                    index=False
                )
            else:
                # Create empty Parquet file
                df = pd.DataFrame()
                df.to_parquet(output_path, index=False)
            
            # Apply compression if requested (note: Parquet has built-in compression)
            final_path = self._add_compression(output_path) if self.config.compression != CompressionType.NONE else output_path
            file_size = final_path.stat().st_size
            
            return ExportResult(
                success=True,
                output_path=str(final_path),
                records_exported=records_exported,
                file_size_bytes=file_size,
                export_time_seconds=time.time() - start_time,
                format=ExportFormat.PARQUET,
                compression=self.config.compression,
                errors=self.errors.copy() if self.errors else None
            )
            
        except Exception as e:
            logger.error(f"Parquet export failed: {str(e)}")
            return ExportResult(
                success=False,
                output_path=str(output_path),
                records_exported=records_exported,
                file_size_bytes=0,
                export_time_seconds=time.time() - start_time,
                format=ExportFormat.PARQUET,
                compression=self.config.compression,
                errors=[str(e)]
            )


class CSVExporter(BaseExporter):
    """Exporter for CSV format."""
    
    def export(self, data: Iterator[Dict[str, Any]]) -> ExportResult:
        start_time = time.time()
        output_path = self._prepare_output_path()
        records_exported = 0
        
        try:
            # Collect records to determine all fieldnames
            records = []
            fieldnames = set()
            
            for record in data:
                processed_record = self._process_record(record)
                records.append(processed_record)
                fieldnames.update(processed_record.keys())
                records_exported += 1
            
            fieldnames = sorted(list(fieldnames))
            
            # Write CSV
            with open(output_path, 'w', newline='', encoding=self.config.encoding) as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=fieldnames,
                    delimiter=self.config.csv_delimiter,
                    quoting=self.config.csv_quoting
                )
                writer.writeheader()
                writer.writerows(records)
            
            # Apply compression if requested
            final_path = self._add_compression(output_path)
            file_size = final_path.stat().st_size
            
            return ExportResult(
                success=True,
                output_path=str(final_path),
                records_exported=records_exported,
                file_size_bytes=file_size,
                export_time_seconds=time.time() - start_time,
                format=ExportFormat.CSV,
                compression=self.config.compression,
                errors=self.errors.copy() if self.errors else None
            )
            
        except Exception as e:
            logger.error(f"CSV export failed: {str(e)}")
            return ExportResult(
                success=False,
                output_path=str(output_path),
                records_exported=records_exported,
                file_size_bytes=0,
                export_time_seconds=time.time() - start_time,
                format=ExportFormat.CSV,
                compression=self.config.compression,
                errors=[str(e)]
            )


class XMLExporter(BaseExporter):
    """Exporter for XML format."""
    
    def export(self, data: Iterator[Dict[str, Any]]) -> ExportResult:
        start_time = time.time()
        output_path = self._prepare_output_path()
        records_exported = 0
        
        try:
            root = ET.Element(self.config.xml_root_element)
            
            for record in data:
                processed_record = self._process_record(record)
                item_elem = ET.SubElement(root, self.config.xml_item_element)
                self._dict_to_xml(processed_record, item_elem)
                records_exported += 1
            
            # Write XML
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ", level=0)
            tree.write(output_path, encoding=self.config.encoding, xml_declaration=True)
            
            # Apply compression if requested
            final_path = self._add_compression(output_path)
            file_size = final_path.stat().st_size
            
            return ExportResult(
                success=True,
                output_path=str(final_path),
                records_exported=records_exported,
                file_size_bytes=file_size,
                export_time_seconds=time.time() - start_time,
                format=ExportFormat.XML,
                compression=self.config.compression,
                errors=self.errors.copy() if self.errors else None
            )
            
        except Exception as e:
            logger.error(f"XML export failed: {str(e)}")
            return ExportResult(
                success=False,
                output_path=str(output_path),
                records_exported=records_exported,
                file_size_bytes=0,
                export_time_seconds=time.time() - start_time,
                format=ExportFormat.XML,
                compression=self.config.compression,
                errors=[str(e)]
            )
    
    def _dict_to_xml(self, data: Dict[str, Any], parent: ET.Element):
        """Convert dictionary to XML elements."""
        for key, value in data.items():
            # Sanitize element name
            elem_name = str(key).replace(' ', '_').replace('-', '_')
            elem = ET.SubElement(parent, elem_name)
            
            if isinstance(value, dict):
                self._dict_to_xml(value, elem)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    item_elem = ET.SubElement(elem, f"item_{i}")
                    if isinstance(item, dict):
                        self._dict_to_xml(item, item_elem)
                    else:
                        item_elem.text = str(item)
            else:
                elem.text = str(value)


class CustomExporter(BaseExporter):
    """Exporter for custom formats using templates or processors."""
    
    def export(self, data: Iterator[Dict[str, Any]]) -> ExportResult:
        start_time = time.time()
        output_path = self._prepare_output_path()
        records_exported = 0
        
        try:
            if self.config.custom_processor:
                # Use custom processor function
                result = self.config.custom_processor(data, self.config)
                records_exported = result.get('records_exported', 0)
            else:
                # Use template-based export
                with open(output_path, 'w', encoding=self.config.encoding) as f:
                    for record in data:
                        processed_record = self._process_record(record)
                        if self.config.custom_template:
                            output_line = self.config.custom_template.format(**processed_record)
                        else:
                            output_line = str(processed_record)
                        f.write(output_line + '\n')
                        records_exported += 1
            
            # Apply compression if requested
            final_path = self._add_compression(output_path)
            file_size = final_path.stat().st_size
            
            return ExportResult(
                success=True,
                output_path=str(final_path),
                records_exported=records_exported,
                file_size_bytes=file_size,
                export_time_seconds=time.time() - start_time,
                format=ExportFormat.CUSTOM,
                compression=self.config.compression,
                errors=self.errors.copy() if self.errors else None
            )
            
        except Exception as e:
            logger.error(f"Custom export failed: {str(e)}")
            return ExportResult(
                success=False,
                output_path=str(output_path),
                records_exported=records_exported,
                file_size_bytes=0,
                export_time_seconds=time.time() - start_time,
                format=ExportFormat.CUSTOM,
                compression=self.config.compression,
                errors=[str(e)]
            )


class ExportManager:
    """Main export manager that coordinates all export operations."""
    
    def __init__(self):
        self.exporters = {
            ExportFormat.JSONL: JSONLExporter,
            ExportFormat.JSON: JSONExporter,
            ExportFormat.PARQUET: ParquetExporter,
            ExportFormat.CSV: CSVExporter,
            ExportFormat.TSV: lambda config: CSVExporter({**asdict(config), 'csv_delimiter': '\t'}),
            ExportFormat.XML: XMLExporter,
            ExportFormat.CUSTOM: CustomExporter
        }
    
    def export(self, data: Union[List[Dict[str, Any]], Iterator[Dict[str, Any]]], config: ExportConfig) -> ExportResult:
        """Export data using the specified configuration."""
        if config.format not in self.exporters:
            raise ValueError(f"Unsupported export format: {config.format}")
        
        # Convert list to iterator if needed
        if isinstance(data, list):
            data = iter(data)
        
        exporter_class = self.exporters[config.format]
        exporter = exporter_class(config)
        
        return exporter.export(data)
    
    def batch_export(self, data: Union[List[Dict[str, Any]], Iterator[Dict[str, Any]]], 
                    configs: List[ExportConfig]) -> List[ExportResult]:
        """Export data to multiple formats simultaneously."""
        results = []
        
        # Convert data to list to allow multiple iterations
        if hasattr(data, '__iter__') and not isinstance(data, list):
            data = list(data)
        
        for config in configs:
            result = self.export(data, config)
            results.append(result)
        
        return results
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats."""
        return [fmt.value for fmt in ExportFormat]
    
    def validate_config(self, config: ExportConfig) -> List[str]:
        """Validate export configuration and return any errors."""
        errors = []
        
        # Check format support
        if config.format not in self.exporters:
            errors.append(f"Unsupported format: {config.format}")
        
        # Check Parquet dependencies
        if config.format == ExportFormat.PARQUET and not PARQUET_AVAILABLE:
            errors.append("PyArrow is required for Parquet export. Install with: pip install pyarrow")
        
        # Check output path
        try:
            output_path = Path(config.output_path)
            if not output_path.parent.exists():
                output_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Invalid output path: {str(e)}")
        
        # Check custom format requirements
        if config.format == ExportFormat.CUSTOM:
            if not config.custom_template and not config.custom_processor:
                errors.append("Custom format requires either custom_template or custom_processor")
        
        return errors


# Utility functions for common export scenarios
def export_chunks_to_jsonl(chunks: List[Dict[str, Any]], output_path: str, **kwargs) -> ExportResult:
    """Convenience function to export chunks to JSONL format."""
    config = ExportConfig(
        format=ExportFormat.JSONL,
        output_path=output_path,
        **kwargs
    )
    manager = ExportManager()
    return manager.export(chunks, config)


def export_chunks_to_parquet(chunks: List[Dict[str, Any]], output_path: str, **kwargs) -> ExportResult:
    """Convenience function to export chunks to Parquet format."""
    config = ExportConfig(
        format=ExportFormat.PARQUET,
        output_path=output_path,
        **kwargs
    )
    manager = ExportManager()
    return manager.export(chunks, config)


def export_chunks_to_csv(chunks: List[Dict[str, Any]], output_path: str, **kwargs) -> ExportResult:
    """Convenience function to export chunks to CSV format."""
    # Set default flatten_nested=True for CSV if not specified
    if 'flatten_nested' not in kwargs:
        kwargs['flatten_nested'] = True
    
    config = ExportConfig(
        format=ExportFormat.CSV,
        output_path=output_path,
        **kwargs
    )
    manager = ExportManager()
    return manager.export(chunks, config)
