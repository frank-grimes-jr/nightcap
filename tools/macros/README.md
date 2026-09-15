# Darth's Classic Ascended GM kit

Run `/mac darthclassic` in the existing MQ2 RoF2 session on Darth. The installed
copy is `E:/EQ_Local_Dev/mq-rof2/Macros/darthclassic.mac`.

Twenty items cover a practical high-end Classic Human Paladin tank set, with
Ghoulbane/shield and Fiery Avenger as an alternative two-handed weapon. Base
items are Valorium armor, Polished Mithril Mask, Black Sapphire jewelry,
Adamantite Epaulets, Cloak of Flames, Platinum Fire Wedding Ring, Djarn's ring,
Thick Banded Belt, Ghoulbane, Shield of the Immaculate and Fiery Avenger.
This is not an exhaustive proof of encounter-specific BiS. Charm/ammo are not
filled, and no later-era/Fabled items or augments are included.

The current item IDs were queried from PEQ September 15 and checked for Paladin,
Human, no deity restriction, required/recommended level <=50, and duplicate lore
constraints. Darth's saved race/deity is Human/Rodcet Nife. The macro does not
change level or character data directly. It checks the character name, skips
already-held quantities, waits for the expected summoned cursor item, and stops
on timeout or full bags. Allow about 20 free bag slots and use GM summon access.
Existing banked lore items can cause a safe stop; it does not remove them.

The macro was not executed in-game by the agent. Item metadata is verified;
parser/runtime behavior remains for the owner's test.
