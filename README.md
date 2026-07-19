# Tri-Mastery Experiments

Hash-sealed preregistrations for media, market, and self-mastery loops.

No external posting has happened from this repo. The current artifact is a preregistration, not a launch receipt.

## Twitter Funnel V1

Artifacts:

```text
artifacts/twitter-funnel-v1/twitter_funnel_prereg.json
artifacts/twitter-funnel-v1/manifest.json
```

Status:

```text
sealed_before_first_post
```

Body hash:

```text
3484c02e3ce555ed1bfd3642db923742bdf8f73ea64dbd89281e65eb7781d2de
```

Variants:

```text
V1-null-duck
V2-receipt-loop
V3-alpha-in-conversations
```

Tri-mastery mapping:

```text
media_mastery: impression_to_visit_and_register_adoption
market_mastery: visit_to_paid_trial_to_retained_subscription
self_mastery: pre_registered_rate_predictions_vs_actuals
```

Scoring hygiene:

```text
impressions: trial_allocation_context_never_score
visits: first_self_measured_denominator
gross_sales: trial_allocation_not_value_settlement
retained_sale: canonical_value_settlement_at_t30
```

Fixed points:

```text
T+30 primary: retained_trial_value_and_register_adoption
T+60 secondary: durable_artifacts_and_delayed_adoption
```

Core rule:

```text
The $42 purchase is trial allocation, not settlement.
The 30-day usage window is the probe.
The continuation call is the verification artifact.
Subscription is canonical status only after admission by evidence.
```

Call hygiene:

```text
first 20 calls: research_primary_continuation_recorded_not_optimized
bring receipts: 30-day usage before call
evidence outranks performance
strong usage + poor narration can pass
weak usage + charismatic narration cannot pass without exception log
```

Residual classes:

```text
saw_no_click
clicked_no_buy
bought_never_onboarded
onboarded_never_used
used_declined_call
called_and_passed
subscribed_then_churned
```

Register adoption sidecar:

```text
minted_terms: null duck, receipt loop, alpha in conversations
score: uses by accounts never interacted with; application, not quotation
settlement: T+30 and T+60
```

Exit exchange:

```text
what_did_you_hope_it_was
what_was_it_instead
```

Forbidden before settlement:

```text
impressions_as_success
gross_sales_as_value_proof
call_close_rate_as_research_success
subscriber_count_without_admission_receipts
```

## Verification

```bash
python3 -m pytest tests -q
```

Current result:

```text
6 passed
```

## Tracking Surface V1

Artifacts:

```text
artifacts/tracking-surface-v1/tracking_instrument_seal.json
artifacts/tracking-surface-v1/raw_visit_events.jsonl
artifacts/tracking-surface-v1/derived_visit_aggregate.json
artifacts/tracking-surface-v1/manifest.json
artifacts/tracking-surface-v1/public/tm-v1-null-duck.html
artifacts/tracking-surface-v1/public/tm-v1-receipt-loop.html
artifacts/tracking-surface-v1/public/tm-v1-alpha-conversations.html
```

Status:

```text
tracking_surface_sealed_no_live_visits
```

Instrument semantics hash:

```text
c543c7a0b79a1d1f6feab2c9b4491227aff4894a218980ae4b0d86f66ce9be32
```

Known slugs:

```text
tm-v1-null-duck -> V1-null-duck
tm-v1-receipt-loop -> V2-receipt-loop
tm-v1-alpha-conversations -> V3-alpha-in-conversations
```

Visit definition, sealed before live visits:

```text
counts_as_visit: http_request_to_known_slug_landing_or_redirect_route
dedup_window_seconds: 86400
dedup_key: slug_plus_ip_hash_plus_user_agent_hash
bot_filtering: conservative_known_bot_user_agent_filter_on_raw_events_retained
param_stripping: strip_all_query_params_except_declared_utm_and_ref
```

Storage policy:

```text
raw_events_append_only_aggregates_derived_at_read_time
```

Null result policy:

```text
compare_variant_rates_against_each_other_and_preregistered_predictions_not_industry_baselines
```

External actions:

```text
analytics_called: false
deployed: false
posted_to_x: false
```

Demo events are included only to prove aggregation behavior. They are not live visits and not evidence of audience response.

## Verification

```bash
python3 -m pytest tests -q
```

Current result:

```text
15 passed
```

## VPS Deployment Receipt

Artifact:

```text
artifacts/tracking-deployment-vps/deployment_receipt.json
```

Status:

```text
deployed_verified_public_https
```

Public base URL:

```text
https://arc.metaspn.network/tm
```

Public URLs:

```text
health: https://arc.metaspn.network/tm/health
aggregate: https://arc.metaspn.network/tm/aggregate
raw_count: https://arc.metaspn.network/tm/raw-events/count
V1-null-duck: https://arc.metaspn.network/tm/tm-v1-null-duck
V2-receipt-loop: https://arc.metaspn.network/tm/tm-v1-receipt-loop
V3-alpha-in-conversations: https://arc.metaspn.network/tm/tm-v1-alpha-conversations
```

VPS:

```text
host alias: arc-vps
app dir: /opt/tri-mastery-tracking
systemd: tri-mastery-tracking.service
port: 127.0.0.1:8830
```

Deployment receipt hash:

```text
029af342322b5602fac26db1de2a11cd40021b41ad2c29c4566b0bee966b5581
```

Smoke:

```text
public health OK
bot-like slug visit retained raw
bot-like slug visit excluded from counted audience visits
```

External actions:

```text
deployed: true
posted_to_x: false
external_analytics_called: false
payment_link_created_or_modified: false
```

Nginx note:

```text
arc.metaspn.network had divergent sites-available and sites-enabled files; nginx was reading sites-enabled. Patched the enabled file and backed up under /root/nginx-backups.
```

## VPS Hardening Receipt

Artifact:

```text
artifacts/tracking-deployment-vps/hardening_receipt.json
artifacts/tracking-deployment-vps/hardening_manifest.json
```

Status:

```text
deployed_hardened_verified_public_https
```

Current tracking seal:

```text
11d9e9b0be08a8a1fc6d5dc3a1e8cc2012bfce04c8404488b435664d48ea00cc
```

Changes since initial deployment:

```text
salted ip_hash/user_agent_hash enforced
TRI_MASTERY_HASH_SALT stored in VPS .env only
pre-salt smoke-only raw log archived and reset before real visitors
positive-path smoke verified
crawler gauntlet verified
nginx sites-enabled reconciled to sites-available symlink
active nginx config hash recorded
off-box nightly raw-event backup scheduled
```

Positive-path smoke:

```text
human-like same fingerprint twice inside dedup window: counted_unique_visits stayed 1
human-like different fingerprint: counted_unique_visits became 2
```

Crawler gauntlet:

```text
Twitterbot
facebookexternalhit
Slackbot-LinkExpanding
Googlebot
```

Result:

```text
raw retained
counted_unique_visits unchanged at 0 for bot slug
```

Nginx:

```text
sites-enabled target: /etc/nginx/sites-available/arc.metaspn.network
active config sha256: d107608a9ac8b77f3480d3dabdbaf357b951eb343036cf74736529d922c44572
backups: /root/nginx-backups
```

Off-box raw backup:

```text
script: /Users/leoguinan/.hermes/scripts/backup_tri_mastery_tracking.sh
cron job: 4384fcb28dd3
schedule: 0 3 * * * local-only
latest backup sha256: 8e996af14dfe9b3fda110d695e256edec306f48b592f0d6418e2d27246cfda39
```

External actions still absent:

```text
posted_to_x: false
external_analytics_called: false
payment_link_created_or_modified: false
```

