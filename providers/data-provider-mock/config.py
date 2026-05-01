"""
Configuration for the provider server mock.

DATA_ROOT resolves to the project's data/ folder. When running inside Docker
the volume is mounted at /app/data; outside Docker it walks up from this file's
location to find the repository root.
"""

import os
from pathlib import Path


def _find_data_root() -> Path:
    """Locate the data/ directory whether running locally or in Docker."""
    env_path = os.getenv("DATA_ROOT")
    if env_path:
        return Path(env_path)

    here = Path(__file__).resolve().parent
    for ancestor in [here, *here.parents]:
        candidate = ancestor / "data"
        if candidate.is_dir():
            return candidate

    raise RuntimeError(
        "Cannot locate data/ directory. "
        "Set the DATA_ROOT environment variable to its absolute path."
    )


DATA_ROOT: Path = _find_data_root()
OPTA_ROOT: Path = DATA_ROOT / "opta"
STATSBOMB_ROOT: Path = DATA_ROOT / "statsbomb"

DEFAULT_COMPETITION_ID = "115"
DEFAULT_SEASON_ID = "2019"
PORT = int(os.getenv("PORT", "7000"))
