"""Create the pinned rotation fixtures on the host; run independent paired dragon encounters inside the fixture."""
import argparse
import collections
import copy
import sys
import json
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
R = Path("/tmp/nightcap-balance-sympathetic")
SEEDS = (1713,1714,1715,1716,1717)
DRAGONS = {32040: [-871,-1395,104.879997,45], 73057: [-262,857,22,407]}
ARMS = {"off": [], "strike": [610338], "healing": [610150], "both": [610338,610150]}


def templates(catalogs):
    root = HERE.parents[3]
    sys.path.insert(0,str(root/"tools/balance"))
    from aa_allocations import Purchases
    prior = root / "docs/items/classic-raid-augments/balance/fixtures.json"
    base = json.loads(prior.read_text())
    gear = json.loads((root/"docs/balance/candidate-builds.json").read_text())["builds"]
    out = {}
    for cohort,src in [("caster","spell"),("tap","pet")]:
        ranks = json.loads((catalogs/(src+"-catalog.json")).read_text())
        def spend(limit):
            state=Purchases(ranks)
            state.free_closure()
            priority=[28,33,34,20,224,18,19,30,189,108,23,114,215,397,398]
            while True:
                legal=[r for r in ranks if not state.reasons(r) and state.spent+r["cost"]<=limit]
                if not legal:break
                state.buy(min(legal,key=lambda r:(priority.index(r["ability_id"]) if r["ability_id"] in priority else 100,
                                                  r["cost"],r["rank"],r["rank_id"])))
            return state
        for stage in ("progression","stacked","cap_stress"):
            b = copy.deepcopy(base[src]["builds"][0])
            b["test_character_id"] = 97102 if cohort=="caster" else 97104
            if stage=="progression":
                worn = next(row["equipment"] for row in gear if row["profile"]==b["profile"] and row["tier"]=="Polished")
                b["equipment"]=[{"slot":x["slot"],"id":x["id"]} for x in worn]
            state=spend(100 if stage=="progression" else 100000)
            b.update(aa_budget=state.spent,aa_rank_ids=state.ids,aa_policy="native curated purchase gates")
            b["tier"]=stage
            out[cohort+"-"+stage]=b
    (HERE/"fixtures.json").write_text(json.dumps(out,indent=2)+"\n")


def compact(result, key):
    b = result["builds"][0]
    e = result["encounter"]
    hp = lambda v:max(0,v)
    def loss(event):
        return hp(hp(event["hp_before"])-hp(event["hp_after"]))
    dmg = [ev for ev in e["damage_ledger"] if ev["source"]==e["player_entity_id"] and ev["depth"]==0]
    heals = e["player_ledger"]["healing"]
    t = e["trace"]
    spent = dict(result["mana_spent_by_spell"])
    row = dict(key,ms=e["elapsed_ms"],outcome=e["result"],initial_hp=t[0]["player_hp"],
               initial_mana=t[0]["player_mana"],end_hp=t[-1]["player_hp"],end_mana=t[-1]["player_mana"],
               min_mana=min(x["player_mana"] for x in t),mana_spent=spent,
               boss_end_hp=t[-1]["npc_hp"],aa_spent=b["aa_spent"],sd=b["spell_damage"],ha=b["heal_amount"])
    row["native_seed"]=result["native_rng_seed"]
    assert row["native_seed"]==row["seed"]
    if "native_seed_hook_calls" in result: assert result["native_seed_hook_calls"]>0
    assert t[0]["npc_hp"]==32000 and row["ms"]>0
    if "strike" in t[0]:
        row["cover_buffs"]=t[0]["cover_buffs"]
        row["strike_last_ms"]=max((x["ms"] for x in t if x["strike"]),default=None)
        row["healing_last_ms"]=max((x["ms"] for x in t if x["healing"]),default=None)
    row["damage"]=sum(map(loss,dmg))
    row["damaging_events"]=dict(collections.Counter(ev["spell"] for ev in dmg if loss(ev)>0))
    row["effective_heal"]=sum(hp(ev["healed"]) for ev in heals)
    row["overheal"]=sum(max(0,ev["requested"]-hp(ev["healed"])) for ev in heals)
    row["heal_by_spell"]={s:[sum(hp(x["healed"]) for x in heals if x["spell"]==s),
                             sum(x["requested"] for x in heals if x["spell"]==s)]
                          for s in sorted({x["spell"] for x in heals})}
    row["strike_damage"]=sum(loss(ev) for ev in dmg if ev["spell"]==44379)
    burst=[ev for ev in heals if ev["spell"]==44380]
    row["burst_count"]=len(burst)
    row["burst_requested"]=sum(ev["requested"] for ev in burst)
    row["burst_actual"]=sum(hp(ev["healed"]) for ev in burst)
    assert not row["burst_count"] or row["arm"] in ("healing","both")
    for seconds in (20,60):
        window=seconds*1000
        if row["ms"]>=window:
            row[f"damage_{seconds}s"]=sum(loss(ev) for ev in dmg if ev["ms"]<=window)
            row[f"healing_{seconds}s"]=sum(hp(ev["healed"]) for ev in heals if ev["ms"]<=window)
    return row


def run(seed, cohort, baseline, larger, pilot, unprepared, final=False):
    assert Path.cwd()==R
    db=json.loads((R/"eqemu_config.json").read_text())["server"]["database"]
    assert (db["host"],db["db"],db["username"])==("nightcap-sympathetic-balance","nightcap_sympathetic_balance","sympathetic_fixture")
    fixtures=json.loads((R/"fixtures.json").read_text())
    out=R/(("" if unprepared else "prepared-")+("final-" if final else "base-" if baseline else "large-" if larger else "")+f"rows-{cohort}-{seed}.jsonl")
    done={tuple(json.loads(line)[k] for k in ("tier","boss","rotation","arm")) for line in out.read_text().splitlines()} if out.exists() else set()
    for stage in ("progression","stacked","cap_stress"):
        b=dict(fixtures[cohort+"-"+stage])
        b["test_character_id"] += 100*(seed-SEEDS[0])
        for boss,position in DRAGONS.items():
            normal_nuke=(732 if boss==32040 else 659) if cohort=="caster" else 447
            normal_heal=9 if cohort=="caster" else 15
            # The fire-immune dragon also gets the quickest cold control.
            rotations={"normal":(normal_nuke,normal_heal)}
            if cohort=="caster":
                rotations.update(fast_nuke=(376,normal_heal),cheapest_heal=(normal_nuke,200))
                if boss==32040: rotations["fast_cold"]=(656,normal_heal)
            else:
                rotations["fast_tap"]=(502,normal_heal)
            for rotation,(nuke,heal) in rotations.items():
                for arm,clicks in ARMS.items():
                    if baseline and arm!="off":continue
                    if pilot and (stage=="cap_stress" or arm not in ("off","both")):continue
                    if stage=="cap_stress" and arm not in ("off","both"):continue
                    if rotation!="normal" and arm not in ("off","both"):continue
                    if (stage,boss,rotation,arm) in done:continue
                    e={"npc_id":boss,"npc_position":position,"duration_ms":900000,"return_to_melee":True,
                       "melee_specials":False,"combat_policy":"caster_heal","nuke":nuke,"heal":heal,"clicks":clicks}
                    if not unprepared:
                        e["cover"]=[60,61,64,80]
                    case=R/f"input-{cohort}-{seed}.json"
                    result=R/f"result-{cohort}-{seed}.json"
                    case.write_text(json.dumps({"builds":[b],"encounter":e}))
                    subprocess.run(["mysql","-h",db["host"],"-u",db["username"],db["db"],"-e",
                                    f"DELETE FROM timers WHERE char_id={int(b['test_character_id'])}"],
                                   env=dict(os.environ,MYSQL_PWD=db["password"]),check=True)
                    if result.exists():result.unlink()
                    with (R/f"current-{cohort}-{seed}.log").open("w") as log:
                        subprocess.run([str(R/("baseline-zone" if baseline else "balance-zone")),"tests:balance",str(case),str(result)],
                                       env=dict(os.environ,NIGHTCAP_BALANCE_RNG_SEED=str(seed),
                                                NIGHTCAP_BALANCE_LARGER_RANK="1" if larger else "0",
                                                NIGHTCAP_BALANCE_CAP_STRESS="1" if stage=="cap_stress" else "0"),
                                       stdout=log,stderr=subprocess.STDOUT,check=True)
                    key=dict(seed=seed,cohort=cohort,tier=stage,boss=boss,rotation=rotation,
                             arm=arm,nuke=nuke,heal=heal,heal_amount_tested=48 if larger or final else 12)
                    row=compact(json.loads(result.read_text()),key)
                    with out.open("a") as stream:stream.write(json.dumps(row)+"\n")
                    print(stage,boss,rotation,arm,row["outcome"],row["ms"],flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=["templates","run","batch"])
    parser.add_argument("--seed",type=int,choices=SEEDS)
    parser.add_argument("--cohort",choices=["caster","tap"])
    parser.add_argument("--catalogs",type=Path)
    parser.add_argument("--baseline",action="store_true")
    parser.add_argument("--larger",action="store_true")
    parser.add_argument("--pilot",action="store_true")
    parser.add_argument("--unprepared",action="store_true")
    parser.add_argument("--final",action="store_true")
    opts=parser.parse_args()
    if opts.action=="templates":templates(opts.catalogs)
    elif opts.action=="run":run(opts.seed,opts.cohort,opts.baseline,opts.larger,opts.pilot,opts.unprepared,opts.final)
    else:
        # Each worker owns a synthetic character and runs both amounts sequentially.
        def sequence(job):
            cohort,seed=job
            if opts.final:
                run(seed,cohort,False,False,False,False,True)
            else:
                for larger in (True,False):
                    run(seed,cohort,False,larger,seed>1715,False)
        with ThreadPoolExecutor(6) as pool:
            list(pool.map(sequence,[(c,s) for s in SEEDS for c in ("caster","tap")]))
