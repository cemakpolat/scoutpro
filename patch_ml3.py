with open('services/ml-service/api/ml.py', 'r') as f:
    content = f.read()

if "import time\n\n_trajectory_cache = {}" not in content:
    content = content.replace("from engine import AnalyticsEngine", "from engine import AnalyticsEngine\nimport time\n\n_trajectory_cache = {}\n_TRAJECTORY_CACHE_TTL = 3600  # 1 hour\n")

with open('services/ml-service/api/ml.py', 'w') as f:
    f.write(content)
