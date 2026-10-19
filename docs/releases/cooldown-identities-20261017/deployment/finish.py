"""Finish the already committed release; accept only proven exhausted market slots."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path

STAGE = Path('/opt/nightcap/releases/cooldown-identities-20261018')
FINISH = STAGE / 'finish'
RESUME_SHA = 'b65a1c9d0b74c0c45c95aa419cefa1d3ce87e2f752e91b233158cdf00e3a5d10'
SECOND_HOLD = 'held-1792335896389206450.json'
SECOND_HOLD_SHA = '74354bb75b78604c90ad7a9bf67e83b5f047adbd386b07e3bbd258668d62ff7c'
FIRST_GAME = '6e4b09f371e9024de46770f43fbf7f1751cf9b77ad206ed13e3dbe1d9509aebe'
FIRST_STARTED = '2026-10-18T15:03:43.92312443Z'
rs = op = None


def save(name, value):
    with (FINISH / 'evidence' / name).open('x') as stream:
        json.dump(value, stream, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def manifest():
    value = rs.read(FINISH / 'manifest.json')
    assert value['original_manifest_sha256'] == rs.ORIGINAL_MANIFEST
    assert value['resume_manifest_sha256'] == RESUME_SHA == rs.sha(STAGE / 'resume' / 'manifest.json')
    assert set(value['files']) == {'finish.py', 'test_finish.py'}
    for name, digest in value['files'].items():
        path = FINISH / name
        assert not path.is_symlink() and rs.sha(path) == digest, name
    rs.manifest(); op.manifest()
    return value


def known_holds():
    expected = {rs.HOLD_NAME: rs.HOLD_SHA, SECOND_HOLD: SECOND_HOLD_SHA}
    assert {path.name for path in op.EVIDENCE.glob('held-*.json')} == set(expected), 'New or missing hold'
    for name, digest in expected.items():
        path = op.EVIDENCE / name
        assert rs.sha(path) == digest
        held = rs.read(path)
        assert held['both_stopped'] and held['running'] == {'gateway': False, 'game': False}
        assert held['database_restored'] is False
    return expected


def verify_market(before, started):
    after = op.market_state()
    op.validate_market_state(before, after, started)
    epoch, era = int(after[2]), int(after[3])
    invalid = op.sql(f"""SELECT COUNT(*) FROM nightcap_market_offers o
LEFT JOIN nightcap_market_actors a ON a.npc_id=o.npc_id LEFT JOIN nightcap_market_catalog c ON c.item_id=o.item_id LEFT JOIN items i ON i.id=o.item_id
WHERE a.npc_id IS NULL OR c.item_id IS NULL OR i.id IS NULL OR o.epoch<>{epoch} OR o.remaining<>1
OR o.zone_id<>a.zone_id OR o.kind<>a.kind OR o.price_cp<=0
OR o.price_cp<>CASE o.kind WHEN 'find' THEN c.find_cp WHEN 'sell' THEN c.sell_cp ELSE c.buy_cp END
OR c.pool<>IF(o.kind='find','find','tunnel') OR c.min_expansion>{era} OR (c.max_expansion>=0 AND c.max_expansion<{era})
OR i.nodrop=0 OR i.norent=0 OR i.stackable<>0 OR i.maxcharges<>0 OR i.itemclass<>0 OR i.questitemflag<>0 OR i.attuneable<>0
OR c.buy_cp>=c.sell_cp OR c.buy_cp>=c.find_cp
OR EXISTS(SELECT 1 FROM merchantlist m JOIN npc_types n ON n.merchant_id=m.merchantid WHERE m.item=o.item_id AND n.id=o.npc_id);
SELECT COUNT(*) FROM (SELECT item_id,kind,COUNT(*) n FROM nightcap_market_offers GROUP BY item_id,kind HAVING n>IF(kind='sell',3,2)) x;""").splitlines()
    assert invalid == ['0', '0'], 'Invalid market offer or duplicate cap'
    # Includes actors with zero offers. Every available slot must be filled or
    # have an empty eligible pool under the procedure's exact predicates.
    rows = op.sql(f"""SELECT a.npc_id,a.kind,COUNT(o.item_id),
(SELECT COUNT(*) FROM nightcap_market_catalog c JOIN items i ON i.id=c.item_id
 WHERE c.min_expansion<={era} AND (c.max_expansion<0 OR c.max_expansion>={era})
 AND c.pool=IF(a.kind='find','find','tunnel')
 AND i.nodrop<>0 AND i.norent<>0 AND i.stackable=0 AND i.maxcharges=0
 AND i.itemclass=0 AND i.questitemflag=0 AND i.attuneable=0
 AND c.buy_cp<c.sell_cp AND c.buy_cp<c.find_cp
 AND (SELECT COUNT(*) FROM nightcap_market_offers used WHERE used.item_id=c.item_id AND used.kind=a.kind)<IF(a.kind='sell',3,2)
 AND NOT EXISTS(SELECT 1 FROM nightcap_market_offers own WHERE own.npc_id=a.npc_id AND own.item_id=c.item_id)
 AND NOT EXISTS(SELECT 1 FROM merchantlist m JOIN npc_types n ON n.merchant_id=m.merchantid WHERE m.item=c.item_id AND n.id=a.npc_id))
FROM nightcap_market_actors a LEFT JOIN nightcap_market_offers o ON o.npc_id=a.npc_id
GROUP BY a.npc_id,a.kind ORDER BY a.npc_id;""").splitlines()
    assert rows, 'No market actors'
    actors, deficits, total, maximum = set(), [], 0, 0
    for line in rows:
        actor, kind, count, eligible = line.split('\t')
        actor, count, eligible = int(actor), int(count), int(eligible)
        assert actor not in actors and kind in ('find', 'sell', 'buy')
        actors.add(actor)
        limit = 1 if kind == 'find' else 2
        assert 0 <= count <= limit and eligible >= 0, 'Actor offer maximum exceeded'
        total += count; maximum += limit
        if count < limit:
            assert eligible == 0, 'Unfilled market slot with an eligible candidate'
            deficits.append({'npc_id': actor, 'kind': kind, 'offers': count, 'maximum': limit, 'eligible_candidates': eligible})
    assert int(op.sql('SELECT COUNT(*) FROM nightcap_market_offers;')) == total
    return {'before': before, 'after': after, 'offers': total, 'maximum_slots': maximum, 'exhausted_actors': deficits}


def preserved_migration(p):
    data = rs.resolved_data()
    assert rs.read(STAGE / 'resume' / 'evidence' / 'resolved-data.json') == data
    started = rs.read(STAGE / 'resume' / 'evidence' / 'resume-started.json')
    assert started['manifest_sha256'] == RESUME_SHA
    inputs, catalog, _ = rs.saved_inputs()
    assert op.load('migration-attempted.json') == inputs
    assert op.load('migration-applied.json') == {'catalog_sha256': rs.CATALOG_SHA, 'legacy_rows_preserved': 9, 'new_timer_rows': 15, 'item_records_preserved': 0}
    op.verify_migration(catalog, rs.CATALOG_SHA, op.load('stopped-timers.json', True), op.load('stopped-item-recasts.json', True))
    rs.preserve_resolved(data); op.untouched(p)
    return data


def restart():
    manifest(); known_holds(); op.stopped()
    p = op.load('preflight.json')
    assert p['manifest_sha256'] == rs.ORIGINAL_MANIFEST
    assert not (FINISH / 'evidence').exists(), 'Finish cannot be replayed'
    for name in ('verified-closed.json', 'opening.json', 'activated.json'):
        assert not (op.EVIDENCE / name).exists(), 'Prior completion attempt'
    state = op.r.state('game')
    assert state['Id'] == FIRST_GAME and state['State']['StartedAt'] == FIRST_STARTED
    assert op.r.compact('game')['image_id'] == p['new_image_id']
    assert op.sql("SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='" + op.SCRATCH + "';").strip() == '0'
    data = preserved_migration(p)
    first_rotation = verify_market(op.load('market-before.json'), FIRST_STARTED)
    assert first_rotation['after'][2] == '81'
    rs.verify_backup(op.load('backup.json'), STAGE / 'private-backup' / 'peq-before.sql.gz')
    rs.verify_backup(rs.read(STAGE / 'resume' / 'evidence' / 'supplemental-backup.json'), STAGE / 'resume' / 'private-backup' / 'peq-before.sql.gz')
    (FINISH / 'evidence').mkdir(mode=0o700)
    save('finish-started.json', {'manifest_sha256': rs.sha(FINISH / 'manifest.json'), 'resolved_holds': known_holds(),
        'prior_game': {'id': FIRST_GAME, 'started_at': FIRST_STARTED}, 'migration_replayed': False, 'database_restored': False})
    try:
        save('first-market-rotation.json', first_rotation)
        op.r.select(p['new_image_id'])
        op.r.compose('up', '-d', '--wait', '--wait-timeout', '240', 'game')
        first = op.r.running(p['new_image_id'], op.binaries(p)); op.health(); op.time.sleep(16); op.health()
        current = op.r.running(p['new_image_id'], op.binaries(p))
        assert first['started_at'] == current['started_at'] and current['started_at'] != FIRST_STARTED
        second_rotation = verify_market(first_rotation['after'], current['started_at'])
        assert second_rotation['after'][2] == '82'
        preserved_migration(p); known_holds()
        assert not op.r.state('gateway')['State']['Running']
        save('second-market-rotation.json', second_rotation)
        op.save('verified-closed.json', {'runtime': current, 'game': op.r.compact('game'), 'market_rotation': second_rotation,
            'cache_sha256': p['cache_sha256'], 'player_tables_preserved': len(data['player']), 'custom_tables_preserved': len(data['custom'])})
        save('hold-resolution.json', {'held_receipts': known_holds(), 'verified_closed_sha256': rs.sha(op.EVIDENCE / 'verified-closed.json'),
            'first_rotation_sha256': rs.sha(FINISH / 'evidence' / 'first-market-rotation.json'),
            'second_rotation_sha256': rs.sha(FINISH / 'evidence' / 'second-market-rotation.json')})
        print('Committed migration and both market rotations verified; gateway closed.', flush=True)
    except BaseException:
        op.hold('Post-migration finish failed/uncertain. Preserve committed migration; do not replay SQL.'); raise


def open_access():
    manifest(); known_holds()
    started = rs.read(FINISH / 'evidence' / 'finish-started.json')
    assert started['manifest_sha256'] == rs.sha(FINISH / 'manifest.json')
    resolution = rs.read(FINISH / 'evidence' / 'hold-resolution.json')
    assert resolution == {'held_receipts': known_holds(), 'verified_closed_sha256': rs.sha(op.EVIDENCE / 'verified-closed.json'),
        'first_rotation_sha256': rs.sha(FINISH / 'evidence' / 'first-market-rotation.json'),
        'second_rotation_sha256': rs.sha(FINISH / 'evidence' / 'second-market-rotation.json')}
    p, a = op.load('preflight.json'), op.load('verified-closed.json')
    assert p['manifest_sha256'] == rs.ORIGINAL_MANIFEST
    assert not (op.EVIDENCE / 'opening.json').exists() and not (op.EVIDENCE / 'activated.json').exists()
    try:
        assert not op.r.state('gateway')['State']['Running'] and op.r.compact('game') == a['game']
        preserved_migration(p); op.health()
        first_rotation = rs.read(FINISH / 'evidence' / 'first-market-rotation.json')
        assert verify_market(first_rotation['after'], a['runtime']['started_at']) == a['market_rotation']
        op.save('opening.json', {'catalog_sha256': rs.CATALOG_SHA, 'finish_manifest_sha256': started['manifest_sha256'], 'resolved_holds': known_holds()})
        op.r.compose('up', '-d', '--wait', '--wait-timeout', '60', 'gateway')
        assert op.r.state('gateway')['State']['Running']; op.health(); op.r.closed_ports()
        current = op.r.running(p['new_image_id'], op.binaries(p))
        assert current['started_at'] == a['runtime']['started_at']
        op.untouched(p)  # No saved-player checks after access may have opened.
        op.save('activated.json', {'status': 'deployed', 'gateway_open': True, 'runtime': current,
            'migration': op.load('migration-applied.json'), 'market_rotation': a['market_rotation'],
            'prior_market_rotation': first_rotation, 'cache_sha256': p['cache_sha256'], 'client_release': op.manifest()['client_release'],
            'database_restored': False, 'owner_gameplay_accepted': False, 'migration_replayed': False, 'authorized_port_preserved': True,
            'finish_manifest_sha256': started['manifest_sha256'], 'player_tables_preserved': a['player_tables_preserved'], 'custom_tables_preserved': a['custom_tables_preserved']})
        print('Cooldown correction deployed; access open.', flush=True)
    except BaseException:
        op.hold('Finish opening failed/uncertain. Preserve subsequent activity and committed migration.'); raise


def initialize():
    global rs, op
    import hashlib
    assert Path(__file__).resolve() == (FINISH / 'finish.py').resolve()
    assert hashlib.sha256((STAGE / 'resume' / 'manifest.json').read_bytes()).hexdigest() == RESUME_SHA
    value = json.loads((STAGE / 'resume' / 'manifest.json').read_text())
    assert hashlib.sha256((STAGE / 'resume' / 'resume.py').read_bytes()).hexdigest() == value['files']['resume.py']
    spec = importlib.util.spec_from_file_location('immutable_cooldown_resume', STAGE / 'resume' / 'resume.py')
    rs = importlib.util.module_from_spec(spec); spec.loader.exec_module(rs); rs.initialize(); op = rs.op
    manifest()


if __name__ == '__main__':
    assert __debug__; os.umask(0o077); initialize()
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['restart', 'open']); action = parser.parse_args().action
    with (op.ROOT / '.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock', 'a') as gm:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB); fcntl.flock(gm, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not (op.ROOT / 'private/gm-maintenance.json').exists() and op.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip() == '1'
        {'restart': restart, 'open': open_access}[action]()
