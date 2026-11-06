"""Read-only production augment content capture; excludes player data and secrets."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
QUERIES = {
    'item_schema': 'SHOW CREATE TABLE items',
    'zone_schema': 'SHOW CREATE TABLE nightcap_zone_hunt_zones',
    'spell_schema': 'SHOW CREATE TABLE spells_new',
    'rules': "SELECT ruleset_id,rule_name,rule_value FROM rule_values WHERE rule_name IN ('Spells:AdditiveBonusWornType','Character:ItemAvoidanceCap','Character:ItemShieldingCap','Character:ItemSpellDmgCap','Character:ItemHealAmtCap','Character:ItemSpellShieldingCap')",
    'zones': 'SELECT z.*,q.short_name,q.long_name FROM nightcap_zone_hunt_zones z JOIN zone q ON q.zoneidnumber=z.zone_id AND q.version=0 ORDER BY z.zone_id',
    'state': 'SELECT * FROM nightcap_zone_hunt_state',
    'items': 'SELECT * FROM items WHERE (id BETWEEN 940000 AND 940999) OR id BETWEEN 961000 AND 961003 OR id BETWEEN 961020 AND 961023 ORDER BY id',
    'effects': 'SELECT id,name,effectid1,effect_base_value1,effect_limit_value1,max1,effectid2,effect_base_value2,effect_limit_value2,max2,effectid3,effect_base_value3,effect_limit_value3,max3 FROM spells_new WHERE id IN (SELECT focuseffect FROM items WHERE id BETWEEN 940000 AND 940999) OR name LIKE \'%Faerune%\' OR name LIKE \'%Improved Dodge%\' OR name LIKE \'%Spell Haste%\' OR name LIKE \'%Mana Preservation%\' ORDER BY id',
    'spawns': 'SELECT DISTINCT z.zone_id,s.id AS spawn_id,n.id AS npc_id,n.name,n.level,n.class,n.merchant_id,n.bodytype,n.special_abilities FROM nightcap_zone_hunt_zones z JOIN zone q ON q.zoneidnumber=z.zone_id AND q.version=0 JOIN spawn2 s ON s.zone=q.short_name AND s.version=0 JOIN spawnentry e ON e.spawngroupID=s.spawngroupID JOIN npc_types n ON n.id=e.npcID ORDER BY z.zone_id,s.id,n.id',
    'sources': 'SELECT * FROM nightcap_zone_hunt_sources ORDER BY zone_id,spawn_id,npc_id',
}
QUERIES['effects'] = "SELECT * FROM spells_new WHERE id IN (2339,2340,2341,2342,2343,2344,3660,3889,4301,4302,4303,4304,4305,4306) OR effectid1=320 OR effectid2=320 OR effectid3=320 ORDER BY id"
REMOTE = '''import json,subprocess,datetime
queries=QUERIES
out={'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':'production'}
def decode(value):
 special={'0':chr(0),'n':chr(10),'r':chr(13),'t':chr(9),'b':chr(8),'Z':chr(26),chr(92):chr(92)}
 result=''; i=0
 while i<len(value):
  if ord(value[i])==92 and i+1<len(value) and value[i+1] in special:
   result+=special[value[i+1]]; i+=2
  else: result+=value[i]; i+=1
 return result
for key,sql in queries.items():
 p=subprocess.run(['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','peq'],cwd='/opt/nightcap/deploy/production',input='START TRANSACTION READ ONLY; '+sql+'; COMMIT;',text=True,capture_output=True)
 if p.returncode: raise RuntimeError(key+': '+p.stderr)
 lines=p.stdout.splitlines(); columns=lines[0].split('\\t') if lines else []
 out[key]=[dict(zip(columns,map(decode,line.split('\\t')))) for line in lines[1:]]
print(json.dumps(out))
'''.replace('QUERIES', repr(QUERIES))

if __name__ == '__main__':
    result = subprocess.run([r'C:\Windows\System32\OpenSSH\ssh.exe', '-i',
        r'C:\Users\verre\.ssh\nightcap_ovh', '-o', 'BatchMode=yes', '-o',
        'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=yes',
        'ubuntu@135.148.47.202', 'sudo -n python3 -'], input=REMOTE,
        text=True, capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr)
    data = json.loads(result.stdout)
    dest = ROOT / 'docs/audits/augments-20261106/production.json'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, indent=2) + '\n')
    print({k: len(v) for k, v in data.items() if isinstance(v, list)})
