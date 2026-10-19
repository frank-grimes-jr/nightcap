"""Curated WPM AA definitions, preserved canonical ownership and client strings."""
import copy
from collections import defaultdict
import gzip
import json
from pathlib import Path
from wpm_migration import migration

ROOT=Path(__file__).resolve().parents[1]
RELEASE=ROOT/'docs/releases/wpm-melee-20261018'
HOLY_ABILITY,HOLY_RANK,HOLY_SPELL=30200,43210,42840
CAPS={30:6,605:5,410:2,891:3,3820:3,131:1,108:12,273:10,341:6,HOLY_ABILITY:1}
MONK_SKILLS=(30,38,52,23,21,26)


def baseline():
    return json.loads(gzip.decompress((ROOT/'tools/fixtures/aa-tbs-catalog.json.gz').read_bytes()))


def catalog():
    tables=copy.deepcopy(baseline())
    abilities={r['id']:r for r in tables['aa_ability']}
    ranks={r['id']:r for r in tables['aa_ranks']}
    assert HOLY_ABILITY not in abilities and HOLY_RANK not in ranks
    def effects(rid, values):
        tables['aa_rank_effects'][:]=[r for r in tables['aa_rank_effects'] if r['rank_id']!=rid]
        tables['aa_rank_effects'] += [dict(rank_id=rid,slot=i,effect_id=spa,base1=b1,base2=b2)
                                     for i,(spa,b1,b2) in enumerate(values,1)]
    abilities[605]['classes']=5
    abilities[605]['name']='[WAR PAL] Shield Specialist'
    for n,rid in enumerate(range(4844,4849),1): effects(rid,[(349,n*20,0)])
    abilities[410]['name']='[MNK] Way of Steel'
    for n,rid in enumerate((12706,12707),1):
        effects(rid,[(220,n*100,skill) for skill in MONK_SKILLS] +
                [(427,23598,n*30)] + [(428,skill,0) for skill in MONK_SKILLS])
    for n,rid in enumerate((6791,6792,6793)):
        effects(rid,[(339,20+n*5,16139),(137,21,0),(385,-18000,0),
                     (339,20+n*5,16139),(137,343,0),(385,-18000,0)])
    for n,rid in enumerate((6395,6396,6397)): effects(rid,[(85,13502+n,n*10)])
    ranks[8303]['recast_time']=60
    # Native309 is disabled and duplicates active30. Redirect only the reviewed
    # families, retaining the required earned rank count and all unrelated edges.
    selected=set()
    for aid in (108,131,341):
        rid=abilities[aid]['first_rank_id']
        for _ in range(CAPS[aid]):
            selected.add(rid);rid=ranks[rid]['next_id']
    for row in tables['aa_rank_prereqs']:
        if row['rank_id'] in selected and row['aa_id']==309:row['aa_id']=30
    holy={**abilities[914], 'id':HOLY_ABILITY,'name':'[PAL] Holy Shield','classes':4,'first_rank_id':HOLY_RANK}
    tables['aa_ability'].append(holy)
    tables['aa_ranks'].append({**ranks[10548],'id':HOLY_RANK,'desc_sid':HOLY_RANK,'title_sid':HOLY_RANK,
                              'expansion':13,'next_id':-1,'prev_id':-1})
    effects(HOLY_RANK,[(200,25,0),(85,HOLY_SPELL,20),(250,25,0)])
    tables['aa_rank_prereqs'].append(dict(rank_id=HOLY_RANK,aa_id=435,points=3))
    for table,rows in tables.items(): rows.sort(key=lambda r:tuple(r[k] for k in (('rank_id','slot') if table=='aa_rank_effects' else ('rank_id','aa_id') if table=='aa_rank_prereqs' else ('id',))))
    return tables


def groups():
    before,after=baseline(),catalog(); output=[]
    for table in before:
        field='rank_id' if table in ('aa_rank_effects','aa_rank_prereqs') else 'id'
        old_groups,new_groups=defaultdict(list),defaultdict(list)
        for r in before[table]:old_groups[r[field]].append(r)
        for r in after[table]:new_groups[r[field]].append(r)
        for value in sorted(old_groups.keys()|new_groups.keys()):
            old,new=old_groups[value],new_groups[value]
            if old!=new:output.append(dict(table=table,key={field:value},before=old,after=new))
    return output


STRINGS={
 (4844,1):'Shield Specialist',
 (4844,4):'While a shield is equipped, increases primary-hand base weapon damage by 20 percent per rank, to 100 percent. Requires Shield Block III.',
 (12706,1):'Way of Steel',
 (12706,4):'Adds 100/200 damage to Kick, Round Kick, Tiger Claw, Eagle Strike, Dragon Punch and Flying Kick. Those specials can trigger Fists of Fury at 30/60 percent of the native skill-proc rate. Does not add weapon-skill damage.',
 (6791,4):'Stun casts have a 20/25/30 percent chance to trigger a 300-base Healing Light group heal. Excludes spell group 18000.',
 (6395,4):'Melee attacks can trigger a 120/180/240-base self heal. Ranks II/III increase its proc rate by 10/20 percent.',
 (8303,4):'Briefly greatly increases weapon proc chance. Base reuse is 60 seconds; existing saved cooldowns are preserved.',
 (HOLY_RANK,1):'Holy Shield',
 (HOLY_RANK,2):'Holy Shield',
 (HOLY_RANK,4):'While holding a shield, increases weapon and spell proc chance by 25 percent and adds a self rune proc. Requires Shield Block III. Removing the shield removes these benefits.',
}


def client_strings(raw):
    out=[];seen=set()
    for line in raw.decode('latin1').splitlines():
        parts=line.split('^',2)
        try:key=(int(parts[0]),int(parts[1]))
        except (ValueError,IndexError):out.append(line);continue
        if key in STRINGS:
            if key in seen:raise ValueError('Duplicate WPM AA string')
            seen.add(key);line=f'{key[0]}^{key[1]}^{STRINGS[key]}'
        out.append(line)
    for key in sorted(STRINGS.keys()-seen):out.append(f'{key[0]}^{key[1]}^{STRINGS[key]}')
    return ('\r\n'.join(out)+'\r\n').encode('latin1')


def main():
    (RELEASE/'content').mkdir(parents=True,exist_ok=True)
    (ROOT/'tools/fixtures/aa-wpm-catalog.json.gz').write_bytes(gzip.compress(json.dumps(catalog(),separators=(',',':')).encode(),mtime=0))
    (RELEASE/'content/aa-forward.sql').write_text(migration(groups(),'nightcap_wpm_aa_20261018'),newline='\n')
    (RELEASE/'content/aa-plan.json').write_text(json.dumps(groups(),indent=2)+'\n')
    print(json.dumps({'groups':len(groups()),'caps':CAPS,'new_holy_shield':HOLY_ABILITY}))


if __name__=='__main__':main()
