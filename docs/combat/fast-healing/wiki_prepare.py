from pathlib import Path
import json,shutil,subprocess,sys,hashlib
A=Path(__file__).resolve().parent
W=Path('E:/EQ_Local_Dev/_worktrees/fast-healing')
P=Path('E:/EQ_Local_Dev/_worktrees/inventory-no-scrollbars/artifacts/inventory-no-scrollbars/wiki-source/wiki')
S=A/'wiki'
if not S.exists():shutil.copytree(P,S,ignore=shutil.ignore_patterns('dist','__pycache__','*.tar.gz','*.tar.json'))
subprocess.run([sys.executable,str(S/'build.py')],check=True)
before=json.loads(Path('E:/EQ_Local_Dev/_worktrees/inventory-no-scrollbars/artifacts/inventory-no-scrollbars/20261120-inventory-no-scrollbars-v1.tar.json').read_bytes())
assert all(hashlib.sha256((S/'dist'/n).read_bytes()).hexdigest()==v for n,v in before.items()),'Public predecessor source does not reproduce'
combat='<h2 id="fast-heals">Fast healing in melee</h2><p>Minor Healing and Light Healing gain at least one healing point per effective Heal Amount on an original cast. Any larger existing bonus is kept. Greater Healing and Healing retain their current scaling. Healing focuses, criticals and heroic Wisdom continue to apply.</p><p>The extra floor does not apply to item clicks, weapon procs or triggered AA heals such as Blessing of Life and Healing Light. Sympathetic Healing still adds up to 5% of a landed direct heal, rounded down, with a maximum of 48 extra healing. Interrupted casts do not produce that extra heal.</p><p>Heal Amount increases healing power; spell haste shortens casting. Djarn\'s Amethyst Ring from Efreeti Lord Djarn in Solusek B has Spell Haste II: Greater Healing takes 2.55 seconds instead of 3, and Light Healing takes 1.7 seconds instead of 2. Minor Healing is below that focus\'s minimum cast time. Train Channeling and avoid movement while casting; stuns and melee hits can still interrupt you.</p>'
equipment='<h2 id="healing-focus-haste">Healing power and casting speed</h2><p>Improved Healing increases healing power. Spell Haste reduces the cast time of qualifying spells. See <a href="combat.html#fast-heals">fast healing in melee</a> for the Minor Healing and Light Healing bonus, Djarn\'s Amethyst Ring and interruption guidance.</p>'
change='<h2 id="fast-healing-20261120">November 20, 2026: fast direct healing</h2><p>Minor Healing and Light Healing now receive a minimum flat Heal Amount contribution on original casts. Greater Healing, Healing and paladin healing procs retain their existing scaling. Sympathetic healing keeps its existing limit. See <a href="combat.html#fast-heals">fast healing in melee</a>. Player combat testing continues.</p>'
for root in [S,W/'wiki']:
 for slug,body in [('combat',combat),('equipment',equipment),('recent-changes',change)]:
  p=root/'articles'/f'{slug}.json';d=json.loads(p.read_bytes())
  assert 'id="fast-heals"' not in d['body'] and 'id="fast-healing-20261120"' not in d['body']
  d['body']=body+d['body'] if slug=='recent-changes' else d['body']+body
  p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
archive=A/'20261120-fast-healing-v1.tar.gz'
subprocess.run([sys.executable,str(S/'build.py'),'--package',str(archive)],check=True)
manifest=json.loads(archive.with_suffix('.json').read_bytes())
changed=sorted(n for n,v in manifest.items() if before.get(n)!=v)
assert set(before)==set(manifest) and changed==['combat.html','equipment.html','recent-changes.html','search-index.json']
(A/'wiki-candidate.json').write_text(json.dumps({'release':'20261120-fast-healing-v1','previous':'20261120-inventory-no-scrollbars-v1','changed':changed,'preserved':len(manifest)-len(changed),'files':len(manifest)},indent=2))
print('PASS predecessor reproduced and four outputs changed')
