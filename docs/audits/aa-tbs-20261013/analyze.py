"""Offline AA inventory and conservative prerequisite closure; never changes PEQ.

Counts describe class-mask eligibility, not race/client/activation or combat QA.
Missing prerequisites block the proposed legal pool, even where native purchase
skips an absent ability. Grant-only ranks never satisfy an unearned prerequisite.
"""
import collections
import csv
import gzip
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CLASSES = 'WAR CLR PAL RNG SHD DRU MNK BRD ROG SHM NEC WIZ MAG ENC BST BER'.split()


class Catalog:
    def __init__(self, tables):
        self.tables = tables
        self.abilities = {a['id']: a for a in tables['aa_ability']}
        self.ranks = {r['id']: r for r in tables['aa_ranks']}
        self.spells = {s['id']: s for s in tables.get('spells', [])}
        self.effects = collections.defaultdict(list)
        self.prereqs = collections.defaultdict(dict)
        self.chains = {}
        self.issues = []
        owners = collections.defaultdict(list)
        for e in tables.get('aa_rank_effects', []):
            if e['slot'] > 0:
                self.effects[e['rank_id']].append(e)
        for p in tables.get('aa_rank_prereqs', []):
            if p['aa_id'] > 0 and p['points'] > 0:
                self.prereqs[p['rank_id']][p['aa_id']] = p['points']
        for aid, a in self.abilities.items():
            rid, seen, chain, inherited = a['first_rank_id'], set(), [], {}
            while rid in self.ranks:
                if rid in seen:
                    raise ValueError(f'Cycle in {aid} at {rid}')
                seen.add(rid)
                r = dict(self.ranks[rid])
                for dep, count in self.prereqs[rid].items():
                    inherited[dep] = max(inherited.get(dep, 0), count)
                r['prereqs'] = dict(inherited)
                r['ordinal'] = len(chain) + 1
                chain.append(r)
                if a['enabled']:
                    owners[rid].append(aid)
                rid = r['next_id']
            if rid >= 0:
                self.issues.append({'ability_id': aid, 'missing_tail': rid})
            self.chains[aid] = chain
        shared = {k:v for k,v in owners.items() if len(v)>1}
        if shared:
            raise ValueError(f'Shared enabled ranks: {shared}')

    def eligible(self, a, mask, paid=True):
        return (a['id'] != 0 and a['enabled'] == 1 and a['classes'] & mask
                and a['category'] not in (3,4) and a['status'] == 0
                and (not paid or not a['grant_only']))

    def pool(self, mask=65535, cutoff=99, level=50, overrides=None):
        candidates = {}
        for aid, a in self.abilities.items():
            if not self.eligible(a,mask):
                continue
            prefix = []
            for r in self.chains[aid]:
                if r['expansion'] > cutoff or r['level_req'] > level:
                    break
                if overrides is not None and len(prefix) >= overrides.get(str(aid),0):
                    break
                prefix.append(r)
            if prefix:
                candidates[aid] = prefix
        counts = collections.defaultdict(int)
        changed = True
        while changed:
            changed = False
            for aid, chain in candidates.items():
                n = counts[aid]
                if n == len(chain):
                    continue
                r = chain[n]
                if all(counts[dep] >= need for dep,need in r['prereqs'].items()):
                    counts[aid] += 1
                    changed = True
        retained = {aid: chain[:counts[aid]] for aid,chain in candidates.items() if counts[aid]}
        blocked = []
        for aid,chain in candidates.items():
            if counts[aid] < len(chain):
                r = chain[counts[aid]]
                blocked.append({'ability_id':aid,'name':self.abilities[aid]['name'],
                                'rank_id':r['id'],'ordinal':r['ordinal'],
                                'unmet':{str(k):v for k,v in r['prereqs'].items() if counts[k]<v}})
        return retained, blocked

    def stats(self, pool):
        return {'families':len(pool),'ranks':sum(len(v) for v in pool.values()),
                'points':sum(r['cost'] for chain in pool.values() for r in chain),
                'spell_linked_families':sum(any(r['spell'] in self.spells for r in chain) for chain in pool.values())}


def write_csv(path, rows):
    if not rows:
        return
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    raw=(HERE/'production-snapshot.json.gz').read_bytes()
    snap=json.loads(gzip.decompress(raw))
    c=Catalog(snap['tables'])
    text=(ROOT/'akk-stack/code/common/spdat.h').read_text()
    effect_names={int(n):name for name,n in re.findall(r'constexpr int\s+(\w+)\s*=\s*(\d+);',text.split('namespace SpellEffect {',1)[1])}
    counts=[]
    blocked={}
    profiles={name:1<<i for i,name in enumerate(CLASSES)}
    profiles.update({'WAR/CLR/WIZ':(1<<0)|(1<<1)|(1<<11),
                     'WAR/CLR/MNK':(1<<0)|(1<<1)|(1<<6),
                     'MAG/NEC/SHM':(1<<12)|(1<<10)|(1<<9),
                     'PAL/WAR/MNK':(1<<2)|(1<<0)|(1<<6),
                     'SHD/SHM/BRD':(1<<4)|(1<<9)|(1<<7),
                     'RNG/DRU/ENC':(1<<3)|(1<<5)|(1<<13),
                     'ALL_CLASSES_UNION':65535})
    for name,mask in profiles.items():
        all_pool, all_blocked=c.pool(mask)
        tbs,tbs_blocked=c.pool(mask,13)
        x={'profile':name}
        for prefix,pool in [('open',all_pool),('tbs',tbs)]:
            x.update({prefix+'_'+k:v for k,v in c.stats(pool).items()})
        x['family_reduction_percent']=round(100*(1-len(tbs)/len(all_pool)),2)
        counts.append(x)
        blocked[name]={'open':all_blocked,'tbs':tbs_blocked}
    all_pool,_=c.pool()
    tbs,_=c.pool(cutoff=13)
    families=[]
    ranks=[]
    for aid,a in sorted(c.abilities.items()):
        chain=c.chains[aid]
        if not chain:
            continue
        kept=tbs.get(aid,[])
        late=[r for r in chain if r['expansion']>13]
        f={'ability_id':aid,'name':a['name'],'enabled':a['enabled'],
           'classes':'/'.join(k for i,k in enumerate(CLASSES) if a['classes']&(1<<i)),
           'first_rank_id':chain[0]['id'],'first_expansion':chain[0]['expansion'],
           'grant_only':a['grant_only'],'charges':a['charges'],
           'native_ranks':len(chain),'legal_open_ranks':len(all_pool.get(aid,[])),
           'tbs_ranks':len(kept),'tbs_top_rank_id':kept[-1]['id'] if kept else '',
           'tbs_cost':sum(r['cost'] for r in kept),'post_tbs_ranks':len(late),
           'first_later_rank_id':late[0]['id'] if late else '',
           'first_later_ordinal':late[0]['ordinal'] if late else '',
           'tbs_top_effects':'; '.join(f"{effect_names.get(e['effect_id'],e['effect_id'])}={e['base1']}/{e['base2']}" for e in c.effects[kept[-1]['id']]) if kept else '',
           'first_later_effects':'; '.join(f"{effect_names.get(e['effect_id'],e['effect_id'])}={e['base1']}/{e['base2']}" for e in c.effects[late[0]['id']]) if late else '',
           'first_later_spell':c.spells.get(late[0]['spell'],{}).get('name','') if late else '',
           'first_later_cooldown':late[0]['recast_time'] if late else ''}
        families.append(f)
        for r in chain:
            ranks.append({'ability_id':aid,'name':a['name'],'ordinal':r['ordinal'],
                          **{k:r[k] for k in ('id','cost','level_req','expansion','spell','recast_time')},
                          'legal_tbs':r in kept,'prereqs':json.dumps(r['prereqs'],sort_keys=True),
                          'effects':'; '.join(f"{effect_names.get(e['effect_id'],e['effect_id'])}={e['base1']}/{e['base2']}" for e in c.effects[r['id']])})
    purchases=collections.Counter()
    expansion_purchases=collections.Counter()
    first={a['first_rank_id']:aid for aid,a in c.abilities.items() if a['enabled']}
    for row in snap['tables']['purchases_aggregate']:
        aid=first.get(row['first_rank_id'])
        if aid is None or row['rank_count'] < 1 or row['rank_count'] > len(c.chains[aid]):
            expansion_reason='unresolved'
        else:
            purchased=c.chains[aid][:row['rank_count']]
            expansion_reason=('above_TBS_expansion' if any(r['expansion']>13 for r in purchased)
                              else 'within_TBS_expansion')
        expansion_purchases[expansion_reason]+=row['rows']
        if aid is None:
            reason='unresolved'
        elif row['rank_count']>len(c.chains[aid]):
            reason='beyond_chain'
        elif row['rank_count']>len(tbs.get(aid,[])):
            reason='above_tbs_cap' if tbs.get(aid) else 'outside_tbs_purchase_pool'
        else:
            reason='within_tbs_global_cap'
        purchases[reason]+=row['rows']
    report={'captured_at':snap['captured_at'],'snapshot_sha256':hashlib.sha256(raw).hexdigest(),
            'method':'Enabled normal-player families; no shrouds/placeholder/grant-only. Sequential prefix and inherited prerequisite closure. All class masks include shared families only once. No race/deity restrictions in this snapshot. Charge families counted once, not repeat spending.',
            'counts':counts,'raw_expansions':dict(sorted(collections.Counter(r['expansion'] for r in c.ranks.values()).items())),
            'raw_levels':dict(collections.Counter(r['level_req'] for r in c.ranks.values())),
            'rules':snap['tables']['rules'],'blocked':blocked,'chain_issues':c.issues,
            'purchase_rows':dict(purchases),
            'purchase_rows_by_expansion_only':dict(expansion_purchases),
            'later_new_families':sum(f['first_expansion']>13 and bool(f['legal_open_ranks']) for f in families),
            'older_families_with_later_ranks':sum(f['tbs_ranks']>0 and f['post_tbs_ranks']>0 for f in families)}
    (HERE/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    write_csv(HERE/'class-coverage.csv',counts)
    write_csv(HERE/'families.csv',families)
    write_csv(HERE/'ranks.csv',ranks)
    print(json.dumps({k:v for k,v in report.items() if k not in ('blocked','chain_issues','rules')},indent=2))


if __name__=='__main__':
    main()
