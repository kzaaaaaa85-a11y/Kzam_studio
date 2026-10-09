#!/usr/bin/env python3
"""Kzam Studio blog tools. Run from the repository root.

    python3 _tools/blog.py status            what is pending, drafted, published
    python3 _tools/blog.py next              the next topic to write
    python3 _tools/blog.py draft <slug>      validate a draft, render its reel, cover, preview, instagram.txt
    python3 _tools/blog.py publish <slug>    move a draft to the live blog and rebuild
    python3 _tools/blog.py discard <slug>    drop a draft and put its topic back in the queue
    python3 _tools/blog.py build             rebuild blog pages, sitemap, homepage blocks
    python3 _tools/blog.py selftest          check this machine can render reels

Layout (folders starting with "_" are never served by GitHub Pages):
    _content/topics.json              keyword queue; each topic has a pillar (cafe, restaurant, landing)
    _content/drafts/<slug>/post.json  a draft waiting for approval (+ reel.mp4, cover.jpg)
    _content/posts/<slug>.json        a published post
    blog/<slug>/                      generated page + its reel and cover
"""
import base64, datetime, html, json, os, re, shutil, subprocess, sys
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://kzamstudio.com'
BRAND = 'Kzam Studio'
WHATSAPP = 'https://wa.me/33777897299'
CONTENT = os.path.join(ROOT, '_content')
DRAFTS = os.path.join(CONTENT, 'drafts')
POSTS = os.path.join(CONTENT, 'posts')
TOPICS = os.path.join(CONTENT, 'topics.json')
BLOG = os.path.join(ROOT, 'blog')
MONTHS = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس',
          'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']

# Phrases that make Arabic copy read as machine-written. A draft containing one fails.
BANNED = ['في عالم اليوم', 'في عصرنا', 'هل تعاني', 'ليس مجرد', 'ليست مجرد', 'لا يخفى على أحد',
          'مما لا شك فيه', 'بلا شك', 'حلول مبتكرة', 'نقلة نوعية', 'في هذا المقال سنتعرف',
          'في هذه المقالة سنتعرف', 'تجربة فريدة', 'على أعلى مستوى', 'لا مثيل له', '!!', '—',
          'في الختام', 'وفي الختام', 'بكل سهولة ويسر']


def today():
    return datetime.datetime.now(ZoneInfo('Europe/Paris')).date().isoformat()


def read_json(path):
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write('\n')


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(text)


def e(text):
    return html.escape(str(text), quote=True)


def inline(text):
    """Escape, then allow **bold** and [text](url) for our own links only."""
    out = e(text)
    out = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', out)

    def link(m):
        url = html.unescape(m.group(2))
        if url.startswith('/') or url.startswith(SITE) or url.startswith(WHATSAPP):
            return f'<a href="{e(url)}">{m.group(1)}</a>'
        return m.group(1)
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link, out)


def ar_date(iso):
    y, m, d = (int(x) for x in iso.split('-'))
    return f'{d} {MONTHS[m - 1]} {y}'


def body_text(post):
    parts = []
    for b in post.get('body', []):
        if b.get('type') in ('p', 'h2', 'h3'):
            parts.append(b.get('text', ''))
        elif b.get('type') in ('ul', 'ol'):
            parts.extend(b.get('items', []))
        elif b.get('type') == 'box':
            parts.extend([b.get('title', ''), b.get('text', '')])
    return '\n'.join(parts)


def validate(post, slug):
    errs, warns = [], []
    need = ['slug', 'keyword', 'title', 'description', 'h1', 'body', 'reel', 'instagram']
    for k in need:
        if not post.get(k):
            errs.append(f'missing field: {k}')
    if errs:
        return errs, warns
    kw = post['keyword']
    if post['slug'] != slug:
        errs.append('slug in post.json does not match its folder name')
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', slug) or len(slug) > 60:
        errs.append('slug must be lowercase latin words joined by hyphens, 60 chars max')
    if os.path.exists(os.path.join(POSTS, slug + '.json')):
        errs.append('a published post already uses this slug')
    if not 30 <= len(post['title']) <= 60:
        errs.append(f'title is {len(post["title"])} chars, needs 30-60')
    if not 110 <= len(post['description']) <= 160:
        errs.append(f'description is {len(post["description"])} chars, needs 110-160')
    for field in ('title', 'h1', 'description'):
        if kw not in post[field]:
            errs.append(f'keyword "{kw}" must appear word for word in {field}')
    body = post['body']
    if not body or body[0].get('type') != 'p':
        errs.append('body must start with a paragraph')
    elif kw not in body[0].get('text', ''):
        errs.append('keyword must appear in the first paragraph')
    if sum(1 for b in body if b.get('type') == 'h2') < 3:
        errs.append('body needs at least 3 h2 sections')
    for b in body:
        if b.get('type') not in ('p', 'h2', 'h3', 'ul', 'ol', 'box'):
            errs.append(f'unknown block type: {b.get("type")}')
    text = body_text(post)
    words = len(text.split())
    if words < 450:
        errs.append(f'body has {words} words, needs at least 450')
    everything = '\n'.join([post['title'], post['description'], post['h1'], text,
                            post['instagram'].get('caption', ''),
                            json.dumps(post['reel'], ensure_ascii=False)])
    for phrase in BANNED:
        if phrase in everything:
            errs.append(f'banned phrase: "{phrase}"')
    reel = post['reel']
    hook = reel.get('hook', [])
    if not 1 <= len(hook) <= 3:
        errs.append('reel.hook needs 1-3 lines')
    for line in hook:
        if len(line) > 26:
            errs.append(f'reel hook line too long ({len(line)} chars, max 26): {line}')
    pts = reel.get('points', [])
    if not 3 <= len(pts) <= 5:
        errs.append('reel.points needs 3-5 items')
    for p in pts:
        if len(p.get('title', '')) > 34 or not p.get('title'):
            errs.append(f'reel point title must be 1-34 chars: {p.get("title")}')
        if len(p.get('sub', '')) > 44:
            errs.append(f'reel point sub too long (max 44): {p.get("sub")}')
    if not reel.get('cta'):
        errs.append('reel.cta needs 1-2 lines')
    ig = post['instagram']
    if len(ig.get('caption', '')) < 80:
        errs.append('instagram.caption is too short')
    if not 5 <= len(ig.get('hashtags', [])) <= 12:
        errs.append('instagram.hashtags needs 5-12 tags')
    emoji = re.findall('[\U0001F300-\U0001FAFF☀-➿]', ig.get('caption', ''))
    if len(emoji) > 2:
        errs.append('instagram.caption has more than 2 emojis')
    if kw not in text[len(body[0].get('text', '')):]:
        warns.append('keyword appears only in the intro; use it once more further down')
    return errs, warns


# ---------------------------------------------------------------- templates

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
:root{--gold:#D4AF37;--brown:#3E2723;--light-brown:#5D4037;--cream:#F5F1E8;--white:#FFF;--text:#2C2C2C;--muted:#6B5E57}
body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;line-height:1.9;color:var(--text);background:var(--cream)}
a{color:var(--light-brown)}
header{background:var(--brown);padding:.6rem 1.25rem;position:sticky;top:0;z-index:10;box-shadow:0 2px 8px rgba(0,0,0,.15)}
.nav{max-width:1100px;margin:0 auto;display:flex;justify-content:space-between;align-items:center;gap:1rem}
.logo{color:var(--gold);font-weight:bold;font-size:1.25rem;text-decoration:none;white-space:nowrap}
.nav ul{display:flex;gap:.4rem;list-style:none}
.nav ul a{color:var(--white);text-decoration:none;display:inline-flex;align-items:center;min-height:44px;padding:0 .5rem;font-size:.95rem}
.nav ul a:hover{color:var(--gold)}
main{max-width:780px;margin:0 auto;padding:2rem 1.25rem 3rem}
.crumbs{font-size:.85rem;color:var(--muted);margin-bottom:1.25rem}
.crumbs a{color:var(--muted)}
h1{font-size:2rem;line-height:1.35;color:var(--brown);margin-bottom:.75rem}
.meta{color:var(--muted);font-size:.9rem;margin-bottom:1.5rem}
article p{margin-bottom:1.1rem;font-size:1.08rem}
article h2{font-size:1.45rem;color:var(--brown);margin:2.2rem 0 .8rem;line-height:1.4}
article h3{font-size:1.15rem;color:var(--light-brown);margin:1.5rem 0 .5rem}
article ul,article ol{margin:0 1.4rem 1.2rem 0;font-size:1.08rem}
article li{margin-bottom:.5rem}
.box{background:var(--white);border-right:4px solid var(--gold);border-radius:8px;padding:1rem 1.25rem;margin:1.25rem 0;box-shadow:0 2px 8px rgba(0,0,0,.05)}
.box strong{display:block;color:var(--brown);margin-bottom:.35rem}
.box p{white-space:pre-line;margin:0;font-size:1.02rem}
.reel{margin:1.5rem auto 2rem;max-width:300px}
.reel video,.reel img{width:100%;aspect-ratio:9/16;display:block;border-radius:16px;border:3px solid var(--gold);background:#000;object-fit:cover}
.reel figcaption{text-align:center;font-size:.9rem;color:var(--muted);margin-top:.5rem}
.cta{background:var(--brown);color:var(--white);border-radius:14px;padding:1.75rem 1.5rem;margin:2.5rem 0;text-align:center}
.cta h2{color:var(--gold);font-size:1.35rem;margin:0 0 .5rem}
.cta p{margin-bottom:1.1rem;font-size:1rem}
.btn{display:inline-block;background:var(--gold);color:var(--brown);font-weight:bold;text-decoration:none;padding:.8rem 2rem;border-radius:50px;margin:.25rem}
.btn.ghost{background:transparent;color:var(--gold);border:2px solid var(--gold)}
.cards{display:grid;gap:1rem;margin-top:1rem}
.card{display:block;background:var(--white);border-radius:10px;padding:1.1rem 1.25rem;text-decoration:none;color:var(--text);border-top:3px solid var(--gold);box-shadow:0 2px 8px rgba(0,0,0,.05)}
.card h3,.card h2{color:var(--brown);font-size:1.15rem;margin:0 0 .3rem;line-height:1.5}
.card p{font-size:.95rem;color:var(--muted);margin:0}
.card span{display:block;font-size:.8rem;color:var(--muted);margin-top:.5rem}
.related h2{font-size:1.25rem;color:var(--brown);margin-top:2.5rem}
.draft{background:#8a1c1c;color:#fff;text-align:center;padding:.6rem;font-weight:bold}
footer{background:var(--brown);color:var(--white);text-align:center;padding:1.75rem 1rem;font-size:.9rem}
footer a{color:var(--gold);text-decoration:none;display:inline-flex;align-items:center;min-height:44px;padding:0 .5rem}
@media (max-width:600px){h1{font-size:1.55rem}article h2{font-size:1.25rem}.logo{font-size:1.05rem}.nav ul a{padding:0 .35rem;font-size:.9rem}}
"""

HEADER = """<header><div class="nav"><a class="logo" href="/">🎨 Kzam Studio</a><ul>
<li><a href="/">الرئيسية</a></li><li><a href="/blog/">المدونة</a></li><li><a href="/#pricing">الأسعار</a></li>
</ul></div></header>"""

FOOTER = f"""<footer><p>&copy; {today()[:4]} Kzam Studio. جميع الحقوق محفوظة.</p>
<p><a href="{WHATSAPP}" target="_blank" rel="noopener">واتساب: 33777897299+</a> | <a href="mailto:kzaaaaaa85@gmail.com">kzaaaaaa85@gmail.com</a> | <a href="https://www.instagram.com/kzam_studo/" target="_blank" rel="noopener">انستقرام: kzam_studo@</a></p></footer>"""

CTA = f"""<aside class="cta"><h2>30 تصميم انستقرام جاهز لمطعمك أو مقهاك كل شهر</h2>
<p>نصوص عربية وقوالب Canva تعدّلها بنفسك. الاشتراك من 15 دولار في الشهر.</p>
<a class="btn" href="/#pricing">شوف الباقات</a>
<a class="btn ghost" href="{WHATSAPP}" target="_blank" rel="noopener">اسأل على واتساب</a>
<a class="btn ghost" href="/#lead">اترك رقمك ونكلمك</a></aside>"""


def head(title, description, canonical, og_type, image=None, extra='', noindex=False, preview=False):
    img_src = "'self' data:" if preview else "'self'"
    robots = '<meta name="robots" content="noindex, nofollow">\n' if noindex else ''
    og_img = (f'<meta property="og:image" content="{e(image)}">\n'
              '<meta name="twitter:card" content="summary_large_image">\n') if image else ''
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src {img_src}; media-src 'self'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="theme-color" content="#3E2723">
{robots}<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(canonical)}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:locale" content="ar_AR">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(canonical)}">
{og_img}{extra}<style>{CSS}</style>
</head>
<body>
"""


def render_body(blocks):
    out = []
    for b in blocks:
        t = b['type']
        if t == 'p':
            out.append(f'<p>{inline(b["text"])}</p>')
        elif t in ('h2', 'h3'):
            out.append(f'<{t}>{inline(b["text"])}</{t}>')
        elif t in ('ul', 'ol'):
            items = ''.join(f'<li>{inline(i)}</li>' for i in b['items'])
            out.append(f'<{t}>{items}</{t}>')
        elif t == 'box':
            out.append(f'<div class="box"><strong>{inline(b.get("title", ""))}</strong>'
                       f'<p>{inline(b["text"])}</p></div>')
    return '\n'.join(out)


def card(post, tag='h3'):
    return (f'<a class="card" href="/blog/{post["slug"]}/"><{tag}>{e(post["h1"])}</{tag}>'
            f'<p>{e(post["description"])}</p><span>{ar_date(post["date"])}</span></a>')


def article_html(post, others, preview_cover=None):
    slug = post['slug']
    url = f'{SITE}/blog/{slug}/'
    date = post.get('date') or today()
    minutes = max(2, round(len(body_text(post).split()) / 180))
    seconds = int(round(post.get('reel_seconds', 14)))
    ld = [{
        '@context': 'https://schema.org', '@type': 'BlogPosting',
        'headline': post['title'], 'description': post['description'],
        'inLanguage': 'ar', 'datePublished': date, 'dateModified': post.get('updated', date),
        'image': f'{url}cover.jpg', 'mainEntityOfPage': url,
        'author': {'@type': 'Organization', 'name': BRAND, 'url': SITE + '/'},
        'publisher': {'@type': 'Organization', 'name': BRAND, 'url': SITE + '/'},
    }, {
        '@context': 'https://schema.org', '@type': 'VideoObject',
        'name': post['h1'], 'description': post.get('reel_caption') or post['description'],
        'thumbnailUrl': f'{url}cover.jpg', 'uploadDate': date + 'T08:00:00+02:00',
        'duration': f'PT{seconds}S', 'contentUrl': f'{url}reel.mp4',
    }, {
        '@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'الرئيسية', 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'المدونة', 'item': SITE + '/blog/'},
            {'@type': 'ListItem', 'position': 3, 'name': post['h1'], 'item': url}]}]
    extra = ('<script type="application/ld+json">'
             + json.dumps(ld, ensure_ascii=False).replace('</', '<\\/') + '</script>\n')
    preview = preview_cover is not None
    page = head(f'{post["title"]} | {BRAND}', post['description'], url, 'article',
                image=f'{url}cover.jpg', extra=extra, noindex=preview, preview=preview)
    if preview:
        page += '<div class="draft">مسودة للمراجعة: غير منشورة على الموقع</div>\n'
        media = (f'<img src="data:image/jpeg;base64,{preview_cover}" alt="غلاف الريلز">'
                 '<figcaption>غلاف الريلز. الفيديو مرفق كملف مستقل.</figcaption>')
    else:
        media = ('<video controls playsinline muted loop preload="metadata" poster="cover.jpg">'
                 '<source src="reel.mp4" type="video/mp4"></video>'
                 f'<figcaption>{e(post.get("reel_caption", ""))}</figcaption>')
    body = post['body']
    related = ''
    if others:
        related = ('<section class="related"><h2>مقالات أخرى</h2><div class="cards">'
                   + ''.join(card(p) for p in others[:3]) + '</div></section>')
    page += f"""{HEADER}
<main>
<nav class="crumbs" aria-label="مسار الصفحة"><a href="/">الرئيسية</a> ‹ <a href="/blog/">المدونة</a></nav>
<article>
<h1>{e(post['h1'])}</h1>
<p class="meta">{ar_date(date)} · قراءة {minutes} دقائق</p>
{render_body(body[:1])}
<figure class="reel">{media}</figure>
{render_body(body[1:])}
</article>
{CTA}
{related}
</main>
{FOOTER}
</body>
</html>
"""
    return page


def index_html(posts):
    title = f'مدونة تسويق المطاعم والمقاهي على انستقرام | {BRAND}'
    desc = ('أفكار منشورات وريلز وكابشن جاهزة لأصحاب المطاعم والمقاهي والكافيهات، '
            'مقال جديد كل يوم مع ريلز قصير يلخصه.')
    page = head(title, desc, f'{SITE}/blog/', 'website')
    cards = ''.join(card(p, 'h2') for p in posts)
    page += f"""{HEADER}
<main>
<h1>مدونة تسويق المطاعم والمقاهي على انستقرام</h1>
<p class="meta">{e(desc)}</p>
<div class="cards">{cards}</div>
{CTA}
</main>
{FOOTER}
</body>
</html>
"""
    return page


def published():
    posts = []
    if os.path.isdir(POSTS):
        for name in os.listdir(POSTS):
            if name.endswith('.json'):
                posts.append(read_json(os.path.join(POSTS, name)))
    posts.sort(key=lambda p: (p['date'], p.get('order', 0), p['slug']), reverse=True)
    return posts


def replace_block(text, name, content):
    pattern = re.compile(rf'(<!-- {name}:start -->).*?(<!-- {name}:end -->)', re.S)
    if not pattern.search(text):
        sys.exit(f'index.html is missing the {name} markers')
    return pattern.sub(lambda m: m.group(1) + content + m.group(2), text)


def build():
    posts = published()
    for i, post in enumerate(posts):
        others = [p for p in posts if p['slug'] != post['slug']]
        folder = os.path.join(BLOG, post['slug'])
        for media in ('reel.mp4', 'cover.jpg'):
            if not os.path.exists(os.path.join(folder, media)):
                sys.exit(f'blog/{post["slug"]}/{media} is missing')
        write_text(os.path.join(folder, 'index.html'), article_html(post, others))
    home_path = os.path.join(ROOT, 'index.html')
    with open(home_path, encoding='utf-8') as fh:
        home = fh.read()
    if posts:
        write_text(os.path.join(BLOG, 'index.html'), index_html(posts))
        nav = '<li><a href="/blog/">المدونة</a></li>'
        latest = ('\n    <section class="latest" id="blog">\n        <div class="container">\n'
                  '            <h2 class="section-title">آخر المقالات</h2>\n'
                  '            <div class="latest-grid">'
                  + ''.join(f'<a class="latest-card" href="/blog/{p["slug"]}/"><h3>{e(p["h1"])}</h3>'
                            f'<p>{e(p["description"])}</p></a>' for p in posts[:3])
                  + '</div>\n            <p class="latest-more"><a href="/blog/">كل المقالات</a></p>\n'
                  '        </div>\n    </section>\n    ')
    else:
        nav, latest = '', ''
    home = replace_block(home, 'blog-nav', nav)
    home = replace_block(home, 'blog-latest', latest)
    write_text(home_path, home)
    urls = [(SITE + '/', posts[0]['date'] if posts else today())]
    if posts:
        urls.append((SITE + '/blog/', posts[0]['date']))
        urls += [(f'{SITE}/blog/{p["slug"]}/', p.get('updated', p['date'])) for p in posts]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    xml += [f'  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>' for u, d in urls]
    xml.append('</urlset>')
    write_text(os.path.join(ROOT, 'sitemap.xml'), '\n'.join(xml) + '\n')
    print(f'built {len(posts)} post(s), sitemap has {len(urls)} url(s)')


# One pillar per day, in this order, so the feed never shows the same subject twice in a row.
PILLARS = ['cafe', 'restaurant', 'landing']
REEL_THEME = {'cafe': 'coffee', 'restaurant': 'teal', 'landing': 'night'}


def set_topic(slug_or_keyword, **fields):
    topics = read_json(TOPICS)
    for t in topics:
        if t.get('slug') == slug_or_keyword or t['keyword'] == slug_or_keyword:
            t.update(fields)
    write_json(TOPICS, topics)


def draft(slug):
    folder = os.path.join(DRAFTS, slug)
    post_path = os.path.join(folder, 'post.json')
    if not os.path.exists(post_path):
        sys.exit(f'no draft at _content/drafts/{slug}/post.json')
    post = read_json(post_path)
    errs, warns = validate(post, slug)
    for w in warns:
        print('warning:', w)
    if errs:
        print('\n'.join('error: ' + x for x in errs))
        sys.exit(1)
    topics = read_json(TOPICS)
    topic = next((t for t in topics if t['keyword'] == post['keyword']), {})
    post['reel'].setdefault('theme', REEL_THEME.get(topic.get('pillar'), 'coffee'))
    seq = topic.get('seq') or max([t.get('seq', 0) for t in topics] + [0]) + 1
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_reel
    seconds = make_reel.render(post['reel'], os.path.join(folder, 'reel.mp4'),
                               os.path.join(folder, 'cover.jpg'))
    post['reel_seconds'] = seconds
    write_json(post_path, post)
    with open(os.path.join(folder, 'cover.jpg'), 'rb') as fh:
        cover = base64.b64encode(fh.read()).decode()
    write_text(os.path.join(folder, 'preview.html'), article_html(post, published(), cover))
    ig = post['instagram']
    write_text(os.path.join(folder, 'instagram.txt'),
               ig['caption'].strip() + '\n\n' + ' '.join(ig['hashtags']) + '\n')
    set_topic(post['keyword'], status='drafted', slug=slug, seq=seq)
    words = len(body_text(post).split())
    print(f'draft ok: {slug} | {words} words | reel {seconds}s')
    print(f'files: _content/drafts/{slug}/reel.mp4, cover.jpg, preview.html, instagram.txt')


def publish(slug):
    folder = os.path.join(DRAFTS, slug)
    post_path = os.path.join(folder, 'post.json')
    if not os.path.exists(post_path):
        sys.exit(f'no draft at _content/drafts/{slug}/post.json')
    for media in ('reel.mp4', 'cover.jpg'):
        if not os.path.exists(os.path.join(folder, media)):
            sys.exit(f'{media} is missing: run "draft {slug}" first')
    post = read_json(post_path)
    errs, _ = validate(post, slug)
    if errs:
        print('\n'.join('error: ' + x for x in errs))
        sys.exit(1)
    post['date'] = today()
    post['order'] = len(published())
    target = os.path.join(BLOG, slug)
    os.makedirs(target, exist_ok=True)
    for media in ('reel.mp4', 'cover.jpg'):
        shutil.move(os.path.join(folder, media), os.path.join(target, media))
    write_json(os.path.join(POSTS, slug + '.json'), post)
    shutil.rmtree(folder)
    set_topic(post['keyword'], status='published', slug=slug)
    build()
    print(f'published: {SITE}/blog/{slug}/')


def discard(slug):
    folder = os.path.join(DRAFTS, slug)
    if not os.path.isdir(folder):
        sys.exit(f'no draft named {slug}')
    shutil.rmtree(folder)
    set_topic(slug, status='pending')
    print(f'discarded draft {slug}; its topic is pending again')


def drafts_list():
    if not os.path.isdir(DRAFTS):
        return []
    return sorted(d for d in os.listdir(DRAFTS)
                  if os.path.exists(os.path.join(DRAFTS, d, 'post.json')))


def status():
    topics = read_json(TOPICS)
    pending = [t for t in topics if t.get('status', 'pending') == 'pending']
    print(f'topics pending: {len(pending)} of {len(topics)}')
    print('pending by pillar: ' + ', '.join(
        f'{p} {sum(1 for t in pending if t.get("pillar") == p)}' for p in PILLARS))
    d = drafts_list()
    print(f'drafts waiting for approval: {len(d)}' + (': ' + ', '.join(d) if d else ''))
    held = [x for x in d if os.path.exists(os.path.join(DRAFTS, x, 'HOLD'))]
    if held:
        print('on hold (skip in the evening auto-publish): ' + ', '.join(held))
    posts = published()
    print(f'published posts: {len(posts)}')
    for p in posts[:5]:
        print(f'  {p["date"]}  /blog/{p["slug"]}/  {p["keyword"]}')


def next_topic():
    """The next pending topic from the pillar that follows the last one written."""
    topics = read_json(TOPICS)
    pending = [t for t in topics if t.get('status', 'pending') == 'pending']
    used = [t for t in topics if t.get('seq')]
    last = max(used, key=lambda t: t['seq']).get('pillar') if used else PILLARS[-1]
    start = (PILLARS.index(last) + 1) % len(PILLARS) if last in PILLARS else 0
    order = PILLARS[start:] + PILLARS[:start]
    for pillar in order:
        for t in pending:
            if t.get('pillar') == pillar:
                if pillar != order[0]:
                    print(f'NOTE: no pending topic in pillar "{order[0]}", add some to topics.json')
                print(json.dumps(t, ensure_ascii=False, indent=2))
                return
    if pending:
        print(json.dumps(pending[0], ensure_ascii=False, indent=2))
        return
    print('NO_PENDING_TOPICS')


def selftest():
    import tempfile
    from PIL import features
    result = {'when': datetime.datetime.now(ZoneInfo('Europe/Paris')).isoformat(timespec='seconds')}
    result['raqm'] = bool(features.check('raqm'))
    result['ffmpeg'] = shutil.which('ffmpeg') is not None
    result['font'] = os.path.exists(os.path.join(ROOT, '_tools', 'fonts', 'Cairo.ttf'))
    ok = all([result['raqm'], result['ffmpeg'], result['font']])
    if ok:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import make_reel
        make_reel.T_HOOK = make_reel.T_POINT = make_reel.T_END = 0.3
        tmp = tempfile.mkdtemp()
        spec = {'hook': ['اختبار', 'الريلز'], 'points': [{'title': 'واحد'}, {'title': 'اثنين'},
                {'title': 'ثلاثة'}], 'cta': ['تمام']}
        make_reel.render(spec, os.path.join(tmp, 'r.mp4'), os.path.join(tmp, 'c.jpg'))
        result['reel_bytes'] = os.path.getsize(os.path.join(tmp, 'r.mp4'))
        ok = result['reel_bytes'] > 10000
    result['ok'] = ok
    write_json(os.path.join(CONTENT, 'healthcheck.json'), result)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    os.chdir(ROOT)
    args = sys.argv[1:]
    cmd = args[0] if args else ''
    if cmd == 'status':
        status()
    elif cmd == 'next':
        next_topic()
    elif cmd == 'build':
        build()
    elif cmd == 'selftest':
        selftest()
    elif cmd in ('draft', 'publish', 'discard') and len(args) == 2:
        {'draft': draft, 'publish': publish, 'discard': discard}[cmd](args[1])
    else:
        sys.exit(__doc__)
