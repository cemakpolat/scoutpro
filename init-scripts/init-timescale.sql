-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create MLflow database
CREATE DATABASE mlflow;

-- Create tables for time-series data
CREATE TABLE IF NOT EXISTS match_stats (
    time TIMESTAMPTZ NOT NULL,
    match_id VARCHAR(50) NOT NULL,
    minute INTEGER,
    home_possession FLOAT,
    away_possession FLOAT,
    home_xg FLOAT,
    away_xg FLOAT,
    home_shots INTEGER,
    away_shots INTEGER,
    metadata JSONB
);

SELECT create_hypertable('match_stats', 'time', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS player_performance (
    time TIMESTAMPTZ NOT NULL,
    player_id VARCHAR(50) NOT NULL,
    match_id VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100),
    metric_value FLOAT,
    metadata JSONB
);

SELECT create_hypertable('player_performance', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_match_stats_match_id ON match_stats (match_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_player_performance_player_id ON player_performance (player_id, time DESC);

-- Create retention policies (keep 1 year)
SELECT add_retention_policy('match_stats', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('player_performance', INTERVAL '1 year', if_not_exists => TRUE);

-- ==========================================
-- STEP 2: MEDALLION ARCHITECTURE (GOLD TIER)
-- Match Events Timeseries Hypertable
-- ==========================================
CREATE TABLE IF NOT EXISTS match_events_ts (
    event_time TIMESTAMPTZ NOT NULL,
    match_id VARCHAR(50) NOT NULL,
    player_id VARCHAR(50),
    team_id VARCHAR(50),
    event_type VARCHAR(100) NOT NULL,
    x_coord FLOAT,
    y_coord FLOAT,
    end_x_coord FLOAT,
    end_y_coord FLOAT,
    is_success BOOLEAN,
    metadata JSONB
);

-- Convert to TimescaleDB hypertable partitioned by event_time
SELECT create_hypertable('match_events_ts', 'event_time', if_not_exists => TRUE);

-- Create fast lookup indexes for spatial and temporal ML queries
CREATE INDEX IF NOT EXISTS idx_match_events_ts_match_time ON match_events_ts (match_id, event_time);
CREATE INDEX IF NOT EXISTS idx_match_events_ts_player ON match_events_ts (player_id, event_type);

-- Keep events for 2 years (historical analysis span)
SELECT add_retention_policy('match_events_ts', INTERVAL '2 years', if_not_exists => TRUE);
