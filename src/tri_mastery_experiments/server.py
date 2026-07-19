from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse

from .tracking import SLUGS, aggregate_visits, build_tracking_instrument_seal, log_visit_event

CAMPAIGN_ID = os.environ.get('TRI_MASTERY_CAMPAIGN_ID', 'tri-mastery-twitter-v1')
DEFAULT_DATA_DIR = Path(os.environ.get('TRI_MASTERY_DATA_DIR', Path(__file__).resolve().parents[2] / 'data' / 'tracking'))
PUBLIC_BASE_URL = os.environ.get('TRI_MASTERY_PUBLIC_BASE_URL', 'https://arc.metaspn.network/tm').rstrip('/')
HASH_SALT = os.environ.get('TRI_MASTERY_HASH_SALT', '')


def _html(slug: str, variant_id: str) -> str:
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{variant_id}</title>
  <style>
    body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; background: #0d0f14; color: #e8e4d8; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
    main {{ max-width: 760px; padding: 40px; }}
    .slug {{ color: #9aa4ff; }}
    .warning {{ color: #a8a29e; font-size: 14px; }}
    a {{ color: #ffd166; }}
  </style>
</head>
<body>
  <main>
    <p class="slug">{slug}</p>
    <h1>{variant_id}</h1>
    <p>This is the sealed tracking landing surface for the tri-mastery funnel experiment.</p>
    <p class="warning">No external analytics are called by this page. Raw visits are append-only; aggregates are derived at read time.</p>
  </main>
</body>
</html>
'''


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get('x-forwarded-for', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.client.host if request.client else ''


def _event_url(request: Request, slug: str) -> str:
    query = str(request.url.query)
    url = f'{PUBLIC_BASE_URL}/{slug}'
    return f'{url}?{query}' if query else url


def create_app(data_dir: str | Path | None = None, hash_salt: str | None = None) -> FastAPI:
    runtime_hash_salt = HASH_SALT if hash_salt is None else hash_salt
    data = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    data.mkdir(parents=True, exist_ok=True)
    seal = build_tracking_instrument_seal(CAMPAIGN_ID)
    raw_path = data / 'raw_visit_events.jsonl'
    seal_path = data / 'tracking_instrument_seal.json'
    if not seal_path.exists():
        seal_path.write_text(__import__('json').dumps(seal, indent=2, sort_keys=True, ensure_ascii=False) + '\n')
    raw_path.touch(exist_ok=True)

    app = FastAPI(title='Tri-Mastery Tracking Endpoint', version='0.1.0')

    @app.get('/health')
    def health() -> dict[str, object]:
        return {
            'ok': True,
            'campaign_id': CAMPAIGN_ID,
            'tracking_status': seal['body']['status'],
            'tracking_seal_sha256': seal['sha256'],
            'known_slugs': sorted(SLUGS),
            'hash_salt_configured': bool(runtime_hash_salt),
        }

    @app.get('/aggregate')
    def aggregate() -> dict[str, object]:
        return aggregate_visits(seal, raw_path)

    @app.get('/raw-events/count')
    def raw_count() -> dict[str, int]:
        if not raw_path.exists():
            return {'raw_event_count': 0}
        return {'raw_event_count': len([line for line in raw_path.read_text().splitlines() if line.strip()])}

    @app.get('/{slug}', response_class=HTMLResponse)
    def slug_landing(slug: str, request: Request) -> HTMLResponse:
        if slug not in SLUGS:
            raise HTTPException(status_code=404, detail='unknown slug')
        log_visit_event(
            seal,
            raw_path,
            {
                'slug': slug,
                'url': _event_url(request, slug),
                'ip': _client_ip(request),
                'user_agent': request.headers.get('user-agent', ''),
                'hash_salt': runtime_hash_salt,
                'ts': None,
            },
        )
        return HTMLResponse(_html(slug, SLUGS[slug]))

    return app


app = create_app()
