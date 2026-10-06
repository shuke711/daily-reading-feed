"""Build full-text RSS and JSON Feed from dated JSON articles (stdlib only)."""
import argparse
import html
import json
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

CONTENT = 'http://purl.org/rss/1.0/modules/content/'
ATOM = 'http://www.w3.org/2005/Atom'
ET.register_namespace('content', CONTENT)
ET.register_namespace('atom', ATOM)

def text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{field}: expected nonempty text')
    return html.escape(value, quote=True)

def https_url(value):
    if not isinstance(value, str) or any(c.isspace() or ord(c) < 32 for c in value):
        raise ValueError('URL must be absolute HTTPS')
    url = urlsplit(value)
    if url.scheme != 'https' or not url.hostname or url.username or url.password:
        raise ValueError('URL must be absolute HTTPS without credentials')
    return html.escape(value, quote=True)

def paragraphs(values):
    if not isinstance(values, list) or not values:
        raise ValueError('paragraphs must be a nonempty list')
    return ''.join('<p>' + text(p, 'paragraph') + '</p>' for p in values)

def render_article(a):
    """Render structured data with fixed HTML, never arbitrary source markup.

    Semantic headings survive readers that discard styles. No word emphasis,
    scripts, embedded CSS, lazy-loading or relative media URLs in feed bodies.
    """
    if 'news_items' not in a:
        return ''.join('<p>' + html.escape(p).replace('\n', '<br>') + '</p>'
                       for p in a['content_text'].split('\n\n'))
    news = a['news_items']
    if a['category'] != 'news' or not isinstance(news, list) or not news:
        raise ValueError('news_items must be a nonempty list in news articles')
    body, plain = [], []
    intro = a.get('intro', [])
    if intro:
        body.append(paragraphs(intro))
        plain.extend(intro)
    for number, n in enumerate(news, 1):
        if not isinstance(n, dict):
            raise ValueError('news item must be an object')
        title = text(n.get('title'), 'news title')
        body.append(f'<h2>{number}. {title}</h2>')
        plain.append(f"{number}. {n['title']}")
        if 'image' in n:
            image = n['image']
            if not isinstance(image, dict):
                raise ValueError('image must be an object; omit it for no image')
            src = https_url(image.get('url'))
            alt = text(image.get('alt'), 'image alt')
            credit = text(image.get('credit'), 'image credit')
            credit_url = https_url(image.get('source_url'))
            caption = text(image.get('caption', image['alt']), 'image caption')
            body.append(f'<p><img src="{src}" alt="{alt}" style="max-width:100%;height:auto;"></p>')
            body.append(f'<p><small>{caption} · 图片来源：<a href="{credit_url}">{credit}</a></small></p>')
        body.append(paragraphs(n.get('body')))
        plain.extend(n['body'])
        why = text(n.get('why_it_matters'), 'why_it_matters')
        body.append(f'<h3>为什么值得关注</h3><p>{why}</p>')
        plain.append('为什么值得关注：' + n['why_it_matters'])
        sources = n.get('sources')
        if not isinstance(sources, list) or not sources:
            raise ValueError('sources must be a nonempty list')
        links = []
        for source in sources:
            href = https_url(source.get('url'))
            label = text(source.get('name'), 'source name')
            links.append(f'<a href="{href}">{label}</a>')
            plain.append(f"来源：{source['name']} {source['url']}")
        body.append('<p><small>来源：' + ' · '.join(links) + '</small></p><hr>')
    if a.get('afterword'):
        body.append(paragraphs(a['afterword']))
        plain.extend(a['afterword'])
    sections = a.get('sections', [])
    if not isinstance(sections, list):
        raise ValueError('sections must be a list')
    for section in sections:
        body.append('<h2>' + text(section.get('title'), 'section title') + '</h2>')
        plain.append(section['title'])
        body.append(paragraphs(section.get('paragraphs')))
        plain.extend(section['paragraphs'])
        for source in section.get('sources', []):
            body.append('<p><a href="' + https_url(source.get('url')) + '">' + text(source.get('name'), 'source name') + '</a></p>')
            plain.append(source['name'] + ' ' + source['url'])
    # Both feed representations come from the same structured content.
    a['content_text'] = '\n\n'.join(plain)
    return ''.join(body)

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
        a['_modified'] = datetime.fromisoformat(a.get('date_modified', a['date_published']).replace('Z', '+00:00'))
        if a['_modified'].tzinfo is None or a['_modified'] < a['_date']:
            raise ValueError(f'{path}: invalid date_modified')
        a['_html'] = render_article(a)
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
            ET.SubElement(channel, 'lastBuildDate').text = format_datetime(max(a['_modified'] for a in selected).astimezone(timezone.utc))
        items = []
        for a in selected:
            url = f"{base}/articles/{a['id']}.html"
            item = ET.SubElement(channel, 'item')
            for key, value in [('title', a['title']), ('link', url), ('pubDate', format_datetime(a['_date'].astimezone(timezone.utc))), ('category', a['category']), ('description', a['_html']), ('{'+CONTENT+'}encoded', a['_html'])]:
                ET.SubElement(item, key).text = value
            ET.SubElement(item, '{'+ATOM+'}updated').text = a['_modified'].isoformat()
            ET.SubElement(item, 'guid', {'isPermaLink': 'false'}).text = a['id']
            items.append({'id': a['id'], 'url': url, 'title': a['title'], 'date_published': a['date_published'], 'content_text': a['content_text'], 'content_html': a['_html'], 'tags': [a['category']]})
            if 'date_modified' in a:
                items[-1]['date_modified'] = a['date_modified']
            if a.get('summary'):
                items[-1]['summary'] = a['summary']
        ET.ElementTree(rss).write(output / f'{name}.xml', encoding='utf-8', xml_declaration=True)
        (output / f'{name}.json').write_text(json.dumps({'version': 'https://jsonfeed.org/version/1.1', 'title': title, 'home_page_url': base+'/', 'feed_url': f'{base}/{name}.json', 'items': items}, ensure_ascii=False, indent=2), encoding='utf-8')
    def page(title, body):
        return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+html.escape(title)+'</title><link rel="alternate" type="application/rss+xml" href="'+base+'/feed.xml"><style>body{max-width:760px;margin:40px auto;padding:0 20px;font:18px/1.8 system-ui;color:#26332e}a{color:#21715a}p{overflow-wrap:anywhere}small{color:#667}h2{font-size:1.3em;line-height:1.5;margin:2em 0 .8em}h3{font-size:1em;margin:1.4em 0 .4em}img{max-width:100%;height:auto}hr{border:0;border-top:1px solid #ddd;margin:2em 0}</style><body>'+body+'</body></html>'
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
