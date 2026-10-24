"""Generate the approved Classic hunt catalog and guarded, offline migrations."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
QUALITY=[6000,3000,800,200]
FAMILY_CHANCE=50
ARMOR_MASK=921732
REVISION=2026100901
# Reviewed signal-only Cazic-Thule follower script; changed bytes fail closed.
COMBAT_QUEST_HASHES={'77429b3df1039c4a16ecaa2a53f051a8b69f555186140886cdc1ecc485f57297'}
SLOTS={'Ear':18,'Head':4,'Face':8,'Neck':32,'Shoulders':64,'Arms':128,
       'Back':256,'Wrist':1536,'Range':2048,'Hands':4096,'Finger':98304,
       'Chest':131072,'Legs':262144,'Feet':524288,'Waist':1048576}
STAT={'HP':'hp','Mana':'mana','AC':'ac','Spell damage':'spelldmg','Healing':'healamt','ATK':'attack'}
STAT.update({x:'a'+x.lower() for x in ('STR','STA','AGI','DEX','WIS','INT','CHA')})
STAT.update({x:x.lower() for x in ('MR','FR','CR','PR','DR')})
STAT.update({'h'+x:'heroic_'+x.lower() for x in ('STR','STA','AGI','DEX','WIS','INT','CHA','MR','FR','CR','PR','DR')})

def items(catalog):
    result=[]
    for index,d in enumerate(catalog['details']):
        if d['status'] not in ('Hunt draft','Access check'): continue
        aug=d['kind']=='Augment'
        v=dict(id=940000+index,Name=d['item'],lore=d['item'],itemclass=0,itemtype=54 if aug else 10,
               slots=ARMOR_MASK if aug else SLOTS[d['slot']],classes=65535,races=65535,deity=0,
               reqlevel=d['req'],reclevel=d['req'],nodrop=0 if aug else 1,norent=1,
               attuneable=0 if aug else 1,stackable=0,stacksize=1,loregroup=0,
               weight=0 if aug else 5,size=1,price=0,sellrate=0,nopet=1,
               augtype=2097152 if aug else 0,augrestrict=0,augdistiller=0,icon=517 if aug else 500,
               clickeffect=-1,worneffect=-1,focuseffect=-1,proceffect=-1,scrolleffect=-1,bardeffect=-1)
        for key in STAT.values(): v[key]=0
        for key,value in d['stats'].items(): v[STAT[key]]=value
        if not aug and v['slots'] & ARMOR_MASK:
            assert not v['slots'] & ~ARMOR_MASK
            v.update(augslot1type=22,augslot1visible=1)
        result.append(dict(id=v['id'],zone=d['code'],kind=d['kind'],tier=d['tier_index'],values=v))
    return result

def eligible(z,n,quests,reviewed=frozenset()):
    if z['status']!='Hunt draft' or n['zone'].lower()!=z['short_name']: return False
    if int(n['version']) or int(n['level'])<z['npc'] or int(n['npcID'])>=900000: return False
    if int(n['merchant_id']) or int(n['class'])>16: return False
    if int(n['min_expansion'])>0 or int(n['max_expansion']) < -1: return False
    if any(n[k] not in ('','NULL') for k in ('content_flags','content_flags_disabled')): return False
    if int(n['respawntime'])<60 or int(n['chance'])<=0: return False
    name=n['name'].lstrip('#')
    generic = name[:1].islower() and '_' in name
    solusek = z['short_name']=='soldunga' and name.startswith('Solusek_')
    if not (generic or solusek): return False
    if any(word in name.lower() for word in ('guard','merchant','trainer','banker','soulbinder','priest_of','druid','ranger','rescued','prisoner','waypoint','invisible','trigger','controller')): return False
    if any(f'{folder}/{stem}{suffix}' in quests and f'{folder}/{stem}{suffix}' not in reviewed for folder in (z['short_name'],'global')
           for stem in (n['npcID'],name) for suffix in ('.pl','.lua')): return False
    # Invulnerability, immunity to aggression and noncombat bodies are never farms.
    abilities={int(s.split(',')[0]) for s in n['special_abilities'].split('^') if s and s.split(',')[0].isdigit()}
    if abilities & {19,20,24,35} or int(n['bodytype']) in (11,60,66,67): return False
    if z['short_name']=='highkeep' and not any(x in name.lower() for x in ('goblin','pickclaw')): return False
    if z['short_name']=='kithicor' and int(n['bodytype']) not in (3,12): return False
    if z['short_name']=='unrest' and int(n['bodytype']) not in (3,12): return False
    return True

def socket_change(row,classic_ids):
    id=int(row['id']); slots=int(row['slots'])
    if id%200000 not in classic_ids or not slots or slots & ~ARMOR_MASK: return None
    if int(row['augtype']) or int(row['reqlevel'])>50 or int(row['reclevel'])>50: return None
    types=[int(row[f'augslot{i}type']) for i in range(1,7)]
    if 22 in types or 0 not in types: return None
    return dict(id=id,socket=types.index(0)+1,before=row)

def sql(value):
    if isinstance(value,str): return "X'"+value.encode().hex()+"'"
    return str(value)

def insert(table,row):
    return 'INSERT INTO '+table+' ('+','.join('`'+k+'`' for k in row)+') VALUES ('+','.join(sql(v) for v in row.values())+');'

def generate(catalog,audit,out):
    if audit['reserved_ids'] or audit['feature_tables']: raise ValueError('Reserved IDs or feature tables already exist: capture/reconcile the installed release instead.')
    if not audit['quest_files']: raise ValueError('Quest source audit is empty')
    data=items(catalog); byzone={z['short_name']:z for z in catalog['zones']}
    quests=set(audit['quest_files']); selected={}
    reviewed={path for path,digest in audit.get('quest_hashes',{}).items()
              if path.startswith('fearplane/') and digest in COMBAT_QUEST_HASHES}
    for n in audit['spawns']:
        z=byzone[n['zone'].lower()]
        if eligible(z,n,quests,reviewed): selected[(z['zoneidnumber'],int(n['id']),int(n['npcID']))]=n
    classic={int(i['item_id']) for i in audit['classic_loot']}
    sockets=[x for r in audit['socket_candidates'] if (x:=socket_change(r,classic))]
    zones=[]
    for z in catalog['zones']:
        family=[i for i in data if i['zone']==z['short_name'] and i['tier']==0]
        if not family: continue
        count=sum(k[0]==z['zoneidnumber'] for k in selected)
        zones.append(dict(zone_id=z['zoneidnumber'],augment_base=family[0]['id'],gear_base=family[1]['id'],
                          min_level=z['npc'],night_only=int(z['short_name']=='kithicor'),enabled=int(count>0)))
    out.mkdir(parents=True,exist_ok=True)
    (out/'items.json').write_text(json.dumps(data,indent=2)+'\n')
    (out/'sources.json').write_text(json.dumps([{'zone_id':k[0],'spawn_id':k[1],'npc_id':k[2],'name':n['name'],
        'level':int(n['level']),'zone':n['zone'],'respawntime':int(n['respawntime'])} for k,n in sorted(selected.items())],indent=2)+'\n')
    (out/'socket-preimages.json').write_text(json.dumps(sockets,indent=2)+'\n')
    counts=Counter(k[0] for k in selected)
    report=[dict(zone=z['short_name'],status=z['status'],eligible_sources=counts[z['zoneidnumber']],
                 enabled=counts[z['zoneidnumber']]>0) for z in catalog['zones']]
    (out/'audit.json').write_text(json.dumps(dict(revision=REVISION,items=len(data),sockets=len(sockets),
        source_sha256=hashlib.sha256(json.dumps(audit,sort_keys=True).encode()).hexdigest(),zones=report),indent=2)+'\n')
    ddl='''-- Offline installation only; stop writers, back up and recapture target first.
CREATE TABLE IF NOT EXISTS nightcap_zone_hunt_state (id TINYINT PRIMARY KEY, revision BIGINT NOT NULL, enabled TINYINT NOT NULL DEFAULT 0) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS nightcap_zone_hunt_zones (zone_id INT PRIMARY KEY, augment_base INT NOT NULL, gear_base INT NOT NULL, min_level INT NOT NULL, night_only TINYINT NOT NULL, enabled TINYINT NOT NULL) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS nightcap_zone_hunt_sources (zone_id INT NOT NULL, spawn_id INT NOT NULL, npc_id INT NOT NULL, PRIMARY KEY(zone_id,spawn_id,npc_id)) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS nightcap_zone_hunt_forges (request_id CHAR(36) PRIMARY KEY, character_id INT NOT NULL, input_id INT NOT NULL, output_id INT NOT NULL, inventory_before TEXT NOT NULL, inventory_after TEXT NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB;
DELIMITER //
CREATE PROCEDURE nightcap_zone_hunt_install_20261009()
BEGIN
 DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
 START TRANSACTION;
 IF (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='items' AND ENGINE='InnoDB')<>1 OR EXISTS (SELECT 1 FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE='items') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Item table must be untriggered InnoDB'; END IF;
 IF EXISTS (SELECT 1 FROM nightcap_zone_hunt_state) OR EXISTS (SELECT 1 FROM items WHERE id BETWEEN 940000 AND 940999) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Zone hunt ownership/ID collision'; END IF;
'''
    stmts=[ddl,insert('nightcap_zone_hunt_state',dict(id=1,revision=REVISION,enabled=0))]
    for i in data: stmts.append(insert('items',i['values']))
    for z in zones: stmts.append(insert('nightcap_zone_hunt_zones',z))
    for (zone,spawn,npc) in sorted(selected): stmts.append(insert('nightcap_zone_hunt_sources',dict(zone_id=zone,spawn_id=spawn,npc_id=npc)))
    for change in sockets:
        r=change['before']; socket=change['socket']
        predicate=' AND '.join(('BINARY ' if k=='Name' else '')+'`'+k+'`='+sql(v if k=='Name' else int(v)) for k,v in r.items())
        stmts.append(f'UPDATE items SET augslot{socket}type=22,augslot{socket}visible=1 WHERE {predicate};')
        stmts.append("IF ROW_COUNT()<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Socket preimage drift'; END IF;")
    stmts+=['COMMIT; END//','DELIMITER ;','CALL nightcap_zone_hunt_install_20261009();','DROP PROCEDURE nightcap_zone_hunt_install_20261009;']
    (out/'install.sql').write_text('\n'.join(stmts)+'\n')
    (out/'activate.sql').write_text(f'-- Matching binary and shared item cache required; reload zones after changing this flag.\nUPDATE nightcap_zone_hunt_state SET enabled=1 WHERE id=1 AND revision={REVISION};\n')
    (out/'rollback.sql').write_text('-- Safe after player activity: retain definitions, sockets, ownership and forge receipts.\nUPDATE nightcap_zone_hunt_state SET enabled=0 WHERE id=1;\n-- Reload zones with the current receipt-capable binary. Never restore old player rows.\n')
    header=['#pragma once','#include <cstdint>','namespace NightcapHunt {','inline bool IsAugment(uint32_t id) { if ((id>=961000 && id<=961003) || (id>=961020 && id<=961023)) { return true; } switch (id) {']
    header += [f'case {i["id"]}:' for i in data if i['kind']=='Augment']
    header += ['return true; default: return false; } }','inline uint32_t NextTier(uint32_t id) { if ((id>=961000 && id<961003) || (id>=961020 && id<961023)) { return id+1; } switch (id) {']
    header += [f'case {i["id"]}: return {i["id"]+1};' for i in data if i['tier']<3]
    header += ['default: return 0; } }','inline bool IsReward(uint32_t id) { if ((id>=961000 && id<=961003) || (id>=961020 && id<=961023)) { return true; } switch (id) {']
    header += [f'case {i["id"]}:' for i in data]
    header += ['return true; default: return false; } }','}']
    h=ROOT/'server-mods/code/common/zone_hunt_catalog.h';h.parent.mkdir(parents=True,exist_ok=True);h.write_text('\n'.join(header)+'\n')
    print(json.dumps(dict(items=len(data),sources=len(selected),sockets=len(sockets),enabled_zones=sum(z['enabled'] for z in zones))))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--audit',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();generate(json.loads((ROOT/'docs/releases/zone-loot-20261009/approved-catalog.json').read_text()),json.loads(a.audit.read_text()),a.output)
