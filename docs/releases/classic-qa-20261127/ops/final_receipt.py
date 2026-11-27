"""Read the production terminal receipts and confirm Cazic, Recall, and open admission."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

from capture import HERE, SSH

STAGE=Path('E:/EQ_Local_Dev/artifacts/classic-qa-20261127/ops/production')
manifest=hashlib.sha256((STAGE/'manifest.json').read_bytes()).hexdigest()
remote='/opt/nightcap/releases/classic-qa-20261127-'+manifest[:12]


def call(*args,data=None):
    return subprocess.check_output([*SSH,shlex.join(['sudo','-n',*args])],input=data,timeout=180)


def receipt(name):
    return json.loads(call('cat',remote+'/'+name+'.json'))


result=receipt('activation-complete')
result['backup_sha256']=receipt('activation-backup')['sha256']
m=json.loads((STAGE/'manifest.json').read_bytes())
assert result['admission_open'] and result['binaries']['zone']==m['zone']
assert result['image']==receipt('prepared')['image']
assert call('docker','inspect','--format','{{.State.Running}}','nightcap-production-gateway-1').strip()==b'true'
sql=b"""SELECT level,hp,mindmg,maxdmg,attack_delay,hp_regen_rate,AC,ATK,Accuracy
FROM npc_types WHERE id=72003 AND name='Cazic_Thule' AND class=5 AND npc_spells_id=116 AND loottable_id=291 AND hp_regen_per_second=0;
SELECT classes FROM aa_ability WHERE id=2220 AND name='Ancient Attunement' AND first_rank_id=22200 AND type=1 AND enabled=1;"""
rows=call('docker','exec','-i','nightcap-production-db-1','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','-NB','peq',data=sql).decode().splitlines()
assert rows==['55\t24000\t85\t218\t32\t13\t397\t0\t0','131071']
result.update(main='58e14d9b15582c455c48571c15f4d76ed16bb970',recall_family=2220,recall_classes=131071,
              cazic={'level':55,'hp':24000,'mindmg':85,'maxdmg':218,'attack_delay':32,'hp_regen_rate':13,'AC':397,'ATK':0,'Accuracy':0},
              previous_image=m['base_image'],production_stage=remote.rsplit('/',1)[-1],rollback='staged and preimages verified')
(HERE/'production-verified.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

