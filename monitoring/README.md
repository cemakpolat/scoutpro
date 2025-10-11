# Monitoring & Observability

Configuration files for monitoring, logging, and observability stack.

## Components

- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Elasticsearch**: Log aggregation
- **Jaeger**: Distributed tracing
- **Alertmanager**: Alert routing

## Directory Structure

```
monitoring/
├── prometheus/
│   ├── prometheus.yml         # Prometheus config
│   └── rules/                 # Alert rules
├── grafana/
│   ├── dashboards/           # Dashboard JSON files
│   └── datasources/          # Data source configs
├── alerts/
│   ├── service-alerts.yml    # Service-level alerts
│   └── infrastructure-alerts.yml
└── elasticsearch/
    └── index-templates/       # ES index templates
```

## Quick Start

### Prometheus

```bash
# Start Prometheus
docker run -d \
  -p 9090:9090 \
  -v $(pwd)/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

### Grafana

```bash
# Start Grafana
docker run -d \
  -p 3000:3000 \
  -v $(pwd)/grafana:/etc/grafana/provisioning \
  grafana/grafana
```

## Access Points

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Alertmanager**: http://localhost:9093

## Dashboards

Pre-configured Grafana dashboards:
1. **Service Overview** - All microservices health
2. **Infrastructure** - CPU, Memory, Disk
3. **Kafka Metrics** - Topics, lag, throughput
4. **Database Performance** - Query times, connections
5. **Business Metrics** - API calls, users, predictions

## Alerts

Key alerts configured:
- Service down
- High error rate (>5%)
- High latency (p95 > 1s)
- High CPU usage (>80%)
- Kafka consumer lag
- Database connection pool exhausted

## Custom Metrics

Add custom metrics to your service:

```python
from prometheus_client import Counter, Histogram

# Define metrics
api_requests = Counter(
    'api_requests_total',
    'Total API requests',
    ['service', 'method', 'endpoint', 'status']
)

request_duration = Histogram(
    'api_request_duration_seconds',
    'Request duration',
    ['service', 'method', 'endpoint']
)

# Use metrics
api_requests.labels(
    service='player-service',
    method='GET',
    endpoint='/players',
    status='200'
).inc()
```

## Log Aggregation

Logs are sent to Elasticsearch via Logstash:

```
Service → Logstash → Elasticsearch → Kibana
```

Query logs in Kibana:
- **URL**: http://localhost:5601
- **Index pattern**: `logs-*`
- **Query**: `service:player-service AND level:ERROR`
