"""Verify current candidate fingerprints while retaining historical drift evidence."""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];REL=Path(__file__).resolve().parent
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
report={'status':'passed','validator':'passed','topics':{},'candidate_entries':0}
for topic in ('balance','items','wiki','operations'):
    result=subprocess.run([sys.executable,str(SKILL/'scripts/context.py'),'--topic',topic,'--root',str(ROOT),'--check'],capture_output=True,text=True)
    assert result.returncode in (0,1),result.stderr
    data=json.loads(result.stdout)
    (REL/'evidence'/f'skill-context-{topic}.json').write_text(json.dumps(data,indent=2)+'\n')
    current=[r for r in data['topics'][topic] if r['role'].startswith('Reviewed combined item/spell and pet/WPM candidate;')]
    assert current and all(r['state']=='unchanged' for r in current),topic
    history=[r for r in data['topics'][topic] if r not in current and r['state']!='unchanged']
    report['topics'][topic]={'candidate_unchanged':len(current),'historical_entries_differing_in_current_root':len(history)}
    report['candidate_entries']+=len(current)
report['historical_drift_policy']='Older deployed/other-checkout fingerprints remain dated evidence; not blindly advanced to candidate state'
assert report['candidate_entries']==35
(REL/'evidence/skill-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
