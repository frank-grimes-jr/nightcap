"""Project explicit public spell controls; never publish raw runtime/character exports."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/balance'))
from spell_math import effect_value, buff_duration


def project():
    snapshot = ROOT / 'tools/balance/fixtures/classic-20260912-v2.json.gz'
    stock = ROOT / 'docs/pok/hub-stock-audit.json'
    archive = ROOT / 'docs/releases/thj-parity-20261018/evidence/native-results.tar.gz'
    rows = {r['id']: r for r in json.loads(gzip.decompress(snapshot.read_bytes()))['tables']['spells_new']}
    levels = {r['spell_id']: r['original_class_levels'] for r in json.loads(stock.read_text())['stock']}
    spells = []
    for ident in [54, 732, 360, 6, 17, 15, 114, 671]:
        r = rows[ident]
        ticks = buff_duration(50, r['buffdurationformula'], r['buffduration'])
        spells.append(dict(id=str(ident), name=r['name'], kind='heal' if r['goodEffect'] else 'dot' if ticks else 'damage',
                           base=abs(effect_value(r['formula1'], r['effect_base_value1'], r['max1'], 50)),
                           cast=r['cast_time']/1000, recovery=r['recovery_time']/1000,
                           cooldown=r['recast_time']/1000, mana=r['mana'], ticks=ticks,
                           group='blood-dot' if ident in [360, 6] else '',
                           classes=[i+1 for i, level in enumerate(levels[ident]) if level <= 50],
                           evidence='Native value control · Oct 18' if ident in [54,17,360] else 'Content formula · Sep 12'))
    controls = []
    with tarfile.open(archive) as tar:
        for suffix in ['starter-normal', 'starter-ascended', 'dungeon-normal', 'observed-ascended']:
            b = json.load(tar.extractfile('parity-l50-'+suffix+'-result.json'))['builds'][0]
            for p in b['spell_probes']:
                values = sorted({o['amount'] for o in p['outcomes'] if o['landed_percent'] == 100})
                controls.append(dict(spell=str(p['spell_id']), sd=b['spell_damage'], ha=b['heal_amount'],
                                     hint=b['heroic_int'], hwis=b['heroic_wis'], landed=values))
    public = dict(version=1, level=50, spells=spells, controls=controls,
                  contentDate='2026-09-12', controlDate='2026-10-18', reviewed='2026-10-22')
    (ROOT/'wiki/build-lab-data.json').write_text(json.dumps(public, indent=2)+'\n', encoding='utf-8')
    inputs = [snapshot, stock, archive, ROOT/'server-mods/code/zone/effects.cpp', ROOT/'server-mods/code/common/nightcap_spell_scaling.h']
    (ROOT/'docs/build-lab/data-provenance.json').write_text(json.dumps({p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}, indent=2)+'\n')


if __name__ == '__main__':
    project()
