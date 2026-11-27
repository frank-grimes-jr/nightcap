"""Repeat an archived Cazic arena case in a prepared content-only diagnostic."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=["hybrid", "melee", "pet", "spell"])
    parser.add_argument("budget", type=int, choices=[0, 200, 500])
    parser.add_argument("seed", type=int)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    evidence = Path(__file__).resolve().parent
    if root.parent != Path("/tmp") or not root.name.startswith("nightcap-balance-"):
        raise SystemExit("Run from the isolated Linux diagnostic directory")
    fixture = json.loads(gzip.decompress((evidence / "inputs.json.gz").read_bytes()))
    case = fixture[str(args.budget)][args.role]
    config = json.loads((root / "eqemu_config.json").read_text())["server"]
    db = config["database"]
    if (db["db"] != "nightcap_raid_aug_balance_20261112" or
        db["username"] != "raid_aug_balance_261112" or "content_database" in config or
        config["auto_database_updates"] != "false"):
        raise SystemExit("Use the named isolated diagnostic database and fixture user")
    native = root / "balance-zone"
    with native.open("rb") as binary:
        if hashlib.sha256(binary.read()).hexdigest() != "9aa1906eec4722661fc09db7f11fdf741f19ad5bad4e26c47ac78a42e4759d83":
            raise SystemExit("The encounter diagnostic differs from the measured binary")
    sql = ["mariadb", "-NB", "-h", db["host"], "-u", db["username"], db["db"]]
    env = dict(os.environ, MYSQL_PWD=db["password"])
    stat = subprocess.check_output(sql, env=env, text=True, input=
        "SELECT level,hp,mindmg,maxdmg,attack_delay,hp_regen_rate,hp_regen_per_second,ac,atk,accuracy FROM npc_types WHERE id=72003;"
        "SELECT COUNT(*) FROM account; SELECT COUNT(*) FROM character_data;"
        "SELECT COUNT(*) FROM npc_spells_entries WHERE npc_spells_id=116 AND spellid=808 AND minlevel=255 AND maxlevel=255;"
        "SELECT attack_proc,proc_chance FROM npc_spells WHERE id=116;").splitlines()
    expected = ["55\t24000\t85\t218\t32\t13\t0\t397\t0\t0", "0", "0", "1", "956\t33"]
    if stat != expected:
        raise SystemExit("Prepare a fresh synthetic fixture with the recorded NPC and spell values")
    char_id = case["builds"][0]["test_character_id"]
    if char_id not in (97101, 97102, 97103, 97104):
        raise SystemExit("Unexpected test character")
    subprocess.run(sql, env=env, input=f"DELETE FROM timers WHERE char_id={char_id}", text=True, check=True)
    stem = f"replay-{args.role}-{args.budget}-{args.seed}"
    src, out = root / (stem + "-input.json"), root / (stem + "-output.json")
    src.write_text(json.dumps(case))
    subprocess.run([str(native), "tests:balance", str(src), str(out)],
        env=dict(os.environ, NIGHTCAP_BALANCE_RNG_SEED=str(args.seed)), check=True)
    result = json.loads(out.read_text())
    fight = result["pet_probe"]["combat"] if args.role == "pet" else result["encounter"]
    print(args.role, result["builds"][0]["aa_spent"], fight["result"], fight["trace"][-1]["ms"])


if __name__ == "__main__":
    main()
