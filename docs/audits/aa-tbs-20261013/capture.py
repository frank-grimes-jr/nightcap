"""Read-only AA content capture. No player/account identities or SQL mutations."""
import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REMOTE = r'''
import datetime, gzip, json, subprocess, sys
DB = ['docker','compose','exec','-T','db','mariadb',
      '--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw',
      '--skip-column-names','peq']
ROOT = '/opt/nightcap/deploy/production'
def sql(q):
    return subprocess.check_output(DB, input=q, cwd=ROOT, text=True)
tables = ['aa_ability','aa_ranks','aa_rank_effects','aa_rank_prereqs']
queries = []
for table in tables:
    cols = [line.split('\t')[0] for line in sql('SHOW COLUMNS FROM '+table+';').splitlines()]
    pairs = ','.join("'%s',`%s`" % (c,c) for c in cols)
    queries.append("SELECT '%s',JSON_OBJECT(%s) FROM %s;" % (table,pairs,table))
cols = ['id','name','mana','cast_time','recast_time','recovery_time','buffduration',
        'buffdurationformula','targettype','resisttype','RecourseLink','EndurCost',
        'EndurUpkeep','numhits','numhitstype','max_dist','aoerange','range']
available = {line.split('\t')[0] for line in sql('SHOW COLUMNS FROM spells_new;').splitlines()}
cols += [p+str(n) for p in ('effectid','effect_base_value','effect_limit_value','max','formula') for n in range(1,13)]
cols = [c for c in cols if c in available]
queries.append("SELECT 'spells',JSON_OBJECT("+','.join("'%s',`%s`" % (c,c) for c in cols)+") FROM spells_new;")
queries.append("SELECT 'rules',JSON_OBJECT('ruleset',ruleset_id,'name',rule_name,'value',rule_value) FROM rule_values WHERE rule_name LIKE 'AA:%' OR rule_name LIKE 'Expansion:%' OR rule_name IN ('Character:MaxLevel','Character:AAExpMinLevel','Character:ExpMultiplier','Character:AAExpMultiplier','Character:FinalExpMultiplier','Character:ItemSpellDmgCap','Character:ItemHealAmtCap','World:ExpansionSettings','Spells:ItemExtraSpellAmtCalcAsPercent');")
queries.append("SELECT 'purchases_aggregate',JSON_OBJECT('first_rank_id',aa_id,'rank_count',aa_value,'charges',charges,'rows',COUNT(*)) FROM character_alternate_abilities GROUP BY aa_id,aa_value,charges;")
queries.append("SELECT 'rulesets',JSON_OBJECT('id',ruleset_id,'name',name) FROM rule_sets;")
queries.append("SELECT 'zone_rulesets',JSON_OBJECT('ruleset',ruleset,'zones',COUNT(*)) FROM zone GROUP BY ruleset;")
query = 'SET SESSION max_statement_time=30; START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY;\n'+'\n'.join(queries)+'\nROLLBACK;'
out = {'environment':'production','captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'queries':query,'tables':{}}
for line in sql(query).splitlines():
    table, row = line.split('\t',1)
    out['tables'].setdefault(table,[]).append(json.loads(row))
sys.stdout.buffer.write(gzip.compress(json.dumps(out, separators=(',',':')).encode(),mtime=0))
'''

if __name__ == '__main__':
    cmd = ['ssh','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes',
           '-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes',
           'ubuntu@135.148.47.202','sudo -n python3 -']
    result = subprocess.run(cmd,input=REMOTE.encode(),capture_output=True,check=True,timeout=180)
    data = json.loads(gzip.decompress(result.stdout))
    target = HERE/'production-snapshot.json.gz'
    target.write_bytes(result.stdout)
    print(json.dumps({'path':str(target),'sha256':hashlib.sha256(result.stdout).hexdigest(),
                      'captured_at':data['captured_at'],
                      'counts':{k:len(v) for k,v in data['tables'].items()}},indent=2))
