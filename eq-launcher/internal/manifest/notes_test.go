package manifest

import (
	"bytes"
	"strings"
	"testing"
)

func TestPatchNotes(t *testing.T) {
	for _, name := range []string{"valid", "legacy", "future", "duplicate", "order", "date", "empty", "long", "kind", "old protocol", "server", "server old protocol", "long reason"} {
		t.Run(name, func(t *testing.T) {
			m, trust, key := fixture(t)
			m.MinLauncher, trust.LauncherVersion = "0.6.0", "0.6.0"
			m.PatchNotes = []PatchNote{{Release: 2, Date: "2026-09-15", Changes: []PatchChange{{Kind: "feature", Text: "Added a merchant Sell All button."}}}, {Release: 1, Date: "2026-09-14", Changes: []PatchChange{{Kind: "fix", Text: "Fixed pet summoning."}}}}
			switch name {
			case "legacy":
				m.PatchNotes = nil
				m.MinLauncher = "0.1.0"
			case "future":
				m.PatchNotes[0].Release = 3
			case "duplicate":
				m.PatchNotes[1].Release = 2
			case "order":
				m.PatchNotes[0], m.PatchNotes[1] = m.PatchNotes[1], m.PatchNotes[0]
			case "date":
				m.PatchNotes[0].Date = "2026-02-30"
			case "empty":
				m.PatchNotes[0].Changes = nil
			case "long":
				m.PatchNotes[0].Changes[0].Text = strings.Repeat("x", 241)
			case "kind":
				m.PatchNotes[0].Changes[0].Kind = "html"
			case "old protocol":
				m.MinLauncher = "0.5.0"
			case "server":
				m.MinLauncher, trust.LauncherVersion = "0.7.0", "0.7.0"
				m.PatchNotes[0].Changes = append(m.PatchNotes[0].Changes, PatchChange{Kind: "server", Text: "Raised Commonlands drop rates.", Reason: "Solo players were under-geared."})
			case "server old protocol":
				m.PatchNotes[0].Changes[0].Reason = "Players asked for it."
			case "long reason":
				m.MinLauncher, trust.LauncherVersion = "0.7.0", "0.7.0"
				m.PatchNotes[0].Changes[0].Reason = strings.Repeat("x", 161)
			}
			raw, sig := signed(t, m, key)
			_, err := Verify(raw, sig, trust)
			if (err == nil) != (name == "valid" || name == "legacy" || name == "server") {
				t.Fatalf("unexpected result: %v", err)
			}
			if name == "legacy" && bytes.Contains(raw, []byte("patch_notes")) {
				t.Fatal("changed legacy encoding")
			}
		})
	}
}
