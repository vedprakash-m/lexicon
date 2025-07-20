import json
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
import gzip
import zipfile
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import logging
from datetime import datetime

@dataclass
class ExportConfig:
    format: str
    compression: Optional[str] = None
    include_metadata: bool = True
    include_chunks: bool = True
    include_relationships: bool = False
    custom_fields: List[str] = None
    output_structure: str = "flat"  # "flat", "nested", "hierarchical"

class ExportManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def export_data(self, data: List[Dict], config: ExportConfig, output_path: str) -> bool:
        """Export data in specified format"""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if config.format.lower() == 'json':
                return self._export_json(data, config, output_path)
            elif config.format.lower() == 'jsonl':
                return self._export_jsonl(data, config, output_path)
            elif config.format.lower() == 'csv':
                return self._export_csv(data, config, output_path)
            elif config.format.lower() == 'parquet':
                return self._export_parquet(data, config, output_path)
            elif config.format.lower() == 'xml':
                return self._export_xml(data, config, output_path)
            elif config.format.lower() == 'langchain':
                return self._export_langchain(data, config, output_path)
            elif config.format.lower() == 'llamaindex':
                return self._export_llamaindex(data, config, output_path)
            elif config.format.lower() == 'haystack':
                return self._export_haystack(data, config, output_path)
            elif config.format.lower() == 'markdown':
                return self._export_markdown(data, config, output_path)
            else:
                raise ValueError(f"Unsupported export format: {config.format}")
                
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return False
            
    def _export_json(self, data: List[Dict], config: ExportConfig, output_path: Path) -> bool:
        """Export as JSON"""
        processed_data = self._process_data_for_export(data, config)
        
        json_data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'format': 'json',
                'total_records': len(processed_data),
                'config': asdict(config)
            },
            'data': processed_data
        }
        
        if config.compression == 'gzip':
            with gzip.open(f"{output_path}.gz", 'wt', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
                
        return True
        
    def _export_jsonl(self, data: List[Dict], config: ExportConfig, output_path: Path) -> bool:
        """Export as JSONL (JSON Lines)"""
        processed_data = self._process_data_for_export(data, config)
        
        if config.compression == 'gzip':
            with gzip.open(f"{output_path}.gz", 'wt', encoding='utf-8') as f:
                for record in processed_data:
                    json.dump(record, f, ensure_ascii=False)
                    f.write('\n')
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                for record in processed_data:
                    json.dump(record, f, ensure_ascii=False)
                    f.write('\n')
                    
        return True
        
    def _export_csv(self, data: List[Dict], config: ExportConfig, output_path: Path) -> bool:
        """Export as CSV"""
        processed_data = self._process_data_for_export(data, config)
        
        if not processed_data:
            return False
            
        # Flatten nested data for CSV
        flattened_data = []
        for record in processed_data:
            flat_record = self._flatten_dict(record)
            flattened_data.append(flat_record)
            
        # Get all possible fieldnames
        fieldnames = set()
        for record in flattened_data:
            fieldnames.update(record.keys())
        fieldnames = sorted(list(fieldnames))
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flattened_data)
            
        return True
        
    def _export_parquet(self, data: List[Dict], config: ExportConfig, output_path: Path) -> bool:
        """Export as Parquet"""
        processed_data = self._process_data_for_export(data, config)
        
        # Flatten data for DataFrame
        flattened_data = []
        for record in processed_data:
            flat_record = self._flatten_dict(record)
            flattened_data.append(flat_record)
            
        df = pd.DataFrame(flattened_data)
        
        # Handle compression
        compression = None
        if config.compression == 'gzip':
            compression = 'gzip'
        elif config.compression == 'snappy':
            compression = 'snappy'
            
        df.to_parquet(output_path, compression=compression, index=False)
        return True
        
    def _export_xml(self, data: List[Dict], config: ExportConfig, output_path: Path) -> bool:
        """Export as XML"""
        processed_data = self._process_data_for_export(data, config)
        
        root = ET.Element('export')
        
        # Add metadata
        metadata = ET.SubElement(root, 'metadata')
        ET.SubElement(metadata, 'timestamp').text = datetime.now().isoformat()
        ET.SubElement(metadata, 'format').text = 'xml'
        ET.SubElement(metadata, 'total_records').text = str(len(processed_data))
        
        # Add data
        data_element = ET.SubElement(root, 'data')
        
        for record in processed_data:
            record_element = ET.SubElement(data_element, 'record')
            self._dict_to_xml(record, record_element)
            
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        return True
        
    def _export_langchain(self, data: List[Dict], config: ExportConfig, output_path: Path) -> bool:
        """Export in LangChain compatible format"""
        langchain_data = []
        
        for record in data:
            # LangChain Document format
            doc = {
                'page_content': record.get('text', ''),
                'metadata': {
                    'source': record.get('source', ''),
                    'title': record.get('title', ''),
                    'author': record.get('author', ''),
                    'chunk_id': record.get('id', ''),
                    'chunk_index': record.get('chunk_index', 0),
                    'word_count': len(record.get('text', '').split()),
                }
            }
            
            # Add custom metadata
            if config.include_metadata and 'metadata' in record:
                doc['metadata'].update(record['metadata'])
                
            langchain_data.append(doc)
            
        # Save as JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(langchain_data, f, indent=2, ensure_ascii=False)
            
        return True
        
    def _export_llamaindex(self, data: List[Dict], config: ExportConfig, output_path: Path) -> bool:
        """Export in LlamaIndex compatible format"""
        llamaindex_data = []
        
        for record in data:
            # LlamaIndex Document format
            doc = {
                'text': record.get('text', ''),
                'doc_id': record.get('id', ''),
                'embedding': None,  # Will be generated by LlamaIndex
                'metadata': {
                    'source': record.get('source', ''),
                    'title': record.get('title', ''),
                    'author': record.get('author', ''),
                    'chunk_index': record.get('chunk_index', 0),
                }
            }
            
            # Add custom metadata
            if config.include_metadata and 'metadata' in record:
                doc['metadata'].update(record['metadata'])
                
            llamaindex_data.append(doc)
            
        # Save as JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(llamaindex_data, f, indent=2, ensure_ascii=False)
            
        return True
        
    def _export_haystack(self, data: List[Dict], config: ExportConfig, output_path: Path) -> bool:
        """Export in Haystack compatible format"""
        haystack_data = []
        
        for record in data:
            # Haystack Document format
            doc = {
                'content': record.get('text', ''),
                'id': record.get('id', ''),
                'meta': {
                    'source': record.get('source', ''),
                    'title': record.get('title', ''),
                    'author': record.get('author', ''),
                    'chunk_index': record.get('chunk_index', 0),
                    'word_count': len(record.get('text', '').split()),
                }
            }
            
            # Add custom metadata
            if config.include_metadata and 'metadata' in record:
                doc['meta'].update(record['metadata'])
                
            haystack_data.append(doc)
            
        # Save as JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(haystack_data, f, indent=2, ensure_ascii=False)
            
        return True
        
    def _export_markdown(self, data: List[Dict], config: ExportConfig, output_path: Path) -> bool:
        """Export as Markdown"""
        markdown_content = []
        
        # Add header
        markdown_content.append("# Exported Data\n")
        markdown_content.append(f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        markdown_content.append(f"**Total Records:** {len(data)}\n\n")
        
        for i, record in enumerate(data):
            # Record header
            title = record.get('title', f'Record {i+1}')
            markdown_content.append(f"## {title}\n")
            
            # Metadata
            if config.include_metadata and 'metadata' in record:
                markdown_content.append("### Metadata\n")
                for key, value in record['metadata'].items():
                    markdown_content.append(f"- **{key}:** {value}\n")
                markdown_content.append("\n")
                
            # Content
            if 'text' in record:
                markdown_content.append("### Content\n")
                markdown_content.append(f"{record['text']}\n\n")
                
            # Separator
            markdown_content.append("---\n\n")
            
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(markdown_content)
            
        return True
        
    def _process_data_for_export(self, data: List[Dict], config: ExportConfig) -> List[Dict]:
        """Process data based on export configuration"""
        processed_data = []
        
        for record in data:
            processed_record = {}
            
            # Always include basic fields
            for field in ['id', 'text', 'title', 'author', 'source']:
                if field in record:
                    processed_record[field] = record[field]
                    
            # Include metadata if requested
            if config.include_metadata and 'metadata' in record:
                if config.output_structure == 'flat':
                    # Flatten metadata into main record
                    for key, value in record['metadata'].items():
                        processed_record[f"metadata_{key}"] = value
                else:
                    processed_record['metadata'] = record['metadata']
                    
            # Include chunks if requested
            if config.include_chunks and 'chunks' in record:
                processed_record['chunks'] = record['chunks']
                
            # Include relationships if requested
            if config.include_relationships and 'relationships' in record:
                processed_record['relationships'] = record['relationships']
                
            # Include custom fields
            if config.custom_fields:
                for field in config.custom_fields:
                    if field in record:
                        processed_record[field] = record[field]
                        
            processed_data.append(processed_record)
            
        return processed_data
        
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert lists to strings for CSV compatibility
                items.append((new_key, json.dumps(v) if v else ''))
            else:
                items.append((new_key, v))
        return dict(items)
        
    def _dict_to_xml(self, d: Dict, parent: ET.Element):
        """Convert dictionary to XML elements"""
        for key, value in d.items():
            # Clean key name for XML
            clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', str(key))
            
            if isinstance(value, dict):
                child = ET.SubElement(parent, clean_key)
                self._dict_to_xml(value, child)
            elif isinstance(value, list):
                for item in value:
                    child = ET.SubElement(parent, clean_key)
                    if isinstance(item, dict):
                        self._dict_to_xml(item, child)
                    else:
                        child.text = str(item)
            else:
                child = ET.SubElement(parent, clean_key)
                child.text = str(value) if value is not None else ''
                
    def create_obsidian_export(self, data: List[Dict], output_dir: str) -> bool:
        """Create Obsidian-compatible export"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            for record in data:
                # Create filename from title
                title = record.get('title', f"Document_{record.get('id', 'unknown')}")
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                filename = f"{safe_title}.md"
                
                # Create markdown content
                content = []
                content.append(f"# {title}\n")
                
                # Add metadata as YAML frontmatter
                if 'metadata' in record:
                    content.append("---\n")
                    for key, value in record['metadata'].items():
                        content.append(f"{key}: {value}\n")
                    content.append("---\n\n")
                    
                # Add main content
                if 'text' in record:
                    content.append(record['text'])
                    
                # Add tags
                if 'keywords' in record:
                    content.append(f"\n\n## Tags\n")
                    for keyword in record['keywords']:
                        content.append(f"#{keyword} ")
                        
                # Write file
                with open(output_path / filename, 'w', encoding='utf-8') as f:
                    f.writelines(content)
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Obsidian export failed: {e}")
            return False
            
    def create_notion_export(self, data: List[Dict], output_path: str) -> bool:
        """Create Notion-compatible CSV export"""
        try:
            notion_data = []
            
            for record in data:
                notion_record = {
                    'Name': record.get('title', ''),
                    'Content': record.get('text', ''),
                    'Author': record.get('author', ''),
                    'Source': record.get('source', ''),
                    'Tags': ', '.join(record.get('keywords', [])),
                    'Created': datetime.now().strftime('%Y-%m-%d'),
                }
                
                # Add metadata fields
                if 'metadata' in record:
                    for key, value in record['metadata'].items():
                        notion_record[f"Meta_{key}"] = str(value)
                        
                notion_data.append(notion_record)
                
            # Export as CSV
            if notion_data:
                fieldnames = list(notion_data[0].keys())
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(notion_data)
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Notion export failed: {e}")
            return False
            
    def create_archive_export(self, data: List[Dict], output_path: str, include_assets: bool = True) -> bool:
        """Create complete archive export"""
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Export data in multiple formats
                formats = ['json', 'jsonl', 'csv', 'markdown']
                
                for fmt in formats:
                    config = ExportConfig(format=fmt, include_metadata=True)
                    temp_path = f"temp_export.{fmt}"
                    
                    if self.export_data(data, config, temp_path):
                        zipf.write(temp_path, f"data/export.{fmt}")
                        Path(temp_path).unlink()  # Clean up temp file
                        
                # Add metadata file
                metadata = {
                    'export_timestamp': datetime.now().isoformat(),
                    'total_records': len(data),
                    'formats_included': formats,
                    'version': '1.0'
                }
                
                zipf.writestr('metadata.json', json.dumps(metadata, indent=2))
                
                # Add README
                readme_content = """# Lexicon Export Archive

This archive contains your processed data in multiple formats:

- `data/export.json` - Complete data in JSON format
- `data/export.jsonl` - Data in JSON Lines format (one record per line)
- `data/export.csv` - Tabular data in CSV format
- `data/export.markdown` - Human-readable Markdown format
- `metadata.json` - Export metadata and information

## Usage

Choose the format that best fits your needs:
- JSON/JSONL for programmatic access
- CSV for spreadsheet applications
- Markdown for documentation or review

Generated by Lexicon - Universal RAG Dataset Preparation Tool
"""
                zipf.writestr('README.md', readme_content)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Archive export failed: {e}")
            return False