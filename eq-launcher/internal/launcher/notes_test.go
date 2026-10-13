package launcher

import (
	"context"
	"nightcap/eq-launcher/internal/manifest"
	"testing"
)

func TestVerifiedNotesSurvivePatchingAndSnapshotsAreIndependent(t *testing.T) {
	c, _, _ := fixture(t)
	if len(c.Snapshot().PatchNotes) != 0 {
		t.Fatal("notes shown before verification")
	}
	if err := c.Check(context.Background()); err != nil {
		t.Fatal(err)
	}
	s := c.Snapshot()
	if len(s.PatchNotes) != 1 || s.PatchNotes[0].Release != s.Release {
		t.Fatal("verified notes missing")
	}
	s.PatchNotes[0].Changes[0].Text = "modified"
	c.show("staging", "Patching")
	if c.Snapshot().PatchNotes[0].Changes[0].Text != "Added patch summaries." {
		t.Fatal("snapshot mutated controller or notes lost during patching")
	}
	if err := c.SelectClient(context.Background(), t.TempDir()); err != nil {
		t.Fatal(err)
	}
	if len(c.Snapshot().PatchNotes) != 0 {
		t.Fatal("old client notes retained")
	}
}

func TestUnverifiedNotesNeverReachUI(t *testing.T) {
	c, raw, sig := fixture(t)
	raw[len(raw)-2] ^= 1
	c.fetch = func(context.Context, Policy) ([]byte, manifest.Signature, error) { return raw, sig, nil }
	if err := c.Check(context.Background()); err == nil {
		t.Fatal("tampered notes accepted")
	}
	if len(c.Snapshot().PatchNotes) != 0 {
		t.Fatal("unverified notes exposed")
	}
}
