"""Render the reviewable dungeon reward catalog from the actual item compiler."""
from pathlib import Path
from dungeon_catalog import items,DUNGEONS
from classic_dungeon_rewards import DESIGNS

ROOT=Path(__file__).resolve().parents[1]
SLOTS={4:'Head',131072:'Chest',128:'Arms',1536:'Wrist',4096:'Hands',262144:'Legs',524288:'Feet',64:'Shoulders',18:'Ear',98304:'Finger',32:'Neck',8:'Face',256:'Back',1048576:'Waist',8192:'Primary (two handed)',24576:'Primary / secondary',2048:'Range',0:'Bag'}

def main():
    data=items()
    lines=['# Classic raid rewards — candidate, not released','',
      'Every dungeon has three exclusive final-boss designs, with Polished and Ascended versions. '
      'The 14 added dungeons contribute 42 designs / 84 definitions. All 414 dungeon items are MAGIC, '
      'including the existing shared and seven-dungeon rewards. The existing 220 non-MAGIC items gain only that flag.', '',
      'Final Raid bosses keep the existing 80% / 18% / 2% roll for one / two / three distinct designs. '
      'Each independently rolls 90% Polished / 10% Ascended. These corpse drops supplement native loot and the personal completion reward. '
      'Grind uses the existing Normal completion pool. Already recorded drops and entitlements are not rerolled.', '',
      'New stats use the same level-band, slot and quality ceilings as the reviewed current dungeon templates. '
      'Different stat pairs and resistances suit each relic; no new haste, focus, proc, heroic, regeneration or multiplier is added. '
      'New recommended levels follow the dungeon band. Plane items require level 46; other new rewards have no required level. '
      'All remain tradeable, permanent, non-LORE and zero-resale, with no forging recipe.', '',
      'Planar clicks require the item to be equipped, level 46 and a 10-second cast. '
      'Polished/Ascended versions and duplicate copies share their respective cooldown: Fear 5 minutes, Hate 10 minutes, Sky 15 minutes. '
      'Ascended does not improve the click. Cast/reuse figures are base values subject to native focus reductions. The Astrolabe uses ordinary Levitate, requiring one Bat Wing (13068); '
      'it respects native no-levitation zones, including the Plane of Sky itself, and does not replace island keys.', '',
      'The item descriptions below are original Nightcap fiction. Their broad themes draw on official accounts of '
      '[Cazic Thule, the Faceless](https://www.everquest.com/news/imported-eq-enus-51455), '
      '[Innoruuk and the kidnapped elven royalty](https://www.everquest.com/news/imported-eq-enus-50364), and '
      '[Veeshan and her first brood](https://www.everquest.com/news/imported-eq-enus-50403). '
      'These relics are custom creations, not a claim about original EverQuest loot.', '',
      'Numbers are **Polished / Ascended**. SD/HA means Spell Damage / Heal Amount. Effects and exact field values are in `../catalog.json`.','']
    for zone,_,_,band,_ in DUNGEONS[7:]:
        lines += [f'## {zone} — equipment band {band}','']
        for design,(title,_,role,_,lore) in enumerate(DESIGNS[zone]):
            pair=[r['values'] for r in data if r['source']==zone and r['design']==design]
            a,b=pair
            val=lambda key:f"{a[key]} / {b[key]}"
            lines += [f'### {title}',f'*{lore}*','',f"- IDs: {a['id']} / {b['id']}; {SLOTS[a['slots']]}; {role}."]
            if a['itemclass']==1:lines += [f"- Capacity: {val('bagslots')} slots; {val('bagwr')}% weight reduction."]
            else:
                if a['damage']:lines += [f"- Damage: {val('damage')}; delay: {a['delay']}." ]
                lines += [f"- AC {val('ac')}; HP {val('hp')}; mana {val('mana')}; endurance {val('endur')}.",
                          f"- Spell Damage {val('spelldmg')}; Heal Amount {val('healamt')}."]
                stats=[k for k in ('astr','asta','aagi','adex','aint','awis','acha','mr','fr','cr','pr','dr') if a[k]]
                lines += ['- '+ '; '.join(k.upper()+': '+val(k) for k in stats)+'.']
            if a['clickeffect']>0:lines += [f"- Equipped click: {a['clickname']}; reuse {a['recastdelay']//60} minutes."]
            lines += ['']
    (ROOT/'docs/dungeons/classic-rewards-20261022/REWARDS.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')

if __name__=='__main__':main()
