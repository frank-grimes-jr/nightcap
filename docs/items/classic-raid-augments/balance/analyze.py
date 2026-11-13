"""Summarize same-seed native results; every failed or timed-out fight remains in the raw rows."""
import argparse
import collections
import csv
import gzip
import json
from pathlib import Path
from statistics import median

HERE=Path(__file__).resolve().parent
WINS={'npc_death','boss_death'}
SEEDS={1112,1113,1114}
NP={32040:'Lord Nagafen',72003:'Cazic-Thule',76007:'Innoruuk',71065:'Eye of Veeshan'}


def effective(row):
    stats=row['raid']
    return sum(stats[k] for k in ['ordinary_owner_heals','ordinary_pet_heals','mend','healed'])*1000/row['ms']


def aggregate(rows):
    groups=collections.defaultdict(list)
    for row in rows:
        assert row['aa_spent']==500 and row['end_measured']
        if row['role']=='pet':assert row['pet_roster']==3
        groups[row['role'],row['npc'],row['item']].append(row)
    out=[]
    for (role,npc,item),arm in sorted(groups.items()):
        assert len(arm)==len({r['seed'] for r in arm})
        if item<963200 or {r['seed'] for r in arm}!=SEEDS:continue
        controls={k[2]:v for k,v in groups.items() if k[:2]==(role,npc) and 0<k[2]<963200 and {r['seed'] for r in v}==SEEDS}
        if not controls:continue
        wins=lambda group:sum(r['result'] in WINS for r in group)
        kill=lambda group:median(r['ms'] for r in group)/1000
        hps=lambda group:median(effective(r) for r in group)
        kt=[i for i,arr in controls.items() if wins(arr)==len(SEEDS)]
        best=min(kt,key=lambda i:(kill(controls[i]),i)) if kt else None
        # A healing gate evaluated on comparable outcomes avoids comparing damage
        # demand in a 20-second fatal attempt with healing during a 10-minute win.
        outcomes=lambda group:tuple('win' if r['result'] in WINS else r['result'] for r in sorted(group,key=lambda r:r['seed']))
        hc=[i for i,arr in controls.items() if outcomes(arr)==outcomes(arm)]
        bestheal=max(hc,key=lambda i:(hps(controls[i]),-i)) if hc else None
        hbase=hps(controls[bestheal]) if bestheal is not None else None
        delta_kill=100*(kill(arm)/kill(controls[best])-1) if best and wins(arm)==3 else None
        delta_heal=100*(hps(arm)/hbase-1) if hbase else None
        empty=groups.get((role,npc,0),[])
        empty_ok=len(empty)==3 and outcomes(empty)==outcomes(arm)
        empty_hps=hps(empty) if empty_ok else None
        ekill=100*(kill(arm)/kill(empty)-1) if empty_ok and wins(arm)==3 else None
        eheal=100*(hps(arm)/empty_hps-1) if empty_hps else None
        out.append(dict(role=role,npc=npc,item=item,wins=wins(arm),deaths=sum(r['result']=='player_death' for r in arm),timeouts=sum(r['result']=='timeout' for r in arm),
            kill_hunt=best,hunt_median_kill_s=round(kill(controls[best]),3) if best else None,
            raid_median_kill_s=round(kill(arm),3) if wins(arm)==3 else None,kill_delta_pct=round(delta_kill,3) if delta_kill is not None else None,
            heal_hunt=bestheal,hunt_effective_hps=round(hbase,3) if hbase is not None else None,raid_effective_hps=round(hps(arm),3),
            heal_delta_pct=round(delta_heal,3) if delta_heal is not None else None,
            empty_kill_delta_pct=round(ekill,3) if ekill is not None else None,
            empty_heal_delta_pct=round(eheal,3) if eheal is not None else None,
            kill_flag=delta_kill is not None and delta_kill < -5,heal_flag=delta_heal is not None and delta_heal>5))
    return out


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('directory',type=Path,nargs='?',default=HERE)
    a=parser.parse_args()
    pairs=sorted(a.directory.glob('*-measured.jsonl'))
    if pairs:
        rows=[json.loads(l) for p in pairs for l in p.read_text().splitlines()]
        rows.sort(key=lambda r:(r['role'],r['npc'],r['item'],r['seed']))
    else:
        rows=json.loads(gzip.decompress((HERE/'measurements.json.gz').read_bytes()))
    summary=aggregate(rows)
    assert len(rows)==1104 and len(summary)==256, 'All four profiles, four bosses, 23 sockets and three seeds are required'
    for r in rows:
        assert r['raid']['absorbed']<=120*r['raid']['wards']
        active=[e for e in r['raid']['events'] if e[1]!=0]
        assert all(b[0]-a[0]>=89000 for a,b in zip(active,active[1:])), 'Timer uses native whole seconds'
        assert all(e[2]<=90 for e in active if e[1]==2)
        assert all(e[2]<=50 for e in active if e[1] in (3,4))
    if pairs:
        (HERE/'measurements.json.gz').write_bytes(gzip.compress(json.dumps(rows,separators=(',',':')).encode(),mtime=0))
    with (HERE/'comparisons.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
    print(len(rows),'runs',len(summary),'three-seed comparisons',sum(r['kill_flag'] for r in summary),'kill flags',sum(r['heal_flag'] for r in summary),'healing flags')


if __name__=='__main__':main()
