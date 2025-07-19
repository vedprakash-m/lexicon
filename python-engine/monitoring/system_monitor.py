"""
System monitoring and alerting system for Lexicon RAG Dataset Preparation Tool.

This module provides real-time monitoring capabilities including:
- System resource monitoring
- Application performance tracking
- Error rate monitoring
- Alert threshold management
- Health check endpoints

Run with: python system_monitor.py
"""

import os
import sys
import time
import json
import psutil
import logging
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import statistics
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SystemMetrics:
    """System performance metrics."""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int
    load_average: List[float]

@dataclass
class ApplicationMetrics:
    """Application-specific metrics."""
    timestamp: float
    active_connections: int
    request_count: int
    error_count: int
    avg_response_time: float
    queue_size: int
    processed_files: int
    failed_files: int
    cache_hit_rate: float
    memory_usage_mb: float

@dataclass
class Alert:
    """Alert data structure."""
    id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: float
    metric_name: str
    metric_value: float
    threshold: float
    acknowledged: bool = False
    resolved: bool = False

class AlertManager:
    """Manages system alerts and notifications."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize alert manager."""
        self.config = config or {}
        self.alerts: List[Alert] = []
        self.alert_handlers: List[Callable] = []
        self.alert_history: List[Alert] = []
        
        # Default thresholds
        self.thresholds = {
            'cpu_percent': {'warning': 80.0, 'critical': 95.0},
            'memory_percent': {'warning': 85.0, 'critical': 95.0},
            'disk_usage_percent': {'warning': 90.0, 'critical': 98.0},
            'error_rate': {'warning': 5.0, 'critical': 10.0},
            'response_time': {'warning': 2.0, 'critical': 5.0},
            'queue_size': {'warning': 100, 'critical': 500}
        }
        
        # Update thresholds from config
        if 'thresholds' in self.config:
            self.thresholds.update(self.config['thresholds'])
    
    def add_alert_handler(self, handler: Callable):
        """Add an alert handler function."""
        self.alert_handlers.append(handler)
    
    def check_metric_thresholds(self, metric_name: str, value: float) -> Optional[Alert]:
        """Check if a metric exceeds thresholds."""
        if metric_name not in self.thresholds:
            return None
        
        thresholds = self.thresholds[metric_name]
        alert_id = f"{metric_name}_{int(time.time())}"
        
        if value >= thresholds.get('critical', float('inf')):
            return Alert(
                id=alert_id,
                severity=AlertSeverity.CRITICAL,
                title=f"Critical {metric_name} threshold exceeded",
                message=f"{metric_name} is at {value:.2f}, exceeding critical threshold of {thresholds['critical']:.2f}",
                timestamp=time.time(),
                metric_name=metric_name,
                metric_value=value,
                threshold=thresholds['critical']
            )
        elif value >= thresholds.get('warning', float('inf')):
            return Alert(
                id=alert_id,
                severity=AlertSeverity.HIGH,
                title=f"Warning {metric_name} threshold exceeded",
                message=f"{metric_name} is at {value:.2f}, exceeding warning threshold of {thresholds['warning']:.2f}",
                timestamp=time.time(),
                metric_name=metric_name,
                metric_value=value,
                threshold=thresholds['warning']
            )
        
        return None
    
    def trigger_alert(self, alert: Alert):
        """Trigger an alert and notify handlers."""
        self.alerts.append(alert)
        self.alert_history.append(alert)
        
        logger.warning(f"ALERT [{alert.severity.value.upper()}]: {alert.title}")
        logger.warning(f"Message: {alert.message}")
        
        # Notify handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                logger.info(f"Alert {alert_id} acknowledged")
                break
    
    def resolve_alert(self, alert_id: str):
        """Resolve an alert."""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                logger.info(f"Alert {alert_id} resolved")
                break
        
        # Remove from active alerts
        self.alerts = [a for a in self.alerts if a.id != alert_id]
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return [a for a in self.alerts if not a.resolved]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics."""
        active_alerts = self.get_active_alerts()
        
        return {
            'total_active': len(active_alerts),
            'critical': len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
            'high': len([a for a in active_alerts if a.severity == AlertSeverity.HIGH]),
            'medium': len([a for a in active_alerts if a.severity == AlertSeverity.MEDIUM]),
            'low': len([a for a in active_alerts if a.severity == AlertSeverity.LOW]),
            'unacknowledged': len([a for a in active_alerts if not a.acknowledged])
        }

class SystemMonitor:
    """Monitors system resources and performance."""
    
    def __init__(self, alert_manager: AlertManager):
        """Initialize system monitor."""
        self.alert_manager = alert_manager
        self.monitoring = False
        self.metrics_history: List[SystemMetrics] = []
        self.max_history_size = 1000
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_usage_percent = disk.percent
        disk_free_gb = disk.free / (1024**3)
        
        # Network metrics
        network = psutil.net_io_counters()
        network_bytes_sent = network.bytes_sent
        network_bytes_recv = network.bytes_recv
        
        # Process metrics
        process_count = len(psutil.pids())
        
        # Load average (Unix-like systems)
        try:
            load_average = list(psutil.getloadavg())
        except AttributeError:
            load_average = [0.0, 0.0, 0.0]  # Windows fallback
        
        metrics = SystemMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_gb=memory_available_gb,
            disk_usage_percent=disk_usage_percent,
            disk_free_gb=disk_free_gb,
            network_bytes_sent=network_bytes_sent,
            network_bytes_recv=network_bytes_recv,
            process_count=process_count,
            load_average=load_average
        )
        
        return metrics
    
    def check_system_alerts(self, metrics: SystemMetrics):
        """Check system metrics against alert thresholds."""
        checks = [
            ('cpu_percent', metrics.cpu_percent),
            ('memory_percent', metrics.memory_percent),
            ('disk_usage_percent', metrics.disk_usage_percent)
        ]
        
        for metric_name, value in checks:
            alert = self.alert_manager.check_metric_thresholds(metric_name, value)
            if alert:
                self.alert_manager.trigger_alert(alert)
    
    def start_monitoring(self, interval: float = 60.0):
        """Start system monitoring."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,)
        )
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info(f"System monitoring started (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop system monitoring."""
        self.monitoring = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=5.0)
        
        logger.info("System monitoring stopped")
    
    def _monitor_loop(self, interval: float):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                # Collect metrics
                metrics = self.collect_system_metrics()
                
                # Store metrics
                self.metrics_history.append(metrics)
                
                # Trim history if needed
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history = self.metrics_history[-self.max_history_size:]
                
                # Check alerts
                self.check_system_alerts(metrics)
                
                # Log current status
                logger.info(f"System Status - CPU: {metrics.cpu_percent:.1f}%, "
                           f"Memory: {metrics.memory_percent:.1f}%, "
                           f"Disk: {metrics.disk_usage_percent:.1f}%")
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                time.sleep(interval)
    
    def get_metrics_summary(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """Get system metrics summary for the specified duration."""
        cutoff_time = time.time() - (duration_minutes * 60)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {}
        
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        disk_values = [m.disk_usage_percent for m in recent_metrics]
        
        return {
            'duration_minutes': duration_minutes,
            'sample_count': len(recent_metrics),
            'cpu': {
                'avg': statistics.mean(cpu_values),
                'min': min(cpu_values),
                'max': max(cpu_values),
                'current': recent_metrics[-1].cpu_percent
            },
            'memory': {
                'avg': statistics.mean(memory_values),
                'min': min(memory_values),
                'max': max(memory_values),
                'current': recent_metrics[-1].memory_percent,
                'available_gb': recent_metrics[-1].memory_available_gb
            },
            'disk': {
                'avg': statistics.mean(disk_values),
                'min': min(disk_values),
                'max': max(disk_values),
                'current': recent_metrics[-1].disk_usage_percent,
                'free_gb': recent_metrics[-1].disk_free_gb
            }
        }

class ApplicationMonitor:
    """Monitors application-specific metrics."""
    
    def __init__(self, alert_manager: AlertManager):
        """Initialize application monitor."""
        self.alert_manager = alert_manager
        self.metrics_history: List[ApplicationMetrics] = []
        self.max_history_size = 1000
        
        # Application state
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
        self.processed_files = 0
        self.failed_files = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def record_request(self, response_time: float, success: bool = True):
        """Record a request with response time."""
        self.request_count += 1
        self.response_times.append(response_time)
        
        # Keep only recent response times
        if len(self.response_times) > 100:
            self.response_times = self.response_times[-100:]
        
        if not success:
            self.error_count += 1
    
    def record_file_processing(self, success: bool = True):
        """Record file processing result."""
        if success:
            self.processed_files += 1
        else:
            self.failed_files += 1
    
    def record_cache_hit(self):
        """Record cache hit."""
        self.cache_hits += 1
    
    def record_cache_miss(self):
        """Record cache miss."""
        self.cache_misses += 1
    
    def collect_application_metrics(self) -> ApplicationMetrics:
        """Collect current application metrics."""
        # Calculate metrics
        avg_response_time = statistics.mean(self.response_times) if self.response_times else 0.0
        
        total_cache_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = (self.cache_hits / total_cache_requests * 100) if total_cache_requests > 0 else 0.0
        
        # Get process memory usage
        try:
            process = psutil.Process()
            memory_usage_mb = process.memory_info().rss / (1024 * 1024)
        except:
            memory_usage_mb = 0.0
        
        metrics = ApplicationMetrics(
            timestamp=time.time(),
            active_connections=0,  # Would be set by application
            request_count=self.request_count,
            error_count=self.error_count,
            avg_response_time=avg_response_time,
            queue_size=0,  # Would be set by application
            processed_files=self.processed_files,
            failed_files=self.failed_files,
            cache_hit_rate=cache_hit_rate,
            memory_usage_mb=memory_usage_mb
        )
        
        return metrics
    
    def check_application_alerts(self, metrics: ApplicationMetrics):
        """Check application metrics against alert thresholds."""
        # Calculate error rate
        total_requests = metrics.request_count
        error_rate = (metrics.error_count / total_requests * 100) if total_requests > 0 else 0.0
        
        checks = [
            ('error_rate', error_rate),
            ('response_time', metrics.avg_response_time),
            ('queue_size', metrics.queue_size)
        ]
        
        for metric_name, value in checks:
            alert = self.alert_manager.check_metric_thresholds(metric_name, value)
            if alert:
                self.alert_manager.trigger_alert(alert)

class HealthChecker:
    """Provides health check endpoints and status."""
    
    def __init__(self, system_monitor: SystemMonitor, app_monitor: ApplicationMonitor):
        """Initialize health checker."""
        self.system_monitor = system_monitor
        self.app_monitor = app_monitor
        self.health_checks = {}
        self.last_check_time = time.time()
    
    def add_health_check(self, name: str, check_func: Callable):
        """Add a custom health check."""
        self.health_checks[name] = check_func
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {
            'timestamp': time.time(),
            'overall_status': 'healthy',
            'checks': {}
        }
        
        # System health checks
        system_metrics = self.system_monitor.collect_system_metrics()
        results['checks']['system'] = {
            'status': 'healthy',
            'cpu_percent': system_metrics.cpu_percent,
            'memory_percent': system_metrics.memory_percent,
            'disk_percent': system_metrics.disk_usage_percent
        }
        
        # Check system thresholds
        if (system_metrics.cpu_percent > 90 or 
            system_metrics.memory_percent > 90 or 
            system_metrics.disk_usage_percent > 95):
            results['checks']['system']['status'] = 'warning'
            results['overall_status'] = 'warning'
        
        # Application health checks
        app_metrics = self.app_monitor.collect_application_metrics()
        results['checks']['application'] = {
            'status': 'healthy',
            'error_rate': (app_metrics.error_count / max(app_metrics.request_count, 1)) * 100,
            'avg_response_time': app_metrics.avg_response_time,
            'processed_files': app_metrics.processed_files,
            'failed_files': app_metrics.failed_files
        }
        
        # Check application thresholds
        error_rate = results['checks']['application']['error_rate']
        if error_rate > 10 or app_metrics.avg_response_time > 5:
            results['checks']['application']['status'] = 'unhealthy'
            results['overall_status'] = 'unhealthy'
        
        # Custom health checks
        for name, check_func in self.health_checks.items():
            try:
                check_result = check_func()
                results['checks'][name] = check_result
                
                if check_result.get('status') == 'unhealthy':
                    results['overall_status'] = 'unhealthy'
                elif check_result.get('status') == 'warning' and results['overall_status'] == 'healthy':
                    results['overall_status'] = 'warning'
                    
            except Exception as e:
                results['checks'][name] = {
                    'status': 'error',
                    'error': str(e)
                }
                results['overall_status'] = 'unhealthy'
        
        self.last_check_time = time.time()
        return results
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return self.run_health_checks()

class EmailAlertHandler:
    """Handles email alerts."""
    
    def __init__(self, smtp_config: Dict[str, Any]):
        """Initialize email alert handler."""
        self.smtp_config = smtp_config
        self.enabled = smtp_config.get('enabled', False)
    
    def send_alert(self, alert: Alert):
        """Send alert via email."""
        if not self.enabled:
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = ', '.join(self.smtp_config['to_emails'])
            msg['Subject'] = f"[LEXICON ALERT] {alert.title}"
            
            body = f"""
Alert Details:
- Severity: {alert.severity.value.upper()}
- Message: {alert.message}
- Metric: {alert.metric_name}
- Value: {alert.metric_value}
- Threshold: {alert.threshold}
- Time: {datetime.fromtimestamp(alert.timestamp)}

This is an automated alert from the Lexicon monitoring system.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port'])
            if self.smtp_config.get('use_tls'):
                server.starttls()
            if self.smtp_config.get('username'):
                server.login(self.smtp_config['username'], self.smtp_config['password'])
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent for {alert.id}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

class MonitoringSystem:
    """Main monitoring system that coordinates all components."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize monitoring system."""
        self.config = self.load_config(config_path)
        
        # Initialize components
        self.alert_manager = AlertManager(self.config.get('alerts', {}))
        self.system_monitor = SystemMonitor(self.alert_manager)
        self.app_monitor = ApplicationMonitor(self.alert_manager)
        self.health_checker = HealthChecker(self.system_monitor, self.app_monitor)
        
        # Setup alert handlers
        self.setup_alert_handlers()
        
        # Monitoring state
        self.running = False
        
        logger.info("Monitoring system initialized")
    
    def load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load monitoring configuration."""
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config from {config_path}: {e}")
        
        # Default configuration
        return {
            'alerts': {
                'thresholds': {
                    'cpu_percent': {'warning': 80.0, 'critical': 95.0},
                    'memory_percent': {'warning': 85.0, 'critical': 95.0},
                    'disk_usage_percent': {'warning': 90.0, 'critical': 98.0},
                    'error_rate': {'warning': 5.0, 'critical': 10.0},
                    'response_time': {'warning': 2.0, 'critical': 5.0}
                }
            },
            'monitoring': {
                'system_interval': 60.0,
                'app_interval': 30.0
            },
            'email': {
                'enabled': False
            }
        }
    
    def setup_alert_handlers(self):
        """Setup alert handlers."""
        # Email handler
        email_config = self.config.get('email', {})
        if email_config.get('enabled'):
            email_handler = EmailAlertHandler(email_config)
            self.alert_manager.add_alert_handler(email_handler.send_alert)
    
    def start(self):
        """Start the monitoring system."""
        if self.running:
            logger.warning("Monitoring system is already running")
            return
        
        self.running = True
        
        # Start system monitoring
        system_interval = self.config.get('monitoring', {}).get('system_interval', 60.0)
        self.system_monitor.start_monitoring(system_interval)
        
        logger.info("Monitoring system started")
    
    def stop(self):
        """Stop the monitoring system."""
        if not self.running:
            return
        
        self.running = False
        
        # Stop monitors
        self.system_monitor.stop_monitoring()
        
        logger.info("Monitoring system stopped")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        return {
            'timestamp': time.time(),
            'system_metrics': self.system_monitor.get_metrics_summary(60),
            'application_metrics': asdict(self.app_monitor.collect_application_metrics()),
            'alerts': {
                'active': [asdict(alert) for alert in self.alert_manager.get_active_alerts()],
                'summary': self.alert_manager.get_alert_summary()
            },
            'health_status': self.health_checker.get_health_status()
        }
    
    def save_metrics_snapshot(self, filepath: str):
        """Save current metrics snapshot to file."""
        data = self.get_dashboard_data()
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Metrics snapshot saved to {filepath}")

def main():
    """Main function to run the monitoring system."""
    monitor = MonitoringSystem()
    
    try:
        monitor.start()
        
        # Run for demonstration
        logger.info("Monitoring system running. Press Ctrl+C to stop.")
        
        # Simulate some application activity
        for i in range(10):
            # Simulate requests
            monitor.app_monitor.record_request(0.5 + (i * 0.1))
            monitor.app_monitor.record_file_processing(success=i % 10 != 0)
            
            if i % 3 == 0:
                monitor.app_monitor.record_cache_hit()
            else:
                monitor.app_monitor.record_cache_miss()
            
            time.sleep(2)
        
        # Get dashboard data
        dashboard_data = monitor.get_dashboard_data()
        
        # Save snapshot
        snapshot_file = Path(__file__).parent / "monitoring_snapshot.json"
        monitor.save_metrics_snapshot(str(snapshot_file))
        
        print("\nMonitoring Dashboard Summary:")
        print(f"System CPU: {dashboard_data['system_metrics']['cpu']['current']:.1f}%")
        print(f"System Memory: {dashboard_data['system_metrics']['memory']['current']:.1f}%")
        print(f"Active Alerts: {dashboard_data['alerts']['summary']['total_active']}")
        print(f"Health Status: {dashboard_data['health_status']['overall_status']}")
        
    except KeyboardInterrupt:
        logger.info("Shutting down monitoring system...")
    finally:
        monitor.stop()

if __name__ == "__main__":
    main()
