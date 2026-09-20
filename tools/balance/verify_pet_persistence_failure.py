"""Inject one pet-state INSERT failure in the isolated database and prove rollback."""
import argparse
import copy
import json
from pathlib import Path
import subprocess
from prepare_native import root_sql
from verify_pet_roster import ROOT, DB, SERVER, RUNTIME, call

CHAR=980002
TRIGGER="nightcap_test_pet_save_failure_20260919"
TABLES=("character_pet_info","character_pet_buffs","character_pet_inventory")

def snapshot():
    return root_sql(f"SELECT * FROM {DB}.character_pet_info WHERE char_id={CHAR} ORDER BY pet; "
        f"SELECT * FROM {DB}.character_pet_buffs WHERE char_id={CHAR} ORDER BY pet,slot; "
        f"SELECT * FROM {DB}.character_pet_inventory WHERE char_id={CHAR} ORDER BY pet,slot;").decode()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",required=True,type=Path);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    guard="+".join(f"(SELECT COUNT(*) FROM {DB}.{t} WHERE char_id={CHAR})" for t in TABLES)
    guard+=f"+(SELECT COUNT(*) FROM {DB}.character_multiclass WHERE character_id={CHAR})"
    assert root_sql("SELECT "+guard+";").decode().strip()=="0"
    assert root_sql(f"SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA='{DB}' AND TRIGGER_NAME='{TRIGGER}';").decode().strip()=="0"
    source=json.loads((ROOT/"docs/balance/pet-ownership-inputs.json").read_text())
    inp=copy.deepcopy(next(c["input"] for c in source["cases"] if c["id"]=="triple-0"))
    inp["builds"][0]["test_character_id"]=CHAR
    inp["pet_probe"]["actions"]=[{"spell":s} for s in [633,443,166]]+[{"lifecycle":"roundtrip"}]
    inp["pet_probe"]["retry_native_fizzles"]=True
    local=args.output/"failure-input.json";local.write_text(json.dumps(inp,indent=2)+"\n")
    created=False
    try:
        root_sql(f"USE {DB}; INSERT INTO character_multiclass(character_id,class2,class3) VALUES({CHAR},11,10); "
            f"INSERT INTO character_pet_info(char_id,pet,petname,petpower,spell_id,hp,mana,size,taunting) VALUES({CHAR},14,'Rollback original',0,633,987,111,6,1); "
            f"INSERT INTO character_pet_buffs(char_id,pet,slot,spell_id,caster_level,ticsremaining,counters) VALUES({CHAR},14,0,107,50,-1,0); "
            f"INSERT INTO character_pet_inventory(char_id,pet,slot,item_id) VALUES({CHAR},14,2,1001);")
        before=snapshot()
        root_sql(f"USE {DB};\nDELIMITER $$\nCREATE TRIGGER {TRIGGER} BEFORE INSERT ON character_pet_info FOR EACH ROW BEGIN "
            f"IF NEW.char_id={CHAR} AND NEW.pet=12 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='isolated pet persistence failure'; END IF; END$$\nDELIMITER ;\n")
        created=True
        call(["docker","cp",str(local),f"{SERVER}:{RUNTIME}/failure-input.json"])
        result=subprocess.run(["docker","exec","-w",RUNTIME,"-e","NIGHTCAP_BALANCE_RNG_SEED=1729",SERVER,
            RUNTIME+"/balance-zone","tests:balance",RUNTIME+"/failure-input.json",RUNTIME+"/failure-output.json"],capture_output=True,timeout=120)
        log=(result.stdout+result.stderr).decode(errors="replace")
        (args.output/"failure.log").write_text(log)
        after=snapshot()
        assert result.returncode!=0, "Failure injection did not terminate the isolated session"
        assert "isolated pet persistence failure" in log, "Did not reach the guarded native INSERT"
        assert before==after, "Pet info, buffs or inventory changed despite failed transaction"
        report={"status":"passed","binary_sha256":call(["docker","exec",SERVER,"sha256sum",RUNTIME+"/balance-zone"]).decode().split()[0],
            "scope":"Conditional INSERT failure for synthetic character980002 in isolated DB; all three original tables restored",
            "exit_code":result.returncode,"before":before,"after":after}
        (args.output/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps({k:v for k,v in report.items() if k not in ["before","after"]}))
    finally:
        if created:root_sql(f"DROP TRIGGER {DB}.{TRIGGER};")
        root_sql(f"USE {DB}; DELETE FROM character_multiclass WHERE character_id={CHAR}; "+" ".join(f"DELETE FROM {t} WHERE char_id={CHAR};" for t in TABLES))

if __name__=="__main__":main()
