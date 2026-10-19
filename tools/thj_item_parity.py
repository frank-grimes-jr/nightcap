"""Sourced item definition overlay. Pure planning; never connects to a database."""
from copy import deepcopy
import gzip
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FIELDS=frozenset(('ac hp mana endur damage delay range backstabdmg elemdmgamt '
    'spelldmg healamt attack accuracy haste damageshield regen manaregen enduranceregen '
    'shielding spellshield avoidance strikethrough combateffects stunresist '
    'astr asta aagi adex aint awis acha fr cr mr dr pr '
    'heroic_str heroic_sta heroic_agi heroic_dex heroic_int heroic_wis heroic_cha '
    'heroic_fr heroic_cr heroic_mr heroic_dr heroic_pr').split())

def catalog():
    return json.loads((ROOT/'config/thj-item-parity.json').read_text(encoding='utf-8'))

def snapshot():
    data=json.loads(gzip.decompress((ROOT/'tools/fixtures/thj-parity-20261018.json.gz').read_bytes()))
    for row in data['items']:
        for field in FIELDS:
            if field in row:row[field]=int(row[field])
    return {row['id']:row for row in data['items']}

def propose(before):
    """Apply exact targets after companion content; retain unknown/effect fields.

    Intermediate tiers retain their original scaling unless a verified reduction
    would put them above Ascended. Such fields are capped at the new top value.
    Normal definitions, delay, equip gates, ownership and acquisition are not
    regenerated. This is a Nightcap interpolation, not a recovered THJ formula.
    """
    result=deepcopy(before)
    identities=snapshot()
    seen=set()
    for target in catalog()['items']:
        ident=target['id']; base=target['base_id']; fields=target['fields']
        if (ident in seen or ident-base not in (600000,800000) or ident>1048575
            or not fields.keys()<=FIELDS or not target['evidence']):
            raise ValueError('Invalid parity catalog target')
        seen.add(ident)
        if any(i not in before or before[i]['Name']!=identities[i]['Name'] for i in (base,ident)):
            raise ValueError(f'Parity identity missing or renamed: {ident}')
        for field,value in fields.items():
            if type(value) is not int or not -32768<=value<=2147483647:
                raise ValueError(f'Invalid numeric target: {ident}/{field}')
            if field not in before[ident]:raise ValueError(f'Missing field: {ident}/{field}')
            if field not in ('delay','range') and value<int(before[base][field]):
                raise ValueError(f'Target would regress below Normal: {ident}/{field}')
            result[ident][field]=value
            if value<0 or field in ('delay','range'):continue
            for offset,label in ((200000,'Polished'),(400000,'Exalted')):
                tier=base+offset
                if tier not in before:continue # epic families can have a different identity layout
                if before[tier]['Name']!=before[base]['Name']+' ('+label+')':
                    raise ValueError(f'Intermediate identity drift: {tier}')
                if int(before[tier][field])>value:
                    result[tier][field]=value
    return result

def changes(before):
    after=propose(before)
    return [(before[i],row) for i,row in sorted(after.items()) if before[i]!=row]
