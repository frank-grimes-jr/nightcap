"""Generate explicit earned-AA and equipment native comparison fixtures offline."""
import copy
import itertools
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
import wpm_aa
from aa_tbs_policy import compile_policy
from wpm_migration import insert


def main():
    table=wpm_aa.catalog();config=json.loads((ROOT/'config/aa-policy.json').read_text())
    rows=compile_policy(table,config);native={r['id']:r for r in table['aa_ranks']}
    def purchases(classes,full):
        mask=sum(1<<(c-1) for c in classes)
        pending=[r for r in rows if r['classes']&mask and (full or native[r['rank_id']]['cost']==0)]
        result=[];owned={};cost=0
        while pending:
            ready=[r for r in pending if owned.get(r['ability_id'],0)==r['ordinal']-1 and
                   all(owned.get(a,0)>=n for a,n in r['prereqs'].items())]
            if not ready:break # inaccessible class-specific prerequisite is not waived
            for r in ready:
                result.append(r['rank_id']);owned[r['ability_id']]=r['ordinal'];cost+=native[r['rank_id']]['cost'];pending.remove(r)
        return result,cost
    old=json.loads((ROOT.parent/'wpm-melee-prior-inputs.json').read_text())['cases'][0]['input']
    pet_old=json.loads((ROOT.parent/'wpm-pet-prior-inputs.json').read_text())['cases'][0]['input']
    cases=[];sql=[];next_id=90001
    def add(name,data,full,pet_equipped=False,seed=1729):
        nonlocal next_id
        data=copy.deepcopy(data);b=data['builds'][0];cid=next_id;next_id+=1
        b['test_character_id']=cid;b['aa_rank_ids'],b['aa_budget']=purchases(b['classes'],full)
        b['aa_stage']='earned_max' if full else 'zero_cost';b['aa_policy']=config['id']
        sql.append(insert('character_data',dict(id=cid,account_id=1,name='WPMProbe'+str(cid),**{'class':b['classes'][0],'level':b['level']})))
        sql.append(insert('character_multiclass',dict(character_id=cid,class2=b['classes'][1],class3=b['classes'][2])))
        if pet_equipped:
            for cls in (13,11,10):
                gear=[dict(slot=13,id=622946,augments=[dict(socket=0,id=780610),dict(socket=2,id=780611)]),dict(slot=14,id=601555)]
                gear += [entry for entry in b['equipment'] if entry['slot'] not in (13,14,21)][:13 if cls==13 else 6]
                for entry in gear:
                    row=dict(character_id=cid,slot_id=entry['slot'],item_id=entry['id'],charges=1,pet_class=cls)
                    for aug in entry.get('augments',[]):row[['augment_one','augment_two','augment_three','augment_four','augment_five','augment_six'][aug['socket']]]=aug['id']
                    sql.append(insert('character_pet_armor',row))
        cases.append(dict(id=name,seed=seed,input=data))
    wpm=copy.deepcopy(old);b=wpm['builds'][0]
    b.update(profile='war-pal-mnk',classes=[1,3,7],level=65,tier='captured_ascended_wpm')
    byslot={e['slot']:e for e in b['equipment']}
    byslot[2]=dict(slot=2,id=604504) # Classic Tranix crown, wearable by all held classes
    byslot[16]=dict(slot=16,id=614679) # Classic crafted ring; prior fixture excluded WPM
    byslot[13]=dict(slot=13,id=623498,augments=[dict(socket=0,id=780622),dict(socket=2,id=780610)])
    byslot[14]=dict(slot=14,id=780621,augments=[dict(socket=0,id=651912)]) # Runic Fragment is weapon-only
    byslot[8]=dict(slot=8,id=622819) # cloak occupies back, not arms
    byslot[21]=dict(slot=21,id=780620)
    # Slot17 is chest; native Back is8 in this inventory layout.
    b['equipment']=list(byslot.values())
    wpm['encounter']=dict(npc_id=32040,npc_position=[-871,-1395,104.879997,45],duration_ms=180000,
                          return_to_melee=True,combat_policy='wpm',melee_specials=True,active_aa_policy='wpm')
    wpm['wpm_state']=True
    for order in itertools.permutations((1,3,7)):
        probe=copy.deepcopy(wpm);probe.pop('encounter');probe['builds'][0]['classes']=list(order);probe['shield_swap_probe']=True
        add('stats-wpm-'+''.join(map(str,order)),probe,True)
    for full in (False,True):
        for mode in ('shield','dual','twohand'):
            data=copy.deepcopy(wpm)
            if mode!='shield':
                gear={e['slot']:e for e in data['builds'][0]['equipment']}
                if mode=='dual':gear[14]=dict(slot=14,id=626740)
                else:
                    gear.pop(14);gear[13]=dict(slot=13,id=631232,augments=[dict(socket=0,id=780622),dict(socket=2,id=780610)])
                data['builds'][0]['equipment']=list(gear.values())
            add('wpm-'+mode+('-max' if full else '-zero'),data,full)
    undead=copy.deepcopy(wpm);undead['encounter']['undead_control']=True
    add('wpm-shield-undead-max',undead,True)
    for full in (False,True):
        for equipped in (False,True):
            data=copy.deepcopy(pet_old);data['builds'][0]['level']=65
            data['pet_probe']['retry_native_fizzles']=True
            data['pet_probe']['combat'].update(duration_ms=180000,approach_policy='native_spell_range',capture_terminal=True)
            add('pet-'+('equipped' if equipped else 'bare')+('-max' if full else '-zero'),data,full,equipped)
    control=copy.deepcopy(wpm);control['heroic_scaling_control']=False
    add('wpm-shield-heroic-off',control,True)
    for base in list(cases):
        if base['id'] in ('wpm-shield-max','pet-equipped-max'):
            add(base['id']+'-seed-2718',base['input'],True,base['id'].startswith('pet'),seed=2718)
    classic=copy.deepcopy(old);classic['builds'][0].update(profile='war-pal-mnk',classes=[1,3,7])
    for entry in classic['builds'][0]['equipment']:
        if entry['slot']==2:entry['id']=604504
        elif entry['slot']==16:entry['id']=614679
    classic['encounter']=copy.deepcopy(wpm['encounter']);classic['wpm_state']=True
    add('wpm-classic50-zero',classic,False)
    add('wpm-classic50-max',classic,True)
    caster=json.loads((ROOT.parent/'wpm-caster-prior-inputs.json').read_text())
    caster['builds']=caster['builds'][:1];caster['builds'][0]['level']=65
    caster['encounter']=dict(npc_id=32040,npc_position=[-871,-1395,104.879997,45],duration_ms=180000,return_to_melee=True,combat_policy='caster_heal')
    add('caster65-zero',caster,False)
    add('caster65-max',caster,True)
    for equipped in (False,True):
        data=copy.deepcopy(next(c['input'] for c in cases if c['id']=='pet-equipped-max'))
        for action in data['pet_probe']['actions']:
            if 'spell' in action:action['spell']={633:3324,443:3314,166:3377}.get(action['spell'],action['spell'])
        add('pet-pop65-'+('equipped' if equipped else 'bare')+'-max',data,True,equipped)
    folder=ROOT.parent/'wpm-native-matrix';folder.mkdir(exist_ok=True)
    (folder/'matrix.json').write_text(json.dumps({'cases':cases,'scope':'Native diagnostic; explicit gear and earned-AA budgets, synthetic identities; no production mutation'},indent=2))
    guard="""DELIMITER //
CREATE PROCEDURE wpm_matrix_guard()
BEGIN
 IF DATABASE()<>'nightcap_wpm_balance_20261018' THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Synthetic WPM database required';
 END IF;
 IF EXISTS(SELECT 1 FROM character_data WHERE id>=90001 AND id<%d AND name NOT LIKE 'WPMProbe%%') THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Fixture ID collision';
 END IF;
END//
DELIMITER ;
CALL wpm_matrix_guard();
DROP PROCEDURE wpm_matrix_guard;
START TRANSACTION;
""" % next_id
    cleanup='\n'.join(f'DELETE FROM {table} WHERE {column}>=90001 AND {column}<{next_id};' for table,column in (
        ('character_pet_armor','character_id'),('character_multiclass','character_id'),('character_data','id')))
    (folder/'characters.sql').write_text(guard+cleanup+'\n'+'\n'.join(sql)+'\nCOMMIT;\n')
    print(json.dumps({'cases':len(cases),'folder':str(folder)}))


if __name__=='__main__':main()
