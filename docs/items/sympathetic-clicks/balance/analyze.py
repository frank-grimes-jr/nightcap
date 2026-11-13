"""Summarize all attempts, paired by native RNG seed, preserving deaths and timeouts."""
from collections import Counter, defaultdict
import csv
import gzip
import json
from pathlib import Path
from statistics import median
from itertools import product

HERE = Path(__file__).resolve().parent


def metrics(row):
    seconds=row["ms"]/1000
    mana=sum(row["mana_spent"].values())
    return {"dps":row["damage"]/seconds,"hps":row["effective_heal"]/seconds,
            "damage_per_mana":row["damage"]/mana if mana else 0,
            "healing_per_mana":row["effective_heal"]/mana if mana else 0,
            "spent":mana,"net_mana":row["initial_mana"]-row["end_mana"],
            "overheal":row["overheal"],"seconds":seconds,"min_mana":row["min_mana"],
            "strike":row["strike_damage"],"burst_heal":row["burst_actual"],
            "strike_contribution_pct":100*row["strike_damage"]/max(1,row["damage"]-row["strike_damage"]),
            "healing_contribution_pct":100*row["burst_actual"]/max(1,row["effective_heal"]-row["burst_actual"])}


def summarize(rows):
    groups=defaultdict(list)
    for row in rows:
        groups[tuple(row[k] for k in ("variant","cohort","tier","boss","rotation","arm"))].append(row)
    result=[]
    for key,rs in sorted(groups.items()):
        variant,cohort,tier,boss,rotation,arm=key
        base=groups[variant,cohort,tier,boss,rotation,"off"]
        lookup={r["seed"]:r for r in base}
        assert len(rs)==len({r["seed"] for r in rs}) and {r["seed"] for r in rs}<=set(lookup)
        m=[metrics(r) for r in rs]
        outcomes=Counter(r["outcome"] for r in rs)
        line=dict(variant=variant,cohort=cohort,tier=tier,boss=boss,rotation=rotation,arm=arm,n=len(rs),
                  aa=rs[0]["aa_spent"],sd=rs[0]["sd"],ha=rs[0]["ha"],
                  kills=outcomes["npc_death"],deaths=outcomes["player_death"],timeouts=outcomes["timeout"])
        for k in m[0]:
            line[k]=round(median(x[k] for x in m),4)
        for k in ("dps","hps","damage_per_mana","healing_per_mana"):
            ratios=[]
            for r in rs:
                denominator=metrics(lookup[r["seed"]])[k]
                if denominator>0:ratios.append(100*(metrics(r)[k]/denominator-1))
            line[k+"_paired_pct"]=round(median(ratios),3) if ratios else None
        result.append(line)
    return result


def check_final(rows):
    bosses=(32040,73057)
    expected=set()
    for profile,stage,boss,seed in product(("caster","tap"),("progression","stacked","cap_stress"),bosses,range(1713,1718)):
        rotations=["normal","fast_tap"] if profile=="tap" else ["normal","fast_nuke","cheapest_heal"]+(["fast_cold"] if boss==32040 else [])
        for rotation in rotations:
            arms=("off","both","strike","healing") if rotation=="normal" and stage!="cap_stress" else ("off","both")
            expected.update((profile,stage,boss,seed,rotation,arm) for arm in arms)
    keys=[tuple(r[k] for k in ("cohort","tier","boss","seed","rotation","arm")) for r in rows]
    assert len(keys)==len(set(keys)) and set(keys)==expected
    for r in rows:
        assert r["cover_buffs"]==4
        assert r["aa_spent"]==(100 if r["tier"]=="progression" else 3463 if r["cohort"]=="caster" else 3059)
        assert r["sd"]==r["ha"]=={"progression":100,"stacked":400,"cap_stress":750}[r["tier"]]
        assert r["burst_requested"]<=48*r["burst_count"]
        assert r["strike_damage"]<=48*r["damaging_events"].get("44379",0)
        if r["arm"] in ("off","healing"): assert r["strike_damage"]==0 and r["strike_last_ms"] is None
        if r["arm"] in ("off","strike"): assert r["burst_count"]==0 and r["healing_last_ms"] is None
    assert any(r["strike_damage"]>0 for r in rows) and any(r["burst_actual"]>0 for r in rows)


def write_windows(rows):
    identify=lambda r:tuple(r[k] for k in ("cohort","tier","boss","rotation","seed"))
    off={identify(r):r for r in rows if r["arm"]=="off"}
    records=[]
    for r in rows:
        if r["arm"]!="both":continue
        other=off[identify(r)]
        for seconds in (20,60):
            line={k:r[k] for k in ("cohort","tier","boss","rotation","seed")}
            line.update(seconds=seconds,off_survived=other["ms"]>=seconds*1000,both_survived=r["ms"]>=seconds*1000)
            for short,key in (("dps","damage"),("hps","healing")):
                field=f"{key}_{seconds}s"
                for side,arm in (("off",other),("both",r)):
                    line[side+"_"+short]=round(arm[field]/seconds,3) if field in arm else None
                line["delta_"+short]=round((r[field]-other[field])/seconds,3) if field in r and field in other else None
            records.append(line)
    with (HERE/"matched-windows.csv").open("w",newline="") as out:
        writer=csv.DictWriter(out,fieldnames=records[0]);writer.writeheader();writer.writerows(records)


if __name__=="__main__":
    archive=HERE/"measurements.json.gz"
    rows=json.loads(gzip.decompress(archive.read_bytes()))
    check_final([r for r in rows if r["variant"]=="bounded48"])
    write_windows([r for r in rows if r["variant"]=="bounded48"])
    result=summarize(rows)
    with (HERE/"comparisons.csv").open("w",newline="") as out:
        writer=csv.DictWriter(out,fieldnames=result[0].keys());writer.writeheader();writer.writerows(result)
