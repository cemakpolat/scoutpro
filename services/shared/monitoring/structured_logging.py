"""
Structured Logging Configuration for ScoutPro Services
JSON-formatted logs for easy parsing by ELK stack
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
import traceback


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging

    Outputs logs in JSON format with:
    - timestamp
    - service name
    - log level
    - message
    - context (extra fields)
    - exception info (if present)
    """

    def __init__(self, service_name: str):
        """
        Initialize JSON formatter

        Args:
            service_name: Name of the service
        """
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'service': self.service_name,
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add thread/process info
        if record.process:
            log_data['process_id'] = record.process
        if record.thread:
            log_data['thread_id'] = record.thread

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'stacktrace': self.formatException(record.exc_info)
            }

        # Add extra fields from record
        # Filter out standard fields to get only custom fields
        standard_fields = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'message', 'pathname', 'process', 'processName',
            'relativeCreated', 'thread', 'threadName', 'exc_info',
            'exc_text', 'stack_info', 'taskName'
        }

        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in standard_fields
        }

        if extra_fields:
            log_data['context'] = extra_fields

        return json.dumps(log_data)


class StructuredLogger:
    """
    Structured logger wrapper for easy context management

    Usage:
        logger = StructuredLogger('player-service')
        logger.info('Player created', player_id='123', team='Arsenal')
        logger.error('Database error', error_type='connection', retry_count=3)
    """

    def __init__(self, service_name: str, logger_name: str = None):
        """
        Initialize structured logger

        Args:
            service_name: Name of the service
            logger_name: Name of the logger (default: service_name)
        """
        self.service_name = service_name
        self.logger = logging.getLogger(logger_name or service_name)

    def _log(self, level: int, message: str, **context):
        """Internal log method with context"""
        self.logger.log(level, message, extra=context)

    def debug(self, message: str, **context):
        """Log debug message with context"""
        self._log(logging.DEBUG, message, **context)

    def info(self, message: str, **context):
        """Log info message with context"""
        self._log(logging.INFO, message, **context)

    def warning(self, message: str, **context):
        """Log warning message with context"""
        self._log(logging.WARNING, message, **context)

    def error(self, message: str, exc_info: bool = False, **context):
        """Log error message with context"""
        self._log(logging.ERROR, message, **context)
        if exc_info:
            self.logger.exception(message, extra=context)

    def critical(self, message: str, exc_info: bool = False, **context):
        """Log critical message with context"""
        self._log(logging.CRITICAL, message, **context)
        if exc_info:
            self.logger.exception(message, extra=context)

    def exception(self, message: str, **context):
        """Log exception with traceback"""
        context['exception_traceback'] = traceback.format_exc()
        self._log(logging.ERROR, message, **context)


def setup_structured_logging(
    service_name: str,
    log_level: str = 'INFO',
    json_output: bool = True
) -> StructuredLogger:
    """
    Setup structured logging for a service

    Args:
        service_name: Name of the service
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: Output logs in JSON format (default: True)

    Returns:
        StructuredLogger instance

    Usage:
        from shared.monitoring import setup_structured_logging

        logger = setup_structured_logging('player-service', 'DEBUG')
        logger.info('Service started', version='2.0.0')
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    # Set formatter
    if json_output:
        formatter = JSONFormatter(service_name)
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Create structured logger
    structured_logger = StructuredLogger(service_name)

    # Log initialization
    structured_logger.info(
        'Structured logging initialized',
        log_level=log_level,
        json_output=json_output
    )

    return structured_logger


class RequestLogger:
    """
    Middleware-friendly request logger

    Usage in FastAPI:
        from fastapi import Request
        from shared.monitoring import RequestLogger

        request_logger = RequestLogger('player-service')

        @app.middleware("http")
        async def log_requests(request: Request, call_next):
            return await request_logger.log_request(request, call_next)
    """

    def __init__(self, service_name: str):
        """
        Initialize request logger

        Args:
            service_name: Name of the service
        """
        self.logger = StructuredLogger(service_name, f"{service_name}.requests")

    async def log_request(self, request, call_next):
        """
        Log HTTP request and response

        Args:
            request: FastAPI Request object
            call_next: Next middleware in chain

        Returns:
            Response
        """
        import time

        # Log request
        start_time = time.time()
        self.logger.info(
            'HTTP request received',
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent')
        )

        # Process request
        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log response
            self.logger.info(
                'HTTP request completed',
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2)
            )

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Log error
            self.logger.error(
                'HTTP request failed',
                method=request.method,
                path=request.url.path,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=round(duration * 1000, 2),
                exc_info=True
            )
            raise


def get_logger(service_name: str, logger_name: Optional[str] = None) -> StructuredLogger:
    """
    Get a structured logger instance

    Args:
        service_name: Name of the service
        logger_name: Name of the logger (optional)

    Returns:
        StructuredLogger instance

    Usage:
        from shared.monitoring import get_logger

        logger = get_logger('player-service', 'api.players')
        logger.info('Player created', player_id='123')
    """
    return StructuredLogger(service_name, logger_name)
