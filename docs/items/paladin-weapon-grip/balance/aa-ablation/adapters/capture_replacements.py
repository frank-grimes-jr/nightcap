"""Bounded read-only public weapon/reward comparison; no player data."""
from pathlib import Path
import subprocess,json,base64,gzip,hashlib
HERE=Path(__file__).resolve().parent
REMOTE=r'''
import subprocess,json,gzip,base64,datetime
root='/opt/nightcap/deploy/production'
def q(statement):
 r=subprocess.run(['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--quick','--skip-column-names','--default-character-set=utf8mb4','peq'],cwd=root,input='SET TRANSACTION READ ONLY; START TRANSACTION WITH CONSISTENT SNAPSHOT; '+statement+'; COMMIT;',capture_output=True,text=True,timeout=90)
 if r.returncode:raise RuntimeError(r.stderr[-700:])
 return [json.loads(v) for v in r.stdout.splitlines()]
cols=['id','Name','itemtype','classes','damage','delay','reqlevel','reclevel','accuracy','avoidance','shielding','ac','hp','mana','astr','awis','heroic_str','heroic_wis','healamt','spelldmg','proceffect','proclevel2','clickeffect']
selected=q("SELECT JSON_ARRAY(id) FROM items WHERE id<200000 AND (classes & 4)<>0 AND itemtype IN (0,1) AND Name REGEXP 'Great Sword|Ssraeshza|Bloodfrenzy|Carnage|Great Blade|Blade of War|Seru|Shissar|Stoneblade' ORDER BY id LIMIT 70")
ids=sorted(set([10099,810099,605504,611050]+[v for r in selected for v in [r[0],r[0]+600000]]))
items=q('SELECT JSON_ARRAY('+','.join('`'+c+'`' for c in cols)+') FROM items WHERE id IN ('+','.join(map(str,ids))+') ORDER BY id')
locations=q('SELECT DISTINCT JSON_ARRAY(lde.item_id,n.name,s.zone,z.expansion) FROM lootdrop_entries lde JOIN loottable_entries le ON le.lootdrop_id=lde.lootdrop_id JOIN npc_types n ON n.loottable_id=le.loottable_id JOIN spawnentry se ON se.npcID=n.id JOIN spawn2 s ON s.spawngroupID=se.spawngroupID LEFT JOIN zone z ON z.short_name=s.zone AND z.version=0 WHERE lde.item_id IN ('+','.join(str(r[0]) for r in selected)+') LIMIT 300') if selected else []
out={'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Selected public weapon definitions and static spawn/drop locations only; no acquisition-time telemetry','columns':cols,'items':items,'drop_locations':locations}
print(base64.b64encode(gzip.compress(json.dumps(out).encode(),mtime=0)).decode())
'''
dest=HERE/'public-replacement-reference.json'
if dest.exists():raise FileExistsError(dest)
p=subprocess.run(['ssh','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo','-n','python3','-'],input=REMOTE,capture_output=True,text=True,timeout=300)
if p.returncode:raise RuntimeError(p.stderr[-1200:])
data=json.loads(gzip.decompress(base64.b64decode(p.stdout)));dest.write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({'captured_at':data['captured_at'],'items':len(data['items']),'locations':len(data['drop_locations']),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'production_changed':False}))
