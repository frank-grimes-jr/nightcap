"""Public loot projection. Mirrors the reviewed NPC::AddLootDropTable probability model.

Probabilities describe newly generated database loot, conditional on killing the
listed NPC. Runtime scripts, saved corpses, looter eligibility and encounter access
are separate. Never treat database chance weights as per-kill probabilities.
"""
from collections import defaultdict
import math


def content_passes(row, era, enabled, disabled, sql=False):
    low, high = int(row.get('min_expansion', -1)), int(row.get('max_expansion', -1))
    if era != -1 and ((low != -1 and era < low) or (high != -1 and era > high)):
        return False
    for field, flags in [('content_flags', enabled), ('content_flags_disabled', disabled)]:
        wanted = set(filter(None, (row.get(field) or '').split(',')))
        if wanted and not (bool(wanted & flags) if sql else wanted <= flags):
            return False
    return True


def quality_outputs(item, items, chances):
    result = {item['id']: 1.0}
    if item['id'] >= 200000 or not (item.get('slots', 0) or item.get('bagslots', 0)):
        return result
    # Native order is Ascended, Exalted, Polished; missing definitions retain base.
    used = 0
    for offset, chance in reversed(list(zip((200000, 400000, 600000), chances))):
        upper = min(10000, max(0, used + chance))
        probability = max(0, upper - min(10000, max(0, used))) / 10000
        used += chance
        if probability and item['id'] + offset in items:
            result[item['id'] + offset] = probability
            result[item['id']] -= probability
    result[item['id']] = round(result[item['id']], 12)
    return {key: value for key, value in result.items() if value > 0}


def drop_probability(entries, target_probabilities, limit, minimum, probability, multiplier, global_multiplier):
    """Chance of >=1 target after all table activations and quality rolls.

    target_probabilities maps each source item to the probability its individual
    AddLootDrop becomes this target. Entries must already pass level/content gates.
    Non-target entries remain in the pool, including non-equipment.
    """
    if not entries or multiplier <= 0 or global_multiplier <= 0 or probability <= 0:
        return 0.0
    if not all(math.isfinite(float(e['chance'])) and e['chance'] >= 0 for e in entries):
        raise ValueError('Unsupported negative or nonfinite loot chance')
    if not 0 <= probability <= 100:
        raise ValueError('Unsupported table probability outside 0..100')
    if limit == 0 and minimum == 0:
        miss = math.prod((1 - min(1,e['chance'] / 100) * target_probabilities.get(e['item_id'], 0)) ** e['multiplier'] for e in entries)
    else:
        if len(entries) > 100 and limit == 0:
            limit = 10
        limit = max(limit, minimum)
        total = sum(e['chance'] for e in entries)
        if total <= 0:
            return 0.0
        pool = 1 - math.prod(1 - min(1,e['chance'] / 100) for e in entries)
        hit = 0.0
        for e in entries:
            quality = target_probabilities.get(e['item_id'], 0)
            # First copy is guaranteed once selected, extra copies reroll chance.
            copies_miss = (1-quality) * (1-min(1,e['chance']/100)*quality) ** (max(1,e['multiplier'])-1)
            hit += e['chance']/total * (1-copies_miss)
        miss = (1-hit)**minimum * (1-pool*hit)**(limit-minimum)
    return max(0.0, min(1.0, 1-(1-probability/100*(1-miss))**(multiplier*global_multiplier)))


RULE_DEFAULTS = {'Zone:GlobalLootMultiplier': 1, 'Zone:LootTierRareChance': 1000,
                 'Zone:LootTierEpicChance': 200, 'Zone:LootTierLegendaryChance': 25}
PUBLIC_ITEM_FIELDS = ('id name classes slots reqlevel reclevel ac hp mana endur damage delay '
    'bagslots bagwr itemtype deity races astr asta aagi adex awis aint acha heroic_str '
    'heroic_sta heroic_agi heroic_dex heroic_wis heroic_int heroic_cha haste regen '
    'manaregen spelldmg healamt attack accuracy mr fr cr dr pr').split()


def rules_for(raw, zone):
    rules = dict(RULE_DEFAULTS)
    # RuleManager loads default first, then overlays the selected ruleset.
    by_id = defaultdict(dict)
    for r in raw['rules']:
        by_id[r['ruleset_id']][r['rule_name']] = int(r['rule_value'])
    rules.update(by_id[raw['default_ruleset']])
    if zone.get('ruleset', 0):
        rules.update(by_id[zone['ruleset']])
    return rules


def project(raw):
    """Return a public-only index and per-item details from a fixed content capture."""
    era = raw['era']
    enabled = {r['flag_name'] for r in raw['flags'] if r['enabled']}
    disabled = {r['flag_name'] for r in raw['flags'] if not r['enabled']}
    def allowed(row, sql=False): return content_passes(row, era, enabled, disabled, sql)
    items = {r['id']: r for r in raw['items']}
    tables = {r['id']: r for r in raw['tables'] if allowed(r)}
    drops = {r['id'] for r in raw['drops'] if allowed(r)}
    pool = defaultdict(list)
    pool_sizes = defaultdict(int)
    links = defaultdict(list)
    for r in raw['entries']:
        if r['lootdrop_id'] in drops and allowed(r):
            # Native default droplimit is chosen before missing item definitions
            # and level requirements are removed from the actual roll pool.
            pool_sizes[r['lootdrop_id']] += 1
            if r['item_id'] in items:
                pool[r['lootdrop_id']].append(r)
    for r in raw['links']:
        if r['loottable_id'] in tables:
            links[r['loottable_id']].append(r)
    npcs = {r['id']: r for r in raw['npcs']}
    zones = {r['short_name']: r for r in raw['zones'] if r['min_status'] == 0 and r['expansion'] <= era and allowed(r)}
    spawn_entries = defaultdict(list)
    for r in raw['spawn_entries']:
        if r['chance'] > 0 and allowed(r, sql=True):
            spawn_entries[r['spawngroupID']].append(r)
    locations = defaultdict(list)
    disabled_spawns={s['spawn2_id'] for s in raw['disabled_spawns'] if s['disabled']}
    for s in raw['spawns']:
        if s['id'] in disabled_spawns or s['zone'] not in zones or not allowed(s, sql=True):
            continue
        for e in spawn_entries[s['spawngroupID']]:
            if e['npcID'] not in npcs:
                continue
            locations[(e['npcID'], s['zone'])].append({
                'id':s['id'], 'x':s['x'], 'y':s['y'], 'z':s['z'],
                'respawn':s['respawntime'], 'variance':s['variance'],
                'path':s['pathgrid'], 'condition':s['_condition'], 'condition_value':s['cond_value'],
                'entry_filter':e['condition_value_filter'], 'min_time':e['min_time'], 'max_time':e['max_time'],
                'spawn_weight':e['chance'], 'version':s['version']})
    found = defaultdict(list)
    for (npc_id, zone_name), points in locations.items():
        npc, zone = npcs[npc_id], zones[zone_name]
        rules = rules_for(raw, zone)
        tier = [rules['Zone:LootTier'+name+'Chance'] for name in ['Rare','Epic','Legendary']]
        low, high = npc['level'], max(npc['level'], npc.get('maxlevel', 0))
        if not 1 <= low <= high <= 255:
            raise ValueError('Unsupported NPC level range')
        by_level = []
        restrictions = defaultdict(set)
        for level in range(low, high+1):
            npc_tables = [npc['loottable_id']]+matching_globals(raw.get('global_loot', []), npc, zone, allowed, level)
            misses = defaultdict(lambda: 1.0)
            for table_id in npc_tables:
                for link in links[table_id]:
                    entries = [e for e in pool[link['lootdrop_id']] if
                               (not e['npc_min_level'] or level >= e['npc_min_level']) and
                               (not e['npc_max_level'] or level <= e['npc_max_level'])]
                    outputs = defaultdict(dict)
                    for e in entries:
                        for target, chance in quality_outputs(items[e['item_id']], items, tier).items():
                            item = items[target]
                            if not (item['slots'] or item['bagslots']) or item['minstatus'] > 0:
                                continue
                            outputs[target][e['item_id']] = chance
                            if e['trivial_min_level'] or e['trivial_max_level']:
                                restrictions[target].add((e['trivial_min_level'],e['trivial_max_level']))
                    for target, probabilities in outputs.items():
                        limit=link['droplimit']
                        if limit==0 and link['mindrop'] and pool_sizes[link['lootdrop_id']]>100:
                            limit=10
                        chance = drop_probability(entries, probabilities, limit,link['mindrop'],link['probability'],link['multiplier'],rules['Zone:GlobalLootMultiplier'])
                        misses[target] *= 1-chance
            by_level.append({item:1-miss for item, miss in misses.items() if miss < 1})
        for target in set().union(*(set(row) for row in by_level)):
            chances = [r.get(target,0)*100 for r in by_level]
            found[target].append({'npc_id':npc_id, 'npc':npc['name'].replace('_',' ').lstrip('#!'),
                'level':[low,high], 'zone':zone_name, 'zone_name':zone['long_name'],
                'zone_id':zone['zoneidnumber'], 'rate':[min(chances),max(chances)],
                'locations':points, 'looter_levels':sorted(restrictions[target])})
    index, details = [], {}
    for item_id, sources in sorted(found.items()):
        item = {key:items[item_id][key] for key in PUBLIC_ITEM_FIELDS}
        item['sources'] = sorted(sources,key=lambda s:(-s['rate'][1],s['zone'],s['npc']))
        item['era'] = era
        details[str(item_id)] = item
        index.append({k:item[k] for k in ['id','name','classes','slots','reqlevel','reclevel','ac','hp','mana','damage','delay','bagslots']} |
                     {'zones':sorted({s['zone'] for s in sources}), 'sources':len(sources), 'best_rate':max(s['rate'][1] for s in sources)})
    return {'schema':1,'captured_at':raw['captured_at'],'era':era,'era_name':raw['era_name'],
            'refresh_minutes':15,'items':index, 'zones':{z:zones[z]['long_name'] for z in sorted({s['zone'] for ss in found.values() for s in ss})},
            'scope':'Database loot on public version-0 spawns, including applicable global loot and ordinary quality upgrades. Quest hand-ins, scripted spawns, Hunt and dungeon completion rewards use their separate guides.'}, details


def matching_globals(rows, npc, zone, allowed, level):
    if npc['skip_global_loot']:
        return []
    result=[]
    for r in rows:
        if not r['enabled'] or not allowed(r, sql=True): continue
        if r['zone'] and str(zone['zoneidnumber']) not in r['zone'].split('|'): continue
        if (r['min_level'] and level<r['min_level']) or (r['max_level'] and level>r['max_level']): continue
        if any(r[key] and not value for key,value in [('rare',npc['rare_spawn']),('raid',npc['raid_target']),('hot_zone',zone['hotzone'])]): continue
        if any(r[key] and str(npc[field]) not in str(r[key]).split('|') for key,field in [('race','race'),('class','class'),('bodytype','bodytype')]): continue
        result.append(r['loottable_id'])
    return result
