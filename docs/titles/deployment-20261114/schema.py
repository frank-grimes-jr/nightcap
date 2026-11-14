"""Exact additive title schema contract, shared by rehearsal and activation."""
import json

TABLES=('nightcap_title_settings','nightcap_title_counters','nightcap_title_awards')
NAMES=','.join("'"+n+"'" for n in TABLES)


def rows(sql,statement):
    return [json.loads(s) for s in sql(statement).splitlines() if s.strip()]


def structure(sql):
    return dict(
        tables=rows(sql,"SELECT JSON_OBJECT('table',table_name,'engine',engine,'type',table_type) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name IN ("+NAMES+") ORDER BY table_name"),
        columns=rows(sql,"SELECT JSON_OBJECT('table',table_name,'column',column_name,'type',data_type,'unsigned',LOCATE('unsigned',column_type)>0,'nullable',is_nullable,'extra',extra) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name IN ("+NAMES+") ORDER BY table_name,ordinal_position"),
        indexes=rows(sql,"SELECT JSON_OBJECT('table',table_name,'index',index_name,'unique',1-non_unique,'seq',seq_in_index,'column',column_name) FROM information_schema.statistics WHERE table_schema=DATABASE() AND table_name IN ("+NAMES+") ORDER BY table_name,index_name,seq_in_index"),
        constraints=rows(sql,"SELECT JSON_OBJECT('table',table_name,'name',constraint_name,'type',constraint_type) FROM information_schema.table_constraints WHERE table_schema=DATABASE() AND table_name IN ("+NAMES+") ORDER BY table_name,constraint_name"),
        triggers=rows(sql,"SELECT JSON_OBJECT('table',event_object_table,'name',trigger_name) FROM information_schema.triggers WHERE trigger_schema=DATABASE() AND event_object_table IN ("+NAMES+") ORDER BY trigger_name"))


def settings(sql):
    return rows(sql,"SELECT JSON_OBJECT('id',id,'catalog_version',catalog_version,'enabled',enabled) FROM nightcap_title_settings ORDER BY id")


def commands(sql):
    return rows(sql,"SELECT JSON_OBJECT('command',command,'access',access,'aliases',aliases) FROM command_settings ORDER BY command")


def without_title(commands):
    return [r for r in commands if r['command']!='titles']


def require_uninstalled(sql):
    assert not structure(sql)['tables'],'Title tables already exist; inspect their owner/state'
    assert sql('SELECT COUNT(*) FROM titles WHERE id>=1900000000 AND id<1900001000').strip()=='0','Reserved title IDs collide'
    for row in commands(sql):
        assert row['command']!='titles' and 'titles' not in (row['aliases'] or '').split('|'),'Title command or alias already exists'


def require_installed(sql,expected,enabled):
    assert structure(sql)==expected,'Title schema/engine/key/trigger drift'
    assert settings(sql)==[dict(id=1,catalog_version=1,enabled=enabled)],'Title control row drift'
    own=[r for r in commands(sql) if r['command']=='titles']
    assert own==[dict(command='titles',access=0,aliases='')],'Title command access/alias drift'
    assert sql('SELECT COUNT(*) FROM titles WHERE id>=1900000000 AND id<1900001000').strip()=='0'


def install(sql,setup,expected,before_commands):
    require_uninstalled(sql)
    assert commands(sql)==before_commands
    sql(setup)
    sql("INSERT INTO command_settings(command,access,aliases) VALUES ('titles',0,'')")
    require_installed(sql,expected,0)
    assert without_title(commands(sql))==before_commands,'Unrelated commands changed'
    assert sql('SELECT COUNT(*) FROM nightcap_title_awards').strip()=='0'
    assert sql('SELECT COUNT(*) FROM nightcap_title_counters').strip()=='0'
    result=sql('UPDATE nightcap_title_settings SET enabled=1 WHERE id=1 AND catalog_version=1 AND enabled=0; SELECT ROW_COUNT()').strip()
    assert result=='1','Enable write acknowledgment is uncertain; inspect, never replay'
    require_installed(sql,expected,1)
