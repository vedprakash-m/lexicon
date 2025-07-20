import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import logging
import json
from pathlib import Path

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class BatchJob:
    id: str
    file_path: str
    processor_type: str
    parameters: Dict
    status: JobStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    progress: float = 0.0

@dataclass
class BatchProgress:
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    running_jobs: int
    pending_jobs: int
    overall_progress: float
    estimated_time_remaining: Optional[float] = None

class BatchProcessor:
    def __init__(self, max_workers: int = 4, checkpoint_interval: int = 10):
        self.max_workers = max_workers
        self.checkpoint_interval = checkpoint_interval
        self.jobs: Dict[str, BatchJob] = {}
        self.job_queue: List[str] = []
        self.running_jobs: Dict[str, threading.Thread] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.checkpoint_file = Path("batch_checkpoint.json")
        
        # Progress tracking
        self.progress_callbacks: List[Callable[[BatchProgress], None]] = []
        
        # Load checkpoint if exists
        self.load_checkpoint()
        
    def add_job(self, job_id: str, file_path: str, processor_type: str, parameters: Dict = None) -> BatchJob:
        """Add a job to the batch queue"""
        if parameters is None:
            parameters = {}
            
        job = BatchJob(
            id=job_id,
            file_path=file_path,
            processor_type=processor_type,
            parameters=parameters,
            status=JobStatus.PENDING,
            created_at=time.time()
        )
        
        self.jobs[job_id] = job
        self.job_queue.append(job_id)
        
        self.logger.info(f"Added job {job_id} to batch queue")
        return job
        
    def add_bulk_jobs(self, file_paths: List[str], processor_type: str, parameters: Dict = None) -> List[BatchJob]:
        """Add multiple jobs at once"""
        jobs = []
        for i, file_path in enumerate(file_paths):
            job_id = f"batch_{int(time.time())}_{i}"
            job = self.add_job(job_id, file_path, processor_type, parameters)
            jobs.append(job)
        return jobs
        
    def start_processing(self) -> None:
        """Start processing the batch queue"""
        if self.is_running:
            self.logger.warning("Batch processing already running")
            return
            
        self.is_running = True
        self.logger.info(f"Starting batch processing with {len(self.job_queue)} jobs")
        
        # Start worker threads
        futures = []
        for _ in range(min(self.max_workers, len(self.job_queue))):
            future = self.executor.submit(self._worker_thread)
            futures.append(future)
            
        # Monitor progress
        self._monitor_progress()
        
    def stop_processing(self) -> None:
        """Stop batch processing"""
        self.is_running = False
        self.logger.info("Stopping batch processing")
        
    def pause_processing(self) -> None:
        """Pause batch processing"""
        self.is_running = False
        self.save_checkpoint()
        self.logger.info("Paused batch processing")
        
    def resume_processing(self) -> None:
        """Resume batch processing from checkpoint"""
        self.load_checkpoint()
        self.start_processing()
        
    def _worker_thread(self) -> None:
        """Worker thread that processes jobs from the queue"""
        while self.is_running and self.job_queue:
            try:
                # Get next job
                if not self.job_queue:
                    break
                    
                job_id = self.job_queue.pop(0)
                job = self.jobs[job_id]
                
                # Update job status
                job.status = JobStatus.RUNNING
                job.started_at = time.time()
                
                self.logger.info(f"Processing job {job_id}: {job.file_path}")
                
                # Process the job
                try:
                    result = self._process_single_job(job)
                    job.result = result
                    job.status = JobStatus.COMPLETED
                    job.progress = 1.0
                    
                except Exception as e:
                    job.error = str(e)
                    job.status = JobStatus.FAILED
                    self.logger.error(f"Job {job_id} failed: {e}")
                    
                finally:
                    job.completed_at = time.time()
                    
                # Save checkpoint periodically
                if len([j for j in self.jobs.values() if j.status in [JobStatus.COMPLETED, JobStatus.FAILED]]) % self.checkpoint_interval == 0:
                    self.save_checkpoint()
                    
            except Exception as e:
                self.logger.error(f"Worker thread error: {e}")
                
    def _process_single_job(self, job: BatchJob) -> Dict:
        """Process a single job based on its type"""
        from .pdf_processor import PDFProcessor
        from .document_processor import DocumentProcessor
        from .ebook_processor import EbookProcessor
        from ..scrapers.web_scraper import WebScraper
        
        # File integrity check
        file_path = Path(job.file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {job.file_path}")
            
        # Format compatibility check
        if not self._is_format_compatible(file_path, job.processor_type):
            raise ValueError(f"File format not compatible with {job.processor_type}")
            
        # Process based on type
        if job.processor_type == "pdf":
            processor = PDFProcessor()
            result = processor.extract_text(str(file_path), job.parameters.get('password'))
            return {
                'text': result.text,
                'metadata': result.metadata,
                'quality_score': result.quality_score,
                'extraction_method': result.extraction_method
            }
            
        elif job.processor_type == "document":
            processor = DocumentProcessor()
            result = processor.process_document(str(file_path))
            return {
                'text': result.text,
                'metadata': result.metadata,
                'structure': result.structure,
                'quality_score': result.quality_score
            }
            
        elif job.processor_type == "ebook":
            processor = EbookProcessor()
            result = processor.process_ebook(str(file_path))
            return {
                'text': result.text,
                'metadata': result.metadata,
                'chapters': result.chapters,
                'quality_score': result.quality_score
            }
            
        elif job.processor_type == "web":
            scraper = WebScraper()
            result = scraper.scrape_url(job.file_path, job.parameters.get('custom_rules'))
            return {
                'text': result.text,
                'metadata': result.metadata,
                'title': result.title,
                'quality_score': result.quality_score
            }
            
        else:
            raise ValueError(f"Unknown processor type: {job.processor_type}")
            
    def _is_format_compatible(self, file_path: Path, processor_type: str) -> bool:
        """Check if file format is compatible with processor"""
        suffix = file_path.suffix.lower()
        
        compatibility_map = {
            'pdf': ['.pdf'],
            'document': ['.docx', '.html', '.htm', '.md', '.markdown', '.txt'],
            'ebook': ['.epub', '.mobi'],
            'web': []  # URLs don't have file extensions
        }
        
        if processor_type == 'web':
            return True  # URLs are always compatible
            
        return suffix in compatibility_map.get(processor_type, [])
        
    def _monitor_progress(self) -> None:
        """Monitor and report progress"""
        while self.is_running or any(job.status == JobStatus.RUNNING for job in self.jobs.values()):
            progress = self.get_progress()
            
            # Notify progress callbacks
            for callback in self.progress_callbacks:
                try:
                    callback(progress)
                except Exception as e:
                    self.logger.error(f"Progress callback error: {e}")
                    
            time.sleep(1)  # Update every second
            
    def get_progress(self) -> BatchProgress:
        """Get current batch progress"""
        total_jobs = len(self.jobs)
        completed_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.COMPLETED])
        failed_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.FAILED])
        running_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.RUNNING])
        pending_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.PENDING])
        
        overall_progress = (completed_jobs + failed_jobs) / max(total_jobs, 1)
        
        # Estimate time remaining
        estimated_time = None
        if completed_jobs > 0:
            completed_job_times = [
                j.completed_at - j.started_at 
                for j in self.jobs.values() 
                if j.status == JobStatus.COMPLETED and j.started_at and j.completed_at
            ]
            if completed_job_times:
                avg_time_per_job = sum(completed_job_times) / len(completed_job_times)
                remaining_jobs = pending_jobs + running_jobs
                estimated_time = remaining_jobs * avg_time_per_job
                
        return BatchProgress(
            total_jobs=total_jobs,
            completed_jobs=completed_jobs,
            failed_jobs=failed_jobs,
            running_jobs=running_jobs,
            pending_jobs=pending_jobs,
            overall_progress=overall_progress,
            estimated_time_remaining=estimated_time
        )
        
    def add_progress_callback(self, callback: Callable[[BatchProgress], None]) -> None:
        """Add a progress callback function"""
        self.progress_callbacks.append(callback)
        
    def get_job_status(self, job_id: str) -> Optional[BatchJob]:
        """Get status of a specific job"""
        return self.jobs.get(job_id)
        
    def get_failed_jobs(self) -> List[BatchJob]:
        """Get all failed jobs"""
        return [job for job in self.jobs.values() if job.status == JobStatus.FAILED]
        
    def retry_failed_jobs(self) -> None:
        """Retry all failed jobs"""
        failed_jobs = self.get_failed_jobs()
        for job in failed_jobs:
            job.status = JobStatus.PENDING
            job.error = None
            job.started_at = None
            job.completed_at = None
            job.progress = 0.0
            self.job_queue.append(job.id)
            
        self.logger.info(f"Retrying {len(failed_jobs)} failed jobs")
        
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a specific job"""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            if job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
                job.status = JobStatus.CANCELLED
                if job_id in self.job_queue:
                    self.job_queue.remove(job_id)
                return True
        return False
        
    def save_checkpoint(self) -> None:
        """Save current state to checkpoint file"""
        checkpoint_data = {
            'jobs': {
                job_id: {
                    'id': job.id,
                    'file_path': job.file_path,
                    'processor_type': job.processor_type,
                    'parameters': job.parameters,
                    'status': job.status.value,
                    'created_at': job.created_at,
                    'started_at': job.started_at,
                    'completed_at': job.completed_at,
                    'error': job.error,
                    'progress': job.progress
                }
                for job_id, job in self.jobs.items()
            },
            'job_queue': self.job_queue,
            'checkpoint_time': time.time()
        }
        
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            self.logger.info("Checkpoint saved")
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
            
    def load_checkpoint(self) -> None:
        """Load state from checkpoint file"""
        if not self.checkpoint_file.exists():
            return
            
        try:
            with open(self.checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
                
            # Restore jobs
            for job_id, job_data in checkpoint_data['jobs'].items():
                job = BatchJob(
                    id=job_data['id'],
                    file_path=job_data['file_path'],
                    processor_type=job_data['processor_type'],
                    parameters=job_data['parameters'],
                    status=JobStatus(job_data['status']),
                    created_at=job_data['created_at'],
                    started_at=job_data.get('started_at'),
                    completed_at=job_data.get('completed_at'),
                    error=job_data.get('error'),
                    progress=job_data.get('progress', 0.0)
                )
                self.jobs[job_id] = job
                
            # Restore queue (only pending jobs)
            self.job_queue = [
                job_id for job_id in checkpoint_data['job_queue']
                if job_id in self.jobs and self.jobs[job_id].status == JobStatus.PENDING
            ]
            
            self.logger.info(f"Checkpoint loaded: {len(self.jobs)} jobs, {len(self.job_queue)} pending")
            
        except Exception as e:
            self.logger.error(f"Failed to load checkpoint: {e}")
            
    def clear_completed_jobs(self) -> int:
        """Clear completed jobs from memory"""
        completed_jobs = [job_id for job_id, job in self.jobs.items() if job.status == JobStatus.COMPLETED]
        for job_id in completed_jobs:
            del self.jobs[job_id]
        return len(completed_jobs)
        
    def get_summary_report(self) -> Dict:
        """Get a summary report of batch processing"""
        progress = self.get_progress()
        
        return {
            'total_jobs': progress.total_jobs,
            'completed_jobs': progress.completed_jobs,
            'failed_jobs': progress.failed_jobs,
            'success_rate': progress.completed_jobs / max(progress.total_jobs, 1),
            'overall_progress': progress.overall_progress,
            'estimated_time_remaining': progress.estimated_time_remaining,
            'failed_job_details': [
                {'id': job.id, 'file_path': job.file_path, 'error': job.error}
                for job in self.get_failed_jobs()
            ]
        }