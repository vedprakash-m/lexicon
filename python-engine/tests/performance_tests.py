"""
Performance and load testing suite for Lexicon RAG Dataset Preparation Tool.

This module provides comprehensive performance testing capabilities including:
- Load testing for concurrent operations
- Memory usage monitoring
- Processing speed benchmarks
- Resource utilization analysis
- Scalability testing

Run with: python performance_tests.py
"""

import os
import sys
import time
import json
import psutil
import threading
import multiprocessing
from pathlib import Path
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass, asdict
import statistics
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from processors.universal_rag_demo import UniversalRAGProcessor
from processors.advanced_chunking import AdvancedChunkingProcessor
from processors.batch_processor import BatchProcessor
from processors.quality_analysis import QualityAnalysisProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    operation_name: str
    duration: float
    memory_usage_mb: float
    cpu_usage_percent: float
    throughput_ops_per_sec: float
    success_count: int
    error_count: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float

@dataclass
class LoadTestResults:
    """Load test results data structure."""
    test_name: str
    concurrent_users: int
    total_operations: int
    duration: float
    success_rate: float
    avg_response_time: float
    throughput: float
    memory_peak_mb: float
    cpu_peak_percent: float
    errors: List[str]

class PerformanceMonitor:
    """Monitor system performance during tests."""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = []
        self.process = psutil.Process()
    
    def start_monitoring(self):
        """Start performance monitoring."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=1.0)
    
    def _monitor_loop(self):
        """Monitoring loop."""
        while self.monitoring:
            try:
                cpu_percent = self.process.cpu_percent()
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                
                metric = {
                    'timestamp': time.time(),
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_mb
                }
                
                self.metrics.append(metric)
                time.sleep(0.1)  # Sample every 100ms
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                break
    
    def get_peak_metrics(self) -> Dict[str, float]:
        """Get peak performance metrics."""
        if not self.metrics:
            return {'cpu_peak': 0.0, 'memory_peak': 0.0}
        
        cpu_values = [m['cpu_percent'] for m in self.metrics]
        memory_values = [m['memory_mb'] for m in self.metrics]
        
        return {
            'cpu_peak': max(cpu_values) if cpu_values else 0.0,
            'memory_peak': max(memory_values) if memory_values else 0.0,
            'cpu_avg': statistics.mean(cpu_values) if cpu_values else 0.0,
            'memory_avg': statistics.mean(memory_values) if memory_values else 0.0
        }

class PerformanceTestSuite:
    """Comprehensive performance testing suite."""
    
    def __init__(self):
        """Initialize the performance test suite."""
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Initialize processors
        self.rag_processor = UniversalRAGProcessor()
        self.chunking_processor = AdvancedChunkingProcessor()
        self.batch_processor = BatchProcessor()
        self.quality_analyzer = QualityAnalysisProcessor()
        
        # Create test data
        self.create_test_data()
        
        # Performance monitor
        self.monitor = PerformanceMonitor()
        
        logger.info("Performance test suite initialized")
    
    def create_test_data(self):
        """Create test data of various sizes."""
        test_texts = {
            'small': "Short text for testing. " * 10,
            'medium': "Medium sized text for performance testing. " * 100,
            'large': "Large text document for stress testing. " * 1000,
            'xlarge': "Extra large text document for heavy load testing. " * 5000
        }
        
        for size, content in test_texts.items():
            file_path = self.test_data_dir / f"test_{size}.txt"
            file_path.write_text(content)
        
        # Create multiple files for batch testing
        for i in range(20):
            file_path = self.test_data_dir / f"batch_test_{i:03d}.txt"
            content = f"Batch test document {i}. " * (50 * (i + 1))
            file_path.write_text(content)
        
        logger.info(f"Created test data in {self.test_data_dir}")
    
    def measure_operation(self, operation_func, *args, **kwargs) -> Tuple[Any, PerformanceMetrics]:
        """Measure performance of a single operation."""
        # Get initial metrics
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        initial_cpu = psutil.Process().cpu_percent()
        
        # Execute operation
        start_time = time.time()
        
        try:
            result = operation_func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Get final metrics
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        final_cpu = psutil.Process().cpu_percent()
        
        metrics = PerformanceMetrics(
            operation_name=operation_func.__name__,
            duration=duration,
            memory_usage_mb=final_memory - initial_memory,
            cpu_usage_percent=(initial_cpu + final_cpu) / 2,
            throughput_ops_per_sec=1.0 / duration if duration > 0 else 0,
            success_count=1 if success else 0,
            error_count=0 if success else 1,
            avg_response_time=duration,
            min_response_time=duration,
            max_response_time=duration
        )
        
        return result, metrics
    
    def test_file_processing_performance(self) -> Dict[str, PerformanceMetrics]:
        """Test file processing performance with different file sizes."""
        results = {}
        
        file_sizes = ['small', 'medium', 'large', 'xlarge']
        
        for size in file_sizes:
            file_path = self.test_data_dir / f"test_{size}.txt"
            
            logger.info(f"Testing file processing performance: {size}")
            
            result, metrics = self.measure_operation(
                self.rag_processor.process_file,
                str(file_path)
            )
            
            results[f"file_processing_{size}"] = metrics
            
            logger.info(f"  Duration: {metrics.duration:.3f}s")
            logger.info(f"  Memory: {metrics.memory_usage_mb:.2f}MB")
            logger.info(f"  Throughput: {metrics.throughput_ops_per_sec:.2f} ops/sec")
        
        return results
    
    def test_chunking_performance(self) -> Dict[str, PerformanceMetrics]:
        """Test chunking performance with different strategies."""
        results = {}
        
        # Test different chunking strategies
        strategies = ['semantic', 'sliding_window', 'sentence_based', 'paragraph_based']
        test_text = (self.test_data_dir / "test_large.txt").read_text()
        
        for strategy in strategies:
            logger.info(f"Testing chunking performance: {strategy}")
            
            config = {
                "strategy": strategy,
                "chunk_size": 200,
                "overlap": 50
            }
            
            result, metrics = self.measure_operation(
                self.chunking_processor.process_text,
                test_text,
                config
            )
            
            results[f"chunking_{strategy}"] = metrics
            
            logger.info(f"  Duration: {metrics.duration:.3f}s")
            logger.info(f"  Throughput: {metrics.throughput_ops_per_sec:.2f} ops/sec")
        
        return results
    
    def test_batch_processing_performance(self) -> PerformanceMetrics:
        """Test batch processing performance."""
        logger.info("Testing batch processing performance")
        
        # Get batch test files
        batch_files = list(self.test_data_dir.glob("batch_test_*.txt"))
        file_paths = [str(f) for f in batch_files[:10]]  # Use first 10 files
        
        batch_config = {
            "chunk_size": 200,
            "overlap": 50,
            "quality_threshold": 0.5,
            "output_format": "json"
        }
        
        def batch_operation():
            batch_job = self.batch_processor.create_batch_job(file_paths, batch_config)
            return self.batch_processor.execute_batch(batch_job["job_id"])
        
        result, metrics = self.measure_operation(batch_operation)
        
        logger.info(f"Batch processing duration: {metrics.duration:.3f}s")
        logger.info(f"Files processed: {len(file_paths)}")
        logger.info(f"Throughput: {len(file_paths) / metrics.duration:.2f} files/sec")
        
        return metrics
    
    def test_concurrent_load(self, concurrent_users: int = 5, operations_per_user: int = 10) -> LoadTestResults:
        """Test concurrent load performance."""
        logger.info(f"Testing concurrent load: {concurrent_users} users, {operations_per_user} ops each")
        
        self.monitor.start_monitoring()
        
        # Test data
        file_path = self.test_data_dir / "test_medium.txt"
        
        # Results tracking
        results = []
        errors = []
        start_time = time.time()
        
        def user_operations():
            """Simulate a user performing multiple operations."""
            user_results = []
            
            for _ in range(operations_per_user):
                try:
                    op_start = time.time()
                    result = self.rag_processor.process_file(str(file_path))
                    op_duration = time.time() - op_start
                    
                    user_results.append({
                        'success': True,
                        'duration': op_duration
                    })
                    
                except Exception as e:
                    user_results.append({
                        'success': False,
                        'duration': 0,
                        'error': str(e)
                    })
            
            return user_results
        
        # Execute concurrent operations
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(user_operations) for _ in range(concurrent_users)]
            
            for future in futures:
                try:
                    user_results = future.result()
                    results.extend(user_results)
                except Exception as e:
                    errors.append(str(e))
        
        total_duration = time.time() - start_time
        self.monitor.stop_monitoring()
        
        # Calculate metrics
        successful_ops = [r for r in results if r['success']]
        failed_ops = [r for r in results if not r['success']]
        
        success_rate = len(successful_ops) / len(results) * 100 if results else 0
        avg_response_time = statistics.mean([r['duration'] for r in successful_ops]) if successful_ops else 0
        throughput = len(successful_ops) / total_duration if total_duration > 0 else 0
        
        # Get peak system metrics
        peak_metrics = self.monitor.get_peak_metrics()
        
        load_test_results = LoadTestResults(
            test_name="concurrent_load",
            concurrent_users=concurrent_users,
            total_operations=len(results),
            duration=total_duration,
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            throughput=throughput,
            memory_peak_mb=peak_metrics['memory_peak'],
            cpu_peak_percent=peak_metrics['cpu_peak'],
            errors=[r.get('error', '') for r in failed_ops]
        )
        
        logger.info(f"Concurrent load test results:")
        logger.info(f"  Success rate: {success_rate:.1f}%")
        logger.info(f"  Avg response time: {avg_response_time:.3f}s")
        logger.info(f"  Throughput: {throughput:.2f} ops/sec")
        logger.info(f"  Peak memory: {peak_metrics['memory_peak']:.2f}MB")
        logger.info(f"  Peak CPU: {peak_metrics['cpu_peak']:.1f}%")
        
        return load_test_results
    
    def test_memory_stress(self) -> Dict[str, Any]:
        """Test memory usage under stress conditions."""
        logger.info("Testing memory stress performance")
        
        self.monitor.start_monitoring()
        
        # Process increasingly large files
        large_files = []
        
        try:
            # Create progressively larger files
            for i in range(5):
                size_multiplier = 2 ** i  # 1x, 2x, 4x, 8x, 16x
                content = "Large content for memory testing. " * (1000 * size_multiplier)
                file_path = self.test_data_dir / f"memory_test_{i}.txt"
                file_path.write_text(content)
                large_files.append(file_path)
                
                # Process the file
                result = self.rag_processor.process_file(str(file_path))
                
                # Get current memory usage
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                logger.info(f"  File {i+1}: {current_memory:.2f}MB memory usage")
                
                # Brief pause between operations
                time.sleep(0.5)
        
        except Exception as e:
            logger.error(f"Memory stress test error: {e}")
        
        finally:
            self.monitor.stop_monitoring()
            
            # Cleanup large files
            for file_path in large_files:
                try:
                    file_path.unlink()
                except:
                    pass
        
        peak_metrics = self.monitor.get_peak_metrics()
        
        return {
            "memory_peak_mb": peak_metrics['memory_peak'],
            "memory_avg_mb": peak_metrics['memory_avg'],
            "cpu_peak_percent": peak_metrics['cpu_peak'],
            "cpu_avg_percent": peak_metrics['cpu_avg']
        }
    
    def test_scalability(self) -> Dict[str, Any]:
        """Test system scalability with increasing load."""
        logger.info("Testing scalability")
        
        scalability_results = {}
        
        # Test with increasing numbers of concurrent users
        user_counts = [1, 2, 4, 8, 16]
        
        for user_count in user_counts:
            logger.info(f"Testing scalability with {user_count} concurrent users")
            
            load_results = self.test_concurrent_load(
                concurrent_users=user_count,
                operations_per_user=5
            )
            
            scalability_results[f"users_{user_count}"] = {
                "throughput": load_results.throughput,
                "avg_response_time": load_results.avg_response_time,
                "success_rate": load_results.success_rate,
                "memory_peak": load_results.memory_peak_mb,
                "cpu_peak": load_results.cpu_peak_percent
            }
            
            # Brief pause between tests
            time.sleep(2)
        
        return scalability_results
    
    def run_performance_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive performance benchmark."""
        logger.info("Starting comprehensive performance benchmark")
        
        benchmark_results = {
            "timestamp": time.time(),
            "system_info": {
                "cpu_count": multiprocessing.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "platform": sys.platform
            }
        }
        
        # Run individual performance tests
        benchmark_results["file_processing"] = self.test_file_processing_performance()
        benchmark_results["chunking"] = self.test_chunking_performance()
        benchmark_results["batch_processing"] = asdict(self.test_batch_processing_performance())
        benchmark_results["concurrent_load"] = asdict(self.test_concurrent_load())
        benchmark_results["memory_stress"] = self.test_memory_stress()
        benchmark_results["scalability"] = self.test_scalability()
        
        # Save benchmark results
        results_file = Path(__file__).parent / "performance_benchmark_results.json"
        
        # Convert PerformanceMetrics objects to dicts
        def convert_metrics(obj):
            if isinstance(obj, PerformanceMetrics):
                return asdict(obj)
            elif isinstance(obj, dict):
                return {k: convert_metrics(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_metrics(item) for item in obj]
            else:
                return obj
        
        serializable_results = convert_metrics(benchmark_results)
        
        results_file.write_text(json.dumps(serializable_results, indent=2))
        
        logger.info(f"Performance benchmark completed. Results saved to {results_file}")
        
        return serializable_results
    
    def generate_performance_report(self, results: Dict[str, Any]) -> str:
        """Generate a human-readable performance report."""
        report_lines = []
        report_lines.append("LEXICON PERFORMANCE BENCHMARK REPORT")
        report_lines.append("=" * 50)
        report_lines.append("")
        
        # System info
        system_info = results["system_info"]
        report_lines.append("SYSTEM INFORMATION:")
        report_lines.append(f"  CPU Cores: {system_info['cpu_count']}")
        report_lines.append(f"  Total Memory: {system_info['memory_total_gb']:.2f} GB")
        report_lines.append(f"  Platform: {system_info['platform']}")
        report_lines.append("")
        
        # File processing performance
        report_lines.append("FILE PROCESSING PERFORMANCE:")
        file_processing = results["file_processing"]
        for test_name, metrics in file_processing.items():
            size = test_name.replace("file_processing_", "")
            report_lines.append(f"  {size.upper()}: {metrics['duration']:.3f}s, {metrics['throughput_ops_per_sec']:.2f} ops/sec")
        report_lines.append("")
        
        # Concurrent load performance
        concurrent_load = results["concurrent_load"]
        report_lines.append("CONCURRENT LOAD PERFORMANCE:")
        report_lines.append(f"  Users: {concurrent_load['concurrent_users']}")
        report_lines.append(f"  Success Rate: {concurrent_load['success_rate']:.1f}%")
        report_lines.append(f"  Avg Response Time: {concurrent_load['avg_response_time']:.3f}s")
        report_lines.append(f"  Throughput: {concurrent_load['throughput']:.2f} ops/sec")
        report_lines.append(f"  Peak Memory: {concurrent_load['memory_peak_mb']:.2f} MB")
        report_lines.append("")
        
        # Memory stress test
        memory_stress = results["memory_stress"]
        report_lines.append("MEMORY STRESS TEST:")
        report_lines.append(f"  Peak Memory Usage: {memory_stress['memory_peak_mb']:.2f} MB")
        report_lines.append(f"  Average Memory Usage: {memory_stress['memory_avg_mb']:.2f} MB")
        report_lines.append(f"  Peak CPU Usage: {memory_stress['cpu_peak_percent']:.1f}%")
        report_lines.append("")
        
        # Scalability results
        scalability = results["scalability"]
        report_lines.append("SCALABILITY TEST:")
        for user_test, metrics in scalability.items():
            users = user_test.replace("users_", "")
            report_lines.append(f"  {users} users: {metrics['throughput']:.2f} ops/sec, {metrics['avg_response_time']:.3f}s response")
        report_lines.append("")
        
        report_lines.append("=" * 50)
        
        return "\n".join(report_lines)

def main():
    """Main function to run performance tests."""
    suite = PerformanceTestSuite()
    
    try:
        # Run benchmark
        results = suite.run_performance_benchmark()
        
        # Generate and display report
        report = suite.generate_performance_report(results)
        print(report)
        
        # Save report
        report_file = Path(__file__).parent / "performance_report.txt"
        report_file.write_text(report)
        
        print(f"\nPerformance report saved to: {report_file}")
        
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        raise

if __name__ == "__main__":
    main()
