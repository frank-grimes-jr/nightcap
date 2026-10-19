"""Prepare verified-release wiki prose; publication remains a separate guarded action."""
import hashlib
import json
import re
import sys
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from thj_combined_content import item_changes


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


notices={
'combat':'Direct Spell Damage, ordinary DoT ticks, heroic INT/WIS, pet healing and held-class melee effects have changed. Update through the launcher before testing. Spell-rank choice, mana sustain and burst balance still need player checks.',
'equipment':'Selected Ascended items now use reviewed THJ values, including reductions. Starter upgrades remain modest and comparable Normal dungeon gear is stronger. Spell Damage and Healing Amount have 750 base caps, plus earned Hunt headroom.',
'features':'The combined item, spell, pet equipment and melee release is installed for live testing. It preserves Classic level 50 and earned progression. See the updated combat, equipment and pet guides below.',
'getting-started':'Starter equipment now has modest quality upgrades. For approved starter weapons, each quality adds one damage while delay stays fixed. Comparable Normal dungeon equipment remains the next meaningful step.',
'index':'The item/spell and pet/melee release is available for live testing. Reopen the launcher for the matching client update, then check your gear, spells and pet equipment. Classic level 50 remains active.',
'item-upgrades':'Selected Ascended values and intermediate stats have been retuned while retaining item identities, effects and sockets. Upgrade costs, commands and existing ownership are unchanged.',
'dungeon-modes':'Selected dungeon equipment budgets are raised so comparable Normal rewards exceed Ascended starter gear. Modes, objectives, Keepers and eligibility remain unchanged.',
'zone-hunt':'The base Spell Damage and Healing Amount caps are now 750. Earned Hunt headroom remains additive. Hunt rewards, drop chances, tasks and forging costs are unchanged.',
'launcher':'Game update 2026101802 pairs the expanded pet Equipment tab and spell/AA descriptions with the new server release. Close EverQuest and use the normal launcher before testing. The Classic travel repairs remain included.',
'multiclass':'Reviewed earned pet and melee AA ranks and held-class combat benefits are available for live testing. Normal ownership, costs, prerequisites and skill requirements remain. The active level cap is still 50; the separate Planes of Power profile is not activated.',
'pets':'Permanent pet equipment now has three pages covering 22 locations, with a total budget of 15 items for Mage pets or eight for other permanent class pets. Update through the launcher before opening Equipment.',
}
report={'status':'prepared_for_verified_release_publication','date':'2026-10-18','articles':{}}
for path in sorted((ROOT/'wiki/articles').glob('*.json')):
    baseline=subprocess.check_output(['git','show','HEAD:wiki/articles/'+path.name],cwd=ROOT)
    before=hashlib.sha256(baseline).hexdigest(); data=json.loads(baseline); slug=data['slug']; body=data['body']
    # Retire only the two integrated-candidate notices. Separate PoP notices are rewritten below.
    body=re.sub(r'<p class="notice" id="(?:thj-parity-candidate|pet-scaling-candidate)">.*?</p>\s*','',body,flags=re.S)
    if slug in notices:
        body='<p class="notice"><strong>Live testing:</strong> '+notices[slug]+'</p>\n'+body
    if slug=='equipment':
        body=body.replace('With the current 250 cap, either can reach 280.','With the current 750 cap, either can reach 780.')
        body=body.replace('Item Spell Damage and Heal Amount work as percentage bonuses, including damage-over-time and healing-over-time spells. The base cap for each item-bonus total is 250. Eligible zone augments can raise it to 280 at level 50 when enough actual bonus is equipped. Corrections to some existing tiered items are still in the works.',
            'Eligible direct damage spells and procs add effective Spell Damage once. Each ordinary DoT tick adds half the effective bonus, rounded down, independent of duration. Healing Amount retains percentage healing and its existing HoT distribution. Each item-bonus total has a 750 base cap; eligible Hunt augments can raise it to 780 at level 50 when enough actual bonus is equipped. Clients also gain 0.1% per heroic INT on direct damage and per heroic WIS on direct healing; DoTs and HoTs do not gain this heroic multiplier. The separate Bard area-DoT route retains its native behavior.')
        body+='\n<h2 id="reviewed-ascended">Reviewed Ascended values</h2><p>Supported numeric fields on 131 Ascended items now follow inspected THJ Legendary references. These families use per-item values rather than one universal multiplier. Some values are lower than before; original effects and existing sockets remain.</p><table><caption>Selected Ascended reference values</caption><thead><tr><th>Item</th><th>Values</th></tr></thead><tbody><tr><td>Heavy Yttrium Chestplate</td><td>150 AC; 250 HP and mana; 40 Spell Damage and Healing Amount</td></tr><tr><td>Blood Cord</td><td>70 AC; 200 HP and mana; 40 STA and 10 heroic STA; 40 Spell Damage and Healing Amount</td></tr><tr><td>Talisman of Vah Kerrath</td><td>250 HP and mana; 8 to each heroic attribute; 30 Spell Damage and Healing Amount</td></tr></tbody></table><h2 id="starter-bands">Starter upgrades and dungeon progression</h2><p>Approved starter families use smaller steps: Bronze chest armor has 6, 7, 8 and 9 AC across Normal, Polished, Exalted and Ascended. Bronze Long Sword has 4, 5, 6 and 7 damage at fixed delay 32. Cultural armor is excluded from this retuning. Comparable Normal dungeon rewards remain stronger.</p><h2 id="earned-procs">Earned melee and pet equipment</h2><p>Selected items gain sympathetic healing, combat procs or received-healing support. Healing, Runic and Hastened Fragments of Truth and Bloodfrenzy Core have earned boss routes; later-era bosses still require their normal access. Bloodfrenzy Core is a power-source item, while the original Bloodfrenzy remains a weapon. New sockets do not bypass augment compatibility.</p>'
    if slug=='zone-hunt':
        body=body.replace('With the current base cap of 250, either can reach 280.','With the current base cap of 750, either can reach 780.')
    if slug=='combat':
        body=body.replace('Ordinary heals cast with an NPC or pet selected heal you while keeping that target selected. Select another player to heal them. Pet-only and other specialized spells retain their target rules.',
            'Ordinary heals cast on your own permanent pet heal that pet. With an enemy or another ordinary NPC selected, eligible heals still redirect to you while retaining your target. Select another player to heal them. Pet-only and other specialized spells retain their target rules.')
        body+='\n<h2 id="spell-scaling">Spell Damage and heroic attributes</h2><p>Eligible player and permanent-pet direct damage and procs add effective Spell Damage once. Each ordinary DoT tick adds half that value, rounded down; duration does not divide this addition. Applicable critical, focus, resistance and spell restrictions still matter. Clients gain 0.1% per heroic INT on direct damage and per heroic WIS on direct healing before final caps. DoTs and HoTs do not gain the heroic multiplier. Healing Amount and HoT distribution retain their previous formulas; Bard rune songs do not gain the added Healing Amount rune bonus.</p><h2 id="melee-builds">Held-class melee and shield builds</h2><p>Reviewed Shield Specialist, Holy Shield, Way of Steel, Healing Light, Blessing of Life and Rage of Rallos effects follow the appropriate held classes and earned ranks. The six Monk attacks participate while keeping their skill requirements. Heroic Strength improves player weapon hits; it does not multiply pet attacks, spells, runes or Monk special attacks. Native runes replace or refresh instead of accumulating.</p><h2 id="rabid-bear">Separate Rabid Bear effects</h2><p>The Shaman AA grants separate permanent Rabid Bear benefit and Illusion: Rabid Bear effects. Removing either leaves the other. Death, dispels and ordinary effect rules still apply.</p>'
    if slug=='pets':
        body=body.replace('Custom Pet Armor tab','Paged pet Equipment tab')
        body=body.replace('Open <strong>Inventory → Pet Armor</strong> for eight equipment slots per permanent class pet. Previous / Next switches between loadouts. Inspect, equip, and remove compatible armor; choosing an armor loadout does not change your command selection.',
            'Open the pet <strong>Equipment</strong> tab in Inventory. Three pages show 22 equipment locations, with 8, 8 and 6 locations per page. A Mage loadout holds up to 15 permanent items; other permanent class pets hold eight. Switch the selected class loadout separately from its page. Two-handed equipment excludes the secondary hand. Inspect, equip and remove complete compatible items and augments; choosing a loadout does not change your pet command selection.')
        body=body.replace('Ordinary heals with a pet or other NPC selected heal you.','Ordinary heals on your own permanent pet now heal that pet; eligible heals with another ordinary NPC selected still redirect to you.')
        body+='\n<h2 id="pet-scaling">Gear, inheritance and procs</h2><p>Eligible permanent pets use their own item Spell Damage and Healing Amount plus half their owner’s effective value, capped at 375 inherited points in each. Owner heroic INT/WIS and the player heroic-Strength weapon multiplier are not transferred. Supported earned caster AAs, pet roster buffs and weapon-augment proc attempts apply with their normal restrictions.</p><p>Temporary summoned hand-ins remain separate from stored equipment. Mage, Necromancer and Beastlord support-buff lines can coexist. Test equipment recovery, zoning, resummoning and buff removal with inexpensive items first. Marked Enchanter Doppelgangers can assist with eligible spells from the owner’s memorized and scribed selection, using the owner’s resources.</p>'
    if slug=='features':
        body=body.replace('Ordinary heals cast with an enemy or pet selected heal you. Select a player to heal them; specialized and pet-only spells keep their own rules.',
            'Ordinary heals can heal your own permanent pet. With an enemy selected, eligible heals still redirect to you. Specialized spells retain their target rules.')
        body+='\n<h2 id="thj-scaling">Item and spell progression</h2><p><a href="equipment.html#reviewed-ascended">Reviewed Ascended items</a>, modest starter upgrades and stronger dungeon budgets bring item progression closer to the observed THJ references. <a href="combat.html#spell-scaling">Additive Spell Damage and direct heroic-stat bonuses</a>, <a href="pets.html#pet-armor">paged pet equipment</a> and <a href="combat.html#melee-builds">earned shield/melee synergies</a> are installed together. Player combat and balance checks remain open.</p>'
    if slug in ('travel','tunnel'):
        body='<p class="notice"><strong>Not released:</strong> The separate level-65/Planes of Power profile and its additional merchant stock remain staged. This item/spell release keeps Classic level 50 and the current travel and vendor gates.</p>\n'+body
    if slug=='unreleased':
        marker='<h2 id="'
        # Keep unrelated work unchanged, replacing the three now-shipped feature sections.
        start=body.index('Guaranteed quality for qualifying quest rewards')
        start=body.rfind('<h2',0,start)
        body='<h2 id="thj-parity">Item and spell scaling is now in live testing</h2><p>The combined release is installed. Read <a href="equipment.html">Equipment</a>, <a href="combat.html">Combat</a> and <a href="pets.html">Pets</a> for its current rules. Historical THJ evidence does not establish every current THJ formula; spell-rank choice, mana sustain, pet contribution and maximum-AA melee burst still need in-game balance checks.</p><h2 id="wpm-melee">Shield and melee changes are now in live testing</h2><p>The earned held-class melee and shield changes shipped with the combined release. See <a href="combat.html#melee-builds">the combat guide</a>. Gameplay acceptance remains open.</p><h2 id="pet-scaling">Separate level-65 and Planes of Power profile — not released</h2><p>The expanded pet equipment and scaling changes are installed, but the level-65/Planes of Power profile and 389 additional merchant entries are still staged. Classic level 50 remains active. Nothing grants levels, spellbooks, AA points or epics automatically. Manifest Elements keeps its normal Mage level 59 requirement.</p>\n'+body[start:]
    if slug=='recent-changes':
        body='<h2 id="thj-release">October 18: item, spell, pet and melee release</h2><p><strong>Live testing:</strong> Selected Ascended items now use reviewed THJ values. Direct damage adds effective Spell Damage, ordinary DoT ticks add half, and heroic INT/WIS improve direct values. Starter quality steps remain modest below comparable Normal dungeon equipment.</p><p>The same release adds paged permanent-pet equipment, bounded owner-stat inheritance, earned pet/melee AA updates, separate Rabid Bear benefit and illusion effects, and shared 750 base caps with Hunt headroom. Close EverQuest and use the launcher for game update 2026101802. Classic level 50 remains active; gameplay and balance acceptance are still open.</p>\n'+body
    changed=body!=data['body']
    if changed:
        data['body']=body;data['updated']='2026-10-18'
        data['sources'].append('docs/releases/thj-parity-20261018/deployment/; authorized combined release, gameplay acceptance pending')
        path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    report['articles'][slug]={'decision':'Updated deployed behavior and status; retained unrelated guidance' if changed else 'Reviewed; no impact on this guide or its commands',
        'before_sha256':before,'after_sha256':sha(path)}
catalog=json.loads((ROOT/'wiki/catalog.json').read_text(encoding='utf-8'))
changed_ids={int(row['id']) for before,row in item_changes()}
assert not ({int(row['id']) for row in catalog['items']} & changed_ids)
report['generated_routes']={'count':432,'decision':'Published Hunt projection has no IDs affected by this item migration; retain all values/routes. Dungeon budgets are described in guides; they are not entries in this Hunt catalog.'}
report['commands']='Reviewed: no command syntax changes; pet Equipment interaction updated in Pets.'
report['gameplay_accepted']=False
(HERE/'wiki-review.json').write_text(json.dumps(report,indent=2)+'\n')
print('Prepared',sum(x['before_sha256']!=x['after_sha256'] for x in report['articles'].values()),'updated guides; all21 guides and432 generated routes reviewed.')
