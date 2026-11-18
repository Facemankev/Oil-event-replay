"""DATA-3 controls use explicitly synthetic bars; none is published as real history."""
import copy,hashlib,json,sqlite3,tempfile,unittest
from datetime import date,timedelta
from pathlib import Path
from event_history.library import ROOT
from daily_prices.ingest import make_capture,poll
from daily_prices.model import validate_rows,validate_capture
from daily_prices.parsers import parse,WIKI_COLUMNS
from daily_prices.database import connect,import_capture,query,conflicts,select_captures
from daily_prices.evaluate import enrich,daily_paths,build_report,HERE
from daily_prices.prospective import lock,settle
from free_pilot.data import load_free_library


class DailyPricesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):(ROOT/'work').mkdir(exist_ok=True);cls.base=load_free_library()

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'work');self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'daily.sqlite';self.db=connect(self.path);self.addCleanup(self.db.close)

    def sample(self,start='2015-01-05',count=30,received='2026-11-18T18:00:00Z',synthetic=True):
        days=[];d=date.fromisoformat(start)
        while len(days)<count:
            if d.weekday()<5:days.append(d.isoformat())
            d+=timedelta(days=1)
        lines=[','.join(WIKI_COLUMNS)]
        for n,day in enumerate(days):
            price=100+n
            lines.append(','.join(map(str,[day,price,price+2,price-2,price,1000,0,1,price,price+2,price-2,price,1000])))
        raw=('\n'.join(lines)+'\n').encode()
        identity=dict(instrument='NVDA',symbol='NVDA',venue='NASDAQ',asset_kind='equity',calendar_basis='SYNTHETIC weekdays for algorithm controls; not an exchange calendar')
        c=make_capture('nasdaq_wiki','https://data.nasdaq.com/api/v3/datasets/WIKI/NVDA.csv',raw,identity,received)
        c['synthetic_control']=synthetic
        return raw,c,parse(raw,c)

    def test_strict_parser_preserves_prices_actions_and_actual_row_locators(self):
        raw,c,r=self.sample();self.assertEqual(len(r),30);self.assertEqual(r[0]['close'],'100')
        self.assertEqual(r[0]['split_factor'],'1');self.assertEqual(r[0]['source_row'],2)
        self.assertIsNone(r[0]['original_available_at']);self.assertIn('Adj. Volume',r[0]['source_fields'])

    def test_repeat_capture_even_later_receipt_never_rewrites_first_observed_time(self):
        raw,c,r=self.sample();a=import_capture(self.db,c,r,raw);later=copy.deepcopy(c);later['retrieved_at']='2026-11-18T19:00:00Z'
        b=import_capture(self.db,later,r,raw)
        self.assertEqual(a['capture_id'],b['capture_id']);self.assertEqual(a['inserted_observations'],30);self.assertEqual(b['inserted_rows'],0)
        self.assertEqual(query(self.db,a['capture_id'],'2015-01-01','2015-12-31')['capture']['retrieved_at'],c['retrieved_at'])

    def test_exact_capture_range_query_and_adjustment_never_splices(self):
        raw,c,r=self.sample();a=import_capture(self.db,c,r,raw)
        q=query(self.db,a['capture_id'],'2015-01-05','2015-01-09','provider_adjusted')
        self.assertEqual(len(q['rows']),5);self.assertFalse(q['executable'])
        with self.assertRaises(Exception):query(self.db,a['capture_id'],'2015-02-01','2015-01-01')
        with self.assertRaises(Exception):select_captures(self.db,[a['capture_id'],a['capture_id']])

    def test_revisions_append_and_original_values_remain_queryable(self):
        raw,c,r=self.sample();a=import_capture(self.db,c,r,raw)
        changed=raw.replace(b',100,1000,0,1,',b',101,1000,0,1,',1);d=copy.deepcopy(c);d['payload_sha256']=hashlib.sha256(changed).hexdigest();updated=parse(changed,d)
        b=import_capture(self.db,d,updated,changed)
        self.assertNotEqual(a['capture_id'],b['capture_id']);self.assertEqual(len(conflicts(self.db)),1)
        self.assertEqual(query(self.db,a['capture_id'],'2015-01-05','2015-01-05')['rows'][0]['close'],'100')

    def test_exact_source_bytes_required_for_non_synthetic_import_and_forged_rows_refused(self):
        raw,c,r=self.sample(synthetic=False)
        with self.assertRaises(Exception):import_capture(self.db,c,r)
        forged=copy.deepcopy(r);forged[0]['close']='101'
        with self.assertRaises(Exception):import_capture(self.db,c,forged,raw)
        self.assertEqual(self.db.execute('SELECT count(*) FROM captures').fetchone()[0],0)

    def test_immutable_tables_and_foreign_database_are_preserved(self):
        raw,c,r=self.sample();import_capture(self.db,c,r,raw)
        for table in ('identity','captures','observations'):
            with self.assertRaises(sqlite3.DatabaseError):self.db.execute('DELETE FROM '+table)
        other=Path(self.tmp.name)/'old.sqlite'
        with sqlite3.connect(other) as db:db.execute('CREATE TABLE prices(value TEXT)')
        before=other.read_bytes()
        with self.assertRaises(Exception):connect(other)
        self.assertEqual(before,other.read_bytes())
        with self.assertRaises(Exception):connect(ROOT/'data'/'daily.sqlite')

    def test_licence_claim_cannot_override_provider_or_resource_rights(self):
        raw,c,r=self.sample()
        for field,value in [('source_id','yahoo'),('rights_url','https://example.com/cc0'),('url','https://data.nasdaq.com/api/v3/datasets/PAID/NVDA.csv'),('currency','TWD')]:
            bad=copy.deepcopy(c);bad[field]=value
            with self.assertRaises(Exception):validate_capture(bad)
        bad=copy.deepcopy(c);bad['rights']['redistribution']=False
        with self.assertRaises(Exception):validate_capture(bad)
        bad=copy.deepcopy(c);bad['frequency']='monthly'
        with self.assertRaises(Exception):validate_capture(bad)

    def test_wrong_ticker_and_credential_urls_are_rejected(self):
        raw,c,r=self.sample()
        for url in ['https://data.nasdaq.com/api/v3/datasets/WIKI/AMD.csv','https://data.nasdaq.com/api/v3/datasets/WIKI/NVDA.csv?api_key=']:
            bad=copy.deepcopy(c);bad['url']=url
            with self.assertRaises(Exception):validate_capture(bad)

    def test_challenge_duplicate_nonpositive_OHLC_future_and_fabricated_adjustments_fail(self):
        raw,c,r=self.sample()
        b=copy.deepcopy(c);html=b'<html>verify browser</html>';b['payload_sha256']=hashlib.sha256(html).hexdigest()
        with self.assertRaises(Exception):parse(html,b)
        for field,value in [('close','0'),('high','90'),('date','2026-12-01'),('adjusted_close','NaN')]:
            bad=copy.deepcopy(r);bad[0][field]=value
            with self.assertRaises(Exception):validate_rows(bad,c)
        with self.assertRaises(Exception):validate_rows(r+[r[0]],c)
        bad=copy.deepcopy(c);bad['price_basis']='provider_adjusted_reference'
        with self.assertRaises(Exception):validate_capture(bad)

    def test_explicit_missing_observation_does_not_become_zero_or_holiday(self):
        raw,c,r=self.sample();bad=copy.deepcopy(r);bad[1].update(status='suspended',**{k:None for k in ('open','high','low','close','volume','cash_dividend','split_factor','adjusted_close')})
        validate_rows(bad,c)
        rows=daily_paths([dict(id='synthetic-only',episode_id='synthetic-only',targets=['NVDA'],public_day='2015-01-04')],{'NVDA':{'capture':c,'rows':bad}})
        self.assertEqual(rows[0]['horizons']['1']['status'],'explicit_unavailable_observation_not_a_holiday')
        self.assertIsNone(rows[0]['horizons']['1']['change_percent'])

    def test_synthetic_bars_cannot_enter_enrichment_or_published_history(self):
        raw,c,r=self.sample();selection={'NVDA':dict(capture=c,rows=r)};after,a=enrich(self.base,selection)
        self.assertEqual(after['observations'],self.base['observations']);self.assertFalse(a['added_instruments'])
        with self.assertRaises(Exception):build_report(selection)

    def test_non_USD_proxy_and_existing_series_are_not_aliased(self):
        raw,c,r=self.sample(synthetic=False)
        proxy=copy.deepcopy(c);proxy.update(currency='TWD',asset_kind='gold_etf_proxy',instrument='TWSE:00635U')
        after,a=enrich(self.base,{'TWSE:00635U':dict(capture=proxy,rows=r)})
        self.assertFalse(a['added_instruments']);self.assertEqual(after['observations'],self.base['observations'])
        c['instrument']='brent';after,a=enrich(self.base,{'brent':dict(capture=c,rows=r)})
        self.assertIn('existing_series_requires_explicit_difference_review',a['blocked'][0]['reasons'])

    def test_failure_429_cooldown_and_no_body_or_licence_inference(self):
        called=[]
        def client(url,headers):called.append(url);return 429,b'private error not retained',{'Retry-After':'120'}
        first=poll(self.db,'nasdaq_wiki',client=client,clock=lambda:'2026-11-18T18:00:00Z')
        second=poll(self.db,'nasdaq_wiki',client=client,clock=lambda:'2026-11-18T18:00:30Z')
        self.assertEqual(len(called),1);self.assertEqual(second['status'],'cooldown_no_request');self.assertEqual(first['imported_rows'],0)
        self.assertNotIn('private error',self.db.execute('SELECT payload FROM receipts').fetchone()[0])

    def test_200_HTML_never_imports_as_a_working_daily_feed(self):
        raw,c,r=self.sample();identity={k:c[k] for k in ('instrument','symbol','venue','asset_kind','calendar_basis')}
        receipt=poll(self.db,'nasdaq_wiki',identity,client=lambda *a:(200,b'<html>captcha</html>',{}),clock=lambda:'2026-11-18T18:00:00Z',import_data=True)
        self.assertEqual(receipt['status'],'invalid_unknown_or_challenge_series');self.assertEqual(receipt['imported_rows'],0)

    def test_twse_ROC_index_dates_identity_and_proxy_are_explicit(self):
        raw=json.dumps(dict(stat='OK',fields=['日期','開盤指數','最高指數','最低指數','收盤指數'],data=[['109/03/02','100','102','98','101']])).encode()
        ident=dict(instrument='TWSE:TAIEX',symbol='TAIEX',venue='TWSE',asset_kind='index',calendar_basis='SYNTHETIC parser control')
        c=make_capture('twse_open_index','https://www.twse.com.tw/indicesReport/MI_5MINS_HIST?response=json',raw,ident,'2026-11-18T18:00:00Z');c['synthetic_control']=True
        r=parse(raw,c);self.assertEqual(r[0]['date'],'2020-03-02');self.assertEqual(c['unit'],'index_points')
        c['instrument']='nasdaq_composite'
        with self.assertRaises(Exception):parse(raw,c)

    def test_twse_snapshot_does_not_invent_historical_depth_or_adjustments(self):
        raw=b'Date,Code,Name,TradeVolume,TradeValue,OpeningPrice,HighestPrice,LowestPrice,ClosingPrice,Change,Transaction\n20261118,2330,synthetic-only,1000,100000,100,102,98,101,1,10\n'
        ident=dict(instrument='TWSE:2330',symbol='2330',venue='TWSE',asset_kind='equity',calendar_basis='SYNTHETIC one-day parser control')
        c=make_capture('twse_open_equities','https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL?response=open_data',raw,ident,'2026-11-18T18:00:00Z');c['synthetic_control']=True
        r=parse(raw,c);self.assertEqual(len(r),1);self.assertIsNone(r[0]['adjusted_close']);self.assertIsNone(r[0]['cash_dividend'])

    def test_retrospective_cannot_be_relabelled_as_prospective_or_late_enrollment(self):
        event=dict(id='synthetic-only',episode_id='synthetic-only',instrument='NVDA',synthetic_control=True,published_at='2026-11-18T17:00:00Z',first_received_at='2026-11-18T17:01:00Z')
        features=dict(as_of='2026-11-19T17:00:00Z',outcomes_used=0,research_action='Watch')
        model=dict(training_through='2019-12-31',test_outcomes_used=0,instruments=['NVDA'],rule='event_long',horizon=5)
        with self.assertRaises(Exception):lock(self.db,event,features,model,[],clock=lambda:features['as_of'])
        event.update(published_at='2026-11-19T16:00:00Z',first_received_at='2026-11-19T16:01:00Z');model['test_outcomes_used']=1
        with self.assertRaises(Exception):lock(self.db,event,features,model,[],clock=lambda:features['as_of'])

    def test_future_signal_locks_once_per_episode_and_outcome_requires_prior_lock(self):
        event=dict(id='synthetic-only',episode_id='synthetic-only',instrument='NVDA',synthetic_control=True,published_at='2026-11-19T16:00:00Z',first_received_at='2026-11-19T16:01:00Z')
        features=dict(as_of='2026-11-19T17:00:00Z',outcomes_used=0,research_action='No Action')
        model=dict(training_through='2019-12-31',test_outcomes_used=0,instruments=['NVDA'],rule='event_long',horizon=5)
        result=lock(self.db,event,features,model,[],clock=lambda:'2026-11-19T17:00:01Z')
        self.assertEqual(result['recorded_at'],'2026-11-19T17:00:01Z')
        self.assertEqual(result['validated_action'],'No Action')
        with self.assertRaises(Exception):lock(self.db,{**event,'id':'renamed-synthetic-copy'},features,model,[],clock=lambda:features['as_of'])
        with self.assertRaises(Exception):settle(self.db,'never-locked','unknown',clock=lambda:'2026-12-01T12:00:00Z')
        self.assertEqual(self.db.execute('SELECT count(*) FROM locks').fetchone()[0],1)

    def test_later_prices_do_not_change_earlier_observed_features_or_frozen_original_inputs(self):
        raw,c,r=self.sample(synthetic=False);selection={'NVDA':dict(capture=c,rows=r)}
        after,_=enrich(self.base,selection)
        self.assertEqual(after['events'],self.base['events']);self.assertEqual(after['reported_reactions'],self.base['reported_reactions'])
        from learning.engine import fit
        changed=copy.deepcopy(after)
        for p in changed['observations']:
            if p['date']>='2020-01-01' and p['status']=='numeric':p['value']='9999' # synthetic future mutation
        self.assertEqual(fit(after),fit(changed))
        old={p['instrument'] for p in self.base['observations']}
        self.assertEqual([p for p in after['observations'] if p['instrument'] in old],self.base['observations'])

    def test_incremental_raw_daily_captures_accumulate_without_latest_revision_splicing(self):
        ids=[]
        for day,close in [('20261117','100'),('20261118','101')]:
            raw=('Date,Code,Name,TradeVolume,TradeValue,OpeningPrice,HighestPrice,LowestPrice,ClosingPrice,Change,Transaction\n'+day+',2330,synthetic-only,100,10000,100,102,98,'+close+',1,10\n').encode()
            ident=dict(instrument='TWSE:2330',symbol='2330',venue='TWSE',asset_kind='equity',calendar_basis='SYNTHETIC parser control')
            c=make_capture('twse_open_equities','https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL?response=open_data',raw,ident,'2026-11-18T18:00:00Z');c['synthetic_control']=True
            ids.append(import_capture(self.db,c,parse(raw,c),raw)['capture_id'])
        selected=select_captures(self.db,ids)
        self.assertEqual([r['date'] for r in selected['TWSE:2330']['rows']],['2026-11-17','2026-11-18'])
        self.assertEqual(len(selected['TWSE:2330']['component_capture_ids']),2)

    def test_no_empty_or_future_price_evidence_can_authorize_research_Watch(self):
        event=dict(id='synthetic-only',episode_id='synthetic-only',instrument='NVDA',synthetic_control=True,published_at='2026-11-19T16:00:00Z',first_received_at='2026-11-19T16:01:00Z')
        f=dict(as_of='2026-11-19T17:00:00Z',outcomes_used=0,research_action='Watch',context=[])
        m=dict(training_through='2019-12-31',test_outcomes_used=0,instruments=['NVDA'],rule='event_long',horizon=5)
        with self.assertRaises(Exception):lock(self.db,event,f,m,[],clock=lambda:f['as_of'])
        f.update(research_action='No Action',context=[dict(date='2026-11-20',close='999')])
        with self.assertRaises(Exception):lock(self.db,event,f,m,[],clock=lambda:f['as_of'])

    def test_prospective_reference_settlement_is_append_only_not_a_validated_trade(self):
        # All bytes/events are fabricated controls, never a real event or reported
        # market history. Exercise the real-payload branch in a temporary test DB.
        e=dict(id='synthetic-only',episode_id='synthetic-only',instrument='TWSE:TAIEX',synthetic_control=True,published_at='2026-11-19T16:00:00Z',first_received_at='2026-11-19T16:01:00Z')
        f=dict(as_of='2026-11-19T17:00:00Z',outcomes_used=0,research_action='No Action')
        m=dict(training_through='2019-12-31',test_outcomes_used=0,instruments=['TWSE:TAIEX'],rule='event_long',horizon=1)
        locked=lock(self.db,e,f,m,[],clock=lambda:f['as_of'])
        raw=json.dumps(dict(stat='OK',fields=['日期','開盤指數','最高指數','最低指數','收盤指數'],data=[['115/11/20','100','102','98','100'],['115/11/23','90','92','88','90']])).encode()
        c=make_capture('twse_open_index','https://www.twse.com.tw/indicesReport/MI_5MINS_HIST?response=json',raw,dict(instrument='TWSE:TAIEX',symbol='TAIEX',venue='TWSE',asset_kind='index',calendar_basis='SYNTHETIC settlement control'),'2026-11-24T18:00:00Z')
        cid=import_capture(self.db,c,parse(raw,c),raw)['capture_id']
        before=self.db.execute('SELECT payload FROM locks').fetchone()[0]
        out=settle(self.db,locked['lock_id'],cid,clock=lambda:'2026-11-24T19:00:00Z')
        self.assertEqual(before,self.db.execute('SELECT payload FROM locks').fetchone()[0])
        self.assertEqual(out['gross_change_percent'],'-10.0000');self.assertIsNone(out['net_pnl_gbp']);self.assertEqual(out['validated_action'],'No Action')
        settle(self.db,locked['lock_id'],cid,clock=lambda:'2026-11-24T20:00:00Z')
        self.assertEqual(self.db.execute('SELECT count(*) FROM settlements').fetchone()[0],1)
        from daily_prices.prospective import summary
        self.assertEqual(summary(self.db)['events'],0) # synthetic event excluded
        for table in ('locks','settlements'):
            with self.assertRaises(sqlite3.DatabaseError):self.db.execute('DELETE FROM '+table)

    def test_actual_empty_source_report_reproduces_original_and_separate_zero_new_evaluation(self):
        from daily_prices.prospective import summary
        report=build_report(new_evaluation=summary(self.db))
        self.assertEqual(report,json.loads((HERE/'report.json').read_text()))
        self.assertEqual(report['raw_daily_captures']['real_numeric'],0)
        self.assertEqual(report['genuinely_new_evaluation']['events'],0)
        before=report['original_examined_evaluation']['before'];after=report['expanded_retrospective_diagnostics']['after']
        self.assertEqual(before,after);self.assertEqual(after['default_simulation']['complete'],69)
        self.assertFalse(report['expanded_retrospective_diagnostics']['predictive_improvement_demonstrated'])

    def test_source_scope_is_exact_and_never_extends_an_open_licence_to_another_product(self):
        raw,c,r=self.sample()
        c.update(source_id='twse_open_equities',url='https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL_unlicensed')
        with self.assertRaises(Exception):validate_capture(c)
        with self.assertRaises(Exception):poll(self.db,'twse_open_equities',request_url=c['url'],client=lambda *a:self.fail('Must reject before HTTP'))
        with self.assertRaises(Exception):poll(self.db,'nasdaq_wiki',request_url='https://data.nasdaq.com/api/v3/datasets/WIKI/../PAID.csv',client=lambda *a:self.fail('Must reject before HTTP'))

    def test_reservation_prevents_concurrent_duplicate_requests(self):
        calls=[];observed=[];violations=[]
        def client(url,headers):
            calls.append(url);other=connect(self.path)
            try:
                blocked=poll(other,'nasdaq_wiki',clock=lambda:'2026-11-18T18:00:01Z',client=lambda *a:(violations.append(True) or (403,b'',{})))
                observed.append(blocked['status'])
            finally:other.close()
            return 403,b'',{}
        poll(self.db,'nasdaq_wiki',client=client,clock=lambda:'2026-11-18T18:00:00Z')
        self.assertEqual(len(calls),1);self.assertEqual(observed,['cooldown_no_request']);self.assertEqual(violations,[])

    def test_IPO_reference_never_substitutes_another_currency_or_listing(self):
        from daily_prices.evaluate import ipo_coverage
        raw,c,r=self.sample()
        result=ipo_coverage({'ROO':dict(capture=c,rows=r)})
        row=next(r for r in result['records'] if r['event_id']=='ipo-deliveroo-2021')
        self.assertEqual(row['status'],'wrong_currency_venue_or_security_identity')
        self.assertEqual(result['five_observation_reference_windows'],0)


    def test_real_label_cannot_hide_a_synthetic_component_in_an_assembled_history(self):
        # Fabricated parser controls in a temporary DB only. Exercise both
        # admission labels without publishing either as actual market history.
        ids=[]
        for day,control in [('20261117',False),('20261118',True)]:
            raw=('Date,Code,Name,TradeVolume,TradeValue,OpeningPrice,HighestPrice,LowestPrice,ClosingPrice,Change,Transaction\n'+day+',2330,synthetic-only,100,10000,100,102,98,100,1,10\n').encode()
            ident=dict(instrument='TWSE:2330',symbol='2330',venue='TWSE',asset_kind='equity',calendar_basis='SYNTHETIC parser control')
            c=make_capture('twse_open_equities','https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL?response=open_data',raw,ident,'2026-11-18T18:00:00Z')
            c['synthetic_control']=control
            ids.append(import_capture(self.db,c,parse(raw,c),raw)['capture_id'])
        for order in (ids,list(reversed(ids))):
            with self.assertRaisesRegex(ValueError,'Real and synthetic'):
                select_captures(self.db,order)


if __name__=='__main__':unittest.main()
