package main

import (
	"encoding/json"
	"nightcap/eq-launcher/internal/manifest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestGameplayAssetGenerationIsCompleteAndBoundToInputs(t *testing.T) {
	for _, required := range []string{"global_chr.s3d", "global4_chr.s3d", "uifiles/nightcap/equi_merchantwnd.xml", "uifiles/nightcap/equi_tradeskillwnd.xml"} {
		found := false
		for _, name := range gameplayNames {
			if name == required {
				found = true
			}
		}
		if !found {
			t.Fatalf("required gameplay asset missing from signed release: %s", required)
		}
	}
	root := t.TempDir()
	client := t.TempDir()
	spells := []byte("original spells")
	if err := os.WriteFile(filepath.Join(client, "spells_us.txt"), spells, 0600); err != nil {
		t.Fatal(err)
	}
	audit := gameplayAudit{Schema: 1, Status: "generated_not_installed", SourceSpellsSHA256: manifest.Digest(spells), Files: map[string]gameplayFile{}}
	for _, name := range gameplayNames {
		data := []byte("fixture for " + name)
		if strings.HasSuffix(name, ".xml") {
			data = []byte(`<XML ID="EQInterfaceDefinitionLanguage"><Schema xmlns="EverQuestData" xmlns:dt="EverQuestDataTypes" /></XML>`)
		}
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
	if err != nil || len(data) != len(gameplayNames) {
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

func TestNativeSkinRejectsGenericNamespaceRewrite(t *testing.T) {
	for _, source := range []string{
		`<XML xmlns:ns0="EverQuestData"><ns0:Schema /></XML>`,
		`<XML><Schema xmlns="EverQuestData" /></XML>`,
		`<XML><Schema xmlns="EverQuestData" xmlns:dt="wrong" /></XML>`,
		`<XML><Schema xmlns="EverQuestData" xmlns:dt="EverQuestDataTypes" />`,
	} {
		if validateNativeSkin([]byte(source)) == nil {
			t.Fatalf("accepted native-incompatible skin: %s", source)
		}
	}
}

func TestNativeSkinRequiresRealSchemaAndCompleteDocument(t *testing.T) {
	schema := `<Schema xmlns="EverQuestData" xmlns:dt="EverQuestDataTypes" />`
	for _, source := range []string{
		`<XML><!-- ` + schema + ` --></XML>`,
		`<XML><Wrapper>` + schema + `</Wrapper></XML>`,
		`<XML>` + schema + `</XML><`,
		`<XML>` + schema + `</XML><XML/>`,
		`<XML>` + schema + `<Wrong></XML>`,
		`<XML>` + schema + schema + `</XML>`,
	} {
		if validateNativeSkin([]byte(source)) == nil {
			t.Fatalf("accepted invalid skin structure: %s", source)
		}
	}
}

func TestNativeSkinAcceptsStockASCIIEncoding(t *testing.T) {
	source := `<?xml version="1.0" encoding="us-ascii" ?><XML ID="EQInterfaceDefinitionLanguage"><Schema xmlns="EverQuestData" xmlns:dt="EverQuestDataTypes" /></XML>`
	if err := validateNativeSkin([]byte(source)); err != nil {
		t.Fatal(err)
	}
}
