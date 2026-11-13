"""Separate actual healing efficiency from the allocation of mana between spells."""
import csv
import json
from pathlib import Path
from statistics import median

HERE=Path(__file__).resolve().parent
rows=json.loads((HERE/"holdout.json").read_text())
assert len(rows)==80 and len({(r['rotation'],r['arm'],r['seed']) for r in rows})==80
result=[]
for name,first,last in (("initial",1713,1717),("holdout",1721,1725),("combined",1713,1725)):
    for rt in ("normal","cheapest_heal"):
        for arm in ("off","strike","healing","both"):
            data=[r for r in rows if first<=r["seed"]<=last and (rt,arm)==(r["rotation"],r["arm"])]
            m=lambda fn:round(median(fn(r) for r in data),3)
            hm=lambda r:r["mana_spent"].get(str(r["heal"]),0)
            nm=lambda r:r["mana_spent"].get(str(r["nuke"]),0)
            assert all(hm(r)>0 for r in data)
            result.append(dict(cohort=name,rotation=rt,arm=arm,n=len(data),
                hps=m(lambda r:1000*r["effective_heal"]/r["ms"]),
                hp_per_all_mana=m(lambda r:r["effective_heal"]/sum(r["mana_spent"].values())),
                hp_per_heal_mana=m(lambda r:r["effective_heal"]/hm(r)),heal_mana=m(hm),nuke_mana=m(nm),
                effective=m(lambda r:r["effective_heal"]),overheal=m(lambda r:r["overheal"]),
                burst_actual=m(lambda r:r["burst_actual"]),burst_requested=m(lambda r:r["burst_requested"]),
                hps_20s=m(lambda r:r["healing_20s"]/20),hps_60s=m(lambda r:r["healing_60s"]/60),
                dps_20s=m(lambda r:r["damage_20s"]/20),dps_60s=m(lambda r:r["damage_60s"]/60),
                kills=sum(r["outcome"]=="npc_death" for r in data),deaths=sum(r["outcome"]=="player_death" for r in data)))
with (HERE/"holdout-comparisons.csv").open("w",newline="") as out:
    writer=csv.DictWriter(out,fieldnames=result[0]);writer.writeheader();writer.writerows(result)
