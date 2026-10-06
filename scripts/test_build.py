import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from build import build, load_articles, CONTENT, ATOM
from html.parser import HTMLParser

class BodyParser(HTMLParser):
    def __init__(self, body):
        super().__init__()
        self.tags, self.images, self.links = [], [], []
        self.feed(body)

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == 'img': self.images.append(dict(attrs))
        if tag == 'a': self.links.append(dict(attrs))

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

    def structured(self):
        self.article.update(intro=['开场'], news_items=[{
            'title': 'AI & iPhone <b>标题</b>',
            'body': ['正文 <script>bad()</script>', '另一段'],
            'why_it_matters': '有意义的解释',
            'sources': [{'name': '来源 & 名称', 'url': 'https://example.org/story?a=1&b=2'}],
            'image': {'url': 'https://example.org/photo.jpg?a=1&b=2', 'alt': '图 <说明>',
                      'caption': '原文配图', 'credit': '摄影师', 'source_url': 'https://example.org/story'}
        }, {'title': '没有图片的新闻', 'body': ['无图正文'], 'why_it_matters': '另一个理由',
            'sources': [{'name': '第二来源', 'url': 'https://example.org/second'}]}],
            afterword=['尾声'], sections=[{'title': '今日长读', 'paragraphs': ['完整长读内容'],
                'sources': [{'name': '长读原文', 'url': 'https://example.org/read'}]}],
            date_modified='2026-10-06T17:00:00+08:00')
        self.write()

    def test_structured_full_text_rss_json_and_optional_images(self):
        self.structured()
        out = self.root/'site'
        build(self.root/'content', out, 'https://example.com/project')
        rss = ET.parse(out/'news.xml')
        item = rss.find('channel/item')
        body = item.findtext('{'+CONTENT+'}encoded')
        parsed = BodyParser(body)
        self.assertEqual(parsed.tags.count('h2'), 3)
        self.assertEqual(parsed.tags.count('h3'), 2)
        self.assertEqual(len(parsed.images), 1)
        self.assertEqual(parsed.images[0]['src'], 'https://example.org/photo.jpg?a=1&b=2')
        self.assertEqual(parsed.images[0]['alt'], '图 <说明>')
        self.assertTrue(all(x['href'].startswith('https://') for x in parsed.links))
        self.assertFalse({'strong', 'b', 'script', 'style', 'iframe'} & set(parsed.tags))
        self.assertNotIn('loading=', body)
        self.assertIn('&lt;b&gt;标题&lt;/b&gt;', body)
        self.assertIn('无图正文', body)
        self.assertIn('完整长读内容', body)
        self.assertEqual(item.findtext('description'), body)
        self.assertEqual(item.findtext('guid'), self.article['id'])
        self.assertEqual(item.findtext('{'+ATOM+'}updated'), self.article['date_modified'])
        self.assertIn('09:00:00', rss.findtext('channel/lastBuildDate'))
        feed = json.loads((out/'news.json').read_text())['items'][0]
        self.assertEqual(feed['content_html'], body)
        self.assertEqual(feed['date_modified'], self.article['date_modified'])
        self.assertIn('完整长读内容', feed['content_text'])
        self.assertIn('https://example.org/read', feed['content_text'])
        self.assertIn('正文 <script>bad()</script>', feed['content_text'])
        page = (out/'articles'/f"{self.article['id']}.html").read_text()
        self.assertIn(body, page)
        first = (out/'news.xml').read_bytes()
        build(self.root/'content', out, 'https://example.com/project')
        self.assertEqual(first, (out/'news.xml').read_bytes())

    def test_reject_invalid_structured_content_and_urls(self):
        self.structured()
        for url in ('javascript:alert(1)', '//example.org/photo.jpg', '/photo.jpg',
                    'https://user:password@example.org/a', 'https://example.org/\nimg'):
            with self.subTest(url=url):
                self.article['news_items'][0]['image']['url'] = url
                self.write()
                with self.assertRaises(ValueError): load_articles(self.root/'content')
        self.structured()
        self.article['news_items'][0]['sources'][0]['url'] = 'javascript:alert(1)'
        self.write()
        with self.assertRaises(ValueError): load_articles(self.root/'content')
        self.structured()
        self.article['news_items'][0]['body'] = []
        self.write()
        with self.assertRaises(ValueError): load_articles(self.root/'content')
        self.structured()
        self.article['date_modified'] = '2026-10-05T17:00:00+08:00'
        self.write()
        with self.assertRaises(ValueError): load_articles(self.root/'content')

    def test_today_fixture_has_eight_items_three_images_and_separate_long_read(self):
        root = Path(__file__).resolve().parents[1]/'content'
        articles = load_articles(root)
        today = next(a for a in articles if a['id'] == '2026-10-06-news')
        self.assertEqual(len(today['news_items']), 8)
        parsed = BodyParser(today['_html'])
        self.assertEqual(len(parsed.images), 3)
        self.assertFalse({'strong', 'b', 'script'} & set(parsed.tags))
        self.assertNotIn('今日长读', today['_html'])
        reading = next(a for a in articles if a['id'] == '2026-10-06-reads')
        self.assertIn('失落的一代', reading['_html'])
        self.assertGreaterEqual(len(articles), 4)
        self.assertIn('2026-10-06-news-welcome', {a['id'] for a in articles})

    def test_shared_directory_filters_by_category_and_preserves_history(self):
        other = dict(self.article, id='2026-10-06-reads', category='reads', content_text='独立长读全文')
        (self.root/'content/news/reads.json').write_text(json.dumps(other))
        out = self.root/'site'
        build(self.root/'content', out, 'https://example.com/project')
        self.assertEqual(ET.parse(out/'news.xml').findtext('channel/item/guid'), self.article['id'])
        self.assertEqual(ET.parse(out/'reads.xml').findtext('channel/item/guid'), other['id'])
        self.assertEqual(len(ET.parse(out/'feed.xml').findall('channel/item')), 2)

if __name__ == '__main__': unittest.main()
