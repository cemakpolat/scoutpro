# Automated ML Pipeline (Crontab Setup)

To fully automatize the `Data -> Medallion -> ML Service` ingestion cycles mapped in `/scripts/batch_03_medallion_pipeline.sh`, run the following instructions on the server hosting the ScoutPro environment.

## 1. Setup Python Environment
Make sure `minio`, `pandas`, and `pymongo` are provided to the cron user (or available in the active virtual environment):

```bash
pip install pandas minio pyarrow pymongo numpy
```

## 2. Edit Crontab
Execute:
```bash
crontab -e
```

Paste the following line to automate the ingest & train process **nightly at 02:00 AM**:

```bash
# ScoutPro: Data-to-ML Pipeline
0 2 * * * /Users/cemakpolat/Development/own-projects/scoutpro/scripts/batch_03_medallion_pipeline.sh >> /tmp/scoutpro_pipeline.log 2>&1
```

## How It Works
1. `batch_01_ingestion.sh`: Hooks `data-sync-service`, parses Opta/StatsBomb, saves JSON to MinIO (`scoutpro-raw`), and SQL/MongoDB data forms.
2. `build_ml_features.py`: Aggregates the newly synced databases into high-computation `xt_training_features_2026.parquet` and exports it directly to the MinIO data lake bucket (`scoutpro-ml-features`).
3. `batch_02_train_models.sh`: Fires an HTTP POST triggering the `ml-service` algorithms to refit utilizing the freshly built Parquet files sitting on object storage.
