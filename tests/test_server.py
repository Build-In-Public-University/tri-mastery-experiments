from pathlib import Path

from fastapi.testclient import TestClient

from tri_mastery_experiments.server import create_app


def test_tracking_server_health_and_aggregate_start_empty(tmp_path):
    app = create_app(data_dir=tmp_path, hash_salt='unit-test-salt')
    with TestClient(app) as client:
        health = client.get('/health')
        assert health.status_code == 200
        assert health.json()['ok'] is True
        assert health.json()['tracking_status'] == 'sealed_before_first_visit'
        assert health.json()['hash_salt_configured'] is True
        aggregate = client.get('/aggregate')
        assert aggregate.status_code == 200
        payload = aggregate.json()
        assert payload['artifact'] == 'derived_visit_aggregate'
        assert payload['slugs']['tm-v1-null-duck']['counted_unique_visits'] == 0


def test_slug_route_logs_raw_event_and_renders_without_external_analytics(tmp_path):
    app = create_app(data_dir=tmp_path, hash_salt='unit-test-salt')
    with TestClient(app) as client:
        response = client.get(
            '/tm-v1-null-duck?utm_source=x&token=discarded&ref=leo',
            headers={'user-agent': 'Mozilla/5.0', 'x-forwarded-for': '203.0.113.9'},
        )
        assert response.status_code == 200
        assert 'V1-null-duck' in response.text
        assert 'No external analytics' in response.text
        count = client.get('/raw-events/count').json()
        assert count['raw_event_count'] == 1
        aggregate = client.get('/aggregate').json()
        assert aggregate['slugs']['tm-v1-null-duck']['raw_events'] == 1
        assert aggregate['slugs']['tm-v1-null-duck']['counted_unique_visits'] == 1


def test_slug_route_excludes_known_bot_from_count_but_retains_raw(tmp_path):
    app = create_app(data_dir=tmp_path, hash_salt='unit-test-salt')
    with TestClient(app) as client:
        response = client.get('/tm-v1-receipt-loop', headers={'user-agent': 'Googlebot', 'x-forwarded-for': '203.0.113.10'})
        assert response.status_code == 200
        assert client.get('/raw-events/count').json()['raw_event_count'] == 1
        aggregate = client.get('/aggregate').json()
        assert aggregate['slugs']['tm-v1-receipt-loop']['raw_events'] == 1
        assert aggregate['slugs']['tm-v1-receipt-loop']['bot_excluded_events'] == 1
        assert aggregate['slugs']['tm-v1-receipt-loop']['counted_unique_visits'] == 0


def test_unknown_slug_404_and_does_not_log(tmp_path):
    app = create_app(data_dir=tmp_path, hash_salt='unit-test-salt')
    with TestClient(app) as client:
        response = client.get('/unknown')
        assert response.status_code == 404
        assert client.get('/raw-events/count').json()['raw_event_count'] == 0
