"""
Merge Strategy Functions

Implements all merge strategies defined in merge_rules.yaml.
Each strategy resolves conflicts between two or more data values from different providers.
"""

from typing import Any, Optional, Dict, List, Callable
from datetime import datetime
from statistics import mean, median


# ========================================
# BASIC STRATEGIES
# ========================================

def prefer_primary(
    primary_value: Any,
    secondary_value: Any,
    **kwargs
) -> Any:
    """
    Always prefer the primary provider's value

    Args:
        primary_value: Value from primary provider
        secondary_value: Value from secondary provider
        **kwargs: Additional context (ignored)

    Returns:
        primary_value

    Example:
        prefer_primary(5, 10) → 5
    """
    return primary_value


def prefer_secondary(
    primary_value: Any,
    secondary_value: Any,
    **kwargs
) -> Any:
    """
    Prefer the secondary provider's value

    Args:
        primary_value: Value from primary provider
        secondary_value: Value from secondary provider
        **kwargs: Additional context (ignored)

    Returns:
        secondary_value

    Example:
        prefer_secondary(5, 10) → 10
    """
    return secondary_value


def prefer_non_null(
    primary_value: Any,
    secondary_value: Any,
    **kwargs
) -> Any:
    """
    Prefer non-null value (fallback logic)

    Args:
        primary_value: Value from primary provider
        secondary_value: Value from secondary provider
        **kwargs: Additional context (ignored)

    Returns:
        First non-null value (primary preferred)

    Example:
        prefer_non_null(None, 10) → 10
        prefer_non_null(5, 10) → 5
    """
    if primary_value is not None:
        return primary_value
    return secondary_value


# ========================================
# NUMERIC STRATEGIES
# ========================================

def average(
    primary_value: Any,
    secondary_value: Any,
    **kwargs
) -> float:
    """
    Average two numeric values

    Args:
        primary_value: Numeric value from primary provider
        secondary_value: Numeric value from secondary provider
        **kwargs: Additional context (ignored)

    Returns:
        Average of both values

    Raises:
        TypeError: If values are not numeric

    Example:
        average(5, 10) → 7.5
    """
    if primary_value is None:
        return secondary_value
    if secondary_value is None:
        return primary_value

    try:
        return (float(primary_value) + float(secondary_value)) / 2
    except (TypeError, ValueError):
        raise TypeError("Values must be numeric for average strategy")


def weighted_average(
    primary_value: Any,
    secondary_value: Any,
    primary_weight: float = 0.6,
    secondary_weight: float = 0.4,
    **kwargs
) -> float:
    """
    Weighted average of two numeric values

    Args:
        primary_value: Numeric value from primary provider
        secondary_value: Numeric value from secondary provider
        primary_weight: Weight for primary value (0.0 to 1.0)
        secondary_weight: Weight for secondary value (0.0 to 1.0)
        **kwargs: Additional context (ignored)

    Returns:
        Weighted average

    Example:
        weighted_average(10, 20, primary_weight=0.7, secondary_weight=0.3)
        → (10 * 0.7) + (20 * 0.3) = 13.0
    """
    if primary_value is None:
        return secondary_value
    if secondary_value is None:
        return primary_value

    try:
        return (float(primary_value) * primary_weight +
                float(secondary_value) * secondary_weight)
    except (TypeError, ValueError):
        raise TypeError("Values must be numeric for weighted_average strategy")


def average_with_threshold(
    primary_value: Any,
    secondary_value: Any,
    threshold: float = 5.0,
    action_if_exceeds: str = 'prefer_primary',
    **kwargs
) -> Any:
    """
    Average if values are close, otherwise use fallback action

    Args:
        primary_value: Numeric value from primary provider
        secondary_value: Numeric value from secondary provider
        threshold: Max difference to allow averaging
        action_if_exceeds: Action if difference exceeds threshold
                          ('prefer_primary', 'prefer_secondary', 'treat_as_different')
        **kwargs: Additional context

    Returns:
        Average if within threshold, otherwise fallback value

    Example:
        average_with_threshold(10, 12, threshold=5) → 11.0
        average_with_threshold(10, 20, threshold=5) → 10 (prefers primary)
    """
    if primary_value is None:
        return secondary_value
    if secondary_value is None:
        return primary_value

    try:
        diff = abs(float(primary_value) - float(secondary_value))

        if diff <= threshold:
            return (float(primary_value) + float(secondary_value)) / 2
        else:
            if action_if_exceeds == 'prefer_primary':
                return primary_value
            elif action_if_exceeds == 'prefer_secondary':
                return secondary_value
            elif action_if_exceeds == 'treat_as_different':
                # Signal that these should be treated as different events
                # Caller should handle this
                return None
            else:
                return primary_value

    except (TypeError, ValueError):
        raise TypeError("Values must be numeric for average_with_threshold strategy")


def prefer_higher(
    primary_value: Any,
    secondary_value: Any,
    **kwargs
) -> Any:
    """
    Prefer the higher numeric value

    Args:
        primary_value: Numeric value from primary provider
        secondary_value: Numeric value from secondary provider
        **kwargs: Additional context (ignored)

    Returns:
        Higher value

    Example:
        prefer_higher(5, 10) → 10
    """
    if primary_value is None:
        return secondary_value
    if secondary_value is None:
        return primary_value

    try:
        return max(float(primary_value), float(secondary_value))
    except (TypeError, ValueError):
        raise TypeError("Values must be numeric for prefer_higher strategy")


def prefer_lower(
    primary_value: Any,
    secondary_value: Any,
    **kwargs
) -> Any:
    """
    Prefer the lower numeric value

    Args:
        primary_value: Numeric value from primary provider
        secondary_value: Numeric value from secondary provider
        **kwargs: Additional context (ignored)

    Returns:
        Lower value

    Example:
        prefer_lower(5, 10) → 5
    """
    if primary_value is None:
        return secondary_value
    if secondary_value is None:
        return primary_value

    try:
        return min(float(primary_value), float(secondary_value))
    except (TypeError, ValueError):
        raise TypeError("Values must be numeric for prefer_lower strategy")


# ========================================
# COLLECTION STRATEGIES
# ========================================

def keep_both(
    primary_value: Any,
    secondary_value: Any,
    primary_provider: str = 'primary',
    secondary_provider: str = 'secondary',
    output_format: Optional[Dict] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Keep both values in a dict

    Args:
        primary_value: Value from primary provider
        secondary_value: Value from secondary provider
        primary_provider: Name of primary provider
        secondary_provider: Name of secondary provider
        output_format: Custom output format (optional)
        **kwargs: Additional context (ignored)

    Returns:
        Dict with both values

    Example:
        keep_both(5, 10, 'opta', 'statsbomb')
        → {'opta': 5, 'statsbomb': 10}

        With output_format:
        keep_both(2.3, 1.8, 'opta', 'statsbomb',
                 output_format={'xg': 'average', 'xg_opta': 'primary', 'xg_statsbomb': 'secondary'})
        → {'xg': 2.05, 'xg_opta': 2.3, 'xg_statsbomb': 1.8}
    """
    if output_format:
        result = {}
        for key, value_type in output_format.items():
            if value_type == 'primary':
                result[key] = primary_value
            elif value_type == 'secondary':
                result[key] = secondary_value
            elif value_type == 'average' or value_type == 'weighted_average':
                result[key] = average(primary_value, secondary_value)
            else:
                result[key] = primary_value
        return result
    else:
        return {
            primary_provider: primary_value,
            secondary_provider: secondary_value
        }


def union(
    primary_value: List[Any],
    secondary_value: List[Any],
    **kwargs
) -> List[Any]:
    """
    Union of two lists (unique elements from both)

    Args:
        primary_value: List from primary provider
        secondary_value: List from secondary provider
        **kwargs: Additional context (ignored)

    Returns:
        Combined list with unique elements

    Example:
        union([1, 2, 3], [2, 3, 4]) → [1, 2, 3, 4]
    """
    if not isinstance(primary_value, list):
        primary_value = [primary_value] if primary_value is not None else []
    if not isinstance(secondary_value, list):
        secondary_value = [secondary_value] if secondary_value is not None else []

    # Preserve order and remove duplicates
    result = list(primary_value)
    for item in secondary_value:
        if item not in result:
            result.append(item)

    return result


def intersection(
    primary_value: List[Any],
    secondary_value: List[Any],
    **kwargs
) -> List[Any]:
    """
    Intersection of two lists (common elements)

    Args:
        primary_value: List from primary provider
        secondary_value: List from secondary provider
        **kwargs: Additional context (ignored)

    Returns:
        List of common elements

    Example:
        intersection([1, 2, 3], [2, 3, 4]) → [2, 3]
    """
    if not isinstance(primary_value, list):
        primary_value = [primary_value] if primary_value is not None else []
    if not isinstance(secondary_value, list):
        secondary_value = [secondary_value] if secondary_value is not None else []

    return [item for item in primary_value if item in secondary_value]


def concatenate(
    primary_value: Any,
    secondary_value: Any,
    separator: str = ', ',
    **kwargs
) -> str:
    """
    Concatenate two string values

    Args:
        primary_value: String from primary provider
        secondary_value: String from secondary provider
        separator: Separator between values
        **kwargs: Additional context (ignored)

    Returns:
        Concatenated string

    Example:
        concatenate('Mo', 'Mohamed', separator=' / ') → 'Mo / Mohamed'
    """
    parts = []
    if primary_value is not None and str(primary_value).strip():
        parts.append(str(primary_value))
    if secondary_value is not None and str(secondary_value).strip():
        parts.append(str(secondary_value))

    return separator.join(parts)


# ========================================
# TEMPORAL STRATEGIES
# ========================================

def prefer_recent(
    primary_value: Any,
    secondary_value: Any,
    primary_timestamp: Optional[datetime] = None,
    secondary_timestamp: Optional[datetime] = None,
    **kwargs
) -> Any:
    """
    Prefer the more recent value based on timestamps

    Args:
        primary_value: Value from primary provider
        secondary_value: Value from secondary provider
        primary_timestamp: Timestamp of primary value
        secondary_timestamp: Timestamp of secondary value
        **kwargs: Additional context (ignored)

    Returns:
        Value from more recent source

    Example:
        prefer_recent(
            'Liverpool', 'Liverpool FC',
            primary_timestamp=datetime(2023, 1, 1),
            secondary_timestamp=datetime(2023, 6, 1)
        ) → 'Liverpool FC' (secondary is more recent)
    """
    if primary_timestamp is None or secondary_timestamp is None:
        return prefer_primary(primary_value, secondary_value)

    if secondary_timestamp > primary_timestamp:
        return secondary_value
    else:
        return primary_value


# ========================================
# QUALITY-BASED STRATEGIES
# ========================================

def prefer_comprehensive(
    primary_value: Any,
    secondary_value: Any,
    primary_quality: Optional[str] = None,
    secondary_quality: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Prefer value from more comprehensive data source

    Args:
        primary_value: Value from primary provider
        secondary_value: Value from secondary provider
        primary_quality: Quality level of primary ('MINIMAL', 'BASIC', 'COMPREHENSIVE', etc.)
        secondary_quality: Quality level of secondary
        **kwargs: Additional context (ignored)

    Returns:
        Value from more comprehensive source

    Example:
        prefer_comprehensive(
            5, 10,
            primary_quality='BASIC',
            secondary_quality='COMPREHENSIVE'
        ) → 10
    """
    quality_order = ['MINIMAL', 'BASIC', 'STANDARD', 'DETAILED', 'COMPREHENSIVE']

    primary_rank = quality_order.index(primary_quality) if primary_quality in quality_order else 0
    secondary_rank = quality_order.index(secondary_quality) if secondary_quality in quality_order else 0

    if secondary_rank > primary_rank:
        return secondary_value
    else:
        return primary_value


# ========================================
# CUSTOM STRATEGIES
# ========================================

def custom_merge(
    primary_value: Any,
    secondary_value: Any,
    merge_function: Callable[[Any, Any], Any],
    **kwargs
) -> Any:
    """
    Apply custom merge function

    Args:
        primary_value: Value from primary provider
        secondary_value: Value from secondary provider
        merge_function: Custom function that takes (primary, secondary) and returns merged value
        **kwargs: Additional context passed to merge_function

    Returns:
        Result of merge_function

    Example:
        def custom_player_merge(p, s):
            return {'name': p['name'], 'age': s['age']}

        custom_merge(
            {'name': 'Mo Salah', 'age': 30},
            {'name': 'Mohamed Salah', 'age': 31},
            merge_function=custom_player_merge
        ) → {'name': 'Mo Salah', 'age': 31}
    """
    return merge_function(primary_value, secondary_value, **kwargs)


# ========================================
# MULTI-VALUE STRATEGIES
# ========================================

def merge_multiple_values(
    values: List[Any],
    strategy: str,
    weights: Optional[List[float]] = None,
    **kwargs
) -> Any:
    """
    Merge multiple values (more than 2 providers) using specified strategy

    Args:
        values: List of values from different providers
        strategy: Strategy name ('average', 'median', 'weighted_average', 'prefer_first', etc.)
        weights: Weights for weighted strategies
        **kwargs: Additional context

    Returns:
        Merged value

    Example:
        merge_multiple_values([10, 12, 11], 'average') → 11.0
        merge_multiple_values([10, 20, 15], 'weighted_average', weights=[0.5, 0.3, 0.2]) → 13.5
    """
    # Remove None values
    values = [v for v in values if v is not None]

    if not values:
        return None

    if len(values) == 1:
        return values[0]

    if strategy == 'average':
        try:
            return mean([float(v) for v in values])
        except (TypeError, ValueError):
            return values[0]

    elif strategy == 'median':
        try:
            return median([float(v) for v in values])
        except (TypeError, ValueError):
            return values[0]

    elif strategy == 'weighted_average':
        if not weights or len(weights) != len(values):
            # Fall back to simple average
            return merge_multiple_values(values, 'average')

        try:
            total = sum(float(v) * w for v, w in zip(values, weights))
            return total
        except (TypeError, ValueError):
            return values[0]

    elif strategy == 'prefer_first':
        return values[0]

    elif strategy == 'prefer_last':
        return values[-1]

    elif strategy == 'prefer_highest':
        try:
            return max(float(v) for v in values)
        except (TypeError, ValueError):
            return values[0]

    elif strategy == 'prefer_lowest':
        try:
            return min(float(v) for v in values)
        except (TypeError, ValueError):
            return values[0]

    else:
        # Default: prefer first
        return values[0]


# ========================================
# STRATEGY REGISTRY
# ========================================

STRATEGY_REGISTRY: Dict[str, Callable] = {
    'prefer_primary': prefer_primary,
    'prefer_secondary': prefer_secondary,
    'prefer_non_null': prefer_non_null,
    'average': average,
    'weighted_average': weighted_average,
    'keep_both': keep_both,
    'prefer_recent': prefer_recent,
    'prefer_comprehensive': prefer_comprehensive,
    'prefer_higher': prefer_higher,
    'prefer_lower': prefer_lower,
    'concatenate': concatenate,
    'union': union,
    'intersection': intersection,
    'average_with_threshold': average_with_threshold,
    'custom': custom_merge,
}


def get_strategy(strategy_name: str) -> Callable:
    """
    Get strategy function by name

    Args:
        strategy_name: Name of strategy

    Returns:
        Strategy function

    Raises:
        ValueError: If strategy not found

    Example:
        strategy_fn = get_strategy('average')
        result = strategy_fn(10, 20) → 15.0
    """
    if strategy_name not in STRATEGY_REGISTRY:
        raise ValueError(
            f"Unknown strategy '{strategy_name}'. "
            f"Available strategies: {list(STRATEGY_REGISTRY.keys())}"
        )

    return STRATEGY_REGISTRY[strategy_name]
