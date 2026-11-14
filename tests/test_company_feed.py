"""Synthetic transport fixtures exercise the collector, never invented news evidence."""
from pathlib import Path
import tempfile
import subprocess
import json
import unittest
from equities.collect import parse_feed, collect, SafeError, ROOT

RSS = b'''<rss version="2.0"><channel><item><title>NVIDIA board investigation</title><link>https://nvidianews.nvidia.com/news/test-transport</link><description>&lt;p&gt;Reported security inquiry.&lt;/p&gt;</description><pubDate>Sun, 08 Nov 2026 15:00:00 -0500</pubDate></item></channel></rss>'''
ATOM = b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>NVIDIA CEO update</title><link href="https://nvidianews.nvidia.com/news/test-transport"/><summary>Attributed company response.</summary><published>2026-11-08T20:00:00Z</published><updated>2026-11-10T12:00:00Z</updated></entry></feed>'''


class CompanyFeedTests(unittest.TestCase):
    def test_timezone_and_actual_receipt_are_distinct(self):
        r = parse_feed(RSS, '2026-11-14T10:00:00Z')['articles'][0]
        self.assertEqual(r['published_at'], '2026-11-08T20:00:00Z')
        self.assertEqual(r['actual_first_seen_at'], '2026-11-14T10:00:00Z')
        self.assertFalse(r['original_vintage_verified'])
        self.assertEqual(r['summary'], 'Reported security inquiry.')

    def test_atom_update_not_backdated(self):
        r = parse_feed(ATOM, '2026-11-14T10:00:00Z')['articles'][0]
        self.assertEqual(r['updated_at'], '2026-11-10T12:00:00Z')
        self.assertNotEqual(r['updated_at'], r['published_at'])

    def test_duplicate_transport_entries_repeat_identically(self):
        duplicate = RSS.replace(b'</channel>', RSS.split(b'<channel>')[1].split(b'</channel>')[0] + b'</channel>')
        self.assertEqual(len(parse_feed(duplicate, '2026-11-14T10:00:00Z')['articles']), 1)
        self.assertEqual(parse_feed(RSS, '2026-11-14T10:00:00Z'), parse_feed(RSS, '2026-11-14T10:00:00Z'))

    def test_unsupported_xml_entities_encodings_and_oversize_are_rejected(self):
        for raw in [b'<!DOCTYPE rss [<!ENTITY x "private">]><rss/>', b'<rss>\x00</rss>', b'x' * (1024 * 1024 + 1), b'<invalid', b'<unrelated/>']:
            with self.assertRaises(SafeError): parse_feed(raw, '2026-11-14T10:00:00Z')

    def test_untrusted_url_and_unknown_timezone_rejected_without_echo(self):
        for raw in [RSS.replace(b'https://nvidianews.nvidia.com', b'https://example.org'), RSS.replace(b'/news/test-transport', b'/news/test-transport?token=untrusted'), RSS.replace(b' -0500', b'')]:
            with self.assertRaises(SafeError): parse_feed(raw, '2026-11-14T10:00:00Z')

    def test_html_and_scripts_are_not_retained_as_active_content(self):
        raw = RSS.replace(b'&lt;p&gt;Reported security inquiry.&lt;/p&gt;', b'&lt;script&gt;secret_marker()&lt;/script&gt;&lt;b&gt;NVIDIA response&lt;/b&gt;')
        summary = parse_feed(raw, '2026-11-14T10:00:00Z')['articles'][0]['summary']
        self.assertEqual(summary, 'NVIDIA response')

    def test_new_local_receipt_snapshot_cannot_overwrite_existing_or_write_source(self):
        work = ROOT / 'work'; work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as tmp:
            tmp = Path(tmp); feed = tmp / 'input.xml'; feed.write_bytes(RSS)
            output = tmp / 'capture'
            result = collect(output, feed, '2026-11-14T10:00:00Z')
            self.assertEqual(result['articles'], 1); self.assertFalse(result['price_or_account_changes'])
            self.assertEqual((output / 'feed.xml').read_bytes(), RSS)
            before = (output / 'news.json').read_bytes()
            with self.assertRaises(SafeError): collect(output, feed)
            self.assertEqual(before, (output / 'news.json').read_bytes())
            with self.assertRaises(SafeError): collect(ROOT / 'equities' / 'not-allowed', feed)

    def test_collector_output_runs_through_actual_node_detector_without_backdating(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'work') as tmp:
            tmp = Path(tmp); feed = tmp / 'input.xml'; feed.write_bytes(RSS)
            collect(tmp / 'capture', feed, '2026-11-14T10:00:00Z')
            args = ['node', 'equities/detect.mjs', '--input', str(tmp / 'capture' / 'news.json'), '--as-of']
            before = json.loads(subprocess.check_output(args + ['2026-11-09T21:01:00Z'], cwd=ROOT))
            after = json.loads(subprocess.check_output(args + ['2026-11-14T10:01:00Z'], cwd=ROOT))
            self.assertEqual(before['news_developments'], 0)
            self.assertEqual(after['news_developments'], 1)
            self.assertEqual(after['action'], 'No Action')
            self.assertEqual(after['alert']['availability_mode'], 'captured_receipt')


if __name__ == '__main__': unittest.main()
