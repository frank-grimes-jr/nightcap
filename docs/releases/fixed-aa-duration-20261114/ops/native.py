"""Reproduce the running heroic-cast zone and compile only the new feature hunks."""
import argparse
import importlib.util
from pathlib import Path

ROOT = Path("/tmp/nightcap-fixed-aa-duration-20261114")
PARENT = Path("/tmp/nightcap-heroic-cast-sources-20261114")
ZONE = "67874c589830a5bb07f8a2b84566b39cf20e1dd3583fa54bbf29599ccb5ada8b"
INPUTS = "7f7b43895976b0931b1d9f9a3c212dbfbcb0bf89bb5ccd96f689ea56ba1511e9"
spec = importlib.util.spec_from_file_location("heroic",PARENT/"native.py")
heroic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(heroic)
builder = heroic.combat
parent_context = heroic.context


def context(profile):
    try:
        source,build,objects,_,replacements,args,_,_ = parent_context(profile)
    finally:
        builder.PINS = {"shipping":ZONE}
    old = PARENT/"shipping/candidate"
    proof = builder.load(old/"build.json")
    assert proof["zone"] == builder.sha(old/"zone") == ZONE
    assert proof["link_manifest_sha256"] == builder.sha(old/"link-inputs.json") == INPUTS
    for name,pin in builder.load(old/"link-inputs.json").items():
        assert builder.sha(build/name) == pin, name
    for name,meta in proof["units"].items():
        obj = old/(name+".o")
        assert builder.sha(obj) == meta["candidate"]
        replacements[name] = obj
    return source,build,objects,old/"zone",replacements,args,old/"vfs.json",old/"zone.pch"


def refine():
    """Archive a superseded isolated candidate and compile the final patch."""
    folder = ROOT/"shipping/candidate"
    assert (folder/"build.json").is_file()
    key = builder.load(folder/"build.json")["zone"]
    archive = folder.with_name("superseded-"+key[:8])
    assert not archive.exists()
    folder.rename(archive)
    # Keep the old candidate intact. Rebuild with exact retained predecessor
    # objects/paths, PCH and fresh source-level verification at the final path.
    heroic.prepare("shipping")
    builder.main("shipping","candidate")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase",choices=("baseline","candidate","refine"))
    phase = parser.parse_args().phase
    heroic.ROOT = builder.ROOT = ROOT
    heroic.context = builder.context = context
    builder.PINS = {"shipping":ZONE}
    if phase == "refine":
        refine()
        raise SystemExit(0)
    if phase == "candidate":
        heroic.prepare("shipping")
    builder.main("shipping",phase)
