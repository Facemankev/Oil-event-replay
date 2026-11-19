"""Clearly fabricated UI controls, never a market result or prospective prediction."""
import copy
from .classify import classify
from .policy import POLICY


def screen_fixture():
    stats=dict(attempts=20,complete=18,missing=2,coverage='0.9',distinct_years=5,
        later_complete=8,control_pairs=15,mean_return_percent='4',median_return_percent='3',
        mean_net_gbp='0.2',median_net_gbp='0.1',later_mean_return_percent='3',later_median_return_percent='2',
        median_paired_difference_gbp='0.1',median_SPY_excess_pp='2',median_net_SPY_excess_gbp='0.1',
        worst_directional_return_percent='-6',successful=12,unsuccessful=6,unchanged=0,
        historical_success_percent='66.6667',historical_failure_percent='33.3333',
        success_definition='SYNTHETIC observed direction, not forecast probability or net profit.',
        minimum_return_percent='-6',maximum_return_percent='12',mean_SPY_excess_pp='2.5',
        net_winning=11,net_losing=7,mean_estimated_friction_gbp='0.03',allocation_gbp='5',
        cost_assumptions={'fee_gbp_per_leg':'0.01','spread_bps':'10','slippage_bps_per_leg':'5'})
    cards=[]
    for instrument,direction in [('NVDA','UP'),('MRNA','DOWN'),('AMD','UP')]:
        c=dict(id=f'{instrument}:spike:{direction}:5',instrument=instrument,pattern='spike',title='A SYNTHETIC price pattern',
               direction=direction,horizon=5,as_of='2026-11-19',validation_id=None,
               costs={cost:copy.deepcopy(stats) for cost in POLICY['costs']},example_ids=['positive','negative'],
               full_matured_examples=20,example_selection='SYNTHETIC chronological positive and negative controls.')
        if direction=='DOWN':
            for s in c['costs'].values():
                for k in ['mean_return_percent','median_return_percent','mean_net_gbp','median_net_gbp','later_mean_return_percent','later_median_return_percent','median_paired_difference_gbp','median_SPY_excess_pp','median_net_SPY_excess_gbp']:s[k]=str(-float(s[k]))
        c['costs']['small_account_flat_fee']['mean_net_gbp']='-2'
        c['costs']['small_account_flat_fee']['median_net_gbp']='-2'
        if instrument=='AMD':
            for s in c['costs'].values():s['control_pairs']=2
        c['ratings']={cost:classify(c,cost) for cost in POLICY['costs']}
        cards.append(c)
    examples={}
    for name,change,net in [('positive','4','0.1'),('negative','-6','-0.3')]:
        examples[name]=dict(instrument='SYNTHETIC',date='2024-01-02',maturity_day='2024-01-10',change_percent=change,SPY_excess_pp=change,
           costs={cost:dict(status='simulated_reference_path',reason='SYNTHETIC',net_pnl_gbp=net,entry_date='2024-01-03',exit_date='2024-01-10') for cost in POLICY['costs']},
           catalyst=dict(category='unexplained',explanation='SYNTHETIC evidence control.',weakness='No actual catalyst is asserted.',sources=['fixture'],retrospective_only=True))
    source=dict(id='fixture',url='https://example.org/synthetic',title='SYNTHETIC source',publisher='SYNTHETIC fixture',published_day='2024-01-02',published_at=None)
    return dict(schema_version=1,kind='PRIVATE_SIGNAL1_SCREEN',synthetic=True,as_of='2026-11-19',source_rows=120,
        all_history_previously_examined=True,source_profile='SYNTHETIC TEST CONTROLS, not actual prices.',cards=cards,examples=examples,sources={'fixture':source},
        issuer_controls=[dict(instrument='NVDA',publication_day='2024-01-02',source=source)],pending_count=1,
        limitations=['SYNTHETIC fixture, not actual historical evidence or performance.'],current_signals=0,likely_approved_validation_ids=[])
