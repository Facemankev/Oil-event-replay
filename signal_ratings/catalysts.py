"""Descriptive contexts from existing dated research, never earlier signal inputs."""
from collections import defaultdict

CONTEXTS = {
 'amd-verdict':'Litigation', 'amd-2002':'Results and guidance','amd-outlook':'Results and guidance',
 'amd-2016':'Results, licensing and partnerships', 'vanlev':'Clinical development and trial results',
 'bmy-warning':'Results and guidance','checkmate':'Clinical development and trial results',
 'celgene':'Acquisitions','aig':'Financial-system stress and policy','liquidity':'Financial-system stress and policy',
 'gold-2013':'Gold, currencies and macro conditions','gold-2026':'Gold, currencies and macro conditions',
 'mrna-ships':'Clinical development and trial results','mrna-phase3':'Clinical development and trial results',
 'mrna-reversal':'Post-announcement reversal','xbox-rumor':'Results, licensing and partnerships',
 'xbox-official':'Results, licensing and partnerships','nvda-earnings':'Results and guidance',
 'nvda-defects':'Product quality and guidance','covid-selloff':'Pandemic disruption',
 'fed-covid':'Financial-system stress and policy',
}


def catalogue(ledger):
    grouped=defaultdict(list)
    for row in ledger['ledger']:
        if not row['investigation_focus']:continue
        evidence=row['evidence']
        contexts={CONTEXTS.get(s['id'],'Other or unexplained') for s in evidence['sources']}
        if evidence['category']=='unexplained' or not contexts:contexts={'Unexplained or later-only evidence'}
        for context in sorted(contexts):
            grouped[context].append(dict(instrument=row['instrument'],date=row['date'],
                explanation=evidence['explanation'],weakness=evidence['weakness'],confidence=evidence['confidence'],
                sources=[s['id'] for s in evidence['sources']],observed_discovery_change_percent=row['close_change_percent'],
                selection='Selected after observing exceptional prices, not independent validation.'))
    return [dict(context=k,cases=v,interpretation='Coarse retrospective circumstances include different and opposite outcomes. These labels cannot estimate recurrence, prove causation or enter an earlier signal.') for k,v in sorted(grouped.items())]
