"""Extract a read-only stock-icon contact sheet for visual QA; never modify client assets."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw
from augment_audit import ICONS, OUT


def main(client):
    ui = client / 'uifiles/default'
    ids = [500, 517] + ICONS
    out = Image.new('RGB', (13 * 88, 2 * 112), (25, 25, 25))
    draw = ImageDraw.Draw(out)
    for i, icon in enumerate(ids):
        index = icon - 500
        sheet, cell = divmod(index, 36)
        x, y = divmod(cell, 6)  # Native A_DragItem Vertical=true.
        image = Image.open(ui / f'dragitem{sheet + 1}.dds')
        crop = image.crop((x * 40, y * 40, x * 40 + 40, y * 40 + 40))
        out.paste(crop.resize((80, 80)), ((i % 13) * 88, (i // 13) * 112 + 22))
        draw.text(((i % 13) * 88, (i // 13) * 112), str(icon), fill='white')
    out.save(OUT / 'icon-review.png')
    evidence = dict(grid='vertical; 40x40 cells; 6 rows/columns; index=icon-500',
        candidate_ids=ICONS, review='24 stock gems/orbs/crystals; same family icon at all qualities',
        protected_client='read-only reference; no assets modified',
        native_evidence='eqgame RVA2655da sets offset500; RVA265af8 subtracts it; RVA47a860 implements column-major SetCurCell')
    for key, path in [('eqgame', client / 'eqgame.exe'), ('dragitem13', ui / 'dragitem13.dds'),
                      ('animation', ui / 'EQUI_Animations.xml')]:
        evidence[key + '_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    (OUT / 'icon-evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('client', type=Path)
    main(parser.parse_args().client)
