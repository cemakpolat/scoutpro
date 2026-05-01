"""
Admin and discovery router for the provider server mock.
"""

from fastapi import APIRouter

from loaders.opta_loader import list_competitions
from loaders.statsbomb_loader import list_matches
from config import DATA_ROOT

router = APIRouter(tags=["Admin"])


@router.get("/health", summary="Health check")
def health():
    return {"status": "ok", "service": "data-provider-mock"}


@router.get("/feeds", summary="Catalogue of all locally available feeds")
def list_feeds():
    """
    Returns a full catalogue of Opta and StatsBomb data available on disk.
    Use this endpoint to discover competition/season/match IDs before making
    feed requests.
    """
    opta = list_competitions()
    statsbomb = list_matches()

    return {
        "data_root": str(DATA_ROOT),
        "opta": {
            "competitions": opta,
            "total_matches": sum(c["match_count"] for c in opta),
        },
        "statsbomb": {
            "matches": statsbomb,
            "total_matches": len(statsbomb),
        },
    }
