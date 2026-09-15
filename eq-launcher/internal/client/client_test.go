package client

import (
	"encoding/hex"
	"fmt"
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
	raw, err := os.ReadFile("../../../eq-client-dll/src/patch_catalog.h")
	if err != nil {
		t.Fatal(err)
	}
	digest, err := hex.DecodeString(SupportedSHA256)
	if err != nil || len(digest) != 32 {
		t.Fatal("invalid supported client digest")
	}
	var values []string
	for _, b := range digest {
		values = append(values, fmt.Sprintf("0x%02X", b))
	}
	source := string(raw)
	if !strings.Contains(source, fmt.Sprintf("kExpectedEqgameSize = %d;", SupportedSize)) ||
		!strings.Contains(source, "kExpectedEqgameSha256[32] = {"+strings.Join(values, ",")+"};") {
		t.Fatal("launcher client guard differs from generated proxy constants")
	}
}

func TestInspectOpenResetsPositionAndRetainsHandle(t *testing.T) {
	file, err := os.CreateTemp(t.TempDir(), "executable")
	if err != nil {
		t.Fatal(err)
	}
	defer file.Close()
	if _, err = file.Write([]byte("unsupported executable")); err != nil {
		t.Fatal(err)
	}
	if err = file.Truncate(SupportedSize); err != nil {
		t.Fatal(err)
	}
	// Leave a nonzero offset: inspection must hash the entire file through the
	// retained handle, not just its unread suffix.
	report, err := InspectOpen(file)
	if err != nil || report.Supported {
		t.Fatalf("wrong open-file report: %+v %v", report, err)
	}
	if _, err = file.Stat(); err != nil {
		t.Fatal("InspectOpen closed caller's guard handle")
	}
}
