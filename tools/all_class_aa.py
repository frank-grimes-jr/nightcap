"""Offline, evidence-bounded all-class AA policy and player changelist generator."""
import argparse
from collections import Counter
import copy
import csv
import gzip
import io
import itertools
import json
from pathlib import Path
import re

from aa_tbs_policy import compile_policy, header
from wpm_migration import migration

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / 'docs/releases/thj-all-class-aa-20261019'
CLASSES = ('Warrior', 'Cleric', 'Paladin', 'Ranger', 'Shadow Knight', 'Druid',
           'Monk', 'Bard', 'Rogue', 'Shaman', 'Necromancer', 'Wizard',
           'Magician', 'Enchanter', 'Beastlord', 'Berserker')
# Preserve the separately reviewed October18 pet/WPM release contracts.
PRESERVED = {267,249,60,207,174,792,241,1205,398,1041,385,1259,33,34,
             195,3512,3818,1403,938,3202,
             30,605,410,891,3820,131,108,273,341,30200}
EXCEPTIONS = {
    25: 'May7 removes Subtlety; preserve earned access pending a replacement/refund decision.',
    331: 'THJ Bazaar and Back is not Nightcap Origin.',
    334: 'Mystical Attuning rank chain differs; no guessed remapping.',
    492: 'Native Dimensional Shielding is a gate proc, not May7 interrupt immunity.',
    516: 'Abundant Healing native spell-level limits differ; effect reconciliation pending.',
    914: 'THJ Paladin Holy Shield uses released Nightcap30200; native914 is Warrior.',
    1246: 'THJ Weapon Mastery and native Blunt Mastery differ.',
    3724: 'THJ Return Bash and native Knight Return Strike/class masks differ.',
}


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def baseline():
    config = read_json(RELEASE / 'baseline-policy.json')
    tables = json.loads(gzip.decompress((ROOT / config['catalog']).read_bytes()))
    return config, tables


def clean_name(name):
    return re.sub(r'^\[[^]]+\]\s*', '', name).strip()


def rank_chain(ability, ranks):
    result, seen = [], set()
    rid = ability['first_rank_id']
    while rid in ranks:
        if rid in seen:
            raise ValueError(f'Rank cycle in {ability["id"]}')
        seen.add(rid)
        result.append(ranks[rid])
        rid = ranks[rid]['next_id']
    return result


def prepare():
    old_config, before = baseline()
    tables, config = copy.deepcopy(before), copy.deepcopy(old_config)
    old_rows = compile_policy(before, old_config)
    old_caps = Counter(r['ability_id'] for r in old_rows)
    abilities = {a['id']: a for a in tables['aa_ability']}
    ranks = {r['id']: r for r in tables['aa_ranks']}
    # Released THJ April20 patch, forum post2671: Druid receives Healing Boon.
    assert abilities[389]['classes'] == 518
    abilities[389]['classes'] |= 1 << 5
    config.update(id='all-class-aa-20261019', catalog='tools/fixtures/aa-all-class-catalog.json.gz',
        notes='All-class rank/access candidate. Every released rank, earned cost, prerequisite and pet/WPM ceiling retained. Druid Healing Boon added from released THJ post2671. Native effects retained; explicit parity gaps and all566 dispositions in docs/releases/thj-all-class-aa-20261019/. Classic50; no autogrants or owner-state edits.')
    config['deferred_abilities'].remove(397)  # Audited native nonstacking Wizard crit family.
    config['rank_caps']['397'] = 0  # Fail closed until its exact reviewed source alias passes.
    ledger = []
    evidence = read_json(RELEASE / 'thj-ranks.json')['abilities']
    if len(evidence) != 566 or len({e['id'] for e in evidence}) != 566:
        raise ValueError('Incomplete or duplicate THJ inventory')
    for source in evidence:
        aid, target = source['id'], source['rank_count']
        current = old_caps[aid]
        row = dict(ability_id=aid, thj_name=source['name'], source_classes=source['classes'],
                   thj_ranks=target, before=current)
        ledger.append(row)
        if aid not in abilities:
            row['decision'] = 'Custom THJ family absent from native catalog; implementation unspecified.'
            continue
        ability = abilities[aid]
        row.update(name=clean_name(ability['name']), classes=ability['classes'])
        chain = rank_chain(ability, ranks)
        same_chain = (len(source['ranks']) == target and
                      [r['ordinal'] for r in source['ranks']] == list(range(1,target+1)) and
                      [r['id'] for r in source['ranks']] == [r['id'] for r in chain[:target]])
        row['cost_differences'] = sum(a['cost'] != b['cost'] for a,b in zip(source['ranks'],chain))
        reason = EXCEPTIONS.get(aid)
        if not reason and aid in PRESERVED:
            reason = 'Preserve October18 pet/WPM reviewed ceiling and behavior.'
        if not reason and (not ability['enabled'] or ability['grant_only'] or ability['charges'] or ability['category'] in (3,4)):
            reason = 'Disabled duplicate, grant/reward-only or charged family; no generic import.'
        if not reason and aid in config['deferred_abilities']:
            reason = 'Retain reviewed execute/resource/charged-family deferral.'
        same_name = row['name'].casefold() == source['name'].casefold()
        if aid == 397:
            same_name = row['name'] == 'Destructive Fury' and source['name'] == 'Destructive Fury (Wizard)'
        if not reason and (not same_chain or not same_name):
            reason = 'Native name or exact rank identity mismatch.'
        if not reason and any(r['cost'] == 0 for r in chain[current:target]):
            reason = 'Preserve starter progression; added prefix contains free native ranks.'
        if reason:
            row['decision'] = reason
            continue
        config['rank_caps'][str(aid)] = max(current,target)
        if any(r['expansion'] > config['expansion_max'] for r in chain[:target]):
            config['later_exceptions'].append(aid)
        row['decision'] = 'Exact archived identity/count; native earned prices and effects retained.'
        row['requested'] = max(current,target)
    config['later_exceptions'] = sorted(set(config['later_exceptions']))
    rows = compile_policy(tables,config)
    caps = Counter(r['ability_id'] for r in rows)
    # Freeze resolved depth, including zero for blocked new chains. Future changes
    # cannot silently unlock an unreviewed dependency tail from this proposal.
    for row in ledger:
        aid = row['ability_id']
        if 'requested' in row:
            config['rank_caps'][str(aid)] = caps[aid]
            if caps[aid] < row['requested']:
                row['decision'] += ' Native prerequisite closure blocks the remaining ranks.'
        row['after'] = caps[aid]
    config['later_exceptions'] = sorted({r['ability_id'] for r in rows if r['expansion'] > config['expansion_max']})
    config['rank_caps'] = dict(sorted(config['rank_caps'].items(),key=lambda p:int(p[0])))
    assert compile_policy(tables,config) == rows
    assert {r['rank_id'] for r in old_rows} <= {r['rank_id'] for r in rows}, 'Released ranks removed'
    accepted = {r['ability_id'] for r in ledger if 'requested' in r}
    assert all(r['ability_id'] in accepted for r in rows if r['rank_id'] not in {x['rank_id'] for x in old_rows})
    return config,tables,old_rows,rows,ledger


def groups(tables):
    before = baseline()[1]
    return [dict(table='aa_ability',key={'id':389},
                 before=[next(r for r in before['aa_ability'] if r['id']==389)],
                 after=[next(r for r in tables['aa_ability'] if r['id']==389)])]


def coverage(rows,tables):
    rank_by_id = {r['id']:r for r in tables['aa_ranks']}
    families = {}
    # Match native timer-map candidate rule: any positive non-UNKNOWN spell.
    for r in rows:
        if 0 < rank_by_id[r['rank_id']]['spell'] < 65535:
            families[r['ability_id']] = r['classes']
    masks = [(sum(1<<i for i in combo),combo) for size in (1,2,3)
             for combo in itertools.combinations(range(16),size)]
    maximum = max((sum(bool(classes&mask) for classes in families.values()),combo)
                  for mask,combo in masks)
    all_families = {r['ability_id']:r['classes'] for r in rows}
    max_profile = max(sum(bool(classes&mask) for classes in all_families.values()) for mask,_ in masks)
    return dict(class_masks=len(masks),max_timer_slots=maximum[0],
                maximum_classes=[CLASSES[c] for c in maximum[1]],limit=100,
                max_profile_families=max_profile,profile_limit=300)


def changes(old_rows,rows):
    old, new = Counter(r['ability_id'] for r in old_rows), Counter(r['ability_id'] for r in rows)
    by_id = {r['ability_id']:r for r in rows}
    result=[]
    for aid in sorted(new):
        if old[aid] != new[aid]:
            r=by_id[aid]
            result.append(dict(id=aid,name=clean_name(r['name']),classes=r['classes'],
                               before=old[aid],after=new[aid],kind='Added' if not old[aid] else 'Changed'))
    return result


def report(old_rows,rows,ledger):
    delta=changes(old_rows,rows)
    added=sum(d['kind']=='Added' for d in delta)
    output=['# All-class AA changes — October19 live testing','',
        '**Deployed October19 for live testing; owner gameplay and balance acceptance pending.** Classic remains level50. Every allowed rank is available from level1 with earned points, held classes and prerequisites.', '',
        f'{len(old_rows)} → {len(rows)} available ranks; {len(set(r["ability_id"] for r in old_rows))} → {len(set(r["ability_id"] for r in rows))} AA lines. **{added} added lines, {len(delta)-added} expanded lines, no removals.**', '',
        '“Added” means newly available in Nightcap, not a newly invented ability. Rank counts are available ranks, not free grants. Native prices and effects remain. All shared lines are listed for each eligible class so each class list is complete.', '',
        '**Class access correction:** Druid receives Healing Boon (six ranks); Cleric, Paladin and Shaman retain it. Current pet/WPM ceilings, starter free-rank limits and all previously legal ranks remain.', '',
        '## Shared changes for all classes','']
    shared=[d for d in delta if d['classes']==65535]
    for d in shared:
        output.append(f'- **{d["kind"]}:** {d["name"]} — {d["before"]} → {d["after"]} ranks (ID{d["id"]}).')
    summary=[]
    for i,name in enumerate(CLASSES):
        class_delta=changes([r for r in old_rows if r['classes']&(1<<i)],
                            [r for r in rows if r['classes']&(1<<i)])
        own=[d for d in class_delta if d['classes']!=65535]
        output+=['',f'## {name}','', 'Also receives every shared change above.','']
        for kind in ('Added','Changed'):
            selected=[d for d in own if d['kind']==kind]
            output.append(f'**{kind}**')
            output.append('')
            for d in selected:
                output.append(f'- {d["name"]} — '+(f'{d["after"]} '+('rank' if d['after']==1 else 'ranks') if kind=='Added' else f'{d["before"]} → {d["after"]} ranks')+f' (ID{d["id"]}).')
            if not selected:output.append('- None.')
            output.append('')
        output.append('**Removed:** none.')
        summary.append(dict(class_name=name,added_lines=sum(d['kind']=='Added' for d in own),
                            expanded_lines=sum(d['kind']=='Changed' for d in own),shared_lines=len(shared),
                            added_ranks=sum(d['after']-d['before'] for d in class_delta)))
    output+=['','## Differences still requiring behavior work','',
        '- This is a rank/access update, not a claim that native AA effect values match every THJ customization. Read PLAN.md and the complete566-record disposition ledger.',
        '- Silent Casting remains native timing/class access; May7 one-minute reuse, one-hour duration and all-caster access are pending alongside Subtlety retirement/refunds.',
        '- Bard Dance of Blades uses native36-minute base reuse (24minutes with Hastened BladesIII), finite native duration and earned prices. The archived shorter range has no per-rank mapping.',
        '- Wizard Destructive Fury uses native nonstacking critical-damage values; combined caster classes take the maximum AA contribution. It does not add both Destructive Fury families.',
        '- Fixed-damage executes, free Touch/LoH/Hunter tails, Abundant Healing limits, custom/misidentified families, resource-burn rewrites and remaining prerequisite-blocked ranks stay excluded or retain their existing released depth.',
        '- April/May custom mechanics such as Warlord’s Fury, interruption-immunity Dimensional Shielding, Act of Valor, Gut Punch’s physical vulnerability and percentage mana conversions are not synthesized from incomplete native equivalents.', '',
        '## Sources','',
        '- [Pinned THJ AA builder](https://github.com/P1xt/thj-wiki/blob/c83d409370343adb30eb0e7e57b0e1149af7e6fa/aatracker.js)',
        '- [THJ forum / retained posts2671 and2845](https://www.firesofheaven.org/threads/the-heroes-journey-multiclass-eqemu-progression-server.15510/)',
        '- Retained Google notebook AAData, all16 class rows; local source manifest records archive inputs.', '']
    return '\n'.join(output),summary


def artifacts():
    config,tables,old,rows,ledger=prepare()
    listing,summary=report(old,rows,ledger)
    group=groups(tables)
    reverse=[{**g,'before':g['after'],'after':g['before']} for g in group]
    dump=lambda value:json.dumps(value,indent=2)+'\n'
    out={ROOT/'config/aa-policy.json':dump(config),
         ROOT/'server-mods/code/common/nightcap_aa_policy.h':header(rows,config,tables),
         RELEASE/'CHANGELIST.md':listing,
         RELEASE/'dispositions.json':dump(ledger),
         RELEASE/'summary.json':dump(dict(before_ranks=len(old),after_ranks=len(rows),
             changes=changes(old,rows),by_class=summary,cooldown_capacity=coverage(rows,tables))),
         RELEASE/'healing-boon-forward.sql':migration(group,'nightcap_allclass_aa_20261019'),
         RELEASE/'healing-boon-rollback.sql':migration(reverse,'nightcap_allclass_aa_rollback_20261019')}
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=('id','name','classes','before','after','kind'));writer.writeheader();writer.writerows(changes(old,rows))
    out[RELEASE/'changes.csv']=stream.getvalue()
    out[ROOT/config['catalog']]=gzip.compress(json.dumps(tables,separators=(',',':')).encode(),mtime=0)
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    for path,value in artifacts().items():
        if args.check:
            actual=path.read_bytes() if isinstance(value,bytes) else path.read_text(encoding='utf-8')
            # CSV uses CRLF; text reads normalize it on every platform.
            assert actual==(value if isinstance(value,bytes) else value.replace('\r\n','\n')), f'Stale artifact: {path}'
        elif isinstance(value,bytes):path.write_bytes(value)
        else:path.write_text(value,encoding='utf-8',newline='\n')
    print(json.dumps(read_json(RELEASE/'summary.json')['cooldown_capacity']))


if __name__=='__main__':main()
