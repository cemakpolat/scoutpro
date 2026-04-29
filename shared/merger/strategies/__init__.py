"""
Merge Strategies

Exports all merge strategy functions for resolving conflicts between providers.
"""

from .merge_strategies import (
    prefer_primary,
    prefer_secondary,
    average,
    weighted_average,
    keep_both,
    prefer_recent,
    prefer_comprehensive,
    prefer_higher,
    prefer_lower,
    concatenate,
    union,
    intersection,
    average_with_threshold,
    prefer_non_null,
    custom_merge
)

__all__ = [
    'prefer_primary',
    'prefer_secondary',
    'average',
    'weighted_average',
    'keep_both',
    'prefer_recent',
    'prefer_comprehensive',
    'prefer_higher',
    'prefer_lower',
    'concatenate',
    'union',
    'intersection',
    'average_with_threshold',
    'prefer_non_null',
    'custom_merge'
]
