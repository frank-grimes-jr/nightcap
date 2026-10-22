"""Authenticate the exact cache-only boot change against an isolated backup restore."""
from pathlib import Path
import json,gzip,hashlib,subprocess,importlib.util,datetime
S=Path('/opt/nightcap/releases/aa-pacing-million-20261021')
spec=importlib.util.spec_from_file_location('op',S/'rollout.py')
op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op);op.initialize()
assert not op.r.state('game')['State']['Running'] and not op.r.state('gateway')['State']['Running']
clone='nightcap_aa_state_hold_20261021';scratch=clone+'.zone_state_spawns'
assert op.sql('SELECT COUNT(*) FROM '+scratch+';').strip()=='0', 'Prior scratch load uncertain; inspect'
backup=op.load(S/'evidence/activation/backup.json')
assert op.sha(Path(backup['path']))==backup['sha256']
statements=[];current=[]
with gzip.open(backup['path'],'rt') as f:
    for line in f:
        if line.startswith('INSERT INTO '+chr(96)+'zone_state_spawns'+chr(96)):
            assert not current;current=[line]
        elif current:current.append(line)
        if current and line.rstrip().endswith(';'):
            statements.append(''.join(current));current=[]
assert len(statements)==15 and not current
args=['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw',clone]
payload="SET NAMES utf8mb4; SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO'; "+''.join(statements)
p=subprocess.run(args,cwd=op.ROOT,input=payload,text=True,capture_output=True,timeout=90)
(S/'evidence/activation/private-cache-restore.log').write_text(p.stdout+p.stderr)
assert p.returncode==0,'Inspect private-cache-restore.log'
raw=op.sql('SELECT * FROM '+scratch+';').splitlines()
before=op.load(S/'evidence/activation/stopped-state.json')['player']['zone_state_spawns']
clone_image={'rows':len(raw),'sha256':hashlib.sha256('\n'.join(sorted(raw)).encode()).hexdigest()}
started=op.r.state('game')['State']['StartedAt']
stamp=datetime.datetime.fromisoformat(started.replace('Z','+00:00')).strftime('%Y-%m-%d %H:%M:%S')
fields=[v.split('\t') for v in op.sql('SHOW COLUMNS FROM zone_state_spawns;').splitlines()]
bt=chr(96);pred=[]
for name,kind,*_ in fields:
    assert name.replace('_','').isalnum()
    if kind.startswith(('float','double')):pred.append('BINARY CAST(o.'+bt+name+bt+' AS CHAR)<=>BINARY CAST(n.'+bt+name+bt+' AS CHAR)')
    else:pred.append('o.'+bt+name+bt+'<=>n.'+bt+name+bt)
mismatch=op.sql('SELECT COUNT(*) FROM '+scratch+' o JOIN peq.zone_state_spawns n ON n.id=o.id WHERE NOT ('+' AND '.join('('+v+')' for v in pred)+');').strip()
added=op.sql('SELECT COUNT(*) FROM peq.zone_state_spawns n LEFT JOIN '+scratch+' o ON n.id=o.id WHERE o.id IS NULL;').strip()
removed=op.sql('SELECT o.zone_id,o.instance_id,o.is_corpse,o.is_zone,COUNT(*),MIN(o.created_at),MAX(o.created_at) FROM '+scratch+' o LEFT JOIN peq.zone_state_spawns n ON n.id=o.id WHERE n.id IS NULL GROUP BY o.zone_id,o.instance_id,o.is_corpse,o.is_zone;')
unexpected=op.sql("SELECT COUNT(*) FROM "+scratch+" o LEFT JOIN peq.zone_state_spawns n ON n.id=o.id WHERE n.id IS NULL AND NOT(o.created_at<DATE_SUB('"+stamp+"',INTERVAL 7 DAY));").strip()
result={'original':before,'scratch_restore':clone_image,'exact_restore_matches':before==clone_image,'surviving_field_differences':int(mismatch),'added_rows':int(added),'removed_groups':removed,'removed_nonexpired':int(unexpected),'first_started_at':started,'rule':op.sql("SELECT rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name='Zone:StateSaveClearDays';").strip(),'scratch_schema':clone}
(S/'evidence/activation/cache-diagnosis.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
