# ScoutPro - Implementation Guide

**Complete step-by-step guide to implementing the ScoutPro backend microservices**

---

## 📚 Table of Contents

1. [Getting Started](#getting-started)
2. [Service Implementation](#service-implementation)
3. [Database Setup](#database-setup)
4. [Event-Driven Architecture](#event-driven-architecture)
5. [Testing](#testing)
6. [Deployment](#deployment)
7. [Monitoring & Observability](#monitoring--observability)

---

## 🚀 Getting Started

### Prerequisites

```bash
# Install required tools
- Python 3.11+
- Docker Desktop
- Node.js 18+ (for frontend)
- Git
- wscat (for WebSocket testing): npm install -g wscat
```

### Project Structure

```
scoutpro/
├── services/              # Backend microservices
│   ├── player-service/
│   ├── team-service/
│   ├── match-service/
│   ├── statistics-service/
│   ├── ml-service/
│   ├── search-service/
│   ├── notification-service/
│   ├── websocket-server/
│   ├── live-ingestion-service/
│   ├── report-service/    # ✅ Implemented (2025-10-19)
│   ├── export-service/    # ✅ Implemented (2025-10-19)
│   ├── video-service/     # ✅ Implemented (2025-10-19)
│   ├── analytics-service/ # ✅ Implemented (2025-10-19)
│   └── shared/            # Shared libraries
├── src/                   # Frontend React app
├── nginx/                 # API Gateway
├── infrastructure/        # IaC (Terraform, K8s)
├── monitoring/            # Prometheus, Grafana configs
├── docker-compose.yml     # Local orchestration
└── scripts/               # Utility scripts
```

**Note**: All 13 microservices are now fully implemented as of 2025-10-19. This guide serves as a reference for maintaining existing services or adding new ones.

---

## 🏗️ Service Implementation

### Step 1: Create New Service

#### Directory Structure

```bash
# Create new service
mkdir -p services/my-service/{api,domain,repository,config,tests}

# Create files
cd services/my-service
touch main.py Dockerfile requirements.txt
```

#### Service Template

**`main.py`**:
```python
"""
My Service - Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import sys
sys.path.append('/app')
from shared.utils.logger import setup_logger
from config.settings import get_settings
from api.routes import router

# Settings
settings = get_settings()
logger = setup_logger(settings.service_name, settings.log_level)

# FastAPI app
app = FastAPI(
    title="My Service",
    description="My Service Description",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Include routers
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    logger.info(f"Starting {settings.service_name}")
    # TODO: Initialize database connections
    # TODO: Initialize Kafka producer/consumer
    logger.info(f"{settings.service_name} started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown"""
    logger.info(f"Shutting down {settings.service_name}")
    # TODO: Close connections

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
```

**`config/settings.py`**:
```python
"""Service configuration"""
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Service
    service_name: str = "my-service"
    debug: bool = False
    log_level: str = "INFO"

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "scoutpro"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
```

**`api/routes.py`**:
```python
"""API routes"""
from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/api/v2", tags=["my-service"])

class MyModel(BaseModel):
    id: str
    name: str

@router.get("/items", response_model=List[MyModel])
async def get_items():
    """Get all items"""
    # TODO: Implement
    return []

@router.get("/items/{item_id}", response_model=MyModel)
async def get_item(item_id: str):
    """Get item by ID"""
    # TODO: Implement
    raise HTTPException(status_code=404, detail="Item not found")

@router.post("/items", response_model=MyModel)
async def create_item(item: MyModel):
    """Create new item"""
    # TODO: Implement
    return item
```

**`Dockerfile`**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Copy shared libraries
COPY ../shared /app/shared

# Expose port
EXPOSE 8000

# Run service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`requirements.txt`**:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6
prometheus-fastapi-instrumentator==6.1.0
motor==3.3.2
mongoengine==0.27.0
redis==5.0.1
aiokafka==0.9.0
```

---

### Step 2: Implement Repository Pattern

**`repository/base.py`**:
```python
"""Base repository interface"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')

class IRepository(ABC, Generic[T]):
    """Base repository interface"""

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities"""
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create entity"""
        pass

    @abstractmethod
    async def update(self, id: str, entity: T) -> T:
        """Update entity"""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete entity"""
        pass
```

**`repository/mongo_repository.py`**:
```python
"""MongoDB repository implementation"""
from typing import List, Optional, Type
from repository.base import IRepository, T
from mongoengine import Document

class MongoRepository(IRepository[T]):
    """MongoDB repository implementation"""

    def __init__(self, model: Type[Document]):
        self.model = model

    async def get_by_id(self, id: str) -> Optional[T]:
        """Get entity by ID"""
        try:
            return self.model.objects(id=id).first()
        except Exception as e:
            return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities"""
        return list(self.model.objects.skip(skip).limit(limit))

    async def create(self, entity: T) -> T:
        """Create entity"""
        entity.save()
        return entity

    async def update(self, id: str, entity: T) -> T:
        """Update entity"""
        existing = await self.get_by_id(id)
        if not existing:
            raise ValueError(f"Entity {id} not found")
        entity.save()
        return entity

    async def delete(self, id: str) -> bool:
        """Delete entity"""
        entity = await self.get_by_id(id)
        if not entity:
            return False
        entity.delete()
        return True
```

---

### Step 3: Implement Domain Logic

**`domain/models.py`**:
```python
"""Domain models"""
from mongoengine import Document, StringField, IntField, DateTimeField
from datetime import datetime

class MyEntity(Document):
    """My entity model"""

    meta = {
        'collection': 'my_entities',
        'indexes': [
            'name',
            'created_at'
        ]
    }

    name = StringField(required=True, max_length=200)
    description = StringField()
    value = IntField(default=0)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'value': self.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
```

**`domain/service.py`**:
```python
"""Business logic service"""
from typing import List, Optional
from domain.models import MyEntity
from repository.mongo_repository import MongoRepository

class MyService:
    """Business logic for my service"""

    def __init__(self):
        self.repository = MongoRepository(MyEntity)

    async def get_entity(self, entity_id: str) -> Optional[MyEntity]:
        """Get entity by ID"""
        return await self.repository.get_by_id(entity_id)

    async def list_entities(self, skip: int = 0, limit: int = 100) -> List[MyEntity]:
        """List all entities"""
        return await self.repository.get_all(skip, limit)

    async def create_entity(self, name: str, description: str, value: int) -> MyEntity:
        """Create new entity"""
        entity = MyEntity(
            name=name,
            description=description,
            value=value
        )
        return await self.repository.create(entity)

    async def update_entity(self, entity_id: str, **kwargs) -> MyEntity:
        """Update entity"""
        entity = await self.get_entity(entity_id)
        if not entity:
            raise ValueError(f"Entity {entity_id} not found")

        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        entity.updated_at = datetime.utcnow()
        return await self.repository.update(entity_id, entity)

    async def delete_entity(self, entity_id: str) -> bool:
        """Delete entity"""
        return await self.repository.delete(entity_id)
```

---

### Step 4: Implement Kafka Integration

**Publishing Events**:
```python
"""Kafka event publisher"""
from aiokafka import AIOKafkaProducer
import json
import logging

logger = logging.getLogger(__name__)

class EventPublisher:
    """Kafka event publisher"""

    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None

    async def start(self):
        """Start producer"""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()
        logger.info("Kafka producer started")

    async def stop(self):
        """Stop producer"""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")

    async def publish(self, topic: str, event: dict):
        """Publish event to topic"""
        try:
            await self.producer.send(topic, value=event)
            logger.info(f"Published event to {topic}: {event.get('event_type')}")
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
```

**Consuming Events**:
```python
"""Kafka event consumer"""
from aiokafka import AIOKafkaConsumer
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class EventConsumer:
    """Kafka event consumer"""

    def __init__(self, bootstrap_servers: str, topics: list, group_id: str):
        self.bootstrap_servers = bootstrap_servers
        self.topics = topics
        self.group_id = group_id
        self.consumer = None
        self.running = False

    async def start(self):
        """Start consumer"""
        self.consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )
        await self.consumer.start()
        logger.info(f"Kafka consumer started for topics: {self.topics}")
        self.running = True

    async def stop(self):
        """Stop consumer"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")

    async def consume(self, handler):
        """Consume events and handle them"""
        try:
            async for message in self.consumer:
                if not self.running:
                    break

                try:
                    await handler(message.value)
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
        except Exception as e:
            logger.error(f"Consumer error: {e}")
```

---

## 🗄️ Database Setup

### MongoDB

**Connection**:
```python
from mongoengine import connect

def setup_mongodb(uri: str, db_name: str):
    """Setup MongoDB connection"""
    connect(
        db=db_name,
        host=uri,
        alias='default'
    )
```

**Indexes**:
```python
from domain.models import MyEntity

def create_indexes():
    """Create database indexes"""
    MyEntity.ensure_indexes()
```

### TimescaleDB

**Schema Initialization**:
```python
import asyncpg

async def initialize_timescaledb():
    """Initialize TimescaleDB schema"""
    conn = await asyncpg.connect('postgresql://user:pass@localhost/db')

    # Create hypertable
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS player_stats (
            time TIMESTAMPTZ NOT NULL,
            player_id TEXT NOT NULL,
            metric TEXT NOT NULL,
            value DOUBLE PRECISION,
            PRIMARY KEY (time, player_id, metric)
        );
    ''')

    await conn.execute('''
        SELECT create_hypertable('player_stats', 'time', if_not_exists => TRUE);
    ''')

    await conn.close()
```

### Redis

**Caching**:
```python
import redis.asyncio as redis
import json

class CacheService:
    """Redis cache service"""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def get(self, key: str):
        """Get from cache"""
        value = await self.redis.get(key)
        return json.loads(value) if value else None

    async def set(self, key: str, value: dict, ttl: int = 300):
        """Set in cache with TTL"""
        await self.redis.setex(key, ttl, json.dumps(value))

    async def delete(self, key: str):
        """Delete from cache"""
        await self.redis.delete(key)
```

---

## 🧪 Testing

### Unit Tests

**`tests/test_service.py`**:
```python
import pytest
from domain.service import MyService

@pytest.fixture
async def service():
    """Create service instance"""
    return MyService()

@pytest.mark.asyncio
async def test_create_entity(service):
    """Test entity creation"""
    entity = await service.create_entity(
        name="Test Entity",
        description="Test Description",
        value=100
    )

    assert entity.name == "Test Entity"
    assert entity.value == 100

@pytest.mark.asyncio
async def test_get_entity(service):
    """Test get entity"""
    # Create entity
    created = await service.create_entity("Test", "Desc", 50)

    # Get entity
    entity = await service.get_entity(str(created.id))

    assert entity is not None
    assert entity.name == "Test"
```

### Integration Tests

**`tests/integration/test_api.py`**:
```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_items():
    """Test get items endpoint"""
    response = client.get("/api/v2/items")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

---

## 🚢 Deployment

### Docker Compose

Add to `docker-compose.yml`:
```yaml
my-service:
  build:
    context: ./services/my-service
    dockerfile: Dockerfile
  ports:
    - "8009:8000"
  environment:
    - MONGODB_URL=mongodb://mongo:27017
    - REDIS_URL=redis://redis:6379
    - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
  depends_on:
    - mongo
    - redis
    - kafka
  networks:
    - scoutpro-network
```

### Kubernetes

**`k8s/deployment.yaml`**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-service
  template:
    metadata:
      labels:
        app: my-service
    spec:
      containers:
      - name: my-service
        image: scoutpro/my-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: MONGODB_URL
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: mongodb-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

---

## 📊 Monitoring & Observability

### Prometheus Metrics

**Custom Metrics**:
```python
from prometheus_client import Counter, Histogram, Gauge

# Request counter
requests_total = Counter(
    'my_service_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

# Request duration
request_duration = Histogram(
    'my_service_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

# Active connections
active_connections = Gauge(
    'my_service_active_connections',
    'Number of active connections'
)

# Usage
requests_total.labels(method='GET', endpoint='/items', status='200').inc()
with request_duration.labels(method='GET', endpoint='/items').time():
    # Handle request
    pass
```

### Structured Logging

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    """JSON log formatter"""

    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'service': 'my-service',
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName
        }

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)

# Setup
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger('my-service')
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

---

## 🎯 Best Practices

### 1. Error Handling

```python
from fastapi import HTTPException

async def get_item_safe(item_id: str):
    """Get item with proper error handling"""
    try:
        item = await service.get_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### 2. Dependency Injection

```python
from fastapi import Depends

async def get_service() -> MyService:
    """Dependency: Get service instance"""
    return MyService()

@router.get("/items")
async def get_items(service: MyService = Depends(get_service)):
    """Get items with injected service"""
    return await service.list_entities()
```

### 3. Request Validation

```python
from pydantic import BaseModel, Field, validator

class CreateItemRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    value: int = Field(..., ge=0, le=1000)

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v
```

---

## 📝 Checklist

### New Service Implementation

- [ ] Create directory structure
- [ ] Implement main.py with FastAPI
- [ ] Create configuration (settings.py)
- [ ] Implement repository pattern
- [ ] Implement domain models
- [ ] Implement business logic
- [ ] Add API routes
- [ ] Add Kafka integration
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Create Dockerfile
- [ ] Add to docker-compose.yml
- [ ] Add Prometheus metrics
- [ ] Add structured logging
- [ ] Document API endpoints
- [ ] Update NGINX routing

---

**Ready to implement!** 🚀

**Next**: [Service-Specific Guides](#) | [API Documentation](#) | [Deployment Guide](#)
