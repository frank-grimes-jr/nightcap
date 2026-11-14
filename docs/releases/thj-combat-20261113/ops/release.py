"""One-shot server-only image promotion above the authenticated sympathetic release."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import time

STAGE = Path(__file__).resolve().parent
PARENT = STAGE.parent / "sympathetic-clicks-20261113-v1"
ROOT = Path("/opt/nightcap/deploy/production")
EVIDENCE = STAGE / "evidence"
ACTIVE = EVIDENCE / "activation"


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def initialize():
    global prior, p, r, m
    m = read(STAGE / "manifest.json")
    assert m["stage"] == STAGE.name == "thj-combat-20261113-v1"
    assert m["prior_operator"] == sha(PARENT / "release.py")
    assert m["prior_receipt"] == sha(PARENT / "evidence/activation/deployed.json")
    assert set(m["files"]) == {"bin/zone", "build.json", "release.py"}
    for name, pin in m["files"].items():
        path = STAGE / name
        assert path.resolve().is_relative_to(STAGE) and not path.is_symlink() and sha(path) == pin, name
    sys.path.insert(0, str(PARENT))
    import importlib.util
    spec = importlib.util.spec_from_file_location("sympathetic_predecessor", PARENT / "release.py")
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    prior.initialize()
    dep = prior.read(prior.ACTIVE / "deployed.json")
    assert dep["gateway_open"] and dep["image"] == m["base_image_id"]
    assert dep["client_channel_sha256"] == m["client_channel_sha256"]
    assert dep["client_release"] == m["client_release"] == 2026111301
    build = read(STAGE / "build.json")
    assert build["profile"] == "shipping" and build["baseline"] == m["base_hashes"]["bin/zone"]
    assert build["zone"] == m["binaries"]["zone"] == m["files"]["bin/zone"] != build["baseline"]
    assert set(build["units"]) == {"attack","mob","special_attacks"} and build["link_input_count"] == 144
    assert build["feature_patches"] == {
        "bow.patch":"75f03059d9b1747bb8a04562aab4b97ec8b508b8a48d47f1cb54f04fa47c9d6f",
        "backstab.patch":"f153b30a27a5b38e676964d9a614561350c803e92a0d918e89b34fd641b06ac8",
    }
    p = prior.p
    r = prior.r
    assert r.image_hashes(dep["image"]) == m["base_hashes"]
    p.STAGE, p.EVIDENCE, p.TAG, p.m = STAGE, EVIDENCE, "nightcap-game:" + STAGE.name, m


def preflight():
    assert all(r.compact(n) == state for n, state in m["baseline_services"].items())
    p.preflight()


def verification(before):
    runtime = r.running(before["image"], p.binaries())
    assert runtime["restart_count"] == 0 and sum(row[0] == "zone" for row in runtime["processes"]) == 12
    assert not any(runtime["errors"].values()), runtime["errors"]
    prior.base.health()
    r.closed_ports()
    backup = read(ACTIVE / "backup.json")
    assert backup["gzip_integrity"] and backup["compressed_bytes"] > 0 and sha(Path(backup["path"])) == backup["sha256"]
    return runtime, backup


def open_access():
    before = read(EVIDENCE / "preflight.json")
    closed = read(ACTIVE / "verified-closed.json")
    assert not (ACTIVE / "opening.json").exists() and not list(ACTIVE.glob("held-*.json"))
    assert not r.compact("gateway")["running"] and r.compact("game") == closed["game"]
    assert p.a.prior.saved() == read(ACTIVE / "expected-boot-state.json")
    p.unchanged(before)
    p.contract()
    runtime, backup = verification(before)
    assert runtime["started_at"] == closed["runtime"]["started_at"]
    p.save(ACTIVE / "opening.json", {"source":m["source_revision"]})
    try:
        r.compose("up", "-d", "--no-deps", "--wait", "--wait-timeout", "60", "gateway")
        assert r.compact("gateway")["running"] and r.compact("game") == closed["game"]
        p.unchanged(before, after_open=True)
        p.save(ACTIVE / "deployed.json", dict(source=m["source_revision"], image=before["image"],
               runtime=runtime, gateway_open=True, backup_sha256=backup["sha256"], client_release=m["client_release"],
               client_channel_sha256=m["client_channel_sha256"], owner_gameplay_accepted=False))
    except BaseException:
        p.h.hold(ACTIVE)
        raise


def verify_open():
    dep = read(ACTIVE / "deployed.json")
    before = read(EVIDENCE / "preflight.json")
    runtime, backup = verification(before)
    assert dep["gateway_open"] and r.compact("gateway")["running"]
    assert dep["image"] == runtime["image_id"] and runtime["started_at"] == dep["runtime"]["started_at"]
    p.unchanged(before, after_open=True)
    return dict(result="PASS", source=dep["source"], image=dep["image"], binaries=p.binaries(),
                workers=12, errors=runtime["errors"], restarts=runtime["restart_count"],
                started_at=runtime["started_at"], gateway_open=True, backup_integrity=True,
                backup_sha256=backup["sha256"], caches=p.h.caches(), contract=p.contract(),
                client_release=dep["client_release"], client_channel_sha256=dep["client_channel_sha256"],
                deployed_receipt=sha(ACTIVE / "deployed.json"), owner_gameplay_accepted=False)


def recover_closed():
    """Reopen the exact predecessor from fresh closed state after an interrupted activation."""
    before = read(EVIDENCE / "preflight.json")
    assert (ACTIVE / "started.json").is_file() and not (ACTIVE / "opening.json").exists()
    assert not (ACTIVE / "recovery").exists() and not (ACTIVE / "deployed.json").exists()
    assert not r.compact("gateway")["running"] and p.a.prior.players() == 0
    game = r.compact("game")
    assert game["image_id"] in (m["base_image_id"],before["image"])
    folder = ACTIVE / "recovery"
    folder.mkdir(mode=0o700)
    try:
        if game["running"] and game["image_id"] == m["base_image_id"]:
            old = r.running(m["base_image_id"],p.binaries(False))
        else:
            if game["running"]:
                start = time.monotonic()
                r.compose("stop","-t","90","game")
                assert time.monotonic()-start < 70
            state = r.state("game")["State"]
            assert not state["Running"] and not state["OOMKilled"] and state["ExitCode"] == 0
            saved = p.a.prior.saved()
            r.STAGE = p.base.EVIDENCE = folder
            backup = r.database_backup()
            assert backup["gzip_integrity"] and sha(Path(backup["path"])) == backup["sha256"]
            p.save(folder/"backup.json", backup)
            expected = p.base.boot_state(saved)
            stock = p.market.market()
            p.unchanged(before)
            r.select(m["base_image_id"])
            r.compose("up","-d","--no-deps","--wait","--wait-timeout","240","game")
            old = r.running(m["base_image_id"],p.binaries(False))
            assert p.a.prior.saved() == expected
            p.market.verify_market(stock,old["started_at"])
        p.unchanged(before)
        p.contract()
        p.base.health()
        r.closed_ports()
        r.compose("up","-d","--no-deps","--wait","--wait-timeout","60","gateway")
        assert r.compact("gateway")["running"] and r.running(m["base_image_id"],p.binaries(False))["started_at"] == old["started_at"]
        p.save(folder/"recovered.json",dict(gateway_open=True, image=m["base_image_id"],restored_player_snapshot=False))
    except BaseException:
        p.h.hold(folder)
        raise


if __name__ == "__main__":
    assert __debug__
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "activate", "open", "verify", "recover-closed"))
    args = parser.parse_args()
    initialize()
    with (ROOT / ".deployment.lock").open("a") as lock, open("/var/lock/nightcap-gm.lock", "a") as gm:
        for f in (lock, gm):
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not (ROOT / "private/gm-maintenance.json").exists()
        assert prior.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes')").strip() == "1"
        if args.action == "verify":
            print(json.dumps(verify_open()))
        else:
            {"preflight": preflight, "activate": p.activate, "open": open_access,"recover-closed":recover_closed}[args.action]()
