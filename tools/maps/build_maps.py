"""Build the Nightcap map pack from Brewall maps plus a production export.

  python tools/maps/build_maps.py [--brewall brewall-20240109] [--data tools/maps/data/prod.json] [--out client-maps]

Writes two map sets the RoF2 map window lists in its folder dropdown:
  <out>/Nightcap       tuned for the default white map background
  <out>/Nightcap Dark  tuned for a black map background
Brewall layers (base, _1, _2) keep their legend colours but get WCAG text contrast and
bigger small labels; layer _3 is new Nightcap service data (unmarked zone exits, banks,
merchants, trainers, crafting stations, hail-responsive NPCs), summarised where they stand together.
Map coordinates are the negated game x/y (verified against Ak'Anon's banker).
Also writes <out>/nightcap-maps.zip for players (unzip into the EverQuest folder).
"""
import argparse, json, math, re, zipfile
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Layer _3 colours reuse the legend Brewall draws on every map (Banker, Guild Master, Merchant,
# Mission, Tradeskill Container, Zone), then get the same contrast fix as everything else.
LEGEND = {'zone': (255, 0, 0), 'bank': (255, 210, 0), 'merchant': (0, 127, 0),
          'trainer': (128, 128, 128), 'craft': (128, 0, 128), 'quest': (0, 127, 127)}
TITLES = {'bank': 'Bank', 'trainer': 'Trainers', 'merchant': 'Merchants', 'quest': 'Quest', 'craft': 'Crafting'}
SETS = {'Nightcap': False, 'Nightcap Dark': True}
TEXT = 4.5  # WCAG text contrast against the background; lines use it too so the in-map legend matches labels
CLUSTER = 150    # same-kind services closer than this share one summary label
ZONE_NEAR = 250  # one exit label per wall-length zone line

TRAINERS = dict(zip(range(20, 36), 'Warrior Cleric Paladin Ranger Shadowknight Druid Monk Bard Rogue Shaman Necromancer '
                                   'Wizard Magician Enchanter Beastlord Berserker'.split()))
SERVICES = {40: ('bank', 'Banker'), 41: ('merchant', 'Merchant'), 59: ('merchant', 'Discord_Merchant'),
            60: ('quest', 'Adventure_Recruiter'), 61: ('merchant', 'Adventure_Merchant'), 63: ('quest', 'Tribute_Master'),
            64: ('quest', 'Guild_Tribute'), 66: ('bank', 'Guild_Bank'), 67: ('merchant', 'Radiant_Crystals'),
            68: ('merchant', 'Ebon_Crystals'), 69: ('quest', 'Fellowships'), 70: ('merchant', 'Currency_Merchant'),
            71: ('quest', 'Mercenaries')}
CRAFT = {9: 'Medicine', 10: 'Tinkering_Table', 12: 'Poison_Table', 14: 'Mixing_Bowl', 15: 'Oven', 16: 'Loom',
         17: 'Forge', 18: 'Fletching_Table', 19: 'Brew_Barrel', 20: 'Jeweler\'s_Bench', 21: 'Pottery_Wheel', 22: 'Kiln'}
CRAFT.update({t: 'Racial_Forge' for t in range(31, 53)})
# ponytail: name heuristic for invisible quest controllers; extend if one shows up on a map.
NOT_A_PERSON = re.compile(r'(?i)trigger|invis|controller|spawner|_event|^zone|^#?\d+$')


def contrast(c, dark):
    """WCAG contrast ratio of colour c against a black (dark) or white background."""
    lin = [(v / 255) / 12.92 if v <= 10 else ((v / 255 + 0.055) / 1.055) ** 2.4 for v in c]
    lum = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    return (lum + 0.05) / 0.05 if dark else 1.05 / (lum + 0.05)


@lru_cache(maxsize=None)
def readable(c, dark, target=TEXT):
    """Keep the hue; step toward black (white background) or white (black background) until readable."""
    c = tuple(c)
    while contrast(c, dark) < target:
        c = tuple(round(v + (255 - v) * 0.1) if dark else int(v * 0.9) for v in c)
    return c


def convert(line, dark):
    """Rewrite one Brewall map line for the target background. Unknown lines pass through."""
    if line.startswith('L '):
        f = [s.strip() for s in line[2:].split(',')]
        if len(f) != 9:
            return line
        r, g, b = readable(tuple(int(float(v)) for v in f[6:9]), dark)
        return 'L ' + ', '.join(f[:6] + [str(r), str(g), str(b)])
    if line.startswith('P '):
        f = [s.strip() for s in line[2:].split(',', 7)]
        if len(f) != 8:
            return line
        rgb = readable(tuple(int(float(v)) for v in f[3:6]), dark)
        size = 3 if f[7].lower().startswith('to_') else max(2, int(f[6]))
        return 'P ' + ', '.join(f[:3] + [str(v) for v in rgb] + [str(size), f[7]])
    return line


def allowed(row, expansion, flags, prefix=''):
    """EQEmu content gates: expansion window and content flags."""
    lo, hi = int(row[prefix + 'min_expansion']), int(row[prefix + 'max_expansion'])
    if lo > expansion or (hi != -1 and hi < expansion):
        return False
    need = [f for f in (row[prefix + 'content_flags'] or '').split(',') if f and f != 'NULL']
    off = [f for f in (row[prefix + 'content_flags_disabled'] or '').split(',') if f and f != 'NULL']
    return all(f in flags for f in need) and not any(f in flags for f in off)


def tokens(label):
    words = re.sub(r'\(.*?\)', ' ', label.lower()).replace('#', '').split('_')
    return {w[:5] for w in words if len(w) > 2 and w not in ('the', 'and', 'to')}


def service_points(data, expansion):
    """Yield (zone, x, y, z, category, label) for layer _3, in map coordinates."""
    flags = set(data['enabled_flags'])
    # Exits into zones from a later expansion are not reachable in this era.
    names = {z['zoneidnumber']: z['long_name'] for z in data['zones'] if int(z['expansion']) <= expansion}
    hail = {tuple(p.rsplit('.', 1)[0].split('/', 1)) for p in data['hail_npcs']}
    for p in data['zone_points']:
        x, y = float(p['x']), float(p['y'])
        # 999999 = whole zone edge, (0,0) = book/portal with no fixed spot: no useful map position.
        located = abs(x) < 20000 and abs(y) < 20000 and (x, y) != (0, 0)
        if located and p['target_zone_id'] in names and allowed(p, expansion, flags):
            yield p['zone'], -x, -y, float(p['z']), 'zone', 'To_' + names[p['target_zone_id']].replace(' ', '_')
    for n in data['npcs']:
        cls, name = int(n['class']), n['name']
        if int(n['chance']) < 50 or NOT_A_PERSON.search(name):
            continue
        if not (allowed(n, expansion, flags) and allowed(n, expansion, flags, 'se_')):
            continue
        last = n['lastname'] if n['lastname'] not in ('', 'NULL') else ''
        if cls in TRAINERS:
            cat, tag = 'trainer', 'GM_' + TRAINERS[cls]
        elif cls in SERVICES:
            cat, tag = SERVICES[cls]
            tag = last.replace(' ', '_') or tag
        elif (n['zone'], name) in hail:
            cat, tag = 'quest', 'Quest'
        else:
            continue
        yield n['zone'], -float(n['x']), -float(n['y']), float(n['z']), cat, f"{name.lstrip('#')}_({tag})"
    for o in data['objects']:
        if int(o['type']) in CRAFT and allowed(o, expansion, flags):
            yield o['zone'], -float(o['x']), -float(o['y']), float(o['z']), 'craft', CRAFT[int(o['type'])]


def layer3(points, brewall_labels):
    """Drop what Brewall already labels, then summarise same-kind services standing together."""
    exits = {t for _, _, t, is_exit in brewall_labels if is_exit for t in t}
    kept = []
    for x, y, z, cat, label in points:
        tok = tokens(label)
        if cat == 'zone':  # Brewall labels nearly every exit, just not at the zone point's spot
            if tok & exits or any(kl == label and math.hypot(kx - x, ky - y) < ZONE_NEAR for kx, ky, _, _, kl in kept):
                continue
        elif any(math.hypot(bx - x, by - y) < 40 and tok & btok for bx, by, btok, _ in brewall_labels):
            continue
        kept.append((x, y, z, cat, label))
    out, groups = [p for p in kept if p[3] == 'zone'], []
    for p in (p for p in kept if p[3] != 'zone'):
        g = next((g for g in groups if g[0][3] == p[3] and math.hypot(g[0][0] - p[0], g[0][1] - p[1]) < CLUSTER), None)
        g.append(p) if g else groups.append([p])
    for g in groups:
        if len(g) == 1:
            out.append(g[0])
            continue
        cat = g[0][3]
        # Trainers and merchants read best by what they offer; quest givers and bankers by name.
        split = [p[4].rsplit('_(', 1) + [''] for p in g]
        parts = [name if cat in ('bank', 'quest') or tag in ('', 'Merchant)') else tag.rstrip(')').removeprefix('GM_')
                 for name, tag, *_ in split]
        parts = list(dict.fromkeys(parts))
        text = f'{TITLES[cat]}:'
        for i, part in enumerate(parts):  # ponytail: 120-char cap keeps labels on screen
            if len(text) + len(part) > 120:
                text += f'_+{len(parts) - i}_more'
                break
            text += ('_' if i == 0 else ',_') + part
        cx, cy = sum(p[0] for p in g) / len(g), sum(p[1] for p in g) / len(g)
        out.append((cx, cy, g[0][2], cat, text))
    return out


def brewall_labels(lines):
    out = []
    for line in lines:
        if line.startswith('P '):
            f = [s.strip() for s in line[2:].split(',', 7)]
            if len(f) == 8:
                out.append((float(f[0]), float(f[1]), tokens(f[7]), f[7].lower().startswith('to_')))
    return out


def build(brewall, data, out, expansion):
    by_zone = {}
    for zone, *rest in service_points(data, expansion):
        by_zone.setdefault(zone.lower(), []).append(tuple(rest))
    files = sorted(brewall.glob('*.txt'))
    bases = {f.stem.lower() for f in files if not re.search(r'_\d$', f.stem)}
    stats = {'files': 0, 'layer3_zones': 0, 'layer3_labels': 0}
    for name, dark in SETS.items():
        dest = out / name
        dest.mkdir(parents=True, exist_ok=True)
        labels = {}
        for f in files:
            lines = f.read_text(encoding='latin-1').splitlines()
            zone = re.sub(r'_\d$', '', f.stem).lower()
            labels.setdefault(zone, []).extend(brewall_labels(lines))
            (dest / f.name).write_text('\n'.join(convert(l, dark) for l in lines if l.strip()) + '\n', encoding='latin-1')
            stats['files'] += dark == 0
        for zone, pts in sorted(by_zone.items()):
            if zone not in bases:
                continue  # ponytail: the client needs a base map; zones without Brewall geometry are skipped
            kept = layer3(pts, labels.get(zone, []))
            body = [f'P {x:.4f}, {y:.4f}, {z:.4f}, {r}, {g}, {b}, {3 if cat == "zone" else 2}, {label}'
                    for x, y, z, cat, label in kept for r, g, b in [readable(LEGEND[cat], dark)]]
            if body:
                (dest / f'{zone}_3.txt').write_text('\n'.join(body) + '\n', encoding='latin-1')
                if not dark:
                    stats['layer3_zones'] += 1
                    stats['layer3_labels'] += len(body)
    return stats


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('--brewall', default=REPO / 'brewall-20240109', type=Path)
    a.add_argument('--data', default=REPO / 'tools/maps/data/prod.json', type=Path)
    a.add_argument('--out', default=REPO / 'client-maps', type=Path)
    args = a.parse_args()
    expansion = json.loads((REPO / 'era.json').read_text())['expansion']
    data = json.loads(args.data.read_text())
    stats = build(args.brewall, data, args.out, expansion)
    # Player download: unzip into the EverQuest folder.
    with zipfile.ZipFile(args.out / 'nightcap-maps.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(Path(__file__).with_name('PLAYER-README.txt'), 'Nightcap-Maps-README.txt')
        for name in SETS:
            for f in sorted((args.out / name).glob('*.txt')):
                z.write(f, f'maps/{name}/{f.name}')
    print(json.dumps({'expansion': expansion, 'export': data['captured_at'], **stats}))
