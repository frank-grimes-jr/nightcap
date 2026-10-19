"""Capture catalog definitions and anonymous timer diagnostics; SELECT only."""
import datetime

QUERIES = {
    'abilities': 'SELECT id,name,classes,first_rank_id,charges,reset_on_death FROM aa_ability ORDER BY id',
    'ranks': 'SELECT id,spell,spell_type,recast_time,prev_id,next_id FROM aa_ranks ORDER BY id',
    'aa_effect_counts': 'SELECT rank_id,COUNT(*) AS effect_count FROM aa_rank_effects GROUP BY rank_id ORDER BY rank_id',
    'spells': 'SELECT '+','.join(['id','name','recast_time','recovery_time','EndurTimerIndex AS timer_id','IsDiscipline','RecourseLink']+[f'classes{i}' for i in range(1,17)])+' FROM spells_new WHERE recast_time>1000 OR EndurTimerIndex>0 OR IsDiscipline<>0 ORDER BY id',
    'items': 'SELECT id,Name,clicktype,clickeffect,recasttype,recastdelay FROM items WHERE clickeffect>0 AND recastdelay>0 ORDER BY id',
    'timer_schema': "SELECT COLUMN_NAME,COLUMN_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='timers' ORDER BY ORDINAL_POSITION",
    'active_timer_groups': 'SELECT type,COUNT(*) AS characters,MIN(duration) AS min_duration,MAX(duration) AS max_duration,MAX(GREATEST(0,CAST(start AS SIGNED)+duration-UNIX_TIMESTAMP())) AS max_remaining FROM timers WHERE enable=1 AND CAST(start AS SIGNED)+duration>UNIX_TIMESTAMP() GROUP BY type ORDER BY type',
    'clock': 'SELECT UTC_TIMESTAMP() AS utc,UNIX_TIMESTAMP() AS epoch',
}

def capture(query):
    result = {}
    for name, statement in QUERIES.items():
        lines = query('START TRANSACTION READ ONLY; '+statement+'; ROLLBACK;', headers=True).splitlines()
        columns = lines[0].split('\t')
        result[name] = [dict(zip(columns, line.split('\t'))) for line in lines[1:]]
    result['captured_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result['scope'] = 'stopped production catalog and anonymous timer aggregates; no player identifiers'
    return result
