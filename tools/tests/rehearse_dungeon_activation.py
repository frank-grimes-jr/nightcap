"""Exercise guarded enablement only in the existing isolated rehearsal DB."""
import hashlib
import json
from pathlib import Path
from rehearse_dungeons import query

ROOT=Path(__file__).resolve().parents[2]
folder=ROOT/'docs/dungeons'
db=json.loads((folder/'rehearsal.json').read_text())['database']
activation=(ROOT/'server-mods/sql/20261016_dungeon_enable.sql').read_text()

def enable(expected=None):
    query('DROP PROCEDURE IF EXISTS nightcap_dungeon_enable_20261016;',db)
    result=query(activation,db,False)
    if expected:
        assert result.returncode and expected in result.stderr,result.stderr
        assert query('SELECT enabled FROM nightcap_dungeon_state;',db).stdout.strip()=='0'
    else:
        assert not result.returncode,result.stderr
        assert query('SELECT enabled FROM nightcap_dungeon_state;',db).stdout.strip()=='1'
        query('UPDATE nightcap_dungeon_state SET enabled=0;',db)

query('UPDATE nightcap_dungeon_state SET enabled=0;',db)
enable()
query('UPDATE items SET damage=damage+1 WHERE id=960000;',db)
try:enable('Dungeon contract mismatch: items/')
finally:query('UPDATE items SET damage=damage-1 WHERE id=960000;',db)
query('ALTER TABLE nightcap_dungeon_deaths ADD COLUMN unexpected INT;',db)
try:enable('Dungeon contract mismatch: nightcap_dungeon_deaths/columns')
finally:query('ALTER TABLE nightcap_dungeon_deaths DROP COLUMN unexpected;',db)
query('CREATE TRIGGER dungeon_test_trigger BEFORE INSERT ON nightcap_dungeon_deaths FOR EACH ROW SET NEW.spawn_id=NEW.spawn_id;',db)
try:enable('Unexpected dungeon storage trigger')
finally:query('DROP TRIGGER dungeon_test_trigger;',db)
enable()
result=dict(status='passed',database=db,activation_sha256=hashlib.sha256(activation.encode()).hexdigest(),
            valid_catalog_enabled=True,item_drift_rejected=True,schema_drift_rejected=True,
            unexpected_trigger_rejected=True,final_enabled=False)
(folder/'activation-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
