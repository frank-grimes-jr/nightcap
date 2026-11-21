"""Verify a generated spell file against the actual preimage and SQL field policy."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cairnwright_spells import FIELDS, client_file, variants


def verify(original, paired):
    assert client_file(original) == paired and paired.startswith(original)
    rows = [r.split(b"^") for r in paired[len(original):].splitlines() if r]
    assert len(rows) == 3
    for row, (_, _, fields) in zip(rows, variants()):
        assert len(row) == 237
        for column, value in fields.items():
            assert row[FIELDS[column]] == str(value).encode(), column
        assert row[104:120] == [b"255"] * 16
    assert [r[98] for r in rows] == [b"6", b"6", b"5"]
    assert [r[85] for r in rows] == [b"0", b"0", b"1"]
    assert [r[86] for r in rows] == [b"254", b"254", b"0"]
    # Duplicate application, different ID using our name, and template drift.
    for bad in (paired, original + b"\n55000^strike cairn^\n", original.replace(b"205^True North^", b"205^Wrong Name^")):
        try:
            client_file(bad)
        except ValueError:
            continue
        raise AssertionError("Expected a candidate preflight failure")


if __name__ == "__main__":
    verify(Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes())
    print("PASS: original bytes, three records, all modified fields, class levels, collisions and template drift")
