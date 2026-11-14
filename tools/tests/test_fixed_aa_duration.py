"""Measure native AA buff lifetime with deterministic zone frames and a row repository.

python tools/tests/test_fixed_aa_duration.py [--source /checkout/server-mods/code]
Use --baseline only when measuring the unmodified source; optional --receipt saves observations.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_aa_temporary_buffs import AA_FIXTURE, compile_native, function, policy_helpers

HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE.parents[1] / "server-mods/code"
FILES = {
    "spells.cpp": ("int CalcBuffDuration_formula(", "int Mob::CalcBuffDuration(",
                   "int32 Mob::GetBuffDurationForTarget(", "uint32 Mob::GetFirstBuffSlot(",
                   "uint32 Mob::GetLastBuffSlot(", "uint32 Client::GetFirstBuffSlot(",
                   "uint32 Client::GetLastBuffSlot(", "int Mob::AddBuff(",
                   "void Client::RestoreBuffEffects()", "void Client::SendBuffDurationPacket(",
                   "void Mob::BuffModifyDurationBySpellID("),
    "effects.cpp": ("int32 Mob::GetActSpellDuration(",),
    "spell_effects.cpp": ("void Mob::BuffProcess()", "void Mob::SetBuffDuration("),
    "zonedb.cpp": ("void ZoneDatabase::SaveBuffs(", "void ZoneDatabase::LoadBuffs("),
}


def measure(source, baseline):
    zone = source / "zone"
    bodies = []
    fingerprints = {}
    files = {}
    for name in (*FILES, "client_process.cpp"):
        path = zone / name
        files[name] = path.read_text(encoding="utf-8")
        fingerprints[f"zone/{name}"] = hashlib.sha256(path.read_bytes()).hexdigest()
    bodies.append(policy_helpers(files["spells.cpp"]))
    for name, signatures in FILES.items():
        bodies.extend(function(files[name], sig) for sig in signatures)
    header_paths = [source / "common" / f for f in ("epic05.h", "nightcap_pet_scaling.h", "nightcap_thj_behaviors.h")]
    header_text = "".join(f'#include "{path.as_posix()}"\n' for path in header_paths)
    if not baseline:
        path = zone / "nightcap_fixed_aa_duration.h"
        fingerprints["zone/" + path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        # Keep the actual duration/encoding logic. Only replace the OS clock read.
        helper = path.read_text(encoding="utf-8")
        helper = helper.replace(function(helper, "inline int64_t Now()"),
                                "inline int64_t Now() { return ::now_ms; }")
        header_text += 'extern int64_t now_ms;\n' + helper + '\n'
        signatures = [(name, function(body, "void Client::ProcessFixedAADurations()"))
                      for name, body in files.items() if "void Client::ProcessFixedAADurations()" in body]
        if len(signatures) != 1:
            raise AssertionError("missing client fixed duration process")
        bodies.append(signatures[0][1])
        assert "ProcessFixedAADurations();" in function(files["client_process.cpp"], "bool Client::Process()")
        assert "ProcessFixedAADurations();" in function(files["spells.cpp"], "void Client::RestoreBuffEffects()")
    assert "BuffProcess();" in function(files["client_process.cpp"], "bool Client::Process()")
    fields = "int mana = 0, endurance_cost = 0, endurance_upkeep = 0, pvp_duration = 0, pvp_duration_cap = 0, hit_number = 0; const char* name = \"fixture\";"
    shared = AA_FIXTURE.replace("struct Spell {", "struct Spell {\n" + fields)
    code = (HERE / "fixed_aa_duration_fixture.cpp").read_text(encoding="utf-8")
    code = code.replace("// NATIVE_METHODS", "\n".join(bodies))
    payload = f"#define CANDIDATE {int(not baseline)}\n" + header_text + shared + code
    with tempfile.TemporaryDirectory(prefix="nightcap-fixed-aa-") as temp:
        exe = compile_native(Path(temp), payload)
        run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=60)
        if run.returncode:
            raise AssertionError(run.stdout + run.stderr)
    phase_rows, lifecycle_rows, guards = [], [], []
    for line in run.stdout.splitlines():
        group, *values = line.split(",")
        if group == "guard":
            guards.append({"control": values[0], "value": int(values[1])})
            continue
        columns = ("spell", "first_tick_ms", "focus_percent", "focus_ticks", "initial_ticks", "fade_after_ms"
                   ) if group == "phase" else ("spell", "saved_rows", "zone_restore_packets", "expired_restore_packets")
        row = dict(zip(columns, map(int, values), strict=True))
        (phase_rows if group == "phase" else lifecycle_rows).append(row)
    assert len(phase_rows) == 36 and len(lifecycle_rows) == 2
    return {"variant": "baseline" if baseline else "candidate", "source_sha256": fingerprints,
            "phase_observations": phase_rows, "lifecycle_observations": lifecycle_rows, "guards": guards}


class FixedAADuration(unittest.TestCase):
    def test_exact_native_durations_and_lifecycle(self):
        measure(DEFAULT_SOURCE, False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    result = measure(args.source.resolve(), args.baseline)
    if args.receipt:
        args.receipt.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"{result['variant']}: 36 phase/focus observations, 2 lifecycle sequences passed")
