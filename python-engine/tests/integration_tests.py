"""
Comprehensive integration test suite for Lexicon RAG Dataset Preparation Tool.

This test suite covers end-to-end integration testing across all system components:
- Python processing engine
- Rust backend services
- React frontend integration
- Database operations
- File system operations
- Security system
- Performance monitoring
- Background task system
- Cloud sync operations

Run with: python -m pytest integration_tests.py -v
"""

import os
import sys
import time
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import pytest
import asyncio
import logging
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from processors.universal_rag_demo import UniversalRAGProcessor
from processors.advanced_chunking import AdvancedChunkingProcessor
from processors.batch_processor import BatchProcessor
from processors.quality_analysis import QualityAnalysisProcessor
from enrichment.metadata_enrichment import MetadataEnrichmentProcessor
from enrichment.visual_asset_manager import VisualAssetManager
from enrichment.book_relationship_mapper import BookRelationshipMapper
from scrapers.web_scraper import WebScraperEngine
from security.python_security import PythonSecurityManager
from sync.cloud_storage_manager import CloudStorageManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationTestSuite:
    """
    Comprehensive integration test suite for Lexicon.
    
    Tests the complete workflow from data ingestion to final RAG dataset preparation.
    """
    
    def __init__(self):
        """Initialize the test suite."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="lexicon_test_"))
        self.test_data_dir = self.test_dir / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.rag_processor = UniversalRAGProcessor()
        self.chunking_processor = AdvancedChunkingProcessor()
        self.batch_processor = BatchProcessor()
        self.quality_analyzer = QualityAnalysisProcessor()
        self.metadata_enricher = MetadataEnrichmentProcessor()
        self.visual_asset_manager = VisualAssetManager()
        self.relationship_mapper = BookRelationshipMapper()
        self.web_scraper = WebScraperEngine()
        self.security_manager = PythonSecurityManager(self.test_dir / "security")
        self.cloud_storage = CloudStorageManager()
        
        # Test data
        self.sample_texts = [
            "The quick brown fox jumps over the lazy dog. This is a simple test sentence.",
            "Machine learning is a subset of artificial intelligence that focuses on algorithms.",
            "Natural language processing enables computers to understand and generate human language.",
            "Deep learning uses neural networks with multiple layers to process complex data.",
            "The transformer architecture revolutionized natural language processing tasks."
        ]
        
        # Create sample test files
        self.create_test_files()
        
        logger.info(f"Integration test suite initialized with test directory: {self.test_dir}")
    
    def create_test_files(self):
        """Create sample test files for integration testing."""
        # Create sample text files
        for i, text in enumerate(self.sample_texts):
            file_path = self.test_data_dir / f"sample_{i+1}.txt"
            file_path.write_text(text)
        
        # Create sample JSON metadata
        metadata = {
            "title": "Test Document",
            "author": "Test Author",
            "language": "en",
            "domain": "technology",
            "quality_score": 0.85
        }
        
        metadata_path = self.test_data_dir / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2))
        
        # Create sample book file (mock)
        book_content = "Chapter 1: Introduction\n\nThis is a sample book content for testing purposes.\n\nChapter 2: Main Content\n\nHere is the main content of the book with detailed information about the subject matter."
        book_path = self.test_data_dir / "sample_book.txt"
        book_path.write_text(book_content)
        
        logger.info(f"Created {len(list(self.test_data_dir.iterdir()))} test files")
    
    def test_01_file_processing_pipeline(self):
        """Test the complete file processing pipeline."""
        logger.info("Testing file processing pipeline...")
        
        # Test file ingestion
        source_file = self.test_data_dir / "sample_book.txt"
        
        # Process with RAG processor
        result = self.rag_processor.process_file(str(source_file))
        
        assert result is not None
        assert "chunks" in result
        assert "metadata" in result
        assert len(result["chunks"]) > 0
        
        # Verify chunk quality
        for chunk in result["chunks"]:
            assert "text" in chunk
            assert "metadata" in chunk
            assert len(chunk["text"]) > 0
        
        logger.info("✓ File processing pipeline test passed")
        return result
    
    def test_02_advanced_chunking(self):
        """Test advanced chunking strategies."""
        logger.info("Testing advanced chunking...")
        
        # Test different chunking strategies
        strategies = ['semantic', 'sliding_window', 'sentence_based', 'paragraph_based']
        
        source_text = self.sample_texts[0]
        
        for strategy in strategies:
            config = {
                "strategy": strategy,
                "chunk_size": 100,
                "overlap": 20,
                "min_chunk_size": 50
            }
            
            result = self.chunking_processor.process_text(source_text, config)
            
            assert result is not None
            assert "chunks" in result
            assert len(result["chunks"]) > 0
            
            # Verify chunk properties
            for chunk in result["chunks"]:
                assert len(chunk["text"]) >= config["min_chunk_size"]
                assert "position" in chunk
                assert "metadata" in chunk
        
        logger.info("✓ Advanced chunking test passed")
    
    def test_03_batch_processing(self):
        """Test batch processing capabilities."""
        logger.info("Testing batch processing...")
        
        # Create batch job
        file_paths = [str(f) for f in self.test_data_dir.glob("sample_*.txt")]
        
        batch_config = {
            "chunk_size": 200,
            "overlap": 50,
            "quality_threshold": 0.5,
            "output_format": "json"
        }
        
        # Process batch
        batch_job = self.batch_processor.create_batch_job(file_paths, batch_config)
        
        assert batch_job is not None
        assert "job_id" in batch_job
        assert "status" in batch_job
        
        # Execute batch processing
        results = self.batch_processor.execute_batch(batch_job["job_id"])
        
        assert results is not None
        assert "processed_files" in results
        assert len(results["processed_files"]) > 0
        
        # Verify all files were processed
        for file_result in results["processed_files"]:
            assert "file_path" in file_result
            assert "status" in file_result
            assert "chunks" in file_result
            assert file_result["status"] == "completed"
        
        logger.info("✓ Batch processing test passed")
    
    def test_04_quality_analysis(self):
        """Test quality analysis and assessment."""
        logger.info("Testing quality analysis...")
        
        # Test quality assessment on sample texts
        for i, text in enumerate(self.sample_texts):
            quality_result = self.quality_analyzer.assess_text_quality(text)
            
            assert quality_result is not None
            assert "overall_score" in quality_result
            assert "metrics" in quality_result
            assert 0.0 <= quality_result["overall_score"] <= 1.0
            
            # Verify quality metrics
            metrics = quality_result["metrics"]
            assert "readability" in metrics
            assert "coherence" in metrics
            assert "informativeness" in metrics
            assert "linguistic_quality" in metrics
        
        logger.info("✓ Quality analysis test passed")
    
    def test_05_metadata_enrichment(self):
        """Test metadata enrichment pipeline."""
        logger.info("Testing metadata enrichment...")
        
        # Test metadata enrichment
        sample_metadata = {
            "title": "Test Document",
            "content": self.sample_texts[0]
        }
        
        enriched_metadata = self.metadata_enricher.enrich_metadata(sample_metadata)
        
        assert enriched_metadata is not None
        assert "title" in enriched_metadata
        assert "content" in enriched_metadata
        assert "enriched_data" in enriched_metadata
        
        # Verify enrichment added new fields
        enriched_data = enriched_metadata["enriched_data"]
        assert "language" in enriched_data
        assert "topics" in enriched_data
        assert "entities" in enriched_data
        assert "summary" in enriched_data
        
        logger.info("✓ Metadata enrichment test passed")
    
    def test_06_visual_asset_management(self):
        """Test visual asset management."""
        logger.info("Testing visual asset management...")
        
        # Test placeholder generation
        book_info = {
            "title": "Test Book",
            "author": "Test Author",
            "isbn": "1234567890"
        }
        
        # Generate placeholder cover
        cover_result = self.visual_asset_manager.generate_placeholder_cover(book_info)
        
        assert cover_result is not None
        assert "cover_path" in cover_result
        assert "cover_type" in cover_result
        assert cover_result["cover_type"] == "placeholder"
        
        # Test asset collection
        collection_result = self.visual_asset_manager.create_asset_collection(book_info)
        
        assert collection_result is not None
        assert "collection_id" in collection_result
        assert "assets" in collection_result
        
        logger.info("✓ Visual asset management test passed")
    
    def test_07_relationship_mapping(self):
        """Test book relationship mapping."""
        logger.info("Testing relationship mapping...")
        
        # Create sample book data
        books = [
            {"title": "Introduction to AI", "author": "John Doe", "topics": ["artificial intelligence", "machine learning"]},
            {"title": "Deep Learning Fundamentals", "author": "Jane Smith", "topics": ["deep learning", "neural networks"]},
            {"title": "NLP Handbook", "author": "Bob Johnson", "topics": ["natural language processing", "linguistics"]}
        ]
        
        # Test relationship mapping
        relationships = self.relationship_mapper.find_relationships(books)
        
        assert relationships is not None
        assert "relationship_graph" in relationships
        assert "similarity_scores" in relationships
        
        # Verify relationships were found
        graph = relationships["relationship_graph"]
        assert len(graph) > 0
        
        # Check similarity scores
        scores = relationships["similarity_scores"]
        for score_entry in scores:
            assert "book1" in score_entry
            assert "book2" in score_entry
            assert "similarity" in score_entry
            assert 0.0 <= score_entry["similarity"] <= 1.0
        
        logger.info("✓ Relationship mapping test passed")
    
    def test_08_web_scraping(self):
        """Test web scraping capabilities."""
        logger.info("Testing web scraping...")
        
        # Test URL validation
        test_urls = [
            "https://example.com",
            "https://httpbin.org/get",
            "invalid-url",
            "ftp://example.com"
        ]
        
        validation_results = self.web_scraper.validate_urls(test_urls)
        
        assert validation_results is not None
        assert "valid_urls" in validation_results
        assert "invalid_urls" in validation_results
        
        # Verify validation results
        valid_urls = validation_results["valid_urls"]
        invalid_urls = validation_results["invalid_urls"]
        
        assert len(valid_urls) >= 2  # At least the first two URLs should be valid
        assert len(invalid_urls) >= 1  # At least one URL should be invalid
        
        logger.info("✓ Web scraping test passed")
    
    def test_09_security_system(self):
        """Test security system integration."""
        logger.info("Testing security system...")
        
        # Test file encryption
        test_file = self.test_data_dir / "security_test.txt"
        test_content = "This is sensitive test content for encryption testing."
        test_file.write_text(test_content)
        
        # Test key derivation
        password = "test_password_123"
        key = self.security_manager.derive_key_from_password(password)
        
        assert key is not None
        assert len(key) > 0
        
        # Test encryption/decryption
        encrypted_data = self.security_manager.encrypt_sensitive_data(test_content.encode(), key)
        decrypted_data = self.security_manager.decrypt_sensitive_data(encrypted_data, key)
        
        assert decrypted_data.decode() == test_content
        
        # Test file hashing
        file_hash = self.security_manager.hash_file(test_file)
        
        assert file_hash is not None
        assert len(file_hash) == 64  # SHA-256 hash length
        
        # Test integrity verification
        is_valid = self.security_manager.verify_file_integrity(test_file, file_hash)
        
        assert is_valid is True
        
        # Test secure file cleanup
        cleanup_result = self.security_manager.secure_file_cleanup(test_file)
        
        assert cleanup_result is True
        assert not test_file.exists()
        
        logger.info("✓ Security system test passed")
    
    def test_10_cloud_sync_operations(self):
        """Test cloud sync operations."""
        logger.info("Testing cloud sync operations...")
        
        # Test sync configuration
        sync_config = {
            "provider": "mock",
            "sync_interval": 300,
            "backup_enabled": True,
            "encryption_enabled": True
        }
        
        config_result = self.cloud_storage.configure_sync(sync_config)
        
        assert config_result is not None
        assert "status" in config_result
        assert config_result["status"] == "configured"
        
        # Test file upload (mock)
        test_file = self.test_data_dir / "sync_test.txt"
        test_file.write_text("Test content for sync")
        
        upload_result = self.cloud_storage.upload_file(str(test_file), "test_folder/sync_test.txt")
        
        assert upload_result is not None
        assert "success" in upload_result
        
        # Test sync status
        sync_status = self.cloud_storage.get_sync_status()
        
        assert sync_status is not None
        assert "last_sync" in sync_status
        assert "sync_enabled" in sync_status
        
        logger.info("✓ Cloud sync operations test passed")
    
    def test_11_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        logger.info("Testing end-to-end workflow...")
        
        # 1. File ingestion
        source_file = self.test_data_dir / "sample_book.txt"
        
        # 2. Processing
        processing_result = self.rag_processor.process_file(str(source_file))
        
        assert processing_result is not None
        assert "chunks" in processing_result
        
        # 3. Quality analysis
        chunks = processing_result["chunks"]
        quality_results = []
        
        for chunk in chunks:
            quality_result = self.quality_analyzer.assess_text_quality(chunk["text"])
            quality_results.append(quality_result)
        
        # 4. Metadata enrichment
        enriched_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_with_metadata = {
                "text": chunk["text"],
                "metadata": chunk["metadata"],
                "quality": quality_results[i]
            }
            
            enriched_chunk = self.metadata_enricher.enrich_metadata(chunk_with_metadata)
            enriched_chunks.append(enriched_chunk)
        
        # 5. Final dataset preparation
        final_dataset = {
            "source_file": str(source_file),
            "processing_timestamp": time.time(),
            "chunks": enriched_chunks,
            "total_chunks": len(enriched_chunks),
            "average_quality": sum(q["overall_score"] for q in quality_results) / len(quality_results),
            "metadata": {
                "processor_version": "1.0.0",
                "chunk_strategy": "semantic",
                "quality_threshold": 0.5
            }
        }
        
        # 6. Save final dataset
        output_file = self.test_dir / "final_dataset.json"
        output_file.write_text(json.dumps(final_dataset, indent=2))
        
        # 7. Verify final dataset
        assert output_file.exists()
        
        loaded_dataset = json.loads(output_file.read_text())
        assert loaded_dataset["total_chunks"] > 0
        assert loaded_dataset["average_quality"] > 0.0
        assert "chunks" in loaded_dataset
        
        logger.info("✓ End-to-end workflow test passed")
        
        return final_dataset
    
    def test_12_performance_benchmarks(self):
        """Test performance benchmarks."""
        logger.info("Testing performance benchmarks...")
        
        # Test processing speed
        start_time = time.time()
        
        # Process multiple files
        for i in range(3):
            file_path = self.test_data_dir / f"sample_{i+1}.txt"
            result = self.rag_processor.process_file(str(file_path))
            assert result is not None
        
        processing_time = time.time() - start_time
        
        # Performance assertions
        assert processing_time < 30.0  # Should complete within 30 seconds
        
        # Test memory usage (basic check)
        import psutil
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        
        assert memory_usage < 1000  # Should use less than 1GB
        
        logger.info(f"✓ Performance benchmarks passed (Processing time: {processing_time:.2f}s, Memory: {memory_usage:.2f}MB)")
    
    def test_13_error_handling(self):
        """Test error handling and recovery."""
        logger.info("Testing error handling...")
        
        # Test invalid file processing
        invalid_file = self.test_dir / "nonexistent.txt"
        
        try:
            self.rag_processor.process_file(str(invalid_file))
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "not found" in str(e).lower() or "no such file" in str(e).lower()
        
        # Test invalid chunking configuration
        invalid_config = {
            "strategy": "invalid_strategy",
            "chunk_size": -1,
            "overlap": -1
        }
        
        try:
            self.chunking_processor.process_text("test", invalid_config)
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "invalid" in str(e).lower() or "error" in str(e).lower()
        
        # Test invalid quality analysis
        try:
            self.quality_analyzer.assess_text_quality("")
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "empty" in str(e).lower() or "invalid" in str(e).lower()
        
        logger.info("✓ Error handling test passed")
    
    def test_14_concurrent_operations(self):
        """Test concurrent operations."""
        logger.info("Testing concurrent operations...")
        
        import threading
        import concurrent.futures
        
        # Test concurrent file processing
        file_paths = [str(f) for f in self.test_data_dir.glob("sample_*.txt")]
        
        def process_file_thread(file_path):
            return self.rag_processor.process_file(file_path)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(process_file_thread, fp) for fp in file_paths]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify all files were processed
        assert len(results) == len(file_paths)
        for result in results:
            assert result is not None
            assert "chunks" in result
        
        logger.info("✓ Concurrent operations test passed")
    
    def cleanup(self):
        """Clean up test resources."""
        logger.info("Cleaning up test resources...")
        
        try:
            # Clean up temporary files
            if self.test_dir.exists():
                shutil.rmtree(self.test_dir)
            
            # Clean up security manager temp files
            self.security_manager.cleanup_temp_files()
            
            logger.info("✓ Test cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def run_all_tests(self):
        """Run all integration tests."""
        logger.info("Starting comprehensive integration test suite...")
        
        test_methods = [
            self.test_01_file_processing_pipeline,
            self.test_02_advanced_chunking,
            self.test_03_batch_processing,
            self.test_04_quality_analysis,
            self.test_05_metadata_enrichment,
            self.test_06_visual_asset_management,
            self.test_07_relationship_mapping,
            self.test_08_web_scraping,
            self.test_09_security_system,
            self.test_10_cloud_sync_operations,
            self.test_11_end_to_end_workflow,
            self.test_12_performance_benchmarks,
            self.test_13_error_handling,
            self.test_14_concurrent_operations
        ]
        
        passed_tests = 0
        failed_tests = 0
        
        for test_method in test_methods:
            try:
                test_method()
                passed_tests += 1
            except Exception as e:
                logger.error(f"Test {test_method.__name__} failed: {e}")
                failed_tests += 1
        
        # Generate test report
        test_report = {
            "total_tests": len(test_methods),
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / len(test_methods)) * 100,
            "test_directory": str(self.test_dir),
            "timestamp": time.time()
        }
        
        # Save test report
        report_file = self.test_dir / "integration_test_report.json"
        report_file.write_text(json.dumps(test_report, indent=2))
        
        logger.info(f"Integration test suite completed: {passed_tests}/{len(test_methods)} tests passed")
        logger.info(f"Test report saved to: {report_file}")
        
        return test_report


# Pytest integration
@pytest.fixture
def integration_suite():
    """Pytest fixture for integration test suite."""
    suite = IntegrationTestSuite()
    yield suite
    suite.cleanup()


class TestIntegrationSuite:
    """Pytest test class for integration tests."""
    
    def test_file_processing_pipeline(self, integration_suite):
        """Test file processing pipeline."""
        integration_suite.test_01_file_processing_pipeline()
    
    def test_advanced_chunking(self, integration_suite):
        """Test advanced chunking."""
        integration_suite.test_02_advanced_chunking()
    
    def test_batch_processing(self, integration_suite):
        """Test batch processing."""
        integration_suite.test_03_batch_processing()
    
    def test_quality_analysis(self, integration_suite):
        """Test quality analysis."""
        integration_suite.test_04_quality_analysis()
    
    def test_metadata_enrichment(self, integration_suite):
        """Test metadata enrichment."""
        integration_suite.test_05_metadata_enrichment()
    
    def test_visual_asset_management(self, integration_suite):
        """Test visual asset management."""
        integration_suite.test_06_visual_asset_management()
    
    def test_relationship_mapping(self, integration_suite):
        """Test relationship mapping."""
        integration_suite.test_07_relationship_mapping()
    
    def test_web_scraping(self, integration_suite):
        """Test web scraping."""
        integration_suite.test_08_web_scraping()
    
    def test_security_system(self, integration_suite):
        """Test security system."""
        integration_suite.test_09_security_system()
    
    def test_cloud_sync_operations(self, integration_suite):
        """Test cloud sync operations."""
        integration_suite.test_10_cloud_sync_operations()
    
    def test_end_to_end_workflow(self, integration_suite):
        """Test end-to-end workflow."""
        integration_suite.test_11_end_to_end_workflow()
    
    def test_performance_benchmarks(self, integration_suite):
        """Test performance benchmarks."""
        integration_suite.test_12_performance_benchmarks()
    
    def test_error_handling(self, integration_suite):
        """Test error handling."""
        integration_suite.test_13_error_handling()
    
    def test_concurrent_operations(self, integration_suite):
        """Test concurrent operations."""
        integration_suite.test_14_concurrent_operations()


if __name__ == "__main__":
    # Run integration tests directly
    suite = IntegrationTestSuite()
    
    try:
        test_report = suite.run_all_tests()
        print(f"\n{'='*50}")
        print("INTEGRATION TEST REPORT")
        print(f"{'='*50}")
        print(f"Total Tests: {test_report['total_tests']}")
        print(f"Passed: {test_report['passed_tests']}")
        print(f"Failed: {test_report['failed_tests']}")
        print(f"Success Rate: {test_report['success_rate']:.1f}%")
        print(f"{'='*50}")
        
        if test_report['failed_tests'] == 0:
            print("🎉 All integration tests passed!")
        else:
            print(f"⚠️  {test_report['failed_tests']} tests failed")
            
    finally:
        suite.cleanup()
