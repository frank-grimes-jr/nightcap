"""Record verified delivery and the still-open owner gameplay acceptance."""
import gzip,hashlib,json,re,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;QUEST=HERE.parent;ROOT=HERE.parents[3]
WIKI=Path('C:/Users/verre/.codex/worktrees/aa-level-wiki/EQ_Local_Dev')

def main():
 d=json.loads((HERE/'deployed.json').read_text());w=json.loads((HERE/'wiki-public-verification.json').read_text())
 assert d['gateway_open'] and d['campaign_enabled'] and w['result']=='PASS'
 text=f'''# Chapterhouse deployment — October 23, 2026

Deployed for owner live testing. Feature8f4f7f1f promoted through PR309 (dev),
PR310 (test), PR311 (main c0c9896e151999e7002a453594079dae7b83bc41).
The owner explicitly requested main and server activation. This is not completed
in-game acceptance. Start with Camil999521 in East Commonlands; Keeper998820
near Befallen in West Commonlands opens the level50 expedition.

## Verified release

Production image `{d['game']['image_id']}` uses paired world97403fda,
zone2c9323e4 and shared_memory375814fe plus13 exact-ID scripts. Both campaign
tables,35 managed spawns,Tasks9800/9742/9743,curated rewards,zone exception,
waypoint and Keeper are installed. Campaign/dungeon admission is enabled.
All12 workers,native health,45schema/532content checks and427cache definitions
pass. The actual loader preserves309844existing item definitions and adds13;
helmet990500 and spells stay unchanged. Classic50 and signed client2026102301
remain; no client update is needed. The server has Chapterhouse map/nav assets.

A fresh stopped backup is retained on the host. {d['state_tables']} saved-state tables
were checked, with the rehearsed waypoint catalog addition and exact native
seven-day non-corpse expiry accounted for. Inventory,earned progress,corpses,
run UUIDs and receipts were not restored or reset. Public access is open.
See deployed.json,preflight-receipt.json and the original private host receipts.

Wiki20261023-camil-chapterhouse-v1 publishes483files/476HTML pages, with a
Vigil guide and14reward pages (13new definitions plus the existing helmet).
All public hashes/security headers and five private-route denials verify.
The existing384Hunt values,Build Lab,loot finder and private guide are preserved.
Wiki source: feature/chapterhouse-wiki in the aa-level-wiki managed checkout.

## Holds and recovery

Initial activation committed the guarded schema/content, then held closed.
The existing preservation list includes `nightcap_waypoints`; its expected
content addition was incorrectly treated as player-state drift. Exact inspection
found only checksum4261781391→2941369031 for that public catalog; all other
saved tables and all content contracts matched. The first continuation refused
the gateway's normal SIGTERM143 exit before any write; native game exit was0.
The tested resume-v2.py accepts those exact stopped states and only the
rehearsed waypoint checksum. It never replays SQL or restores a snapshot.
Original evidence and held receipts are retained. Successful continuation uses
`/opt/nightcap/releases/camil-chapterhouse-20261023/resume-evidence/`.
Do not replay activation or continuation. For later recovery, disable new Vigil
admission while retaining matching schema/content/runtime and earned claims.

The host initially had584MiBfree. Seventeen explicitly selected,unmounted
historical staging binaries were losslessly compressed with verified
decompressed SHA256,freeing3767819385bytes. No image,active file or database
backup was removed. Adjacent `.chapterhouse-recovery.gz` files and
storage-recovery.json retain restoration hashes/modes. Restore an old binary
copy before attempting its historical operator; do not roll back player data.

## Validation and owner QA

Five release test groups cover16injected activation failures,cache preservation,
campaign gating,waypoint-only state adjustment and exact stopped-state exits.
Chapterhouse5tests pass again; prior native,dungeon,Hunt,SQL,geometry and48case
maximum-legal-power arena evidence remains in the parent directory.
Wiki68Linux checks,15focused Windows checks,Build Lab and equipment Node suites
pass. Installation and visible gameplay acceptance remain separate.

Use [the exact in-game checklist](../QA.md): Camil eligibility and both journals,
Sered interruption,Elowen's three waves,Halvyr's adds,Vaelen/Shadow movement and
stuns,personal recovery/helmet delivery,waypoint/exits,era-safe drops and forging.
Test both modes with legal maximum power including Ascended Ghoulbane,Slay/proc/
critical AAs and other strong Paladin combinations. Full-clear difficulty,
pathing,client models and owner acceptance remain open.
'''
 (HERE/'README.md').write_text(text,encoding='utf-8')
 p=ROOT/'CHANGES.md';body=p.read_text(encoding='utf-8');body=body.replace('# CHANGES\n','# CHANGES\n\n## 2026-10-23 — Chapterhouse deployed for live testing\n\nOwner-authorized main PR311/c0c9896e and paired production activation are verified.\nCamil’s Vigil, native story/dungeon Tasks, four level50–53 bosses, curated loot,\nEmber augment, waypoint and Keeper are live. Fresh backup, all12workers,\n45schema/532content checks and427reward cache definitions pass;309844old items\nremain byte-identical. A strict preservation guard held on the intended public\nwaypoint addition; an audited continuation reconciled only that catalog row,\nwithout player restoration. Wiki483files is published; client2026102301 remains.\nFull encounters and owner balance acceptance remain open.\n[Delivery and recovery](docs/quests/camil-chapterhouse/deployment/README.md).\n',1);p.write_text(body,encoding='utf-8')
 p=ROOT/'docs/status.md';body=p.read_text(encoding='utf-8');body=re.sub(r'## 2026-10-23 — Chapterhouse.*?(?=\n## )','''## 2026-10-23 — Chapterhouse deployed for live testing

Main PR311/c0c9896e and paired production image db570029 are verified. Camil’s
level50 Paladin Vigil uses native Tasks and persistent personal progress. The
four level50–53 bosses, curated rewards, Ember augment, waypoint and Keeper near
Befallen are live. All12workers,45schema/532content and427reward cache checks
pass;309844existing items,player state and signed client2026102301 remain.
The planned waypoint catalog addition was reconciled after a strict guard held
activation; no player snapshot was restored. Public access is open.
Wiki20261023-camil-chapterhouse-v1/all483files verifies. Full encounters, other
maximum-power combinations and owner acceptance remain open.
[Delivery/recovery](quests/camil-chapterhouse/deployment/README.md);
[exact in-game checks](quests/camil-chapterhouse/QA.md).
''',body,count=1,flags=re.S);p.write_text(body,encoding='utf-8')
 p=QUEST/'SPEC.md';body=p.read_text(encoding='utf-8').replace('# The Vigil of the Dawn — Chapterhouse candidate','# The Vigil of the Dawn — Chapterhouse')
 body=body.replace('5d0a0d31bd1b8c07ca1df3cc620d323c0c07f175. **Not deployed or player accepted.**','5d0a0d31bd1b8c07ca1df3cc620d323c0c07f175. Promoted to main c0c9896e and deployed\nOctober23 for live testing. **Owner gameplay acceptance remains open.**\n[Delivery evidence](deployment/README.md).');p.write_text(body,encoding='utf-8')
 p=QUEST/'RUNBOOK.md';body=p.read_text(encoding='utf-8').replace('# Chapterhouse candidate operations','# Chapterhouse operations')
 body=body.replace('Not installed. Source tests, native build, SQL rehearsal, map probes and arena\ncalibration are separate from production and player QA. Local-preimage SQL must\nnot be applied to production without fresh capture and target rehearsal.',
 'Installed October23 after explicit owner authorization, fresh production capture,\nrehearsal and stopped backup. Main c0c9896e and paired runtime are live for testing.\nThe original guard held on the expected public waypoint catalog addition; the\nreviewed resume-v2 continuation preserves all other state. See\n[delivery and recovery](deployment/README.md). Never replay either operator.\nNative calibration remains separate from owner in-game acceptance.')
 body=body.replace('## Future authorized activation','## Requirements for a future authorized release');p.write_text(body,encoding='utf-8')
 p=QUEST/'verification.json';v=json.loads(p.read_text());v['delivery']='Main c0c9896e and paired production activation verified; see deployment/deployed.json';v['outstanding']=[s for s in v['outstanding'] if not s.startswith(('Fresh production','Separate public wiki'))];p.write_text(json.dumps(v,indent=2)+'\n')
 # Preserve the public capture without another large text diff.
 capture=HERE/'production-preimage.json'
 (HERE/'production-preimage.json.gz').write_bytes(gzip.compress(capture.read_bytes(),mtime=0))
 print(json.dumps({'docs_updated':True,'wiki_files':w['files']}))

if __name__=='__main__':main()
