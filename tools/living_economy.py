"""Capture a reviewed Classic market catalog. This command never applies SQL."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import quote
from urllib.request import Request, urlopen

from pok_hub_migration import read_sql, sql_value

ROOT = Path(__file__).resolve().parents[1]
# Explicit provenance candidates, not a level-based scan of all database loot.
CANDIDATES = {
    'Polished Granite Tomahawk': ('find', 'Highpass Hold', 'a scalded rat'),
    'Shiny Brass Shield': ('find', 'Crushbone', 'Trainer'),
    'Dragoon Dirk': ('find', 'Crushbone', 'Ambassador DVinn'),
    'Bloodstained Tunic': ('find', 'Unrest', 'a ghoul magus'),
    'Bloodstained Mantle': ('find', 'Unrest', 'a ghoul magus'),
    'Dwarven Work Boots': ('find', 'Unrest', 'a reanimated hand'),
    'Savant\'s Cap': ('find', 'Unrest', 'a gnomish spelunker'),
    'Glowing Black Stone': ('find', 'Qeynos Hills', 'Pyzin'),
    'Gatorscale Sleeves': ('find', 'Upper Guk', 'an ancient croc'),
    'Jagged Band': ('find', 'Unrest', 'a skeletal monk'),
    'Skull-shaped Barbute': ('find', 'Unrest', 'a reanimated hand'),
    'Foreman\'s Tunic': ('find', 'Solusek\'s Eye', 'a goblin foreman'),
    'Flowing Black Silk Sash': ('tunnel', 'Lower Guk', 'a frenzied ghoul'),
    'Golden Efreeti Boots': ('tunnel', 'Solusek B', 'Efreeti Lord Djarn'),
    'Short Sword of the Ykesha': ('tunnel', 'Lower Guk', 'a ghoul lord'),
    'Runed Cowl': ('tunnel', 'Lower Guk', 'a ghoul ritualist'),
    'Shiny Metallic Robes': ('tunnel', 'Lower Guk', 'a froglok arch magus'),
    'Robe of the Ishva': ('tunnel', 'Splitpaw', 'The Ishva Mal'),
    'Crested Mistmoore Shield': ('tunnel', 'Mistmoore', 'a glyphed sentry'),
    'Hooded Black Cloak': ('tunnel', 'Mistmoore', 'a cloaked dhampyre'),
    'Thick Banded Belt': ('tunnel', 'Lower Guk', 'a froglok dar knight'),
    'Executioners Hood': ('tunnel', 'Lower Guk', 'a ghoul executioner'),
}


class AuctionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.cell = None
        self.cells = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'div':
            if attrs.get('id') == 'auc_Green':
                self.depth = 1
            elif self.depth:
                self.depth += 1
        if self.depth and tag in ('td', 'th'):
            self.cell = ''

    def handle_data(self, text):
        if self.cell is not None:
            self.cell += text

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            self.cells.append(' '.join(self.cell.split()))
            self.cell = None
        if tag == 'div' and self.depth:
            self.depth -= 1


def parse_price(html):
    parser = AuctionParser()
    parser.feed(html)
    cells = parser.cells
    if not cells or cells[:2] != ['30d Avg', '90d Avg']:
        raise ValueError('Missing/changed P1999 Green auction summary')
    # Real pages have five summary headings; compact fixtures may have two.
    start = 0
    while start < len(cells) and ('Avg' in cells[start] or cells[start] in ('All Time Range', '# Seen')):
        start += 1
    for index, window in enumerate(('30d', '90d')):
        value = cells[start + index].split('\u00b1', 1)[0].strip().replace(',', '')
        if not re.fullmatch(r'\d+(?:\.\d+)?', value):
            continue
        price = Decimal(value)
        if not 0 < price <= 100000:
            continue
        dates = [c for c in cells if re.fullmatch(r'\d{4}-\d{2}-\d{2}', c)]
        if not dates:
            raise ValueError('Missing auction dates')
        return {'reference_pp': float(price), 'window': window, 'latest_auction': max(dates)}
    raise ValueError('No positive recent P1999 Green price')


def prices(reference_pp, native_price_cp, policy=None, sellrate=1):
    reference = Decimal(str(reference_pp))
    if not 0 < reference <= 100000 or native_price_cp < 0:
        raise ValueError('Invalid price')
    # Whole platinum quotes avoid fractional-payment ambiguity in dialogue.
    factor = Decimal(1)
    native_floor = Decimal(native_price_cp) * 2
    find_premium = Decimal('0.85')
    sell_premium = Decimal('1.20')
    buy_fraction = Decimal('0.70')
    if policy:
        if policy['income_basis'] not in ('item_drops_and_vendor_payout', 'vendor_payout'):
            raise ValueError('Unknown income basis')
        factor = Decimal(policy['buy_cost_mod']) / Decimal(policy['baseline_buy_cost_mod'])
        if policy['income_basis'] == 'item_drops_and_vendor_payout':
            factor *= policy['global_loot_multiplier']
        if not 0 < factor <= 100:
            raise ValueError('Unreviewed income multiplier')
        find_premium = Decimal(policy['find_premium'])
        sell_premium = Decimal(policy['tunnel_premium'])
        buy_fraction = Decimal(policy['buy_fraction'])
        if not 0 < buy_fraction < min(find_premium, sell_premium) or sell_premium < 1 or find_premium < 1:
            raise ValueError('Invalid market premium/spread')
        native_floor = max(Decimal(native_price_cp)*Decimal(str(sellrate))*Decimal(policy['sell_cost_mod'])*
                           (1+Decimal(policy['price_penalty_pct'])/100)*Decimal('1.20'),
                           Decimal(native_price_cp)*Decimal(policy['buy_cost_mod'])*
                           (1+Decimal(policy['price_bonus_pct'])/100)*Decimal('1.20'))
    sell = int((reference * factor * sell_premium).to_integral_value(rounding=ROUND_CEILING)) * 1000
    buy = int(reference * factor * buy_fraction) * 1000
    find = int(max(reference * factor * find_premium, native_floor/1000,
                   Decimal(buy)/1000+1).to_integral_value(rounding=ROUND_CEILING)) * 1000
    if max(sell, buy, find) > 2000000000:
        raise ValueError('Price exceeds native signed packet limit')
    return {'sell_cp': sell, 'buy_cp': buy, 'find_cp': find}


def capture(output):
    if output.exists():
        raise ValueError('Refusing to replace an existing price snapshot')
    result = {'captured_at': datetime.now(timezone.utc).isoformat(), 'server': 'Green',
              'expansion': 0, 'items': [], 'excluded': []}
    for name, (pool, source_zone, source_npc) in CANDIDATES.items():
        url = 'https://wiki.project1999.com/' + quote(name.replace(' ', '_'))
        try:
            request = Request(url, headers={'User-Agent': 'Nightcap-catalog-audit/1.0'})
            with urlopen(request, timeout=30) as response:
                html = response.read().decode('utf-8')
            price = parse_price(html)
            if '"Classic Era"' not in html:
                raise ValueError('Wiki does not identify Classic Era')
            revision = re.search(r'"wgCurRevisionId":(\d+)', html)
            if not revision:
                raise ValueError('Wiki revision unavailable')
            fields = ['id','Name','nodrop','norent','stackable','maxcharges','price','sellrate','loregroup','questitemflag','itemclass','attuneable']
            query = 'SELECT JSON_OBJECT(' + ','.join(sql_value(k)+',`'+k+'`' for k in fields) + \
                ') FROM items WHERE Name=' + sql_value(name) + ' AND nodrop<>0 AND norent<>0 AND stackable=0 AND maxcharges=0 AND itemclass=0;'
            rows = [json.loads(line) for line in read_sql(query).splitlines()]
            if len(rows) != 1:
                raise ValueError('Expected one permanent tradeable uncharged PEQ item')
            item = rows[0]
            if item['questitemflag'] or item['attuneable'] or not 0 < item['id'] < 1048576:
                raise ValueError('Unsupported item flags')
            loot = read_sql(f"SELECT JSON_OBJECT('npc_id',n.id,'npc',n.name,'level',n.level,'zone',s.zone,'min_expansion',s.min_expansion) "
                f"FROM lootdrop_entries d JOIN loottable_entries t ON t.lootdrop_id=d.lootdrop_id "
                f"JOIN npc_types n ON n.loottable_id=t.loottable_id JOIN spawnentry e ON e.npcID=n.id "
                f"JOIN spawn2 s ON s.spawngroupID=e.spawngroupID WHERE d.item_id={item['id']} "
                "AND s.version=0 AND s.min_expansion<=0 AND n.level<=50 GROUP BY n.id,s.zone;")
            sources = [json.loads(line) for line in loot.splitlines()]
            if not sources:
                raise ValueError('No Classic level<=50 live drop source')
            item.update(pool=pool, min_expansion=0, source_zone=source_zone, source_npc=source_npc,
                        sources=sources, source_url=url, revision=int(revision[1]), **price,
                        **prices(price['reference_pp'], item['price']))
            result['items'].append(item)
            print(f"{name}: {price['reference_pp']} pp ({price['window']}); {len(sources)} PEQ sources", flush=True)
        except Exception as error:
            result['excluded'].append({'name': name, 'reason': str(error), 'source_url': url})
            print(f'Excluded {name}: {error}', flush=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    if len(result['items']) < 12:
        raise ValueError('Insufficient verified catalog; inspect exclusions')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    capture(parser.parse_args().capture)
