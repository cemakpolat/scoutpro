import logging
from typing import Dict, Any, Optional

from shared.adapters.opta.taxonomies.strategies import (
    OptaEventStrategy,
    PassEventStrategy,
    ShotEventStrategy,
    FoulEventStrategy,
    CardEventStrategy,
    DuelEventStrategy,
    TakeOnEventStrategy,
    GoalkeeperEventStrategy,
    BallControlEventStrategy,
    InterceptionEventStrategy,
    TackleEventStrategy
)
from shared.domain.entities import BaseEventInfo

logger = logging.getLogger(__name__)

class OptaEventFactory:
    """
    Registry for routing incoming Type IDs from Opta to their respective Strategies
    """
    def __init__(self):
        self._strategies: Dict[int, OptaEventStrategy] = {
            1: PassEventStrategy(),
            3: TakeOnEventStrategy(),
            4: FoulEventStrategy(),
            7: TackleEventStrategy(),
            8: InterceptionEventStrategy(),
            10: GoalkeeperEventStrategy(),
            11: GoalkeeperEventStrategy(),
            13: ShotEventStrategy(),
            14: ShotEventStrategy(),
            15: ShotEventStrategy(),
            16: ShotEventStrategy(),
            17: CardEventStrategy(),
            41: GoalkeeperEventStrategy(),
            44: DuelEventStrategy(),
            49: BallControlEventStrategy(),
            50: BallControlEventStrategy(),
            58: GoalkeeperEventStrategy(),
        }
        
    def create_event(self, raw_event: Dict[str, Any]) -> Optional[BaseEventInfo]:
        """Convert a raw dictionaries payload directly into Unified Domain models."""
        try:
            type_id = int(raw_event.get("type_id", 0))
            strategy = self._strategies.get(type_id)
            
            if strategy:
                return strategy.parse(raw_event)
            else:
                # Fallback to Generic Entity mapping when no deep taxonomy Strategy applied yet
                base_data_extracted = {
                    "event_id": str(raw_event.get("id")),
                    "match_id": str(raw_event.get("game_id", raw_event.get("match_id", ""))),
                    "player_id": str(raw_event.get("player_id")) if "player_id" in raw_event else None,
                    "team_id": str(raw_event.get("team_id", "")),
                    "minute": int(raw_event.get("min", 0)),
                    "second": int(raw_event.get("sec", 0)),
                    "period": int(raw_event.get("period_id", 0)),
                    "type_name": str(raw_event.get("type_id", "unknown")),
                    "provider": "opta"
                }
                logger.debug(f"Missing Strategy for Taxonomical mapping of type ID: {type_id}, mapping to Base.")
                return BaseEventInfo(**base_data_extracted)
                
        except Exception as e:
            logger.error(f"Failed to parse Event ID {raw_event.get('id')} with factory mapping: {e}")
            return None

