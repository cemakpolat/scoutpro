import sys

def modify_file():
    with open('/Users/cemakpolat/Development/own-projects/scoutpro/services/statistics-service/services/event_aggregator_enhanced.py', 'r') as f:
        lines = f.readlines()
    
    # We want to add our methods near the end, just before the file ends.
    # Let's just append them to the class.
    
    new_code = """
    # ==================== PHASE 3 ENRICHMENTS ====================

    async def get_spatial_density_heatmap(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None,
        event_type: Optional[str] = None,
        grid_cols: int = 10,
        grid_rows: int = 10
    ) -> Dict[str, Any]:
        \"\"\"
        Generate a spatial density heatmap for events.
        Divides the pitch (100x100) into a grid and counts events in each cell.
        \"\"\"
        cache_key = f"event:heatmap:{player_id}:{team_id}:{competition_id}:{season_id}:{event_type}:{grid_cols}:{grid_rows}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        filters = self._build_match_filters(player_id, team_id, competition_id, season_id)
        if event_type:
            filters["type_name"] = event_type

        try:
            docs = await self.db.scoutpro.match_events.find(filters).to_list(None)
            
            grid = [[0 for _ in range(grid_rows)] for _ in range(grid_cols)]
            x_step = 100.0 / grid_cols
            y_step = 100.0 / grid_rows
            
            total_events = 0

            for doc in docs:
                location = doc.get("location", {})
                if location and "x" in location and "y" in location:
                    x, y = location["x"], location["y"]
                    # Boundary protection
                    col = min(int(x / x_step), grid_cols - 1)
                    row = min(int(y / y_step), grid_rows - 1)
                    grid[col][row] += 1
                    total_events += 1

            stats = {
                "total_events": total_events,
                "grid_cols": grid_cols,
                "grid_rows": grid_rows,
                "matrix": grid
            }
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats, default=str))
            return stats
            
        except Exception as e:
            logger.error(f"Error in generating heatmap: {e}", exc_info=True)
            return {"error": str(e), "total_events": 0}

    async def get_player_composite_index(
        self,
        player_id: str,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        \"\"\"
        Calculate an overall player rating/index based on aggregated stats.
        Combines passing, shooting, duels, etc. into a single score.
        \"\"\"
        cache_key = f"event:composite:{player_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
            
        try:
            passes = await self.get_pass_statistics_enhanced(player_id=player_id, competition_id=competition_id, season_id=season_id)
            shots = await self.get_shot_statistics_enhanced(player_id=player_id, competition_id=competition_id, season_id=season_id)
            duels = await self.get_duel_statistics_enhanced(player_id=player_id, competition_id=competition_id, season_id=season_id)
            
            # Simple weighting mechanism for composite score
            # These weights would need tuning in a real system
            pass_score = (passes.get("open_play_completion", 0) / 100.0) * min(passes.get("total_passes", 0) / 50.0, 1.0) * 30
            shot_score = (shots.get("shot_accuracy", 0) / 100.0) * min(shots.get("total_shots", 0) / 5.0, 1.0) * 30
            duel_score = (duels.get("duel_success_rate", 0) / 100.0) * min(duels.get("total_duels", 0) / 15.0, 1.0) * 40
            
            # Additional boost for goals
            goal_boost = min(shots.get("goals", 0) * 5, 20)
            
            overall_index = min(max(pass_score + shot_score + duel_score + goal_boost, 0), 100)
            
            stats = {
                "player_id": player_id,
                "composite_index": round(overall_index, 2),
                "components": {
                    "passing_contribution": round(pass_score, 2),
                    "shooting_contribution": round(shot_score + goal_boost, 2),
                    "duel_contribution": round(duel_score, 2)
                }
            }
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats, default=str))
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating composite index: {e}", exc_info=True)
            return {"error": str(e), "composite_index": 0}

    async def get_expected_metrics(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        \"\"\"
        Calculate expected metrics (xG, xA) from enriched events.
        \"\"\"
        cache_key = f"event:expected:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        filters = self._build_match_filters(player_id, team_id, competition_id, season_id)
        # Get shots and passes to extract xG and xA
        filters["type_name"] = {"$in": ["shot", "pass"]}

        try:
            docs = await self.db.scoutpro.match_events.find(filters).to_list(None)
            
            stats = {
                "total_xg": 0.0,
                "total_xa": 0.0,
                "shots_with_xg": 0,
                "passes_with_xa": 0
            }
            
            for doc in docs:
                t_name = doc.get("type_name")
                xg = doc.get("analytical_xg")
                xa = doc.get("analytical_xa") # Assuming similar field for xA
                
                if t_name == "shot" and xg is not None:
                    stats["total_xg"] += float(xg)
                    stats["shots_with_xg"] += 1
                    
                if t_name == "pass" and xa is not None:
                    stats["total_xa"] += float(xa)
                    stats["passes_with_xa"] += 1

            stats["total_xg"] = round(stats["total_xg"], 3)
            stats["total_xa"] = round(stats["total_xa"], 3)
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats, default=str))
            return stats
            
        except Exception as e:
            logger.error(f"Error extracting expected metrics: {e}", exc_info=True)
            return {"error": str(e), "total_xg": 0.0, "total_xa": 0.0}

    async def get_player_similarity(
        self,
        player_id: str,
        target_player_ids: List[str],
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        \"\"\"
        Calculate similarity score between a primary player and target players based on a stat vector.
        \"\"\"
        try:
            primary_stats = await self.get_player_composite_index(player_id, competition_id, season_id)
            if "error" in primary_stats:
                return primary_stats
                
            p_comp = primary_stats.get("components", {})
            p_vec = [
                p_comp.get("passing_contribution", 0),
                p_comp.get("shooting_contribution", 0),
                p_comp.get("duel_contribution", 0)
            ]
            
            p_mag = math.sqrt(sum(v*v for v in p_vec)) or 1.0
            
            similarities = []
            for t_id in target_player_ids:
                t_stats = await self.get_player_composite_index(t_id, competition_id, season_id)
                if "error" in t_stats:
                    continue
                    
                t_comp = t_stats.get("components", {})
                t_vec = [
                    t_comp.get("passing_contribution", 0),
                    t_comp.get("shooting_contribution", 0),
                    t_comp.get("duel_contribution", 0)
                ]
                
                t_mag = math.sqrt(sum(v*v for v in t_vec)) or 1.0
                dot = sum(p*t for p, t in zip(p_vec, t_vec))
                
                cosine_sim = dot / (p_mag * t_mag)
                similarities.append({
                    "player_id": t_id,
                    "similarity_score": round(cosine_sim * 100, 2),
                    "composite_index": t_stats.get("composite_index")
                })
                
            similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            return {
                "base_player_id": player_id,
                "base_composite_index": primary_stats.get("composite_index"),
                "similar_players": similarities
            }
            
        except Exception as e:
            logger.error(f"Error calculating player similarity: {e}", exc_info=True)
            return {"error": str(e)}
"""

    with open('/Users/cemakpolat/Development/own-projects/scoutpro/services/statistics-service/services/event_aggregator_enhanced.py', 'a') as f:
        f.write(new_code)

if __name__ == "__main__":
    modify_file()
