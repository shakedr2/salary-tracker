# -*- coding: utf-8 -*-
"""
Observability module - Metrics, structured logging, and monitoring.

Provides:
- Structured logging for CloudWatch
- Performance metrics
- Health metrics
- Error tracking
"""
import json
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from functools import wraps
from contextlib import contextmanager

# Structured logger for CloudWatch
class CloudWatchStructuredLogger:
    """Structured logger that outputs JSON for CloudWatch Logs."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(handler)
    
    def _log(self, level: str, message: str, **kwargs: Any) -> None:
        """Log with structured data."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        getattr(self.logger, level.lower())(json.dumps(log_data, ensure_ascii=False))
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log("INFO", message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._log("ERROR", message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log("WARNING", message, **kwargs)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log("DEBUG", message, **kwargs)


class StructuredFormatter(logging.Formatter):
    """Formatter that outputs structured JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        # If already JSON, return as-is
        if isinstance(record.msg, dict) or (isinstance(record.msg, str) and record.msg.startswith('{')):
            return record.msg
        
        # Otherwise create structured log
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


# Metrics collector
class MetricsCollector:
    """Collects and stores application metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "scraping": {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "avg_duration_seconds": 0.0,
                "total_records_scraped": 0,
            },
            "calculations": {
                "total_calculations": 0,
                "total_days_processed": 0,
                "total_salary_calculated": 0.0,
            },
            "api": {
                "total_requests": 0,
                "health_checks": 0,
                "salary_requests": 0,
                "refresh_requests": 0,
                "errors": 0,
            },
            "health": {
                "status": "healthy",
                "last_check": None,
                "uptime_seconds": 0,
            }
        }
        self.start_time = time.time()
    
    def record_scraping(self, duration: float, records_count: int, success: bool) -> None:
        """Record scraping metrics."""
        self.metrics["scraping"]["total_runs"] += 1
        if success:
            self.metrics["scraping"]["successful_runs"] += 1
            self.metrics["scraping"]["total_records_scraped"] += records_count
        else:
            self.metrics["scraping"]["failed_runs"] += 1
        
        # Update average duration
        total = self.metrics["scraping"]["total_runs"]
        current_avg = self.metrics["scraping"]["avg_duration_seconds"]
        self.metrics["scraping"]["avg_duration_seconds"] = (
            (current_avg * (total - 1) + duration) / total
        )
    
    def record_calculation(self, days_count: int, total_salary: float) -> None:
        """Record calculation metrics."""
        self.metrics["calculations"]["total_calculations"] += 1
        self.metrics["calculations"]["total_days_processed"] += days_count
        self.metrics["calculations"]["total_salary_calculated"] += total_salary
    
    def record_api_request(self, endpoint: str, success: bool = True) -> None:
        """Record API request."""
        self.metrics["api"]["total_requests"] += 1
        if not success:
            self.metrics["api"]["errors"] += 1
        
        if endpoint == "/api/health":
            self.metrics["api"]["health_checks"] += 1
        elif endpoint == "/api/salary":
            self.metrics["api"]["salary_requests"] += 1
        elif endpoint == "/api/refresh":
            self.metrics["api"]["refresh_requests"] += 1
    
    def update_health(self, status: str = "healthy") -> None:
        """Update health status."""
        self.metrics["health"]["status"] = status
        self.metrics["health"]["last_check"] = datetime.utcnow().isoformat()
        self.metrics["health"]["uptime_seconds"] = time.time() - self.start_time
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        self.update_health()
        return self.metrics.copy()


# Global metrics instance
_metrics = MetricsCollector()


def get_metrics() -> MetricsCollector:
    """Get global metrics collector."""
    return _metrics


# Performance monitoring decorator
def monitor_performance(operation_name: str):
    """Decorator to monitor function performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger = CloudWatchStructuredLogger(func.__module__)
            
            try:
                logger.info(
                    f"Starting {operation_name}",
                    operation=operation_name,
                    function=func.__name__
                )
                
                result = func(*args, **kwargs)
                
                duration = time.time() - start_time
                logger.info(
                    f"Completed {operation_name}",
                    operation=operation_name,
                    function=func.__name__,
                    duration_seconds=round(duration, 3),
                    success=True
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Failed {operation_name}",
                    operation=operation_name,
                    function=func.__name__,
                    duration_seconds=round(duration, 3),
                    success=False,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
        
        return wrapper
    return decorator


# Context manager for timing operations
@contextmanager
def time_operation(operation_name: str, logger: Optional[CloudWatchStructuredLogger] = None):
    """Context manager to time an operation."""
    if logger is None:
        logger = CloudWatchStructuredLogger("observability")
    
    start_time = time.time()
    logger.info(f"Starting {operation_name}", operation=operation_name)
    
    try:
        yield
        duration = time.time() - start_time
        logger.info(
            f"Completed {operation_name}",
            operation=operation_name,
            duration_seconds=round(duration, 3),
            success=True
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Failed {operation_name}",
            operation=operation_name,
            duration_seconds=round(duration, 3),
            success=False,
            error=str(e),
            error_type=type(e).__name__
        )
        raise


def get_structured_logger(name: str) -> CloudWatchStructuredLogger:
    """Get a structured logger instance."""
    return CloudWatchStructuredLogger(name)

