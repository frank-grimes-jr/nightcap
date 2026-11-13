"""Exact paired replay on the final worn group-heal correction in the isolated runtime."""
import json
from pathlib import Path
import subprocess
import os
from matrix import DRAGONS,R,compact

assert Path.cwd()==R
db=json.loads((R/"eqemu_config.json").read_text())["server"]["database"]
assert db["host"]=="nightcap-sympathetic-balance" and db["db"]=="nightcap_sympathetic_balance"
fixtures=json.loads((R/"fixtures.json").read_text())
checks=[]
for cohort in ("caster","tap"):
    old=[json.loads(x) for x in (R/f"prepared-final-rows-{cohort}-1713.jsonl").read_text().splitlines()]
    for key in [r for r in old if r["arm"] in ("off","both") and r["rotation"]=="normal" and r["tier"] in ("progression","stacked")]:
        b=fixtures[cohort+'-'+key["tier"]]
        e=dict(npc_id=key["boss"],npc_position=DRAGONS[key["boss"]],duration_ms=900000,
               return_to_melee=True,melee_specials=False,combat_policy="caster_heal",nuke=key["nuke"],
               heal=key["heal"],clicks=[610338,610150] if key["arm"]=="both" else [],cover=[60,61,64,80])
        src,out=R/"replay-input.json",R/"replay-output.json"
        src.write_text(json.dumps({"builds":[b],"encounter":e}))
        subprocess.run(["mysql","-h",db["host"],"-u",db["username"],db["db"],"-e",
                        f"DELETE FROM timers WHERE char_id={int(b['test_character_id'])}"],
                       env=dict(os.environ,MYSQL_PWD=db["password"]),check=True)
        subprocess.run([str(R/"balance-zone"),"tests:balance",str(src),str(out)],
                       env=dict(os.environ,NIGHTCAP_BALANCE_RNG_SEED="1713"),check=True)
        identify=("seed","cohort","tier","boss","rotation","arm","nuke","heal","heal_amount_tested")
        row=compact(json.loads(out.read_text()),{k:key[k] for k in identify})
        row=json.loads(json.dumps(row))
        assert row==key,[(k,row.get(k),key.get(k)) for k in row if row.get(k)!=key.get(k)]
        checks.append({k:key[k] for k in ("cohort","tier","boss","arm","seed")})
(R/"replay.json").write_text(json.dumps({"matches":len(checks),"cases":checks,
    "original":json.loads((R/"measured-build.json").read_text())["binary"],
    "final":json.loads((R/"build.json").read_text())["binary"]},indent=2)+"\n")
