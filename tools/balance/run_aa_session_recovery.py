"""Real native Process entry termination and fresh-process loader/retry proof.

Only the isolated balance clone may be used. No network login or uncertain
COMMIT is simulated by this test. Failed evidence and unexpected rows are kept.
"""
import json
from aa_policy_preflight import read_json
from aa_owned_view_controls import prepare
from run_aa_owned_core import counts
import run_aa_projection as io

TRIGGER = 'nightcap_session_recovery_failure'
RUNTIME = '/tmp/nightcap-balance-aa-recovery-20260913'


def require(value, message):
    if not value:
        raise ValueError(message)


def make_input(matrix, classes, operations, fresh=False):
    value = prepare(matrix)['input']
    value.update(profile_save_fixture=True, capture_class_release_transport=True,
                 capture_disconnect_events=True)
    value['builds'][0].update(test_character_id=1, classes=classes, equipment=[])
    # Deliberately wrong wallet in a fresh process proves the native profile
    # loader replaces the diagnostic build wallet with persisted values.
    if fresh:
        value['builds'][0]['aa_budget'] = 999
    probe = value['aa_ownership_probe']
    probe.update(first_rank_id=267, initial_spent_points=35, initial_expended_points=5,
                 operations=operations, inspect_earned=True, inspect_lifecycle=True,
                 inspect_classes=True, inspect_release_details=True,
                 inspect_release_packets=True, inspect_disconnect=True,
                 load_release_skills=not fresh, watched_skills=[0,4],
                 allowed_failures=['release_third','process_invalid_session','save','load'])
    if fresh:
        probe.pop('initial_spent_points')
        probe.pop('initial_expended_points')
    return value


def check_state(step, released, valid=True):
    classes = [1,7,0] if released else [1,7,12]
    aa = [] if released else [{'first_rank_id':267,'rank_count':6,'charges':0}]
    for key, expected in {
        'loaded_classes':classes, 'saved_classes':classes,
        'class_mask':sum(1 << c for c in classes if c),
        'earned_rank_count':0 if released else 6,
        'earned_state_valid':valid,
        'stored':aa, 'profile':aa, 'effective_rank_count':0 if released else 6,
        'unspent_points':47 if released else 17, 'spent_points':5 if released else 35,
        'expended_points':5,
        'saved_points':{'wallet':47 if released else 17,'spent':5 if released else 35,'expended':5},
        'saved_skills':[{'id':0,'value':260},{'id':4,'value':0 if released else 250}],
        'loaded_skills':[{'id':0,'value':260},{'id':4,'value':0 if released else 250}],
    }.items():
        require(step.get(key) == expected, f'{step["operation"]}.{key}: {step.get(key)!r} != {expected!r}')


def main():
    output = io.DOCS/'aa-session-recovery.json'
    require(not output.exists(), 'Refusing to overwrite recovery evidence')
    require(not (io.DOCS/'aa-session-recovery-preimage.json').exists(), 'Refusing to overwrite recovery preimage')
    require(io.DATABASE == 'nightcap_balance_20260912' and not any(counts().values()), 'Unexpected clone/fixtures')
    require(not io.sql('SELECT character_id FROM character_stats_record;').strip(), 'Stats fixtures exist')
    require(not io.sql('SELECT id FROM character_skills WHERE id=1;').strip(), 'Character 1 skills exist')
    require(io.sql('SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE();').strip() == '0', 'Existing triggers')
    io.RUNTIME = RUNTIME
    build = json.loads(io.command(['docker','exec',io.SERVER,'cat',RUNTIME+'/native-build-manifest.json']))
    binary = io.command(['docker','exec',io.SERVER,'sha256sum',RUNTIME+'/balance-zone']).decode().split()[0]
    require(binary == build['binary_sha256'], 'Changed diagnostic binary')
    original_classes = io.sql('SELECT * FROM character_multiclass ORDER BY character_id;')
    original_skills = io.sql('SELECT * FROM character_skills ORDER BY id,skill_id;')
    original = io.sql('SELECT class2,class3,applied_at FROM character_multiclass WHERE character_id=1;').strip().split('\t')
    require(original[:2] == ['2','12'], 'Unexpected class fixture')
    catalog = io.digest(io.dump_tables())
    event_setting = io.sql('SELECT * FROM player_event_log_settings WHERE id=11;')
    require(event_setting.strip().split('\t')[1:3] == ['Went Offline','0'], 'Unexpected logout event setting')
    matrix = read_json(io.DOCS/'gear-source-inputs.json')
    initial = make_input(matrix,[1,7,12],['load','release_third','process_invalid_session','save'])
    creation = initial['builds'][0]['creation']
    stats = ','.join('`'+k+'`' for k in ('str','sta','agi','dex','int','wis','cha'))
    values = ','.join(str(int(creation[k])) for k in ('str','sta','agi','dex','int','wis','cha'))
    io.write(io.DOCS/'aa-session-recovery-preimage.json', {
        'classes':original_classes,'skills':original_skills,'event_setting':event_setting,'catalog_sha256':catalog})
    report = {'status':'running','binary_sha256':binary,'inputs':[initial], 'runs':[]}
    try:
        io.sql('UPDATE player_event_log_settings SET event_enabled=1 WHERE id=11 AND event_enabled=0;')
        io.sql(f"START TRANSACTION; INSERT INTO character_data (id,account_id,name,class,level,level2,race,deity,ingame,aa_points,aa_points_spent,e_expended_aa_spent,{stats}) VALUES (1,1,'AA_Lifecycle_Probe',1,50,50,1,396,1,17,35,5,{values}); UPDATE character_multiclass SET class2=7,class3=12 WHERE character_id=1; INSERT INTO character_skills (id,skill_id,value) VALUES (1,0,260),(1,4,250); INSERT INTO character_alternate_abilities (id,aa_id,aa_value,charges) VALUES (1,267,6,0); COMMIT;")
        before_row = io.sql('SELECT * FROM character_data WHERE id=1;')
        # Skill-write failure fires once in release; logout does not write skills.
        io.sql('DELIMITER //\nCREATE TRIGGER '+TRIGGER+" BEFORE UPDATE ON character_skills FOR EACH ROW BEGIN SET @nightcap_class_release_failures=COALESCE(@nightcap_class_release_failures,0)+1; SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='injected recovery skill failure'; END //\nDELIMITER ;")
        try:
            report['runs'].append(io.native(initial))
        finally:
            io.sql('DROP TRIGGER '+TRIGGER+';')
        steps = report['runs'][0]['report']['aa_ownership_probe']['steps']
        require([s['operation'] for s in steps] == initial['aa_ownership_probe']['operations'], 'Missing initial operations')
        check_state(steps[0],False)
        require(steps[0]['saved_ingame'] == 1 and steps[0]['stats_rows'] == 0, 'Logout preimage differs')
        for s in steps[1:]:
            check_state(s,False,False)
            require(s['injected_release_failures'] == 1, 'Injection not observed exactly once')
            require(s['session_exited'] and not s['connected'] and s['release_packets']['transport_closed'], 'Old session remains active')
            require(s['release_packets']['publication'] is None, 'Old session published success')
        require(not steps[1]['success'] and not steps[2]['success'] and not steps[3]['success'], 'Failed session operation succeeded')
        require(steps[1]['disconnect_events'] == [] and steps[2]['disconnect_events'] == [{'event_type_id':11,'character_id':1}], 'Native logout event missing/duplicate')
        require(steps[3]['disconnect_events'] == steps[2]['disconnect_events'], 'Later save emitted another logout')
        require(steps[2]['saved_ingame'] == 0 and steps[2]['stats_rows'] == 1, 'Native disconnect writes missing')
        columns = io.sql('SHOW COLUMNS FROM character_data;').splitlines()
        idx = [line.split('\t')[0] for line in columns].index('ingame')
        after = io.sql('SELECT * FROM character_data WHERE id=1;').strip().split('\t')
        expected = before_row.strip().split('\t'); expected[idx] = '0'
        report['character_row_check'] = {'before':before_row,'after':io.sql('SELECT * FROM character_data WHERE id=1;'),'columns':[line.split('\t')[0] for line in columns], 'only_ingame_changed':after==expected}
        require(after == expected, 'Disconnect changed unexpected character fields')
        for released, ops in ((False,['load_saved_profile','release_third']), (True,['load_saved_profile','release_third'])):
            value = make_input(matrix,[1,7] if released else [1,7,12],ops,True)
            report['inputs'].append(value)
            report['runs'].append(io.native(value))
            fresh = report['runs'][-1]['report']['aa_ownership_probe']['steps']
            require([s['operation'] for s in fresh] == ops, 'Missing fresh-process operations')
            check_state(fresh[0],released)
            check_state(fresh[1],True)
            require(fresh[0]['success'] and fresh[1]['success'] == (not released), 'Release retry outcome differs')
            require(all(s['connected'] and not s['session_exited'] and not s['release_packets']['transport_closed'] and s['disconnect_events']==[] for s in fresh), 'Fresh session unexpectedly closed or logged out')
        report['status'] = 'native_checks_passed_cleanup_pending'
    except Exception as error:
        report.update(status='failed_fixtures_preserved', error=str(error))
        io.write(output,report)
        raise
    finally:
        io.sql('UPDATE player_event_log_settings SET event_enabled=0 WHERE id=11 AND event_enabled=1;')
    # Cleanup only after exact native state and identity checks passed.
    require(io.sql('SELECT id,name FROM character_data;').strip() == '1\tAA_Lifecycle_Probe', 'Unexpected cleanup character')
    require(io.sql('SELECT character_id FROM character_stats_record;').strip() == '1', 'Unexpected stats rows')
    io.sql(f"START TRANSACTION; DELETE FROM character_stats_record WHERE character_id=1; DELETE FROM character_skills WHERE id=1; DELETE FROM character_data WHERE id=1; UPDATE character_multiclass SET class2=2,class3=12,applied_at='{original[2]}' WHERE character_id=1; COMMIT;")
    report['final'] = {'remaining_rows':counts(), 'catalog_unchanged':io.digest(io.dump_tables())==catalog,
        'classes_restored':io.sql('SELECT * FROM character_multiclass ORDER BY character_id;')==original_classes,
        'skills_restored':io.sql('SELECT * FROM character_skills ORDER BY id,skill_id;')==original_skills,
        'stats_empty':not io.sql('SELECT character_id FROM character_stats_record;').strip(),
        'event_setting_restored':io.sql('SELECT * FROM player_event_log_settings WHERE id=11;')==event_setting,
        'triggers_empty':io.sql('SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE();').strip()=='0'}
    cleanup_ok = not any(report['final']['remaining_rows'].values()) and all(v for k,v in report['final'].items() if k!='remaining_rows')
    report['status'] = 'passed' if cleanup_ok else 'failed_cleanup'
    io.write(output,report)
    require(cleanup_ok, 'Cleanup differs')
    print(json.dumps({'status':report['status'],'processes':len(report['runs']),'final':report['final']},indent=2))


if __name__ == '__main__':
    main()
