"""Pair a separate owner-local RoF2 copy with just the two TEST spell rows."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
from sympathetic_content import overlay

WORKSPACE = Path("E:/EQ_Local_Dev")
SOURCE = WORKSPACE / "Client_RoF2_Dev/everquest_rof2"
ARTIFACT = WORKSPACE / "artifacts/sympathetic-classic-test-20261113"
CLIENT = ARTIFACT / "player-client"
ASSETS = {
    "spells_us.txt": "fd0a88825eaacb46d438bb3739ffe4bc05607f9e3122a3a34f4520fc05551599",
    "dbstr_us.txt": "56e7747e05e3f0b5dabd47ee3c8c54a3cd4cda7eb39bb4238309b7352e84ae7d",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    assert CLIENT.is_dir() and not CLIENT.is_junction() and not CLIENT.is_symlink()
    assert SOURCE != CLIENT and SOURCE not in CLIENT.parents
    for file in ("eqgame.exe", "eqmain.dll", "dinput8.dll"):
        assert sha((SOURCE / file).read_bytes()) == sha((CLIENT / file).read_bytes())
    receipts = {}
    for file, parent in ASSETS.items():
        raw = (SOURCE / file).read_bytes()
        assert sha(raw) == parent
        result = overlay(raw, file)
        assert result.startswith(raw) and len(result) > len(raw) and overlay(result, file) == result
        target = CLIENT / file
        assert not target.exists() or target.stat().st_nlink == 1
        target.write_bytes(result)
        receipts[file] = {"base": parent, "candidate": sha(target.read_bytes()),
                          "bytes_added": len(result) - len(raw)}
    assert (SOURCE / "eqhost.txt").read_text().strip().splitlines() == ["[LoginServer]", "Host=localhost:5998"]
    (CLIENT / "eqhost.txt").write_bytes(b"[LoginServer]\r\nHost=127.0.0.1:5998\r\n")
    # eqgame creates fresh local INI defaults if an owner has no preferences.
    if not (CLIENT / "eqclient.ini").exists():
        shutil.copyfile(SOURCE / "eqclient.ini", CLIENT / "eqclient.ini")
    (ARTIFACT / "local-client.json").write_text(json.dumps(receipts, indent=2) + "\n")
    launch = [
        "@echo off", "setlocal", 'cd /d "%~dp0player-client" || exit /b 1',
        'findstr /x /c:"Host=127.0.0.1:5998" eqhost.txt >nul || exit /b 2',
    ]
    for file, receipt in receipts.items():
        launch.append('powershell -NoProfile -Command "if ((Get-FileHash -Algorithm SHA256 -LiteralPath '
                      + "'" + file + "').Hash -ne '" + receipt["candidate"] + "') { exit 3 }\" || exit /b 3")
    launch.append('start "" "%CD%\\eqgame.exe" patchme')
    (ARTIFACT / "Play Local Sympathetic Test.cmd").write_bytes(("\r\n".join(launch) + "\r\n").encode("ascii"))
    print(json.dumps(receipts))


if __name__ == "__main__":
    main()
