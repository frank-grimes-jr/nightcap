package hailstone

import (
	"archive/zip"
	"bytes"
	"os"
	"path/filepath"
	"testing"
)

func TestExtractRejectsRelativeEscape(t *testing.T) {
	var buffer bytes.Buffer
	writer := zip.NewWriter(&buffer)
	if _, err := writer.Create("../escape.exe"); err != nil {
		t.Fatal(err)
	}
	if err := writer.Close(); err != nil {
		t.Fatal(err)
	}
	if err := extract(buffer.Bytes(), t.TempDir()); err == nil {
		t.Fatal("accepted parent path")
	}
}

func TestPackagedPreview(t *testing.T) {
	if !Available() {
		t.Skip("desktop build without optional client")
	}
	data, err := bundle.ReadFile(archive)
	if err != nil {
		t.Fatal(err)
	}
	dir := t.TempDir()
	if err := extract(data, dir); err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"hailstone.exe", "SDL3.dll", "zlib1.dll", "ui/modern/charcreate.lua", "LICENSE", "THIRD_PARTY.md"} {
		info, err := os.Stat(filepath.Join(dir, filepath.FromSlash(name)))
		if err != nil || info.Size() == 0 {
			t.Fatalf("missing runtime file %s", name)
		}
	}
}

func TestSpellOverlay(t *testing.T) {
	parent := []byte("1^Stock\r\n")
	overlay, err := spellOverlay(parent, starterRows)
	if err != nil || !bytes.HasPrefix(overlay, parent) {
		t.Fatal(err)
	}
	for _, id := range []string{"44381^Strike Cairn^", "44382^Sound the Seam^", "44383^Seam Fracture^"} {
		if bytes.Count(overlay, []byte(id)) != 1 {
			t.Fatal(id)
		}
	}
	replay, err := spellOverlay(overlay, starterRows)
	if err != nil || !bytes.Equal(overlay, replay) {
		t.Fatal("replay changed catalog", err)
	}
	if _, err := spellOverlay([]byte("44381^Other"), starterRows); err == nil {
		t.Fatal("accepted conflicting spell")
	}
}
