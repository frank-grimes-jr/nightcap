"""Re-run native Attack/Quick Attack range and missing-primary controls."""
import argparse,copy,gzip,json,subprocess
from pathlib import Path
from prepare_native import root_sql
from verify_pet_roster import ROOT,DB,SERVER,RUNTIME,call
from pet_combat_controls import assess_commands

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",required=True,type=Path);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    char=980003
    assert root_sql(f"SELECT COUNT(*) FROM {DB}.character_multiclass WHERE character_id={char};").decode().strip()=="0"
    matrix=json.loads((ROOT/"docs/balance/pet-command-after-inputs.json").read_text())
    binary=call(["docker","exec",SERVER,"sha256sum",RUNTIME+"/balance-zone"]).decode().split()[0]
    results=[]
    try:
        root_sql(f"INSERT INTO {DB}.character_multiclass(character_id,class2,class3) VALUES({char},11,10);")
        for index,case in enumerate(matrix["cases"][:8]):
            inp=copy.deepcopy(case["input"]);inp["builds"][0]["test_character_id"]=char
            inp["pet_probe"]["retry_native_fizzles"]=True
            name=f"attack-{index}";local=args.output/(name+"-input.json");local.write_text(json.dumps(inp,indent=2))
            call(["docker","cp",str(local),f"{SERVER}:{RUNTIME}/{name}-input.json"])
            result=subprocess.run(["docker","exec","-w",RUNTIME,"-e","NIGHTCAP_BALANCE_RNG_SEED=1729",SERVER,
                RUNTIME+"/balance-zone","tests:balance",f"{RUNTIME}/{name}-input.json",f"{RUNTIME}/{name}-output.json"],capture_output=True,timeout=120)
            (args.output/(name+".log")).write_bytes(result.stdout+result.stderr)
            assert result.returncode==0,name
            raw=call(["docker","exec",SERVER,"cat",f"{RUNTIME}/{name}-output.json"])
            (args.output/(name+"-output.json.gz")).write_bytes(gzip.compress(raw,mtime=0))
            output=json.loads(raw);combat=output["pet_probe"]["combat"]
            checked=assess_commands(combat)
            assert checked["passed"],(case["id"],checked)
            assert len(combat["pet_ids"])==len(case["expected_spells"])
            results.append({"id":case["id"],**checked})
            print(json.dumps(results[-1]),flush=True)
        assert call(["docker","exec",SERVER,"sha256sum",RUNTIME+"/balance-zone"]).decode().split()[0]==binary
        (args.output/"summary.json").write_text(json.dumps({"binary_sha256":binary,"passed":len(results),"cases":results},indent=2))
    finally:
        root_sql(f"DELETE FROM {DB}.character_multiclass WHERE character_id={char};")

if __name__=="__main__":main()
