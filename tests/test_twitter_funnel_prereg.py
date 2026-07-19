import hashlib
import json

from tri_mastery_experiments import build_twitter_funnel_prereg, write_twitter_funnel_prereg


def test_twitter_funnel_prereg_seals_media_market_self_mastery_and_not_score_impressions():
    prereg = build_twitter_funnel_prereg(campaign_id='tri-mastery-twitter-v1')
    body = prereg['body']
    assert prereg['artifact'] == 'twitter_funnel_conversion_retention_preregistration'
    assert prereg['sha256'] == hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    assert body['status'] == 'sealed_before_first_post'
    assert body['scoring_hygiene']['impressions'] == 'trial_allocation_context_never_score'
    assert body['tri_mastery_mapping']['media_mastery'] == 'impression_to_visit_and_register_adoption'
    assert body['tri_mastery_mapping']['market_mastery'] == 'visit_to_paid_trial_to_retained_subscription'
    assert body['tri_mastery_mapping']['self_mastery'] == 'pre_registered_rate_predictions_vs_actuals'
    assert body['fixed_points']['t30']['primary'] == 'retained_trial_value_and_register_adoption'
    assert body['fixed_points']['t60']['secondary'] == 'durable_artifacts_and_delayed_adoption'


def test_variants_are_tagged_and_have_predicted_stage_rates():
    body = build_twitter_funnel_prereg('tri-mastery-twitter-v1')['body']
    variants = body['variants']
    assert {v['variant_id'] for v in variants} == {'V1-null-duck', 'V2-receipt-loop', 'V3-alpha-in-conversations'}
    for variant in variants:
        assert variant['link_slug'].startswith('tm-v1-')
        assert len(variant['content_hash']) == 64
        rates = variant['predicted_rates']
        assert rates['impression_to_visit'] > 0
        assert rates['visit_to_paid_trial'] > 0
        assert rates['paid_trial_to_30d_usage_probe'] > 0
        assert rates['probe_to_continuation_call'] > 0
        assert rates['call_to_retained_subscription'] > 0


def test_funnel_boundaries_and_residuals_keep_sale_trial_and_retention_separate():
    body = build_twitter_funnel_prereg('tri-mastery-twitter-v1')['body']
    boundaries = body['funnel_boundaries']
    assert boundaries['impression_to_visit']['first_self_measured_denominator'] == 'visits'
    assert boundaries['visit_to_paid_trial']['trial_price_usd'] == 42
    assert boundaries['paid_trial_to_30d_usage_probe']['purchase_is'] == 'trial_allocation_not_settlement'
    assert boundaries['retained_subscription']['canonical_status'] == 'subscriber_admitted_after_verification_artifact'
    assert body['outcomes']['primary_settlement'] == 'retained_sale_at_t30_not_gross_sale'
    assert body['residual_classes'] == [
        'saw_no_click',
        'clicked_no_buy',
        'bought_never_onboarded',
        'onboarded_never_used',
        'used_declined_call',
        'called_and_passed',
        'subscribed_then_churned',
    ]


def test_30_day_call_gate_is_research_primary_and_receipt_confronted():
    body = build_twitter_funnel_prereg('tri-mastery-twitter-v1')['body']
    call = body['thirty_day_call_protocol']
    assert call['first_n_calls']['mode'] == 'research_primary_continuation_recorded_not_optimized'
    assert call['first_n_calls']['n'] == 20
    assert call['bring_receipts'] == 'pull_30_day_usage_before_call_declared_vs_verified_comparison'
    assert call['admission_rule']['evidence_outranks_performance'] is True
    assert call['admission_rule']['strong_usage_poor_narration'] == 'can_pass'
    assert call['admission_rule']['weak_usage_charismatic_narration'] == 'cannot_pass_without_exception_log'
    assert call['exception_policy'] == 'hash_logged_reason_required_when_admitting_below_bar'


def test_register_adoption_sidecar_and_exit_exchange_are_declared():
    body = build_twitter_funnel_prereg('tri-mastery-twitter-v1')['body']
    assert body['register_adoption']['minted_terms'] == ['null duck', 'receipt loop', 'alpha in conversations']
    assert body['register_adoption']['score'] == 'uses_by_accounts_never_interacted_with_application_not_quotation'
    assert body['durable_artifacts']['score'] == 'repos_posts_projects_downstream_that_cite_or_build_on_frame'
    assert body['exit_exchange']['questions'] == ['what_did_you_hope_it_was', 'what_was_it_instead']
    assert body['survivorship_bias_guard'] == 'rejected_and_self_selected_out_users_are_miss_log_not_trash'


def test_write_prereg_outputs_manifest_with_matching_hashes(tmp_path):
    result = write_twitter_funnel_prereg(tmp_path, campaign_id='tri-mastery-twitter-v1')
    assert (tmp_path / 'twitter_funnel_prereg.json').exists()
    assert (tmp_path / 'manifest.json').exists()
    manifest = json.loads((tmp_path / 'manifest.json').read_text())
    prereg = json.loads((tmp_path / 'twitter_funnel_prereg.json').read_text())
    assert manifest['status'] == 'sealed_before_first_post'
    assert manifest['artifacts']['twitter_funnel_prereg']['sha256'] == hashlib.sha256((tmp_path / 'twitter_funnel_prereg.json').read_bytes()).hexdigest()
    assert manifest['artifacts']['twitter_funnel_prereg']['body_sha256'] == prereg['sha256']
    assert result['status'] == 'sealed_before_first_post'
