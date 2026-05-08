import re

with open('services/ml-service/api/ml.py', 'r') as f:
    content = f.read()

# Add a module-level cache dictionary near the imports
if "_trajectory_cache" not in content:
    content = re.sub(
        r"from core\.engine import AnalyticsEngine",
        r"from core.engine import AnalyticsEngine\nimport time\n\n_trajectory_cache = {}\n_TRAJECTORY_CACHE_TTL = 3600  # 1 hour\n",
        content
    )

old_endpoint = """@router.get("/players/{player_id}/trajectory", response_model=APIResponse)
async def get_player_trajectory(player_id: str, provider: Optional[str] = None):
    \"\"\"
    Get the developmental trajectory for a player across consecutive seasons. 
    Also forecasts the likely cluster they will be in for the next 1-2 seasons.
    \"\"\"
    cache_key = f"{player_id}_{provider}"
    now = time.time()
    
    if cache_key in _trajectory_cache:
        cached_data, timestamp = _trajectory_cache[cache_key]
        if now - timestamp < _TRAJECTORY_CACHE_TTL:
            return cached_data
            
    engine = get_engine()"""

new_endpoint = old_endpoint

old_ret = """        return APIResponse(
            success=True,
            data=prediction,
            message="Player trajectory computed"
        )
    except Exception as e:"""

new_ret = """        result = APIResponse(
            success=True,
            data=prediction,
            message="Player trajectory computed"
        )
        _trajectory_cache[cache_key] = (result, now)
        return result
    except Exception as e:"""

content = content.replace(old_ret, new_ret)

with open('services/ml-service/api/ml.py', 'w') as f:
    f.write(content)
