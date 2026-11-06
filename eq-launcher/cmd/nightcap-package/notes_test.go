package main

import (
	"encoding/json"
	"nightcap/eq-launcher/internal/manifest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestLoadPatchHistory(t *testing.T) {
	raw, err := os.ReadFile("../../patch-notes.json")
	if err != nil {
		t.Fatal(err)
	}
	var history []manifest.PatchNote
	if err := json.Unmarshal(raw, &history); err != nil || len(history) == 0 || history[0].Release == 0 {
		t.Fatal("invalid repository patch history", err)
	}
	notes, err := loadPatchNotes("../../patch-notes.json", history[0].Release)
	if err != nil || len(notes) != len(history) {
		t.Fatalf("catalog: %v, %d entries", err, len(notes))
	}
	for _, data := range []string{"[]", "null", `[{"release":1,"date":"2026-10-12","changes":[{"kind":"feature","text":"Added notes."}],"unknown":true}]`, `[] {}`} {
		path := filepath.Join(t.TempDir(), "notes.json")
		if err := os.WriteFile(path, []byte(data), 0600); err != nil {
			t.Fatal(err)
		}
		if _, err := loadPatchNotes(path, 2); err == nil {
			t.Fatalf("accepted %s", data)
		}
	}
	if _, err := loadPatchNotes("../../patch-notes.json", history[0].Release-1); err == nil {
		t.Fatal("accepted future notes")
	}
}

func TestNotesRequireNewDesktopBeforePackaging(t *testing.T) {
	p := profileFixture()
	notes := []manifest.PatchNote{{Release: 1, Date: "2026-10-12", Changes: []manifest.PatchChange{{Kind: "feature", Text: "Added patch summaries."}}}}
	err := buildWithNotes("", "", "", false, 1, "", &p, notes)
	if err == nil || !strings.Contains(err.Error(), "desktop version 0.6.0") {
		t.Fatalf("missing compatibility gate: %v", err)
	}
	p.Version = "0.6.0"
	notes[0].Changes = []manifest.PatchChange{{Kind: "server", Text: "Raised Commonlands drop rates."}}
	err = buildWithNotes("", "", "", false, 1, "", &p, notes)
	if err == nil || !strings.Contains(err.Error(), "desktop version 0.7.0") {
		t.Fatalf("missing server notes gate: %v", err)
	}
}
