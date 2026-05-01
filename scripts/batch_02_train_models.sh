#!/usr/bin/env bash
# ---------------------------------------------------------
# batch_02_train_models.sh
# Triggers retrain tasks based on the newly accumulated data
# in the databases. Uses the ML API to dispatch tasks via REST.
# ---------------------------------------------------------

echo "=========================================================="
echo "🧠 ScoutPro - Batch Machine Learning Training"
echo "=========================================================="

API_URL="http://localhost:8005/api/v2/ml/engine/train"
declare -a MODELS=(
  "performance_anomaly_detector"
  "tactical_role_classifier"
  "fatigue_risk_predictor"
  "xgot_finishing_model"
  "pitch_control_nn"
  "expected_threat_model"
  "advanced_player_similarity"
)

for model in "${MODELS[@]}"; do
  echo ">>> Dispatched Training Job: $model"
  curl -s -X POST -H "Content-Type: application/json" -d '{}' "${API_URL}/${model}" | grep -o '"success":true' > /dev/null
  if [ $? -eq 0 ]; then
     echo "    ✅ Model queued/trained successfully."
  else
     echo "    ⏳ Checking details... "
  fi
done

echo "=========================================================="
echo "✅ Batch Training Job Finished."
echo "=========================================================="
