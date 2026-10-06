"""Build full-text RSS and JSON Feed from dated JSON articles (stdlib only)."""
import argparse
import html
import json
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
import xml.etree.ElementTree as ET

CONTENT = 'http://purl.org/rss/1.0/modules/content/'
ATOM = 'http://www.w3.org/2005/Atom'
ET.register_namespace('content', CONTENT)
ET.register_namespace('atom', ATOM)

def load_articles(root):
    articles, ids = [], set()
    for path in sorted(root.glob('*/*.json')):
        a = json.loads(path.read_text(encoding='utf-8'))
        for key in ('id', 'title', 'date_published', 'content_text', 'category'):
            if not isinstance(a.get(key), str) or not a[key].strip():
                raise ValueError(f'{path}: missing or empty {key}')
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,100}', a['id']):
            raise ValueError(f'{path}: invalid id')
        if a['id'] in ids:
            raise ValueError(f'{path}: duplicate id')
        ids.add(a['id'])
        if a['category'] not in ('news', 'reads'):
            raise ValueError(f'{path}: category must be news or reads')
        a['_date'] = datetime.fromisoformat(a['date_published'].replace('Z', '+00:00'))
        if a['_date'].tzinfo is None:
            raise ValueError(f'{path}: date must include timezone')
        # Escape all source text; no scripts or arbitrary HTML can enter the feed.
        a['_html'] = ''.join('<p>' + html.escape(p).replace('\n', '<br>') + '</p>'
                             for p in a['content_text'].split('\n\n'))
        articles.append(a)
    return sorted(articles, key=lambda a: (a['_date'], a['id']), reverse=True)

def build(source, output, base):
    if not base.startswith('https://') or '?' in base or '#' in base:
        raise ValueError('base URL must be an HTTPS URL without query or fragment')
    base = base.rstrip('/')
    articles = load_articles(source)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'articles').mkdir(exist_ok=True)
    for name, category, title in [('feed', None, '每日阅读'), ('news', 'news', '每日新闻简报'), ('reads', 'reads', '每日长文精读')]:
        selected = [a for a in articles if category is None or a['category'] == category]
        rss = ET.Element('rss', {'version': '2.0'})
        channel = ET.SubElement(rss, 'channel')
        for key, value in [('title', title), ('link', base + '/'), ('description', title + ' · 全文订阅'), ('language', 'zh-CN')]:
            ET.SubElement(channel, key).text = value
        ET.SubElement(channel, '{'+ATOM+'}link', {'href': f'{base}/{name}.xml', 'rel': 'self', 'type': 'application/rss+xml'})
        if selected:
            ET.SubElement(channel, 'lastBuildDate').text = format_datetime(selected[0]['_date'].astimezone(timezone.utc))
        items = []
        for a in selected:
            url = f"{base}/articles/{a['id']}.html"
            item = ET.SubElement(channel, 'item')
            for key, value in [('title', a['title']), ('link', url), ('pubDate', format_datetime(a['_date'].astimezone(timezone.utc))), ('category', a['category']), ('description', a.get('summary', a['content_text'][:180])), ('{'+CONTENT+'}encoded', a['_html'])]:
                ET.SubElement(item, key).text = value
            ET.SubElement(item, 'guid', {'isPermaLink': 'false'}).text = a['id']
            items.append({'id': a['id'], 'url': url, 'title': a['title'], 'date_published': a['date_published'], 'content_text': a['content_text'], 'content_html': a['_html'], 'tags': [a['category']]})
        ET.ElementTree(rss).write(output / f'{name}.xml', encoding='utf-8', xml_declaration=True)
        (output / f'{name}.json').write_text(json.dumps({'version': 'https://jsonfeed.org/version/1.1', 'title': title, 'home_page_url': base+'/', 'feed_url': f'{base}/{name}.json', 'items': items}, ensure_ascii=False, indent=2), encoding='utf-8')
    def page(title, body):
        return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+html.escape(title)+'</title><link rel="alternate" type="application/rss+xml" href="'+base+'/feed.xml"><style>body{max-width:760px;margin:48px auto;padding:0 24px;font:18px/1.8 system-ui;color:#26332e}a{color:#21715a}p{overflow-wrap:anywhere}small{color:#667}</style><body>'+body+'</body></html>'
    links = ''
    for a in articles:
        filename = 'articles/'+a['id']+'.html'
        (output / filename).write_text(page(a['title'], '<a href="../">每日阅读</a><h1>'+html.escape(a['title'])+'</h1><small>'+html.escape(a['date_published'])+'</small>'+a['_html']), encoding='utf-8')
        links += '<li><a href="'+filename+'">'+html.escape(a['title'])+'</a></li>'
    (output / 'index.html').write_text(page('每日阅读', '<h1>每日阅读</h1><p>新闻简报与长文精读，在 Reeder 中阅读全文。</p><p><a href="feed.xml">全部 RSS</a> · <a href="news.xml">新闻 RSS</a> · <a href="reads.xml">长文 RSS</a></p><ul>'+links+'</ul>'), encoding='utf-8')
    (output / '.nojekyll').touch()
    print(f'Built {len(articles)} articles and 3 full-text feeds.')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--base-url', required=True)
    p.add_argument('--source', type=Path, default=Path('content'))
    p.add_argument('--output', type=Path, default=Path('_site'))
    args = p.parse_args()
    build(args.source, args.output, args.base_url)
