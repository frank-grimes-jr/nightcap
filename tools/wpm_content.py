"""WPM item effects and earned acquisition, generated offline from reviewed rows."""
import gzip
import json
from pathlib import Path
from wpm_migration import migration
import pet_content
from collections import defaultdict

ROOT=Path(__file__).resolve().parents[1]
RELEASE=ROOT/'docs/releases/wpm-melee-20261018/content'
BASE_POWER,BASE_SHIELD,BASE_HASTE=180620,180621,180622
QUALITIES=('', ' (Polished)', ' (Exalted)', ' (Ascended)')


def snapshot():
    return json.loads(gzip.decompress((ROOT/'tools/fixtures/wpm-content-20261018.json.gz').read_bytes()))


def spell_rows():
    templates={r['id']:r for r in snapshot()['tables']['spells_new']}
    def spell(sid,name,effects,target=6,duration=0,good=1):
        row=dict(templates[12])
        row.update(id=sid,name=name,targettype=target,mana=0,cast_time=0,recovery_time=0,recast_time=0,
                   buffdurationformula=4 if duration else 0,buffduration=duration,goodEffect=good,
                   short_buff_box=0,spellgroup=sid,can_mgb=0)
        for i in range(1,17):row[f'classes{i}']=255
        for i in range(1,5):
            row[f'components{i}']=-1;row[f'component_counts{i}']=1;row[f'NoexpendReagent{i}']=-1
        for i in range(1,13):
            row[f'effectid{i}']=254;row[f'effect_base_value{i}']=0;row[f'effect_limit_value{i}']=0
            row[f'max{i}']=0;row[f'formula{i}']=100
        for i,(effect,base,limit) in enumerate(effects,1):
            row[f'effectid{i}']=effect;row[f'effect_base_value{i}']=base;row[f'effect_limit_value{i}']=limit
        if set(row)!=set(templates[12]):raise ValueError('Unknown spell schema')
        return row
    # Calibrated Nightcap magnitudes; do not present these as recovered THJ rows.
    out=[spell(42840,'Holy Shield Rune',[(55,230,0)],duration=10),
         spell(42841,'Sympathetic Healing VI',[(0,300,0)],target=5),
         spell(42842,'Sympathetic Healing VII',[(0,350,0)],target=5),
         spell(42843,'Sympathetic Healing Focus VI',[(383,100,42841),(138,1,0),(348,10,0),(142,50,0),(134,60,0),(141,1,0),(137,0,0)]),
         spell(42844,'Sympathetic Healing Focus VII',[(383,100,42842),(138,1,0),(348,10,0),(142,61,0),(134,65,0),(141,1,0),(137,0,0)]),
         # A visible worn marker; native HealDamage/Mend owns the one10% multiplier.
         spell(42845,"Marr's Renewal",[]),
         spell(42846,'Diaku Retaliation',[(0,-150,0)],target=5,good=0),
         spell(42847,'Diaku Combat Blessing',[(85,42846,0)],duration=1)]
    for tier,value in enumerate((-100,-175,-250,-338)):
        row=spell(42848+tier,'Hastened Truth '+str(tier+1),[(182,value,0)],duration=2)
        row['short_buff_box']=1;out.append(row)
    return out


def gear_changes():
    changes=[]
    for original in snapshot()['tables']['items']:
        base=original['id']%200000;after=dict(original)
        if base in (23498,22819):
            after.update(focuseffect=42844 if base==23498 else 42843,focustype=6,focuslevel=1,focuslevel2=1,
                         focusname='Sympathetic Healing Focus '+('VII' if base==23498 else 'VI'))
        if base==51912:
            after.update(worneffect=42847,worntype=2,wornlevel=1,wornlevel2=1,wornname='Diaku Combat Blessing',nopet=0)
        if base in (23498,27290,27298):
            combat=[original[f'augslot{i}type'] for i in range(1,7) if original[f'augslot{i}type'] in (4,7,8)]
            if len(combat)!=1:raise ValueError('Unreviewed WPM sockets')
            free=next(i for i in range(1,7) if original[f'augslot{i}type']==0)
            after[f'augslot{free}type']=combat[0];after[f'augslot{free}visible']=1
        if after!=original:changes.append((original,after))
    return changes


def item_rows():
    templates={r['id']:r for r in snapshot()['tables']['items']};out=[]
    for tier,suffix in enumerate(QUALITIES):
        power=dict(templates[28855+tier*200000])
        power.update(id=BASE_POWER+tier*200000,Name='Bloodfrenzy Core'+suffix,slots=1<<21,itemtype=69,
                     damage=0,delay=0,proceffect=-1,proctype=0,procname='',powersourcecapacity=1000,
                     maxcharges=0,price=0,sellrate=0,classes=65535,races=65535,loregroup=0,
                     comment='WPM power-source equivalent; native Bloodfrenzy weapon preserved',
                     serialized=None,serialization=None)
        for i in range(1,7):power[f'augslot{i}type']=0;power[f'augslot{i}visible']=0
        out.append(power)
        shield=dict(templates[27298+tier*200000])
        shield.update(id=BASE_SHIELD+tier*200000,Name='Shining Shield of Marr'+suffix,haste=68,
                      focuseffect=-1,focusname='',worneffect=42845,worntype=2,wornlevel=1,wornlevel2=1,
                      wornname="Marr's Renewal",price=0,sellrate=0,loregroup=0,
                      augslot3type=8,augslot3visible=1,serialized=None,serialization=None)
        out.append(shield)
        haste=dict(templates[51722])
        haste.update(id=BASE_HASTE+tier*200000,Name='Hastened Fragment of Truth'+suffix,
                     augtype=136,augrestrict=2,proceffect=42848+tier,procname='Hastened Truth '+str(tier+1),
                     procrate=0,proclevel=1,proclevel2=1,proctype=0,reqlevel=0,reclevel=0,
                     classes=65535,races=65535,nopet=0,norent=1,nodrop=1,price=0,sellrate=0,loregroup=0,
                     serialized=None,serialization=None)
        out.append(haste)
    return out


def acquisition():
    # Separate drops preserve the boss's native loot probabilities and pet fragments.
    routes=((988620,13335,BASE_POWER,3),(988621,104959,BASE_SHIELD,4),(988622,13516,BASE_HASTE,3))
    out=[]
    for drop,table,base,era in routes:
        out.append(('lootdrop',dict(id=drop,name='Nightcap WPM '+str(base),min_expansion=era,max_expansion=-1,
                                   content_flags=None,content_flags_disabled=None),{'id':drop}))
        for tier,chance in enumerate((60,30,8,2)):
            row=dict(lootdrop_id=drop,item_id=base+tier*200000,item_charges=1,equip_item=0,
                     chance=chance,disabled_chance=0,trivial_min_level=0,trivial_max_level=0,multiplier=1,
                     npc_min_level=0,npc_max_level=0,min_expansion=era,max_expansion=-1,
                     content_flags=None,content_flags_disabled=None)
            out.append(('lootdrop_entries',row,{'lootdrop_id':drop}))
        link=dict(loottable_id=table,lootdrop_id=drop,multiplier=1,droplimit=1,mindrop=1,probability=100)
        out.append(('loottable_entries',link,{'lootdrop_id':drop}))
    return out


def groups(rollback=False, include_gear=True):
    data=snapshot()['tables'];out=[]
    grouped=defaultdict(list)
    for table,row,key in acquisition():grouped[(table,tuple(key.items()))].append(row)
    for (table,key_items),rows in grouped.items():
        key=dict(key_items)
        if rollback:
            if table=='loottable_entries':out.append(dict(table=table,key=key,before=rows,after=[]))
        else:
            existing=[r for r in data.get(table,[]) if all(r[k]==v for k,v in key.items())]
            if existing:raise ValueError('Occupied WPM acquisition ID')
            out.append(dict(table=table,key=key,before=[],after=rows))
    if rollback:return out
    # Identity-only guards; never rewrite the NPC or its existing loot table.
    npcs={r['id']:r for r in data['npc_types']}
    for nid,table in ((162206,13335),(223077,104959),(159691,13516)):
        row={k:npcs[nid][k] for k in ('id','name','level','loottable_id')}
        if row['loottable_id']!=table:raise ValueError('WPM boss route drift')
        out.insert(0,dict(table='npc_types',key={'id':nid},before=[row],after=[row]))
    for table,rows in (('spells_new',spell_rows()),('items',item_rows())):
        ids={r['id'] for r in data[table]}
        for row in rows:
            if row['id'] in ids:raise ValueError('Occupied WPM content ID')
            out.append(dict(table=table,key={'id':row['id']},before=[],after=[row]))
    for before,after in (gear_changes() if include_gear else []):out.append(dict(table='items',key={'id':before['id']},before=[before],after=[after]))
    return out


def client_rows():
    return {str(r['id']):'^'.join('' if v is None else str(v) for v in r.values()) for r in spell_rows()}


def client_spells(raw):
    expected=client_rows();out=[];seen=set()
    for line in raw.decode('latin1').splitlines():
        fields=line.split('^')
        if len(fields)!=237 or fields[0] in seen:raise ValueError('Malformed or duplicate WPM client spell')
        seen.add(fields[0])
        if fields[0] in expected and expected[fields[0]]!=line:raise ValueError('WPM client spell identity drift')
        out.append(line)
    out.extend(row for sid,row in expected.items() if sid not in seen)
    return ('\r\n'.join(out)+'\r\n').encode('latin1')


def main():
    RELEASE.mkdir(parents=True,exist_ok=True)
    for rollback in (False,True):
        name='items-acquisition-rollback.sql' if rollback else 'items-forward.sql'
        (RELEASE/name).write_text(migration(groups(rollback),'nightcap_wpm_items_20261018'),newline='\n')
    (RELEASE/'items-plan.json').write_text(json.dumps(groups(),indent=2)+'\n')
    rule=dict(ruleset_id=1,rule_name='Combat:NightcapHeroicMeleeScaling',rule_value='true',
              notes='Reviewed WPM heroic-strength weapon-hit curve; requires paired world and zone.')
    disabled=dict(rule,rule_value='false')
    for name,before,after in [('forward',[],[rule]),('disable',[rule],[disabled]),('enable',[disabled],[rule])]:
        group=dict(table='rule_values',key={k:rule[k] for k in ('ruleset_id','rule_name')},before=before,after=after)
        (RELEASE/f'heroic-rule-{name}.sql').write_text(migration([group],'nightcap_wpm_heroic_20261018'),newline='\n')
    print(json.dumps({'new_items':len(item_rows()),'new_spells':len(spell_rows()),'changed_items':len(gear_changes())}))


if __name__=='__main__':main()
