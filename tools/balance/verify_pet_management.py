"""Exercise real native pet selection and commands in the isolated balance DB.

Never connects to peq. Checks the runtime's database configuration before writes,
reserves unused synthetic IDs, and cleans only rows belonging to those IDs.
Native input packets bypass the RoF2 wire decoder and actual Windows client.
"""
import argparse
import copy
import gzip
import json
from pathlib import Path
import re
import subprocess

from prepare_native import root_sql
from verify_pet_roster import DB, ROOT, SERVER, call

CLASS_SPELL = {10: 166, 11: 443, 13: 633}
TABLES = {
    "character_multiclass": "character_id",
    "character_pet_armor": "character_id",
    "character_pet_info": "char_id",
    "character_pet_buffs": "char_id",
    "character_pet_inventory": "char_id",
    "character_data": "id",
}
COMMAND_FIELDS = ("order", "appearance", "taunt", "stop", "held", "gheld", "no_cast", "focused", "regroup", "feigned")


def live_pets(state, owner):
    return {pet["entity_id"]: pet for pet in state["pets"]
            if pet["owner_id"] == owner and not pet["depop"] and pet["hp"] > 0}


def cases():
    matrix = json.loads((ROOT / "docs/balance/pet-ownership-inputs.json").read_text())
    base = next(case["input"] for case in matrix["cases"] if case["id"] == "triple-0")
    for selected in (10, 11, 13):
        other = next(cls for cls in (10, 11, 13) if cls != selected)
        data = copy.deepcopy(base)
        actions = [{"spell": spell} for spell in (633, 443, 166)]
        commands = ["sit", "sit", "guard", "follow", "taunt", "taunt", "stop", "stop"]
        actions += [{"command": command} for command in commands]
        actions += [{"select_class": selected}]
        actions += [{"command": command} for command in ("sit", "stand", "guard", "follow", "taunt", "taunt", "stop", "stop")]
        actions += [{"target_class": other}]
        actions += [{"command": command} for command in ("sit", "stand", "guard", "follow")]
        actions += [{"target_class": 0}, {"command": "sit"}, {"command": "sit"}]
        actions += [{"select_class": selected}, {"command": "dismiss"}, {"command": "guard"}]
        actions += [{"target_class": other}, {"command": "dismiss"}, {"select_class": 0}, {"command": "follow"}, {"command": "dismiss"}]
        data["pet_probe"]["actions"] = actions
        data["pet_probe"]["retry_native_fizzles"] = True
        yield f"select-class-{selected}", data
    attack_matrix = json.loads((ROOT / "docs/balance/pet-command-after-inputs.json").read_text())
    for command in (2, 3):
        for selected, distance in ((0, 80), (11, 80), (11, 500)):
            original = next(case["input"] for case in attack_matrix["cases"]
                            if case["id"] == f"command-{command}-{distance}-extraonly-False")
            data = copy.deepcopy(original)
            data["pet_probe"]["actions"] = [{"spell": spell} for spell in (633, 443, 166)] + [{"select_class": selected}]
            data["pet_probe"]["retry_native_fizzles"] = True
            data["pet_probe"]["combat"]["target_via_mouse"] = True
            yield f"attack-{command}-select-{selected}-range-{distance}", data


def verify(output):
    probe = output["pet_probe"]
    owner = probe["player_entity_id"]
    selected = 0
    commands = 0
    for index, action in enumerate(probe["actions"]):
        before, after, request = action["before"], action["settled"], action["input"]
        old, new = live_pets(before, owner), live_pets(after, owner)
        expected_before = [selected] if selected else sorted(old)
        assert before["command_pet_ids"] == expected_before, (index, "scope before", before["command_pet_ids"], expected_before)
        if "spell" in request:
            assert request["spell"] in {pet["spell"] for pet in new.values()}, (index, "failed summon")
        elif "select_class" in request or "target_class" in request:
            cls = request.get("select_class", request.get("target_class"))
            selected = next((pet_id for pet_id, pet in new.items() if pet["spell"] == CLASS_SPELL[cls]), 0) if cls else 0
            assert not cls or selected, (index, "missing selected class")
            assert old.keys() == new.keys(), (index, "selection changed roster")
            if "target_class" in request:
                assert after["player_target"] == selected, (index, "native target packet not applied")
        elif "command" in request:
            commands += 1
            command = request["command"]
            recipients = set(expected_before)
            if command == "dismiss":
                assert set(new) == set(old) - recipients, (index, "wrong pets dismissed", old.keys(), new.keys(), recipients)
                if selected in recipients:
                    selected = 0
            else:
                assert old.keys() == new.keys(), (index, "command changed roster")
                anchor = old[selected or before["primary_pet"]]
                for pet_id, pet in new.items():
                    if pet_id not in recipients:
                        assert all(pet[field] == old[pet_id][field] for field in COMMAND_FIELDS), (index, "unselected pet changed", pet_id)
                        continue
                    if command in ("sit", "stand"):
                        want = 0 if command == "stand" or anchor["order"] == 1 else 1
                        assert pet["appearance"] == want, (index, command, pet_id, pet["appearance"], want)
                    elif command in ("guard", "follow"):
                        assert pet["order"] == (2 if command == "guard" else 0), (index, command, pet_id)
                    elif command in ("taunt", "stop"):
                        assert pet[command] == (not anchor[command]), (index, command, pet_id)
        if selected and selected not in new:
            selected = 0
        assert after["command_pet_ids"] == ([selected] if selected else sorted(new)), (index, "wrong settled command scope")
        assert len(new) <= 3
    if "combat" not in probe:
        assert not live_pets(probe["final"], owner), "Final all-pet dismiss did not empty roster"
        return {"actions": len(probe["actions"]), "commands": commands, "final_pets": 0}
    combat = probe["combat"]
    assert combat["input"]["commands_only"] and combat["input"]["target_via_mouse"]
    expected = [selected] if selected else sorted(live_pets(probe["final"], owner))
    if combat["input"]["starting_distance"] == 500:
        expected = []
    assert [request["input"] for request in combat["commands"]] == combat["input"]["commands"], "Incomplete attack schedule"
    for request in combat["commands"]:
        assert request["before"]["boss_hp"] == request["after"]["boss_hp"], "Attack must enqueue AI orders, never deal immediate damage"
        ordered = sorted(pet["id"] for pet in request["after"]["pets"] if pet["present"] and pet["hate"] > 0)
        assert ordered == expected, ("Wrong attack recipients after native enemy target packet", ordered, expected)
    return {"actions": len(probe["actions"]), "commands": len(combat["commands"]),
            "final_pets": len(combat["pet_ids"]), "ordered_pet_ids": expected}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", default="/tmp/nightcap-balance-pet-management-20260922")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"/tmp/nightcap-balance-[A-Za-z0-9_-]+", args.runtime):
        raise ValueError("Runtime must be an isolated /tmp/nightcap-balance-* directory")
    args.output.mkdir(parents=True, exist_ok=True)
    # Print only the database name; never export configuration credentials.
    configured = call(["docker", "exec", "-w", args.runtime, SERVER, "python3", "-c",
                       "import json; c=json.load(open('eqemu_config.json')); print(c['server']['database']['db'])"]).decode().strip()
    if configured != DB:
        raise ValueError("Runtime is not bound to the isolated balance database")
    binary = call(["docker", "exec", SERVER, "sha256sum", args.runtime + "/balance-zone"]).decode().split()[0]
    checked = []
    for index, (name, data) in enumerate(cases()):
        char = 980070 + index
        counts = "+".join(f"(SELECT COUNT(*) FROM {DB}.{table} WHERE {key}={char})" for table, key in TABLES.items())
        if root_sql("SELECT " + counts + ";").decode().strip() != "0":
            raise ValueError("Reserved synthetic character is in use")
        data["builds"][0]["test_character_id"] = char
        local = args.output / (name + "-input.json")
        local.write_text(json.dumps(data, indent=2) + "\n")
        reserved = False
        try:
            root_sql(f"INSERT INTO {DB}.character_multiclass(character_id,class2,class3) VALUES({char},11,10);")
            reserved = True
            call(["docker", "cp", str(local), f"{SERVER}:{args.runtime}/{name}-input.json"])
            run = subprocess.run(["docker", "exec", "-w", args.runtime, "-e", "NIGHTCAP_BALANCE_RNG_SEED=1729", SERVER,
                                  args.runtime + "/balance-zone", "tests:balance", args.runtime + "/" + name + "-input.json",
                                  args.runtime + "/" + name + "-output.json"], capture_output=True, timeout=120)
            (args.output / (name + ".log")).write_bytes(run.stdout + run.stderr)
            assert run.returncode == 0, f"Native run failed: {name}; see evidence log"
            raw = call(["docker", "exec", SERVER, "cat", args.runtime + "/" + name + "-output.json"])
            (args.output / (name + "-output.json.gz")).write_bytes(gzip.compress(raw, mtime=0))
            result = {"id": name, **verify(json.loads(raw))}
            assert call(["docker", "exec", SERVER, "sha256sum", args.runtime + "/balance-zone"]).decode().split()[0] == binary, "Diagnostic changed during test"
            checked.append(result)
            print(json.dumps(result), flush=True)
            (args.output / "summary.json").write_text(json.dumps({"binary_sha256": binary, "database": DB, "passed": len(checked), "cases": checked}, indent=2) + "\n")
        finally:
            if reserved:
                root_sql(" ".join(f"DELETE FROM {DB}.{table} WHERE {key}={char};" for table, key in TABLES.items() if table != "character_data"))
                if root_sql("SELECT " + counts + ";").decode().strip() != "0":
                    raise RuntimeError("Synthetic cleanup left rows; inspect the isolated diagnostic database")


if __name__ == "__main__":
    main()
