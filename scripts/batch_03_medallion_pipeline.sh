#!/usr/bin/env bash
# ---------------------------------------------------------
# batch_03_medallion_pipeline.sh
# End-to-End automated orchestrator for the entire Data-to-ML pipeline.
# Ideally run via Crontab (e.g. nightly at 02:00 AM) or Airflow API.
# ---------------------------------------------------------
set -e

# Change into project root relative to script
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$PROJECT_ROOT"

echo "=========================================================="
echo "🚀 SCOUTPRO MEDALLION MLOps PIPELINE AUTOMATION"
echo "=========================================================="
echo "Time: $(date)"

# STEP 1: BRONZE & SILVER (Extraction & Load)
# Pulls provider feeds -> Parses them -> Saves Raw payload to MinIO -> Upserts Mongo/Timescale
if [ -f "$PROJECT_ROOT/scripts/batch_01_ingestion.sh" ]; then
    echo ""
    echo "▶️ [STEP 1] Running Data Lake Ingestion (Bronze & Silver Tiers)..."
    bash "$PROJECT_ROOT/scripts/batch_01_ingestion.sh"
else
    echo "⚠️ ERROR: Ingestion script not found."
    exit 1
fi

# STEP 2: GOLD TIER (Feature Engineering)
# Queries Mongo/Timescale -> Builds complex ML aggregations -> Saves .parquet directly to MinIO
if [ -f "$PROJECT_ROOT/scripts/build_ml_features.py" ]; then
    echo ""
    echo "▶️ [STEP 2] Running Feature Engineering (Gold Tier / Parquet Builder)..."
    python3 "$PROJECT_ROOT/scripts/build_ml_features.py"
else
    echo "⚠️ Warning: build_ml_features.py not found. Skipping Parquet build."
fi

# STEP 3: MODEL TRAINING (ML Laboratory)
# Triggers ml-service to read new .parquet from MinIO and retrain the Engine's scikit-learn models
if [ -f "$PROJECT_ROOT/scripts/batch_02_train_models.sh" ]; then
    echo ""
    echo "▶️ [STEP 3] Triggering ML Service Retraining Iteration..."
    bash "$PROJECT_ROOT/scripts/batch_02_train_models.sh"
else
    echo "⚠️ ERROR: Training script not found."
    exit 1
fi

echo ""
echo "=========================================================="
echo "✅ PIPELINE AUTOMATION COMPLETED SUCCESSFULLY"
echo "Duration finished at: $(date)"
echo "=========================================================="
