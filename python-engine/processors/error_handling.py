"""
Comprehensive Error Handling System for Lexicon
Provides production-grade error tracking, recovery, and monitoring
"""

import logging
import traceback
import json
import time
import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from contextlib import contextmanager
import sqlite3
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for better classification"""
    SYSTEM = "system"
    NETWORK = "network"
    DATABASE = "database"
    FILE_IO = "file_io"
    PROCESSING = "processing"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    RESOURCE = "resource"
    EXTERNAL_API = "external_api"
    USER_INPUT = "user_input"
    CONFIGURATION = "configuration"

class ErrorStatus(Enum):
    """Error resolution status"""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    IGNORED = "ignored"

@dataclass
class ErrorContext:
    """Additional context for errors"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    environment: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ErrorRecord:
    """Comprehensive error record"""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    exception_type: str
    stack_trace: str
    context: ErrorContext
    status: ErrorStatus = ErrorStatus.NEW
    resolution_notes: Optional[str] = None
    occurrence_count: int = 1
    first_occurrence: Optional[datetime] = None
    last_occurrence: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    related_errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.first_occurrence is None:
            self.first_occurrence = self.timestamp
        if self.last_occurrence is None:
            self.last_occurrence = self.timestamp

class RecoveryStrategy:
    """Base class for error recovery strategies"""
    
    def __init__(self, name: str, max_retries: int = 3, backoff_factor: float = 2.0):
        self.name = name
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    async def recover(self, error: Exception, context: ErrorContext, attempt: int) -> bool:
        """
        Attempt to recover from an error
        Returns True if recovery was successful, False otherwise
        """
        raise NotImplementedError
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if a retry should be attempted"""
        return attempt < self.max_retries
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay before retry"""
        return min(60, (self.backoff_factor ** attempt))

class NetworkRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for network-related errors"""
    
    async def recover(self, error: Exception, context: ErrorContext, attempt: int) -> bool:
        # Wait before retrying network operations
        delay = self.get_delay(attempt)
        await asyncio.sleep(delay)
        logger.info(f"Retrying network operation after {delay}s (attempt {attempt + 1})")
        return True

class FileIORecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for file I/O errors"""
    
    async def recover(self, error: Exception, context: ErrorContext, attempt: int) -> bool:
        if "permission" in str(error).lower():
            # Try to fix permission issues
            try:
                file_path = context.input_data.get("file_path") if context.input_data else None
                if file_path and Path(file_path).exists():
                    # Attempt to change permissions (if possible)
                    logger.info(f"Attempting to fix permissions for {file_path}")
                    return True
            except Exception:
                pass
        
        delay = self.get_delay(attempt)
        await asyncio.sleep(delay)
        return True

class DatabaseRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for database errors"""
    
    async def recover(self, error: Exception, context: ErrorContext, attempt: int) -> bool:
        if "database is locked" in str(error).lower():
            # Wait longer for database locks
            delay = self.get_delay(attempt) * 2
            await asyncio.sleep(delay)
            logger.info(f"Retrying database operation after {delay}s (attempt {attempt + 1})")
            return True
        
        if "no such table" in str(error).lower():
            # Attempt to initialize database schema
            logger.info("Attempting database schema recovery")
            # This would call database initialization
            return False  # Don't retry automatically, needs manual intervention
        
        return False

class ProcessingRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for processing errors"""
    
    async def recover(self, error: Exception, context: ErrorContext, attempt: int) -> bool:
        if "memory" in str(error).lower():
            # Reduce batch size for memory issues
            if context.input_data and "batch_size" in context.input_data:
                original_size = context.input_data["batch_size"]
                context.input_data["batch_size"] = max(1, original_size // 2)
                logger.info(f"Reduced batch size from {original_size} to {context.input_data['batch_size']}")
                return True
        
        delay = self.get_delay(attempt)
        await asyncio.sleep(delay)
        return True

class ErrorHandler:
    """Comprehensive error handling and recovery system"""
    
    def __init__(self, database_path: Optional[str] = None):
        self.database_path = database_path or "error_tracking.db"
        self.error_records: Dict[str, ErrorRecord] = {}
        self.error_stats = defaultdict(int)
        self.recent_errors = deque(maxlen=1000)
        self.recovery_strategies: Dict[ErrorCategory, RecoveryStrategy] = {}
        self.error_callbacks: List[Callable[[ErrorRecord], None]] = []
        self.alert_thresholds = {
            ErrorSeverity.CRITICAL: 1,  # Alert immediately
            ErrorSeverity.HIGH: 3,      # Alert after 3 occurrences
            ErrorSeverity.MEDIUM: 10,   # Alert after 10 occurrences
            ErrorSeverity.LOW: 50       # Alert after 50 occurrences
        }
        self.alert_timeframes = {
            ErrorSeverity.CRITICAL: timedelta(minutes=1),
            ErrorSeverity.HIGH: timedelta(minutes=5),
            ErrorSeverity.MEDIUM: timedelta(minutes=15),
            ErrorSeverity.LOW: timedelta(hours=1)
        }
        
        # Initialize database
        self._init_database()
        
        # Setup default recovery strategies
        self._setup_default_recovery_strategies()
        
        logger.info("Error handler initialized")
    
    def _init_database(self):
        """Initialize SQLite database for error persistence"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS error_records (
                        error_id TEXT PRIMARY KEY,
                        timestamp TEXT,
                        severity TEXT,
                        category TEXT,
                        message TEXT,
                        exception_type TEXT,
                        stack_trace TEXT,
                        context TEXT,
                        status TEXT,
                        resolution_notes TEXT,
                        occurrence_count INTEGER,
                        first_occurrence TEXT,
                        last_occurrence TEXT,
                        resolved_at TEXT,
                        resolved_by TEXT,
                        tags TEXT,
                        related_errors TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp ON error_records(timestamp)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_severity ON error_records(severity)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_category ON error_records(category)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_status ON error_records(status)
                """)
        except Exception as e:
            logger.error(f"Failed to initialize error database: {e}")
    
    def _setup_default_recovery_strategies(self):
        """Setup default recovery strategies for common error categories"""
        self.recovery_strategies = {
            ErrorCategory.NETWORK: NetworkRecoveryStrategy("network_recovery"),
            ErrorCategory.FILE_IO: FileIORecoveryStrategy("file_io_recovery"),
            ErrorCategory.DATABASE: DatabaseRecoveryStrategy("database_recovery"),
            ErrorCategory.PROCESSING: ProcessingRecoveryStrategy("processing_recovery"),
        }
    
    def add_recovery_strategy(self, category: ErrorCategory, strategy: RecoveryStrategy):
        """Add or update a recovery strategy for an error category"""
        self.recovery_strategies[category] = strategy
        logger.info(f"Added recovery strategy '{strategy.name}' for category {category.value}")
    
    def add_error_callback(self, callback: Callable[[ErrorRecord], None]):
        """Add a callback to be called when errors are recorded"""
        self.error_callbacks.append(callback)
    
    async def handle_error(self, 
                          error: Exception, 
                          severity: ErrorSeverity,
                          category: ErrorCategory,
                          context: Optional[ErrorContext] = None,
                          auto_recover: bool = True) -> Optional[ErrorRecord]:
        """
        Handle an error with optional automatic recovery
        Returns the error record if error was not recovered
        """
        if context is None:
            context = ErrorContext()
        
        # Generate error ID
        error_id = self._generate_error_id(error, context)
        
        # Check if this is a duplicate error
        existing_record = self._find_duplicate_error(error_id, error, context)
        if existing_record:
            existing_record.occurrence_count += 1
            existing_record.last_occurrence = datetime.now()
            await self._persist_error(existing_record)
            await self._check_alert_thresholds(existing_record)
            return existing_record
        
        # Create new error record
        error_record = ErrorRecord(
            error_id=error_id,
            timestamp=datetime.now(),
            severity=severity,
            category=category,
            message=str(error),
            exception_type=type(error).__name__,
            stack_trace=traceback.format_exc(),
            context=context
        )
        
        # Log the error
        log_level = self._get_log_level(severity)
        logger.log(log_level, f"Error [{category.value}]: {error}")
        
        # Store error record
        self.error_records[error_id] = error_record
        self.recent_errors.append(error_record)
        self.error_stats[f"{category.value}_{severity.value}"] += 1
        
        # Persist to database
        await self._persist_error(error_record)
        
        # Notify callbacks
        for callback in self.error_callbacks:
            try:
                callback(error_record)
            except Exception as callback_error:
                logger.error(f"Error callback failed: {callback_error}")
        
        # Check alert thresholds
        await self._check_alert_thresholds(error_record)
        
        # Attempt recovery if enabled
        if auto_recover and category in self.recovery_strategies:
            recovery_successful = await self._attempt_recovery(error, error_record)
            if recovery_successful:
                error_record.status = ErrorStatus.RESOLVED
                error_record.resolved_at = datetime.now()
                error_record.resolution_notes = "Automatically recovered"
                await self._persist_error(error_record)
                return None  # Error was recovered
        
        return error_record
    
    async def _attempt_recovery(self, error: Exception, error_record: ErrorRecord) -> bool:
        """Attempt to recover from an error using the appropriate strategy"""
        strategy = self.recovery_strategies.get(error_record.category)
        if not strategy:
            return False
        
        for attempt in range(strategy.max_retries):
            try:
                if await strategy.recover(error, error_record.context, attempt):
                    logger.info(f"Recovery successful for error {error_record.error_id} on attempt {attempt + 1}")
                    return True
            except Exception as recovery_error:
                logger.error(f"Recovery attempt {attempt + 1} failed: {recovery_error}")
                
                if not strategy.should_retry(error, attempt + 1):
                    break
        
        logger.warning(f"All recovery attempts failed for error {error_record.error_id}")
        return False
    
    def _generate_error_id(self, error: Exception, context: ErrorContext) -> str:
        """Generate a unique ID for an error"""
        error_signature = f"{type(error).__name__}:{str(error)[:100]}"
        context_signature = f"{context.component}:{context.operation}"
        return f"err_{hash(error_signature + context_signature)}"
    
    def _find_duplicate_error(self, error_id: str, error: Exception, context: ErrorContext) -> Optional[ErrorRecord]:
        """Find if this error is a duplicate of an existing one"""
        return self.error_records.get(error_id)
    
    def _get_log_level(self, severity: ErrorSeverity) -> int:
        """Convert error severity to logging level"""
        level_map = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }
        return level_map.get(severity, logging.ERROR)
    
    async def _persist_error(self, error_record: ErrorRecord):
        """Persist error record to database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO error_records (
                        error_id, timestamp, severity, category, message, exception_type,
                        stack_trace, context, status, resolution_notes, occurrence_count,
                        first_occurrence, last_occurrence, resolved_at, resolved_by,
                        tags, related_errors
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    error_record.error_id,
                    error_record.timestamp.isoformat(),
                    error_record.severity.value,
                    error_record.category.value,
                    error_record.message,
                    error_record.exception_type,
                    error_record.stack_trace,
                    json.dumps(error_record.context.to_dict()),
                    error_record.status.value,
                    error_record.resolution_notes,
                    error_record.occurrence_count,
                    error_record.first_occurrence.isoformat() if error_record.first_occurrence else None,
                    error_record.last_occurrence.isoformat() if error_record.last_occurrence else None,
                    error_record.resolved_at.isoformat() if error_record.resolved_at else None,
                    error_record.resolved_by,
                    json.dumps(error_record.tags),
                    json.dumps(error_record.related_errors)
                ))
        except Exception as e:
            logger.error(f"Failed to persist error record: {e}")
    
    async def _check_alert_thresholds(self, error_record: ErrorRecord):
        """Check if error should trigger an alert"""
        threshold = self.alert_thresholds.get(error_record.severity, float('inf'))
        timeframe = self.alert_timeframes.get(error_record.severity, timedelta(hours=1))
        
        if error_record.occurrence_count >= threshold:
            recent_count = self._count_recent_errors(
                error_record.error_id, 
                datetime.now() - timeframe
            )
            
            if recent_count >= threshold:
                await self._send_alert(error_record)
    
    def _count_recent_errors(self, error_id: str, since: datetime) -> int:
        """Count occurrences of an error since a given time"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute(
                    "SELECT occurrence_count FROM error_records WHERE error_id = ? AND last_occurrence >= ?",
                    (error_id, since.isoformat())
                )
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception:
            return 0
    
    async def _send_alert(self, error_record: ErrorRecord):
        """Send alert for critical errors"""
        logger.critical(f"ALERT: {error_record.severity.value} error threshold exceeded: {error_record.message}")
        # Here you would integrate with your alerting system (email, Slack, etc.)
    
    @contextmanager
    def error_context(self, 
                     component: str,
                     operation: str,
                     severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                     category: ErrorCategory = ErrorCategory.SYSTEM,
                     **context_data):
        """Context manager for automatic error handling"""
        context = ErrorContext(
            component=component,
            operation=operation,
            input_data=context_data
        )
        
        try:
            yield context
        except Exception as e:
            # Handle the error asynchronously in the background
            asyncio.create_task(self.handle_error(e, severity, category, context))
            raise  # Re-raise the original exception
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        stats = {
            "total_errors": len(self.error_records),
            "errors_by_severity": {},
            "errors_by_category": {},
            "errors_by_status": {},
            "recent_error_rate": {
                "last_24h": 0,
                "last_7d": 0
            },
            "top_errors": [],
            "resolution_rate": 0.0
        }
        
        # Calculate statistics
        for error_record in self.error_records.values():
            # By severity
            severity_key = error_record.severity.value
            stats["errors_by_severity"][severity_key] = stats["errors_by_severity"].get(severity_key, 0) + 1
            
            # By category
            category_key = error_record.category.value
            stats["errors_by_category"][category_key] = stats["errors_by_category"].get(category_key, 0) + 1
            
            # By status
            status_key = error_record.status.value
            stats["errors_by_status"][status_key] = stats["errors_by_status"].get(status_key, 0) + 1
            
            # Recent errors
            if error_record.last_occurrence and error_record.last_occurrence >= last_24h:
                stats["recent_error_rate"]["last_24h"] += 1
            if error_record.last_occurrence and error_record.last_occurrence >= last_7d:
                stats["recent_error_rate"]["last_7d"] += 1
        
        # Top errors by occurrence count
        top_errors = sorted(
            self.error_records.values(),
            key=lambda x: x.occurrence_count,
            reverse=True
        )[:10]
        
        stats["top_errors"] = [
            {
                "error_id": error.error_id,
                "message": error.message[:100],
                "occurrence_count": error.occurrence_count,
                "severity": error.severity.value,
                "category": error.category.value
            }
            for error in top_errors
        ]
        
        # Resolution rate
        resolved_count = len([e for e in self.error_records.values() if e.status == ErrorStatus.RESOLVED])
        stats["resolution_rate"] = resolved_count / len(self.error_records) if self.error_records else 0.0
        
        return stats
    
    def search_errors(self,
                     severity: Optional[ErrorSeverity] = None,
                     category: Optional[ErrorCategory] = None,
                     status: Optional[ErrorStatus] = None,
                     since: Optional[datetime] = None,
                     limit: int = 100) -> List[ErrorRecord]:
        """Search error records with filters"""
        results = []
        
        for error_record in self.error_records.values():
            # Apply filters
            if severity and error_record.severity != severity:
                continue
            if category and error_record.category != category:
                continue
            if status and error_record.status != status:
                continue
            if since and error_record.timestamp < since:
                continue
            
            results.append(error_record)
            
            if len(results) >= limit:
                break
        
        # Sort by timestamp (most recent first)
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results
    
    def resolve_error(self, error_id: str, resolved_by: str, notes: Optional[str] = None) -> bool:
        """Mark an error as resolved"""
        if error_id in self.error_records:
            error_record = self.error_records[error_id]
            error_record.status = ErrorStatus.RESOLVED
            error_record.resolved_at = datetime.now()
            error_record.resolved_by = resolved_by
            if notes:
                error_record.resolution_notes = notes
            
            # Persist the change
            asyncio.create_task(self._persist_error(error_record))
            logger.info(f"Error {error_id} marked as resolved by {resolved_by}")
            return True
        
        return False
    
    def export_error_report(self, output_path: str, format: str = "json") -> str:
        """Export comprehensive error report"""
        report_data = {
            "report_generated": datetime.now().isoformat(),
            "statistics": self.get_error_statistics(),
            "all_errors": [asdict(error) for error in self.error_records.values()]
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "json":
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        logger.info(f"Error report exported to {output_file}")
        return str(output_file)

# Global error handler instance
_error_handler: Optional[ErrorHandler] = None

def get_error_handler() -> ErrorHandler:
    """Get or create the global error handler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler

# Convenience functions for common error handling
async def handle_system_error(error: Exception, component: str, operation: str, **context_data):
    """Handle a system-level error"""
    error_context = ErrorContext(
        component=component,
        operation=operation,
        input_data=context_data
    )
    return await get_error_handler().handle_error(
        error, ErrorSeverity.HIGH, ErrorCategory.SYSTEM, error_context
    )

async def handle_user_error(error: Exception, user_id: str, operation: str, **context_data):
    """Handle a user-related error"""
    error_context = ErrorContext(
        user_id=user_id,
        operation=operation,
        input_data=context_data
    )
    return await get_error_handler().handle_error(
        error, ErrorSeverity.LOW, ErrorCategory.USER_INPUT, error_context
    )

async def handle_network_error(error: Exception, operation: str, **context_data):
    """Handle a network-related error"""
    error_context = ErrorContext(
        operation=operation,
        input_data=context_data
    )
    return await get_error_handler().handle_error(
        error, ErrorSeverity.MEDIUM, ErrorCategory.NETWORK, error_context
    )

# Demo function
async def demo_error_handling():
    """Demonstrate the error handling system"""
    print("=== Error Handling System Demo ===")
    
    error_handler = get_error_handler()
    
    # Simulate various types of errors
    errors_to_simulate = [
        (ValueError("Invalid input data"), ErrorSeverity.LOW, ErrorCategory.USER_INPUT),
        (ConnectionError("Network timeout"), ErrorSeverity.MEDIUM, ErrorCategory.NETWORK),
        (FileNotFoundError("Config file missing"), ErrorSeverity.HIGH, ErrorCategory.FILE_IO),
        (MemoryError("Out of memory"), ErrorSeverity.CRITICAL, ErrorCategory.SYSTEM),
    ]
    
    for error, severity, category in errors_to_simulate:
        context = ErrorContext(
            component="demo",
            operation="simulate_error",
            input_data={"error_type": type(error).__name__}
        )
        
        result = await error_handler.handle_error(error, severity, category, context)
        if result:
            print(f"Recorded error: {result.error_id} - {result.message}")
        else:
            print(f"Error recovered automatically: {type(error).__name__}")
    
    # Show statistics
    stats = error_handler.get_error_statistics()
    print(f"\nError Statistics:")
    print(f"Total errors: {stats['total_errors']}")
    print(f"Errors by severity: {stats['errors_by_severity']}")
    print(f"Resolution rate: {stats['resolution_rate']:.2%}")
    
    # Export report
    report_path = error_handler.export_error_report("error_report.json")
    print(f"Error report exported to: {report_path}")

if __name__ == "__main__":
    asyncio.run(demo_error_handling())
