"""Offline dungeon-budget candidate; never mutates ordinary item definitions.

An explicit captured starter catalog supplies comparison floors. This is a
balance proposal, not a live migration or replacement for encounter measurements.
"""
from copy import deepcopy
import argparse
import json
from pathlib import Path

STATS = ('ac','hp','mana','endur','astr','asta','aagi','adex','aint','awis','acha',
         'fr','cr','mr','pr','dr','spelldmg','healamt','regen','manaregen',
         'enduranceregen','attack','accuracy','heroic_str','heroic_sta','heroic_agi',
         'heroic_dex','heroic_int','heroic_wis','heroic_cha')
ONE_HAND = (0,2,3,45)
TWO_HAND = (1,4,35)


def comparable(a,b):
    if not a['classes'] & b['classes']:
        return False
    if a['damage'] > 0 and b['damage'] > 0:
        return any(a['itemtype'] in group and b['itemtype'] in group
                   for group in (ONE_HAND,TWO_HAND,(5,)))
    return (a['damage']==b['damage']==0 and a['itemtype']==b['itemtype']==10
            and bool(a['slots'] & b['slots']))


def candidate(references, dungeon):
    for ref in references:
        if (not 600000<ref['id']<800000 or not ref.get('Name','').endswith(' (Ascended)')
                or ref.get('damage',0)>0 and ref.get('delay',0)<=0
                or any(ref.get(f,0)>0 for f in ('haste','clickeffect','proceffect','worneffect','focuseffect'))):
            raise ValueError('Reference must be an audited plain ordinary Ascended item')
    if len({r['id'] for r in references})!=len(references):
        raise ValueError('Duplicate starter reference')
    if (len(dungeon)!=330 or {r['id'] for r in dungeon}!=set(range(960000,960330))
            or any(r['id']!=r['values']['id'] for r in dungeon)):
        raise ValueError('Expected complete owned dungeon catalog')
    result=deepcopy(dungeon)
    normals=[r for r in dungeon if r['quality']=='Normal' and r['source']=='completion']
    for row in result:
        target=row['values']
        if target['itemclass']==1:
            continue
        refs=[r for r in references if comparable(r,target)]
        if not refs:
            continue  # Report unbenchmarked roles; do not invent a starter source.
        template=lambda r: (r['values']['itemtype']==target['itemtype']
                             and r['values']['slots']==target['slots'])
        normal=next(r['values'] for r in normals if r['band']==row['band'] and template(r))
        lowest=next(r['values'] for r in normals if r['band']==20 and template(r))
        quality=('Normal','Polished','Ascended').index(row['quality'])
        boost=(100,115,135)[quality]
        scale=lambda v:max(v+quality,v*boost//100) if v else 0
        for stat in STATS:
            floor=max(max(0,r.get(stat,0)) for r in refs)
            if stat=='ac' and target['damage']==0 and floor:
                floor+=1
            budget=max(normal[stat],floor+normal[stat]-lowest[stat])
            target[stat]=max(target[stat],scale(budget))
        if target['damage']:
            # Smallest integer damage strictly above the strongest starter ratio.
            floor=max(r['damage']*target['delay']//r['delay']+1 for r in refs)
            budget=max(normal['damage'],floor+normal['damage']-lowest['damage'])
            target['damage']=max(target['damage'],scale(budget))
    return result


def main():
    from dungeon_catalog import items
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--references',type=Path,default=Path(__file__).resolve().parents[1]/'docs/items/starter-gear-reference.json')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    parser.error("Superseded preserve-Normal proposal. Use tools/starter_retune.py for the current offline candidate.")
    captured=json.loads(args.references.read_text(encoding='utf-8'))
    references=[]
    for family in captured['families']:
        normal,ascended=family['normal'],family['ascended']
        if (normal['id']!=family['id'] or ascended['id']!=normal['id']+600000
                or ascended['Name']!=normal['Name']+' (Ascended)'):
            raise ValueError('Starter reference identity drift')
        references.append(ascended)
    original=items()
    proposed=candidate(references,original)
    changes=[]
    for old,new in zip(original,proposed):
        delta={key:dict(old=value,new=new['values'][key]) for key,value in old['values'].items()
               if new['values'][key]!=value}
        if delta:
            changes.append(dict(id=old['id'],name=old['values']['Name'],band=old['band'],
                                quality=old['quality'],changes=delta))
    report=dict(applied=False,normal_legacy_items_changed=0,starter_families=len(references),
                dungeon_definitions_changed=len(changes),unbenchmarked_normal_designs=[
                    dict(id=r['id'],name=r['values']['Name']) for r in original
                    if r['band']==20 and r['quality']=='Normal' and r['values']['itemclass']==0
                    and not any(comparable(a,r['values']) for a in references)],changes=changes)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
