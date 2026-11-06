"""Build the official wiki using only explicitly reviewed public content. No dependencies."""
from pathlib import Path
import argparse
import hashlib
import html
import json
import re
import shutil
import tarfile
from catalog import catalog_articles
from augment_candidate import annotate as annotate_augment_candidates
import experience
import build_lab
import loot_finder

ROOT = Path(__file__).resolve().parent
ORIGIN = 'https://wiki.nightcapgame.org'
CATEGORIES = ['Getting started', 'Character', 'Equipment', 'Adventuring', 'World', 'Quests', 'Reference']
ASSET_VERSION = hashlib.sha256(b''.join((ROOT/'assets'/name).read_bytes() for name in ['wiki.css', 'equipment.css', 'experience.css', 'clarity.css', 'build-lab.css', 'loot-finder.css', 'search.js', 'equipment.js', 'experience.js', 'build-lab-model.js', 'build-lab.js', 'loot-finder-model.js', 'loot-finder.js'])).hexdigest()[:12]


def plain(value):
    return html.unescape(re.sub('<[^>]+>', ' ', value))


def link(article):
    return f'<a href="{article["slug"]}.html">{html.escape(article["title"])}</a>'


def load_articles():
    articles = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((ROOT / 'articles').glob('*.json'))]
    articles += catalog_articles()
    articles = annotate_augment_candidates(articles)
    slugs = set()
    for a in articles:
        if not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*', a['slug']) or a['slug'] in slugs:
            raise ValueError('Duplicate or unsafe article slug')
        if a['category'] not in CATEGORIES or a['status'] not in ['Reference', 'Live testing', 'Not released']:
            raise ValueError('Unknown category or release status')
        if not a.get('sources') or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', a['updated']):
            raise ValueError('Articles require dated source provenance')
        if re.search(r'<(?:script|iframe|form|object)|\son\w+\s*=|javascript:', a['body'], re.I):
            raise ValueError('Active content is not allowed in articles')
        slugs.add(a['slug'])
    return articles


def render(title, description, body, page, category='Reference', status='Reference', updated='2026-10-16', toc=''):
    e = html.escape
    nav = [('getting-started', '↗', 'Getting started'), ('multiclass', '✧', 'Classes & AA'), ('combat', '⚔', 'Combat'), ('pets', '◇', 'Pets'),
           ('equipment', '⚒', 'Gear & upgrades'), ('dungeon-modes', '▤', 'Dungeons'), ('travel', '⌁', 'Travel')]
    navigation = ''.join(f'<a href="{slug}.html"'+(' aria-current="page"' if slug == page else '')+f'><span aria-hidden="true">{icon}</span>{label}</a>' for slug, icon, label in nav)
    category_nav = ''.join(f'<a href="{slug}.html">{label}</a>' for slug,label in [('loot-finder','Loot finder'),('items','Hunt rewards'),('zones','Zone directory'),('build-lab','Build Lab'),('commands','Commands')])
    section = page if page in ['index','features','recent-changes'] else 'all-pages'
    tabs = ''.join(f'<a href="{slug}.html"'+(' aria-current="page"' if section==slug else '')+f'>{label}</a>' for slug,label in [('index','Home'),('features','Features'),('all-pages','Guides'),('recent-changes','Change Log')])
    breadcrumb = '<a href="items.html">Equipment</a>' if category == 'Equipment' and page != 'items' else e(category)
    badge = f'<span class="badge {"unreleased" if status == "Not released" else ""}">{e(status)}</span>'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · Nightcap Wiki</title><meta name="description" content="{e(description, quote=True)}">
<meta name="theme-color" content="#102b25"><link rel="canonical" href="{ORIGIN}/{page+'.html' if page != 'index' else ''}">
<link rel="icon" href="assets/moon.svg"><link rel="stylesheet" href="assets/wiki.css?v={ASSET_VERSION}"><script src="assets/search.js?v={ASSET_VERSION}" defer></script></head>
<body data-page="{page}" class="{'home-page' if page == 'index' else 'guide-page'}"><a class="skip" href="#content">Skip to content</a><progress class="reading-progress" max="100" value="0" aria-label="Reading progress" hidden></progress>
<header class="masthead"><a class="brand" href="index.html"><span class="moon" aria-hidden="true">☾</span><span>NIGHTCAP<small>THE OFFICIAL WIKI</small></span></a>
<form class="search" action="search.html" role="search"><label class="sr-only" for="wiki-search">Search the wiki</label><input type="search" id="wiki-search" name="q" placeholder="Search guides, zones, items…" maxlength="160"><button type="submit">Search</button></form><button class="quick-trigger" type="button" data-open-search hidden>Quick search <kbd>/</kbd></button>
<a class="player-site" href="https://play.nightcapgame.org/">Player site <span aria-hidden="true">↗</span><small>Approved players</small></a></header>
<div class="layout"><aside class="sidebar"><details class="navigation" open><summary>Wiki navigation</summary><nav aria-label="Wiki">{navigation}</nav>
<div class="sidebar-categories"><p class="side-label">TOOLS &amp; DIRECTORIES</p><nav aria-label="Tools and directories">{category_nav}</nav></div></details>
<div class="personal-tools" hidden><button type="button" data-open-saved>☆ Saved guides <span data-saved-count>0</span></button><button type="button" data-theme-toggle aria-pressed="false">☼ Light mode</button></div>
<div class="era-note"><span class="side-label">THE CURRENT CHAPTER</span><strong>Classic, reimagined.</strong><span>Level cap 50 · Three classes</span><span>Solo preferred. Friends welcome.</span><a href="features.html">Discover Nightcap →</a></div></aside>
<div class="page"><nav class="page-tabs" aria-label="Wiki sections">{tabs}</nav>
<main id="content" tabindex="-1"><div class="breadcrumb"><a href="index.html">Nightcap Wiki</a><span aria-hidden="true"> / </span>{'Features' if page=='features' else 'Change Log' if page=='recent-changes' else breadcrumb}</div>
<div class="title-row"><h1>{e(title)}</h1>{badge}</div><p class="subtitle">{e(description)}</p><div class="article-tools" hidden><button type="button" data-save-page aria-pressed="false">☆ Save this guide</button><span class="reading-time"></span></div>
{('<aside class="notice">This feature is built but not released. The details below describe the candidate.</aside>' if status == 'Not released' else '')}
<div class="reading-layout">{toc}<article>{body}</article></div>
<div class="article-meta">Reviewed <time datetime="{updated}">{updated}</time> · Official Nightcap guide · <a href="about.html#corrections">Report a correction</a></div></main>
<footer><span>☾ One more adventure before the lights go out.</span><a href="about.html">About &amp; content policy</a><a href="#content">Back to top ↑</a></footer></div></div>{experience.dialogs()}</body></html>'''


def build():
    articles = load_articles()
    out = ROOT / 'dist'
    if out.exists():
        # Delete only this builder's fixed, resolved generated directory.
        if out.is_symlink() or out.resolve().parent != ROOT.resolve():
            raise ValueError('Unsafe output directory')
        shutil.rmtree(out)
    (out / 'assets').mkdir(parents=True)
    for name in ['wiki.css', 'search.js', 'moon.svg', 'traders-at-dusk.png']:
        shutil.copyfile(ROOT / 'assets' / name, out / 'assets' / name)
    # Keep the existing public asset allowlist: bundle the two small browser features.
    (out/'assets/search.js').write_bytes(b'\n'.join((ROOT/'assets'/name).read_bytes() for name in ['search.js', 'equipment.js', 'experience.js', 'build-lab-model.js', 'build-lab.js', 'loot-finder-model.js', 'loot-finder.js']))
    (out/'assets/wiki.css').write_bytes(b'\n'.join((ROOT/'assets'/name).read_bytes() for name in ['wiki.css', 'equipment.css', 'experience.css', 'build-lab.css', 'loot-finder.css', 'clarity.css']))
    for a in articles:
        headings = [(m[0] or m[2],m[1] or m[3]) for m in re.findall(r'<h2 id="([^"]+)">(.+?)</h2>|<details class="guide-topic" id="([^"]+)"><summary>(.+?)</summary>',a['body'])]
        toc = '<nav class="contents" aria-label="On this page"><strong>On this page</strong><ol>'+''.join(f'<li><a href="#{id}">{title}</a></li>' for id,title in headings[:6])+'</ol>'+('<details><summary>More topics</summary><ol>'+''.join(f'<li><a href="#{id}">{title}</a></li>' for id,title in headings[6:])+'</ol></details>' if len(headings)>6 else '')+'</nav>' if len(headings)>1 else ''
        if a['slug'] in ['features','recent-changes']:
            toc = ''
        body = a['body']
        if a['slug'] == 'index':
            body = experience.home(body, {item['slug']: item for item in articles})
            toc = ''
        if a['slug'] == 'build-lab':
            body = build_lab.render() + body
            toc = ''
        if a['slug'] == 'loot-finder':
            body = loot_finder.render() + body
            toc = ''
        (out / (a['slug'] + '.html')).write_text(render(a['title'], a['summary'], body, a['slug'], a['category'], a['status'], a['updated'], toc), encoding='utf-8')
    listing = ''
    maintained = {p.stem for p in (ROOT/'articles').glob('*.json')} | {'items','zones'}
    for i, category in enumerate(CATEGORIES):
        group = sorted([a for a in articles if a['category'] == category and a['slug'] in maintained and a['slug'] not in ['index','features','recent-changes']], key=lambda a: a['title'].lower())
        if category == 'Equipment':
            group = [a for a in group if not a['slug'].startswith('item-')]
            listing += f'<h2 id="category-{i}">Equipment</h2><div class="equipment-directory-link"><a class="button" href="items.html">Browse equipment →</a><p>384 rewards grouped into 96 item families. Filter by type, slot, required level and source zone; compare all four qualities together.</p></div><h3>Equipment guides</h3><ul class="article-list">'+''.join(f'<li>{link(a)}<small>{html.escape(a["summary"])}</small></li>' for a in group if a['slug'] != 'items')+'</ul>'
            continue
        listing += f'<h2 id="category-{i}">{category}</h2><ul class="article-list">'+''.join(f'<li>{link(a)}<small>{html.escape(a["summary"])}</small></li>' for a in group)+'</ul>'
    (out / 'all-pages.html').write_text(render('Guides', 'Find instructions by topic. Use the item and zone directories for individual rewards.', listing, 'all-pages'), encoding='utf-8')
    search_body = '<p id="search-status" role="status" aria-live="polite">Enter a name, command, or topic in the search above.</p><ol id="search-results" class="article-list"></ol><noscript><p>Search needs JavaScript. Browse <a href="all-pages.html">all articles</a>, the <a href="zones.html">zone directory</a> or <a href="items.html">item index</a> instead.</p></noscript>'
    (out / 'search.html').write_text(render('Search the wiki', 'Find a guide, a destination, or your next piece of gear.', search_body, 'search'), encoding='utf-8')
    (out / '404.html').write_text(render('Page not found', 'This trail does not lead to an article.', '<p>Try the search above, <a href="all-pages.html">browse all articles</a>, or return to the <a href="index.html">main page</a>.</p>', '404'), encoding='utf-8')
    index = [{k:a[k] for k in ['slug', 'title', 'summary', 'category', 'status']} | {'keywords':a.get('keywords', []), 'text':re.sub(r'\s+', ' ', plain(a['body']))} for a in articles]
    (out / 'search-index.json').write_text(json.dumps(index, ensure_ascii=False), encoding='utf-8')
    urls = [ORIGIN + ('/' if p.name == 'index.html' else '/' + p.name) for p in sorted(out.glob('*.html')) if p.stem not in ['404', 'search']]
    (out / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{u}</loc></url>' for u in urls)+'</urlset>', encoding='utf-8')
    (out / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {ORIGIN}/sitemap.xml\n', encoding='utf-8')
    return out


def package(out, target):
    target = Path(target)
    if target.exists() or target.with_suffix('.json').exists():
        raise ValueError('Release packages are immutable; choose a new filename')
    files = sorted(p for p in out.rglob('*') if p.is_file())
    manifest = {p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    with tarfile.open(target, 'x:gz') as tar:
        for p in files:
            tar.add(p, arcname=p.relative_to(out).as_posix(), recursive=False)
    target.with_suffix('.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path)
    args = parser.parse_args()
    out = build()
    if args.package:
        package(out, args.package)
    print(f'Built {len(list(out.glob("*.html")))} pages in {out}')
