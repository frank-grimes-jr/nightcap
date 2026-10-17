"""Read-only production AA review; writes the received evidence locally only."""
import gzip
import hashlib
import json
import subprocess
from pathlib import Path

REMOTE = r'''
import datetime,json,subprocess,sys,gzip
DB=['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--skip-column-names','peq']
ROOT='/opt/nightcap/deploy/production'
def sql(q):
 return subprocess.check_output(DB,input=q,cwd=ROOT,text=True)
queries=[]
for table in ['aa_ability','aa_ranks','aa_rank_effects','aa_rank_prereqs']:
 cols=[x.split('\t')[0] for x in sql('SHOW COLUMNS FROM '+table+';').splitlines()]
 pairs=','.join("'%s',`%s`"%(c,c) for c in cols)
 queries.append("SELECT '%s',JSON_OBJECT(%s) FROM %s;"%(table,pairs,table))
queries += [
 "SELECT 'palwar',JSON_OBJECT('name',c.name,'level',c.level,'class',c.class,'race',c.race,'exp',c.exp,'aa_exp',c.aa_exp,'aa_points',c.aa_points,'aa_points_spent',c.aa_points_spent,'allocation',c.e_percent_to_aa,'time_played',c.time_played,'zone_id',c.zone_id,'class2',m.class2,'class3',m.class3) FROM character_data c LEFT JOIN character_multiclass m ON m.character_id=c.id WHERE c.name='Palwar';",
 "SELECT 'purchases',JSON_OBJECT('aa_id',aa_id,'aa_value',aa_value,'charges',charges) FROM character_alternate_abilities WHERE id=(SELECT id FROM character_data WHERE name='Palwar') ORDER BY aa_id;",
 "SELECT 'rules',JSON_OBJECT('ruleset',ruleset_id,'name',rule_name,'value',rule_value) FROM rule_values WHERE rule_name LIKE 'AA:%' OR rule_name LIKE '%Exp%' OR rule_name IN ('Character:UseRaceClassExpBonuses','Character:UseXPConScaling','Character:GreenModifier','Character:LightBlueModifier','Character:BlueModifier','Character:WhiteModifier','Character:YellowModifier','Character:RedModifier','Zone:HotZoneBonus');",
 "SELECT 'zone',JSON_OBJECT('short_name',short_name,'version',version,'ruleset',ruleset,'zem',zone_exp_multiplier,'hotzone',hotzone) FROM zone WHERE zoneidnumber=(SELECT zone_id FROM character_data WHERE name='Palwar');"
]
query='SET SESSION max_statement_time=30; START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY;\n'+'\n'.join(queries)+'\nROLLBACK;'
out={'environment':'production','captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'queries':query,'tables':{}}
for line in sql(query).splitlines():
 table,row=line.split('\t',1)
 out['tables'].setdefault(table,[]).append(json.loads(row))
out['services']=subprocess.check_output(['docker','compose','ps','--format','json'],cwd=ROOT,text=True)
sys.stdout.buffer.write(gzip.compress(json.dumps(out,separators=(',',':')).encode(),mtime=0))
'''

if __name__ == '__main__':
    cmd=['C:/Windows/System32/OpenSSH/ssh.exe','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -']
    p=subprocess.run(cmd,input=REMOTE.encode(),capture_output=True,timeout=90)
    if p.returncode:
        raise SystemExit(p.stderr.decode(errors='replace'))
    data=json.loads(gzip.decompress(p.stdout))
    target=Path(__file__).parent/'production-snapshot.json.gz'
    target.write_bytes(p.stdout)
    print(json.dumps({'path':str(target),'captured_utc':data['captured_utc'],'sha256':hashlib.sha256(p.stdout).hexdigest(),'counts':{k:len(v) for k,v in data['tables'].items()},'palwar':data['tables']['palwar']},indent=2))
