"""Owner-announced gateway drain followed by the existing verified zone-only operator."""
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time

STAGE=Path("/opt/nightcap/releases/thj-combat-20261113-v1")
spec=importlib.util.spec_from_file_location("combat_release",STAGE/"release.py")
op=importlib.util.module_from_spec(spec)
spec.loader.exec_module(op)


def run():
    op.initialize()
    p,r,m=op.p,op.r,op.m
    notice=op.read(STAGE/"maintenance-notice-result.json")
    assert notice["queued"] and notice["event_removed"]
    assert m["source_revision"]=="c151a149f399124647c7929e4b1f3cdae2686404"
    with (op.ROOT/".deployment.lock").open("a") as lock,open("/var/lock/nightcap-gm.lock","a") as gm:
        for f in (lock,gm):
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (op.ROOT/"private/gm-maintenance.json").exists()
        assert op.prior.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes')").strip()=="1"
        assert not op.EVIDENCE.exists() and not (STAGE/"announced-started.json").exists()
        services={n:r.compact(n) for n in m["baseline_services"]}
        assert services==m["baseline_services"] and all(v["running"] for v in services.values())
        assert services["db"]["health"]==services["game"]["health"]=="healthy"
        assert p.sha(op.ROOT/"data/public/channel.json")==m["client_channel_sha256"]
        assert shutil.disk_usage(op.ROOT).free>4*1024**3
        p.base.health()
        p.startup.startup_guards()
        r.closed_ports()
        r.running(m["base_image_id"],p.binaries(False))
        p.contract()
        # Validate the image while the incumbent can still finish play.
        image=p.image()
        assert all(r.compact(n)==state for n,state in services.items())
        players=p.a.prior.players()
        p.save(STAGE/"announced-started.json",dict(players=players,image=image,source=m["source_revision"]))
        try:
            r.compose("stop","gateway")
            assert not r.compact("gateway")["running"]
            deadline=time.monotonic()+300
            time.sleep(125)
            while p.a.prior.players():
                assert time.monotonic()<deadline,"Active session has not completed its native disconnect grace"
                time.sleep(5)
            assert all(r.compact(n)==state for n,state in services.items() if n!="gateway")
            assert not r.compact("gateway")["running"] and p.a.prior.players()==0
            op.EVIDENCE.mkdir(mode=0o700)
            services["gateway"]=r.compact("gateway")
            before=dict(manifest_sha256=op.sha(STAGE/"manifest.json"),services=services,checks=p.contract(),
                        runtime=r.runtime(),publication=p.h.publication(),caches=p.h.caches(),content=p.a.content(),
                        rules=p.a.prior.p.rules(),image=image)
            dry=op.EVIDENCE/"boot-preflight"
            dry.mkdir(mode=0o700)
            previous=p.base.EVIDENCE
            p.base.EVIDENCE=dry
            try:
                p.base.boot_state(p.a.prior.saved())
            finally:
                p.base.EVIDENCE=previous
            p.unchanged(before)
            assert all(r.compact(n)==state for n,state in services.items())
            p.save(op.EVIDENCE/"preflight.json",before)
            p.activate()
            op.open_access()
        except BaseException:
            if not op.ACTIVE.exists() and r.compact("game")==services["game"]:
                r.running(m["base_image_id"],p.binaries(False))
                p.base.health()
                r.compose("up","-d","--no-deps","--wait","--wait-timeout","60","gateway")
                assert r.compact("gateway")["running"] and r.compact("game")==services["game"]
                p.save(STAGE/"announced-original-reopened.json",dict(source=m["source_revision"],gateway_open=True))
            raise


if __name__=="__main__":
    assert __debug__
    os.umask(0o077)
    run()
