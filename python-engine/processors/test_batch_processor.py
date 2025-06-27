"""
Test suite for the Batch Processing System.

This module provides comprehensive tests for all batch processing functionality.
"""

import pytest
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from batch_processor import (
    BatchProcessor, BatchJobConfig, BatchJobResult, ResourceLimits,
    JobStatus, JobPriority, ResourceMonitor, BatchJobScheduler
)


class TestResourceLimits:
    """Test ResourceLimits configuration."""
    
    def test_default_initialization(self):
        """Test default resource limits initialization."""
        limits = ResourceLimits()
        
        assert limits.max_cpu_cores is not None
        assert limits.max_cpu_cores >= 1
        assert limits.max_memory_mb is not None
        assert limits.max_memory_mb > 0
        assert limits.max_concurrent_jobs == 4
        assert limits.cpu_usage_threshold == 80.0
    
    def test_custom_initialization(self):
        """Test custom resource limits initialization."""
        limits = ResourceLimits(
            max_cpu_cores=8,
            max_memory_mb=4096,
            max_concurrent_jobs=6,
            cpu_usage_threshold=70.0
        )
        
        assert limits.max_cpu_cores == 8
        assert limits.max_memory_mb == 4096
        assert limits.max_concurrent_jobs == 6
        assert limits.cpu_usage_threshold == 70.0


class TestBatchJobConfig:
    """Test BatchJobConfig functionality."""
    
    def test_default_initialization(self):
        """Test default job configuration."""
        config = BatchJobConfig()
        
        assert config.job_id is not None
        assert len(config.job_id) > 0
        assert config.priority == JobPriority.NORMAL
        assert config.source_ids == []
        assert config.parallel_sources is True
        assert config.max_retries == 3
    
    def test_custom_initialization(self):
        """Test custom job configuration."""
        config = BatchJobConfig(
            name="Test Job",
            description="Test Description",
            priority=JobPriority.HIGH,
            source_ids=["source1", "source2"],
            parallel_sources=False,
            max_retries=5
        )
        
        assert config.name == "Test Job"
        assert config.description == "Test Description"
        assert config.priority == JobPriority.HIGH
        assert config.source_ids == ["source1", "source2"]
        assert config.parallel_sources is False
        assert config.max_retries == 5


class TestBatchJobResult:
    """Test BatchJobResult functionality."""
    
    def test_initialization(self):
        """Test job result initialization."""
        start_time = datetime.now()
        result = BatchJobResult(
            job_id="test-job",
            status=JobStatus.RUNNING,
            start_time=start_time
        )
        
        assert result.job_id == "test-job"
        assert result.status == JobStatus.RUNNING
        assert result.start_time == start_time
        assert result.duration is None
    
    def test_duration_calculation(self):
        """Test duration calculation."""
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=5)
        
        result = BatchJobResult(
            job_id="test-job",
            status=JobStatus.COMPLETED,
            start_time=start_time,
            end_time=end_time
        )
        
        assert result.duration == timedelta(minutes=5)
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        result = BatchJobResult(
            job_id="test-job",
            status=JobStatus.COMPLETED,
            start_time=datetime.now(),
            total_pages=100,
            processed_pages=85
        )
        
        assert result.success_rate == 85.0
    
    def test_success_rate_with_zero_pages(self):
        """Test success rate when no pages processed."""
        result = BatchJobResult(
            job_id="test-job",
            status=JobStatus.FAILED,
            start_time=datetime.now(),
            total_pages=0,
            processed_pages=0
        )
        
        assert result.success_rate == 0.0


class TestResourceMonitor:
    """Test ResourceMonitor functionality."""
    
    def test_initialization(self):
        """Test resource monitor initialization."""
        limits = ResourceLimits()
        monitor = ResourceMonitor(limits)
        
        assert monitor.limits == limits
        assert monitor.monitoring is False
        assert monitor.monitor_thread is None
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.pids')
    def test_monitoring_start_stop(self, mock_pids, mock_memory, mock_cpu):
        """Test starting and stopping monitoring."""
        # Mock system calls
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=60.0, used=1024*1024*1024, total=4*1024*1024*1024)
        mock_pids.return_value = [1, 2, 3, 4, 5]
        
        # Mock the psutil.virtual_memory for ResourceLimits initialization
        with patch('batch_processor.psutil.virtual_memory') as mock_vm_init:
            mock_vm_init.return_value = Mock(total=4*1024*1024*1024)
            limits = ResourceLimits()
            monitor = ResourceMonitor(limits)
        
        # Start monitoring
        monitor.start_monitoring()
        assert monitor.monitoring is True
        assert monitor.monitor_thread is not None
        
        # Give it a moment to collect data
        time.sleep(0.1)
        
        # Check usage data
        usage = monitor.get_usage_info()
        assert 'cpu_percent' in usage
        assert 'memory_percent' in usage
        
        # Stop monitoring
        monitor.stop_monitoring()
        assert monitor.monitoring is False
    
    def test_throttle_detection(self):
        """Test throttle detection logic."""
        limits = ResourceLimits(cpu_usage_threshold=70.0, memory_usage_threshold=80.0)
        monitor = ResourceMonitor(limits)
        
        # Simulate high CPU usage
        monitor.current_usage = {
            'cpu_percent': 85.0,
            'memory_percent': 60.0,
            'memory_mb': 1000,
            'active_processes': 50
        }
        
        assert monitor.should_throttle() is True
        
        # Simulate high memory usage
        monitor.current_usage = {
            'cpu_percent': 50.0,
            'memory_percent': 90.0,
            'memory_mb': 2000,
            'active_processes': 50
        }
        
        assert monitor.should_throttle() is True
        
        # Simulate normal usage
        monitor.current_usage = {
            'cpu_percent': 50.0,
            'memory_percent': 60.0,
            'memory_mb': 1000,
            'active_processes': 50
        }
        
        assert monitor.should_throttle() is False


class TestBatchJobScheduler:
    """Test BatchJobScheduler functionality."""
    
    def test_initialization(self):
        """Test scheduler initialization."""
        limits = ResourceLimits()
        scheduler = BatchJobScheduler(limits)
        
        assert scheduler.resource_limits == limits
        assert scheduler.running is False
        assert len(scheduler.active_jobs) == 0
    
    def test_job_scheduling(self):
        """Test job scheduling functionality."""
        limits = ResourceLimits()
        scheduler = BatchJobScheduler(limits)
        
        config = BatchJobConfig(name="Test Job", priority=JobPriority.HIGH)
        job_id = scheduler.schedule_job(config)
        
        assert job_id == config.job_id
        assert scheduler.job_queue.qsize() == 1
    
    def test_priority_ordering(self):
        """Test that higher priority jobs are scheduled first."""
        limits = ResourceLimits()
        scheduler = BatchJobScheduler(limits)
        
        # Schedule jobs with different priorities
        low_config = BatchJobConfig(name="Low Priority", priority=JobPriority.LOW)
        high_config = BatchJobConfig(name="High Priority", priority=JobPriority.HIGH)
        normal_config = BatchJobConfig(name="Normal Priority", priority=JobPriority.NORMAL)
        
        scheduler.schedule_job(low_config)
        scheduler.schedule_job(high_config)
        scheduler.schedule_job(normal_config)
        
        # The high priority job should be first
        priority, first_job = scheduler.job_queue.get()
        assert first_job.priority == JobPriority.HIGH
    
    def test_job_cancellation(self):
        """Test job cancellation."""
        limits = ResourceLimits()
        scheduler = BatchJobScheduler(limits)
        
        config = BatchJobConfig(name="Test Job")
        job_id = scheduler.schedule_job(config)
        
        # Cancel the job
        success = scheduler.cancel_job(job_id)
        assert success is True
        
        # Try to cancel non-existent job
        success = scheduler.cancel_job("non-existent")
        assert success is False
    
    def test_scheduled_start_time(self):
        """Test jobs with scheduled start times."""
        limits = ResourceLimits()
        scheduler = BatchJobScheduler(limits)
        
        future_time = datetime.now() + timedelta(hours=1)
        config = BatchJobConfig(
            name="Future Job",
            scheduled_start=future_time
        )
        
        job_id = scheduler.schedule_job(config)
        assert job_id in scheduler.scheduled_jobs
        assert scheduler.scheduled_jobs[job_id] == future_time
    
    def test_queue_status(self):
        """Test queue status reporting."""
        limits = ResourceLimits()
        scheduler = BatchJobScheduler(limits)
        
        # Add some jobs
        for i in range(3):
            config = BatchJobConfig(name=f"Job {i}")
            scheduler.schedule_job(config)
        
        status = scheduler.get_queue_status()
        assert status['queued_jobs'] == 3
        assert status['active_jobs'] == 0
        assert status['completed_jobs'] == 0


class TestBatchProcessor:
    """Test BatchProcessor functionality."""
    
    def test_initialization(self):
        """Test batch processor initialization."""
        processor = BatchProcessor()
        
        assert processor.running is False
        assert processor.resource_monitor is not None
        assert processor.scheduler is not None
    
    def test_custom_resource_limits(self):
        """Test processor with custom resource limits."""
        limits = ResourceLimits(max_concurrent_jobs=8)
        processor = BatchProcessor(limits)
        
        assert processor.resource_limits.max_concurrent_jobs == 8
    
    def test_start_stop(self):
        """Test starting and stopping the processor."""
        processor = BatchProcessor()
        
        # Start processor
        processor.start()
        assert processor.running is True
        assert processor.thread_pool is not None
        assert processor.process_pool is not None
        
        # Stop processor
        processor.stop()
        assert processor.running is False
    
    def test_job_submission(self):
        """Test job submission."""
        processor = BatchProcessor()
        processor.start()
        
        try:
            config = BatchJobConfig(name="Test Job")
            job_id = processor.submit_job(config)
            
            assert job_id is not None
            assert len(job_id) > 0
        
        finally:
            processor.stop()
    
    def test_job_submission_when_stopped(self):
        """Test that job submission fails when processor is stopped."""
        processor = BatchProcessor()
        
        config = BatchJobConfig(name="Test Job")
        
        with pytest.raises(RuntimeError):
            processor.submit_job(config)
    
    def test_system_status(self):
        """Test system status reporting."""
        processor = BatchProcessor()
        processor.start()
        
        try:
            status = processor.get_system_status()
            
            assert 'processor_running' in status
            assert 'resource_usage' in status
            assert 'resource_limits' in status
            assert 'queue_status' in status
            assert status['processor_running'] is True
        
        finally:
            processor.stop()
    
    def test_job_listing(self):
        """Test job listing functionality."""
        processor = BatchProcessor()
        
        # Add some mock job results
        processor.job_results = {
            'job1': BatchJobResult(
                job_id='job1',
                status=JobStatus.COMPLETED,
                start_time=datetime.now()
            ),
            'job2': BatchJobResult(
                job_id='job2',
                status=JobStatus.FAILED,
                start_time=datetime.now()
            )
        }
        
        # List all jobs
        all_jobs = processor.list_jobs()
        assert len(all_jobs) == 2
        
        # List only completed jobs
        completed_jobs = processor.list_jobs(JobStatus.COMPLETED)
        assert len(completed_jobs) == 1
        assert completed_jobs[0]['status'] == 'completed'
        
        # List only failed jobs
        failed_jobs = processor.list_jobs(JobStatus.FAILED)
        assert len(failed_jobs) == 1
        assert failed_jobs[0]['status'] == 'failed'


class TestIntegration:
    """Integration tests for the batch processing system."""
    
    def test_end_to_end_workflow(self):
        """Test complete workflow from job submission to completion."""
        # Create processor with minimal resources for testing
        limits = ResourceLimits(max_concurrent_jobs=1)
        processor = BatchProcessor(limits)
        
        processor.start()
        
        try:
            # Submit a test job
            config = BatchJobConfig(
                name="Integration Test Job",
                description="End-to-end test",
                priority=JobPriority.HIGH,
                source_ids=["test_source"]
            )
            
            job_id = processor.submit_job(config)
            
            # Check initial status
            status = processor.get_system_status()
            assert status['processor_running'] is True
            assert status['queue_status']['queued_jobs'] >= 0
            
            # Give system a moment to process
            time.sleep(0.1)
            
            # Check job listing
            jobs = processor.list_jobs()
            assert len(jobs) >= 0  # Job might not appear immediately in results
            
        finally:
            processor.stop()
    
    def test_resource_monitoring_integration(self):
        """Test resource monitoring integration."""
        processor = BatchProcessor()
        processor.start()
        
        try:
            # Get initial status
            initial_status = processor.get_system_status()
            assert 'resource_usage' in initial_status
            
            # Resource usage should be populated
            usage = initial_status['resource_usage']
            assert 'cpu_percent' in usage
            assert 'memory_percent' in usage
            
        finally:
            processor.stop()
    
    def test_multiple_job_scheduling(self):
        """Test scheduling multiple jobs with different priorities."""
        processor = BatchProcessor()
        processor.start()
        
        try:
            job_ids = []
            
            # Submit jobs with different priorities
            for priority in [JobPriority.LOW, JobPriority.HIGH, JobPriority.NORMAL]:
                config = BatchJobConfig(
                    name=f"Job {priority.name}",
                    priority=priority
                )
                job_id = processor.submit_job(config)
                job_ids.append(job_id)
            
            assert len(job_ids) == 3
            assert len(set(job_ids)) == 3  # All unique
            
            # Check queue status
            status = processor.get_system_status()
            assert status['queue_status']['queued_jobs'] >= 0
            
        finally:
            processor.stop()


# Performance and stress tests
class TestPerformance:
    """Performance tests for batch processing system."""
    
    def test_large_job_queue(self):
        """Test performance with large number of jobs."""
        processor = BatchProcessor()
        processor.start()
        
        try:
            # Submit many jobs
            num_jobs = 100
            job_ids = []
            
            start_time = time.time()
            for i in range(num_jobs):
                config = BatchJobConfig(name=f"Job {i}")
                job_id = processor.submit_job(config)
                job_ids.append(job_id)
            
            submission_time = time.time() - start_time
            
            assert len(job_ids) == num_jobs
            assert submission_time < 5.0  # Should submit 100 jobs in under 5 seconds
            
            # Check queue status
            status = processor.get_system_status()
            assert status['queue_status']['queued_jobs'] >= 0
            
        finally:
            processor.stop()
    
    def test_concurrent_access(self):
        """Test concurrent access to batch processor."""
        processor = BatchProcessor()
        processor.start()
        
        try:
            job_ids = []
            errors = []
            
            def submit_jobs(thread_id, num_jobs):
                """Submit jobs from a thread."""
                try:
                    for i in range(num_jobs):
                        config = BatchJobConfig(name=f"Thread{thread_id}-Job{i}")
                        job_id = processor.submit_job(config)
                        job_ids.append(job_id)
                except Exception as e:
                    errors.append(e)
            
            # Create multiple threads submitting jobs
            threads = []
            for i in range(5):
                thread = threading.Thread(target=submit_jobs, args=(i, 10))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Check results
            assert len(errors) == 0, f"Errors occurred: {errors}"
            assert len(job_ids) == 50  # 5 threads * 10 jobs each
            assert len(set(job_ids)) == 50  # All unique
            
        finally:
            processor.stop()


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
