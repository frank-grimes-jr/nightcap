"""Offline starter/dungeon band proposal. No database or live compiler writes."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from gear_progression import comparable

LABELS=('Normal','Polished','Exalted','Ascended')
# Reviewed entry-dungeon AC by worn slot. Higher bands add four AC per step.
ENTRY_AC={4:9,131072:12,128:8,1536:6,4096:7,262144:9,524288:8,64:7,
          18:2,98304:2,32:6,8:6,256:7,1048576:6}
PRIMARY=('astr','asta','aagi','adex','aint','awis','acha')
RESISTS=('fr','cr','mr','pr','dr')
POOLS=('hp','mana','endur')
UTILITY=('regen','manaregen','enduranceregen','attack','accuracy')
# Fixed reviewed identities, independent of a caller-supplied capture. These
# ranges are contiguous audited item IDs, not name or material heuristics.
RUSTY_IDS=frozenset((5013,5014,5015,5016,5019,5020,5021,5022,5023,5024,5025,
                    5040,5072,5074,5076,6011,6013,6014,6015,6016,7007,7008,
                    7009,7010,13346,13970,26800,30980))
APPROVED_IDS=frozenset((*range(1001,1037),1039,10152,*range(2001,2037),2038,
                       *range(4201,4237),*range(7409,7445),*range(5026,5038),
                       6019,6021,6022,6023,6024,6025,*range(6900,6907),6910,6911,
                       *range(7012,7017),26801,30981)) | RUSTY_IDS


def rounded(numerator,denominator):
    return (2*numerator+denominator)//(2*denominator)


def dungeon_proposal(source):
    if (len(source)!=330 or {r['id'] for r in source}!=set(range(960000,960330))
            or any(r['values']['id']!=r['id'] for r in source)):
        raise ValueError('Expected complete owned dungeon catalog')
    result=deepcopy(source)
    normals=[r for r in source if r['source']=='completion' and r['quality']=='Normal']
    for row in result:
        item=row['values']
        if item['itemclass']==1:continue
        band=(20,30,40,50).index(row['band'])
        quality=('Normal','Polished','Ascended').index(row['quality'])
        boost=(100,115,135)[quality]
        scale=lambda value:max(value+quality,value*boost//100) if value else 0
        if item['damage']==0:
            item['ac']=max(item['ac'],scale(ENTRY_AC[item['slots']]+4*band))
        elif item['itemtype'] in (0,2,3,45):
            normal=next(r['values'] for r in normals if r['band']==row['band']
                        and r['values']['itemtype']==item['itemtype']
                        and r['values']['slots']==item['slots'])
            item['damage']=max(item['damage'],scale(normal['damage']+1))
        for field in ('spelldmg','healamt'):
            item[field]=max(item[field],scale(4+band*2))
        if item['damage']:
            item['endur']=max(item['endur'],scale(5+band*5))
    return result


def propose(capture,dungeon):
    if (len(capture['families'])!=len(APPROVED_IDS)
            or {f['id'] for f in capture['families']}!=APPROVED_IDS):
        raise ValueError('Capture must exactly match the reviewed starter allowlist')
    proposed_dungeon=dungeon_proposal(dungeon)
    normals=[r['values'] for r in proposed_dungeon if r['quality']=='Normal']
    result={}
    for family in capture['families']:
        bid=family['id'];tiers=family['tiers'];profile=family['profile']
        if (type(bid) is not int or not 0<bid<200000 or len(tiers)!=4
                or profile!=('rusty' if bid in RUSTY_IDS else 'starter') or bid in result):
            raise ValueError('Invalid/duplicate explicit starter family')
        base=tiers[0]
        if base['Name']!=family['name']:
            raise ValueError('Starter catalog name drift')
        for quality,item in enumerate(tiers):
            if (item['id']!=bid+quality*200000
                    or item['Name']!=base['Name']+(' ('+LABELS[quality]+')' if quality else '')
                    or any(item[key]!=base[key] for key in ('itemtype','itemclass','slots','classes','races','deity','delay'))
                    or any(item.get(key,0)>0 for key in ('haste','clickeffect','proceffect','worneffect','focuseffect'))):
                raise ValueError('Unexpected starter identity or special effect')
        matches=[item for item in normals if comparable(base,item)]
        if not matches:
            raise ValueError('No comparable dungeon floor for '+base['Name'])
        if base['damage']>0:
            if base['delay']<=0:raise ValueError('Invalid weapon delay')
            # Integer ceiling minus one enforces strict ratio inequality.
            cap=min((i['damage']*base['delay']-1)//i['delay'] for i in matches)
            damage=min(max(1,rounded(base['damage']*(2 if profile=='rusty' else 3),4)),cap-3)
            if damage<1:raise ValueError('Insufficient room for four increasing damage tiers')
        else:damage=0
        if base['ac']>0:
            ac=min(max(1,rounded(base['ac']*6,17)),min(i['ac'] for i in matches)-4)
            if ac<1:raise ValueError('Insufficient armor quality budget')
        else:ac=0
        for quality,old in enumerate(tiers):
            item=deepcopy(old)
            item['damage']=damage+quality if damage else 0
            item['ac']=ac+quality if ac else 0
            boost=(100,110,120,135)[quality]
            for field in POOLS+PRIMARY+RESISTS+UTILITY:
                cap=3 if field in POOLS else 1 if field in PRIMARY+RESISTS else 0
                value=min(base[field],cap)
                item[field]=rounded(value*boost,100) if value>0 else value
            for field in ('spelldmg','healamt'):
                # Preserve negative drawbacks; starter quality bonus never exceeds3.
                item[field]=base[field] if base[field]<0 else quality
            for field in item:
                if field.startswith('heroic_'):item[field]=0
            result[item['id']]=item
    return result,proposed_dungeon


def main():
    from dungeon_catalog import legacy_items as items
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--references',type=Path,default=root/'docs/items/starter-retune-reference.json')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    capture=json.loads(args.references.read_text(encoding='utf-8'))
    source=items();starters,dungeon=propose(capture,source)
    def delta(old,new):return {k:dict(old=v,new=new[k]) for k,v in old.items() if new[k]!=v}
    changes=[]
    for family in capture['families']:
        for old in family['tiers']:
            diff=delta(old,starters[old['id']])
            if diff:changes.append(dict(id=old['id'],name=old['Name'],source='starter',changes=diff))
    for old,new in zip(source,dungeon):
        diff=delta(old['values'],new['values'])
        if diff:changes.append(dict(id=old['id'],name=old['values']['Name'],source='dungeon',changes=diff))
    report=dict(applied=False,policy='Normal starter reductions allowed; cultural armor excluded',
                starter_families=len(capture['families']),starter_definitions_changed=sum(r['source']=='starter' for r in changes),
                dungeon_definitions_changed=sum(r['source']=='dungeon' for r in changes),changes=changes)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='changes'}))


if __name__=='__main__':main()
