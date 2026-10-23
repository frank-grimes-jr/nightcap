"""Read-only public reward/spell preimages and aggregate reserved-ID audit."""
import argparse
import json
from pathlib import Path
import subprocess
from dungeon_migration import ITEM_REFERENCES

REMOTE = r'''
import datetime,json,subprocess
from pathlib import Path
def query(sql):
    p=subprocess.run(['docker','compose','exec','-T','db','mariadb',
        '--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw',
        '--skip-column-names','--default-character-set=utf8mb4','peq'],
        cwd='/opt/nightcap/deploy/production',input='START TRANSACTION READ ONLY;\n'+sql+';\nROLLBACK;\n',
        text=True,capture_output=True,check=True,timeout=120)
    return p.stdout.splitlines()
def rows(table,where):
    columns=[v.split('\t')[0] for v in query('SHOW COLUMNS FROM `'+table+'`')]
    expr=','.join("'"+c+"',`"+c+'`' for c in columns)
    return [json.loads(v) for v in query('SELECT JSON_OBJECT('+expr+') FROM `'+table+'` WHERE '+where)]
data={'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'scope':'Production read-only public definitions and aggregate collisions; no player records'}
data['items']=rows('items','id BETWEEN 960000 AND 960413')
data['spells']=rows('spells_new',"name IN ('See Invisible','Invisibility','Levitate')")
data['click_examples']=query('SELECT id,Name,clickeffect,clicktype,clicklevel,clicklevel2,casttime,casttime_,maxcharges,recastdelay,recasttype FROM items WHERE clickeffect IN (42,80,261) LIMIT 15')
data['recast_groups']=query('SELECT recasttype,COUNT(*) FROM items WHERE recasttype BETWEEN 1 AND 100 GROUP BY recasttype')
data['timers']=query('SELECT type,COUNT(*) FROM timers WHERE type BETWEEN 100 AND 200 GROUP BY type')
data['item_recast']=query('SELECT recast_type,COUNT(*) FROM character_item_recast WHERE recast_type BETWEEN 91 AND 93 GROUP BY recast_type')
data['serialized_collisions']={t:int(query("SELECT COUNT(*) FROM "+t+" WHERE payload REGEXP '(^|[^0-9])960(3[3-9][0-9]|40[0-9]|41[0-3])([^0-9]|$)'")[0]) for t in ('nightcap_dungeon_checkpoints','nightcap_dungeon_corpses')}
data['collisions']={}
for table,columns in references.items():
    for column in columns:
        exists=query("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='"+table+"' AND column_name='"+column+"'")[0]
        if exists!='0':
            data['collisions'][table+'.'+column]=int(query('SELECT COUNT(*) FROM `'+table+'` WHERE `'+column+'` BETWEEN 960330 AND 960413')[0])
print(json.dumps(data))
'''

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    refs={**ITEM_REFERENCES,'nightcap_dungeon_members':['reward_item'],'nightcap_dungeon_loot':['item_id']}
    p=subprocess.run(['ssh','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes',
        '-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -'],
        input='references='+repr(refs)+'\n'+REMOTE,text=True,encoding='utf-8',capture_output=True,check=True)
    data=json.loads(p.stdout)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in data.items() if k not in ('items','spells')}))
    print(json.dumps({'items':len(data['items']),'spells':[{k:r[k] for k in ('id','name','targettype','effectid1','effect_base_value1')} for r in data['spells']]}))

if __name__=='__main__':main()
