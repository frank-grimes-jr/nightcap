package main

import (
	"nightcap/eq-launcher/internal/manifest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestLoadPatchHistory(t *testing.T) {
	notes, err := loadPatchNotes("../../patch-notes.json", 2026101202)
	if err != nil || len(notes) != 6 {
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
	if _, err := loadPatchNotes("../../patch-notes.json", 2026101201); err == nil {
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
}
