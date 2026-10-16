"""Generate linked zone and item articles from the reviewed, public-only catalog."""
import html
import json
from pathlib import Path
from equipment import equipment_directory

ROOT = Path(__file__).resolve().parent
QUALITIES = ['Base', 'Polished', 'Exalted', 'Ascension']


def catalog_articles():
    data = json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8'))
    articles = []

    def add(slug, title, summary, body, category):
        articles.append(dict(slug=slug, title=title, summary=summary, body=body,
                             category=category, status='Live testing', updated=data['updated'],
                             sources=data['sources']))

    for z in data['zones']:
        rows = [i for i in data['items'] if i['zone'] == z['slug']]
        body = '<p>This page covers Nightcap’s custom rewards in this zone. It is not a complete camp, map, or ordinary loot guide.</p>'
        body += '<h2 id="rewards">Zone rewards</h2><div class="table-scroll"><table><caption>Both reward families, at every quality</caption><thead><tr><th scope="col">Item</th><th scope="col">Family</th><th scope="col">Quality</th><th scope="col">Required level</th></tr></thead><tbody>'
        for i in rows:
            body += f'<tr><td><a href="item-{i["id"]}.html">{html.escape(i["name"])}</a></td><td>{i["kind"]}</td><td>{QUALITIES[i["tier"]]}</td><td>{i["required_level"]}</td></tr>'
        body += '</tbody></table></div><h2 id="finding-rewards">Finding these rewards</h2><p>Eligible native enemies have an independent 0.5% roll for the augment family and 0.5% for the gear family. Both may drop together. A successful family roll then chooses Base (60%), Polished (30%), Exalted (8%), or Ascension (2%). Ordinary loot remains.</p><p>Only the zone’s approved native enemies qualify. Pets, merchants, hub residents, summoned copies and city services do not. There is no guaranteed drop or pity timer.</p>'
        if z['slug'] == 'kithicor':
            body += '<p><strong>Kithicor requires eligible nighttime undead.</strong></p>'
        body += '<h2 id="upgrading">Upgrading your finds</h2><p>Forge three identical Base copies into Polished, then four Polished into Exalted or four Exalted into Ascension. Read <a href="zone-hunt.html#forging">the forging guide</a> before using <code>#zoneforge</code>. All new zone rewards have zero merchant resale value.</p><p><a href="zones.html">Browse all 48 reward zones →</a></p>'
        add('zone-'+z['slug'], z['name'], 'Custom augment and equipment rewards · Classic era.', body, 'World')
        for i in rows:
            e = html.escape
            details = [('Quality', QUALITIES[i['tier']]), ('Family', i['kind']), ('Required level', i['required_level']), ('Recommended level', i['recommended_level']), ('Slot', i['slot']), ('Classes / races', 'All'), ('Merchant resale', 'None')]
            details += list(i['stats'].items())
            body = '<h2 id="stats">Item details</h2><table class="item-stats"><caption>Published item values</caption><tbody>'+''.join(f'<tr><th scope="row">{e(str(k))}</th><td>{e(str(v))}</td></tr>' for k,v in details)+'</tbody></table>'
            if i['kind'] == 'Augment':
                body += '<p>Fits a type-22 socket in eligible head, arms, hands, chest, legs or feet armor. Required levels and item compatibility still apply. See <a href="zone-hunt.html#sockets">sockets and heroic stat limits</a>.</p>'
            elif i['socket']:
                body += '<p>Includes one type-22 augment socket. See <a href="zone-hunt.html#sockets">the augment guide</a>.</p>'
            body += f'<h2 id="source">Where to find it</h2><p>From the <a href="zone-{z["slug"]}.html">{e(z["name"])}</a> reward pool. This family rolls at 0.5% per eligible kill, followed by the quality roll. <strong>{QUALITIES[i["tier"]]}</strong> is {[60,30,8,2][i["tier"]]}% of successful family rolls, not of all kills. See the zone page for eligibility.</p>'
            body += '<h2 id="quality">Quality family</h2><ul>'
            for sibling in rows:
                if sibling['kind'] == i['kind']:
                    body += f'<li><a href="item-{sibling["id"]}.html">{e(sibling["name"])}</a> · {QUALITIES[sibling["tier"]]}</li>'
            body += '</ul><p>Use <a href="zone-hunt.html#forging">#zoneforge</a> with three identical Base copies or four identical Polished/Exalted copies for the next quality. The <a href="item-upgrades.html#box">Reforging Box</a> also handles the four-copy steps. Ascension is the final quality. These items can be traded, but cannot be sold to merchants.</p>'
            add('item-'+str(i['id']), i['name'], f'{QUALITIES[i["tier"]]} {i["kind"].lower()} · {z["name"]} · Required level {i["required_level"]}.', body, 'Equipment')
    zone_links = ''.join(f'<li><a href="zone-{z["slug"]}.html">{html.escape(z["name"])}</a></li>' for z in sorted(data['zones'], key=lambda z:z['name']))
    add('zones', 'Zones & rewards', 'Explore all 48 enabled Classic reward zones.', '<p>Each listed zone has one custom augment family and one equipment family. Click a zone for all four qualities and their item details. The level shown on an item is its required level, not a recommended adventuring level.</p><ul class="article-list">'+zone_links+'</ul><h2 id="excluded">Outside this reward release</h2><p>Highpass, Splitpaw, Cazic-Thule, Jaggedpine, Nedaria, Hate B and both tutorial zones remain outside the reward pool pending access checks. Cities and Plane of Knowledge have no new random drops. This does not mean every excluded zone is inaccessible.</p>', 'World')
    add('items', 'Equipment', '48 gear families. 48 augments. Four qualities for every reward.', equipment_directory(data), 'Equipment')
    return articles
