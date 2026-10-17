"""Read-only OVH probe; run as root over SSH and retain the JSON locally."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

ROOT = Path('/opt/nightcap/deploy/production')


def run(args, data=None):
    return subprocess.run(args, cwd=ROOT, input=data, capture_output=True,
                          text=True, check=True).stdout


query = """
SELECT ruleset_id, rule_name, rule_value FROM rule_values
WHERE rule_name IN ('Character:DeathExpLossLevel', 'Character:DeathExpLossMaxLevel',
'Character:UseDeathExpLossMult', 'Character:DeathExpLossMultiplier', 'Character:DeathKeepLevel')
ORDER BY ruleset_id,rule_name;
"""
db = ['docker','compose','exec','-T','db','mariadb',
      '--defaults-extra-file=/run/secrets/db_backup_config','--batch',
      '--skip-column-names','peq']
result = {
    'checked_at_utc': datetime.now(timezone.utc).isoformat(),
    'operation': 'read_only',
    'rules': run(db, query).strip().splitlines(),
    'rulesets': run(db, 'SELECT ruleset_id,name FROM rule_sets ORDER BY ruleset_id;').strip().splitlines(),
    'world_ruleset_variable': run(db, "SELECT value FROM variables WHERE varname='RuleSet';").strip() or '(absent: default)',
    'zone_rulesets': run(db, 'SELECT ruleset,COUNT(*) FROM zone GROUP BY ruleset;').strip().splitlines(),
    'binaries': run(['docker','compose','exec','-T','game','sha256sum',
                     '/opt/nightcap/bin/world','/opt/nightcap/bin/zone']).strip().splitlines(),
    'services': run(['docker','compose','ps','--format','{{.Service}} {{.State}} {{.Health}}']).strip().splitlines(),
}
assert [v for v in result['rules'] if '\tCharacter:DeathExpLossLevel\t' in v] == ['1\tCharacter:DeathExpLossLevel\t10']
print(json.dumps(result, indent=2))
