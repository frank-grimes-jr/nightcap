"""Record whole-wiki candidate impact without publishing or advancing live state."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];REL=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
target=REL/'wiki-review.json'
if target.exists():raise RuntimeError('Review already recorded; reconcile subsequent changes explicitly')
notices={
'combat':'The combined scaling candidate adds effective Spell Damage to direct damage and half to each ordinary DoT tick. Heroic INT/WIS improve direct damage/healing by 0.1% per point. Healing Amount and HoT distribution retain their current formulas; Bard rune songs gain no added HA bonus.',
'equipment':'The combined candidate matches supported numeric fields on 131 observed Ascended items, including reductions where current stats exceed the reference. Starter qualities keep modest earned steps below comparable Normal dungeon rewards. Existing named pet/WPM effects and sockets are retained.',
'features':'A combined candidate brings selected Ascended items and spell scaling closer to the THJ references, alongside the pet/WPM work. Exact item tuning and modest starter progression replace a universal multiplier for the reviewed families.',
'getting-started':'Starter and dungeon equipment tuning is prepared for testing: each starter quality remains a small upgrade, while comparable Normal dungeon rewards remain stronger. These candidate values are not the live starter stats.',
'index':'The combined item/spell scaling candidate is prepared alongside pet/WPM changes. It includes selected Ascended values, additive spell damage and preserved starter progression; gameplay acceptance is still pending.',
'pets':'The combined spell candidate changes eligible permanent-pet direct damage and ordinary DoT ticks using their own gear plus capped owner inheritance. Owner heroic INT/WIS are not copied. Pet/WPM equipment and effects remain part of the same testing candidate.',
'item-upgrades':'The combined candidate adjusts selected Ascended values and caps intermediate numeric stats where needed to avoid reversing progression. Item identities, ownership, upgrade receipts, existing effects and sockets are preserved; upgrade costs and commands are unchanged.',
'dungeon-modes':'Candidate equipment tuning raises selected dungeon budgets so comparable Normal dungeon rewards beat Ascended starter gear. Existing modes, objectives, keepers and reward eligibility stay the same. Live reward values have not changed.',
'zone-hunt':'The combined spell candidate retains earned Hunt cap headroom. Heroic INT/WIS become separate direct-value modifiers rather than additional Spell Damage or Healing Amount. Existing Hunt rewards, tasks and commands are unchanged.',
'recent-changes':'Prepared a combined item/spell and pet/WPM testing candidate: 131 observed Ascended targets, additive direct Spell Damage, half-SD ordinary DoT ticks, direct heroic INT/WIS and modest starter-to-dungeon progression. No gameplay or wiki publication is included.'}
report={'status':'source_only_publication_pending','date':'2026-10-18','articles':{},
        'generated_routes':{'count':432,'decision':'Retain published reward catalog and generated item/zone routes. Candidate ordinary/starter/dungeon changes are labeled in guides; no candidate values presented as live.'},
        'source_authority':'feature/thj-item-spell-parity working tree; actual hash inventory in evidence',
        'global_reviewed_revision':'retained; source drift is assessed, not silently accepted'}
for path in sorted((ROOT/'wiki/articles').glob('*.json')):
    before=sha(path);data=json.loads(path.read_text(encoding='utf-8'));slug=data['slug']
    if slug in notices:
        assert 'id="thj-parity-candidate"' not in data['body']
        data['body']='<p class="notice" id="thj-parity-candidate"><strong>Not released:</strong> '+notices[slug]+' See <a href="unreleased.html#thj-parity">the combined candidate</a>.</p>\n'+data['body']
    elif slug=='unreleased':
        data['body']='<h2 id="thj-parity">Combined item and spell scaling — not released</h2><p>The candidate tunes supported numeric fields on 131 observed Ascended items and preserves modest starter upgrades below comparable Normal dungeon rewards. Exact per-item values replace a blanket multiplier for these reviewed families. Unresolved workbook/screenshot conflicts are deferred.</p><p>Direct spell damage adds effective Spell Damage once; each ordinary DoT tick adds half, independent of duration. Clients gain 0.1% per heroic INT/WIS on direct damage/healing. DoTs and HoTs do not receive the heroic multiplier. Existing HA healing/HoT formulas remain, Bard rune songs gain no HA rune bonus, and the separate native Bard area-DoT route remains unchanged.</p><p>The pet/WPM candidate below is integrated: 750 base caps and Hunt headroom, bounded owner inheritance, complete pet items/augments, earned AAs and named melee effects. Historical THJ observations do not prove every current THJ formula; critical DoT ordering and unobserved effects remain calibration choices. No production installation, signed client publication or player acceptance is claimed.</p>\n'+data['body']
    changed=slug in notices or slug=='unreleased'
    if changed:
        data['updated']='2026-10-18';data['sources'].append('docs/releases/thj-parity-20261018/README.md and QA.md; combined source candidate, not deployed or owner accepted')
        path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    report['articles'][slug]={'decision':'Added explicit combined candidate guidance; live values/status retained' if changed else 'Reviewed: no additional impact on this topic, commands, travel, class ownership or live release labels; existing companion notices retained',
        'before_sha256':before,'after_sha256':sha(path)}
ledger=ROOT/'wiki/content-review.json';data=json.loads(ledger.read_text(encoding='utf-8'))
data['supplemental_evidence'].append('October18 combined THJ parity candidate: all21 maintained articles and432 generated reward routes reviewed against the working item/spell/starter and pet/WPM source. Eleven guides updated with Not released notices/details; published catalog, commands, acquisition and current era retained. docs/releases/thj-parity-20261018/wiki-review.json records every decision. No wiki publication or global reviewed_revision advancement.')
ledger.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
target.write_text(json.dumps(report,indent=2)+'\n')
print('Reviewed',len(report['articles']),'articles; updated',len(notices)+1)
