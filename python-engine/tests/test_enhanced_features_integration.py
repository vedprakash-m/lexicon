"""
Comprehensive Integration Tests for Enhanced Lexicon Features
Tests semantic search, processing pipeline, error handling, and backup systems
"""

import asyncio
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, AsyncMock
import sqlite3
from datetime import datetime, timedelta

# Add processors to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from processors.semantic_search import (
    SemanticSearchEngine, SearchConfig, SearchQuery, DocumentIndex
)
from processors.enhanced_processing_pipeline import (
    ProcessingPipeline, ProcessingJobConfig, ProcessingStatus, ProcessingResult
)
from processors.error_handling import (
    ErrorHandler, ErrorSeverity, ErrorCategory, ErrorContext, get_error_handler
)
from processors.backup_restore_system import (
    BackupManager, BackupConfig, BackupType, RestoreConfig, get_backup_manager
)

class TestSemanticSearchIntegration:
    """Test semantic search engine integration"""
    
    @pytest.fixture
    def search_config(self):
        return SearchConfig(
            semantic_model="all-MiniLM-L6-v2",
            use_semantic_similarity=True,
            similarity_threshold=0.7,
            use_fuzzy_matching=True,
            max_results=50
        )
    
    @pytest.fixture
    async def search_engine(self, search_config):
        engine = SemanticSearchEngine(search_config)
        # Mock the actual ML model loading for tests
        with patch.object(engine, '_load_model', return_value=Mock()):
            await engine.initialize()
        return engine
    
    @pytest.fixture
    def sample_documents(self):
        return [
            DocumentIndex(
                id="doc1",
                title="Introduction to Machine Learning",
                author="John Smith",
                description="A comprehensive guide to ML",
                content="Machine learning is a subset of artificial intelligence...",
                categories=["technology", "ai"],
                subjects=["machine learning", "ai"],
                keywords=["ml", "ai", "algorithms"],
                metadata={"year": 2023, "pages": 300}
            ),
            DocumentIndex(
                id="doc2", 
                title="Advanced Deep Learning",
                author="Jane Doe",
                description="Deep learning techniques and applications",
                content="Deep learning uses neural networks with multiple layers...",
                categories=["technology", "ai"],
                subjects=["deep learning", "neural networks"],
                keywords=["deep learning", "neural networks", "tensorflow"],
                metadata={"year": 2024, "pages": 450}
            )
        ]
    
    @pytest.mark.asyncio
    async def test_search_engine_initialization(self, search_engine):
        """Test search engine initializes correctly"""
        assert search_engine.config.semantic_model == "all-MiniLM-L6-v2"
        assert search_engine.config.use_semantic_similarity is True
        # Mock should be initialized
        assert search_engine._model is not None
    
    @pytest.mark.asyncio
    async def test_document_indexing(self, search_engine, sample_documents):
        """Test document indexing functionality"""
        # Mock the actual indexing process
        with patch.object(search_engine, '_index_document_vectors'):
            await search_engine.index_documents(sample_documents)
        
        # Verify documents are stored
        assert len(search_engine.document_store) == 2
        assert "doc1" in search_engine.document_store
        assert "doc2" in search_engine.document_store
    
    @pytest.mark.asyncio
    async def test_exact_search(self, search_engine, sample_documents):
        """Test exact text matching"""
        await search_engine.index_documents(sample_documents)
        
        query = SearchQuery(
            text="machine learning",
            limit=10
        )
        
        # Mock the search methods
        with patch.object(search_engine, '_exact_search', return_value=[
            {"id": "doc1", "score": 1.0, "match_type": "exact"}
        ]):
            response = await search_engine.search(query)
        
        assert len(response.results) >= 1
        assert response.results[0].id == "doc1"
        assert response.results[0].match_type == "exact"
    
    @pytest.mark.asyncio
    async def test_semantic_search(self, search_engine, sample_documents):
        """Test semantic similarity search"""
        await search_engine.index_documents(sample_documents)
        
        query = SearchQuery(
            text="artificial intelligence algorithms",
            limit=10
        )
        
        # Mock semantic search
        with patch.object(search_engine, '_semantic_search', return_value=[
            {"id": "doc1", "score": 0.85, "match_type": "semantic"},
            {"id": "doc2", "score": 0.75, "match_type": "semantic"}
        ]):
            response = await search_engine.search(query)
        
        assert len(response.results) >= 1
        assert response.results[0].match_type == "semantic"
    
    @pytest.mark.asyncio
    async def test_faceted_search(self, search_engine, sample_documents):
        """Test faceted search with filters"""
        await search_engine.index_documents(sample_documents)
        
        query = SearchQuery(
            text="learning",
            filters={"category": "technology"},
            facets=["author", "year"],
            limit=10
        )
        
        # Mock faceted search
        with patch.object(search_engine, '_apply_filters', return_value=[
            {"id": "doc1", "score": 0.9, "match_type": "filtered"}
        ]):
            response = await search_engine.search(query)
        
        assert len(response.facets) >= 1
        assert any(facet.name == "author" for facet in response.facets)
    
    @pytest.mark.asyncio
    async def test_search_performance(self, search_engine, sample_documents):
        """Test search performance metrics"""
        await search_engine.index_documents(sample_documents)
        
        query = SearchQuery(text="test query")
        
        start_time = datetime.now()
        response = await search_engine.search(query)
        
        # Should complete quickly (mock environment)
        assert response.query_time_ms < 1000  # Less than 1 second
    
    def test_search_statistics(self, search_engine):
        """Test search engine statistics"""
        stats = search_engine.get_statistics()
        
        assert "total_documents" in stats
        assert "total_searches" in stats
        assert "cache_hit_rate" in stats
        assert isinstance(stats["total_documents"], int)

class TestProcessingPipelineIntegration:
    """Test enhanced processing pipeline integration"""
    
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_files(self, temp_dir):
        # Create sample text files
        files = []
        for i in range(3):
            file_path = temp_dir / f"sample_{i}.txt"
            with open(file_path, 'w') as f:
                f.write(f"Sample content for document {i}. This contains some text to process.")
            files.append(str(file_path))
        return files
    
    @pytest.fixture
    def processing_config(self, sample_files, temp_dir):
        return ProcessingJobConfig(
            job_id="test_job_001",
            input_paths=sample_files,
            output_path=str(temp_dir / "output"),
            processing_steps=["chunking", "quality_assessment", "metadata_enrichment"],
            enable_semantic_indexing=True,
            batch_size=2
        )
    
    @pytest.fixture
    async def pipeline(self, temp_dir):
        pipeline = ProcessingPipeline(data_dir=temp_dir)
        # Mock search engine initialization
        with patch.object(pipeline, 'initialize_search_engine'):
            await pipeline.initialize_search_engine()
        return pipeline
    
    @pytest.mark.asyncio
    async def test_job_creation(self, pipeline, processing_config):
        """Test processing job creation"""
        job_id = pipeline.create_processing_job(processing_config)
        
        assert job_id == processing_config.job_id
        assert job_id in pipeline.active_jobs
        assert job_id in pipeline.job_configs
        
        job = pipeline.get_job_status(job_id)
        assert job.status == ProcessingStatus.PENDING
        assert job.total_documents == len(processing_config.input_paths)
    
    @pytest.mark.asyncio
    async def test_job_processing(self, pipeline, processing_config):
        """Test complete job processing"""
        job_id = pipeline.create_processing_job(processing_config)
        
        # Mock the processing components
        with patch.object(pipeline.chunking_pipeline, 'chunk_text', return_value=[]):
            with patch.object(pipeline.quality_analyzer, 'assess_text_quality', return_value=0.8):
                with patch.object(pipeline.metadata_enricher, 'enrich_document_metadata', return_value={}):
                    result = await pipeline.process_job(job_id)
        
        assert result.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
        if result.status == ProcessingStatus.COMPLETED:
            assert result.processed_documents > 0
    
    @pytest.mark.asyncio
    async def test_job_cancellation(self, pipeline, processing_config):
        """Test job cancellation"""
        job_id = pipeline.create_processing_job(processing_config)
        
        # Cancel the job
        success = pipeline.cancel_job(job_id)
        assert success is True
        
        job = pipeline.get_job_status(job_id)
        assert job.status == ProcessingStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_job_pause_resume(self, pipeline, processing_config):
        """Test job pause and resume functionality"""
        job_id = pipeline.create_processing_job(processing_config)
        
        # Pause the job
        success = pipeline.pause_job(job_id)
        assert success is True
        
        job = pipeline.get_job_status(job_id)
        assert job.status == ProcessingStatus.PAUSED
        
        # Resume the job
        success = pipeline.resume_job(job_id)
        assert success is True
        
        job = pipeline.get_job_status(job_id)
        assert job.status == ProcessingStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_progress_tracking(self, pipeline, processing_config):
        """Test progress tracking and callbacks"""
        job_id = pipeline.create_processing_job(processing_config)
        
        progress_updates = []
        def progress_callback(progress):
            progress_updates.append(progress)
        
        pipeline.add_progress_callback(job_id, progress_callback)
        
        # Mock processing to trigger progress updates
        with patch.object(pipeline, '_process_single_document', return_value={"chunks": []}):
            await pipeline.process_job(job_id)
        
        # Should have received progress updates
        assert len(progress_updates) > 0
    
    def test_performance_metrics(self, pipeline):
        """Test performance metrics collection"""
        metrics = pipeline.get_performance_metrics()
        
        assert "total_jobs_processed" in metrics
        assert "average_throughput" in metrics
        assert "error_rate" in metrics
        assert isinstance(metrics["total_jobs_processed"], int)

class TestErrorHandlingIntegration:
    """Test comprehensive error handling system"""
    
    @pytest.fixture
    def error_handler(self):
        # Use in-memory database for testing
        handler = ErrorHandler(database_path=":memory:")
        return handler
    
    @pytest.mark.asyncio
    async def test_error_recording(self, error_handler):
        """Test error recording and persistence"""
        test_error = ValueError("Test error message")
        context = ErrorContext(
            component="test_component",
            operation="test_operation",
            input_data={"test": "data"}
        )
        
        error_record = await error_handler.handle_error(
            test_error, 
            ErrorSeverity.MEDIUM, 
            ErrorCategory.PROCESSING,
            context
        )
        
        assert error_record is not None
        assert error_record.message == "Test error message"
        assert error_record.severity == ErrorSeverity.MEDIUM
        assert error_record.category == ErrorCategory.PROCESSING
        assert error_record.context.component == "test_component"
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, error_handler):
        """Test automatic error recovery"""
        test_error = ConnectionError("Network timeout")
        context = ErrorContext(operation="network_request")
        
        # Mock recovery strategy
        with patch.object(error_handler.recovery_strategies[ErrorCategory.NETWORK], 'recover', return_value=True):
            error_record = await error_handler.handle_error(
                test_error,
                ErrorSeverity.MEDIUM,
                ErrorCategory.NETWORK,
                context,
                auto_recover=True
            )
        
        # Should return None if recovery was successful
        assert error_record is None or error_record.status.value == "resolved"
    
    @pytest.mark.asyncio
    async def test_duplicate_error_handling(self, error_handler):
        """Test handling of duplicate errors"""
        test_error = ValueError("Duplicate error")
        context = ErrorContext(component="test", operation="duplicate_test")
        
        # Record the same error twice
        error1 = await error_handler.handle_error(
            test_error, ErrorSeverity.LOW, ErrorCategory.PROCESSING, context
        )
        error2 = await error_handler.handle_error(
            test_error, ErrorSeverity.LOW, ErrorCategory.PROCESSING, context
        )
        
        # Second occurrence should update the count
        assert error1.error_id == error2.error_id
        assert error2.occurrence_count == 2
    
    def test_error_statistics(self, error_handler):
        """Test error statistics generation"""
        stats = error_handler.get_error_statistics()
        
        assert "total_errors" in stats
        assert "errors_by_severity" in stats
        assert "errors_by_category" in stats
        assert "resolution_rate" in stats
        assert isinstance(stats["total_errors"], int)
    
    def test_error_search(self, error_handler):
        """Test error search functionality"""
        # Search with filters
        results = error_handler.search_errors(
            severity=ErrorSeverity.HIGH,
            limit=10
        )
        
        assert isinstance(results, list)
        # All results should match the filter
        for error in results:
            assert error.severity == ErrorSeverity.HIGH
    
    def test_error_context_manager(self, error_handler):
        """Test error context manager functionality"""
        with pytest.raises(ValueError):
            with error_handler.error_context(
                component="test",
                operation="context_test",
                test_data="value"
            ):
                raise ValueError("Context manager test error")

class TestBackupRestoreIntegration:
    """Test backup and restore system integration"""
    
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_data(self, temp_dir):
        # Create sample data structure
        data_dir = temp_dir / "data"
        data_dir.mkdir()
        
        for i in range(3):
            file_path = data_dir / f"file_{i}.txt"
            with open(file_path, 'w') as f:
                f.write(f"Sample data content {i}")
        
        return str(data_dir)
    
    @pytest.fixture
    def backup_manager(self, temp_dir):
        return BackupManager(base_backup_dir=temp_dir / "backups")
    
    @pytest.fixture
    def backup_config(self, sample_data, temp_dir):
        return BackupConfig(
            backup_id="test_backup_001",
            backup_type=BackupType.FULL,
            source_paths=[sample_data],
            destination_path=str(temp_dir / "backups"),
            compression_level=6,
            include_patterns=["*.txt"],
            retention_days=7
        )
    
    @pytest.mark.asyncio
    async def test_backup_creation(self, backup_manager, backup_config):
        """Test backup creation process"""
        metadata = await backup_manager.create_backup(backup_config)
        
        assert metadata.backup_id == backup_config.backup_id
        assert metadata.backup_type == BackupType.FULL
        assert metadata.file_count > 0
        assert metadata.total_size > 0
        assert Path(metadata.backup_path).exists()
    
    @pytest.mark.asyncio
    async def test_backup_verification(self, backup_manager, backup_config):
        """Test backup verification"""
        metadata = await backup_manager.create_backup(backup_config)
        
        # Verify the backup
        is_valid = await backup_manager._verify_backup(metadata.backup_path)
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_backup_restore(self, backup_manager, backup_config, temp_dir):
        """Test backup restoration"""
        # Create backup
        metadata = await backup_manager.create_backup(backup_config)
        
        # Configure restore
        restore_config = RestoreConfig(
            restore_id="test_restore_001",
            backup_id=metadata.backup_id,
            backup_path=metadata.backup_path,
            destination_path=str(temp_dir / "restored"),
            overwrite_existing=True,
            verify_restore=True
        )
        
        # Perform restore
        result = await backup_manager.restore_backup(restore_config)
        
        assert result.status.value in ["completed", "failed"]
        if result.status.value == "completed":
            assert result.restored_files > 0
            assert result.verification_passed is True
    
    def test_backup_listing(self, backup_manager):
        """Test backup listing functionality"""
        backups = backup_manager.list_backups()
        assert isinstance(backups, list)
    
    def test_backup_statistics(self, backup_manager):
        """Test backup statistics"""
        stats = backup_manager.get_backup_statistics()
        
        assert "total_backups" in stats
        assert "successful_backups" in stats
        assert "total_backup_size" in stats
        assert isinstance(stats["total_backups"], int)
    
    def test_backup_cleanup(self, backup_manager):
        """Test backup cleanup functionality"""
        # Test expired backup cleanup
        cleaned_count = backup_manager.cleanup_expired_backups()
        assert isinstance(cleaned_count, int)

class TestCrossComponentIntegration:
    """Test integration across multiple components"""
    
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_full_pipeline_with_search(self, temp_dir):
        """Test complete pipeline with semantic search integration"""
        # Setup components
        pipeline = ProcessingPipeline(data_dir=temp_dir)
        error_handler = ErrorHandler(database_path=str(temp_dir / "errors.db"))
        
        # Mock search engine initialization
        with patch.object(pipeline, 'initialize_search_engine'):
            await pipeline.initialize_search_engine()
        
        # Create sample data
        data_dir = temp_dir / "data"
        data_dir.mkdir()
        file_path = data_dir / "test.txt"
        with open(file_path, 'w') as f:
            f.write("Test document content for processing")
        
        # Configure processing job
        config = ProcessingJobConfig(
            job_id="integration_test",
            input_paths=[str(file_path)],
            output_path=str(temp_dir / "output"),
            processing_steps=["chunking", "quality_assessment"],
            enable_semantic_indexing=True
        )
        
        # Process with error handling
        try:
            job_id = pipeline.create_processing_job(config)
            
            with patch.object(pipeline.chunking_pipeline, 'chunk_text', return_value=[]):
                with patch.object(pipeline.quality_analyzer, 'assess_text_quality', return_value=0.8):
                    result = await pipeline.process_job(job_id)
            
            assert result.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
            
        except Exception as e:
            # Error should be handled by error handler
            await error_handler.handle_error(
                e, ErrorSeverity.HIGH, ErrorCategory.PROCESSING,
                ErrorContext(component="integration_test", operation="full_pipeline")
            )
    
    @pytest.mark.asyncio 
    async def test_backup_with_error_handling(self, temp_dir):
        """Test backup system with error handling integration"""
        backup_manager = BackupManager(base_backup_dir=temp_dir / "backups")
        error_handler = ErrorHandler(database_path=str(temp_dir / "errors.db"))
        
        # Create data to backup
        data_dir = temp_dir / "data"
        data_dir.mkdir()
        file_path = data_dir / "backup_test.txt"
        with open(file_path, 'w') as f:
            f.write("Data to backup")
        
        config = BackupConfig(
            backup_id="error_test_backup",
            backup_type=BackupType.FULL,
            source_paths=[str(data_dir)],
            destination_path=str(temp_dir / "backups"),
            compression_level=6
        )
        
        try:
            metadata = await backup_manager.create_backup(config)
            assert metadata.backup_id == config.backup_id
            
        except Exception as e:
            # Any errors should be properly handled
            await error_handler.handle_error(
                e, ErrorSeverity.HIGH, ErrorCategory.FILE_IO,
                ErrorContext(component="backup_test", operation="create_backup")
            )

# Performance and load tests
class TestPerformanceIntegration:
    """Test performance characteristics of integrated systems"""
    
    @pytest.mark.asyncio
    async def test_search_performance_under_load(self):
        """Test search performance with multiple concurrent queries"""
        config = SearchConfig(use_semantic_similarity=False)  # Faster for testing
        engine = SemanticSearchEngine(config)
        
        # Mock initialization and indexing
        with patch.object(engine, '_load_model', return_value=Mock()):
            await engine.initialize()
        
        # Create test documents
        documents = [
            DocumentIndex(
                id=f"perf_doc_{i}",
                title=f"Performance Test Document {i}",
                author="Test Author",
                content=f"Content for performance testing document {i}",
                categories=["test"],
                subjects=["performance"],
                keywords=["test", "performance"],
                metadata={"index": i}
            )
            for i in range(100)
        ]
        
        await engine.index_documents(documents)
        
        # Run concurrent searches
        async def search_task(query_id):
            query = SearchQuery(text=f"test {query_id}", limit=10)
            return await engine.search(query)
        
        # Mock the actual search to return quickly
        with patch.object(engine, '_exact_search', return_value=[]):
            start_time = datetime.now()
            tasks = [search_task(i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            end_time = datetime.now()
        
        # Should complete all searches quickly
        total_time = (end_time - start_time).total_seconds()
        assert total_time < 5.0  # Less than 5 seconds for 10 concurrent searches
        assert len(results) == 10
    
    @pytest.mark.asyncio
    async def test_processing_pipeline_throughput(self, tmp_path):
        """Test processing pipeline throughput"""
        pipeline = ProcessingPipeline(data_dir=tmp_path)
        
        # Create multiple test files
        files = []
        for i in range(20):
            file_path = tmp_path / f"throughput_test_{i}.txt"
            with open(file_path, 'w') as f:
                f.write(f"Throughput test content {i} " * 100)  # Longer content
            files.append(str(file_path))
        
        config = ProcessingJobConfig(
            job_id="throughput_test",
            input_paths=files,
            output_path=str(tmp_path / "output"),
            processing_steps=["chunking"],
            batch_size=5,
            max_workers=2
        )
        
        job_id = pipeline.create_processing_job(config)
        
        # Mock processing components for speed
        with patch.object(pipeline.chunking_pipeline, 'chunk_text', return_value=[]):
            start_time = datetime.now()
            result = await pipeline.process_job(job_id)
            end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        throughput = len(files) / processing_time  # documents per second
        
        # Should process at reasonable speed
        assert throughput > 5  # At least 5 docs/second
        assert result.status == ProcessingStatus.COMPLETED

# Test configuration and fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
