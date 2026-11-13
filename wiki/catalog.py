"""Generate linked zone and item articles from the reviewed, public-only catalog."""
import html
import re
import json
from pathlib import Path
from equipment import equipment_directory

ROOT = Path(__file__).resolve().parent
QUALITIES = ['Base', 'Polished', 'Exalted', 'Ascension']
RATES = json.loads((ROOT.parent / 'config/zone-hunt-rates.json').read_text(encoding='utf-8'))


def rate(slug, kind):
    r = {**RATES['default'], **RATES['zones'].get(slug, {})}['augment_chance' if kind == 'Augment' else 'gear_chance']
    return f'{r / 100:g}%'


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
        body += '<h2 id="rewards">Zone rewards</h2><div class="table-scroll"><table><caption>Available reward families, at every quality</caption><thead><tr><th scope="col">Item</th><th scope="col">Family</th><th scope="col">Quality</th><th scope="col">Required level</th></tr></thead><tbody>'
        for i in rows:
            body += f'<tr><td><a href="item-{i["id"]}.html">{html.escape(i["name"])}</a></td><td>{i["kind"]}</td><td>{QUALITIES[i["tier"]]}</td><td>{i["required_level"]}</td></tr>'
        body += f'</tbody></table></div><h2 id="finding-rewards">Finding these rewards</h2><p>Unowned killable enemies have an independent {rate(z["slug"],"Augment")} roll for the augment family and {rate(z["slug"],"Gear")} for the gear family when they qualify as approved equipment sources. Both may drop together. A successful family roll then chooses Base (60%), Polished (30%), Exalted (8%), or Ascension (2%). Ordinary loot remains.</p><p>Any unowned, killable NPC in an enabled augment zone can roll its augment, including guards, named and quest NPCs, killable merchants and scripted combat adds. Player-owned/charmed pets, mercenaries, swarm pets, protected noncombat actors and restored corpses do not reroll. Native corpse ownership and encounter access still apply. Augments roll at 1.5%; approved native equipment sources keep their separate 0.5% chance and level/night restrictions. There is no guaranteed drop or pity timer.</p>'
        if z.get('augment_only'):
            body = re.sub(r'(<h2 id="finding-rewards">Finding these rewards</h2>)<p>.*?</p>', lambda m: m[1] + '<p>Any unowned killable enemy has a 1.5% augment roll, followed by Base60%, Polished30%, Exalted8% or Ascension2%. Ordinary loot remains; this pool has no public wearable drops.</p>', body, count=1)
            body += '<p><strong>Augment-only pool:</strong> only the augment family listed here drops. There are no approved public wearable sources in this pool. Managed newer Hate runs retain the original Hate equipment family and its source rules.</p>'
        if z['slug'] == 'highkeep':
            body += '<h2 id="prison-break">High Keep prison break</h2><p>New managed Raid runs use the <a href="dungeon-modes.html#highkeep-rescue">Osargen rescue route</a>. Hunt item values and ordinary acquisition remain unchanged. Live testing; native escort acceptance remains open.</p>'
        if z['slug'] == 'hole':
            body += '<h2 id="entrance">Entrance access</h2><p>See <a href="travel.html#hole-entrance">the Paineel passage access note</a> for keyless entrance and internal door access, remaining restrictions and release status.</p>'
        if z['slug'] == 'kithicor':
            body += '<p><strong>Kithicor’s nighttime-undead restriction applies to equipment only; augments can drop day or night.</strong></p>'
        body += '<h2 id="upgrading">Upgrading your finds</h2><p>Forge three identical Base copies into Polished, then four Polished into Exalted or four Exalted into Ascension. Read <a href="zone-hunt.html#forging">the forging guide</a> before using <code>#zoneforge</code>. All new zone rewards have zero merchant resale value.</p><p><a href="zones.html">Browse all 50 reward zones →</a></p>'
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
            body += f'<h2 id="source">Where to find it</h2><p>From the <a href="zone-{z["slug"]}.html">{e(z["name"])}</a> reward pool. This family rolls at {rate(z["slug"],i["kind"])} per eligible kill, followed by the quality roll. <strong>{QUALITIES[i["tier"]]}</strong> is {[60,30,8,2][i["tier"]]}% of successful family rolls, not of all kills. See the zone page for eligibility.</p>'
            body += '<h2 id="quality">Quality family</h2><ul>'
            for sibling in rows:
                if sibling['kind'] == i['kind']:
                    body += f'<li><a href="item-{sibling["id"]}.html">{e(sibling["name"])}</a> · {QUALITIES[sibling["tier"]]}</li>'
            body += '</ul><p>Use <a href="zone-hunt.html#forging">#zoneforge</a> with three identical Base copies or four identical Polished/Exalted copies for the next quality. The <a href="item-upgrades.html#box">Reforging Box</a> also handles three Base copies for Polished and the four-copy higher steps. Ascension is the final quality. These items can be traded, but cannot be sold to merchants.</p>'
            add('item-'+str(i['id']), i['name'], f'{QUALITIES[i["tier"]]} {i["kind"].lower()} · {z["name"]} · Required level {i["required_level"]}.', body, 'Equipment')
    zone_links = ''.join(f'<li><a href="zone-{z["slug"]}.html">{html.escape(z["name"])}</a></li>' for z in sorted(data['zones'], key=lambda z:z['name']))
    add('zones', 'Zones & rewards', 'Explore all 50 enabled Classic reward zones.', '<p>Each listed zone has a custom augment family. The original 48 zones also retain their equipment families; Cazic-Thule and newer Hate add augment-only pools. Click a zone for all four qualities and their item details. The level shown on an item is its required level, not a recommended adventuring level.</p><ul class="article-list">'+zone_links+'</ul><h2 id="excluded">Outside this reward release</h2><p>Highpass, Splitpaw, Jaggedpine, Nedaria and both tutorial zones remain outside the reward pool pending access checks. Cities and Plane of Knowledge have no new random drops. This does not mean every excluded zone is inaccessible. Cazic-Thule has restored Classic encounters in public and private runs, but remains outside this Hunt equipment pool.</p>', 'World')
    add('items', 'Equipment', '48 gear families. 50 augments. Four qualities for every reward.', equipment_directory(data), 'Equipment')
    if data.get('chapterhouse'):
        from chapterhouse_catalog import articles as chapterhouse_articles
        articles.extend(chapterhouse_articles(data['chapterhouse']))
        next(a for a in articles if a['slug']=='zones')['body'] += '<h2 id="chapterhouse">Custom expedition</h2><p><a href="zone-chapterhouse.html">Chapterhouse of the Fallen</a> has a separate curated capstone reward pool. Its scoped access exception does not expand the 48 Classic Hunt zones.</p>'
    next(a for a in articles if a['slug']=='zones')['body'] += '<h2 id="ashen-compact">The Ashen Compact</h2><p><a href="zone-kael.html">Kael: The Ashen Compact</a> is a separate curated campaign in live testing.</p>'
    from last_lantern_catalog import articles as lantern_articles
    articles.extend(lantern_articles(json.loads((ROOT/'last-lantern-catalog.json').read_text(encoding='utf-8'))))
    for article in articles:
        if article['slug'] in ('zone-unrest','zone-gukbottom','zone-soldungb','zone-cazicthule','zone-hole','zone-fearplane','zone-hateplane'):
            article['body'] += '<h2 id="last-lantern-memory">A company memory</h2><p>The <a href="adventure-journal.html#chapters">Last Lantern campaign</a> revisits this terrain in a separate private journal memory. Enter through the Ancient Chronicler with the active chapter. Public populations, Keeper runs and Hunt reward values remain separate.</p>'
    from raid_augment_catalog import add_raid_rewards
    return add_raid_rewards(articles)
