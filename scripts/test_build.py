import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from build import build, load_articles, CONTENT

class FeedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'content/news').mkdir(parents=True)
        (self.root/'content/reads').mkdir()
        self.article = dict(id='2026-10-06-news', title='中文 & 标题', date_published='2026-10-06T08:00:00+08:00', category='news', content_text='全文 <script>alert(1)</script> &\n\n第二段')
        self.write()

    def write(self):
        (self.root/'content/news/a.json').write_text(json.dumps(self.article), encoding='utf-8')

    def test_full_text_filter_and_stable_id(self):
        out = self.root/'site'
        build(self.root/'content', out, 'https://example.com/project')
        rss = ET.parse(out/'feed.xml')
        self.assertEqual(rss.findtext('channel/item/title'), self.article['title'])
        self.assertEqual(rss.findtext('channel/item/guid'), self.article['id'])
        body = rss.findtext('channel/item/{'+CONTENT+'}encoded')
        self.assertIn('第二段', body)
        self.assertNotIn('<script>', body)
        self.assertEqual(len(ET.parse(out/'reads.xml').findall('channel/item')), 0)
        self.assertEqual(json.loads((out/'feed.json').read_text())['items'][0]['content_text'], self.article['content_text'])
        before = (out/'feed.xml').read_bytes()
        build(self.root/'content', out, 'https://example.com/project')
        self.assertEqual(before, (out/'feed.xml').read_bytes())

    def test_timezone_and_duplicate_validation(self):
        self.article['date_published'] = '2026-10-06T08:00:00'
        self.write()
        with self.assertRaises(ValueError): load_articles(self.root/'content')
        self.article['date_published'] += '+08:00'
        self.write()
        (self.root/'content/news/b.json').write_text(json.dumps(self.article))
        with self.assertRaises(ValueError): load_articles(self.root/'content')

if __name__ == '__main__': unittest.main()
