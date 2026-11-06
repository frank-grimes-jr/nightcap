"""Apply per-zone Hunt rates to a live wiki/ checkout: zone/item pages, two guides, Change Log."""
from pathlib import Path
import json,shutil,sys
HERE=Path(__file__).resolve().parent
SOURCE='docs/releases/zone-hunt-rates-20261101/README.md'
CHANGE=('<h2 id="hunt-rates-20261101">November 1: zone augments drop three times as often - live</h2>'
 '<p>Zone Hunt augments now drop at <strong>1.5%</strong> per eligible kill (was 0.5%), about one per 67 kills. '
 'Zone equipment stays at 0.5%, and qualities stay Base 60%, Polished 30%, Exalted 8%, Ascension 2%. '
 'Each zone page lists its rates. Chapterhouse and Ashen Compact augments are unchanged. No client update is required. '
 '<a href="zone-hunt.html#drops">How drops work</a>.</p>')
OLD_HUNT=('<strong>0.5% for its zone augment</strong> and <strong>0.5% for its zone equipment</strong>. Both may drop together. '
 'Ordinary loot remains. Each family averages one reward per 200 eligible kills, with no guarantee or pity counter.')
NEW_HUNT=('<strong>1.5% for its zone augment</strong> and <strong>0.5% for its zone equipment</strong> by default; each zone page '
 'lists its exact rates. Both may drop together. Ordinary loot remains. At the defaults an augment averages one per about 67 '
 'eligible kills and equipment one per 200, with no guarantee or pity counter.')
OLD_EQUIP=('<strong>0.5% chance for its zone’s augment</strong> and <strong>0.5% chance for its new gear piece</strong>. '
 'Both can drop together, and ordinary loot remains. Each family averages one drop per 200 eligible kills;')
NEW_EQUIP=('<strong>1.5% chance for its zone’s augment</strong> and <strong>0.5% chance for its new gear piece</strong> by '
 'default; each zone page lists its exact rates. Both can drop together, and ordinary loot remains. At the defaults an augment '
 'averages one drop per about 67 eligible kills and gear one per 200;')

def once(text,old,new):
    assert text.count(old)==1,old[:60];return text.replace(old,new)

def article(wiki,name,fn):
    p=wiki/'articles'/(name+'.json');a=json.loads(p.read_text(encoding='utf-8'))
    assert 'hunt-rates-20261101' not in a['body'],name
    fn(a);a['updated']='2026-11-01'
    if isinstance(a.get('sources'),list):a['sources'].append(SOURCE)
    p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

def catalog(wiki):
    p=wiki/'catalog.py';s=p.read_text(encoding='utf-8')
    s=once(s,"QUALITIES = ['Base', 'Polished', 'Exalted', 'Ascension']\n",
        "QUALITIES = ['Base', 'Polished', 'Exalted', 'Ascension']\n"
        "RATES = json.loads((ROOT.parent / 'config/zone-hunt-rates.json').read_text(encoding='utf-8'))\n\n\n"
        "def rate(slug, kind):\n"
        "    r = {**RATES['default'], **RATES['zones'].get(slug, {})}['augment_chance' if kind == 'Augment' else 'gear_chance']\n"
        "    return f'{r / 100:g}%'\n")
    s=once(s,"body += '</tbody></table></div><h2 id=\"finding-rewards\">","body += f'</tbody></table></div><h2 id=\"finding-rewards\">")
    s=once(s,'independent 0.5% roll for the augment family and 0.5% for the gear family.',
        'independent {rate(z["slug"],"Augment")} roll for the augment family and {rate(z["slug"],"Gear")} for the gear family.')
    s=once(s,'This family rolls at 0.5% per eligible kill,','This family rolls at {rate(z["slug"],i["kind"])} per eligible kill,')
    p.write_text(s,encoding='utf-8',newline='\n')

if __name__=='__main__':
    wiki=Path(sys.argv[1]);(wiki.parent/'config').mkdir(exist_ok=True)
    shutil.copyfile(HERE.parents[2]/'config/zone-hunt-rates.json',wiki.parent/'config/zone-hunt-rates.json')
    catalog(wiki)
    article(wiki,'zone-hunt',lambda a:a.__setitem__('body',once(a['body'],OLD_HUNT,NEW_HUNT)))
    article(wiki,'equipment',lambda a:a.__setitem__('body',once(a['body'],OLD_EQUIP,NEW_EQUIP)))
    article(wiki,'recent-changes',lambda a:a.__setitem__('body',CHANGE+a['body']))
