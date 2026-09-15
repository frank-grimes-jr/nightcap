package launchlock

import (
	"context"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"
	"testing"
	"time"

	"nightcap/eq-launcher/internal/installguard"
)

func fixture(t *testing.T) string {
	t.Helper()
	dir := filepath.Join(t.TempDir(), "client-ä")
	if err := os.MkdirAll(filepath.Join(dir, "uifiles", "nightcap"), 0700); err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"eqgame.exe", "uifiles/nightcap/window.xml", "eqclient.ini"} {
		if err := os.WriteFile(filepath.Join(dir, filepath.FromSlash(name)), []byte("original"), 0600); err != nil {
			t.Fatal(err)
		}
	}
	return dir
}
func TestReadLocksAndDirectoryPins(t *testing.T) {
	dir := fixture(t)
	s, err := Acquire(dir)
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	if _, err = s.Open("uifiles/nightcap/window.xml"); err != nil {
		t.Fatal(err)
	}
	second, err := Acquire(dir)
	if err != nil {
		t.Fatal("concurrent read lease:", err)
	}
	second.Close()
	if g, err := installguard.Acquire(dir); err == nil {
		g.Close()
		t.Fatal("updater admitted")
	}
	for _, name := range []string{"eqgame.exe", "uifiles/nightcap/window.xml"} {
		path := filepath.Join(dir, filepath.FromSlash(name))
		if _, err := os.ReadFile(path); err != nil {
			t.Fatal("reader blocked:", err)
		}
		if err := os.WriteFile(path, []byte("changed"), 0600); err == nil {
			t.Fatal("write permitted:", name)
		}
		if err := os.Rename(path, path+".moved"); err == nil {
			t.Fatal("rename permitted:", name)
		}
		if err := os.Remove(path); err == nil {
			t.Fatal("delete permitted:", name)
		}
	}
	for _, path := range []string{filepath.Join(dir, "uifiles", "nightcap"), dir, filepath.Dir(dir)} {
		if err := os.Rename(path, path+"-moved"); err == nil {
			t.Fatal("directory rename permitted:", path)
		}
	}
	if err := os.WriteFile(filepath.Join(dir, "eqclient.ini"), []byte("user change"), 0600); err != nil {
		t.Fatal("user file blocked:", err)
	}
	if err := os.WriteFile(filepath.Join(dir, "nightcap_health_123.json"), []byte("health"), 0600); err != nil {
		t.Fatal("new health blocked:", err)
	}
	if err := s.Close(); err != nil {
		t.Fatal(err)
	}
	if err := s.Close(); err != nil {
		t.Fatal("close not idempotent:", err)
	}
	if _, err := s.Open("eqgame.exe"); err == nil {
		t.Fatal("closed set reused")
	}
	if err := os.WriteFile(filepath.Join(dir, "eqgame.exe"), []byte("after close"), 0600); err != nil {
		t.Fatal("lock leaked:", err)
	}
}
func TestExistingWriterAndFailureCleanup(t *testing.T) {
	dir := fixture(t)
	f, err := os.OpenFile(filepath.Join(dir, "eqgame.exe"), os.O_WRONLY, 0)
	if err != nil {
		t.Fatal(err)
	}
	if s, err := Acquire(dir); err == nil {
		s.Close()
		t.Fatal("existing writer accepted")
	}
	f.Close()
	if err := os.Rename(dir, dir+"-moved"); err != nil {
		t.Fatal("failed acquire leaked directory pins:", err)
	}
}
func TestUnsafeAndAbsentPaths(t *testing.T) {
	dir := fixture(t)
	s, err := Acquire(dir)
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	for _, name := range []string{"../escape", "a/../eqgame.exe", "eqgame.exe:stream", "NUL", "eqgame.exe.", "eqgame.exe ", `a\b`, ".", "/eqgame.exe"} {
		if _, err := s.Open(name); err == nil {
			t.Fatal("unsafe path accepted:", name)
		}
	}
	if err := s.Absent("missing/subdir/file.dll"); err != nil {
		t.Fatal(err)
	}
	if err := s.Absent("uifiles/nightcap/missing.xml"); err != nil {
		t.Fatal(err)
	}
	if err := s.Absent("eqgame.exe"); err == nil {
		t.Fatal("present tombstone accepted")
	}
}
func TestRejectJunction(t *testing.T) {
	dir := fixture(t)
	alias := filepath.Join(t.TempDir(), "alias")
	cmd := exec.Command("cmd", "/c", "mklink", "/J", alias, dir)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("junction fixture: %v %s", err, out)
	}
	// Removing the junction itself does not remove its target.
	defer os.Remove(alias)
	if s, err := Acquire(alias); err == nil {
		s.Close()
		t.Fatal("junction root accepted")
	}
	s, err := Acquire(dir)
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	nested := filepath.Join(dir, "alias")
	cmd = exec.Command("cmd", "/c", "mklink", "/J", nested, filepath.Join(dir, "uifiles"))
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("nested junction: %v %s", err, out)
	}
	defer os.Remove(nested)
	if _, err := s.Open("alias/nightcap/window.xml"); err == nil {
		t.Fatal("junction asset accepted")
	}
}
func TestLaunchLockChild(t *testing.T) {
	if os.Getenv("NIGHTCAP_LAUNCHLOCK_CHILD") == "1" {
		os.Exit(0)
	}
}
func TestLockedImageCanExecute(t *testing.T) {
	dir := fixture(t)
	self, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(self)
	if err != nil {
		t.Fatal(err)
	}
	exe := filepath.Join(dir, "eqgame.exe")
	if err := os.WriteFile(exe, data, 0700); err != nil {
		t.Fatal(err)
	}
	s, err := Acquire(dir)
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, exe, "-test.run=^TestLaunchLockChild$")
	cmd.Env = append(os.Environ(), "NIGHTCAP_LAUNCHLOCK_CHILD=1")
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("read lock blocked execution: %v %s", err, out)
	}
}

func TestHardLinkCannotMutateLockedAsset(t *testing.T) {
	dir := fixture(t)
	original := filepath.Join(dir, "eqgame.exe")
	alias := filepath.Join(t.TempDir(), "alias.exe")
	if err := os.Link(original, alias); err != nil {
		t.Fatal(err)
	}
	s, err := Acquire(dir)
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	if err := os.WriteFile(alias, []byte("changed through alias"), 0600); err == nil {
		t.Fatal("hard link bypassed lock")
	}
	s.Close()
	if err := os.WriteFile(alias, []byte("after close"), 0600); err != nil {
		t.Fatal(err)
	}
}
