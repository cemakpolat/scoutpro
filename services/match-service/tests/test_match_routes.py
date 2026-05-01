from datetime import datetime
from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient


SERVICE_ROOT = Path(__file__).resolve().parents[1]
SERVICES_ROOT = SERVICE_ROOT.parent

for path in (SERVICE_ROOT, SERVICES_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


from api.matches import router  # noqa: E402
from dependencies import get_match_service  # noqa: E402


class StubMatch:
    def __init__(self, match_id: str, status: str = "scheduled"):
        self.match_id = match_id
        self.status = status

    def dict(self):
        return {
            "id": self.match_id,
            "home_team_id": "996",
            "away_team_id": "6468",
            "home_score": 0,
            "away_score": 0,
            "date": "2026-04-29T12:43:13.431763+00:00",
            "status": self.status,
        }


class StubMatchService:
    def __init__(self):
        self.calls = []

    async def list_matches(self, filters, limit):
        self.calls.append(("list_matches", filters, limit))
        return []

    async def get_team_matches(self, team_id, limit):
        self.calls.append(("get_team_matches", team_id, limit))
        return []

    async def get_live_matches(self):
        self.calls.append(("get_live_matches",))
        return [StubMatch("live-3946949", status="live")]

    async def get_matches_by_date_range(self, start_date, end_date, limit):
        self.calls.append(("get_matches_by_date_range", start_date, end_date, limit))
        return [StubMatch("range-3946949", status="finished")]

    async def get_match(self, match_id):
        self.calls.append(("get_match", match_id))
        return StubMatch(match_id, status="finished")

    async def get_match_events(self, match_id):
        self.calls.append(("get_match_events", match_id))
        return [{"type": "pass"}]


def build_client(service: StubMatchService) -> TestClient:
    app = FastAPI()
    app.dependency_overrides[get_match_service] = lambda: service
    app.include_router(router)
    return TestClient(app)


def test_live_route_resolves_before_dynamic_match_id():
    service = StubMatchService()
    client = build_client(service)

    response = client.get("/api/v2/matches/live")

    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == "live-3946949"
    assert service.calls == [("get_live_matches",)]


def test_date_range_route_resolves_before_dynamic_match_id():
    service = StubMatchService()
    client = build_client(service)

    response = client.get(
        "/api/v2/matches/date-range",
        params={
            "start_date": datetime(2026, 4, 1).isoformat(),
            "end_date": datetime(2026, 4, 30).isoformat(),
            "limit": 5,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == "range-3946949"
    assert service.calls[0][0] == "get_matches_by_date_range"
    assert all(call[0] != "get_match" for call in service.calls)


def test_dynamic_match_route_still_returns_match_by_id():
    service = StubMatchService()
    client = build_client(service)

    response = client.get("/api/v2/matches/3946949")

    assert response.status_code == 200
    assert response.json()["data"]["id"] == "3946949"
    assert service.calls == [("get_match", "3946949")]