"""Promote the fixed AA-duration zone over the authenticated heroic-cast runtime."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

STAGE = Path(__file__).resolve().parent
PREVIOUS = STAGE.parent / "heroic-cast-sources-20261114-v1"
ROOT = Path("/opt/nightcap/deploy/production")
BASE_ZONE = "67874c589830a5bb07f8a2b84566b39cf20e1dd3583fa54bbf29599ccb5ada8b"
BASE_RECEIPT = "dbe7ea53f2dd7b4daa07839e752f7568bf0f63a86d397729b1fcd21069a681f9"
PATCH = "0ac9dced18ce67345a37815e1abd778de93cf411bb8aea1e9b6c1140df4ee737"
UNITS = {"client_process","spell_effects","spells","zonedb"}


def initialize():
    sys.path.insert(0,str(PREVIOUS))
    spec = importlib.util.spec_from_file_location("heroic_predecessor", PREVIOUS/"release.py")
    heroic = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(heroic)
    combat = heroic.initialize()
    m = combat.read(STAGE/"manifest.json")
    assert STAGE.name == m["stage"] == "fixed-aa-duration-20261114-v1"
    assert re.fullmatch(r"[0-9a-f]{40}", m["source_revision"])
    assert combat.sha(PREVIOUS/"release.py") == m["prior_operator"]
    assert combat.sha(PREVIOUS/"evidence/activation/deployed.json") == m["prior_receipt"] == BASE_RECEIPT
    assert set(m["files"]) == {"release.py", "build.json", "bin/zone"}
    for name,pin in m["files"].items():
        file = STAGE/name
        assert not file.is_symlink() and file.resolve().is_relative_to(STAGE) and combat.sha(file) == pin, name
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
    # Use the same mutex-protected, native save/drain path whether a player is
    # online at admission close or joins while the candidate image is built.
    file = PREVIOUS/"maintenance.py"
    assert combat.sha(file) == "db33908a16da4125ffa7d10cc56f3dc6d1706c648636ddeee6e09103a4464832"
    spec = importlib.util.spec_from_file_location("prior_maintenance",file)
    maintenance = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(maintenance)
    maintenance.release = sys.modules[__name__]
    maintenance.REVISION = combat.m["source_revision"]
    maintenance.deploy(combat)


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
