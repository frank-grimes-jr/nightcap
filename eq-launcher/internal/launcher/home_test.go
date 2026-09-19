package launcher

import (
	"errors"
	"path/filepath"
	"testing"
	"testing/fstest"
)

func TestQAHomeIsolation(t *testing.T) {
	dir := t.TempDir()
	exe := func() (string, error) { return filepath.Join(dir, "qa.exe"), nil }
	forbidden := func() (string, error) { t.Fatal("QA must not access user config"); return "", nil }
	p := Policy{Bundle: fstest.MapFS{}}
	home, err := StateHome(p, exe, forbidden)
	if err != nil || home != filepath.Join(dir, "launcher-state") {
		t.Fatalf("home=%s error=%v", home, err)
	}
	broken := func() (string, error) { return "", errors.New("no executable") }
	if _, err = StateHome(p, broken, forbidden); err == nil {
		t.Fatal("must fail closed")
	}
	normal, err := StateHome(Policy{}, forbidden, func() (string, error) { return dir, nil })
	if err != nil || normal != filepath.Join(dir, "NightcapLauncher") {
		t.Fatal(normal, err)
	}
}
