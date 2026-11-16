"""Synthetic HTTP fixtures test the transport; live findings are reported separately."""
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from news_pilot.ingest import parse,poll,visible,open_journal,retry_seconds,SafeError
from news_pilot.run import run
from equities.collect import ROOT

RSS = b'<rss><channel><item><title>NVIDIA board investigation</title><link>https://nvidianews.nvidia.com/news/statement-from-nvidia-board-of-directors</link><description>Reported allegations; company says no reason to believe secrets compromised.</description><pubDate>Sun, 08 Nov 2026 15:00:00 -0500</pubDate></item></channel></rss>'
ATOM = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>v-test</title><link href="https://github.com/NVIDIA/TensorRT-LLM/releases/tag/test"/><updated>2026-11-08T20:00:00Z</updated><content>Software release fixture.</content></entry></feed>'

class Clock:
    def __init__(self):self.value=datetime(2026,11,8,20,1,tzinfo=timezone.utc)
    def __call__(self):return self.value.isoformat().replace('+00:00','Z')
    def advance(self,seconds):self.value+=timedelta(seconds=seconds)

class PilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):(ROOT/'work').mkdir(exist_ok=True)
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'work');self.directory=Path(self.tmp.name)/'journal';self.clock=Clock();self.calls=[]
    def tearDown(self):self.tmp.cleanup()
    def client(self,status=200,payload=RSS,headers=None):
        def fetch(url,request_headers):
            self.calls.append(request_headers);return status,payload,headers or {}
        return fetch

    def test_updated_only_feed_does_not_invent_original_publication(self):
        a=parse(ATOM,'nvidia_releases',self.clock())[0]
        self.assertIsNone(a['published_at']);self.assertEqual(a['updated_at'],'2026-11-08T20:00:00Z')
        self.assertFalse(a['original_publication_verified'])

    def test_bounded_xml_url_and_timestamp_validation(self):
        for payload in [b'x'*(4*1024*1024+1),b'<!DOCTYPE x><rss/>',b'\x00',RSS.replace(b'nvidianews.nvidia.com',b'example.org'),RSS.replace(b' -0500',b'')]:
            with self.assertRaises(SafeError):parse(payload,'nvidia_news',self.clock())

    def test_full_body_revision_hash_does_not_ignore_a_late_counterpoint(self):
        p=RSS.replace(b'Reported allegations; company says no reason to believe secrets compromised.',b'x'*1400+b' Original statement')
        q=p.replace(b'Original statement',b'Company denial')
        a=parse(p,'nvidia_news',self.clock())[0];b=parse(q,'nvidia_news',self.clock())[0]
        self.assertEqual(a['summary'],b['summary']);self.assertNotEqual(a['content_sha256'],b['content_sha256'])

    def test_actual_receipt_is_retained_and_future_receipt_hidden(self):
        r=poll(self.directory,'nvidia_news',self.client(),self.clock)
        self.assertEqual(r['new_versions'],1)
        self.assertEqual(visible(self.directory,'2026-11-08T20:00:59Z'),[])
        self.assertEqual(len(visible(self.directory,self.clock())),1)

    def test_conditional_304_and_minimum_interval_do_not_refresh_news(self):
        first=poll(self.directory,'nvidia_news',self.client(headers={'ETag':'"v1"'}),self.clock)
        skipped=poll(self.directory,'nvidia_news',self.client(),self.clock)
        self.assertEqual(skipped['status'],'cooldown_no_request');self.assertEqual(len(self.calls),1)
        self.clock.advance(61)
        repeat=poll(self.directory,'nvidia_news',self.client(304),self.clock)
        self.assertEqual(self.calls[-1]['If-None-Match'],'"v1"');self.assertEqual(repeat['new_versions'],0)
        self.assertEqual(visible(self.directory,self.clock())[0]['first_seen_at'],first['received_at'])

    def test_metadata_reposts_do_not_create_a_fresh_version(self):
        first=poll(self.directory,'nvidia_releases',self.client(payload=ATOM),self.clock)
        self.clock.advance(61)
        r=poll(self.directory,'nvidia_releases',self.client(payload=ATOM.replace(b'20:00:00Z',b'20:01:30Z')),self.clock)
        self.assertEqual(r['new_versions'],0);self.assertEqual(r['metadata_only_changes'],1)
        self.assertEqual(visible(self.directory,self.clock())[0]['first_seen_at'],first['received_at'])

    def test_real_content_revisions_are_append_only_and_as_of(self):
        poll(self.directory,'nvidia_news',self.client(),self.clock);before=self.clock();self.clock.advance(61)
        r=poll(self.directory,'nvidia_news',self.client(payload=RSS.replace(b'Reported allegations;',b'Updated reported allegations;')),self.clock)
        self.assertEqual(r['new_versions'],1);self.assertEqual(len(visible(self.directory,before)),1);self.assertEqual(len(visible(self.directory,self.clock())),2)

    def test_denial_and_retry_after_backoff_are_honoured_without_auto_retries(self):
        r=poll(self.directory,'nvidia_news',self.client(403),self.clock)
        self.clock.advance(60);self.assertEqual(poll(self.directory,'nvidia_news',self.client(),self.clock)['status'],'cooldown_no_request')
        self.assertEqual(len(self.calls),1);self.assertEqual(r['http_status'],403)
        r=poll(self.directory,'fed_news',self.client(429,headers={'Retry-After':'120'}),self.clock)
        self.clock.advance(119);self.assertEqual(poll(self.directory,'fed_news',self.client(),self.clock)['status'],'cooldown_no_request')
        self.assertEqual(retry_seconds('Sun, 08 Nov 2026 21:00:00 GMT','2026-11-08T20:00:00Z'),3600)

    def test_unrepresentable_retry_after_fails_closed(self):
        r=poll(self.directory,'nvidia_news',self.client(429,headers={'Retry-After':'9'*60}),self.clock)
        self.assertTrue(r['next_attempt_at'].startswith('9999-12-31'))
        self.clock.advance(86400)
        self.assertEqual(poll(self.directory,'nvidia_news',self.client(),self.clock)['status'],'cooldown_no_request')

    def test_server_and_parse_failures_never_import_partial_items(self):
        for source,status,payload in [('nvidia_news',503,b''),('fed_news',200,b'<broken')]:
            r=poll(self.directory,source,self.client(status,payload),self.clock);self.assertEqual(r['new_versions'],0)
            self.assertEqual(visible(self.directory,self.clock()),[])

    def test_regressed_receipt_clock_blocks_import_and_does_not_shorten_backoff(self):
        times=iter(['2026-11-08T20:01:00Z','2026-11-08T20:00:00Z'])
        r=poll(self.directory,'nvidia_news',self.client(),lambda:next(times))
        self.assertEqual(r['status'],'wall_clock_regressed');self.assertEqual(r['new_versions'],0)
        self.assertTrue(r['next_attempt_at'].startswith('2026-11-08T21:01:00'))
        self.assertEqual(visible(self.directory,'2026-11-08T21:01:00Z'),[])

    def test_unrelated_database_and_source_paths_are_refused(self):
        self.directory.mkdir(parents=True)
        p=self.directory/'receipts.sqlite'
        with sqlite3.connect(p) as db:db.execute('CREATE TABLE unrelated(x)');db.execute('PRAGMA user_version=1')
        before=p.read_bytes()
        with self.assertRaises(SafeError):open_journal(self.directory)
        self.assertEqual(p.read_bytes(),before)
        with self.assertRaises(SafeError):open_journal(ROOT/'equities')
        with self.assertRaises(SafeError):poll(self.directory,'unregistered',self.client(),self.clock)

    def test_concurrent_workers_reserve_one_request(self):
        _,db=open_journal(self.directory);db.close()
        entered=threading.Event();release=threading.Event();results=[]
        def blocking(url,headers):entered.set();release.wait(3);return 200,RSS,{}
        thread=threading.Thread(target=lambda:results.append(poll(self.directory,'nvidia_news',blocking,self.clock)))
        thread.start();self.assertTrue(entered.wait(3))
        second=poll(self.directory,'nvidia_news',self.client(),self.clock);release.set();thread.join(4)
        self.assertEqual(second['status'],'cooldown_no_request');self.assertFalse(self.calls);self.assertEqual(results[0]['new_versions'],1)

    def test_end_to_end_local_card_has_no_order_or_delivery_and_nonnegative_measurements(self):
        r=run(self.directory,'nvidia_news',client=self.client(),clock=self.clock)
        self.assertEqual(r['analysis']['cards'][0]['action'],'No Action')
        self.assertEqual(r['analysis']['external_alerts_sent'],0)
        self.assertEqual(r['analysis']['cards'][0]['historical_cross_check']['qualified_count'],0)
        self.assertGreaterEqual(r['timings_ms']['fetch_to_card_ms'],0)
        self.assertEqual(r['new_receipt_cards'],1)

if __name__=='__main__':unittest.main()
