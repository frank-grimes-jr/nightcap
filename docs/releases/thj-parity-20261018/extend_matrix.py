"""Add explicit low/mid/endgame spell and equipment controls to WPM's matrix."""
import copy,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];REL=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import thj_combined_content as content,starter_retune,wpm_aa
from aa_tbs_policy import compile_policy
from dungeon_catalog import items as dungeon_items
from wpm_migration import insert
from prepare_native import DB,db_command,STAGE

def select_gear(rows,level,mask):
    available=[r for r in rows if int(r['itemclass'])==0 and int(r.get('augtype',0))==0 and int(r.get('reqlevel',0))<=level and int(r['classes'])&mask and int(r.get('races',65535))&1 and int(r.get('deity',0)) in (0,65535) and int(r['damage'])==0]
    result=[];lore=set()
    def lore_key(row):
        group=int(row['loregroup'])
        return (group,row['id'] if group==-1 else 0)
    for slot in (0,1,2,3,4,5,6,7,8,9,10,12,15,16,17,18,19,20):
        choices=[r for r in available if int(r['slots'])&(1<<slot) and
                 (int(r['loregroup'])==0 or lore_key(r) not in lore)]
        if choices:
            row=max(choices,key=lambda r:(int(r['hp'])+int(r['mana'])+int(r['ac'])+int(r['spelldmg']),-int(r['id'])))
            result.append(dict(slot=slot,id=row['id']))
            if int(row['loregroup']):lore.add(lore_key(row))
    return result

def main():
    matrix=json.loads((STAGE/'matrix.json').read_text())
    assert len(matrix['cases'])==26,'Extend the original handoff exactly once'
    template=copy.deepcopy(next(c['input'] for c in matrix['cases'] if c['id']=='caster65-zero'))
    template.pop('encounter');template.update(spell_samples=200,export_equipment=True)
    template['builds']=template['builds'][:1]
    table=wpm_aa.catalog();config=json.loads((ROOT/'config/aa-policy.json').read_text())
    policy=compile_policy(table,config);native={r['id']:r for r in table['aa_ranks']}
    classes=[11,2,12];mask=sum(1<<(c-1) for c in classes)
    free=[r['rank_id'] for r in policy if r['classes']&mask and native[r['rank_id']]['cost']==0 and r['ordinal']==1 and not r['prereqs']]
    after=content.proposed_items(content.after_companions(content.original_items()))
    starter=[after[i] for i in sorted(starter_retune.APPROVED_IDS) if i<1037]
    dungeon=[r['values'] for r in dungeon_items() if r['quality']=='Normal' and r['source']=='completion']
    targets=[after[r['id']] for r in content.thj_item_parity.catalog()['items']]
    def gear(rows,level):
        return select_gear(rows,level,mask)
    sql=[];next_id=90100
    def add(name,level,rows,enabled=True):
        nonlocal next_id
        data=copy.deepcopy(template);b=data['builds'][0];cid=next_id;next_id+=1
        b.update(test_character_id=cid,profile='nec-clr-wiz',classes=classes,level=level,
                 equipment=gear(rows,level),tier=name,aa_rank_ids=free,aa_budget=0,aa_stage='zero_cost')
        b['spell_probes']=[dict(spell_id=54,npc_id=32040),dict(spell_id=17),dict(spell_id=360,npc_id=32040,periodic=True)]
        data.update(thj_damage_control=enabled,heroic_spell_control=enabled)
        sql.append(insert('character_data',dict(id=cid,account_id=1,name='THJProbe'+str(cid),**{'class':11,'level':level})))
        sql.append(insert('character_multiclass',dict(character_id=cid,class2=2,class3=12)))
        matrix['cases'].append(dict(id=name,seed=1729,input=data))
    for level in (10,20,30,40,50):
        add(f'parity-l{level}-starter-normal',level,starter)
        add(f'parity-l{level}-starter-ascended',level,[after[r['id']+600000] for r in starter])
        if level>=20:add(f'parity-l{level}-dungeon-normal',level,dungeon)
    for level in (50,65):
        add(f'parity-l{level}-observed-ascended',level,targets)
        add(f'parity-l{level}-observed-legacy-spells',level,targets,False)
    # Paired full encounters hold the combined item afterimages constant.
    for base in list(matrix['cases'][:26]):
        if base['id'] in ('caster65-max','pet-equipped-max','wpm-shield-max'):
            case=copy.deepcopy(base);case['id']+='-legacy-spells';case['input'].update(thj_damage_control=False,heroic_spell_control=False)
            matrix['cases'].append(case)
    sql=['START TRANSACTION;']+sql+['COMMIT;']
    subprocess.run(db_command(DB),input='\n'.join(sql),text=True,check=True)
    target=STAGE/'matrix.json';target.write_text(json.dumps(matrix,indent=2)+'\n')
    (REL/'native-matrix.json').write_bytes(target.read_bytes())
    subprocess.run(['docker','cp',str(target),'akk-stack-eqemu-server-1:/tmp/nightcap-balance-thj-parity-20261018/matrix.json'],check=True)
    for name in ('native_harness.cpp','native_runtime.cpp','native_runtime.h','build_native.py'):
        subprocess.run(['docker','cp',str(ROOT/'tools/balance'/name),'akk-stack-eqemu-server-1:/tmp/nightcap-balance-thj-parity-20261018/'+name],check=True)
    print(json.dumps({'cases':len(matrix['cases']),'new_fixture_characters':next_id-90100,'database':DB}))

if __name__=='__main__':main()
