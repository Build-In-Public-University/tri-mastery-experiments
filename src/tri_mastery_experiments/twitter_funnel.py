from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _variant(variant_id: str, link_slug: str, hook: str, predicted_rates: dict[str, float]) -> dict[str, Any]:
    return {
        'variant_id': variant_id,
        'link_slug': link_slug,
        'hook': hook,
        'content_hash': _content_hash(hook),
        'predicted_rates': predicted_rates,
    }


def build_twitter_funnel_prereg(campaign_id: str) -> dict[str, Any]:
    body = {
        'campaign_id': campaign_id,
        'status': 'sealed_before_first_post',
        'scope': 'twitter_x_content_to_paid_trial_to_30_day_usage_probe_to_continuation_call_to_retained_subscription',
        'tri_mastery_mapping': {
            'media_mastery': 'impression_to_visit_and_register_adoption',
            'market_mastery': 'visit_to_paid_trial_to_retained_subscription',
            'self_mastery': 'pre_registered_rate_predictions_vs_actuals',
        },
        'scoring_hygiene': {
            'impressions': 'trial_allocation_context_never_score',
            'visits': 'first_self_measured_denominator',
            'gross_sales': 'trial_allocation_not_value_settlement',
            'retained_sale': 'canonical_value_settlement_at_t30',
        },
        'fixed_points': {
            't30': {
                'primary': 'retained_trial_value_and_register_adoption',
                'forbidden_before': 'no value claim, no conversion victory, no retention claim',
            },
            't60': {
                'secondary': 'durable_artifacts_and_delayed_adoption',
                'forbidden_before': 'no slow-media-installation claim',
            },
        },
        'variants': [
            _variant(
                'V1-null-duck',
                'tm-v1-null-duck',
                'A null duck is the baseline you keep in the room so your clever system has something honest to beat.',
                {
                    'impression_to_visit': 0.012,
                    'visit_to_paid_trial': 0.035,
                    'paid_trial_to_30d_usage_probe': 0.55,
                    'probe_to_continuation_call': 0.45,
                    'call_to_retained_subscription': 0.35,
                },
            ),
            _variant(
                'V2-receipt-loop',
                'tm-v1-receipt-loop',
                'A receipt loop is what happens when every claim has to come home carrying an outcome.',
                {
                    'impression_to_visit': 0.010,
                    'visit_to_paid_trial': 0.04,
                    'paid_trial_to_30d_usage_probe': 0.60,
                    'probe_to_continuation_call': 0.50,
                    'call_to_retained_subscription': 0.40,
                },
            ),
            _variant(
                'V3-alpha-in-conversations',
                'tm-v1-alpha-conversations',
                'The alpha is in conversations now so it can be in the artifact later.',
                {
                    'impression_to_visit': 0.009,
                    'visit_to_paid_trial': 0.045,
                    'paid_trial_to_30d_usage_probe': 0.62,
                    'probe_to_continuation_call': 0.55,
                    'call_to_retained_subscription': 0.45,
                },
            ),
        ],
        'funnel_boundaries': {
            'impression_to_visit': {
                'instrument': 'platform impressions plus first-party link slug visits',
                'first_self_measured_denominator': 'visits',
                'residual': 'saw_no_click means hook may transfer but promise did not',
            },
            'visit_to_paid_trial': {
                'trial_price_usd': 42,
                'purchase_is': 'costly_signal_filter_for_trial_allocation',
                'residual': 'clicked_no_buy means promise transferred but value claim failed probe',
            },
            'paid_trial_to_30d_usage_probe': {
                'purchase_is': 'trial_allocation_not_settlement',
                'probe_window_days': 30,
                'residual': 'bought_never_onboarded_or_onboarded_never_used',
            },
            'probe_to_continuation_call': {
                'call_is': 'verification_artifact_boundary_pair',
                'residual': 'used_declined_call',
            },
            'retained_subscription': {
                'canonical_status': 'subscriber_admitted_after_verification_artifact',
                'residual': 'called_and_passed_or_subscribed_then_churned',
            },
        },
        'outcomes': {
            'primary_settlement': 'retained_sale_at_t30_not_gross_sale',
            'usage_receipts': ['logins_or_sessions', 'core_actions', 'artifacts_created', 'declared_value_claim'],
            'retention_definition': 'subscription_continues_after_customer_case_and_assayer_review',
        },
        'thirty_day_call_protocol': {
            'first_n_calls': {'n': 20, 'mode': 'research_primary_continuation_recorded_not_optimized'},
            'bring_receipts': 'pull_30_day_usage_before_call_declared_vs_verified_comparison',
            'primary_function': 'assayer_session_collect_evidence_about_value_claim',
            'secondary_function': 'continuation_decision_recorded_but_not_optimized_in_first_n',
            'semi_structured_questions': [
                'what_did_you_think_you_were_buying',
                'what_did_you_actually_use_it_for',
                'what_outcome_mattered',
                'what_confused_you_into_silence',
                'what_words_would_you_use_to_describe_it',
                'make_the_case_for_or_against_continuing',
            ],
            'admission_rule': {
                'evidence_outranks_performance': True,
                'strong_usage_poor_narration': 'can_pass',
                'weak_usage_charismatic_narration': 'cannot_pass_without_exception_log',
            },
            'exception_policy': 'hash_logged_reason_required_when_admitting_below_bar',
            'recording_policy': 'record_with_consent_or_write_structured_notes_if_not_recorded',
        },
        'register_adoption': {
            'minted_terms': ['null duck', 'receipt loop', 'alpha in conversations'],
            'score': 'uses_by_accounts_never_interacted_with_application_not_quotation',
            'settlement_times': ['T+30', 'T+60'],
        },
        'generative_probe_passes': {
            'score': 'strangers_applying_frame_to_material_we_never_touched',
            'examples': ['someone calls their own baseline a null duck', 'someone publishes their own miss log'],
        },
        'durable_artifacts': {
            'score': 'repos_posts_projects_downstream_that_cite_or_build_on_frame',
            'settlement': 'T+60_secondary_slow_loop',
        },
        'residual_classes': [
            'saw_no_click',
            'clicked_no_buy',
            'bought_never_onboarded',
            'onboarded_never_used',
            'used_declined_call',
            'called_and_passed',
            'subscribed_then_churned',
        ],
        'exit_exchange': {
            'audience': 'bought_and_did_not_continue_or_self_selected_out_after_trial',
            'questions': ['what_did_you_hope_it_was', 'what_was_it_instead'],
        },
        'survivorship_bias_guard': 'rejected_and_self_selected_out_users_are_miss_log_not_trash',
        'distillation_threshold': {
            'target': 'self_serve_threshold_or_async_checkin_reaches_80_percent_of_call_driven_continuation_quality',
            'warning': 'ceremony_may_be_load_bearing_do_not_automate_away_without_evidence',
        },
        'forbidden_claims_before_settlement': [
            'impressions_as_success',
            'gross_sales_as_value_proof',
            'call_close_rate_as_research_success',
            'subscriber_count_without_admission_receipts',
        ],
    }
    return {
        'artifact': 'twitter_funnel_conversion_retention_preregistration',
        'sealed_at_utc': _now(),
        'body': body,
        'sha256': _sha(body),
    }


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + '\n')


def write_twitter_funnel_prereg(out_dir: str | Path, campaign_id: str) -> dict[str, Any]:
    out = Path(out_dir)
    prereg = build_twitter_funnel_prereg(campaign_id)
    prereg_path = out / 'twitter_funnel_prereg.json'
    _write_json(prereg_path, prereg)
    manifest = {
        'artifact': 'tri_mastery_experiment_manifest',
        'status': 'sealed_before_first_post',
        'created_at_utc': _now(),
        'artifacts': {
            'twitter_funnel_prereg': {
                'path': 'twitter_funnel_prereg.json',
                'sha256': hashlib.sha256(prereg_path.read_bytes()).hexdigest(),
                'body_sha256': prereg['sha256'],
            }
        },
        'external_actions': {
            'posted_to_x': False,
            'payment_link_created_or_modified': False,
            'analytics_called': False,
        },
    }
    _write_json(out / 'manifest.json', manifest)
    return {'status': manifest['status'], 'manifest': manifest}
