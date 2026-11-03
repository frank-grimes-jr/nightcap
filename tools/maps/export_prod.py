"""Read-only production export for the Nightcap map layer.

Run from the workstation through the deployment SSH runner:
  python <remote.py> tools/maps/export_prod.py > tools/maps/data/prod.json
Only SELECTs and a quest-file grep; nothing is written on the host.
"""
import json, subprocess
from datetime import datetime, timezone

ROOT = '/opt/nightcap/deploy/production'


def run(*args, stdin=None):
    p = subprocess.run(args, cwd=ROOT, input=stdin, text=True, capture_output=True, timeout=300)
    if p.returncode:
        raise RuntimeError(f'{args[-1][:40]} rc={p.returncode}: {(p.stderr or p.stdout)[-2000:]}')
    return p.stdout


def sql(q):
    out = run('docker', 'compose', 'exec', '-T', 'db', 'mariadb', '--defaults-extra-file=/run/secrets/db_backup_config',
              '--batch', '--raw', 'peq', stdin=q)
    lines = out.rstrip('\n').split('\n')
    head = lines[0].split('\t')
    return [dict(zip(head, l.split('\t'))) for l in lines[1:] if l]


GATES = "min_expansion, max_expansion, content_flags, content_flags_disabled"
data = {
    'captured_at': datetime.now(timezone.utc).isoformat(),
    'zones': sql("SELECT short_name, long_name, zoneidnumber, expansion FROM zone WHERE version = 0;"),
    'enabled_flags': [r['flag_name'] for r in sql("SELECT flag_name FROM content_flags WHERE enabled = 1;")],
    'zone_points': sql(f"SELECT zone, x, y, z, target_zone_id, {GATES} FROM zone_points WHERE version = 0;"),
    # Service NPCs: class trainers 20-35, banker 40, merchant 41, special merchants/masters 59-71 (62 = trigger objects, skipped).
    'npcs': sql(f"""SELECT s.zone, s.x, s.y, s.z, n.name, n.lastname, n.class, n.level, se.chance,
        s.min_expansion, s.max_expansion, s.content_flags, s.content_flags_disabled,
        se.min_expansion AS se_min_expansion, se.max_expansion AS se_max_expansion,
        se.content_flags AS se_content_flags, se.content_flags_disabled AS se_content_flags_disabled
        FROM spawn2 s JOIN spawnentry se ON se.spawngroupID = s.spawngroupID JOIN npc_types n ON n.id = se.npcID
        WHERE s.version = 0 AND se.chance > 0;"""),
    'objects': sql(f"""SELECT z.short_name AS zone, o.xpos AS x, o.ypos AS y, o.zpos AS z, o.type,
        o.min_expansion, o.max_expansion, o.content_flags, o.content_flags_disabled
        FROM object o JOIN zone z ON z.zoneidnumber = o.zoneid AND z.version = 0 WHERE o.version = 0 AND o.type BETWEEN 9 AND 52;"""),
}
# NPCs that answer a hail: quest files with a say event. Filename = NPC name (or npc id).
out = run('docker', 'compose', 'exec', '-T', 'game', 'sh', '-c',
          "cd /srv/nightcap/quests && grep -l -i -E 'EVENT_SAY|event_say' */*.pl */*.lua 2>/dev/null || true")
data['hail_npcs'] = sorted(set(out.split()))
print(json.dumps(data))
