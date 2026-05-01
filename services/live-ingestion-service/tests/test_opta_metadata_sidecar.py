from pathlib import Path
import sys

import pytest


SERVICES_ROOT = Path(__file__).resolve().parents[2]
if str(SERVICES_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICES_ROOT))


from ingestion.stream_processor import LiveDataProcessor


@pytest.mark.asyncio
async def test_process_live_update_loads_local_opta_metadata_sidecar(monkeypatch):
    processor = LiveDataProcessor(kafka_producer=None, bootstrap_servers='unused')
    materialize_calls = []

    async def fake_materialize(provider, match_id, documents):
        materialize_calls.append((provider, match_id, documents))
        return {'teams': 2, 'players': 0}

    async def fake_ensure_kafka():
        return False

    monkeypatch.setattr(processor.metadata_materializer, 'materialize', fake_materialize)
    monkeypatch.setattr(processor, '_ensure_kafka', fake_ensure_kafka)

    try:
        await processor.process_live_update(
            {
                'match_id': '935592',
                'source': 'opta',
                'events': [
                    {
                        '@attributes': {
                            'id': '1',
                            'event_id': '1',
                            'type_id': '1',
                            'team_id': '3073',
                            'outcome': '1',
                            'x': '50',
                            'y': '50',
                        }
                    }
                ],
            },
            source='opta',
        )
    finally:
        await processor.close()

    assert len(materialize_calls) == 1

    provider, match_id, documents = materialize_calls[0]
    assert provider == 'opta'
    assert match_id == '935592'
    assert len(documents) == 1

    teams = documents[0]['SoccerFeed']['SoccerDocument']['Team']
    assert {team['@attributes']['uID'] for team in teams} == {'t2134', 't3073'}
    assert {team['Name'] for team in teams} == {'Gençlerbirligi', 'Karabükspor'}