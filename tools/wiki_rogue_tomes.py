"""Prepare the scoped tome-learning guide and release-note update."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ARTICLES=ROOT/'wiki/articles'
GUIDE='''<h2 id="learning-tomes">Learn combat disciplines from tomes</h2><p>Right-click a tome to learn it when one of your three held classes qualifies and you meet the discipline's level requirement. This also works when Rogue is your second or third class, including with a caster primary class. A successful learn consumes one tome and adds the discipline to Combat Abilities.</p><p>If you already know the discipline, your list is full, you do not qualify, or saving fails, the right-clicked tome stays in its original inventory slot. Disciplines keep their normal level, endurance, positioning and reuse requirements. Early spellbook scribing does not remove discipline levels.</p><p>For example, Sneak Attack is a level-20 Rogue discipline. After learning it, hide for at least four seconds and meet its combat requirements before activating it. Higher-level tomes remain restricted. Released AA ranks remain available from level 1; AA requirements and discipline requirements are separate.</p><p>The tome repair is live for testing; in-game acceptance is still being checked.</p>'''
NOTE='''<h2 id="rogue-tome-learning">October 24 - Multiclass tome learning repaired</h2><p>Eligible tomes can now be learned through any held class, fixing secondary and third-class Rogue learning. Failed right-clicks preserve the original tome; full lists, duplicate entries and failed saves no longer consume it. Discipline use levels and the level-1 AA policy are unchanged. See <a href="multiclass.html#learning-tomes">learning combat disciplines</a> for requirements. Live gameplay acceptance remains under review.</p>'''
for slug in ('multiclass','recent-changes'):
    p=ARTICLES/(slug+'.json');d=json.loads(p.read_text(encoding='utf-8'))
    assert 'id="learning-tomes"' not in d['body'] and 'id="rogue-tome-learning"' not in d['body']
    if slug=='multiclass':
        anchor='<h2 id="starter-provisions">';assert anchor in d['body'];d['body']=d['body'].replace(anchor,GUIDE+'\n'+anchor,1)
        d['keywords']+=['rogue tomes','learn disciplines','Sneak Attack']
    else:d['body']=NOTE+d['body']
    d['updated']='2026-10-24'
    d['sources'].append('docs/releases/rogue-tomes-20261024/README.md (authorized deployment; native gameplay QA remains pending)')
    p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
