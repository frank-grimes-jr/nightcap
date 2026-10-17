"""Equipment directory: one row per family, with all quality variants together."""
from collections import Counter
from html import escape as e

QUALITIES = ['Base', 'Polished', 'Exalted', 'Ascension']


def equipment_directory(data):
    zones = {z['slug']: z['name'] for z in data['zones']}
    families = sorted((i for i in data['items'] if i['tier'] == 0), key=lambda i: i['name'])
    slots = sorted({s.strip().title() for i in families for s in i['slot'].split(',')})
    counts = Counter(i['kind'] for i in families)
    body = '''<div class="equipment-intro"><p><strong>Find your next upgrade.</strong> Browse custom zone rewards by slot, required level, or where they drop. Each row groups an item's four qualities.</p><p class="catalog-scope">This catalog covers the Classic zone-hunt release, not every ordinary item in Nightcap. Required level is the level to equip an item, not a zone's difficulty.</p></div>
<nav class="equipment-guides" aria-label="Equipment guides"><a href="equipment.html"><strong>Equipment &amp; trading</strong><span>Qualities, bags and selling</span></a><a href="zone-hunt.html#sockets"><strong>Augments &amp; sockets</strong><span>Fit, heroic stats and limits</span></a><a href="zone-hunt.html#forging"><strong>Forging upgrades</strong><span>Three copies → next quality</span></a></nav>
<section data-equipment-browser aria-labelledby="browse-heading"><h2 id="browse-heading">Browse rewards</h2>
<div id="equipment-controls" hidden><div class="equipment-types" role="group" aria-label="Reward type">'''
    for kind, label, count in [('', 'All rewards', len(families)), ('Gear', 'Gear', counts['Gear']), ('Augment', 'Augments', counts['Augment'])]:
        body += f'<button type="button" data-kind="{kind}" aria-pressed="{str(not kind).lower()}">{label} <span>{count}</span></button>'
    body += '</div><div class="equipment-filters"><label class="equipment-query" for="equipment-query">Item name<input id="equipment-query" type="search" maxlength="160" placeholder="Find an item…"></label>'
    def select(id, label, options):
        return f'<label for="{id}">{label}<select id="{id}">' + ''.join(f'<option value="{e(str(value), quote=True)}">{e(str(text))}</option>' for value, text in options) + '</select></label>'
    body += select('equipment-slot', 'Equipment slot', [('', 'All slots')] + [(s.lower(), s) for s in slots])
    body += select('equipment-level', 'Your level', [('', 'Any level')] + [(n, f'Level {n} and below') for n in [1, 10, 20, 30, 40, 50]])
    body += select('equipment-zone', 'Source zone', [('', 'All zones')] + sorted(zones.items(), key=lambda z:z[1]))
    body += '</div><div class="equipment-toolbar">'
    body += select('equipment-sort', 'Sort by', [('name', 'Item name'), ('level', 'Required level')])
    body += '<button type="button" id="equipment-reset">Clear filters</button></div></div>'
    body += f'<p id="equipment-status" class="equipment-status" role="status" aria-live="polite">{len(families)} item families · {len(data["items"])} quality variants</p>'
    body += '<noscript><p>Filters need JavaScript. All item families and quality links are available in the table below.</p></noscript><p id="equipment-empty" class="notice" hidden>No rewards match these filters. Choose another slot or zone, increase your level, or clear the filters.</p>'
    body += '<table class="equipment-table"><caption class="sr-only">Custom reward families and their quality variants</caption><thead><tr><th scope="col">Item family</th><th scope="col">Type / slot</th><th scope="col">Req. level</th><th scope="col">Source zone</th><th scope="col">View quality</th></tr></thead><tbody id="equipment-rows">'
    for item in families:
        variants = sorted((i for i in data['items'] if i['zone'] == item['zone'] and i['kind'] == item['kind']), key=lambda i:i['tier'])
        slots_value = '|'.join(s.strip().lower() for s in item['slot'].split(','))
        search_names = ' | '.join(i['name'] for i in variants)
        body += f'<tr data-equipment-row data-name="{e(item["name"], quote=True)}" data-search="{e(search_names, quote=True)}" data-kind="{item["kind"]}" data-slots="{slots_value}" data-level="{item["required_level"]}" data-zone="{item["zone"]}">'
        body += f'<th scope="row"><a href="item-{item["id"]}.html">{e(item["name"])}</a></th>'
        slot = 'Armor sockets (type 22)' if item['kind'] == 'Augment' else item['slot']
        body += f'<td data-label="Type / slot"><span class="equipment-kind">{item["kind"]}</span>{e(slot)}</td><td data-label="Req. level" class="equipment-level">{item["required_level"]}</td>'
        body += f'<td data-label="Source"><a href="zone-{item["zone"]}.html">{e(zones[item["zone"]])}</a></td><td data-label="View quality"><div class="quality-links">'
        for variant in variants:
            quality = QUALITIES[variant['tier']]
            body += f'<a class="quality-{variant["tier"]}" href="item-{variant["id"]}.html" aria-label="{e(item["name"], quote=True)} — {quality}">{quality}</a>'
        body += '</div></td></tr>'
    body += '</tbody></table><nav id="equipment-pagination" class="equipment-pagination" aria-label="Equipment results pages" hidden><button id="equipment-prev" type="button">← Previous</button><span id="equipment-page"></span><button id="equipment-next" type="button">Next →</button></nav></section>'
    return body
