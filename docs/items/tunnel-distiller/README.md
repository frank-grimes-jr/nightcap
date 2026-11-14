# Tunnel augment distiller

Della (Jewelcrafting Supplies) has a permanent Perfected Augmentation Distiller in the test candidate. Find her in the public East Commonlands tunnel workshop at `/loc -1718, -334, 3.75` (Y, X, Z). One distiller removes one augment that requires a reagent through the RoF2 item window. Gear stays in its original slot and the augment returns to the cursor for reuse.

## Catalog and price

The November 14 read-only production check found Della (NPC/shop/spawn 999609, merchant class 41) alone on her shop page with 104 stock entries. Slot 105 was free. Item 52023 is the existing stackable Perfected Augmentation Distiller, type 64. Its raw price is zero and its original NO DROP flag is set. East Commonlands uses ruleset 1 with `Items:FreeTrade=true`. The shared-item loader gives it a 1 platinum base and fixed resale. The purchase handler applies the 1 platinum floor after merchant modifiers. Use the displayed shop quote for the exact purchase price.

`Client::Handle_OP_AugmentItem` accepts a perfected distiller even when the augment specifies a different distiller ID. **Remove** consumes one from the stack, restores the host, and puts the removed augment on the cursor. Augments with a zero distiller requirement can be removed with an empty cursor and no reagent. **Destroy** is a separate, destructive action. Use the RoF2 item window for the perfected distiller. The legacy sealer only recognizes the ordinary matching distiller.

## Apply and withdraw

On the authorized target, capture Della's stock first. Run [forward.sql](forward.sql) in MariaDB against the content database, then use the GM command `#reload merchants` and reopen the shop. A freshly loaded East Commonlands zone also loads the permanent stock. Check:
```sql
SELECT * FROM merchantlist WHERE merchantid=999609 AND (slot=105 OR item=52023);
```
Expect one row with slot 105, item 52023 and probability 100. The change needs only a merchant reload. The existing item cache, client and binaries are sufficient. Apply this addition after any historical full tunnel-catalog rebuild. For withdrawal, run [rollback.sql](rollback.sql) and reload merchants. It compares the owned row before deleting it. Purchased distillers and player gear remain in player custody.

## Player QA on test

1. In public East Commonlands, open Della's shop at the location above. Buy two Perfected Augmentation Distillers. Check the displayed quote, coin deduction and stack count. Close and reopen her shop and confirm she still sells them and her Jewelcrafting supplies.
2. Socket a Singed Goblin Eye (51904, normally a Class IV distiller) into a compatible type-7 armor socket. Put the two perfected distillers in inventory and empty the cursor. Open the armor's item window, select the socket and choose **Remove**. Confirm the prompt describes removal.
3. Verify the same Eye appears once on the cursor, the original armor is still in its slot, and one distiller remains. Put the Eye into another compatible socket. Zone or relog and verify its new socket, the old empty socket, and the remaining distiller.
4. Bank the remaining distiller and repeat removal with a Hunt augment that lists no reagent. Verify the augment returns and the host remains intact. A required-reagent removal attempted without a distiller must leave both the host and augment intact.

## Verification and wiki

Four MariaDB tests passed with the local developer container. Run `python -B docs/items/tunnel-distiller/test_stock.py`. The fixture uses a fresh disposable database and reads the native merchant schema and existing item from PEQ. It exercises install, replay, withdrawal, slot and item collisions, altered afterimages, wrong item type, disabled pricing and wrong or shared merchants. An early fixture run wrote three temporary test entries to the local PEQ merchantlist. All three exact rows were removed and their absence verified before the corrected rehearsal.

`python -B tools/tests/test_tunnel_distiller.py` compiled and ran the actual RoF2 distiller gate and Remove case against seven in-memory inventory scenarios. A perfected distiller returned the Eye to the cursor, emptied the socket, preserved the host and consumed one from stacks of one and two. A matching ordinary distiller and reagent-free removal passed. A wrong-class distiller, destructive solvent offered to Remove, and a missing required reagent left the original socket intact. The six native FreeTrade tests also passed. Client click behavior and persisted inventory after a relog still require player QA.

The Tunnel, Equipment, zone augment guide and Change Log carry the player instructions and links. Home and Features already link the owning guides. Commands, generated reward and zone catalogs, augment stats, recipes and drop rates have no changes. Publish the guide text against the current public wiki once the merchant is activated.

Fifteen integration wiki tests passed. The integration search test checks for both distiller guides and matches the current public test for the four Hillside Dewstone items. Applying just the four article additions to the November 14 staged public guide source passed all five public-language checks and its current Node search suite. All three distiller search records were present. The repository refresh checker reports accumulated drift since October 24; the scoped review leaves the global ledger intact. The public site has not been updated with this candidate.
