"""
Prometheus Metrics for ScoutPro Services
"""
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry
)
from fastapi import Response
import time
from typing import Optional, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class PrometheusMetrics:
    """
    Prometheus metrics instrumentation for ScoutPro services

    Provides:
    - Request counters
    - Response time histograms
    - Active request gauges
    - Error counters
    - Custom business metrics
    """

    def __init__(self, service_name: str, registry: Optional[CollectorRegistry] = None):
        """
        Initialize Prometheus metrics

        Args:
            service_name: Name of the service (e.g., 'player-service')
            registry: Custom registry (optional)
        """
        self.service_name = service_name
        self.registry = registry or CollectorRegistry()

        # ============ HTTP Metrics ============

        # Total HTTP requests
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['service', 'method', 'endpoint', 'status'],
            registry=self.registry
        )

        # Request duration histogram
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['service', 'method', 'endpoint'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )

        # Active requests gauge
        self.http_requests_in_progress = Gauge(
            'http_requests_in_progress',
            'HTTP requests currently in progress',
            ['service', 'method', 'endpoint'],
            registry=self.registry
        )

        # ============ Error Metrics ============

        # Total errors
        self.errors_total = Counter(
            'errors_total',
            'Total errors',
            ['service', 'type', 'endpoint'],
            registry=self.registry
        )

        # ============ Database Metrics ============

        # Database query duration
        self.db_query_duration_seconds = Histogram(
            'db_query_duration_seconds',
            'Database query duration in seconds',
            ['service', 'operation', 'collection'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
            registry=self.registry
        )

        # Database operations counter
        self.db_operations_total = Counter(
            'db_operations_total',
            'Total database operations',
            ['service', 'operation', 'collection', 'status'],
            registry=self.registry
        )

        # ============ Kafka Metrics ============

        # Kafka messages produced
        self.kafka_messages_produced_total = Counter(
            'kafka_messages_produced_total',
            'Total Kafka messages produced',
            ['service', 'topic'],
            registry=self.registry
        )

        # Kafka messages consumed
        self.kafka_messages_consumed_total = Counter(
            'kafka_messages_consumed_total',
            'Total Kafka messages consumed',
            ['service', 'topic'],
            registry=self.registry
        )

        # Kafka message processing duration
        self.kafka_message_processing_duration_seconds = Histogram(
            'kafka_message_processing_duration_seconds',
            'Kafka message processing duration in seconds',
            ['service', 'topic', 'event_type'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            registry=self.registry
        )

        # ============ Cache Metrics ============

        # Cache hits
        self.cache_hits_total = Counter(
            'cache_hits_total',
            'Total cache hits',
            ['service', 'cache_type'],
            registry=self.registry
        )

        # Cache misses
        self.cache_misses_total = Counter(
            'cache_misses_total',
            'Total cache misses',
            ['service', 'cache_type'],
            registry=self.registry
        )

        # ============ Business Metrics ============

        # Player queries
        self.player_queries_total = Counter(
            'player_queries_total',
            'Total player queries',
            ['service', 'query_type'],
            registry=self.registry
        )

        # Match events processed
        self.match_events_processed_total = Counter(
            'match_events_processed_total',
            'Total match events processed',
            ['service', 'event_type'],
            registry=self.registry
        )

        # Live matches gauge
        self.live_matches_active = Gauge(
            'live_matches_active',
            'Number of active live matches',
            ['service'],
            registry=self.registry
        )

        # WebSocket connections
        self.websocket_connections_active = Gauge(
            'websocket_connections_active',
            'Active WebSocket connections',
            ['service'],
            registry=self.registry
        )

        # ML predictions
        self.ml_predictions_total = Counter(
            'ml_predictions_total',
            'Total ML predictions made',
            ['service', 'model_type'],
            registry=self.registry
        )

        logger.info(f"Prometheus metrics initialized for {service_name}")

    # ============ HTTP Tracking Methods ============

    def track_request(self, method: str, endpoint: str, status_code: int):
        """Track HTTP request"""
        self.http_requests_total.labels(
            service=self.service_name,
            method=method,
            endpoint=endpoint,
            status=status_code
        ).inc()

    def track_request_duration(self, method: str, endpoint: str, duration: float):
        """Track HTTP request duration"""
        self.http_request_duration_seconds.labels(
            service=self.service_name,
            method=method,
            endpoint=endpoint
        ).observe(duration)

    def track_error(self, error_type: str, endpoint: str):
        """Track error"""
        self.errors_total.labels(
            service=self.service_name,
            type=error_type,
            endpoint=endpoint
        ).inc()

    # ============ Database Tracking Methods ============

    def track_db_operation(
        self,
        operation: str,
        collection: str,
        status: str,
        duration: Optional[float] = None
    ):
        """Track database operation"""
        self.db_operations_total.labels(
            service=self.service_name,
            operation=operation,
            collection=collection,
            status=status
        ).inc()

        if duration is not None:
            self.db_query_duration_seconds.labels(
                service=self.service_name,
                operation=operation,
                collection=collection
            ).observe(duration)

    # ============ Kafka Tracking Methods ============

    def track_kafka_produce(self, topic: str):
        """Track Kafka message produced"""
        self.kafka_messages_produced_total.labels(
            service=self.service_name,
            topic=topic
        ).inc()

    def track_kafka_consume(self, topic: str):
        """Track Kafka message consumed"""
        self.kafka_messages_consumed_total.labels(
            service=self.service_name,
            topic=topic
        ).inc()

    def track_kafka_processing(self, topic: str, event_type: str, duration: float):
        """Track Kafka message processing duration"""
        self.kafka_message_processing_duration_seconds.labels(
            service=self.service_name,
            topic=topic,
            event_type=event_type
        ).observe(duration)

    # ============ Cache Tracking Methods ============

    def track_cache_hit(self, cache_type: str = "redis"):
        """Track cache hit"""
        self.cache_hits_total.labels(
            service=self.service_name,
            cache_type=cache_type
        ).inc()

    def track_cache_miss(self, cache_type: str = "redis"):
        """Track cache miss"""
        self.cache_misses_total.labels(
            service=self.service_name,
            cache_type=cache_type
        ).inc()

    # ============ Business Metrics Methods ============

    def track_player_query(self, query_type: str):
        """Track player query"""
        self.player_queries_total.labels(
            service=self.service_name,
            query_type=query_type
        ).inc()

    def track_match_event(self, event_type: str):
        """Track match event processed"""
        self.match_events_processed_total.labels(
            service=self.service_name,
            event_type=event_type
        ).inc()

    def set_live_matches(self, count: int):
        """Set number of live matches"""
        self.live_matches_active.labels(
            service=self.service_name
        ).set(count)

    def set_websocket_connections(self, count: int):
        """Set number of active WebSocket connections"""
        self.websocket_connections_active.labels(
            service=self.service_name
        ).set(count)

    def track_ml_prediction(self, model_type: str):
        """Track ML prediction"""
        self.ml_predictions_total.labels(
            service=self.service_name,
            model_type=model_type
        ).inc()

    # ============ Decorators ============

    def track_time(self, operation: str):
        """
        Decorator to track execution time

        Usage:
            @metrics.track_time('process_player_data')
            async def process_player_data(player_id):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    logger.debug(f"{operation} took {duration:.3f}s")

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    logger.debug(f"{operation} took {duration:.3f}s")

            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def generate_metrics(self) -> bytes:
        """Generate Prometheus metrics in text format"""
        return generate_latest(self.registry)


# Global metrics instance
_metrics: Optional[PrometheusMetrics] = None


def get_metrics(service_name: str) -> PrometheusMetrics:
    """
    Get global metrics instance

    Args:
        service_name: Name of the service

    Returns:
        PrometheusMetrics instance
    """
    global _metrics
    if _metrics is None:
        _metrics = PrometheusMetrics(service_name)
    return _metrics


def setup_metrics_endpoint(app, service_name: str):
    """
    Setup /metrics endpoint for Prometheus scraping

    Args:
        app: FastAPI application
        service_name: Name of the service

    Usage:
        from fastapi import FastAPI
        from shared.monitoring import setup_metrics_endpoint

        app = FastAPI()
        setup_metrics_endpoint(app, 'player-service')
    """
    metrics = get_metrics(service_name)

    @app.get("/metrics")
    async def prometheus_metrics():
        """Prometheus metrics endpoint"""
        return Response(
            content=metrics.generate_metrics(),
            media_type=CONTENT_TYPE_LATEST
        )

    logger.info(f"Metrics endpoint configured at /metrics for {service_name}")
