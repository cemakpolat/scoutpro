"""Position standardization utility for football/soccer player positions.

Converts Opta F40 position values and other provider formats to standardized
position codes and maintains detailed position information for reference.

Standard Position Codes:
    - GK: Goalkeeper
    - DF: Defender
    - MF: Midfielder
    - FW: Forward/Attacker

Detailed Positions (for UI/reporting):
    - GK: Goalkeeper
    - CB: Center Back
    - LB: Left Back
    - RB: Right Back
    - RWB: Right Wing Back
    - LWB: Left Wing Back
    - CM: Central Midfielder
    - RM: Right Midfielder
    - LM: Left Midfielder
    - CAM: Central Attacking Midfielder
    - RAM: Right Attacking Midfielder
    - LAM: Left Attacking Midfielder
    - CDM: Central Defensive Midfielder
    - RDM: Right Defensive Midfielder
    - LDM: Left Defensive Midfielder
    - ST: Striker/Striker
    - CF: Center Forward
    - RW: Right Winger
    - LW: Left Winger
    - RF: Right Forward
    - LF: Left Forward

Examples:
    >>> mapper = PositionMapper()
    >>> mapper.standardize("Forward")
    {'code': 'FW', 'detailed': 'ST', 'raw': 'Forward'}
    
    >>> mapper.standardize("Goalkeeper")
    {'code': 'GK', 'detailed': 'GK', 'raw': 'Goalkeeper'}
    
    >>> mapper.standardize("Midfielder")
    {'code': 'MF', 'detailed': 'CM', 'raw': 'Midfielder'}
"""

from typing import Dict, Optional, Tuple


class PositionMapper:
    """Maps player positions from various sources to standardized codes."""

    # Mapping: raw_position → (standard_code, detailed_position)
    _POSITION_MAP = {
        # Goalkeepers
        "goalkeeper": ("GK", "GK"),
        "goalie": ("GK", "GK"),
        "gk": ("GK", "GK"),
        
        # Defenders (Backs)
        "defender": ("DF", "CB"),
        "centre-back": ("DF", "CB"),
        "center-back": ("DF", "CB"),
        "cb": ("DF", "CB"),
        "central defender": ("DF", "CB"),
        "left back": ("DF", "LB"),
        "lb": ("DF", "LB"),
        "right back": ("DF", "RB"),
        "rb": ("DF", "RB"),
        "left wing-back": ("DF", "LWB"),
        "left wingback": ("DF", "LWB"),
        "lwb": ("DF", "LWB"),
        "right wing-back": ("DF", "RWB"),
        "right wingback": ("DF", "RWB"),
        "rwb": ("DF", "RWB"),
        
        # Midfielders
        "midfielder": ("MF", "CM"),
        "mid": ("MF", "CM"),
        "midfield": ("MF", "CM"),
        "central midfielder": ("MF", "CM"),
        "cm": ("MF", "CM"),
        "left midfielder": ("MF", "LM"),
        "left mid": ("MF", "LM"),
        "lm": ("MF", "LM"),
        "right midfielder": ("MF", "RM"),
        "right mid": ("MF", "RM"),
        "rm": ("MF", "RM"),
        "attacking midfielder": ("MF", "CAM"),
        "attacking mid": ("MF", "CAM"),
        "cam": ("MF", "CAM"),
        "central attacking midfielder": ("MF", "CAM"),
        "left attacking midfielder": ("MF", "LAM"),
        "right attacking midfielder": ("MF", "RAM"),
        "defensive midfielder": ("MF", "CDM"),
        "defensive mid": ("MF", "CDM"),
        "cdm": ("MF", "CDM"),
        "box-to-box midfielder": ("MF", "CM"),
        
        # Forwards/Attackers
        "forward": ("FW", "ST"),
        "fw": ("FW", "ST"),
        "striker": ("FW", "ST"),
        "st": ("FW", "ST"),
        "centre-forward": ("FW", "CF"),
        "center-forward": ("FW", "CF"),
        "cf": ("FW", "CF"),
        "left winger": ("FW", "LW"),
        "left wing": ("FW", "LW"),
        "lw": ("FW", "LW"),
        "right winger": ("FW", "RW"),
        "right wing": ("FW", "RW"),
        "rw": ("FW", "RW"),
        "left forward": ("FW", "LF"),
        "lf": ("FW", "LF"),
        "right forward": ("FW", "RF"),
        "rf": ("FW", "RF"),
    }

    def __init__(self):
        """Initialize the position mapper."""
        self._cache: Dict[str, Dict[str, str]] = {}

    def standardize(
        self,
        raw_position: Optional[str],
        detailed_position: Optional[str] = None
    ) -> Dict[str, Optional[str]]:
        """
        Standardize a position string to canonical format.

        Args:
            raw_position: The original position string from data source (e.g., "Forward")
            detailed_position: Optional pre-computed detailed position

        Returns:
            Dict with keys:
                - 'code': Standard position code (GK, DF, MF, FW) or None
                - 'detailed': Detailed position (CB, ST, etc.) or None
                - 'raw': Original raw position value

        Examples:
            >>> mapper.standardize("Forward")
            {'code': 'FW', 'detailed': 'ST', 'raw': 'Forward'}
            
            >>> mapper.standardize("Unknown Position")
            {'code': None, 'detailed': None, 'raw': 'Unknown Position'}
            
            >>> mapper.standardize(None)
            {'code': None, 'detailed': None, 'raw': None}
        """
        if not raw_position:
            return {"code": None, "detailed": None, "raw": raw_position}

        # Check cache first
        cache_key = (raw_position or "").lower().strip()
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Normalize for matching
        normalized = raw_position.lower().strip()

        # Direct lookup
        if normalized in self._POSITION_MAP:
            code, detail = self._POSITION_MAP[normalized]
            result = {
                "code": code,
                "detailed": detailed_position or detail,
                "raw": raw_position,
            }
            self._cache[cache_key] = result
            return result

        # Try fuzzy matching (partial match, common variations)
        result = self._fuzzy_match(normalized, detailed_position, raw_position)
        self._cache[cache_key] = result
        return result

    def _fuzzy_match(
        self,
        normalized: str,
        detailed_position: Optional[str],
        raw_position: str
    ) -> Dict[str, Optional[str]]:
        """
        Attempt fuzzy matching for unrecognized positions.
        
        Args:
            normalized: Lowercased, stripped position string
            detailed_position: Optional detailed position fallback
            raw_position: Original raw position
            
        Returns:
            Standardized position dict
        """
        # Check for substring matches
        for pos_str, (code, detail) in self._POSITION_MAP.items():
            if pos_str in normalized or normalized in pos_str:
                return {
                    "code": code,
                    "detailed": detailed_position or detail,
                    "raw": raw_position,
                }

        # Check for keyword indicators
        if any(kw in normalized for kw in ["goal", "keeper", "gk"]):
            return {"code": "GK", "detailed": "GK", "raw": raw_position}
        
        if any(kw in normalized for kw in ["back", "defender", "def", "centre", "center", "cb"]):
            return {"code": "DF", "detailed": "CB", "raw": raw_position}
        
        if any(kw in normalized for kw in ["mid", "midfielder"]):
            return {"code": "MF", "detailed": "CM", "raw": raw_position}
        
        if any(kw in normalized for kw in ["forward", "fw", "striker", "forward", "wing", "winger"]):
            return {"code": "FW", "detailed": "ST", "raw": raw_position}

        # Unknown position
        return {
            "code": None,
            "detailed": detailed_position,
            "raw": raw_position,
        }

    def get_all_mappings(self) -> Dict[str, Tuple[str, str]]:
        """
        Get all standardized position mappings.

        Returns:
            Dict mapping raw positions to (code, detailed) tuples
        """
        return dict(self._POSITION_MAP)

    def is_goalkeeper(self, raw_position: Optional[str]) -> bool:
        """Check if position is a goalkeeper."""
        result = self.standardize(raw_position)
        return result["code"] == "GK"

    def is_defender(self, raw_position: Optional[str]) -> bool:
        """Check if position is a defender."""
        result = self.standardize(raw_position)
        return result["code"] == "DF"

    def is_midfielder(self, raw_position: Optional[str]) -> bool:
        """Check if position is a midfielder."""
        result = self.standardize(raw_position)
        return result["code"] == "MF"

    def is_forward(self, raw_position: Optional[str]) -> bool:
        """Check if position is a forward."""
        result = self.standardize(raw_position)
        return result["code"] == "FW"


# Global instance for convenience
_mapper = PositionMapper()


def standardize_position(
    raw_position: Optional[str],
    detailed_position: Optional[str] = None
) -> Dict[str, Optional[str]]:
    """
    Standardize a position using the global mapper instance.

    Args:
        raw_position: The original position string from data source
        detailed_position: Optional pre-computed detailed position

    Returns:
        Dict with 'code', 'detailed', and 'raw' keys
    """
    return _mapper.standardize(raw_position, detailed_position)
