"""Add SSF guidance to a wiki/ checkout: multiclass section, Features row, Change Log."""
from pathlib import Path
import json,sys
SOURCE='docs/releases/ssf-mode-20261101/README.md and docs/adr/0074-solo-self-found-mode.md'
GUIDE=('<h2 id="solo-self-found">Solo self-found (optional)</h2>'
 '<p>At level 1 you may swear the solo self-found oath: hail the Ancient Chronicler in the '
 '<a href="tunnel.html">East Commonlands tunnel</a>, choose <strong>walk alone</strong> and confirm. '
 'The oath is permanent; only a GM can remove it. Hailing the Chronicler shows your status.</p><ul>'
 '<li>No trading with players, either Bazaar, sending or receiving parcels, or the shared or guild bank.</li>'
 '<li>No grouping or raiding with players. Bots and mercenaries are allowed.</li>'
 '<li>Quest hand-ins to NPCs still work.</li>'
 '<li>No passive AA. At 0% you earn full leveling EXP and no AA; use + in the AA window to put part of your experience into AA.</li>'
 '<li>Leveling EXP is the same as for other characters.</li></ul>')
FEATURE=('<h3 id="solo-self-found-preview">Solo self-found</h3><p>Swear a permanent level-1 oath to find '
 'everything yourself: no player trading, Bazaar, parcels, shared bank or player groups, and no passive AA. '
 '<a href="multiclass.html#solo-self-found">How to walk alone</a>.</p>')
CHANGE=('<h2 id="ssf-20261101">November 1: solo self-found mode - live testing</h2>'
 '<p>New level-1 characters can swear a permanent solo self-found oath at the Ancient Chronicler. '
 'Self-found characters cannot trade with players, use either Bazaar, parcels, the shared or guild bank, '
 'or group or raid with players, and earn no passive AA. No client update is required. '
 'Player acceptance remains open. <a href="multiclass.html#solo-self-found">How it works</a>.</p>')

def edit(name,fn):
    p=Path(sys.argv[1])/'articles'/(name+'.json');a=json.loads(p.read_text(encoding='utf-8'))
    assert 'solo-self-found' not in a['body'] and 'ssf-20261101' not in a['body'],name
    fn(a);a['updated']='2026-11-01'
    if isinstance(a.get('sources'),list):a['sources'].append(SOURCE)
    p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

def once(text,old,new):
    assert text.count(old)==1,old;return text.replace(old,new)

def guide(a):
    a['body']=once(a['body'],'<h2 id="alternate-abilities">',GUIDE+'<h2 id="alternate-abilities">')
    a['keywords']+=['SSF','solo self-found','self found','walk alone']
def features(a):
    head='<h2 id="custom-builds">Custom character &amp; combat systems</h2>'
    a['body']=once(a['body'],head,head+FEATURE)
def changes(a):a['body']=CHANGE+a['body']

if __name__=='__main__':
    edit('multiclass',guide);edit('features',features);edit('recent-changes',changes)
