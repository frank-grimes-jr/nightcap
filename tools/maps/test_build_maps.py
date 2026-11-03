"""python tools/maps/test_build_maps.py"""
import build_maps as m

# Contrast: white/yellow darken on light maps, black lightens on dark maps, dark colours stay.
assert m.contrast(m.readable((240, 240, 0), False), False) >= m.TEXT
assert m.readable((127, 64, 0), False) == (127, 64, 0) and m.readable((255, 0, 0), True) == (255, 0, 0)
assert m.contrast(m.readable((0, 0, 0), True), True) >= m.TEXT and m.contrast(m.readable((0, 0, 255), True), True) >= m.TEXT

# Line and label rewriting keeps geometry, label text and Brewall's hue; tiny labels grow.
assert m.convert('L 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 255, 255, 255', False) == 'L 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 108, 108, 108'
assert m.convert('P 1, 2, 3, 0, 127, 0, 1, Bob_(Merchant)', False) == 'P 1, 2, 3, 0, 127, 0, 2, Bob_(Merchant)'
assert m.convert('P 1, 2, 3, 255, 0, 0, 2, to_Steamfont, east', True).endswith('255, 0, 0, 3, to_Steamfont, east')

# Content gates follow era and flags.
row = {'min_expansion': '-1', 'max_expansion': '-1', 'content_flags': 'NULL', 'content_flags_disabled': 'NULL'}
assert m.allowed(row, 0, set())
assert not m.allowed({**row, 'min_expansion': '3'}, 0, set())
assert not m.allowed({**row, 'content_flags': 'x'}, 0, set()) and m.allowed({**row, 'content_flags': 'x'}, 0, {'x'})

# Layer 3 skips what Brewall already labels (exits zone-wide), our own repeats, and summarises groups.
brew = m.brewall_labels(['P 852, -1348, -30, 255, 210, 0, 2, Clockwork_(Banker)',
                         'P 0, 5000, 0, 255, 0, 0, 3, to_West_Commonlands'])
pts = [(862, -1348, -30, 'bank', 'a_clockwork_banker_(Banker)'),
       (0, 0, 0, 'zone', 'To_West_Commonlands'), (0, 0, 0, 'zone', 'To_Kithicor_Forest'),
       (0, 10, 0, 'zone', 'To_Kithicor_Forest'),
       (0, 0, 0, 'trainer', 'Garran_(GM_Warrior)'), (20, 0, 0, 'trainer', 'Brakka_(GM_Berserker)'),
       (40, 0, 0, 'quest', 'Matron_Restora_(Quest)')]
assert [p[4] for p in m.layer3(pts, brew)] == ['To_Kithicor_Forest', 'Trainers:_Warrior,_Berserker', 'Matron_Restora_(Quest)']
print('ok')
