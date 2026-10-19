"""Read-only diagnosis of closed-access verification hold."""
import json
import sys
from pathlib import Path

stage=Path('/opt/nightcap/releases/thj-parity-20261018')
sys.path.insert(0,str(stage));import rollout as op
op.initialize();p=op.load(stage/'evidence/preflight.json')
current=op.checksums(op.TABLES)
result={'content_mismatches':{n:{'expected':p['after'][n],'actual':v} for n,v in current.items() if v!=p['after'][n]},
 'rules':op.sql('SELECT ruleset_id,rule_name,rule_value,notes FROM rule_values ORDER BY ruleset_id,rule_name;'),
 'clone_rules':op.sql('SELECT ruleset_id,rule_name,rule_value,notes FROM rule_values ORDER BY ruleset_id,rule_name;',op.CLONE),
 'services':{s:op.r.compact(s) for s in ('game','gateway','db','web','tunnel')},
 'held_receipts':{f.name:op.load(f) for f in (stage/'evidence').glob('held-*.json')},
 'player_preserved':op.saved_state()==op.load(stage/'evidence/stopped-state.json')}
print(json.dumps(result))
