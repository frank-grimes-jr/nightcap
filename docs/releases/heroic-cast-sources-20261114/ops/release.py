"""Promote the heroic spell-source zone over the authenticated bow/Backstab runtime."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

STAGE = Path(__file__).resolve().parent
PREVIOUS = STAGE.parent / "thj-combat-20261113-v1"
ROOT = Path("/opt/nightcap/deploy/production")
BASE_ZONE = "ad119ac221bc6e46e7770827e2777d75a6f0937c9632f88512a169ce20525e00"
BASE_RECEIPT = "3457bed76f3184c037425503099062c3c4b1d36f3f260e11a1003682791cb869"
PATCH = "8714bc54c62c7e41f93dda7631b968340ed17f99791a66a1de47bbe207730e0a"
UNITS = {"beacon","effects","special_attacks","spell_effects","spells"}


def initialize():
    sys.path.insert(0,str(PREVIOUS))
    spec = importlib.util.spec_from_file_location("combat", PREVIOUS/"release.py")
    combat = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(combat)
    m = combat.read(STAGE/"manifest.json")
    assert STAGE.name == m["stage"] == "heroic-cast-sources-20261114-v1"
    assert re.fullmatch(r"[0-9a-f]{40}", m["source_revision"])
    assert combat.sha(PREVIOUS/"release.py") == m["prior_operator"]
    assert combat.sha(PREVIOUS/"evidence/activation/deployed.json") == m["prior_receipt"] == BASE_RECEIPT
    assert set(m["files"]) == {"release.py", "build.json", "bin/zone"}
    for name,pin in m["files"].items():
        file = STAGE/name
        assert not file.is_symlink() and file.resolve().is_relative_to(STAGE) and combat.sha(file) == pin, name
    combat.initialize()
    dep = combat.read(combat.ACTIVE/"deployed.json")
    assert dep["gateway_open"] and m["base_image_id"] == dep["image"]
    assert dep["client_release"] == m["client_release"] == 2026111301
    assert dep["client_channel_sha256"] == m["client_channel_sha256"]
    assert combat.r.image_hashes(dep["image"]) == m["base_hashes"]
    build = combat.read(STAGE/"build.json")
    assert m["base_hashes"]["bin/zone"] == build["baseline"] == BASE_ZONE
    assert build["profile"] == "shipping" and build["link_input_count"] == 144
    assert build["zone"] == m["binaries"]["zone"] == m["files"]["bin/zone"] != BASE_ZONE
    assert build["feature_patch_sha256"] == m["feature_patch_sha256"] == PATCH
    assert set(build["units"]) == UNITS and all(v["predecessor"] != v["candidate"] for v in build["units"].values())
    assert set(m["binaries"]) == {"zone"}
    combat.STAGE = combat.p.STAGE = STAGE
    combat.EVIDENCE = combat.p.EVIDENCE = STAGE / "evidence"
    combat.ACTIVE = combat.EVIDENCE / "activation"
    combat.p.TAG = "nightcap-game:" + STAGE.name
    combat.m = combat.p.m = m
    return combat


def deploy(combat):
    preflight = combat.EVIDENCE/"preflight.json"
    if preflight.is_file():
        assert not combat.ACTIVE.exists()
        before = combat.read(preflight)
        assert combat.sha(STAGE/"manifest.json") == before["manifest_sha256"]
        assert all(combat.r.compact(n) == state for n,state in before["services"].items())
        combat.p.unchanged(before)
    else:
        combat.preflight()
    assert combat.p.a.prior.players() == 0, "Players online"
    combat.p.activate()
    combat.open_access()


if __name__ == "__main__":
    assert __debug__
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument("action",choices=("deploy","verify","recover-closed"))
    action = parser.parse_args().action
    combat = initialize()
    with (ROOT/".deployment.lock").open("a") as lock, open("/var/lock/nightcap-gm.lock","a") as gm:
        for handle in (lock,gm):
            fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/"private/gm-maintenance.json").exists()
        assert combat.prior.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes')").strip() == "1"
        if action == "verify":
            print(json.dumps(combat.verify_open()))
        elif action == "recover-closed":
            combat.recover_closed()
        else:
            deploy(combat)
