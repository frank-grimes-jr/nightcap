"""Replace superseded Quick Buff knowledge after the verified follow-up release."""
import argparse,difflib,hashlib,json
from pathlib import Path
from update_quick_buff_live_skill import section
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/releases/quick-buff-20261112/hotkey-fix'
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');args=p.parse_args()
 live=json.loads((OUT/'production-verification.json').read_text());wiki=json.loads((OUT/'wiki-public-verification.json').read_text())
 assert live['status']=='PASS' and live['gateway_open'] and not live['client_update_required']
 assert wiki['status']=='PASS' and wiki['files']==613
 names=['references/'+n for n in ('multiclass.md','operations.md','client.md','wiki.md','sources.json')]
 before={n:(SKILL/n).read_text(encoding='utf-8') for n in names};after=dict(before)
 oldzone='1fe268a18c45190f43ea25290c95ad852561029da5cacb024d7c99a91d40abd4'
 newzone='3eeb72c9adf0f7cc19baf144b1d5365d392415980eb87618774e2ae5205f4ae2'
 for name,heading in [('multiclass.md','Quick Buff — November12 deployed for live QA'),('operations.md','Current native baseline — November12 Quick Buff live QA'),('client.md','Quick Buff — November12 signed text published')]:
  key='references/'+name;text=before[key];start=text.index('## '+heading);end=text.find('\n## ',start+3);current=text[start:end if end>=0 else len(text)]
  current=current.replace('PR422/a2ae50f0','PR423/60d51362 (v1 PR422/a2ae50f0)').replace(oldzone,newzone).replace('zone1fe268a1','zone3eeb72c9').replace('Full zone1fe268a1','Full-build baseline plus follow-up zone3eeb72c9')
  current=current.replace('Client gained a member: full zone/common/GM/Lua/Perl rebuild is mandatory.','The v1 Client member required a full zone/common/GM/Lua/Perl build. The v2\nmetadata-only follow-up reproduces that completed build, keeps Client layout\nunchanged, compiles AA/spells and verifies all146retained link inputs.')
  current=current.replace('Full zone/common/GM/Lua/Perl build and stripped ELF identity pass. Client layout\nchanged: do not replace this full build with a two-TU retained-object relink.','The v1 full zone/common/GM/Lua/Perl build is retained. V2 reproduces it,\ncompiles AA/spells against unchanged Client layout and verifies all146link\ninputs/ELF identity. Never use objects predating the v1 Client member.')
  current+='\n\nOwner reported v1 Make Hotkey disabled on earned Palwar rank3. Pinned RoF2\ngate0x6081E4 compares ability+0x64 against zero. ClientPresentationReuse\nadvertises1only for family48 while authoritative reuse stays0; every family48\nSendAlternateAdvancementTimer is reset(begin0,end=current time), including stale\nresends. Never use(0,0), which starts the nominal client timer. Generic AA details\ncan show1second; actual readiness is immediate. Exact native gate/receiver36\nchecks reproduce old failure and pass the fix; identity17and Linux rollout9\ntests pass, fresh-context review resolved. No extra signed client/DLL download,\nAA grant or casting/mana change. Relog then Make Hotkey. Native visible creation,\nrepeat activation, delivery and balance acceptance remain OPEN. Follow-up\nhotkey-fix/ owns one-shot rollout, build and live preservation/backup receipts;\nnever replay v1 or v2 terminal actions. Client2026111201 remains unchanged.\n'
  after[key]=section(text,heading,current)
 key='references/wiki.md';text=before[key]
 note='''## Quick Buff — November12 published for live testing

Wiki20261112-quick-buff-v2 replaces Quick Buff v1. The exact previous613public
outputs reproduced before Combat instructions, Change Log and search changed;
610files retained. Instructions cover relog/Make Hotkey, nominal native1second
detail with actual immediate readiness, unchanged50%maximum-mana cost and no
additional download. All42authored guides/Home/Features/commands and generated
item/zone/catalog impacts reviewed: no other player values or instructions change.
All613HTTPS hashes/security headers and five private denials pass. Guarded
pointer update rehearses rollback and retains all five service identities,
channel/config/private downloads; no Nginx reload. No global ledger advance:
unrelated source drift remains REVIEW REQUIRED. Exact source is the authenticated
wiki artifact tree. Evidence/tools: quick-buff-hotkey/docs/releases/quick-buff-20261112/hotkey-fix/.
Owner visible hotkey/gameplay/balance acceptance remains OPEN; v1 Make Hotkey
failure on Palwar is retained in release history, not relabeled accepted.
'''
 after[key]=section(text,'Quick Buff — November12 published for live testing',note)
 manifest=json.loads(before['references/sources.json']);revision='PR423/main60d51362; source6c3240a2; verified v2 metadata follow-up, owner acceptance OPEN'
 manifest['observed_revisions']['quick_buff_deployed_20261112']=revision
 paths={e['path'] for e in manifest['topics']['quick-buff']}
 paths.update('docs/releases/quick-buff-20261112/hotkey-fix/'+n for n in ('README.md','native-build.json','rollout.py','production-verification.json','wiki-public-verification.json','review.json','release-checks.json'))
 paths.update(('eq-client-dll/tests/aa-reuse-native.cpp','tools/tests/test_quick_buff_hotkey_native.py','tools/tests/test_quick_buff_hotkey_rollout.py','tools/build_quick_buff_hotkey_fix.py','tools/prepare_quick_buff_hotkey_wiki.py','tools/verify_quick_buff_hotkey_fix.py'))
 entries=[]
 for n in sorted(paths):
  if (ROOT/n).is_file():entries.append(dict(root=ROOT.as_posix(),path=n,role='Reviewed Quick Buff implementation/native compatibility/deployment evidence; owner acceptance OPEN',revision=revision,sha256=hashlib.sha256((ROOT/n).read_bytes()).hexdigest()))
 manifest['topics']['quick-buff']=entries
 # Refresh only previously reviewed Quick Buff paths in other topics; retain unrelated knowledge.
 bypath={e['path']:e for e in entries}
 for topic in ('operations','client','wiki'):
  manifest['topics'][topic]=[bypath.get(e['path'],e) for e in manifest['topics'][topic]]
  owned={'operations':['native-build.json','production-verification.json','rollout.py'],'wiki':['wiki-public-verification.json'],'client':[]}[topic]
  new=[e for e in entries if '/hotkey-fix/' in e['path'] and any(e['path'].endswith('/'+n) for n in owned)]
  manifest['topics'][topic]=new+manifest['topics'][topic]
 after['references/sources.json']=json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'
 patch=''.join(''.join(difflib.unified_diff(before[n].splitlines(True),after[n].splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n in names)
 (OUT/'installed-skill.patch').write_text(patch,encoding='utf-8',newline='\n')
 if args.write:
  for n,text in after.items():(SKILL/n).write_text(text,encoding='utf-8',newline='\n')
 print(json.dumps({'status':'installed' if args.write else 'prepared','files':len(after)}))
if __name__=='__main__':main()
