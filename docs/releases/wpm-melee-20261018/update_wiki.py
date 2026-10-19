"""Record whole-wiki candidate impact without publishing or changing live claims."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
import wpm_content


def main():
    link='<a href="unreleased.html#wpm-melee">WPM melee implementation</a>'
    additions={
        'index':f'The same candidate includes the {link}: Warrior/Paladin/Monk shield damage, sustain, earned AAs and combat item effects.',
        'features':f'The {link} adds held-class melee synergies, shield AAs and heroic-STR weapon scaling alongside the pet work.',
        'combat':f'The {link} combines held-class defenses, six Monk attacks, shield damage, rune/healing procs and earned Rage of Rallos. Native runes replace or refresh rather than accumulate.',
        'equipment':f'The {link} adds sympathetic healing, Diaku combat procs, a Bloodfrenzy Core power source, Marr shield sustain and Hastened Fragments of Truth, with earned boss acquisition.',
        'multiclass':f'The {link} opens reviewed WPM AA depth and applies combat capabilities across all three held classes. Earned ownership, costs, prerequisites and saved waits remain.',
        'pets':f'The {link} shares the proc and healing changes with pets. The new player heroic-STR weapon multiplier is not inherited by pets.',
        'launcher':f'The {link} also requires matching AA descriptions and spell data in that client release.',
        'recent-changes':f'The {link} is implemented in the combined candidate; both builds are being validated together before deployment.'
    }
    details='''<h2 id="wpm-melee">Warrior/Paladin/Monk shield build — not released</h2>
<p>The combined candidate supports one-handed weapon and shield combat with Shield Specialist, Holy Shield, Way of Steel, Healing Light, Blessing of Life and Rage of Rallos. All six Monk attacks participate. Relevant combat benefits follow held classes rather than their selection order; earned ranks and normal skill requirements remain.</p>
<p>Hopebringer and Cloak of the Black Wind gain sympathetic healing. Diaku Armor Fragment supplies a combat proc, Marr's shield provides haste and received healing, Bloodfrenzy Core occupies the power-source slot, and Hastened Fragments of Truth supply temporary attack-speed procs. The original Bloodfrenzy weapon remains a weapon. New families have earned Cursed, Tallon Zek and Seru routes.</p>
<p>A separately controlled heroic-STR multiplier applies to player weapon hits. It does not multiply pet attacks, spells, runes or Monk special attacks. The same candidate retains the pet equipment, augment, inheritance, healing/rune and split Rabid Bear changes described above. Rune and heroic-scaling values are Nightcap choices, not certified THJ formula parity.</p>
<p><strong>This is not deployed.</strong> Combined native combat validation and actual client gameplay acceptance precede release. Live equipment, progression, commands and reward-catalog values remain unchanged.</p>'''
    decisions={}
    source='docs/releases/wpm-melee-20261018/README.md; combined WPM/pet candidate, not deployed or gameplay accepted'
    for path in sorted((ROOT/'wiki/articles').glob('*.json')):
        doc=json.loads(path.read_text(encoding='utf-8'));slug=doc['slug']
        before=hashlib.sha256(path.read_bytes()).hexdigest()
        if slug=='unreleased':
            assert 'id="wpm-melee"' not in doc['body'],'Already reconciled'
            doc['body']=details+'\n'+doc['body']
        elif slug in additions:
            pattern=r'(<p class="notice" id="pet-scaling-candidate">.*?)(</p>)'
            doc['body'],count=re.subn(pattern,lambda m:m[1]+' '+additions[slug]+m[2],doc['body'],count=1,flags=re.S)
            assert count==1,slug
        if slug=='unreleased' or slug in additions:
            doc['updated']='2026-10-18';doc['sources'].append(source)
            path.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        decisions[slug]={'decision':'Combined candidate notice/detail; live behavior preserved' if slug=='unreleased' or slug in additions
                         else 'No additional WPM impact; prior pet/progression notice retained where applicable; commands, crafting, travel and live status unchanged',
                         'before_sha256':before,'after_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    catalog_path=ROOT/'wiki/catalog.json';catalog=json.loads(catalog_path.read_text())
    changed={r['id'] for r in wpm_content.item_rows()}|{r['id'] for _,r in wpm_content.gear_changes()}
    assert not changed & {int(r['id']) for r in catalog['items']}
    report={'status':'source_only_publication_pending','date':'2026-10-18','articles':decisions,
            'catalog':{'routes':len(catalog['items'])+len(catalog['zones']),
                       'sha256':hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
                       'decision':'No changed item IDs overlap released hunt rewards; acquisition, forging and catalog stats preserved'},
            'features':'WPM is explicit and unreleased, alongside pet candidate',
            'commands':'No new public command', 'publication':'Not authorized or performed'}
    Path(__file__).with_name('wiki-review.json').write_text(json.dumps(report,indent=2)+'\n')
    ledger=ROOT/'wiki/content-review.json';doc=json.loads(ledger.read_text())
    doc['supplemental_evidence'].append('October18 combined WPM/pet candidate: all21 articles and432 generated reward routes reviewed; nine articles clarify unreleased melee synergies, AAs and item effects alongside pet work. docs/releases/wpm-melee-20261018/wiki-review.json records decisions and content hashes. Live catalog/commands unchanged; no publication or global source-ledger advancement.')
    ledger.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'articles':len(decisions),'changed':9,'routes':report['catalog']['routes']}))


if __name__=='__main__':main()
