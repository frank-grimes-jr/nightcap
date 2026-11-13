"""One-shot paired Inventory server/client release; no player snapshot restore."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ROOT=Path('/opt/nightcap/deploy/production')
STAGE=Path('/opt/nightcap/releases/inventory-combat-stats-20261112-v1')
PRIOR=Path('/opt/nightcap/releases/dot-no-initial-damage-20261112-v2/rollout.py')
AUTHORIZATION='Yes, implement it to match the screenshot, including the caps and combat stats above. Use the correct server values for MIT and AVD, and publish it for live testing.'
SOURCE_DELTA=['common/inventory_stats_protocol.h','zone/client.h','zone/command.cpp','zone/gm_commands/nightcapui.cpp']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def initialize():
    m=json.loads((STAGE/'manifest.json').read_text())
    assert m['owner_authorization']==AUTHORIZATION
    assert sha(PRIOR)==m['prior_operator_sha256']
    for name,pin in m['files'].items():
        path=STAGE/name
        assert not path.is_symlink() and path.resolve().is_relative_to(STAGE) and sha(path)==pin,name
    proof=json.loads((STAGE/'native-build.json').read_text())
    assert proof['status']=='PASS' and proof['baseline_reproduced']
    assert proof['source_delta']==SOURCE_DELTA
    assert proof['binary_sha256']['baseline']==m['base_hashes']['bin/zone']
    assert proof['binary_sha256']['candidate']==m['binaries']['zone']==m['files']['bin/zone']
    for name in SOURCE_DELTA:
        assert proof['source_sha256'][name]==m['files']['source/'+name]
    checks=json.loads((STAGE/'release-checks.json').read_text())
    assert checks['status']=='PASS' and checks['native_build_sha256']==m['files']['native-build.json']
    assert json.loads((STAGE/'review.json').read_text())['status']=='PASS'
    signed=json.loads((STAGE/'client/verification.json').read_text())
    assert signed['release']==m['client_release']==2026111202 and signed['changed_assets']==3
    assert signed['previous_channel_sha256']==m['client_channel_sha256']
    assert signed['channel_sha256']==m['files']['client/channel.json']
    spec=importlib.util.spec_from_file_location('inventory_prior',PRIOR)
    parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
    prior=parent.initialize()
    assert prior.r.image_hashes(m['base_image_id'])==m['base_hashes']
    assert prior.m['client_channel_sha256']==m['client_channel_sha256']
    prior.STAGE=STAGE;prior.EVIDENCE=STAGE/'evidence'
    prior.TAG='nightcap-game:inventory-combat-stats-20261112-v1';prior.m=m
    return prior


def publish_client(prior):
    folder=prior.EVIDENCE/'activation'
    verified=prior.read(folder/'verified-closed.json');before=prior.read(prior.EVIDENCE/'preflight.json')
    assert not (STAGE/'client/published.json').exists(),'Inspect existing publication receipt; never replay blindly'
    assert not prior.r.state('gateway')['State']['Running']
    assert prior.r.compact('game')==verified['game'] and prior.a.prior.players()==0
    prior.unchanged(before);prior.base.health()
    spec=importlib.util.spec_from_file_location('inventory_publisher',STAGE/'client/publish.py')
    publisher=importlib.util.module_from_spec(spec);spec.loader.exec_module(publisher)
    def snapshot():
        services={name:prior.r.compact(name) for name in ('game','gateway','db','web','tunnel')}
        assert not services['gateway']['running']
        assert all(s['running'] and not s['oom_killed'] for name,s in services.items() if name!='gateway')
        assert services['game']['health']==services['db']['health']=='healthy'
        return services
    result=publisher.publish(STAGE/'client',ROOT/'data/public',snapshot=snapshot)
    prior.save(STAGE/'client/published.json',result)
    prior.unchanged(before,client_published=True)
    return result


def open_access(prior):
    result=prior.read(STAGE/'client/published.json')
    assert result['channel_sha256']==prior.m['files']['client/channel.json']
    verification=prior.read(STAGE/'public-client-verified.json')
    assert verification['release']==2026111202 and verification['hosted']
    assert verification['channel_sha256']==result['channel_sha256']
    assert verification['signature']=='valid against shipped production key'
    assert sha(ROOT/'data/public/channel.json')==result['channel_sha256']
    unchanged=prior.unchanged
    def paired_unchanged(before,after_open=False,client_published=False):
        return unchanged(before,after_open=after_open,client_published=True)
    prior.unchanged=paired_unchanged
    prior.open_access()
    deployed=prior.read(prior.EVIDENCE/'activation/deployed.json')
    deployed.update(client_release=2026111202,client_channel_sha256=result['channel_sha256'],owner_gameplay_accepted=False)
    prior.save(prior.EVIDENCE/'activation/paired-deployed.json',deployed)
    return deployed


def main():
    assert __debug__;os.umask(0o077)
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('preflight','activate','publish-client','open'))
    action=parser.parse_args().action;prior=initialize()
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists()
        assert prior.a.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        if action=='preflight':prior.preflight()
        elif action=='activate':prior.activate()
        elif action=='publish-client':publish_client(prior)
        else:open_access(prior)
    print('Inventory release action verified: '+action,flush=True)


if __name__=='__main__':main()
