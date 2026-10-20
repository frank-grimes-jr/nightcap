from pathlib import Path
import re,gzip,shutil,hashlib,json,subprocess,sys,base64
root=Path(r'C:/Users/verre/.codex/worktrees/thj-item-spell-parity/EQ_Local_Dev'); here=root/'docs/releases/thj-behaviors-20261019/deployment'; prior=root/'docs/releases/thj-parity-20261018/deployment'
out=Path('E:/EQ_Local_Dev/artifacts/thj-behaviors-20261019/production-stage');out.mkdir();(out/'content').mkdir();(out/'recovery').mkdir();(out/'client').mkdir()
bundle=out.parent/'test-bundle-v1'
shutil.copytree(bundle/'server/bin',out/'bin');shutil.copytree(bundle/'client-delta',out/'client/assets')
for src,dst in [('content-forward.sql','content/01-aa-spells.sql'),('gear-forward.sql.gz','content/02-items.sql'),('rule-forward.sql','content/03-rule.sql'),('content-rollback.sql','recovery/content-rollback.sql'),('gear-rollback.sql.gz','recovery/gear-rollback.sql'),('rule-disable.sql','recovery/rule-disable.sql'),('rule-enable.sql','recovery/rule-enable.sql')]:
 p=here.parent/src;data=gzip.decompress(p.read_bytes()).decode() if p.suffix=='.gz' else p.read_text();(out/dst).write_text(data,newline='\n')
oldnote='THJ behavior candidate; paired world/zone, content and client required'
note=re.search(r'RULE_BOOL\(Spells, NightcapTHJBehaviors, false, "([^"]+)"', (root/'server-mods/code/common/ruletypes.h').read_text()).group(1)
for p in [out/'content/03-rule.sql',out/'recovery/rule-disable.sql',out/'recovery/rule-enable.sql']:
 s=p.read_text();assert oldnote.encode().hex() in s;s=s.replace(oldnote.encode().hex(),note.encode().hex());p.write_text(s,newline='\n')
(here/'rule-note-normalization.json').write_text(json.dumps({'old':oldnote,'compiled':note,'reason':'World normalizes descriptions at boot; preserve exact guarded recovery preimages. Values unchanged.'},indent=2))
s=(prior/'rollout.py').read_text().replace('thj-parity-20261018','thj-behaviors-live-20261019').replace('nightcap_thj_release_20261018','nightcap_thj_behaviors_live_20261019').replace('2026101802','2026101902').replace("len(m['components']) == 10","len(m['components']) == 3").replace('timeout=900','timeout=1800')
s=s.replace("'aa_rank_prereqs', 'lootdrop', 'lootdrop_entries', 'loottable_entries', 'rule_values'","'aa_rank_prereqs', 'rule_values'")
s=s.replace("'merchantlist', 'doors', 'zone', 'content_flags')","'merchantlist', 'doors', 'zone', 'content_flags', 'lootdrop', 'lootdrop_entries', 'loottable_entries', 'character_pet_armor')")
s=s.replace("names = TABLES + ('character_pet_armor',)","names = TABLES")
s=s.replace("    assert schema() == load(STAGE/'production-before.json')['pet_schema']\n    expected_schema(schema())",'')
s=s.replace("LIKE 'nightcap%20261018%'","LIKE 'nightcap_thj%'")
s=s.replace("    assert schema() == (expected_schema(p['pet_schema']) if installed else p['pet_schema'])",'')
s=s.replace("assert shutil.disk_usage(ROOT).free >= 5*1024**3","assert shutil.disk_usage(ROOT).free >= 3*1024**3")
s=s.replace("'control':checksums(CONTROL),'pet_schema':schema(),'routing':routing()","'control':checksums(CONTROL),'routing':routing()")
s=s.replace("for table in TABLES + CONTROL + ('character_pet_armor',):","for table in TABLES:").replace("        if table != 'character_pet_armor':\n            sql(","        sql(")
s=s.replace("    assert checksums(CONTROL, CLONE) == p['control'] and schema(CLONE) == p['pet_schema']",'')
s=s.replace("    assert schema(CLONE) == expected_schema(p['pet_schema'])",'')
a=s.index("    for component in m['components'][1:]:");b=s.index("    p['rules_after']",a);s=s[:a]+s[b:]
s=s.replace("    p['new_image_id'] = build_image(m)","    sql('DROP DATABASE `'+CLONE+'`;')\n    p['new_image_id'] = build_image(m)")
s=s.replace("assert shutil.disk_usage(ROOT).free >= 3*1024**3\n    save(EVIDENCE/'activation-started.json'", "assert shutil.disk_usage(ROOT).free >= 1024**3 + 512*1024**2 + sum((ROOT/'data/server/shared'/n).stat().st_size for n in ('items','spells'))\n    save(EVIDENCE/'activation-started.json'")
s=s.replace("EVIDENCE.mkdir(mode=0o700); save", "EVIDENCE.mkdir(mode=0o700); (STAGE/'private-backup').mkdir(mode=0o700); save")
(here/'rollout.py').write_text(s,newline='\n');shutil.copyfile(here/'rollout.py',out/'rollout.py')
shutil.copyfile(root/'docs/releases/thj-all-class-aa-20261019/deployment/rollout.py',out/'base_operator.py')
for n in ['prepare_client.py','publish_client.py']:
 s=(prior/n).read_text().replace('thj-parity-20261018','thj-behaviors-live-20261019').replace('2026101802','2026101902').replace('2026101801','2026101901')
 if n=='prepare_client.py':
  a=s.index("    changed = {");b=s.index('    previous =',a);s=s[:a]+"    changed = {'spells_us.txt','dbstr_us.txt'}\n"+s[b:]
 (here/n).write_text(s,newline='\n');(out/'client'/('prepare.py' if n=='prepare_client.py' else 'publish.py')).write_text(s,newline='\n')
pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'client/assets').iterdir()}
for n in ['sign-client.go','verify-client.go']:
 s=(prior/n).read_text().replace('2026101802','2026101902').replace('2026101801','2026101901')
 a=s.index('pins:=map[string]string{') if 'pins:=map' in s else s.index('pins :=map[string]string{');b=s.index('\n\t}',a)+3
 s=s[:a]+'pins := map[string]string{\n'+''.join('\t\t"'+k+'":"'+v+'",\n' for k,v in pins.items())+'\t}'+s[b:]
 s=s.replace('changed!=5','changed!=2').replace('five paired changes','two paired changes').replace('five-file','two-file').replace('"changed_assets": 5','"changed_assets": 2').replace('"existing_assets_preserved": 133','"existing_assets_preserved": 136')
 (here/n).write_text(s,newline='\n')
sys.path.insert(0,str(root/'docs/releases/thj-all-class-aa-20261019/deployment'));from remote import run
raw=run("from pathlib import Path\nimport sys\nsys.stdout.buffer.write(Path('/opt/nightcap/deploy/production/data/public/channel.json').read_bytes())")
(out/'client/previous-channel.json').write_bytes(raw)
before=json.loads((here/'production-before.json').read_text());assert hashlib.sha256(raw).hexdigest()==before['client_channel_sha256']
old=json.loads(base64.b64decode(json.loads(raw)['manifest'])); assert old['release']==2026101901
history=[{'release':2026101902,'date':'2026-10-19','changes':[{'kind':'feature','text':'Custom AA resource costs, cooldowns and spell focuses now follow researched THJ behavior. Updated ordinary tiered gear uses stock EverQuest baselines; Classic level 50 and starter progression remain. Open for live balance testing.'}]}]+old['patch_notes']
(root/'eq-launcher/patch-notes.json').write_text(json.dumps(history,indent=2)+'\n')
cmd=root/'eq-launcher/cmd/thj-behaviors-sign';cmd.mkdir();shutil.copyfile(here/'sign-client.go',cmd/'main.go')
try: subprocess.run(['E:/EQ_Local_Dev/artifacts/toolchains/go1.27.1/go/bin/go.exe','run','./cmd/thj-behaviors-sign','-assets',str(out/'client/assets'),'-previous',str(out/'client/previous-channel.json'),'-notes',str(root/'eq-launcher/patch-notes.json'),'-key','E:/EQ_Local_Dev/artifacts/ovh-private-20260920/production.seed','-output',str(out/'client/channel.json')],cwd=root/'eq-launcher',check=True)
finally:(cmd/'main.go').unlink();cmd.rmdir()
print('Prepared and signed 2026101902; not published.')
