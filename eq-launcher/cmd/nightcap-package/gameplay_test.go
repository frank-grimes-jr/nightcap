package main

import (
	"encoding/json"
	"nightcap/eq-launcher/internal/manifest"
	"os"
	"path/filepath"
	"testing"
)

func TestGameplayAssetGenerationIsCompleteAndBoundToInputs(t *testing.T) {
	root := t.TempDir()
	client := t.TempDir()
	spells := []byte("original spells")
	if err := os.WriteFile(filepath.Join(client, "spells_us.txt"), spells, 0600); err != nil {
		t.Fatal(err)
	}
	audit := gameplayAudit{Schema: 1, Status: "generated_not_installed", SourceSpellsSHA256: manifest.Digest(spells), Files: map[string]gameplayFile{}}
	for _, name := range gameplayNames {
		data := []byte("fixture for " + name)
		path := filepath.Join(root, filepath.FromSlash(name))
		if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(path, data, 0600); err != nil {
			t.Fatal(err)
		}
		audit.Files[name] = gameplayFile{Size: int64(len(data)), SHA256: manifest.Digest(data)}
	}
	writeAudit := func() {
		raw, err := json.Marshal(audit)
		if err != nil {
			t.Fatal(err)
		}
		if err = os.WriteFile(filepath.Join(root, "audit.json"), raw, 0600); err != nil {
			t.Fatal(err)
		}
	}
	writeAudit()
	data, err := loadGameplayAssets(root, filepath.Join(client, "eqgame.exe"))
	if err != nil || len(data) != 9 {
		t.Fatalf("expected complete generation: %d %v", len(data), err)
	}
	t.Run("tampered asset", func(t *testing.T) {
		path := filepath.Join(root, "mur.eqg")
		original, _ := os.ReadFile(path)
		if err := os.WriteFile(path, []byte("changed"), 0600); err != nil {
			t.Fatal(err)
		}
		if _, err := loadGameplayAssets(root, filepath.Join(client, "eqgame.exe")); err == nil {
			t.Fatal("accepted changed archive")
		}
		if err := os.WriteFile(path, original, 0600); err != nil {
			t.Fatal(err)
		}
	})
	t.Run("source mismatch", func(t *testing.T) {
		audit.SourceSpellsSHA256 = manifest.Digest([]byte("other"))
		writeAudit()
		if _, err := loadGameplayAssets(root, filepath.Join(client, "eqgame.exe")); err == nil {
			t.Fatal("accepted different source spells")
		}
		audit.SourceSpellsSHA256 = manifest.Digest(spells)
		writeAudit()
	})
	t.Run("missing required file", func(t *testing.T) {
		saved := audit.Files["poknowledge_chr.txt"]
		delete(audit.Files, "poknowledge_chr.txt")
		writeAudit()
		if _, err := loadGameplayAssets(root, filepath.Join(client, "eqgame.exe")); err == nil {
			t.Fatal("accepted incomplete generation")
		}
		audit.Files["poknowledge_chr.txt"] = saved
		writeAudit()
	})
}
