from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SLUGS = {
    'tm-v1-null-duck': 'V1-null-duck',
    'tm-v1-receipt-loop': 'V2-receipt-loop',
    'tm-v1-alpha-conversations': 'V3-alpha-in-conversations',
}
ALLOWED_PARAMS = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'ref'}
BOT_UA_MARKERS = [
    'bot',
    'crawler',
    'spider',
    'preview',
    'slurp',
    'facebookexternalhit',
    'slackbot',
    'twitterbot',
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha_obj(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _sha_with_salt(salt: str, text: str) -> str:
    if not salt:
        raise ValueError('hash_salt is required')
    return hashlib.sha256(f'{salt}\n{text}'.encode()).hexdigest()


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + '\n')


def _strip_params(url: str) -> str:
    parts = urlsplit(url)
    kept = sorted((k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k in ALLOWED_PARAMS)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(kept), ''))


def _is_bot(user_agent: str) -> bool:
    ua = (user_agent or '').lower()
    return any(marker in ua for marker in BOT_UA_MARKERS)


def build_tracking_instrument_seal(campaign_id: str) -> dict[str, Any]:
    body = {
        'campaign_id': campaign_id,
        'status': 'sealed_before_first_visit',
        'known_slugs': dict(SLUGS),
        'visit_definition': {
            'counts_as_visit': 'http_request_to_known_slug_landing_or_redirect_route',
            'dedup_window_seconds': 86400,
            'dedup_key': 'slug_plus_salted_ip_hash_plus_salted_user_agent_hash',
            'bot_filtering': 'conservative_known_bot_user_agent_filter_on_raw_events_retained',
            'param_stripping': 'strip_all_query_params_except_declared_utm_and_ref',
            'allowed_query_params': sorted(ALLOWED_PARAMS),
            'hashing_salt_policy': 'required_secret_runtime_env_not_stored_in_repo_or_events',
        },
        'storage_policy': 'raw_events_append_only_aggregates_derived_at_read_time',
        'null_result_policy': 'compare_variant_rates_against_each_other_and_preregistered_predictions_not_industry_baselines',
        'denominator_warning': 'post_hoc_denominator_adjustment_is_metric_shopping_with_extra_steps',
    }
    return {
        'artifact': 'tracking_instrument_semantics_seal',
        'sealed_at_utc': _now(),
        'body': body,
        'sha256': _sha_obj(body),
    }


def normalize_visit_event(seal: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    known_slugs = seal['body']['known_slugs']
    slug = event.get('slug')
    if slug not in known_slugs:
        raise ValueError(f'unknown slug: {slug}')
    user_agent = event.get('user_agent', '')
    salt = event.get('hash_salt', '')
    bot = _is_bot(user_agent)
    normalized = {
        'artifact': 'raw_visit_event',
        'tracking_seal_sha256': seal['sha256'],
        'ts': event.get('ts') or _now(),
        'slug': slug,
        'variant_id': known_slugs[slug],
        'normalized_url': _strip_params(event.get('url', '')),
        'ip_hash': _sha_with_salt(salt, event.get('ip', '')),
        'user_agent_hash': _sha_with_salt(salt, user_agent),
        'bot_flag': bot,
        'counting_status': 'excluded_known_bot' if bot else 'counted_candidate',
        'raw_event_retained': True,
    }
    normalized['event_hash'] = _sha_obj(normalized)
    return normalized


def log_visit_event(seal: dict[str, Any], path: str | Path, event: dict[str, Any]) -> dict[str, Any]:
    p = Path(path)
    normalized = normalize_visit_event(seal, event)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('a') as f:
        f.write(json.dumps(normalized, sort_keys=True, ensure_ascii=False) + '\n')
    return normalized


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def aggregate_visits(seal: dict[str, Any], path: str | Path) -> dict[str, Any]:
    events = _read_jsonl(Path(path))
    slugs: dict[str, dict[str, Any]] = {
        slug: {'variant_id': variant, 'raw_events': 0, 'bot_excluded_events': 0, 'counted_unique_visits': 0}
        for slug, variant in seal['body']['known_slugs'].items()
    }
    unique_keys: dict[str, set[tuple[str, str, str]]] = {slug: set() for slug in slugs}
    for event in events:
        slug = event['slug']
        if slug not in slugs:
            continue
        slugs[slug]['raw_events'] += 1
        if event.get('bot_flag'):
            slugs[slug]['bot_excluded_events'] += 1
            continue
        unique_keys[slug].add((slug, event['ip_hash'], event['user_agent_hash']))
    for slug, keys in unique_keys.items():
        slugs[slug]['counted_unique_visits'] = len(keys)
    return {
        'artifact': 'derived_visit_aggregate',
        'derived_at_utc': _now(),
        'source': 'raw_visit_events_jsonl',
        'tracking_seal_sha256': seal['sha256'],
        'definition': seal['body']['visit_definition'],
        'slugs': slugs,
    }


def _landing_html(slug: str, variant_id: str) -> str:
    return f'''<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>{slug}</title></head>
<body>
  <h1>{variant_id}</h1>
  <p>Local sealed tracking placeholder for {slug}.</p>
  <p>No external analytics are called by this static page.</p>
</body>
</html>
'''


def write_tracking_surface(out_dir: str | Path, campaign_id: str, include_demo_events: bool = False) -> dict[str, Any]:
    out = Path(out_dir)
    seal = build_tracking_instrument_seal(campaign_id)
    seal_path = out / 'tracking_instrument_seal.json'
    raw_path = out / 'raw_visit_events.jsonl'
    _write_json(seal_path, seal)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text('')
    for slug, variant in SLUGS.items():
        (out / 'public').mkdir(parents=True, exist_ok=True)
        (out / 'public' / f'{slug}.html').write_text(_landing_html(slug, variant))
    if include_demo_events:
        log_visit_event(seal, raw_path, {'slug': 'tm-v1-null-duck', 'url': 'https://example.test/tm-v1-null-duck?utm_source=demo&token=discarded', 'ip': '127.0.0.1', 'user_agent': 'Mozilla', 'hash_salt': 'demo-salt', 'ts': 'demo-1'})
        log_visit_event(seal, raw_path, {'slug': 'tm-v1-receipt-loop', 'url': 'https://example.test/tm-v1-receipt-loop', 'ip': '127.0.0.2', 'user_agent': 'Googlebot', 'hash_salt': 'demo-salt', 'ts': 'demo-2'})
    aggregate = aggregate_visits(seal, raw_path)
    aggregate_path = out / 'derived_visit_aggregate.json'
    _write_json(aggregate_path, aggregate)
    artifacts: dict[str, dict[str, str]] = {}
    for key, rel in [
        ('tracking_instrument_seal', 'tracking_instrument_seal.json'),
        ('raw_visit_events', 'raw_visit_events.jsonl'),
        ('derived_visit_aggregate', 'derived_visit_aggregate.json'),
        ('public_tm_v1_null_duck', 'public/tm-v1-null-duck.html'),
        ('public_tm_v1_receipt_loop', 'public/tm-v1-receipt-loop.html'),
        ('public_tm_v1_alpha_conversations', 'public/tm-v1-alpha-conversations.html'),
    ]:
        artifact_path = out / rel
        artifacts[key] = {'path': rel, 'sha256': hashlib.sha256(artifact_path.read_bytes()).hexdigest()}
    artifacts['tracking_instrument_seal']['body_sha256'] = seal['sha256']
    manifest = {
        'artifact': 'tracking_surface_manifest',
        'status': 'tracking_surface_sealed_no_live_visits',
        'created_at_utc': _now(),
        'campaign_id': campaign_id,
        'artifacts': artifacts,
        'external_actions': {'analytics_called': False, 'deployed': False, 'posted_to_x': False},
    }
    _write_json(out / 'manifest.json', manifest)
    return {'status': manifest['status'], 'manifest': manifest}
