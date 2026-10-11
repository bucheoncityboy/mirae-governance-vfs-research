import json
import numpy as np
import pandas as pd
import pytest

from vfs_research.data_ingest import ROOT, digest
from vfs_research.economic_recovery import (
    economic_return, missing_contribution_scenarios, parse_nodes, plain_text,
)


def test_only_verified_per_old_share_payoff_can_extend_nav():
    with pytest.raises(ValueError, match='unverified'):
        economic_return(100, 50, quantity_ratio=2)
    assert economic_return(100, 50, quantity_ratio=2,
        status='VERIFIED_CORRECTABLE', basis_verified=True) == 0
    assert economic_return(100, 0, cash=80,
        status='VERIFIED_CORRECTABLE', basis_verified=True) == pytest.approx(-.2)


def test_cash_and_split_cannot_double_adjust_an_adjusted_series():
    for values in [dict(quantity_ratio=2), dict(cash=5), dict(rights=5)]:
        with pytest.raises(ValueError, match='double adjustment'):
            economic_return(100, 80, status='VERIFIED_CORRECTABLE',
                basis_verified=True, source_already_adjusted=True, **values)


@pytest.mark.parametrize('previous,current,ratio,cash', [(0,10,1,0),(100,-10,1,0),(100,10,-1,0),(100,10,1,np.nan)])
def test_invalid_or_missing_payoffs_rejected(previous,current,ratio,cash):
    with pytest.raises(ValueError):
        economic_return(previous,current,ratio,cash,
            status='VERIFIED_CORRECTABLE',basis_verified=True)


def test_exchange_html_body_and_korean_encodings():
    nodes=parse_nodes('viewDoc("20250828800064", "10788238", "0", "0", "0", "HTML", "");')
    assert nodes[0]['dtd']=='HTML'
    assert plain_text('<STYLE>hidden</STYLE><p>정리매매</p>'.encode('cp949'))=='정리매매'


def test_assumptions_never_become_empirical_months_or_complete_returns():
    q=missing_contribution_scenarios(pd.DataFrame([{'date':'2024-07-01','strategy':'VFS','missing_weight':.01}]))
    assert q.unknown_position_contribution_pp.tolist()==[-1.,-.5,.5,1.]
    assert q.observed_portfolio_return.isna().all()
    assert not q.extends_observed_NAV.any()
    assert q.role.eq('ASSUMPTION_ONLY_NOT_OBSERVED_RETURN').all()


def test_current_and_previous_analysis_locks_are_immutable():
    lock=json.loads((ROOT/'config/economic_recovery_followup_lock.json').read_text())
    assert digest(ROOT/'config/economic_recovery_followup.yaml')==lock['sha256']
    assert lock['new_document_outcomes_viewed'] is False


def test_final_evidence_cannot_claim_recovered_returns_or_inference():
    out=ROOT/'outputs/final'
    if not (out/'completion_status.json').exists():
        pytest.skip('final evidence export not yet generated')
    status=json.loads((out/'completion_status.json').read_text())
    repairs=pd.read_csv(out/'return_repair_status.csv')
    evidence=pd.read_csv(out/'event_evidence_register.csv')
    assert len(repairs)==11 and repairs.event_id.nunique()==11
    assert repairs.repaired.eq(False).all()
    assert repairs.return_status.eq('UNVERIFIED').all()
    assert set(repairs.event_id)==set(evidence.event_id)
    assert evidence.body_sha256.str.fullmatch('[a-f0-9]{64}').all()
    assert status['economic_returns_repaired']==0
    assert status['classification']=='COMPLETE_LIMITED_EVIDENCE'
    assert status['long_investable_strategy_verified'] is False
    baseline=pd.read_csv(out/'baseline_vs_final.csv')
    assert np.allclose(baseline.baseline_total_return,baseline.final_total_return,atol=1e-12)
    assert np.allclose(baseline.baseline_mdd,baseline.final_mdd,atol=1e-12)
    tests=pd.read_csv(out/'robustness_and_alpha_status.csv')
    alpha=tests.loc[tests.analysis_type.eq('FF3_HAC')]
    assert alpha.status.eq('NOT_ESTIMATED').all()
    assert alpha[['alpha','p_hac','ci_low','ci_high']].isna().all().all()
    assert len(pd.read_csv(out/'missing_exposure_scenarios.csv'))==40


def test_economic_event_dates_do_not_authorize_future_signal_or_wrong_month_adjustment():
    findings=json.loads((ROOT/'config/economic_event_findings.json').read_text())['events']
    e={r['event_id']:r for r in findings}
    assert '2024-09-09' in e['E08']['fact'] and '2024-07' in e['E08']['fact']
    assert '2025-12-17' in e['E11']['fact']
    assert '형성 전' in e['E07']['reason']


def test_publication_is_idempotent_and_same_status_embedded_on_pages():
    import re
    from vfs_research.final_publication import sync
    if not (ROOT/'outputs/final/completion_status.json').exists():
        pytest.skip('final publication not generated')
    names=['README.md','reports/RESEARCH_REPORT.md','reports/EXECUTIVE_BRIEF.md','dashboard/index.html']
    before={p:digest(ROOT/p) for p in names}
    sync()
    assert before=={p:digest(ROOT/p) for p in names},'committed narrative must already match generated evidence'
    sync()
    assert before=={p:digest(ROOT/p) for p in names}
    page=(ROOT/'dashboard/index.html').read_text()
    status=json.loads(re.search(r'<script id="final-evidence-data" type="application/json">(.*?)</script>',page,re.S)[1])
    assert status==json.loads((ROOT/'outputs/final/completion_status.json').read_text())


def test_final_public_documents_links_and_source_counts():
    import re
    paths=[ROOT/'docs'/n for n in ['ECONOMIC_RETURN_RECOVERY.md','RESEARCH_CONCLUSION.md','INTERVIEW_BRIEF.md']]
    for p in paths:
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if not link.startswith(('http:','https:','#')):
                assert (p.parent/link.split('#')[0]).exists(),link
    q=json.loads((ROOT/'outputs/final/source_missingness_types.json').read_text())
    for k in ['full_source','study_2016_01_to_2026_04']:
        row=q[k]
        assert row['missing']==sum(row[n] for n in ['current_price_absent','previous_price_or_first_observation_unavailable','extreme_filter','other_source_gap'])
    assert q['all_659_filtered_positive']
