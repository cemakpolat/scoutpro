# ScoutPro Microservices

This directory contains all backend microservices for the ScoutPro platform.

## Architecture

The backend follows a microservices architecture with the following services:

### Core Data Services

1. **Player Service** (Port 8001)
   - Player data management
   - Player search and filtering
   - Player statistics
   - Repository pattern with MongoDB

2. **Team Service** (Port 8002)
   - Team data management
   - Team search and filtering
   - Team squad information
   - Repository pattern with MongoDB

3. **Match Service** (Port 8003)
   - Match data management
   - Live match updates
   - Match events and statistics
   - Supports real-time data streaming

4. **Statistics Service** (Port 8004)
   - Statistical analysis
   - Player/team rankings
   - Player comparisons
   - Aggregated statistics over time

### Advanced Services

5. **ML Service** (Port 8005)
   - Machine learning predictions
   - Player performance prediction
   - Match outcome prediction
   - Player similarity analysis
   - Integration with MLflow

6. **Live Ingestion Service** (Port 8006)
   - Real-time data ingestion from Opta API
   - Stream processing
   - Kafka event publishing
   - Live match data polling

7. **Search Service** (Port 8007)
   - Full-text search with Elasticsearch
   - Multi-entity search (players, teams, matches)
   - Fuzzy matching
   - Search indexing

8. **Notification Service** (Port 8008)
   - Email notifications
   - In-app notifications
   - Bulk notification support
   - SMTP integration

9. **WebSocket Server** (Port 8080)
   - Real-time WebSocket connections
   - Topic-based subscriptions
   - Live match updates broadcast
   - Connection management

## Technology Stack

### Core Technologies
- **Framework**: FastAPI (Python 3.11)
- **API Documentation**: OpenAPI/Swagger
- **Async Runtime**: asyncio/uvicorn

### Databases
- **MongoDB**: Primary data store
- **PostgreSQL/TimescaleDB**: Time-series data
- **Redis**: Caching layer
- **Elasticsearch**: Search engine

### Messaging & Streaming
- **Apache Kafka**: Event streaming
- **WebSocket**: Real-time communication

### ML & Analytics
- **MLflow**: ML model management
- **Scikit-learn**: ML algorithms
- **XGBoost**: Gradient boosting
- **Pandas/Numpy**: Data processing

### Monitoring
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **Jaeger**: Distributed tracing
- **ELK Stack**: Logging

## Shared Libraries

All services share common code through the `shared/` directory:

- **models/base.py**: Pydantic models for domain entities
- **utils/logger.py**: Structured JSON logging
- **utils/database.py**: Database connection management

## Running Services

### Docker Compose (Local Development)

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d player-service

# View logs
docker-compose logs -f player-service

# Stop all services
docker-compose down
```

### Individual Service

```bash
# Navigate to service directory
cd services/player-service

# Install dependencies
pip install -r requirements.txt

# Run service
uvicorn main:app --reload --port 8001
```

## Service Structure

Each service follows a consistent structure:

```
service-name/
├── config/
│   ├── __init__.py
│   └── settings.py          # Pydantic settings
├── repository/              # Data access layer (if applicable)
│   ├── __init__.py
│   ├── interfaces.py        # Repository interfaces
│   └── mongo_repository.py  # MongoDB implementation
├── services/                # Business logic layer
│   ├── __init__.py
│   └── service_name.py
├── api/                     # API endpoints
│   ├── __init__.py
│   └── routes.py
├── dependencies.py          # FastAPI dependencies
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
└── Dockerfile              # Container definition
```

## API Endpoints

Each service exposes:

- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

Service-specific endpoints are documented in each service's Swagger UI.

## Environment Variables

Common environment variables for all services:

```bash
# Service
SERVICE_NAME=player-service
DEBUG=false
LOG_LEVEL=INFO

# MongoDB
MONGODB_URL=mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin
MONGODB_DATABASE=scoutpro

# Redis
REDIS_URL=redis://redis:6379/0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Opta API
OPTA_API_KEY=your_api_key_here
```

## SOLID Principles Implementation

### Single Responsibility
Each service has a single, well-defined purpose. Each class/module within a service has one reason to change.

### Open/Closed
Repository pattern allows extending functionality without modifying existing code. New data sources can be added by implementing repository interfaces.

### Liskov Substitution
Repository implementations can be swapped without affecting service logic (MongoRepository, OptaRepository, etc.).

### Interface Segregation
Focused interfaces like IPlayerRepository contain only methods needed for player operations.

### Dependency Inversion
Services depend on abstractions (interfaces) not concrete implementations. Dependencies are injected via FastAPI's dependency injection.

## Repository Pattern

The repository pattern abstracts data sources:

```python
# Interface
class IPlayerRepository(ABC):
    async def get_by_id(self, player_id: str) -> Optional[Player]:
        pass

# Implementation
class MongoPlayerRepository(IPlayerRepository):
    async def get_by_id(self, player_id: str) -> Optional[Player]:
        # MongoDB-specific implementation
        pass

# Service uses interface
class PlayerService:
    def __init__(self, repository: IPlayerRepository):
        self.repository = repository
```

## Event-Driven Architecture

Services communicate via Kafka events:

- `player.events` - Player CRUD events
- `team.events` - Team CRUD events
- `match.events` - Match CRUD events
- `live.events` - Live match data updates
- `statistics.events` - Statistical updates

## Caching Strategy

Redis caching is implemented at the service layer:

- Player data: 5 minutes TTL
- Team data: 10 minutes TTL
- Match data: 1 minute TTL (live matches), 5 minutes (finished)
- Statistics: 3 minutes TTL
- Rankings: 6 minutes TTL

## Testing

Each service includes pytest tests:

```bash
# Run tests
cd services/player-service
pytest

# With coverage
pytest --cov=. --cov-report=html
```

## Monitoring

Each service exposes Prometheus metrics at `/metrics`:

- Request count
- Request duration
- Active connections (WebSocket)
- Cache hit/miss rates
- Error rates

## Scaling

Services can be scaled independently:

```bash
# Scale player service to 3 instances
docker-compose up -d --scale player-service=3
```

## Development Workflow

1. Make changes to service code
2. Run tests: `pytest`
3. Build Docker image: `docker build -t player-service .`
4. Test in Docker Compose: `docker-compose up -d player-service`
5. Check logs: `docker-compose logs -f player-service`
6. Access Swagger docs: `http://localhost:8001/docs`

## Production Deployment

Services are designed to run in Kubernetes or ECS:

- Each service has a Dockerfile
- Health checks configured
- Resource limits defined in docker-compose.yml
- Horizontal auto-scaling supported
- Prometheus metrics for monitoring

## API Gateway

All services sit behind an Nginx API Gateway (Port 80):

```
http://localhost/api/v2/players/*    -> player-service:8001
http://localhost/api/v2/teams/*      -> team-service:8002
http://localhost/api/v2/matches/*    -> match-service:8003
http://localhost/api/v2/statistics/* -> statistics-service:8004
http://localhost/api/v2/ml/*         -> ml-service:8005
http://localhost/api/v2/search/*     -> search-service:8007
http://localhost/ws                  -> websocket-server:8080
```

## Troubleshooting

### Service won't start
- Check logs: `docker-compose logs service-name`
- Verify dependencies are running (MongoDB, Kafka, Redis)
- Check environment variables

### Can't connect to database
- Verify MongoDB/Redis/TimescaleDB are running
- Check connection strings in .env
- Ensure networks are configured correctly

### Kafka errors
- Ensure Zookeeper is healthy
- Check Kafka broker is running
- Verify topic creation

## Contributing

1. Follow the existing service structure
2. Implement repository pattern for data access
3. Add comprehensive tests
4. Document API endpoints
5. Update this README if adding new service

## License

Copyright © 2025 ScoutPro. All rights reserved.
