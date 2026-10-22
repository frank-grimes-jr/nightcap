"""Deterministic, reviewed Classic equipment and objective catalog compiler."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REVISION=2026101601
BANDS=(20,30,40,50)
# Explicit Classic base budgets: AC, HP, mana, primary stat, resist.
BUDGET={20:(5,10,10,2,2),30:(7,20,20,3,3),40:(9,30,30,4,4),50:(12,40,40,5,5)}
QUALITIES=('Normal','Polished','Ascended')
# name, slot mask, icon, two supporting stats. These are eight independent designs.
ARMOR=[('Oathkeeper Helm',4,639,'asta','awis'),
       ('Deepward Cuirass',131072,678,'asta','astr'),
       ('Delver Armguards',128,546,'astr','adex'),
       ('Runeseeker Bracers',1536,634,'aint','awis'),
       ('Lanternwatch Gloves',4096,517,'adex','aagi'),
       ('Stonepath Greaves',262144,631,'asta','aagi'),
       ('Silentvault Boots',524288,666,'aagi','adex'),
       ('Warden Shoulderwrap',64,535,'awis','aint')]
# name, native type, delay, damage by band, icon, existing model. No quality delay changes.
WEAPONS=[('Vaultsteel Saber',0,28,(7,9,11,13),604,'IT41'),
         ('Oathstone Maul',3,30,(8,10,12,14),567,'IT14'),
         ('Whisperpoint Dirk',2,22,(5,6,8,10),592,'IT10650'),
         ('Cryptwarden Greatblade',1,42,(14,18,22,26),579,'IT39'),
         ('Runebound Greatstaff',4,40,(13,17,21,25),602,'IT8'),
         ('Deepguard Pike',35,38,(12,16,20,24),598,'IT17'),
         ('Lanternwood Longbow',5,35,(10,13,16,19),597,'IT9'),
         ('Wayfarer Knuckles',45,24,(6,8,10,12),592,'IT10650')]
ACCESSORIES=[('Hearthglass Earring',18,535,'awis','asta'),
             ('Nightward Signet',98304,615,'astr','adex'),
             ('Witness Pendant',32,500,'aint','awis'),
             ('Veil of Lost Runes',8,677,'aint','acha'),
             ('Waykeeper Cloak',256,661,'asta','aagi'),
             ('Delver Utility Belt',1048576,565,'astr','asta')]
BAGS=['Wayfarer Field Satchel','Runekeeper Reliquary']
# Audited explicit exclusions, including a native spawn with no era gate.
# See permafrost-era-audit.json; public populations are not changed.
EXCLUDED_NPCS=[dict(zone_id=73,npc_id=i) for i in (73039,73090,73092)]
BOSS_DESIGNS=[
 ("Moltor's Graveblade","Amiaz's Ossuary Ward","Befallen Bonekeeper's Bag"),
 ("Rucksif's Dirgehammer","Rucksif's Mourning Mantle","Unrest Memory Satchel"),
 ("McCabe's Concealed Stiletto","High Keep Captain's Gorget","McCabe's Hidden Treasury"),
 ("Najena's Runestaff","Drelzna's Midnight Gloves","Najena's Spellfold Satchel"),
 ("Fearbound Ceremonial Pike","Avatar's Dreadscale Mantle","Thule's Sealed Reliquary"),
 ("Vox's Rimecleaver","Vox's Hoarfrost Aegis","Vox's Hoarfrost Satchel"),
 ("Nagafen's Emberfang","Nagafen's Cinderheart Guard","Nagafen's Ashen Hoard")]

# Fixed identity selection. The compiler resolves exact spawn identities once;
# runtime never searches names, rare flags, or event/era guesses.
DUNGEONS=[
 ('befallen',36,999227,20,[36040,36095,36097,36000,36103]),
 ('unrest',63,999228,30,[63092,63075,63086,63010,63003,63052,63062]),
 ('highkeep',6,999229,40,[6034,6042,6047,6181]),
 ('najena',44,999230,30,[44027,44102,44095,44024,44004,44094,44033,44103,44100]),
 ('cazicthule',48,999231,40,[]),
 ('permafrost',73,999232,50,[73104,73068,73022,73013,73004,73006,73103,73057]),
 ('soldungb',32,999233,50,[32068,32063,32045,32059,32066,32083,32015,32057,32062,32041,32022,32020,32040])]

LEGACY_DUNGEONS=tuple(DUNGEONS)
from classic_dungeon_catalog import ADDED_DUNGEONS, SKY_PRIVATE, SKY_SERVICES, SKY_KEY_SERVICE
DUNGEONS += ADDED_DUNGEONS

def base_item(id,name):
    item=dict.fromkeys(('ac hp mana astr asta aagi adex aint awis acha mr fr cr pr dr damage delay magic range '
        'bagsize bagslots bagtype bagwr accuracy attack avoidance damageshield dotshielding endur haste regen '
        'manaregen enduranceregen shielding spellshield strikethrough stunresist svcorruption skillmodtype '
        'skillmodvalue skillmodmax banedmgamt banedmgraceamt banedmgbody banedmgrace elemdmgtype elemdmgamt '
        'bardtype bardvalue extradmgskill extradmgamt augtype augrestrict healamt spelldmg clairvoyance '
        'backstabdmg dsmitigation purity evoitem evoid evolvinglevel evomax notransfer heirloom epicitem '
        'scriptfileid recskill procrate material herosforgemodel').split(),0)
    item.update({f'heroic_{stat}':0 for stat in ('str','sta','agi','dex','int','wis','cha','mr','fr','cr','pr','dr','svcorrup')})
    item.update({f'augslot{i}{field}':0 for i in range(1,7) for field in ('type','visible','unk2')})
    item.update(dict(id=id,Name=name,lore=name,itemclass=0,itemtype=10,slots=0,
                classes=65535,races=65535,deity=0,nodrop=1,norent=1,attuneable=0,
                loregroup=0,price=0,sellrate=0,stackable=0,stacksize=1,reqlevel=0,
                reclevel=0,weight=5,size=2,icon=500,idfile='IT63',
                clickeffect=-1,worneffect=-1,focuseffect=-1,proceffect=-1,
                scrolleffect=-1,bardeffect=-1,nopet=0,combateffects='0'))
    return item

def equipment(id,design,band,quality,name=None):
    prefix=('Delver','Keeper','Warden','Elder')[BANDS.index(band)]
    names=[a[0] for a in ARMOR]+[w[0] for w in WEAPONS]+[a[0] for a in ACCESSORIES]+BAGS
    title=(QUALITIES[quality]+' ' if quality else '')+(name or prefix+' '+names[design])
    item=base_item(id,title)
    ac,hp,mana,stat,resist=BUDGET[band]
    boost=(100,115,135)[quality]
    scale=lambda v:max(v+quality,v*boost//100) if v else 0
    if design<8 or 16<=design<22:
        row=ARMOR[design] if design<8 else ACCESSORIES[design-16]
        _,slot,icon,s1,s2=row
        item.update(slots=slot,icon=icon,ac=scale(ac if design<8 else ac//2),
                    hp=scale(hp),mana=scale(mana),mr=scale(resist),**{s1:scale(stat),s2:scale(stat)})
    elif design<16:
        _,kind,delay,damages,icon,model=WEAPONS[design-8]
        damage=damages[BANDS.index(band)]
        item.update(itemtype=kind,slots=2048 if kind==5 else 8192 if kind in (1,4,35) else 24576,
                    delay=delay,damage=scale(damage),icon=icon,idfile=model,
                    hp=scale(hp//2),mana=scale(mana//2),adex=scale(stat),astr=scale(stat),magic=1)
        if kind==5:item['range']=100
    else:
        index=BANDS.index(band)
        capacity=min(10,6+2*((index+1)//2+quality+(design==23)))
        wr=min(100,20+index*15+quality*15+(10 if design==23 else 0))
        item.update(itemclass=1,itemtype=11,bagslots=capacity,bagwr=wr,bagsize=4,
                    bagtype=1,icon=884 if design==23 else 667,idfile='IT64',weight=10)
    assert len(title)<64
    return item

def legacy_items():
    """October16 captured budgets, retained only to build guarded migrations."""
    result=[]
    for band_index,band in enumerate(BANDS):
        for design in range(24):
            for quality in range(3):
                id=960000+(band_index*24+design)*3+quality
                result.append(dict(id=id,band=band,quality=QUALITIES[quality],design=design,
                                   source='completion',values=equipment(id,design,band,quality)))
    for dungeon,(_,_,_,band,_) in enumerate(LEGACY_DUNGEONS):
        for design,template in enumerate(((8,17,22),(9,20,22),(10,18,23),(12,4,22),(13,7,23),(11,7,23),(8,1,23))[dungeon]):
            for quality in (1,2):
                id=960288+(dungeon*3+design)*2+quality-1
                result.append(dict(id=id,band=band,quality=QUALITIES[quality],design=design,
                                   source=DUNGEONS[dungeon][0],values=equipment(id,template,band,quality,BOSS_DESIGNS[dungeon][design])))
    return result

def items():
    # One policy supplies the live compiler and the starter comparison. Do not
    # feed these afterimages back into the historical preimage planner.
    from starter_retune import dungeon_proposal
    return dungeon_proposal(legacy_items())

def objectives(snapshot):
    result=[]
    npcs={n['id']:n for n in snapshot['npc_types']}
    for index,(short,zone,keeper,band,roster) in enumerate(DUNGEONS):
        used=set(); bosses=[]
        for position,npcid in enumerate(roster):
            npc=npcs[npcid]
            assert npc['merchant_id']==0 and npc['class']<=16
            groups={e['spawngroupID'] for e in snapshot['spawnentry'] if e['npcID']==npcid
                    and e['min_expansion']<=0 and not e['content_flags']}
            candidates=sorted((s for s in snapshot['spawn2'] if s['zone']==short and s['spawngroupID'] in groups
                               and s['min_expansion']<=0 and not s['content_flags'] and s['id'] not in used),key=lambda s:s['id'])
            if not candidates:raise ValueError(f'No independent Classic spawn for {npcid} {npc["name"]}')
            spawn=candidates[0];used.add(spawn['id'])
            bosses.append(dict(boss_id=position+1,npc_id=npcid,name=npc['name'].lstrip('#').replace('_',' '),
                               spawn_id=spawn['id'],spawn=spawn,is_final=position==len(roster)-1))
        result.append(dict(index=index,zone=short,zone_id=zone,keeper_id=keeper,band=band,
                           band_index=BANDS.index(band),task_grind=9700+index*2,task_raid=9701+index*2,bosses=bosses))
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'docs/dungeons')
    args=parser.parse_args()
    snap=json.loads((ROOT/'docs/dungeons/local-content.json').read_text())
    added=json.loads((ROOT/'docs/dungeons/classic-expansion-20261022/content.json').read_text())
    for table in ('npc_types','spawnentry','spawn2'):
        snap[table] += added[table]
    dungeons=objectives(snap)
    adapted=json.loads((ROOT/'docs/dungeons/classic-ct-adapted.json').read_text())
    dungeons[4]['bosses']=adapted['roster']
    data={'revision':REVISION,'era':'Classic','items':items(),'dungeons':dungeons,'excluded_npcs':EXCLUDED_NPCS,
          'content_sha256':hashlib.sha256((ROOT/'docs/dungeons/local-content.json').read_bytes()).hexdigest(),
          'status':'candidate; automated integration and all gameplay acceptance pending'}
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'catalog.json').write_text(json.dumps(data,indent=2)+'\n')
    header=['#pragma once','#include <cstdint>','namespace NightcapDungeon {',
      'struct Dungeon { uint32_t zone, keeper; unsigned band, count, index; const char *name; };',
      'struct Boss { uint32_t zone, spawn, npc; unsigned objective; bool final; const char *name; };',
      'inline constexpr Dungeon Dungeons[] = {']
    for d in dungeons:
        header.append('\t{%d,%d,%d,%d,%d,"%s"},'%(d['zone_id'],d['keeper_id'],d['band_index'],len(d['bosses']),d['index'],d['zone']))
    header+=['};','inline constexpr unsigned DungeonCount = sizeof(Dungeons)/sizeof(Dungeons[0]);','inline constexpr Boss Bosses[] = {']
    for d in dungeons:
        for b in d['bosses']:
            header.append('\t{%d,%d,%d,%d,%s,"%s"},'%(d['zone_id'],b['spawn_id'],b['npc_id'],b['boss_id'],'true' if b['is_final'] else 'false',b['name']))
    header+=['};','struct ExcludedNPC { uint32_t zone, npc; };','inline constexpr ExcludedNPC ExcludedNPCs[] = {']
    header += ['\t{%d,%d},'%(r['zone_id'],r['npc_id']) for r in EXCLUDED_NPCS]
    header+=['};',f'inline constexpr uint32_t SkyKeyService = {SKY_KEY_SERVICE};',
      f'inline unsigned PrivateSpawnCount(uint32_t zone) {{ return zone==48 ? 188 : zone==71 ? {len(SKY_PRIVATE)+len(SKY_SERVICES)} : 0; }}',
      'inline const Dungeon *FindDungeon(uint32_t zone) { for (const auto &d : Dungeons) { if (d.zone==zone) { return &d; } } return nullptr; }','}']
    (ROOT/'server-mods/code/common/dungeon_catalog.h').write_text('\n'.join(header)+'\n')
    print(f'{len(data["items"])} item definitions; {sum(len(d["bosses"]) for d in data["dungeons"])} objectives')

if __name__=='__main__': main()
