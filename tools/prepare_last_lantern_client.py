"""Write the reviewed signer program; no signing or publication occurs here."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]


def main():
    baseline=ROOT/'artifacts/last-lantern-20261107/baseline/channel.json'
    candidate=baseline.parent.parent/'candidate/spells_us.txt'
    assert hashlib.sha256(baseline.read_bytes()).hexdigest()=='3f02f08d31734883dc6269fc2e0e1980750e491f6d335f7ae91d384bfd9daa92'
    source=(ROOT/'docs/releases/character-stats-shield-block-20261106/prepare.go').read_text()
    source=source.replace('Run a copy in eq-launcher/cmd/aa-level-sign','Run a copy in eq-launcher/cmd/last-lantern-sign')
    source=source.replace('LauncherVersion: "0.6.0"','LauncherVersion: "0.7.0"')
    source=source.replace('38805c66c797cece765796c53a9e27a3fcf76c2d8c1c6d7b3415c07611b64fbf',hashlib.sha256(baseline.read_bytes()).hexdigest())
    source=source.replace('2026110603','2026110605').replace('2026110604','2026110701')
    source=source.replace('uifiles/nightcap/equi_inventory.xml','spells_us.txt')
    source=source.replace('cf0402a36438a2a667add72cb37c259fd276a7ac1ac444fae7f8e7f63eb05648',hashlib.sha256(candidate.read_bytes()).hexdigest())
    notes=[('feature','The Last Lantern carries the Adventure Journal from level 20 through 50: three shared chapters, five oath paths to choose from, and eight further chapters.'),
           ('feature','Meet Mera, Oren and Tovin, recover lost names in private company expeditions, and face the Hollow Witness.'),
           ('feature','Earn eight matching armor pieces. Oren offers legal woven, leather, chain and plate fits, with earned refits at levels 40, 46 and 50.'),
           ('feature',"Refits preserve augments and custom dye. Campaign equipment is personal; Wayfarer's Oath powers share a ten-minute recovery."),
           ('feature','Begin with the Ancient Chronicler in the East Commonlands tunnel. Fully exit EverQuest and press Play to install the journal spells.'),
           ('feature','Released for live QA. Rendered armor appearances and full encounter balance still await player acceptance.')]
    start=source.index('\tm.PatchNotes = append(');end=source.index('\n\n\tchanged :=',start)
    line='\tm.PatchNotes = append([]manifest.PatchNote{{Release: m.Release, Date: "2026-11-07", Changes: []manifest.PatchChange{'
    line+=','.join('{Kind: '+json.dumps(k)+', Text: '+json.dumps(t)+'}' for k,t in notes)+'}}}, old.PatchNotes...)'
    source=source[:start]+line+source[end:]
    source=source.replace('Augment-description','Last Lantern spell')
    out=ROOT/'docs/adventure-journal/release-20261107/prepare_client.go'
    out.write_text(source,encoding='utf-8')
    command=ROOT/'eq-launcher/cmd/last-lantern-sign';command.mkdir(exist_ok=True)
    (command/'main.go').write_text(source,encoding='utf-8')
    print('Staged signer and six client-note entries; no publication.')


if __name__=='__main__':main()
