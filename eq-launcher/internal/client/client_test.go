package client

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestInspectionNeverChangesFile(t *testing.T) {
	p := filepath.Join(t.TempDir(), "eqgame.exe")
	data := []byte("unsupported test client")
	if err := os.WriteFile(p, data, 0600); err != nil {
		t.Fatal(err)
	}
	r, err := Inspect(p)
	if err != nil || r.Supported || r.ReadyToPlay || r.Size != int64(len(data)) {
		t.Fatalf("%+v %v", r, err)
	}
	after, err := os.ReadFile(p)
	if err != nil || string(after) != string(data) {
		t.Fatal("inspection changed file")
	}
}
func TestCorrectSizeWrongBytes(t *testing.T) {
	p := filepath.Join(t.TempDir(), "eqgame.exe")
	f, err := os.Create(p)
	if err != nil {
		t.Fatal(err)
	}
	if err = f.Truncate(SupportedSize); err != nil {
		t.Fatal(err)
	}
	f.Close()
	r, err := Inspect(p)
	if err != nil || r.Supported || r.ReadyToPlay || len(r.SHA256) != 64 {
		t.Fatalf("%+v %v", r, err)
	}
}
func TestMissingAndDirectory(t *testing.T) {
	dir := t.TempDir()
	for _, p := range []string{dir, filepath.Join(dir, "missing.exe")} {
		if _, err := Inspect(p); err == nil {
			t.Fatal("accepted invalid file")
		}
	}
}
func TestGuardAgreesWithProxySource(t *testing.T) {
	raw, err := os.ReadFile("../../../eq-client-dll/src/dllmain.cpp")
	if err != nil {
		t.Fatal(err)
	}
	s := string(raw)
	if !strings.Contains(s, "kExpectedEqgameSize = 8774656;") || !strings.Contains(s, "// sha256 "+SupportedSHA256) {
		t.Fatal("launcher client guard differs from paired proxy")
	}
}
