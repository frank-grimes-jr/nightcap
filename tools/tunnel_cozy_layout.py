"""Relaxed EC workshop bays. Coordinates are world X/Y, not /loc Y/X."""
from tunnel_services import pos

# Suppliers face a usable approach, not an exact row or a station's back wall.
SUPPLIERS = {
    999601: (-377, -1726, -363, -1740),  # Berrin / smithing I
    999602: (-369, -1756, -357, -1747),  # Torvik / smithing II
    999603: (-395, -1768, -383, -1754),  # Haldra / smithing III
    999611: (-352, -1741, -366, -1748),  # Nelli / tinkering
    999608: (-359, -1697, -345, -1701),  # Aven / tailoring
    999609: (-334, -1718, -339, -1703),  # Della / jewelcraft
    999610: (-337, -1687, -347, -1679),  # Corin / fletching
    999616: (-357, -1786, -343, -1775),  # Rusk / poison I
    999617: (-338, -1794, -334, -1779),  # Vessa / poison II
    999612: (-162, -1721, -146, -1732),  # Yara / alchemy I
    999613: (-140, -1714, -144, -1731),  # Fenrik / alchemy II
    999614: (-121, -1732, -139, -1735),  # Mosslin / alchemy III
    999615: (-144, -1752, -143, -1735),  # Usha / alchemy IV
    999618: (-296, -1745, -282, -1740),  # Ilyen / research I
    999619: (-279, -1755, -266, -1762),  # Meris / research II
    999620: (-285, -1778, -274, -1765),  # Davin / research III
    999621: (-267, -1806, -265, -1820),  # Finn / fishing
    999604: (-285, -1805, -295, -1793),  # Pella / pottery
    999605: (-337, -1816, -323, -1812),  # Odel / baking I
    999606: (-332, -1845, -328, -1829),  # Mara / baking II
    999607: (-311, -1831, -315, -1817),  # Fenna / brewing
    999226: (-373, -1801, -366, -1790),  # Epic Forgemaster; Veyra stays
}

# Leave the buff bots where players know them. These three face their shared
# south-facing approach from the sides, within 35 units of a buffer.
SERVICES = {
    999220: (-215, -1585, -207, -1600),
    999225: (-161, -1579, -173, -1591),
    999600: (-169, -1614, -181, -1606),
}

STATIONS = {
    999600: ('Loom', -356, -1715, 128),
    999601: ('Oven', -351, -1827, 128),
    999602: ('Forge', -400, -1742, 128),
    999603: ('Brewing Barrel', -299, -1850, 128),
    999604: ('Pottery Wheel', -302, -1817, 448),
    999605: ('Kiln', -285, -1840, 0),
}

# Exact existing model donors; no new assets, loot or interactive services.
# ID: (zone door ID, donor ID, model, X, Y, heading, size)
ORNAMENTS = {
    999611: (216, 999606, 'CAMPFIRE', -315, -1784, 0, 35),
    999612: (217, 405, 'BARREL3', -378, -1786, 32, 75),
    999613: (218, 40600, 'HANGLANT', -266, -1737, 0, 60),
}

def placements():
    return {ident: pos(*pose) for ident, pose in (SUPPLIERS | SERVICES).items()}
