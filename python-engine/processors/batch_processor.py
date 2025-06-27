"""
Batch Processing System for Lexicon.

This module provides comprehensive batch processing capabilities for handling
multiple sources, parallel processing, resource management, and job scheduling.
"""

import asyncio
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union, Tuple, Set
import json
import threading
from queue import Queue, PriorityQueue
import multiprocessing
import psutil
import os

# Configure logging
logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Status enumeration for batch jobs."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(Enum):
    """Priority levels for batch jobs."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class ResourceLimits:
    """Resource limits for batch processing."""
    max_cpu_cores: Optional[int] = None  # None = auto-detect
    max_memory_mb: Optional[int] = None  # None = 80% of available
    max_concurrent_jobs: int = 4
    max_concurrent_sources: int = 2
    cpu_usage_threshold: float = 80.0  # Pause if CPU > threshold
    memory_usage_threshold: float = 85.0  # Pause if memory > threshold
    
    def __post_init__(self):
        """Set defaults based on system capabilities."""
        if self.max_cpu_cores is None:
            self.max_cpu_cores = max(1, multiprocessing.cpu_count() - 1)
        
        if self.max_memory_mb is None:
            # Use 80% of available memory
            total_memory = psutil.virtual_memory().total
            self.max_memory_mb = int((total_memory * 0.8) / (1024 * 1024))


@dataclass
class BatchJobConfig:
    """Configuration for a batch job."""
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    priority: JobPriority = JobPriority.NORMAL
    
    # Source configuration
    source_ids: List[str] = field(default_factory=list)
    source_configs: Dict[str, Any] = field(default_factory=dict)
    
    # Processing configuration
    parallel_sources: bool = True
    parallel_pages: bool = False
    chunk_size: int = 100  # Pages per chunk
    
    # Retry configuration
    max_retries: int = 3
    retry_delay_seconds: float = 30.0
    
    # Output configuration
    output_path: Optional[Path] = None
    output_format: str = "jsonl"
    
    # Scheduling
    scheduled_start: Optional[datetime] = None
    estimated_duration: Optional[timedelta] = None
    
    # Callbacks
    progress_callback: Optional[Callable] = None
    completion_callback: Optional[Callable] = None
    error_callback: Optional[Callable] = None


@dataclass
class BatchJobResult:
    """Result of a batch job execution."""
    job_id: str
    status: JobStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Processing statistics
    total_sources: int = 0
    completed_sources: int = 0
    failed_sources: int = 0
    total_pages: int = 0
    processed_pages: int = 0
    failed_pages: int = 0
    
    # Performance metrics
    average_pages_per_second: float = 0.0
    peak_memory_usage_mb: float = 0.0
    average_cpu_usage: float = 0.0
    
    # Error tracking
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    
    # Output information
    output_files: List[Path] = field(default_factory=list)
    output_size_bytes: int = 0
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate job duration."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_pages == 0:
            return 0.0
        return (self.processed_pages / self.total_pages) * 100.0


class ResourceMonitor:
    """Monitor system resources during batch processing."""
    
    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self.monitoring = False
        self.monitor_thread = None
        self.current_usage = {
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'memory_mb': 0.0,
            'active_processes': 0
        }
        self._lock = threading.Lock()
    
    def start_monitoring(self):
        """Start resource monitoring in background thread."""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("Started resource monitoring")
    
    def stop_monitoring(self):
        """Stop resource monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        logger.info("Stopped resource monitoring")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                # Get current system usage
                cpu_percent = psutil.cpu_percent(interval=1.0)
                memory = psutil.virtual_memory()
                
                with self._lock:
                    self.current_usage.update({
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory.percent,
                        'memory_mb': memory.used / (1024 * 1024),
                        'active_processes': len(psutil.pids())
                    })
                
                # Log warnings if thresholds exceeded
                if cpu_percent > self.limits.cpu_usage_threshold:
                    logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
                
                if memory.percent > self.limits.memory_usage_threshold:
                    logger.warning(f"High memory usage: {memory.percent:.1f}%")
                
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
            
            time.sleep(1.0)
    
    def should_throttle(self) -> bool:
        """Check if processing should be throttled due to resource usage."""
        with self._lock:
            cpu_high = self.current_usage['cpu_percent'] > self.limits.cpu_usage_threshold
            memory_high = self.current_usage['memory_percent'] > self.limits.memory_usage_threshold
            return cpu_high or memory_high
    
    def get_usage_info(self) -> Dict[str, float]:
        """Get current resource usage information."""
        with self._lock:
            return self.current_usage.copy()


class BatchJobScheduler:
    """Scheduler for managing batch job execution order and timing."""
    
    def __init__(self, resource_limits: ResourceLimits):
        self.resource_limits = resource_limits
        self.job_queue = PriorityQueue()
        self.scheduled_jobs = {}  # job_id -> scheduled_time
        self.active_jobs = {}     # job_id -> BatchJobConfig
        self.completed_jobs = {}  # job_id -> BatchJobResult
        self.scheduler_thread = None
        self.running = False
        self._lock = threading.Lock()
    
    def start(self):
        """Start the job scheduler."""
        if not self.running:
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            logger.info("Started batch job scheduler")
    
    def stop(self):
        """Stop the job scheduler."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2.0)
        logger.info("Stopped batch job scheduler")
    
    def schedule_job(self, job_config: BatchJobConfig) -> str:
        """Schedule a job for execution."""
        priority_value = job_config.priority.value
        timestamp = time.time()
        
        # Higher priority jobs get negative timestamp for earlier execution
        queue_priority = (-priority_value, timestamp)
        
        with self._lock:
            self.job_queue.put((queue_priority, job_config))
            
            if job_config.scheduled_start:
                self.scheduled_jobs[job_config.job_id] = job_config.scheduled_start
        
        logger.info(f"Scheduled job {job_config.job_id}: {job_config.name}")
        return job_config.job_id
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled or active job."""
        with self._lock:
            # Remove from scheduled jobs
            if job_id in self.scheduled_jobs:
                del self.scheduled_jobs[job_id]
                logger.info(f"Cancelled scheduled job {job_id}")
                return True
            
            # Mark active job for cancellation
            if job_id in self.active_jobs:
                self.active_jobs[job_id].status = JobStatus.CANCELLED
                logger.info(f"Marked active job {job_id} for cancellation")
                return True
            
            # Check if job is in the queue
            temp_queue = []
            found = False
            while not self.job_queue.empty():
                try:
                    priority, job_config = self.job_queue.get_nowait()
                    if job_config.job_id == job_id:
                        found = True
                        logger.info(f"Cancelled queued job {job_id}")
                    else:
                        temp_queue.append((priority, job_config))
                except Exception:
                    break
            
            # Put non-cancelled jobs back in queue
            for item in temp_queue:
                self.job_queue.put(item)
            
            return found
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        with self._lock:
            return {
                'queued_jobs': self.job_queue.qsize(),
                'active_jobs': len(self.active_jobs),
                'completed_jobs': len(self.completed_jobs),
                'scheduled_jobs': len(self.scheduled_jobs)
            }
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.running:
            try:
                # Check for jobs ready to start
                current_time = datetime.now()
                ready_jobs = []
                
                # Process queue to find ready jobs
                temp_queue = []
                while not self.job_queue.empty():
                    try:
                        priority, job_config = self.job_queue.get_nowait()
                        
                        # Check if job is scheduled for future
                        if (job_config.scheduled_start and 
                            job_config.scheduled_start > current_time):
                            temp_queue.append((priority, job_config))
                            continue
                        
                        # Check if we can start this job
                        if len(self.active_jobs) < self.resource_limits.max_concurrent_jobs:
                            ready_jobs.append(job_config)
                        else:
                            temp_queue.append((priority, job_config))
                    
                    except Exception:
                        break
                
                # Put unprocessed jobs back in queue
                for item in temp_queue:
                    self.job_queue.put(item)
                
                # Start ready jobs
                for job_config in ready_jobs:
                    self._start_job(job_config)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
            
            time.sleep(1.0)
    
    def _start_job(self, job_config: BatchJobConfig):
        """Start execution of a job."""
        with self._lock:
            self.active_jobs[job_config.job_id] = job_config
        
        # This would trigger the actual job execution
        # Implementation depends on integration with BatchProcessor
        logger.info(f"Starting job {job_config.job_id}: {job_config.name}")


class BatchProcessor:
    """Main batch processing engine."""
    
    def __init__(self, resource_limits: Optional[ResourceLimits] = None):
        self.resource_limits = resource_limits or ResourceLimits()
        self.resource_monitor = ResourceMonitor(self.resource_limits)
        self.scheduler = BatchJobScheduler(self.resource_limits)
        self.active_jobs = {}
        self.job_results = {}
        self.running = False
        
        # Threading components
        self.thread_pool = None
        self.process_pool = None
        
        # Callbacks
        self.job_started_callback = None
        self.job_completed_callback = None
        self.job_failed_callback = None
    
    def start(self):
        """Start the batch processor."""
        if not self.running:
            self.running = True
            
            # Start resource monitoring
            self.resource_monitor.start_monitoring()
            
            # Start job scheduler
            self.scheduler.start()
            
            # Initialize thread pools
            max_workers = min(self.resource_limits.max_concurrent_jobs, 
                            self.resource_limits.max_cpu_cores)
            self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
            
            # Process pool for CPU-intensive tasks
            self.process_pool = ProcessPoolExecutor(
                max_workers=self.resource_limits.max_cpu_cores
            )
            
            logger.info("Batch processor started")
    
    def stop(self):
        """Stop the batch processor."""
        if self.running:
            self.running = False
            
            # Stop scheduler
            self.scheduler.stop()
            
            # Stop resource monitor
            self.resource_monitor.stop_monitoring()
            
            # Shutdown thread pools
            if self.thread_pool:
                self.thread_pool.shutdown(wait=True)
            
            if self.process_pool:
                self.process_pool.shutdown(wait=True)
            
            logger.info("Batch processor stopped")
    
    def submit_job(self, job_config: BatchJobConfig) -> str:
        """Submit a job for batch processing."""
        if not self.running:
            raise RuntimeError("Batch processor is not running")
        
        return self.scheduler.schedule_job(job_config)
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        return self.scheduler.cancel_job(job_id)
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job."""
        if job_id in self.job_results:
            result = self.job_results[job_id]
            return {
                'job_id': job_id,
                'status': result.status.value,
                'progress': {
                    'sources': f"{result.completed_sources}/{result.total_sources}",
                    'pages': f"{result.processed_pages}/{result.total_pages}",
                    'success_rate': result.success_rate
                },
                'performance': {
                    'duration': str(result.duration) if result.duration else None,
                    'pages_per_second': result.average_pages_per_second,
                    'memory_usage_mb': result.peak_memory_usage_mb
                }
            }
        
        return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        resource_usage = self.resource_monitor.get_usage_info()
        queue_status = self.scheduler.get_queue_status()
        
        return {
            'processor_running': self.running,
            'resource_usage': resource_usage,
            'resource_limits': {
                'max_cpu_cores': self.resource_limits.max_cpu_cores,
                'max_memory_mb': self.resource_limits.max_memory_mb,
                'max_concurrent_jobs': self.resource_limits.max_concurrent_jobs
            },
            'queue_status': queue_status,
            'should_throttle': self.resource_monitor.should_throttle()
        }
    
    def list_jobs(self, status_filter: Optional[JobStatus] = None) -> List[Dict[str, Any]]:
        """List all jobs with optional status filter."""
        jobs = []
        
        for job_id, result in self.job_results.items():
            if status_filter is None or result.status == status_filter:
                jobs.append({
                    'job_id': job_id,
                    'name': getattr(result, 'name', 'Unknown'),
                    'status': result.status.value,
                    'start_time': result.start_time.isoformat(),
                    'end_time': result.end_time.isoformat() if result.end_time else None,
                    'success_rate': result.success_rate,
                    'duration': str(result.duration) if result.duration else None
                })
        
        return sorted(jobs, key=lambda x: x['start_time'], reverse=True)


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create batch processor with custom limits
    limits = ResourceLimits(
        max_concurrent_jobs=2,
        max_cpu_cores=4,
        max_memory_mb=2048
    )
    
    processor = BatchProcessor(limits)
    
    try:
        # Start the processor
        processor.start()
        
        # Create a sample job
        job_config = BatchJobConfig(
            name="Test Batch Job",
            description="Testing batch processing system",
            priority=JobPriority.HIGH,
            source_ids=["vedabase_bg", "vedabase_sb"],
            parallel_sources=True
        )
        
        # Submit the job
        job_id = processor.submit_job(job_config)
        print(f"Submitted job: {job_id}")
        
        # Monitor for a bit
        for i in range(10):
            status = processor.get_system_status()
            print(f"System status: {status}")
            time.sleep(2)
        
    finally:
        # Clean shutdown
        processor.stop()
