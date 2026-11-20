from pathlib import Path
import hashlib,json,shutil,subprocess,sys
A=Path(__file__).resolve().parent
W=Path('E:/EQ_Local_Dev/_worktrees/aa-availability')
P=A.parent/'fast-healing-20261120'
S=A/'wiki'
if not S.exists():shutil.copytree(P/'wiki',S,ignore=shutil.ignore_patterns('dist','__pycache__','*.tar.gz','*.tar.json'))
subprocess.run([sys.executable,str(S/'build.py')],check=True)
before=json.loads((P/'20261120-fast-healing-v1.tar.json').read_bytes())
assert all(hashlib.sha256((S/'dist'/n).read_bytes()).hexdigest()==v for n,v in before.items())
body='<h2 id="mastery-access">Mastery of the Past availability</h2><p>Clerics, Paladins, Rangers, Druids, Shamans and Beastlords can purchase the existing three ranks of Mastery of the Past without Spell Casting Expertise, which those classes cannot purchase. Holding any one of these classes provides this path, regardless of your primary class. Builds using only Shadow Knight, Bard, Necromancer, Wizard, Magician or Enchanter retain the Expertise III prerequisite.</p><p>Ranks, prices and effects are unchanged. This AA reduces spell fizzles; it does not prevent melee interruptions. Relog to refresh the AA window. Turn off the Recommended filter to see all eligible abilities. Fury of Magic and Mystical Attuning remain available under their existing class rules and rank limits.</p>'
change='<h2 id="aa-availability-20261120">November 20, 2026: AA availability</h2><p>Fixed an impossible prerequisite blocking Mastery of the Past for Cleric, Paladin, Ranger, Druid, Shaman and Beastlord builds. All existing AA ranks, prices and effects remain unchanged. Relog to refresh the AA window. See <a href="multiclass.html#mastery-access">AA availability</a>. Player acceptance testing continues.</p>'
for root in (S,W/'wiki'):
 for slug,extra in [('multiclass',body),('recent-changes',change)]:
  p=root/'articles'/f'{slug}.json';d=json.loads(p.read_bytes())
  assert 'id="mastery-access"' not in d['body'] and 'id="aa-availability-20261120"' not in d['body']
  d['body']=extra+d['body'] if slug=='recent-changes' else d['body']+extra
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
archive=A/'20261120-aa-availability-v1.tar.gz'
subprocess.run([sys.executable,str(S/'build.py'),'--package',str(archive)],check=True)
manifest=json.loads(archive.with_suffix('.json').read_bytes())
changed=sorted(n for n,v in manifest.items() if before.get(n)!=v)
assert set(before)==set(manifest) and changed==['multiclass.html','recent-changes.html','search-index.json']
(A/'wiki-candidate.json').write_text(json.dumps(dict(release='20261120-aa-availability-v1',previous='20261120-fast-healing-v1',changed=changed,preserved=len(manifest)-len(changed),files=len(manifest)),indent=2))
print('PASS public predecessor reproduced; three outputs changed')
