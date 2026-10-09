"""Apply the owner-authorized helmet appearance with fresh stopped-server evidence."""
import base64, copy, fcntl, gzip, hashlib, json, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path('/opt/nightcap/deploy/production')
OUT = Path('/opt/nightcap/backups/winged-helmet-20261004/camil-live')
DB = ['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--skip-column-names','peq']
payload = json.loads(sys.stdin.read())
SCOPES = {'npc_types':'id=999521', 'npc_types_tint':'id=999521',
          'spawn2':'spawngroupID=999521', 'spawnentry':'npcID=999521',
          'spawngroup':'id=999521', 'items':'id=990500',
          'zone_state_spawns':'zone_id=22 AND instance_id=0 AND npc_id=999521 AND is_corpse=0'}

def run(args, **kw):
    return subprocess.run(args, cwd=ROOT, check=True, timeout=150, **kw)

def dc(*args):
    return run(['docker','compose',*args], text=True, capture_output=True).stdout

def sql(statement):
    return run(DB, input=statement, text=True, capture_output=True).stdout

def capture():
    result = {}
    for table, scope in SCOPES.items():
        columns = [line.split('\t')[0] for line in sql(f'SHOW COLUMNS FROM `{table}`;').splitlines()]
        fields = ','.join(f"'{name}',CAST(`{name}` AS CHAR)" for name in columns)
        result[table] = [json.loads(line) for line in sql(f'SELECT JSON_OBJECT({fields}) FROM `{table}` WHERE {scope};').splitlines()]
    return result

def health():
    for attempt in range(45):
        statuses = [json.loads(line) for line in dc('ps','--format','json').splitlines()]
        if any(s['Service']=='game' and s.get('Health')=='healthy' for s in statuses):
            return
        time.sleep(2)
    raise RuntimeError('Game did not become healthy; gateway remains closed')

def probe():
    return json.loads(dc('exec','-T','game','python3','-c',payload['probe']))

def verify_runtime(before_runtime):
    after_runtime = probe()
    assert after_runtime['hashes']==before_runtime['hashes'], 'Runtime binary drift'
    assert min(int(p['start']) for p in after_runtime['processes'])>max(int(p['start']) for p in before_runtime['processes']), 'Old world/zone process survived'
    cache_size = int(dc('exec','-T','game','python3','-c',"from pathlib import Path; p=Path('/srv/nightcap/shared/items'); assert b'Winged Helm of the Dawn' in p.read_bytes(); print(p.stat().st_size)"))
    return after_runtime, cache_size

with (ROOT/'.deployment.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    manifest = json.loads(base64.b64decode(json.loads((ROOT/'data/public/channel.json').read_bytes())['manifest']))
    assert manifest['release']==2026100401, 'Publish the matching client before Camil activation'
    before_runtime = probe()
    assert before_runtime['hashes']==payload['binary_hashes']
    OUT.mkdir(mode=0o700, exist_ok=False)
    for name in ('forward','rollback'):
        (OUT/(name+'.sql')).write_text(payload[name])
    dc('stop','gateway')
    stopped = False
    try:
        dc('stop','game')
        stopped = True
        cid = dc('ps','-aq','game').strip()
        assert not json.loads(run(['docker','inspect',cid], text=True, capture_output=True).stdout)[0]['State']['Running']
        before = capture()
        assert before['npc_types']==payload['expected_npc'], 'Camil row drift'
        assert len(before['items'])==1 and before['items'][0]['material']=='90'
        assert len(before['spawn2'])==1 and before['spawn2'][0]['zone']=='ecommons'
        assert all(r['npc_id']=='999521' for r in before['zone_state_spawns'])
        for row in before['zone_state_spawns']:
            loot = json.loads(row['loot_data']) if row['loot_data'] else {}
            assert not loot.get('entries') and not loot.get('nightcap_npc_loot_v1',{}).get('items'), 'Unexpected Camil equipment cache'
        (OUT/'before.json').write_text(json.dumps(before,indent=2)+'\n')
        dump = ['docker','compose','exec','-T','db','mariadb-dump','--defaults-extra-file=/run/secrets/db_backup_config','--single-transaction','--routines','--triggers','--events','--hex-blob','peq']
        raw_backup = OUT/'peq-before.sql'
        with raw_backup.open('xb') as target, (OUT/'dump-errors.txt').open('wb') as errors:
            subprocess.run(dump,cwd=ROOT,stdout=target,stderr=errors,check=True,timeout=90)
        with raw_backup.open('rb') as source, gzip.open(OUT/'peq-before.sql.gz','xb') as zipped:
            shutil.copyfileobj(source,zipped)
        with gzip.open(OUT/'peq-before.sql.gz','rb') as backup:
            size = sum(len(block) for block in iter(lambda:backup.read(1024*1024),b''))
        assert size>100_000_000
        assert size==raw_backup.stat().st_size
        raw_backup.unlink()
        assert payload['forward'].count('COMMIT;')==1
        sql(payload['forward'].replace('COMMIT;','ROLLBACK;'))
        assert capture()==before, 'Rehearsal changed state'
        sql(payload['forward'])
        expected = copy.deepcopy(before)
        expected['npc_types'][0]['helmtexture']='90'
        after = capture()
        assert after==expected, 'Unexpected deployment afterimage'
        (OUT/'after.json').write_text(json.dumps(after,indent=2)+'\n')
        dc('start','game')
        health()
        after_runtime, cache_size = verify_runtime(before_runtime)
        dc('start','gateway')
        result = {'status':'deployed_for_live_qa','npc_id':999521,'helmtexture':90,
                  'only_npc_field_changed':'helmtexture','cache_rows_preserved':len(before['zone_state_spawns']),
                  'spawn_tint_weapon_item_preserved':True,'rehearsal_rolled_back':True,
                  'backup_uncompressed_bytes':size,'backup_sha256':hashlib.file_digest((OUT/'peq-before.sql.gz').open('rb'),'sha256').hexdigest(),
                  'native_binaries_unchanged':True,'all_zones_restarted':True,
                  'helmet_in_item_cache':True,'item_cache_bytes':cache_size,'gateway_reopened':True,
                  'native_visual_qa':'pending','before_runtime':before_runtime,'after_runtime':after_runtime}
        (OUT/'deployment.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))
    except Exception:
        # Reopen only when persisted content is the exact reviewed before/after
        # and the game is healthy. Otherwise retain the gate for investigation.
        if stopped and 'before' in locals():
            current = capture()
            expected = copy.deepcopy(before)
            expected['npc_types'][0]['helmtexture']='90'
            if current in (before, expected):
                dc('start','game')
                health()
                verify_runtime(before_runtime)
                dc('start','gateway')
        raise
