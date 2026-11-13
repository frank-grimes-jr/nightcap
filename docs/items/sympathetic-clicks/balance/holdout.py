"""Isolate the two clicks in both original and previously unused Vox seeds."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
from matrix import DRAGONS,R,compact,ARMS

assert Path.cwd()==R
database=json.loads((R/"eqemu_config.json").read_text())["server"]["database"]
assert database["host"]=="nightcap-sympathetic-balance" and database["db"]=="nightcap_sympathetic_balance"
build=json.loads((R/"fixtures.json").read_text())["caster-stacked"]

def run(seed):
    first_seed=1721 if seed>=1721 else 1713
    b=dict(build,test_character_id=97102+(seed-first_seed)*100)
    rows=[]
    for rotation,heal in (("normal",9),("cheapest_heal",200)):
        for arm,clicks in ARMS.items():
            e=dict(npc_id=73057,npc_position=DRAGONS[73057],duration_ms=900000,return_to_melee=True,
                   melee_specials=False,combat_policy="caster_heal",nuke=659,heal=heal,clicks=clicks,cover=[60,61,64,80])
            inp,out=R/f"holdout-{seed}-in.json",R/f"holdout-{seed}-out.json"
            inp.write_text(json.dumps({"builds":[b],"encounter":e}))
            subprocess.run(["mysql","-h",database["host"],"-u",database["username"],database["db"],"-e",
                            f"DELETE FROM timers WHERE char_id={int(b['test_character_id'])}"],
                           env=dict(os.environ,MYSQL_PWD=database["password"]),check=True)
            subprocess.run([str(R/"balance-zone"),"tests:balance",str(inp),str(out)],
                           env=dict(os.environ,NIGHTCAP_BALANCE_RNG_SEED=str(seed)),check=True)
            key=dict(seed=seed,cohort="caster",tier="stacked",boss=73057,rotation=rotation,arm=arm,
                     nuke=659,heal=heal,heal_amount_tested=48)
            raw=json.loads(out.read_text())
            row=compact(raw,key)
            ledger=raw["encounter"]["player_ledger"]["healing"]
            row["ordinary_direct_requested_histogram"]={}
            for ev in ledger:
                if ev["spell"]==65535:
                    amount=str(ev["requested"])
                    row["ordinary_direct_requested_histogram"][amount]=row["ordinary_direct_requested_histogram"].get(amount,0)+1
            rows.append(row)
    return rows

with ThreadPoolExecutor(5) as pool:
    records=[]
    for sample in (range(1713,1718),range(1721,1726)):
        records.extend(r for cohort in pool.map(run,sample) for r in cohort)
(R/"holdout.json").write_text(json.dumps(records,separators=(",",":"))+"\n")
