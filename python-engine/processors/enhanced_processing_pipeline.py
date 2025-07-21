"""
Enhanced Processing Pipeline Integration for Lexicon
Connects frontend UI components to backend processing with semantic search integration
"""

import asyncio
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from .semantic_search import SemanticSearchEngine, SearchConfig, DocumentIndex
from .chunking import ChunkingPipeline, ChunkingConfig
from .metadata_enrichment import MetadataEnrichment
from .relationship_mapping import RelationshipMapper
from .quality_assessment import QualityAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessingStatus(Enum):
    """Processing job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

@dataclass
class ProcessingJobConfig:
    """Configuration for a processing job"""
    job_id: str
    input_paths: List[str]
    output_path: str
    processing_steps: List[str]
    chunking_config: Optional[Dict[str, Any]] = None
    search_config: Optional[Dict[str, Any]] = None
    quality_threshold: float = 0.7
    enable_semantic_indexing: bool = True
    enable_relationship_mapping: bool = True
    enable_metadata_enrichment: bool = True
    batch_size: int = 10
    max_workers: int = 4
    priority: int = 5  # 1-10, higher is more priority

@dataclass
class ProcessingResult:
    """Result of a processing operation"""
    job_id: str
    status: ProcessingStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    processed_documents: int = 0
    total_documents: int = 0
    chunked_segments: int = 0
    indexed_documents: int = 0
    error_message: Optional[str] = None
    warnings: List[str] = None
    output_files: List[str] = None
    quality_metrics: Optional[Dict[str, Any]] = None
    processing_time_ms: int = 0

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.output_files is None:
            self.output_files = []

@dataclass
class ProcessingProgress:
    """Real-time processing progress information"""
    job_id: str
    current_step: str
    progress_percentage: float
    current_document: str
    documents_processed: int
    total_documents: int
    estimated_time_remaining: Optional[int] = None  # seconds
    current_operation: str = ""
    throughput_docs_per_second: float = 0.0

class ProcessingPipeline:
    """Enhanced processing pipeline with semantic search integration"""
    
    def __init__(self, 
                 data_dir: Path = Path("data"),
                 cache_dir: Path = Path("cache"),
                 temp_dir: Path = Path("temp")):
        self.data_dir = Path(data_dir)
        self.cache_dir = Path(cache_dir)
        self.temp_dir = Path(temp_dir)
        
        # Ensure directories exist
        for directory in [self.data_dir, self.cache_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.chunking_pipeline = ChunkingPipeline()
        self.metadata_enricher = MetadataEnrichment()
        self.relationship_mapper = RelationshipMapper()
        self.quality_analyzer = QualityAnalyzer()
        self.search_engine: Optional[SemanticSearchEngine] = None
        
        # Job management
        self.active_jobs: Dict[str, ProcessingResult] = {}
        self.job_configs: Dict[str, ProcessingJobConfig] = {}
        self.progress_callbacks: Dict[str, List[Callable]] = {}
        
        # Performance tracking
        self.performance_metrics = {
            "total_jobs_processed": 0,
            "total_processing_time": 0,
            "average_throughput": 0.0,
            "cache_hit_rate": 0.0,
            "error_rate": 0.0
        }
        
        logger.info("Processing pipeline initialized")
    
    async def initialize_search_engine(self, config: Optional[SearchConfig] = None) -> None:
        """Initialize the semantic search engine"""
        try:
            search_config = config or SearchConfig()
            self.search_engine = SemanticSearchEngine(search_config)
            logger.info("Semantic search engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize search engine: {e}")
            raise
    
    def create_processing_job(self, config: ProcessingJobConfig) -> str:
        """Create a new processing job"""
        job_id = config.job_id
        
        # Validate configuration
        if not config.input_paths:
            raise ValueError("Input paths cannot be empty")
        
        if not config.processing_steps:
            raise ValueError("Processing steps cannot be empty")
        
        # Initialize job result
        job_result = ProcessingResult(
            job_id=job_id,
            status=ProcessingStatus.PENDING,
            start_time=datetime.now(),
            total_documents=len(config.input_paths)
        )
        
        self.active_jobs[job_id] = job_result
        self.job_configs[job_id] = config
        self.progress_callbacks[job_id] = []
        
        logger.info(f"Created processing job {job_id} with {len(config.input_paths)} documents")
        return job_id
    
    def add_progress_callback(self, job_id: str, callback: Callable[[ProcessingProgress], None]) -> None:
        """Add a progress callback for a job"""
        if job_id in self.progress_callbacks:
            self.progress_callbacks[job_id].append(callback)
    
    def get_job_status(self, job_id: str) -> Optional[ProcessingResult]:
        """Get the status of a processing job"""
        return self.active_jobs.get(job_id)
    
    def get_all_jobs(self) -> Dict[str, ProcessingResult]:
        """Get all active jobs"""
        return self.active_jobs.copy()
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a processing job"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job.status in [ProcessingStatus.PENDING, ProcessingStatus.RUNNING, ProcessingStatus.PAUSED]:
                job.status = ProcessingStatus.CANCELLED
                job.end_time = datetime.now()
                logger.info(f"Cancelled job {job_id}")
                return True
        return False
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a processing job"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job.status == ProcessingStatus.RUNNING:
                job.status = ProcessingStatus.PAUSED
                logger.info(f"Paused job {job_id}")
                return True
        return False
    
    def resume_job(self, job_id: str) -> bool:
        """Resume a paused processing job"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job.status == ProcessingStatus.PAUSED:
                job.status = ProcessingStatus.RUNNING
                logger.info(f"Resumed job {job_id}")
                return True
        return False
    
    async def process_job(self, job_id: str) -> ProcessingResult:
        """Process a job with full pipeline integration"""
        if job_id not in self.job_configs:
            raise ValueError(f"Job {job_id} not found")
        
        config = self.job_configs[job_id]
        job = self.active_jobs[job_id]
        
        try:
            job.status = ProcessingStatus.RUNNING
            start_time = time.time()
            
            # Process each document
            processed_docs = []
            for i, input_path in enumerate(config.input_paths):
                # Check for cancellation/pause
                if job.status == ProcessingStatus.CANCELLED:
                    break
                
                while job.status == ProcessingStatus.PAUSED:
                    await asyncio.sleep(1)
                
                # Update progress
                progress = ProcessingProgress(
                    job_id=job_id,
                    current_step="Processing document",
                    progress_percentage=(i / len(config.input_paths)) * 100,
                    current_document=input_path,
                    documents_processed=i,
                    total_documents=len(config.input_paths),
                    current_operation=f"Processing {Path(input_path).name}"
                )
                await self._notify_progress(job_id, progress)
                
                # Process document
                try:
                    doc_result = await self._process_single_document(input_path, config)
                    processed_docs.append(doc_result)
                    job.processed_documents += 1
                    
                    if doc_result.get("chunks"):
                        job.chunked_segments += len(doc_result["chunks"])
                    
                except Exception as e:
                    logger.error(f"Failed to process document {input_path}: {e}")
                    job.warnings.append(f"Failed to process {input_path}: {str(e)}")
            
            # Index documents in search engine if enabled
            if config.enable_semantic_indexing and self.search_engine and processed_docs:
                await self._index_processed_documents(job_id, processed_docs)
            
            # Finalize job
            job.end_time = datetime.now()
            job.processing_time_ms = int((time.time() - start_time) * 1000)
            job.status = ProcessingStatus.COMPLETED if job.status != ProcessingStatus.CANCELLED else ProcessingStatus.CANCELLED
            
            # Calculate quality metrics
            if processed_docs:
                job.quality_metrics = await self._calculate_quality_metrics(processed_docs)
            
            # Update performance metrics
            self._update_performance_metrics(job)
            
            logger.info(f"Job {job_id} completed: {job.processed_documents}/{job.total_documents} documents")
            
        except Exception as e:
            job.status = ProcessingStatus.FAILED
            job.error_message = str(e)
            job.end_time = datetime.now()
            logger.error(f"Job {job_id} failed: {e}")
        
        return job
    
    async def _process_single_document(self, input_path: str, config: ProcessingJobConfig) -> Dict[str, Any]:
        """Process a single document through the pipeline"""
        document_path = Path(input_path)
        
        # Read document
        if not document_path.exists():
            raise FileNotFoundError(f"Document not found: {input_path}")
        
        with open(document_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Initialize document metadata
        doc_metadata = {
            "source_path": str(document_path),
            "filename": document_path.name,
            "file_size": document_path.stat().st_size,
            "processing_timestamp": datetime.now().isoformat()
        }
        
        result = {
            "document_id": document_path.stem,
            "content": content,
            "metadata": doc_metadata,
            "chunks": [],
            "relationships": [],
            "quality_score": 0.0
        }
        
        # Step 1: Text Chunking
        if "chunking" in config.processing_steps:
            chunking_config = ChunkingConfig(**(config.chunking_config or {}))
            chunks = await self.chunking_pipeline.chunk_text(content, chunking_config)
            result["chunks"] = [asdict(chunk) for chunk in chunks]
        
        # Step 2: Quality Assessment
        if "quality_assessment" in config.processing_steps:
            quality_score = await self.quality_analyzer.assess_text_quality(content)
            result["quality_score"] = quality_score
            
            # Filter out low-quality documents
            if quality_score < config.quality_threshold:
                result["metadata"]["quality_warning"] = f"Quality score {quality_score} below threshold {config.quality_threshold}"
        
        # Step 3: Metadata Enrichment
        if "metadata_enrichment" in config.processing_steps and config.enable_metadata_enrichment:
            enriched_metadata = await self.metadata_enricher.enrich_document_metadata(
                content, doc_metadata
            )
            result["metadata"].update(enriched_metadata)
        
        # Step 4: Relationship Mapping
        if "relationship_mapping" in config.processing_steps and config.enable_relationship_mapping:
            relationships = await self.relationship_mapper.map_document_relationships(
                content, result["chunks"]
            )
            result["relationships"] = relationships
        
        return result
    
    async def _index_processed_documents(self, job_id: str, processed_docs: List[Dict[str, Any]]) -> None:
        """Index processed documents in the search engine"""
        if not self.search_engine:
            return
        
        job = self.active_jobs[job_id]
        
        # Convert processed documents to search index format
        document_indices = []
        for doc in processed_docs:
            doc_index = DocumentIndex(
                id=doc["document_id"],
                title=doc["metadata"].get("title", doc["metadata"]["filename"]),
                author=doc["metadata"].get("author", "Unknown"),
                description=doc["metadata"].get("description", ""),
                content=doc["content"],
                categories=doc["metadata"].get("categories", []),
                subjects=doc["metadata"].get("subjects", []),
                keywords=doc["metadata"].get("keywords", []),
                metadata=doc["metadata"]
            )
            document_indices.append(doc_index)
        
        # Index documents
        try:
            await self.search_engine.index_documents(document_indices)
            job.indexed_documents = len(document_indices)
            logger.info(f"Indexed {len(document_indices)} documents for job {job_id}")
        except Exception as e:
            logger.error(f"Failed to index documents for job {job_id}: {e}")
            job.warnings.append(f"Search indexing failed: {str(e)}")
    
    async def _calculate_quality_metrics(self, processed_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall quality metrics for processed documents"""
        if not processed_docs:
            return {}
        
        quality_scores = [doc.get("quality_score", 0.0) for doc in processed_docs]
        total_chunks = sum(len(doc.get("chunks", [])) for doc in processed_docs)
        
        return {
            "average_quality_score": sum(quality_scores) / len(quality_scores),
            "min_quality_score": min(quality_scores),
            "max_quality_score": max(quality_scores),
            "total_documents": len(processed_docs),
            "total_chunks": total_chunks,
            "average_chunks_per_document": total_chunks / len(processed_docs) if processed_docs else 0,
            "documents_above_threshold": len([s for s in quality_scores if s >= 0.7])
        }
    
    async def _notify_progress(self, job_id: str, progress: ProcessingProgress) -> None:
        """Notify progress callbacks"""
        if job_id in self.progress_callbacks:
            for callback in self.progress_callbacks[job_id]:
                try:
                    callback(progress)
                except Exception as e:
                    logger.error(f"Progress callback error for job {job_id}: {e}")
    
    def _update_performance_metrics(self, job: ProcessingResult) -> None:
        """Update overall performance metrics"""
        self.performance_metrics["total_jobs_processed"] += 1
        self.performance_metrics["total_processing_time"] += job.processing_time_ms
        
        if job.processing_time_ms > 0:
            throughput = (job.processed_documents * 1000) / job.processing_time_ms
            current_avg = self.performance_metrics["average_throughput"]
            total_jobs = self.performance_metrics["total_jobs_processed"]
            self.performance_metrics["average_throughput"] = (
                (current_avg * (total_jobs - 1) + throughput) / total_jobs
            )
        
        # Update error rate
        total_failures = sum(1 for j in self.active_jobs.values() if j.status == ProcessingStatus.FAILED)
        self.performance_metrics["error_rate"] = total_failures / self.performance_metrics["total_jobs_processed"]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.performance_metrics.copy()
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up old completed jobs"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        removed_count = 0
        
        jobs_to_remove = []
        for job_id, job in self.active_jobs.items():
            if (job.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED, ProcessingStatus.CANCELLED] 
                and job.end_time 
                and job.end_time.timestamp() < cutoff_time):
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.active_jobs[job_id]
            del self.job_configs[job_id]
            if job_id in self.progress_callbacks:
                del self.progress_callbacks[job_id]
            removed_count += 1
        
        logger.info(f"Cleaned up {removed_count} old jobs")
        return removed_count
    
    async def export_job_results(self, job_id: str, output_path: str, format: str = "json") -> str:
        """Export job results to file"""
        if job_id not in self.active_jobs:
            raise ValueError(f"Job {job_id} not found")
        
        job = self.active_jobs[job_id]
        export_data = {
            "job_result": asdict(job),
            "job_config": asdict(self.job_configs[job_id]),
            "export_timestamp": datetime.now().isoformat()
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "json":
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        logger.info(f"Exported job {job_id} results to {output_file}")
        return str(output_file)

# Global pipeline instance
_pipeline_instance: Optional[ProcessingPipeline] = None

def get_pipeline() -> ProcessingPipeline:
    """Get or create the global pipeline instance"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = ProcessingPipeline()
    return _pipeline_instance

async def initialize_pipeline(data_dir: Optional[str] = None, 
                             search_config: Optional[SearchConfig] = None) -> ProcessingPipeline:
    """Initialize the global pipeline with optional configuration"""
    global _pipeline_instance
    
    if data_dir:
        _pipeline_instance = ProcessingPipeline(data_dir=Path(data_dir))
    else:
        _pipeline_instance = ProcessingPipeline()
    
    # Initialize search engine
    await _pipeline_instance.initialize_search_engine(search_config)
    
    return _pipeline_instance

# Demo function for testing the integration
async def demo_pipeline_integration():
    """Demonstrate the processing pipeline integration"""
    print("=== Processing Pipeline Integration Demo ===")
    
    # Initialize pipeline
    pipeline = await initialize_pipeline()
    
    # Create a sample processing job
    job_config = ProcessingJobConfig(
        job_id="demo_job_001",
        input_paths=["data/sample/book1.txt", "data/sample/book2.txt"],
        output_path="output/demo_results",
        processing_steps=["chunking", "quality_assessment", "metadata_enrichment", "relationship_mapping"],
        enable_semantic_indexing=True,
        batch_size=5
    )
    
    # Create and start job
    job_id = pipeline.create_processing_job(job_config)
    print(f"Created job: {job_id}")
    
    # Add progress callback
    def progress_callback(progress: ProcessingProgress):
        print(f"Progress: {progress.progress_percentage:.1f}% - {progress.current_operation}")
    
    pipeline.add_progress_callback(job_id, progress_callback)
    
    # Process job
    result = await pipeline.process_job(job_id)
    
    print(f"Job completed with status: {result.status}")
    print(f"Processed {result.processed_documents}/{result.total_documents} documents")
    print(f"Created {result.chunked_segments} chunks")
    print(f"Indexed {result.indexed_documents} documents")
    print(f"Processing time: {result.processing_time_ms}ms")
    
    if result.quality_metrics:
        print(f"Average quality score: {result.quality_metrics['average_quality_score']:.3f}")
    
    # Export results
    if result.status == ProcessingStatus.COMPLETED:
        export_path = await pipeline.export_job_results(job_id, "output/demo_results.json")
        print(f"Results exported to: {export_path}")
    
    # Show performance metrics
    metrics = pipeline.get_performance_metrics()
    print(f"Performance metrics: {metrics}")

if __name__ == "__main__":
    asyncio.run(demo_pipeline_integration())
