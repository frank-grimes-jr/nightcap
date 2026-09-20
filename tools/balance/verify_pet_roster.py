"""Run real native pet controls in the pre-existing isolated balance database.

Requires the candidate diagnostic built in /tmp/nightcap-balance-pets-20260919.
Never writes peq. Reserves unused synthetic IDs and cleans only its own rows.
Evidence retains complete inputs and outputs, plus independently checked results.
"""
import argparse
import copy
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
from prepare_native import root_sql

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = "/tmp/nightcap-balance-pets-20260919"
SERVER = "akk-stack-eqemu-server-1"
DB = "nightcap_balance_20260912"
CLASS_SPELL = {10:166,11:443,13:633}
ARMOR = {166:([2],[1211,0,0,0,0,0,0,0]),443:([17],[0,1004,0,0,0,0,0,0]),633:([7],[0,0,1008,0,0,0,0,0])}

def call(args):
    p = subprocess.run(args,capture_output=True,timeout=120)
    if p.returncode:
        raise RuntimeError(p.stderr.decode(errors="replace")[-1500:])
    return p.stdout

def pets(state,owner):
    return {p["spell"]:p for p in state["pets"] if p["owner_id"]==owner and not p["depop"]}

def verify(output):
    probe=output["pet_probe"]; owner=probe["player_entity_id"]
    for action in probe["actions"]:
        before,after=action["before"],action["settled"]
        current=pets(after,owner); previous=pets(before,owner)
        assert len(current)==len([p for p in after["pets"] if p["owner_id"]==owner and not p["depop"]]), "Duplicate class summon"
        assert len(current)<=3
        refs={r["class"]:r["entity_id"] for r in after["class_pets"]}
        for cls,spell in CLASS_SPELL.items():
            assert refs[cls]==(current[spell]["entity_id"] if spell in current else 0), (cls,refs,current)
        if current:
            assert after["primary_pet"] in {p["entity_id"] for p in current.values()}
        request=action["input"]
        if "spell" in request:
            spell=request["spell"]
            assert spell in current, ("summon failed",request)
            if spell in previous: assert current[spell]["entity_id"]==previous[spell]["entity_id"], "Duplicate replaced pet"
        if "command" in request:
            command=request["command"]
            if command=="dismiss": assert not current; continue
            assert current.keys()==previous.keys()
            anchor=next(p for p in previous.values() if p["entity_id"]==before["primary_pet"])
            if command=="sit":
                want=0 if anchor["order"]==1 else 1
                assert all(p["appearance"]==want for p in current.values()), (command,current)
            if command=="guard": assert all(p["order"]==2 for p in current.values())
            if command=="follow": assert all(p["order"]==0 for p in current.values())
            if command in ["taunt","stop"]:
                assert all(p[command]==(not anchor[command]) for p in current.values()), command
            if command in ["hold","ghold","spellhold","focus","regroup"]:
                key={"hold":"held","ghold":"gheld","spellhold":"no_cast","focus":"focused","regroup":"regroup"}[command]
                assert all(not p[key] for p in current.values()), "AA-gated command was granted without AA"
        lifecycle=request.get("lifecycle")
        if lifecycle=="roundtrip":
            assert current.keys()==previous.keys()
            for spell,p in current.items():
                assert p["hp"]>=previous[spell]["hp"], ("Lost HP during restore",spell,p["hp"],previous[spell]["hp"])
                assert p["mana"]>=previous[spell]["mana"], ("Lost mana during restore",spell)
        if lifecycle=="depop_representative":
            assert len(current)==len(previous)-1
            assert after["primary_pet"]!=before["primary_pet"]
        if lifecycle=="inspect_underlying_armor":
            assert current[166]["legacy_items"][0]==1001, "Original underlying gear lost"
        else:
            for spell,p in current.items():
                assert p["armor_slots"]==ARMOR[spell][0], ("Wrong armor class",spell,p["armor_slots"])

    # Singular buff packets must always describe the last selected live anchor.
    anchor=0
    for event in probe["events"]:
        if event["type"]=="pet_anchor": anchor=event["pet"] if event["command"] else 0
        if event["type"]=="pet_buffs": assert event["pet"]==anchor, ("Mixed pet window",event,anchor)
    return {"actions":len(probe["actions"]),"final_pets":len(pets(probe["final"],owner)),"anchor_packets":sum(e["type"]=="pet_anchor" for e in probe["events"])}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--limit",type=int,default=36)
    args=parser.parse_args()
    if not 1<=args.limit<=36: raise ValueError("Limit must be 1..36")
    args.output.mkdir(parents=True,exist_ok=True)
    source=json.loads((ROOT/"docs/balance/pet-ownership-inputs.json").read_text())
    base=next(c["input"] for c in source["cases"] if c["id"]=="triple-0")
    binary_sha=call(["docker","exec",SERVER,"sha256sum",RUNTIME+"/balance-zone"]).decode().split()[0]
    results=[]
    cases=list(itertools.product(itertools.permutations([10,11,13]),itertools.permutations([166,443,633])))[:args.limit]
    for index,(classes,summons) in enumerate(cases):
        char=980010+index
        # Explicit unused-ID guard across every table we will write.
        tables={"character_multiclass":"character_id","character_pet_armor":"character_id","character_pet_info":"char_id","character_pet_buffs":"char_id","character_pet_inventory":"char_id","character_data":"id"}
        counts = "+".join(f"(SELECT COUNT(*) FROM {DB}.{table} WHERE {key}={char})" for table,key in tables.items())
        assert root_sql("SELECT "+counts+";").decode().strip()=="0", "Reserved test ID already in use"

        inp=copy.deepcopy(base); build=inp["builds"][0]
        build["classes"]=list(classes); build["test_character_id"]=char
        actions=[{"spell":s} for s in summons]+[{"spell":443}]
        actions += [{"command":c} for c in ["sit","sit","guard","follow","taunt","taunt","stop","stop","hold","ghold","spellhold","focus","regroup"]]
        actions += [{"lifecycle":c} for c in ["seed_native_armor","roundtrip","inspect_underlying_armor","suspend","roundtrip","suspend","depop_representative"]]
        actions += [{"command":"sit"},{"command":"dismiss"}]
        inp["pet_probe"]["actions"]=actions
        inp["pet_probe"]["retry_native_fizzles"]=True
        name=f"case-{index:02d}"; local=args.output/(name+"-input.json")
        local.write_text(json.dumps(inp,indent=2)+"\n")
        try:
            root_sql(f"USE {DB}; INSERT INTO character_multiclass(character_id,class2,class3) VALUES({char},{classes[1]},{classes[2]}); "
                f"INSERT INTO character_pet_armor(character_id,pet_class,slot_id,item_id,charges) VALUES({char},10,2,1211,1),({char},11,17,1004,1),({char},13,7,1008,1);")
            call(["docker","cp",str(local),f"{SERVER}:{RUNTIME}/{name}-input.json"])
            run=subprocess.run(["docker","exec","-w",RUNTIME,"-e","NIGHTCAP_BALANCE_RNG_SEED=1729",SERVER,
                f"{RUNTIME}/balance-zone","tests:balance",f"{RUNTIME}/{name}-input.json",f"{RUNTIME}/{name}-output.json"],capture_output=True,timeout=120)
            (args.output/(name+".log")).write_bytes(run.stdout+run.stderr)
            assert run.returncode==0, f"Native run failed: {name}; see evidence log"
            raw=call(["docker","exec",SERVER,"cat",f"{RUNTIME}/{name}-output.json"])
            (args.output/(name+"-output.json.gz")).write_bytes(gzip.compress(raw,mtime=0))
            assert call(["docker","exec",SERVER,"sha256sum",RUNTIME+"/balance-zone"]).decode().split()[0]==binary_sha, "Diagnostic binary changed during run"
            checked=verify(json.loads(raw))
            results.append({"case":name,"classes":classes,"summons":summons,**checked})
            print(json.dumps(results[-1]),flush=True)
            (args.output/"summary.json").write_text(json.dumps({"binary_sha256":binary_sha,"passed":len(results),"cases":results},indent=2)+"\n")
        finally:
            root_sql("USE "+DB+"; "+" ".join(f"DELETE FROM {table} WHERE {key}={char};" for table,key in tables.items() if table!="character_data"))

if __name__=="__main__": main()
