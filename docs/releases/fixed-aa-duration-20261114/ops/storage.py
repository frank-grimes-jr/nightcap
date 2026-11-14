"""Round-trip signed coordinate markers in a temporary table cloned from live PEQ."""
import json
from probe import LOAD,remote,write

QUERY = """
CREATE TEMPORARY TABLE tmp_fixed_aa_roundtrip LIKE character_buffs;
INSERT INTO tmp_fixed_aa_roundtrip(character_id,slot_id,spell_id,caster_level,caster_name,ticsremaining,counters,
 numhits,melee_rune,magic_rune,persistent,dot_rune,caston_x,caston_y,caston_z,ExtraDIChance,instrument_mod)
 VALUES(1,1,21773,50,'fixture',2,0,0,0,0,0,0,29825531,59789,21773,0,0),
       (1,2,30736,50,'fixture',2,0,0,0,0,0,0,0,11987,-30736,0,0);
SELECT spell_id,ticsremaining,caston_x,caston_y,caston_z,
 CASE WHEN caston_z>0 THEN CAST(caston_x AS SIGNED)*60000+caston_y ELSE caston_y END AS decoded_ms
 FROM tmp_fixed_aa_roundtrip ORDER BY slot_id;
DROP TEMPORARY TABLE tmp_fixed_aa_roundtrip;
"""

if __name__ == "__main__":
    data = json.loads(remote(LOAD+"\nprint(json.dumps(prior.sql("+repr(QUERY)+").splitlines()))"))
    expected = [[21773,2,29825531,59789,21773,29825531*60000+59789],[30736,2,0,11987,-30736,11987]]
    rows = [[int(v) for v in s.split("\t")] for s in data]
    assert rows == expected
    write("storage-roundtrip.json",dict(result="PASS",temporary_table_like="character_buffs",rows=rows))
    print(rows)
