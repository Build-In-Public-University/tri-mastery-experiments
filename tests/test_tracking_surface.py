import hashlib
import json

from tri_mastery_experiments.tracking import (
    aggregate_visits,
    build_tracking_instrument_seal,
    log_visit_event,
    normalize_visit_event,
    write_tracking_surface,
)


def test_twitter_funnel_prereg_seals_media_market_self_mastery_and_not_score_the_impression():
    seal = build_tracking_instrument_seal('tri-mastery-twitter-v1')
    body = seal['body']

    assert body['campaign_id'] == 'tri-mastery-twitter-v1'
    assert body['status'] == 'sealed_before_first_visit'
    assert set(body['known_slugs']) == {
        'tm-v1-null-duck',
        'tm-v1-receipt-loop',
        'tm-v1-alpha-conversations',
    }
    assert body['visit_definition']['counts_as_visit'] == 'http_request_to_known_slug_landing_or_redirect_route'
    assert body['visit_definition']['dedup_window_seconds'] == 86400
    assert body['visit_definition']['dedup_key'] == 'slug_plus_salted_ip_hash_plus_salted_user_agent_hash'
    assert body['visit_definition']['hashing_salt_policy'] == 'required_secret_runtime_env_not_stored_in_repo_or_events'
    assert body['storage_policy'] == 'raw_events_append_only_aggregates_derived_at_read_time'
    assert body['null_result_policy'] == 'compare_variant_rates_against_each_other_and_preregistered_predictions_not_industry_baselines'
    assert 'industry' in body['null_result_policy']
    assert 'metric_shopping' in body['denominator_warning']
    assert seal['sha256'] == hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def test_normalize_visit_strips_params_hashes_with_salt_and_flags_bots():
    seal = build_tracking_instrument_seal('tri-mastery-twitter-v1')
    event = normalize_visit_event(
        seal,
        {
            'slug': 'tm-v1-null-duck',
            'url': 'https://arc.metaspn.network/tm/tm-v1-null-duck?token=SECRET&utm_source=x&ref=leo&debug=1',
            'ip': '203.0.113.7',
            'user_agent': 'Twitterbot/1.0',
            'hash_salt': 'unit-test-salt',
            'ts': '2026-07-19T00:00:00+00:00',
        },
    )

    assert event['slug'] == 'tm-v1-null-duck'
    assert event['variant_id'] == 'V1-null-duck'
    assert event['normalized_url'] == 'https://arc.metaspn.network/tm/tm-v1-null-duck?ref=leo&utm_source=x'
    assert 'SECRET' not in json.dumps(event)
    assert event['ip_hash'] == hashlib.sha256('unit-test-salt\n203.0.113.7'.encode()).hexdigest()
    assert event['ip_hash'] != hashlib.sha256('203.0.113.7'.encode()).hexdigest()
    assert event['user_agent_hash'] == hashlib.sha256('unit-test-salt\nTwitterbot/1.0'.encode()).hexdigest()
    assert event['bot_flag'] is True
    assert event['counting_status'] == 'excluded_known_bot'
    assert 'hash_salt' not in event
    assert event['raw_event_retained'] is True


def test_log_raw_events_and_derive_aggregate_without_storing_only_cooked_counts(tmp_path):
    seal = build_tracking_instrument_seal('tri-mastery-twitter-v1')
    raw = tmp_path / 'raw_visit_events.jsonl'

    log_visit_event(
        seal,
        raw,
        {'slug': 'tm-v1-null-duck', 'url': 'https://x.test/a?utm_source=x', 'ip': '1.1.1.1', 'user_agent': 'Mozilla/5.0', 'hash_salt': 's'},
    )
    log_visit_event(
        seal,
        raw,
        {'slug': 'tm-v1-null-duck', 'url': 'https://x.test/a?utm_source=x', 'ip': '1.1.1.1', 'user_agent': 'Mozilla/5.0', 'hash_salt': 's'},
    )
    log_visit_event(
        seal,
        raw,
        {'slug': 'tm-v1-null-duck', 'url': 'https://x.test/a?utm_source=x', 'ip': '1.1.1.2', 'user_agent': 'Mozilla/5.0', 'hash_salt': 's'},
    )
    log_visit_event(
        seal,
        raw,
        {'slug': 'tm-v1-receipt-loop', 'url': 'https://x.test/b', 'ip': '2.2.2.2', 'user_agent': 'Googlebot', 'hash_salt': 's'},
    )

    lines = raw.read_text().splitlines()
    assert len(lines) == 4
    assert all(json.loads(line)['artifact'] == 'raw_visit_event' for line in lines)

    aggregate = aggregate_visits(seal, raw)
    assert aggregate['source'] == 'raw_visit_events_jsonl'
    assert aggregate['slugs']['tm-v1-null-duck']['raw_events'] == 3
    assert aggregate['slugs']['tm-v1-null-duck']['counted_unique_visits'] == 2
    assert aggregate['slugs']['tm-v1-receipt-loop']['raw_events'] == 1
    assert aggregate['slugs']['tm-v1-receipt-loop']['bot_excluded_events'] == 1
    assert aggregate['slugs']['tm-v1-receipt-loop']['counted_unique_visits'] == 0


def test_unknown_slug_rejected_before_logging(tmp_path):
    seal = build_tracking_instrument_seal('tri-mastery-twitter-v1')
    raw = tmp_path / 'raw_visit_events.jsonl'

    try:
        log_visit_event(seal, raw, {'slug': 'tm-v1-made-up', 'url': 'https://x.test', 'ip': '1', 'user_agent': 'Mozilla', 'hash_salt': 's'})
    except ValueError as exc:
        assert 'unknown slug' in str(exc)
    else:
        raise AssertionError('unknown slug should fail')

    assert not raw.exists()


def test_write_tracking_surface_manifest_hashes_everything(tmp_path):
    result = write_tracking_surface(tmp_path, 'tri-mastery-twitter-v1', include_demo_events=True)
    manifest = result['manifest']

    assert manifest['status'] == 'tracking_surface_sealed_no_live_visits'
    assert manifest['external_actions'] == {'analytics_called': False, 'deployed': False, 'posted_to_x': False}
    for meta in manifest['artifacts'].values():
        path = tmp_path / meta['path']
        assert path.exists()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == meta['sha256']
    seal = json.loads((tmp_path / 'tracking_instrument_seal.json').read_text())
    assert manifest['artifacts']['tracking_instrument_seal']['body_sha256'] == seal['sha256']
