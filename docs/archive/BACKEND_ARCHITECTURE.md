# ScoutPro Backend Architecture - SOLID-Based Design

**Version**: 2.0
**Date**: 2025-10-04
**Status**: Design Phase

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current System Analysis](#current-system-analysis)
3. [Architecture Overview](#architecture-overview)
4. [SOLID Principles Application](#solid-principles-application)
5. [Core Components](#core-components)
6. [Data Source Abstraction](#data-source-abstraction)
7. [ML/Analytics Engine](#ml-analytics-engine)
8. [API Design](#api-design)
9. [Data Flow](#data-flow)
10. [Technology Stack](#technology-stack)
11. [Implementation Roadmap](#implementation-roadmap)

---

## 📊 Executive Summary

This document outlines a modern, scalable backend architecture for ScoutPro - a comprehensive football scouting and analytics platform. The architecture is designed with SOLID principles to support multiple data sources, advanced ML capabilities, and real-time analytics.

### Key Goals
- ✅ Abstract multiple data sources (MongoDB, Opta API, StatsBomb, PostgreSQL, Redis)
- ✅ Provide unified REST/GraphQL APIs for frontend consumption
- ✅ Support pluggable ML algorithms with versioning
- ✅ Enable real-time data processing and streaming
- ✅ Maintain high scalability and performance
- ✅ Ensure code maintainability and testability

---

## 🔍 Current System Analysis

### Existing Backend Structure (`backend/optaapi/`)

**Components Identified**:
- **88 Python files** organized in modular structure
- **MongoDB** as primary data store with MongoEngine ODM
- **Flask** REST API with blueprint architecture
- **Multiple Feed Sources**: F1 (matches), F9 (detailed), F24 (events), F40 (teams/players)
- **ML Engine**: Algorithm factory with Decision Tree, Clustering, Regression, Feature Selection
- **Statistics Processing**: Comprehensive event aggregation (Aerial, Pass, Shot, Duel, etc.)

### Data Models (MongoDB Collections)

#### Feed 1 (F1) - Match Basic Data
```python
- F1_MatchData: Match information
- F1_MatchInfo: Date, venue, status, scores
- F1_TeamData: Team scores, goals
- F1_Goal: Goal events
- F1_MatchOfficial: Referee data
```

#### Feed 9 (F9) - Detailed Match Data
```python
- F9_MatchData: Complete match details
- F9_Team: Team information with players
- F9_Player: Player details and stats
- F9_TeamData: Match team stats
- F9_MatchPlayer: Player lineup
- F9_Booking: Cards
- F9_Substitution: Subs
- F9_Goal: Goals with assists
```

#### Feed 24 (F24) - Event-Level Data
```python
- F24_Game: Game container
- F24_Event: Individual events (passes, shots, etc.)
- F24_QEvent: Event qualifiers (position, outcome)
```

#### Feed 40 (F40) - Team/Player Personal Info
```python
- F40_Team: Team metadata
- F40_Player: Player personal info
- F40_Stadium: Stadium details
- F40_PersonalInfo: Biographical data
```

#### Statistics Collections
```python
- PlayerStatistics: Aggregated player stats
- PlayerStatisticsPer90: Per 90 minute stats
- PlayerPercentileStatistics: Percentile rankings
- TeamStatistics: Team aggregations
- GameMinuteStatistics: Minute-by-minute data
```

### Current API Endpoints

**Players** (`/api/v1/players/...`):
- `/players/<id>` - Get player by ID
- `/players/personal/<name>` - Player personal info
- `/players/statistics/<player>/<team>` - Player statistics
- `/players/compare` - Compare multiple players
- `/statistics/important/players/<name>` - Key stats
- `/statistics/rank/player/...` - Player rankings

**Teams** (`/api/v1/teams/...`):
- Team data, statistics, rankings

**Games** (`/api/v1/games/...`):
- Match data, statistics, events

**Analytics** (`/api/v1/analytic/...`):
- `/analytic/<algorithm>/<function>` - ML execution
- Supports: cluster, linear-regression, logistic-regression, feature-selection

### Strengths
✅ Rich statistical processing (per90, percentile)
✅ Flexible MongoDB query system
✅ ML algorithm abstraction exists
✅ Comprehensive data models

### Weaknesses
❌ Tight coupling to MongoDB
❌ No data source abstraction layer
❌ Monolithic architecture
❌ Limited API versioning
❌ No caching strategy
❌ Synchronous processing only

---

## 🏗️ Architecture Overview

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │   React UI   │  Mobile App  │  Dashboard   │  3rd Party   │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                           │
│              (FastAPI + GraphQL + WebSocket)                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  /api/v2/players | /api/v2/teams | /api/v2/matches      │   │
│  │  /api/v2/analytics | /api/v2/ml | /graphql | /ws        │   │
│  └──────────────────────────────────────────────────────────┘   │
│  [Authentication] [Rate Limiting] [Request Validation]           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   APPLICATION SERVICE LAYER                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  PlayerService │ TeamService │ MatchService              │   │
│  │  StatisticsService │ MLService │ CacheService            │   │
│  └──────────────────────────────────────────────────────────┘   │
│  [Business Logic] [Data Orchestration] [Validation]              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              DATA ACCESS LAYER (Repository Pattern)              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  IPlayerRepository │ ITeamRepository │ IMatchRepository  │   │
│  │  IStatsRepository │ IMLModelRepository                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│  [Abstraction Layer - Dependency Inversion Principle]            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│            DATA SOURCE ADAPTERS (Strategy Pattern)               │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────────┐   │
│  │ MongoDB  │  Opta    │StatsBomb │PostgreSQL│  Redis       │   │
│  │ Adapter  │ Adapter  │ Adapter  │ Adapter  │  Cache       │   │
│  └──────────┴──────────┴──────────┴──────────┴──────────────┘   │
│  [Data Source Abstraction - Open/Closed Principle]               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                              │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────────┐   │
│  │ MongoDB  │Opta API  │StatsBomb │PostgreSQL│   Redis      │   │
│  │  (F1,F9, │ (Feeds)  │   API    │  (Time   │  (Cache)     │   │
│  │ F24,F40) │          │          │  Series) │              │   │
│  └──────────┴──────────┴──────────┴──────────┴──────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    ML/ANALYTICS ENGINE                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Algorithm Factory (Strategy Pattern)                     │   │
│  │  ┌──────────┬──────────┬──────────┬──────────────────┐   │   │
│  │  │ Decision │Clustering│LinearReg │FeatureSelection  │   │   │
│  │  │   Tree   │ K-Means  │Logistic  │   PCA, ANOVA     │   │   │
│  │  │  Random  │  DBSCAN  │  Ridge   │   Mutual Info    │   │   │
│  │  │  Forest  │Hierarchi │  Lasso   │   Chi-Square     │   │   │
│  │  └──────────┴──────────┴──────────┴──────────────────┘   │   │
│  │                                                            │   │
│  │  Data Pipeline (ETL)                                      │   │
│  │  ┌──────────┬──────────┬──────────┬──────────────────┐   │   │
│  │  │Extractor │Transform │Validator │   Loader         │   │   │
│  │  │ (Query)  │(Features)│(Quality) │ (Training Set)   │   │   │
│  │  └──────────┴──────────┴──────────┴──────────────────┘   │   │
│  │                                                            │   │
│  │  Model Registry & Versioning                              │   │
│  │  ┌──────────┬──────────┬──────────┬──────────────────┐   │   │
│  │  │  Model   │ Metadata │ Metrics  │   Versioning     │   │   │
│  │  │  Store   │  Store   │  Store   │   (MLflow)       │   │   │
│  │  └──────────┴──────────┴──────────┴──────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    SUPPORTING SERVICES                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Message Queue │ Task Queue │ Logging │ Monitoring       │   │
│  │  (RabbitMQ)    │  (Celery)  │(ELK)    │(Prometheus)      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 SOLID Principles Application

### 1. Single Responsibility Principle (SRP)
**Each class/module has ONE reason to change**

```python
# ✅ GOOD - Single responsibility
class PlayerService:
    """Handles player business logic ONLY"""
    def get_player_with_stats(self, player_id: str) -> PlayerDTO:
        pass

class PlayerRepository:
    """Handles player data access ONLY"""
    def get_by_id(self, player_id: str) -> Player:
        pass

class StatisticsAggregator:
    """Handles statistics calculations ONLY"""
    def calculate_per_90(self, stats: Dict) -> Dict:
        pass

# ❌ BAD - Multiple responsibilities
class PlayerManager:
    def get_player(self): pass  # Data access
    def calculate_stats(self): pass  # Business logic
    def format_response(self): pass  # Presentation
    def save_to_db(self): pass  # Data persistence
```

### 2. Open/Closed Principle (OCP)
**Open for extension, closed for modification**

```python
# ✅ GOOD - New data sources added without modifying existing code
class IPlayerRepository(ABC):
    @abstractmethod
    async def get_by_id(self, player_id: str) -> Player:
        pass

# Add new source by implementing interface
class OptaPlayerRepository(IPlayerRepository):
    async def get_by_id(self, player_id: str) -> Player:
        # Opta-specific implementation
        pass

class StatsBombPlayerRepository(IPlayerRepository):
    async def get_by_id(self, player_id: str) -> Player:
        # StatsBomb-specific implementation
        pass

# ❌ BAD - Requires modification for each new source
class PlayerRepository:
    def get_player(self, source: str, player_id: str):
        if source == "mongo":
            # mongo code
        elif source == "opta":
            # opta code
        elif source == "statsbomb":  # Need to modify this class!
            # statsbomb code
```

### 3. Liskov Substitution Principle (LSP)
**Subclasses must be substitutable for their base classes**

```python
# ✅ GOOD - All implementations can replace the interface
def get_player_from_any_source(repo: IPlayerRepository, player_id: str):
    return repo.get_by_id(player_id)

# All these work identically
mongo_repo = MongoPlayerRepository()
opta_repo = OptaPlayerRepository()
statsbomb_repo = StatsBombPlayerRepository()

player1 = get_player_from_any_source(mongo_repo, "123")
player2 = get_player_from_any_source(opta_repo, "123")
player3 = get_player_from_any_source(statsbomb_repo, "123")
```

### 4. Interface Segregation Principle (ISP)
**Clients should not depend on interfaces they don't use**

```python
# ✅ GOOD - Specific, focused interfaces
class IPlayerReader(ABC):
    @abstractmethod
    def get_by_id(self, player_id: str) -> Player: pass

class IPlayerWriter(ABC):
    @abstractmethod
    def create(self, player: Player) -> str: pass
    @abstractmethod
    def update(self, player: Player) -> None: pass

class IPlayerStatistics(ABC):
    @abstractmethod
    def get_statistics(self, player_id: str) -> Dict: pass

# Implement only what's needed
class ReadOnlyPlayerRepository(IPlayerReader):
    def get_by_id(self, player_id: str) -> Player:
        pass

# ❌ BAD - Fat interface with unnecessary methods
class IPlayerRepository(ABC):
    def get(self): pass
    def create(self): pass
    def update(self): pass
    def delete(self): pass
    def get_stats(self): pass
    def calculate_percentile(self): pass
    def export_to_excel(self): pass  # Why is this here?
    def send_email(self): pass  # This doesn't belong!
```

### 5. Dependency Inversion Principle (DIP)
**Depend on abstractions, not concretions**

```python
# ✅ GOOD - Depend on abstraction (interface)
class PlayerService:
    def __init__(
        self,
        player_repo: IPlayerRepository,  # ← Abstraction
        stats_aggregator: IStatisticsAggregator,  # ← Abstraction
        cache: ICacheService  # ← Abstraction
    ):
        self.player_repo = player_repo
        self.stats_aggregator = stats_aggregator
        self.cache = cache

# Dependency Injection
service = PlayerService(
    player_repo=MongoPlayerRepository(),
    stats_aggregator=DefaultStatsAggregator(),
    cache=RedisCache()
)

# ❌ BAD - Depend on concrete implementation
class PlayerService:
    def __init__(self):
        self.player_repo = MongoPlayerRepository()  # ← Concrete class
        self.stats_aggregator = DefaultStatsAggregator()  # ← Concrete
        self.cache = RedisCache()  # ← Concrete
```

---

## 🔧 Core Components

### 1. Repository Pattern (Data Access Layer)

**Purpose**: Abstract data source access behind a unified interface

```python
# repository/interfaces.py
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from domain.models import Player, PlayerFilters

class IPlayerRepository(ABC):
    """Player repository interface - all implementations must conform"""

    @abstractmethod
    async def get_by_id(self, player_id: str) -> Optional[Player]:
        """Retrieve player by ID"""
        pass

    @abstractmethod
    async def find_by_filters(self, filters: PlayerFilters) -> List[Player]:
        """Find players matching filters"""
        pass

    @abstractmethod
    async def get_statistics(
        self,
        player_id: str,
        stat_type: str,
        per_90: bool = False,
        percentile: bool = False
    ) -> Dict:
        """Get player statistics"""
        pass

    @abstractmethod
    async def search(self, query: str) -> List[Player]:
        """Search players by name/club/position"""
        pass

# repository/mongo_player_repository.py
from pymongo import MongoClient
from .interfaces import IPlayerRepository

class MongoPlayerRepository(IPlayerRepository):
    """MongoDB implementation"""

    def __init__(self, db: MongoClient):
        self.db = db
        self.collection = db['players']

    async def get_by_id(self, player_id: str) -> Optional[Player]:
        data = await F9_Player.objects(uID=player_id).first()
        if not data:
            return None
        return self._map_to_domain(data)

    async def get_statistics(
        self,
        player_id: str,
        stat_type: str,
        per_90: bool = False,
        percentile: bool = False
    ) -> Dict:
        # Use existing aggregation logic
        if per_90:
            stats = await PlayerStatisticsPer90.objects(playerID=player_id).first()
        elif percentile:
            stats = await PlayerPercentileStatistics.objects(playerID=player_id).first()
        else:
            stats = await PlayerStatistics.objects(playerID=player_id).first()

        return self._extract_event_stats(stats, stat_type)

    def _map_to_domain(self, mongo_doc) -> Player:
        """Map MongoDB document to domain model"""
        return Player(
            id=str(mongo_doc.uID),
            name=mongo_doc.name or f"{mongo_doc.first} {mongo_doc.last}",
            position=mongo_doc.position,
            # ... map other fields
        )

# repository/opta_player_repository.py
class OptaPlayerRepository(IPlayerRepository):
    """Opta API implementation"""

    def __init__(self, opta_client: OptaAPIClient):
        self.client = opta_client

    async def get_by_id(self, player_id: str) -> Optional[Player]:
        # Call Opta Feed 40 for player info
        response = await self.client.get_feed_40_player(player_id)
        return self._map_opta_to_domain(response)

    async def get_statistics(
        self,
        player_id: str,
        stat_type: str,
        per_90: bool = False,
        percentile: bool = False
    ) -> Dict:
        # Call Opta Feed 24 for events
        events = await self.client.get_feed_24_events(player_id)
        # Aggregate using Opta-specific logic
        return self._aggregate_opta_stats(events, stat_type, per_90)

# repository/statsbomb_player_repository.py
class StatsBombPlayerRepository(IPlayerRepository):
    """StatsBomb API implementation"""

    def __init__(self, statsbomb_client):
        self.client = statsbomb_client

    async def get_by_id(self, player_id: str) -> Optional[Player]:
        response = await self.client.players.get(player_id)
        return self._map_statsbomb_to_domain(response)

# repository/composite_player_repository.py
class CompositePlayerRepository(IPlayerRepository):
    """Aggregates data from multiple sources"""

    def __init__(self, repositories: List[IPlayerRepository]):
        self.repositories = repositories
        self.primary = repositories[0]

    async def get_by_id(self, player_id: str) -> Optional[Player]:
        # Get from primary source
        player = await self.primary.get_by_id(player_id)

        # Enrich from other sources
        for repo in self.repositories[1:]:
            try:
                additional_data = await repo.get_by_id(player_id)
                player = self._merge_player_data(player, additional_data)
            except Exception as e:
                logger.warning(f"Failed to enrich from {repo}: {e}")

        return player
```

### 2. Service Layer (Business Logic)

```python
# services/player_service.py
from repository.interfaces import IPlayerRepository
from services.interfaces import IStatisticsAggregator, ICacheService
from domain.dto import PlayerDTO

class PlayerService:
    """Orchestrates player-related business logic"""

    def __init__(
        self,
        player_repo: IPlayerRepository,
        stats_aggregator: IStatisticsAggregator,
        cache: ICacheService,
        logger: ILogger
    ):
        self.player_repo = player_repo
        self.stats_aggregator = stats_aggregator
        self.cache = cache
        self.logger = logger

    async def get_player_with_stats(
        self,
        player_id: str,
        include_percentile: bool = False,
        per_90: bool = False,
        stat_groups: List[str] = None
    ) -> PlayerDTO:
        """Get player with statistics"""

        # Build cache key
        cache_key = f"player:{player_id}:per90={per_90}:percentile={include_percentile}"

        # Check cache
        cached = await self.cache.get(cache_key)
        if cached:
            self.logger.info(f"Cache hit for {player_id}")
            return PlayerDTO.from_json(cached)

        # Get player from repository
        player = await self.player_repo.get_by_id(player_id)
        if not player:
            raise PlayerNotFoundException(player_id)

        # Get statistics
        stat_groups = stat_groups or ['aerial', 'pass', 'shot', 'duel']
        stats = {}

        for group in stat_groups:
            stats[group] = await self.stats_aggregator.calculate(
                player_id=player_id,
                stat_type=group,
                per_90=per_90,
                percentile=include_percentile
            )

        # Build DTO
        dto = PlayerDTO.from_domain(player, stats)

        # Cache result (5 min TTL)
        await self.cache.set(cache_key, dto.to_json(), ttl=300)

        return dto

    async def compare_players(
        self,
        player_ids: List[str],
        stat_groups: List[str] = None,
        per_90: bool = False
    ) -> Dict[str, PlayerDTO]:
        """Compare multiple players"""

        results = {}
        for player_id in player_ids:
            try:
                results[player_id] = await self.get_player_with_stats(
                    player_id=player_id,
                    per_90=per_90,
                    stat_groups=stat_groups
                )
            except Exception as e:
                self.logger.error(f"Failed to get player {player_id}: {e}")

        return results

    async def rank_players(
        self,
        stat_type: str,
        stat_name: str,
        limit: int = 10,
        filters: PlayerFilters = None
    ) -> List[PlayerDTO]:
        """Rank players by a specific statistic"""

        # Get filtered players
        players = await self.player_repo.find_by_filters(filters)

        # Calculate stat for each
        player_stats = []
        for player in players:
            stats = await self.stats_aggregator.calculate(
                player_id=player.id,
                stat_type=stat_type
            )
            player_stats.append({
                'player': player,
                'stat_value': stats.get(stat_name, 0)
            })

        # Sort and limit
        sorted_players = sorted(
            player_stats,
            key=lambda x: x['stat_value'],
            reverse=True
        )[:limit]

        # Build DTOs
        return [
            PlayerDTO.from_domain(item['player'], {'stat_value': item['stat_value']})
            for item in sorted_players
        ]
```

### 3. Data Source Factory

```python
# factory/data_source_factory.py
from typing import Dict, Type
from repository.interfaces import IPlayerRepository
from repository.mongo_player_repository import MongoPlayerRepository
from repository.opta_player_repository import OptaPlayerRepository
from repository.statsbomb_player_repository import StatsBombPlayerRepository
from repository.composite_player_repository import CompositePlayerRepository

class DataSourceFactory:
    """Factory for creating repository instances"""

    def __init__(self, config: Config):
        self.config = config
        self._repositories: Dict[str, IPlayerRepository] = {}
        self._initialize_repositories()

    def _initialize_repositories(self):
        """Initialize all configured repositories"""

        if self.config.mongodb_enabled:
            self._repositories['mongodb'] = MongoPlayerRepository(
                db=self.config.mongo_client
            )

        if self.config.opta_enabled:
            self._repositories['opta'] = OptaPlayerRepository(
                opta_client=self.config.opta_client
            )

        if self.config.statsbomb_enabled:
            self._repositories['statsbomb'] = StatsBombPlayerRepository(
                statsbomb_client=self.config.statsbomb_client
            )

    def get_player_repository(
        self,
        source: str = "default"
    ) -> IPlayerRepository:
        """Get repository for specific source"""

        if source == "default":
            source = self.config.default_data_source

        if source not in self._repositories:
            raise ValueError(f"Data source '{source}' not configured")

        return self._repositories[source]

    def get_composite_repository(
        self,
        sources: List[str] = None
    ) -> IPlayerRepository:
        """Get composite repository aggregating multiple sources"""

        if sources is None:
            sources = list(self._repositories.keys())

        repos = [
            self._repositories[source]
            for source in sources
            if source in self._repositories
        ]

        if not repos:
            raise ValueError("No valid data sources available")

        return CompositePlayerRepository(repos)
```

---

## 🤖 ML/Analytics Engine

### Architecture

```python
# ml/engine.py
from ml.interfaces import IAlgorithm, IDataPipeline, IModelRegistry
from ml.factory import AlgorithmFactory
from ml.dto import TrainRequest, TrainResult, PredictRequest, PredictResult

class MLEngine:
    """Orchestrates ML training and prediction"""

    def __init__(
        self,
        algorithm_factory: AlgorithmFactory,
        data_pipeline: IDataPipeline,
        model_registry: IModelRegistry
    ):
        self.algorithm_factory = algorithm_factory
        self.data_pipeline = data_pipeline
        self.model_registry = model_registry

    async def train_model(self, request: TrainRequest) -> TrainResult:
        """Train a new ML model"""

        # 1. Extract data from configured sources
        raw_data = await self.data_pipeline.extract(
            source=request.data_source,
            query=request.query_config
        )

        # 2. Transform and prepare features
        features, target = await self.data_pipeline.transform(
            data=raw_data,
            feature_config=request.feature_config
        )

        # 3. Validate data quality
        validation_result = await self.data_pipeline.validate(features, target)
        if not validation_result.is_valid:
            raise DataValidationError(validation_result.errors)

        # 4. Get algorithm instance
        algorithm = self.algorithm_factory.create(
            algorithm_name=request.algorithm,
            config=request.algorithm_config
        )

        # 5. Split data
        X_train, X_test, y_train, y_test = algorithm.split_data(
            features,
            target,
            test_size=request.test_size,
            random_state=request.random_state
        )

        # 6. Train model
        model = await algorithm.train(X_train, y_train)

        # 7. Evaluate
        metrics = await algorithm.evaluate(model, X_test, y_test)

        # 8. Register model
        model_id = await self.model_registry.register(
            model=model,
            metadata={
                "algorithm": request.algorithm,
                "metrics": metrics,
                "feature_config": request.feature_config,
                "version": "1.0",
                "created_at": datetime.utcnow().isoformat()
            }
        )

        return TrainResult(
            model_id=model_id,
            metrics=metrics,
            feature_importance=algorithm.get_feature_importance(model)
        )

    async def predict(self, request: PredictRequest) -> PredictResult:
        """Make predictions using trained model"""

        # 1. Load model from registry
        model_metadata = await self.model_registry.get_metadata(request.model_id)
        model = await self.model_registry.load(request.model_id)

        # 2. Prepare input data with same transformations
        input_data = await self.data_pipeline.transform(
            data=request.input_data,
            feature_config=model_metadata['feature_config']
        )

        # 3. Make predictions
        predictions = model.predict(input_data)

        # 4. Get prediction confidence/probabilities if available
        confidence = None
        if hasattr(model, 'predict_proba'):
            confidence = model.predict_proba(input_data)

        return PredictResult(
            predictions=predictions.tolist(),
            confidence=confidence.tolist() if confidence is not None else None,
            model_id=request.model_id,
            model_version=model_metadata['version']
        )

    async def get_feature_importance(self, model_id: str) -> Dict:
        """Get feature importance for a model"""

        model = await self.model_registry.load(model_id)
        metadata = await self.model_registry.get_metadata(model_id)

        algorithm = self.algorithm_factory.create(
            algorithm_name=metadata['algorithm']
        )

        return algorithm.get_feature_importance(model)

# ml/algorithms/decision_tree.py
from ml.interfaces import IAlgorithm
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.model_selection import train_test_split
import numpy as np

class DecisionTreeAlgorithm(IAlgorithm):
    """Decision Tree implementation"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.model_type = self.config.get('model_type', 'classifier')

    def split_data(self, features, target, test_size=0.2, random_state=42):
        return train_test_split(
            features,
            target,
            test_size=test_size,
            random_state=random_state
        )

    async def train(self, X_train, y_train):
        if self.model_type == 'classifier':
            model = DecisionTreeClassifier(
                criterion=self.config.get('criterion', 'gini'),
                max_depth=self.config.get('max_depth'),
                min_samples_split=self.config.get('min_samples_split', 2),
                random_state=self.config.get('random_state', 42)
            )
        else:
            model = DecisionTreeRegressor(
                criterion=self.config.get('criterion', 'mse'),
                max_depth=self.config.get('max_depth'),
                min_samples_split=self.config.get('min_samples_split', 2),
                random_state=self.config.get('random_state', 42)
            )

        model.fit(X_train, y_train)
        return model

    async def evaluate(self, model, X_test, y_test):
        predictions = model.predict(X_test)

        if self.model_type == 'classifier':
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            return {
                'accuracy': accuracy_score(y_test, predictions),
                'precision': precision_score(y_test, predictions, average='weighted'),
                'recall': recall_score(y_test, predictions, average='weighted'),
                'f1_score': f1_score(y_test, predictions, average='weighted')
            }
        else:
            from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
            return {
                'mse': mean_squared_error(y_test, predictions),
                'rmse': np.sqrt(mean_squared_error(y_test, predictions)),
                'mae': mean_absolute_error(y_test, predictions),
                'r2_score': r2_score(y_test, predictions)
            }

    def get_feature_importance(self, model) -> Dict:
        if hasattr(model, 'feature_importances_'):
            return {
                'importances': model.feature_importances_.tolist(),
                'sorted_indices': np.argsort(model.feature_importances_)[::-1].tolist()
            }
        return {}

# ml/data_pipeline.py
class MLDataPipeline(IDataPipeline):
    """Extract, Transform, Load pipeline for ML"""

    def __init__(self, data_source_factory: DataSourceFactory):
        self.data_source_factory = data_source_factory

    async def extract(self, source: str, query: Dict) -> pd.DataFrame:
        """Extract data from source"""

        repo = self.data_source_factory.get_player_repository(source)

        # Build filters from query
        filters = PlayerFilters(**query.get('filters', {}))
        players = await repo.find_by_filters(filters)

        # Extract statistics
        data = []
        for player in players:
            stats = await repo.get_statistics(
                player_id=player.id,
                stat_type=query.get('stat_type', 'all')
            )
            data.append({
                'player_id': player.id,
                'player_name': player.name,
                **stats
            })

        return pd.DataFrame(data)

    async def transform(self, data: pd.DataFrame, feature_config: Dict) -> Tuple:
        """Transform data for ML"""

        # Select features
        feature_cols = feature_config.get('included', [])
        target_col = feature_config.get('target')

        # Exclude columns
        exclude_cols = feature_config.get('excluded', [])
        feature_cols = [c for c in feature_cols if c not in exclude_cols]

        # Handle missing values
        if feature_config.get('fill_na'):
            data = data.fillna(feature_config['fill_na'])

        # Normalize if requested
        if feature_config.get('normalize'):
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            data[feature_cols] = scaler.fit_transform(data[feature_cols])

        # Extract features and target
        X = data[feature_cols].values
        y = data[target_col].values if target_col else None

        return X, y

    async def validate(self, features, target) -> ValidationResult:
        """Validate data quality"""

        errors = []

        # Check for NaN
        if np.isnan(features).any():
            errors.append("Features contain NaN values")

        if target is not None and np.isnan(target).any():
            errors.append("Target contains NaN values")

        # Check for infinite values
        if np.isinf(features).any():
            errors.append("Features contain infinite values")

        # Check data size
        if len(features) < 30:
            errors.append("Insufficient data for training (< 30 samples)")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
```

---

## 🌐 API Design

### RESTful API (FastAPI)

```python
# api/v2/players.py
from fastapi import APIRouter, Depends, Query, HTTPException
from dependency_injector.wiring import inject, Provide
from typing import List, Optional
from api.dto import PlayerResponse, PlayerListResponse, ErrorResponse
from services.player_service import PlayerService

router = APIRouter(prefix="/api/v2/players", tags=["players"])

@router.get("/{player_id}", response_model=PlayerResponse)
@inject
async def get_player(
    player_id: str,
    per_90: bool = Query(False, description="Return per 90 minute stats"),
    percentile: bool = Query(False, description="Include percentile rankings"),
    stat_groups: Optional[List[str]] = Query(None, description="Stat groups to include"),
    source: str = Query("default", description="Data source (mongodb, opta, statsbomb, composite)"),
    player_service: PlayerService = Depends(Provide["services.player"])
):
    """Get player by ID with statistics"""
    try:
        player = await player_service.get_player_with_stats(
            player_id=player_id,
            include_percentile=percentile,
            per_90=per_90,
            stat_groups=stat_groups
        )
        return PlayerResponse(success=True, data=player)
    except PlayerNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=PlayerListResponse)
@inject
async def list_players(
    position: Optional[List[str]] = Query(None),
    club: Optional[List[str]] = Query(None),
    age_min: Optional[int] = Query(None),
    age_max: Optional[int] = Query(None),
    rating_min: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    player_service: PlayerService = Depends(Provide["services.player"])
):
    """List players with filters"""
    filters = PlayerFilters(
        position=position,
        club=club,
        ageMin=age_min,
        ageMax=age_max,
        ratingMin=rating_min
    )

    players = await player_service.list_players(
        filters=filters,
        page=page,
        limit=limit
    )

    return PlayerListResponse(
        success=True,
        data=players,
        pagination={
            'page': page,
            'limit': limit,
            'total': len(players)
        }
    )

@router.post("/compare", response_model=PlayerListResponse)
@inject
async def compare_players(
    player_ids: List[str],
    stat_groups: Optional[List[str]] = None,
    per_90: bool = False,
    player_service: PlayerService = Depends(Provide["services.player"])
):
    """Compare multiple players"""
    comparison = await player_service.compare_players(
        player_ids=player_ids,
        stat_groups=stat_groups,
        per_90=per_90
    )

    return PlayerListResponse(
        success=True,
        data=list(comparison.values())
    )

@router.get("/rank/{stat_type}/{stat_name}", response_model=PlayerListResponse)
@inject
async def rank_players(
    stat_type: str,
    stat_name: str,
    limit: int = Query(10, ge=1, le=100),
    position: Optional[str] = Query(None),
    player_service: PlayerService = Depends(Provide["services.player"])
):
    """Rank players by statistic"""
    filters = PlayerFilters(position=[position] if position else None)

    ranked = await player_service.rank_players(
        stat_type=stat_type,
        stat_name=stat_name,
        limit=limit,
        filters=filters
    )

    return PlayerListResponse(success=True, data=ranked)

# api/v2/ml.py
from fastapi import APIRouter, Depends, HTTPException
from dependency_injector.wiring import inject, Provide
from ml.engine import MLEngine
from ml.dto import TrainRequest, TrainResponse, PredictRequest, PredictResponse

router = APIRouter(prefix="/api/v2/ml", tags=["machine-learning"])

@router.post("/train", response_model=TrainResponse)
@inject
async def train_model(
    request: TrainRequest,
    ml_engine: MLEngine = Depends(Provide["services.ml_engine"])
):
    """Train a new ML model"""
    try:
        result = await ml_engine.train_model(request)
        return TrainResponse(success=True, data=result)
    except DataValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict", response_model=PredictResponse)
@inject
async def predict(
    request: PredictRequest,
    ml_engine: MLEngine = Depends(Provide["services.ml_engine"])
):
    """Make predictions using trained model"""
    try:
        result = await ml_engine.predict(request)
        return PredictResponse(success=True, data=result)
    except ModelNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_id}/importance")
@inject
async def get_feature_importance(
    model_id: str,
    ml_engine: MLEngine = Depends(Provide["services.ml_engine"])
):
    """Get feature importance for a model"""
    importance = await ml_engine.get_feature_importance(model_id)
    return {"success": True, "data": importance}

@router.get("/algorithms")
async def list_algorithms():
    """List available ML algorithms"""
    return {
        "success": True,
        "data": [
            {
                "name": "decision-tree",
                "type": "classifier/regressor",
                "description": "Decision Tree algorithm",
                "parameters": {
                    "criterion": ["gini", "entropy"],
                    "max_depth": "int or None",
                    "min_samples_split": "int"
                }
            },
            {
                "name": "linear-regression",
                "type": "regressor",
                "description": "Linear Regression",
                "parameters": {
                    "normalize": "bool",
                    "fit_intercept": "bool"
                }
            },
            # ... more algorithms
        ]
    }

# api/v2/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v2 import players, teams, matches, analytics, ml

app = FastAPI(
    title="ScoutPro API",
    version="2.0.0",
    description="Football Scouting & Analytics Platform"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(players.router)
app.include_router(teams.router)
app.include_router(matches.router)
app.include_router(analytics.router)
app.include_router(ml.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}
```

---

## 🔄 Data Flow Examples

### Example 1: Get Player Statistics from Multiple Sources

```
1. Client Request:
   GET /api/v2/players/123?source=composite&per_90=true

2. API Gateway (FastAPI):
   ├→ Authenticate request
   ├→ Validate parameters
   └→ Route to PlayerController.get_player()

3. PlayerService.get_player_with_stats():
   ├→ Check Redis cache (miss)
   ├→ DataSourceFactory.get_composite_repository()
   │  └→ Returns CompositePlayerRepository([MongoDB, Opta, StatsBomb])
   │
   ├→ CompositePlayerRepository.get_by_id("123")
   │  ├→ MongoPlayerRepository.get_by_id("123") [Primary Source]
   │  │  └→ Query MongoDB F9_Player collection
   │  │
   │  ├→ OptaPlayerRepository.get_by_id("123") [Enrichment]
   │  │  └→ Call Opta Feed 40 API
   │  │
   │  └→ StatsBombPlayerRepository.get_by_id("123") [Enrichment]
   │     └→ Call StatsBomb Players API
   │
   │  └→ Merge data from all sources
   │
   ├→ StatisticsAggregator.calculate(player_id="123", per_90=True)
   │  ├→ AerialEventAggregator.calculate_per_90()
   │  ├→ PassEventAggregator.calculate_per_90()
   │  ├→ ShotEventAggregator.calculate_per_90()
   │  └→ DuelEventAggregator.calculate_per_90()
   │
   ├→ Build PlayerDTO
   └→ Cache in Redis (TTL: 5 min)

4. Response:
   {
     "success": true,
     "data": {
       "id": "123",
       "name": "Player Name",
       "statistics": { /* per 90 stats */ }
     },
     "meta": {
       "sources": ["mongodb", "opta", "statsbomb"],
       "cached": false,
       "timestamp": "2025-10-04T19:30:00Z"
     }
   }
```

### Example 2: Train ML Model

```
1. Client Request:
   POST /api/v2/ml/train
   {
     "algorithm": "decision-tree",
     "algorithm_config": {
       "criterion": "gini",
       "max_depth": 10
     },
     "data_source": "mongodb",
     "query_config": {
       "filters": {
         "position": ["Forward"],
         "age_min": 20,
         "age_max": 30
       },
       "stat_type": "shot"
     },
     "feature_config": {
       "included": ["goals", "shots_on_target", "xG"],
       "excluded": ["player_id"],
       "target": "goals",
       "normalize": true
     },
     "test_size": 0.2,
     "random_state": 42
   }

2. MLEngine.train_model():
   ├→ MLDataPipeline.extract(source="mongodb", query={...})
   │  ├→ DataSourceFactory.get_player_repository("mongodb")
   │  ├→ MongoPlayerRepository.find_by_filters({position: "Forward", ...})
   │  ├→ For each player:
   │  │  └→ MongoPlayerRepository.get_statistics(player_id, "shot")
   │  └→ Return DataFrame with 500 rows
   │
   ├→ MLDataPipeline.transform(data, feature_config)
   │  ├→ Select columns: ["goals", "shots_on_target", "xG"]
   │  ├→ Normalize with StandardScaler
   │  └→ Return (X, y)
   │
   ├→ MLDataPipeline.validate(X, y)
   │  ├→ Check for NaN: ✓
   │  ├→ Check for infinite: ✓
   │  └→ Check data size: ✓ (500 > 30)
   │
   ├→ AlgorithmFactory.create("decision-tree", config)
   │  └→ Return DecisionTreeAlgorithm instance
   │
   ├→ DecisionTreeAlgorithm.split_data(X, y, test_size=0.2)
   │  └→ Return (X_train, X_test, y_train, y_test)
   │
   ├→ DecisionTreeAlgorithm.train(X_train, y_train)
   │  └→ Fit sklearn DecisionTreeClassifier
   │
   ├→ DecisionTreeAlgorithm.evaluate(model, X_test, y_test)
   │  └→ Calculate metrics: {accuracy: 0.85, precision: 0.82, ...}
   │
   └→ ModelRegistry.register(model, metadata)
      ├→ Save model to disk (pickle/joblib)
      ├→ Store metadata in MongoDB
      └→ Return model_id: "model_abc123"

3. Response:
   {
     "success": true,
     "data": {
       "model_id": "model_abc123",
       "metrics": {
         "accuracy": 0.85,
         "precision": 0.82,
         "recall": 0.79,
         "f1_score": 0.80
       },
       "feature_importance": {
         "importances": [0.45, 0.35, 0.20],
         "sorted_indices": [0, 1, 2]
       }
     }
   }
```

---

## 🛠️ Technology Stack

### Backend Core
- **Framework**: FastAPI (Python 3.11+)
- **ORM/ODM**: SQLAlchemy (PostgreSQL), MongoEngine (MongoDB)
- **Validation**: Pydantic
- **DI Container**: dependency-injector
- **Async**: asyncio, aiohttp

### Data Sources
- **MongoDB**: Primary statistics storage (existing feeds)
- **PostgreSQL**: Time-series data, relational analytics
- **Redis**: Caching, session management
- **Opta API**: Live feed integration (F1, F9, F24, F40)
- **StatsBomb API**: Alternative data source

### ML/Analytics
- **ML Framework**: scikit-learn, XGBoost, LightGBM
- **Deep Learning**: PyTorch (future)
- **Feature Engineering**: pandas, numpy
- **Model Registry**: MLflow
- **Data Processing**: Apache Spark (future scale)

### Infrastructure
- **API Gateway**: Kong/Nginx
- **Message Queue**: RabbitMQ/Kafka
- **Task Queue**: Celery with Redis
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Tracing**: Jaeger
- **CI/CD**: GitHub Actions, Docker, Kubernetes

### Development
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Linting**: pylint, black, isort
- **Documentation**: Sphinx, OpenAPI/Swagger
- **Version Control**: Git, GitHub

---

## 📅 Implementation Roadmap

### Phase 1: Foundation (Weeks 1-3)
- ✅ Set up project structure with SOLID architecture
- ✅ Implement Repository Pattern with MongoDB adapter
- ✅ Create Service Layer (PlayerService, TeamService)
- ✅ Set up FastAPI with basic endpoints
- ✅ Implement Redis caching
- ✅ Write unit tests (>80% coverage)

### Phase 2: Data Source Abstraction (Weeks 4-6)
- ✅ Implement Opta API adapter
- ✅ Implement StatsBomb API adapter
- ✅ Create Composite Repository pattern
- ✅ Implement Data Source Factory
- ✅ Add PostgreSQL support for time-series data
- ✅ Integration tests for multi-source queries

### Phase 3: ML Engine (Weeks 7-10)
- ✅ Implement Algorithm Factory
- ✅ Port existing ML algorithms (Decision Tree, Clustering, etc.)
- ✅ Create ML Data Pipeline (ETL)
- ✅ Implement Model Registry with versioning
- ✅ Add ML API endpoints
- ✅ ML model testing and validation

### Phase 4: Advanced Features (Weeks 11-14)
- ✅ WebSocket support for real-time updates
- ✅ GraphQL API implementation
- ✅ Advanced caching strategies (multi-level)
- ✅ Batch processing with Celery
- ✅ API rate limiting and throttling
- ✅ Comprehensive API documentation

### Phase 5: Performance & Scale (Weeks 15-16)
- ✅ Performance optimization (database indexing, query optimization)
- ✅ Load testing and benchmarking
- ✅ Horizontal scaling with Kubernetes
- ✅ CDN integration for static assets
- ✅ Database sharding strategy

### Phase 6: Production Readiness (Weeks 17-18)
- ✅ Monitoring and alerting setup
- ✅ Logging and distributed tracing
- ✅ Security audit and hardening
- ✅ Disaster recovery planning
- ✅ Production deployment
- ✅ Documentation finalization

---

## 📈 Success Metrics

### Technical Metrics
- **API Response Time**: < 200ms (p95)
- **ML Training Time**: < 5 minutes for 10K samples
- **Prediction Latency**: < 50ms
- **Cache Hit Rate**: > 70%
- **API Uptime**: > 99.9%
- **Test Coverage**: > 85%

### Business Metrics
- **Data Source Availability**: 99.5% aggregate
- **Model Accuracy**: > 80% for classification tasks
- **User Query Success Rate**: > 95%
- **Data Freshness**: < 5 minutes lag for live data

---

## 🔒 Security Considerations

### API Security
- JWT-based authentication
- Role-based access control (RBAC)
- API key management
- Rate limiting per user/IP
- Request validation and sanitization
- HTTPS/TLS encryption

### Data Security
- Encryption at rest (database)
- Encryption in transit (API)
- PII data masking
- Audit logging for sensitive operations
- Secure credential management (Vault)

### Infrastructure Security
- Network isolation (VPC)
- Firewall rules
- DDoS protection
- Regular security patches
- Penetration testing

---

## 📚 References

### Design Patterns
- Repository Pattern: https://martinfowler.com/eaaCatalog/repository.html
- Service Layer: https://martinfowler.com/eaaCatalog/serviceLayer.html
- Strategy Pattern: https://refactoring.guru/design-patterns/strategy

### SOLID Principles
- Uncle Bob's SOLID: https://blog.cleancoder.com/uncle-bob/2020/10/18/Solid-Relevance.html
- Python SOLID: https://realpython.com/solid-principles-python/

### Architecture
- Clean Architecture: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- Hexagonal Architecture: https://alistair.cockburn.us/hexagonal-architecture/

---

**Document Version**: 1.0
**Last Updated**: 2025-10-04
**Author**: ScoutPro Engineering Team
