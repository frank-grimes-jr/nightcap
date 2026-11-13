"""Generate the live Classic raid trophy item pages and zone links from the drop catalog."""
import html
import json
from pathlib import Path

ZONES = {32:'soldungb',39:'hole',64:'kedge',71:'airplane',72:'fearplane',73:'permafrost',76:'hateplane'}
BOSSES = {
    73057:'Lady Vox',32040:'Lord Nagafen',64001:'Phinigel Autropos',39138:'Master Yael',
    72000:'Dread',72004:'Fright',72002:'Terror',72090:'a dracoliche',76015:'Hand of the Maestro',
    76011:'Maestro of Rancor',76019:"Magi P’Tasa",71032:'a thunder spirit princess',
    71059:'Protector of Sky',71021:'Gorgalosk',71075:'Keeper of Souls',71013:'The Spiroc Guardian',
    71012:'The Spiroc Lord',71076:'Sister of the Spire',71072:'Bazzt Zzzt',71057:'Noble Dojorn',
    71034:'Overseer of Air',71060:'the Hand of Veeshan',72003:'Cazic-Thule',76007:'Innoruuk',71065:'Eye of Veeshan'}
STATS = {'healamt':'Healing Amount','spelldmg':'Spell Damage','attack':'ATK','cr':'cold resist',
    'fr':'fire resist','mr':'magic resist','dr':'disease resist','pr':'poison resist','ac':'AC','hp':'HP',
    'accuracy':'Accuracy','avoidance':'Avoidance','mana':'mana'}
EFFECTS = {963213:'A direct hostile hit that leaves you alive below 35% HP grants a 120-point rune for up to 12 seconds.',
    963214:'A direct melee, ranged or gem-cast spell hit restores up to 90 missing HP.',
    963215:'Spend 10% of maximum mana or endurance in combat to recover 1% of that pool, up to 50 points.'}

def add_raid_rewards(articles):
    root=Path(__file__).resolve().parent
    catalog=json.loads((root.parent/'config/classic-raid-augments.json').read_bytes())
    pages={a['slug']:a for a in articles}
    links={}
    for item in catalog:
        ident=item['id'];name=html.escape(item['name'])
        sources=item['sources']
        zone=ZONES[sources[0][0]]
        page=pages['zone-'+zone]
        source=', '.join(BOSSES[n] for _,n,_ in sources)
        chance=sources[0][2]
        link=f'<a href="item-{ident}.html">{name}</a>'
        links.setdefault(zone,[]).append(f'<li>{link} · {source} · {chance}%</li>')
        stats=item['stats']
        benefit=', '.join(f'+{v} '+STATS.get(k,k.replace("heroic_","heroic ").upper()) for k,v in stats.items()) if stats else EFFECTS[ident]
        body=f'<p>{benefit}</p><p>Level 50 · individually LORE · type-22 chest socket.</p><p>{source} · {chance}% per eligible corpse in <a href="{page["slug"]}.html">{html.escape(page["title"])}</a>.</p>'
        if ident in EFFECTS: body+='<p>The three planar capstones share 90 to 91 seconds of reuse across swaps, zoning and relogging.</p>'
        if ident==963203:body+='<p>Master Yael’s public spawn route still needs confirmation.</p>'
        body+='<p><a href="classic-raid-augments.html">All Classic raid augments</a></p>'
        articles.append(dict(slug=f'item-{ident}',title=item['name'],summary=f'Level-50 chest augment from {source}.',body=body,category='Equipment',status='Live testing',updated='2026-11-12',sources=['config/classic-raid-augments.json']))
    for zone,items in links.items():
        pages['zone-'+zone]['body']+='<h2 id="raid-augments">Raid boss augments</h2><ul>'+''.join(items)+'</ul>'
    pages['zone-hateplaneb']['body']+='<p>Credited managed Hate raids can earn the <a href="zone-hateplane.html#raid-augments">Hate boss augments</a>.</p>'
    pages['items']['body']+='<h2 id="raid-augments">Raid boss augments</h2><p><a href="classic-raid-augments.html">Compare all 16 chest trophies</a> from Classic dragons and planar bosses.</p>'
    return articles
