"""Generate exact schema fingerprints and explicit runtime content checks.

Schema fingerprints come only from a successful isolated installation rehearsal.
Content predicates come from the reviewed catalog, not a mutable live database.
"""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/tests'))
from rehearse_dungeons import query
from dungeon_prepare import sql

TABLES=['nightcap_dungeon_'+x for x in ('state','runs','members','kills','deaths','loot','spawns','checkpoints','corpses','respawns')]+['instance_list','instance_list_player','character_advloot_claims']

def schema_checks():
    checks=[]
    for table in TABLES:
        for source,fields,order,where in (
            ('columns','column_name,column_type,is_nullable,column_default,extra,collation_name','ordinal_position','table_schema=DATABASE()'),
            ('statistics','index_name,non_unique,seq_in_index,column_name,sub_part,index_type','index_name,seq_in_index','table_schema=DATABASE()'),
            ('key_column_usage','constraint_name,column_name,ordinal_position,referenced_table_name,referenced_column_name','constraint_name,ordinal_position','table_schema=DATABASE()')):
            # Hash each metadata row before concatenating: bounded to 64 bytes
            # per column/index. Check the server limit explicitly at runtime.
            # MariaDB >=10.6 reports the legacy utf8_general_ci collation as
            # utf8mb3_general_ci. Canonicalize only this audited name alias;
            # utf8mb4 and genuinely different collations must still reject.
            def metadata_field(field):
                return ("CASE collation_name WHEN 'utf8_general_ci' THEN 'utf8mb3_general_ci' ELSE collation_name END"
                        if field=='collation_name' else field)
            expression="CONCAT_WS('|',"+','.join("COALESCE(CAST("+metadata_field(f)+" AS CHAR),'~NULL~')" for f in fields.split(','))+')'
            statement=f"SELECT COALESCE(SHA2(GROUP_CONCAT(SHA2({expression},256) ORDER BY {order} SEPARATOR ''),256),'empty') FROM information_schema.{source} WHERE {where} AND table_name='{table}'"
            checks.append(dict(label=table+'/'+source,sql=statement))
    return checks

def predicate(row):
    return '('+' AND '.join((f'ABS(`{k}`-({sql(v)}))<0.0001' if isinstance(v,float) else f'`{k}` <=> {sql(v)}') for k,v in row.items())+')'

def content_checks():
    folder=ROOT/'docs/dungeons'
    payload=json.loads((folder/'install-rows.json').read_text())
    catalog=json.loads((folder/'catalog.json').read_text())
    snap=json.loads((folder/'local-content.json').read_text())
    checks=[]
    for table,rows in payload.items():
        # Small queries avoid packet limits; every expected row must occur once.
        for i in range(0,len(rows),8):
            batch=rows[i:i+8]
            checks.append(dict(label=f'{table}/{i}',sql=f'SELECT COUNT(*) FROM `{table}` WHERE '+' OR '.join(predicate(r) for r in batch),expected=str(len(batch))))
    for d in catalog['dungeons']:
        if d['zone_id']==48:continue
        for b in d['bosses']:
            npc=next(n for n in snap['npc_types'] if n['id']==b['npc_id'])
            fields=('id','name','level','class','hp','mindmg','maxdmg','loottable_id','npc_spells_id','npc_faction_id','merchant_id')
            checks.append(dict(label='objective/'+str(b['npc_id']),sql='SELECT COUNT(*) FROM npc_types WHERE '+predicate({k:npc[k] for k in fields}),expected='1'))
            fields=('id','zone','version','spawngroupID','respawntime','min_expansion','content_flags','content_flags_disabled')
            checks.append(dict(label='spawn/'+str(b['spawn_id']),sql='SELECT COUNT(*) FROM spawn2 WHERE '+predicate({k:b['spawn'][k] for k in fields}),expected='1'))
    return checks

def loaded_races(v):
    # Mirror NightcapEquipment::ApplyRacePolicy: wearable player gear loads with every
    # race. SQL rows and their predicates keep the stored mask.
    if (v.get('itemclass',0)==0 and v.get('classes',0)&0xffff and v.get('races',0)&0xffff
            and (v.get('slots',0)&0x7fffff or v.get('augtype',0))):
        return 0xffff
    return v.get('races',0)

def render_header(checks, content, items):
    out=['#pragma once','#include "common/item_data.h"','#include <cstring>','namespace NightcapDungeon {','struct ContractCheck { const char *label, *sql, *expected; };']
    for name,rows in [('SchemaChecks',checks),('ContentChecks',content)]:
        out.append('inline constexpr ContractCheck '+name+'[] = {')
        for c in rows:out.append('\t{'+json.dumps(c['label'])+',R"NC('+c['sql']+')NC",'+json.dumps(c['expected'])+'},')
        out.append('};')
    fields={'itemclass':'ItemClass','itemtype':'ItemType','slots':'Slots','classes':'Classes','races':'Races',
            'damage':'Damage','delay':'Delay','hp':'HP','mana':'Mana','ac':'AC','bagslots':'BagSlots','bagwr':'BagWR','bagsize':'BagSize',
            'astr':'AStr','asta':'ASta','aagi':'AAgi','adex':'ADex','aint':'AInt','awis':'AWis','acha':'ACha',
            'mr':'MR','fr':'FR','cr':'CR','pr':'PR','dr':'DR','reqlevel':'ReqLevel','reclevel':'RecLevel','icon':'Icon',
            'magic':'Magic','range':'Range','bagtype':'BagType','size':'Size','deity':'Deity','weight':'Weight','stackable':'Stackable',
            'stacksize':'StackSize','nopet':'NoPet','sellrate':'SellRate','clickeffect':'Click.Effect','proceffect':'Proc.Effect',
            'worneffect':'Worn.Effect','focuseffect':'Focus.Effect','scrolleffect':'Scroll.Effect','bardeffect':'Bard.Effect'}
    fields.update(dict(zip(
        'accuracy attack avoidance damageshield dotshielding endur haste regen manaregen enduranceregen shielding spellshield strikethrough stunresist svcorruption skillmodtype skillmodvalue skillmodmax banedmgamt banedmgraceamt banedmgbody banedmgrace elemdmgtype elemdmgamt bardtype bardvalue extradmgskill extradmgamt augtype augrestrict healamt spelldmg clairvoyance backstabdmg dsmitigation purity evoitem evoid evolvinglevel evomax notransfer scriptfileid recskill procrate material herosforgemodel combateffects'.split(),
        'Accuracy Attack Avoidance DamageShield DotShielding Endur Haste Regen ManaRegen EnduranceRegen Shielding SpellShield StrikeThrough StunResist SVCorruption SkillModType SkillModValue SkillModMax BaneDmgAmt BaneDmgRaceAmt BaneDmgBody BaneDmgRace ElemDmgType ElemDmgAmt BardType BardValue ExtraDmgSkill ExtraDmgAmt AugType AugRestrict HealAmt SpellDmg Clairvoyance BackstabDmg DSMitigation Purity EvolvingItem EvolvingID EvolvingLevel EvolvingMax NoTransfer ScriptFileID RecSkill ProcRate Material HerosForgeModel CombatEffects'.split())))
    for stat in ('Str','Sta','Agi','Dex','Int','Wis','Cha','MR','FR','CR','PR','DR','SVCorrup'):
        fields['heroic_'+stat.lower()]='Heroic'+stat
    for i in range(1,7):
        for field,native in [('type','AugSlotType'),('visible','AugSlotVisible'),('unk2','AugSlotUnk2')]:
            fields[f'augslot{i}{field}']=f'{native}[{i-1}]'
    out.append('inline bool CacheMatches(const EQ::ItemData &i) { switch(i.ID) {')
    for item in items:
        v=item['values']
        conditions=['std::strcmp(i.Name,'+json.dumps(v['Name'])+')==0','std::strcmp(i.IDFile,'+json.dumps(v['idfile'])+')==0',
                    'std::strcmp(i.Lore,'+json.dumps(v['lore'])+')==0']
        conditions += ['i.'+native+'=='+str(loaded_races(v) if sql=='races' else v.get(sql,0)) for sql,native in fields.items()]
        for key,native in {'clicktype':'Click.Type','clicklevel':'Click.Level','clicklevel2':'Click.Level2',
                           'casttime':'CastTime','casttime_':'CastTime_','maxcharges':'MaxCharges',
                           'recastdelay':'RecastDelay','recasttype':'RecastType'}.items():
            if key in v:conditions.append('i.'+native+'=='+str(v[key]))
        if 'clickname' in v:conditions.append('std::strcmp(i.ClickName,'+json.dumps(v['clickname'])+')==0')
        if v.get('focuseffect',-1)>0:
            conditions += ['i.Focus.'+native+'=='+str(v.get(field,0)) for field,native in
                           [('focustype','Type'),('focuslevel','Level'),('focuslevel2','Level2')]]
        out.append('case '+str(v['id'])+': return '+' && '.join(conditions)+';')
    out+=['default: return false; } }','}']
    return '\n'.join(out)+'\n'


def main():
    raise SystemExit('Historical October16 generator is frozen. Use tools/dungeon_refresh_contract.py for the current release contract.')

def historical_main():
    folder=ROOT/'docs/dungeons'
    rehearsal=json.loads((folder/'rehearsal.json').read_text())
    import hashlib
    assert rehearsal['migration_sha256']==hashlib.sha256((ROOT/'server-mods/sql/20261016_dungeon_content.sql').read_text().encode()).hexdigest(), 'Rehearse the current migration first'
    assert rehearsal['schema_sha256']==hashlib.sha256((ROOT/'server-mods/sql/20261016_dungeons.sql').read_text().encode()).hexdigest(), 'Rehearse the current schema first'
    checks=schema_checks()
    results=query(';\n'.join(c['sql'] for c in checks)+';',rehearsal['database']).stdout.strip().splitlines()
    assert len(results)==len(checks)
    for c,value in zip(checks,results):c['expected']=value
    content=content_checks()
    results=query(';\n'.join(c['sql'] for c in content)+';',rehearsal['database']).stdout.strip().splitlines()
    assert len(results)==len(content)
    for c,value in zip(content,results):assert value==c['expected'],(c['label'],value,c['expected'])
    (folder/'runtime-contract.json').write_text(json.dumps(dict(schema=checks,content=content),indent=2)+'\n')
    (ROOT/'server-mods/code/common/dungeon_contract.h').write_text(render_header(checks,content,json.loads((folder/'catalog.json').read_text())['items']))
    activation=['-- Explicit activation only after matching binaries/cache and test-environment approval.',
                'DELIMITER //','CREATE PROCEDURE nightcap_dungeon_enable_20261016()','BEGIN',
                'DECLARE revision_value BIGINT UNSIGNED;',
                'DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;',
                'START TRANSACTION;',
                'SELECT revision INTO revision_value FROM nightcap_dungeon_state WHERE id=1 FOR UPDATE;',
                "IF revision_value IS NULL OR revision_value<>2026101601 OR @@group_concat_max_len<4096 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Dungeon activation revision/SQL limit mismatch'; END IF;"]
    tables=','.join(sql(t) for t in TABLES)
    activation += [
        f"IF (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND engine='InnoDB' AND table_name IN ({tables}))<>13 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Dungeon storage engine mismatch'; END IF;",
        f"IF (SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema=DATABASE() AND event_object_table IN ({tables}))<>0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unexpected dungeon storage trigger'; END IF;"]
    for c in checks+content:
        activation.append("IF NOT (("+c['sql']+") <=> "+sql(c['expected'])+") THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT="+sql('Dungeon contract mismatch: '+c['label'])+"; END IF;")
    activation += ['UPDATE nightcap_dungeon_state SET enabled=1 WHERE id=1 AND revision=2026101601;',
                   'COMMIT;','END//','DELIMITER ;','CALL nightcap_dungeon_enable_20261016();','DROP PROCEDURE nightcap_dungeon_enable_20261016;','']
    (ROOT/'server-mods/sql/20261016_dungeon_enable.sql').write_text('\n'.join(activation))
    print(f'Validated {len(checks)} schema and {len(content)} catalog checks against the isolated rehearsal.')

if __name__=='__main__':main()
