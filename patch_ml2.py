import re

with open('services/ml-service/api/ml.py', 'r') as f:
    content = f.read()

# Add a module-level cache dictionary near the imports
if "_trajectory_cache" not in content:
    content = re.sub(
        r"from engine import AnalyticsEngine",
        r"from engine import AnalyticsEngine\nimport time\n\n_trajectory_cache = {}\n_TRAJECTORY_CACHE_TTL = 3600  # 1 hour\n",
        content
    )

with open('services/ml-service/api/ml.py', 'w') as f:
    f.write(content)
