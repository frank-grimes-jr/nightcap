"""Native load/recall tests for old and class-keyed suspended pet saves."""
import argparse,copy,gzip,json,subprocess
from pathlib import Path
from prepare_native import root_sql
from verify_pet_roster import ROOT,DB,SERVER,RUNTIME,call,pets

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",required=True,type=Path);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    base=next(c["input"] for c in json.loads((ROOT/"docs/balance/pet-ownership-inputs.json").read_text())["cases"] if c["id"]=="triple-0")
    cases=[("legacy-held",[13,11,10],50,1,11),("legacy-released",[13,10,14],50,1,0),
           ("saved-shared-class",[5,11,13],64,28,11),("saved-released",[13,10,14],50,28,0)]
    results=[]
    binary=call(["docker","exec",SERVER,"sha256sum",RUNTIME+"/balance-zone"]).decode().split()[0]
    for index,(name,classes,level,key,wanted) in enumerate(cases):
        char=980004+index
        tables={"character_multiclass":"character_id","character_pet_info":"char_id","character_pet_buffs":"char_id","character_pet_inventory":"char_id","character_pet_armor":"character_id","character_data":"id"}
        counts="+".join(f"(SELECT COUNT(*) FROM {DB}.{t} WHERE {k}={char})" for t,k in tables.items())
        assert root_sql("SELECT "+counts+";").decode().strip()=="0"
        inp=copy.deepcopy(base);b=inp["builds"][0]
        b.update(classes=classes,level=level,equipment=[],aa_rank_ids=[],aa_budget=0,test_character_id=char)
        actions=[{"lifecycle":"load_saved"}]
        if wanted:actions += [{"lifecycle":"roundtrip"},{"lifecycle":"suspend"}]
        else:actions += [{"spell":633},{"lifecycle":"suspend"}]
        inp["pet_probe"]["actions"]=actions;inp["pet_probe"]["retry_native_fizzles"]=True
        local=args.output/(name+"-input.json");local.write_text(json.dumps(inp,indent=2))
        try:
            root_sql(f"USE {DB}; INSERT INTO character_multiclass(character_id,class2,class3) VALUES({char},{classes[1]},{classes[2]}); "
                f"INSERT INTO character_pet_info(char_id,pet,petname,petpower,spell_id,hp,mana,size,taunting) VALUES({char},{key},'Saved necromancer',0,443,987,0,6,1);")
            call(["docker","cp",str(local),f"{SERVER}:{RUNTIME}/{name}-input.json"])
            run=subprocess.run(["docker","exec","-w",RUNTIME,"-e","NIGHTCAP_BALANCE_RNG_SEED=1729",SERVER,
                RUNTIME+"/balance-zone","tests:balance",f"{RUNTIME}/{name}-input.json",f"{RUNTIME}/{name}-output.json"],capture_output=True,timeout=120)
            (args.output/(name+".log")).write_bytes(run.stdout+run.stderr)
            assert run.returncode==0,name
            raw=call(["docker","exec",SERVER,"cat",f"{RUNTIME}/{name}-output.json"])
            (args.output/(name+"-output.json.gz")).write_bytes(gzip.compress(raw,mtime=0))
            probe=json.loads(raw)["pet_probe"];mapped=probe["actions"][0]["settled"]["suspended_class"]
            assert mapped==wanted,(name,mapped,wanted)
            final=probe["final"];roster=pets(final,probe["player_entity_id"])
            if wanted:
                assert set(roster)=={443}
                assert next(r["entity_id"] for r in final["class_pets"] if r["class"]==11)==roster[443]["entity_id"]
                saved=root_sql(f"SELECT pet FROM {DB}.character_pet_info WHERE char_id={char};").decode().strip()
                assert saved=="28",(name,saved)
                assert final["suspended_class"]==0
            else:
                assert not roster and final["suspended_class"]==13, "Stale suspension blocked Mage suspension"
            results.append({"case":name,"mapped_class":mapped,"status":"passed"});print(json.dumps(results[-1]),flush=True)
        finally:
            root_sql(f"USE {DB}; "+" ".join(f"DELETE FROM {t} WHERE {k}={char};" for t,k in tables.items() if t!="character_data"))
    assert call(["docker","exec",SERVER,"sha256sum",RUNTIME+"/balance-zone"]).decode().split()[0]==binary
    (args.output/"summary.json").write_text(json.dumps({"binary_sha256":binary,"passed":len(results),"cases":results},indent=2))

if __name__=="__main__":main()
