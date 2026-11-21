"""Exercise the paired zone and Perl scripts after the world-storage probe."""
import argparse
from pathlib import PurePosixPath
import sys

from run_world_probe import DB, ROOT, SERVER, docker, local_content_dump, target

sys.path.insert(0, str(ROOT / "tools"))
from cairnwright_spells import server_sql


MODES = ("first", "relog", "adopt2", "release2", "released2",
         "adopt3", "release3", "released3")
QUEST_FILES = ("plugins/cairnwright.pl", "plugins/multiclass.pl",
               "quests/global/spells/44381.pl", "quests/global/spells/44382.pl",
               "quests/ecommons/The_Ancient_Chronicler.pl")


def seed(directory):
    assert target(b"SELECT COUNT(*) FROM character_data WHERE name='Cairnproof' AND class=17").strip() == b"1"
    dump = local_content_dump()
    schemas = ("spells_new base_data character_multiclass character_spells character_memmed_spells "
               "character_alternate_abilities timers damageshieldtypes").split()
    target(docker(*dump, "--no-data", "peq", *schemas))
    for table, predicate in (("spells_new", "id IN (93,205)"),
                             ("base_data", "(class=10 AND level BETWEEN 1 AND 50) OR (class IN (1,2) AND level=1)")):
        target(docker(*dump, "--no-create-info", "--where=" + predicate, "peq", table))
    target(docker(*dump, "--where=id IN (999220,2000)", "peq", "npc_types"))
    target(docker(*dump, "peq", "perl_event_export_settings"))
    target(server_sql().encode())
    target((ROOT / "server-mods/sql/cairnwright_class_base.sql").read_bytes())
    # These two stock-primary comparison characters start with zero/one additional discipline.
    target(b"""INSERT INTO character_data
        (account_id,name,class,race,deity,level,zone_id,x,y,z,wis,cur_hp)
        VALUES (43,'Cairnsecond',1,8,202,1,22,-190,-1725,3.75,88,100),
               (43,'Cairnthird',1,8,202,1,22,-190,-1725,3.75,88,100);
        INSERT INTO character_multiclass(character_id,class2,class3)
        SELECT id,2,NULL FROM character_data WHERE name='Cairnthird';""")
    docker("exec", SERVER, "ln", "-s", "/home/eqemu/server/maps", str(directory / "maps"))
    for name in QUEST_FILES:
        destination = directory / name
        docker("exec", SERVER, "mkdir", "-p", str(destination.parent))
        docker("cp", str(ROOT / "server-mods" / name), f"{SERVER}:{destination}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=PurePosixPath)
    parser.add_argument("action", choices=("seed", *MODES))
    args = parser.parse_args()
    if args.work.parent != PurePosixPath("/tmp") or not args.work.name.startswith("cairnwright-"):
        parser.error("expected the dedicated /tmp/cairnwright-* Docker build directory")
    directory = args.work / "storage-qa"
    if args.action == "seed":
        seed(directory)
        return
    credential = docker("exec", DB, "printenv", "MYSQL_PASSWORD")
    output = docker("exec", "-i", "-w", str(directory), SERVER,
                    str(args.work / "candidate/zone-qa"), args.action, data=credential)
    print(output.decode(errors="replace").strip())


if __name__ == "__main__":
    main()
