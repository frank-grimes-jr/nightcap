package installguard

import (
	"bufio"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"
	"testing"
)

func TestExclusiveGuard(t *testing.T) {
	root := t.TempDir()
	name := filepath.Join(root, "eqgame.exe")
	if err := os.WriteFile(name, []byte("unchanged"), 0600); err != nil {
		t.Fatal(err)
	}
	guard, err := acquire(root, "unlikely-nightcap-test-process.exe")
	if err != nil {
		t.Fatal(err)
	}
	if second, err := acquire(root, "unlikely-nightcap-test-process.exe"); err == nil {
		second.Close()
		t.Fatal("second updater admitted")
	}
	if _, err := os.ReadFile(name); err == nil {
		t.Fatal("exclusive executable can be reopened")
	}
	if err := guard.Close(); err != nil {
		t.Fatal(err)
	}
	b, err := os.ReadFile(name)
	if err != nil || string(b) != "unchanged" {
		t.Fatalf("file modified: %q %v", b, err)
	}
}
func TestSnapshotFindsSelf(t *testing.T) {
	exe, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	running, err := Running(filepath.Base(exe))
	if err != nil || !running {
		t.Fatalf("self not found: %v %v", running, err)
	}
	if g, err := acquire(t.TempDir(), filepath.Base(exe)); err == nil {
		g.Close()
		t.Fatal("running process ignored")
	}
}
func TestProcessGuardHelper(t *testing.T) {
	if os.Getenv("NIGHTCAP_GUARD_HELPER") != "1" {
		return
	}
	io.WriteString(os.Stdout, "ready\n")
	var b [1]byte
	os.Stdin.Read(b[:])
	os.Exit(0)
}
func TestGuardBlocksLaunchAndRunningImage(t *testing.T) {
	root := t.TempDir()
	fixture := filepath.Join(root, "eqgame.exe")
	self, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(self)
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(fixture, data, 0700); err != nil {
		t.Fatal(err)
	}
	guard, err := acquire(root, "unlikely-nightcap-test-process.exe")
	if err != nil {
		t.Fatal(err)
	}
	blocked := exec.Command(fixture, "-test.run=TestProcessGuardHelper")
	blocked.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	if err = blocked.Start(); err == nil {
		blocked.Process.Kill()
		blocked.Wait()
		guard.Close()
		t.Fatal("executable started under guard")
	}
	if err = guard.Close(); err != nil {
		t.Fatal(err)
	}
	helper := exec.Command(fixture, "-test.run=TestProcessGuardHelper")
	helper.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	helper.Env = append(os.Environ(), "NIGHTCAP_GUARD_HELPER=1")
	output, err := helper.StdoutPipe()
	if err != nil {
		t.Fatal(err)
	}
	input, err := helper.StdinPipe()
	if err != nil {
		t.Fatal(err)
	}
	if err = helper.Start(); err != nil {
		t.Fatal(err)
	}
	defer func() { input.Close(); helper.Process.Kill(); helper.Wait() }()
	line, err := bufio.NewReader(output).ReadString('\n')
	if err != nil || line != "ready\n" {
		t.Fatalf("helper not ready: %q %v", line, err)
	}
	// Deliberately bypass the process-name match to test the executable handle.
	if g, err := acquire(root, "unlikely-nightcap-test-process.exe"); err == nil {
		g.Close()
		t.Fatal("running image did not block exclusive writable handle")
	}
}
