"""
TimescaleDB Client for Time-Series Data
Used for storing match events, player statistics over time, and performance metrics
"""
import asyncpg
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class TimescaleDBClient:
    """
    Async TimescaleDB client for time-series data storage

    Used for:
    - Match events timeline
    - Player statistics over time
    - Team performance metrics
    - Real-time analytics aggregations
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize TimescaleDB client

        Args:
            host: Database host (default: from TIMESCALE_HOST env)
            port: Database port (default: from TIMESCALE_PORT env or 5432)
            database: Database name (default: from TIMESCALE_DB env)
            user: Database user (default: from TIMESCALE_USER env)
            password: Database password (default: from TIMESCALE_PASSWORD env)
        """
        self.host = host or os.getenv('TIMESCALE_HOST', 'timescaledb')
        self.port = port or int(os.getenv('TIMESCALE_PORT', '5432'))
        self.database = database or os.getenv('TIMESCALE_DB', 'scoutpro_timeseries')
        self.user = user or os.getenv('TIMESCALE_USER', 'scoutpro')
        self.password = password or os.getenv('TIMESCALE_PASSWORD', 'scoutpro_password')

        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Create connection pool"""
        if self.pool is not None:
            return

        try:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info(f"Connected to TimescaleDB: {self.host}:{self.port}/{self.database}")
        except Exception as e:
            logger.error(f"Failed to connect to TimescaleDB: {e}")
            raise

    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Disconnected from TimescaleDB")

    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as connection:
            yield connection

    # ============ Schema Management ============

    async def initialize_schema(self):
        """
        Create TimescaleDB hypertables for time-series data

        Creates tables for:
        - match_events: All match events timeline
        - player_stats_timeseries: Player statistics over time
        - team_stats_timeseries: Team statistics over time
        - match_metrics: Real-time match metrics
        """
        async with self.acquire() as conn:
            # Enable TimescaleDB extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

            # Match Events Table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS match_events (
                    time TIMESTAMPTZ NOT NULL,
                    match_id TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    player_id TEXT,
                    team_id TEXT,
                    minute INTEGER,
                    x_coordinate FLOAT,
                    y_coordinate FLOAT,
                    outcome TEXT,
                    metadata JSONB,
                    PRIMARY KEY (time, event_id)
                );
            """)

            # Convert to hypertable
            await conn.execute("""
                SELECT create_hypertable('match_events', 'time', if_not_exists => TRUE);
            """)

            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_match_events_match_id ON match_events (match_id, time DESC);
                CREATE INDEX IF NOT EXISTS idx_match_events_player_id ON match_events (player_id, time DESC);
                CREATE INDEX IF NOT EXISTS idx_match_events_team_id ON match_events (team_id, time DESC);
                CREATE INDEX IF NOT EXISTS idx_match_events_type ON match_events (event_type, time DESC);
            """)

            # Player Stats Timeseries Table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS player_stats_timeseries (
                    time TIMESTAMPTZ NOT NULL,
                    player_id TEXT NOT NULL,
                    match_id TEXT,
                    goals INTEGER DEFAULT 0,
                    assists INTEGER DEFAULT 0,
                    shots INTEGER DEFAULT 0,
                    shots_on_target INTEGER DEFAULT 0,
                    passes_completed INTEGER DEFAULT 0,
                    passes_attempted INTEGER DEFAULT 0,
                    tackles INTEGER DEFAULT 0,
                    interceptions INTEGER DEFAULT 0,
                    minutes_played INTEGER DEFAULT 0,
                    yellow_cards INTEGER DEFAULT 0,
                    red_cards INTEGER DEFAULT 0,
                    rating FLOAT,
                    metadata JSONB,
                    PRIMARY KEY (time, player_id)
                );
            """)

            await conn.execute("""
                SELECT create_hypertable('player_stats_timeseries', 'time', if_not_exists => TRUE);
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_player_stats_player_id ON player_stats_timeseries (player_id, time DESC);
                CREATE INDEX IF NOT EXISTS idx_player_stats_match_id ON player_stats_timeseries (match_id, time DESC);
            """)

            # Team Stats Timeseries Table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS team_stats_timeseries (
                    time TIMESTAMPTZ NOT NULL,
                    team_id TEXT NOT NULL,
                    match_id TEXT,
                    goals INTEGER DEFAULT 0,
                    shots INTEGER DEFAULT 0,
                    shots_on_target INTEGER DEFAULT 0,
                    possession FLOAT,
                    passes_completed INTEGER DEFAULT 0,
                    passes_attempted INTEGER DEFAULT 0,
                    corners INTEGER DEFAULT 0,
                    offsides INTEGER DEFAULT 0,
                    fouls INTEGER DEFAULT 0,
                    yellow_cards INTEGER DEFAULT 0,
                    red_cards INTEGER DEFAULT 0,
                    metadata JSONB,
                    PRIMARY KEY (time, team_id)
                );
            """)

            await conn.execute("""
                SELECT create_hypertable('team_stats_timeseries', 'time', if_not_exists => TRUE);
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_team_stats_team_id ON team_stats_timeseries (team_id, time DESC);
                CREATE INDEX IF NOT EXISTS idx_team_stats_match_id ON team_stats_timeseries (match_id, time DESC);
            """)

            # Match Metrics Table (real-time aggregations)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS match_metrics (
                    time TIMESTAMPTZ NOT NULL,
                    match_id TEXT NOT NULL,
                    minute INTEGER,
                    home_possession FLOAT,
                    away_possession FLOAT,
                    home_shots INTEGER DEFAULT 0,
                    away_shots INTEGER DEFAULT 0,
                    home_passes INTEGER DEFAULT 0,
                    away_passes INTEGER DEFAULT 0,
                    home_score INTEGER DEFAULT 0,
                    away_score INTEGER DEFAULT 0,
                    metadata JSONB,
                    PRIMARY KEY (time, match_id)
                );
            """)

            await conn.execute("""
                SELECT create_hypertable('match_metrics', 'time', if_not_exists => TRUE);
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_match_metrics_match_id ON match_metrics (match_id, time DESC);
            """)

            logger.info("TimescaleDB schema initialized successfully")

    # ============ Match Events Methods ============

    async def insert_match_event(
        self,
        match_id: str,
        event_id: str,
        event_type: str,
        timestamp: datetime,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        minute: Optional[int] = None,
        x_coordinate: Optional[float] = None,
        y_coordinate: Optional[float] = None,
        outcome: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Insert a match event"""
        async with self.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO match_events
                (time, match_id, event_id, event_type, player_id, team_id, minute,
                 x_coordinate, y_coordinate, outcome, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (time, event_id) DO NOTHING
                """,
                timestamp, match_id, event_id, event_type, player_id, team_id,
                minute, x_coordinate, y_coordinate, outcome, metadata or {}
            )

    async def get_match_events(
        self,
        match_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[str]] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get match events with optional filters"""
        query = "SELECT * FROM match_events WHERE match_id = $1"
        params = [match_id]
        param_count = 1

        if start_time:
            param_count += 1
            query += f" AND time >= ${param_count}"
            params.append(start_time)

        if end_time:
            param_count += 1
            query += f" AND time <= ${param_count}"
            params.append(end_time)

        if event_types:
            param_count += 1
            query += f" AND event_type = ANY(${param_count})"
            params.append(event_types)

        query += f" ORDER BY time DESC LIMIT {limit}"

        async with self.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    # ============ Player Stats Methods ============

    async def insert_player_stats(
        self,
        player_id: str,
        timestamp: datetime,
        match_id: Optional[str] = None,
        stats: Dict[str, Any] = None
    ):
        """Insert player statistics snapshot"""
        async with self.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO player_stats_timeseries
                (time, player_id, match_id, goals, assists, shots, shots_on_target,
                 passes_completed, passes_attempted, tackles, interceptions,
                 minutes_played, yellow_cards, red_cards, rating, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                """,
                timestamp, player_id, match_id,
                stats.get('goals', 0), stats.get('assists', 0),
                stats.get('shots', 0), stats.get('shots_on_target', 0),
                stats.get('passes_completed', 0), stats.get('passes_attempted', 0),
                stats.get('tackles', 0), stats.get('interceptions', 0),
                stats.get('minutes_played', 0),
                stats.get('yellow_cards', 0), stats.get('red_cards', 0),
                stats.get('rating'), stats.get('metadata', {})
            )

    async def get_player_stats_history(
        self,
        player_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get player statistics history"""
        query = "SELECT * FROM player_stats_timeseries WHERE player_id = $1"
        params = [player_id]
        param_count = 1

        if start_time:
            param_count += 1
            query += f" AND time >= ${param_count}"
            params.append(start_time)

        if end_time:
            param_count += 1
            query += f" AND time <= ${param_count}"
            params.append(end_time)

        query += f" ORDER BY time DESC LIMIT {limit}"

        async with self.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    # ============ Aggregation Methods ============

    async def get_player_aggregated_stats(
        self,
        player_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get aggregated player statistics for a time period"""
        async with self.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    SUM(goals) as total_goals,
                    SUM(assists) as total_assists,
                    SUM(shots) as total_shots,
                    SUM(shots_on_target) as total_shots_on_target,
                    SUM(passes_completed) as total_passes_completed,
                    SUM(passes_attempted) as total_passes_attempted,
                    SUM(minutes_played) as total_minutes,
                    AVG(rating) as avg_rating,
                    COUNT(*) as matches_played
                FROM player_stats_timeseries
                WHERE player_id = $1 AND time >= $2 AND time <= $3
                """,
                player_id, start_time, end_time
            )
            return dict(row) if row else {}

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()


# Global client instance
_timescale_client: Optional[TimescaleDBClient] = None


async def get_timescale_client() -> TimescaleDBClient:
    """Get global TimescaleDB client instance"""
    global _timescale_client

    if _timescale_client is None:
        _timescale_client = TimescaleDBClient()
        await _timescale_client.connect()
        await _timescale_client.initialize_schema()

    return _timescale_client
