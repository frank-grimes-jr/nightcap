package installguard

import (
	"bufio"
	"context"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"
	"testing"
	"time"
)

func TestExclusiveGuard(t *testing.T) {
	root := t.TempDir()
	name := filepath.Join(root, "eqgame.exe")
	if err := os.WriteFile(name, []byte("unchanged"), 0600); err != nil {
		t.Fatal(err)
	}
	guard, err := Acquire(root)
	if err != nil {
		t.Fatal(err)
	}
	if second, err := Acquire(root); err == nil {
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
	guard, err := Acquire(root)
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
	// A running target image must prevent the exclusive writable handle.
	if g, err := Acquire(root); err == nil {
		g.Close()
		t.Fatal("running image did not block exclusive writable handle")
	}
}

// guardTestExecutable copies only this test binary; real installed games are
// never launched, signaled, closed, or modified by these regression tests.
func guardTestExecutable(t *testing.T, root string) string {
	t.Helper()
	self, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(self)
	if err != nil {
		t.Fatal(err)
	}
	fixture := filepath.Join(root, "eqgame.exe")
	if err := os.WriteFile(fixture, data, 0700); err != nil {
		t.Fatal(err)
	}
	return fixture
}

func startGuardTestExecutable(t *testing.T, fixture string) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	helper := exec.CommandContext(ctx, fixture, "-test.run=^TestProcessGuardHelper$")
	helper.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	helper.Env = append(os.Environ(), "NIGHTCAP_GUARD_HELPER=1")
	output, err := helper.StdoutPipe()
	if err != nil {
		cancel()
		t.Fatal(err)
	}
	input, err := helper.StdinPipe()
	if err != nil {
		cancel()
		t.Fatal(err)
	}
	if err := helper.Start(); err != nil {
		input.Close()
		cancel()
		t.Fatal(err)
	}
	t.Cleanup(func() {
		input.Close()
		cancel() // This context owns only the temporary test helper process.
		helper.Wait()
	})
	line, err := bufio.NewReader(output).ReadString('\n')
	if err != nil || line != "ready\n" {
		t.Fatalf("temporary helper not ready: %q %v", line, err)
	}
}

func TestGuardAllowsOtherRunningInstallationWithSameExecutableName(t *testing.T) {
	other := guardTestExecutable(t, t.TempDir())
	startGuardTestExecutable(t, other)
	root := t.TempDir()
	if err := os.WriteFile(filepath.Join(root, "eqgame.exe"), []byte("unchanged target"), 0600); err != nil {
		t.Fatal(err)
	}
	guard, err := Acquire(root)
	if err != nil {
		t.Fatalf("unrelated installation blocked target update: %v", err)
	}
	defer guard.Close()
	data, err := io.ReadAll(guard.Executable())
	if err != nil || string(data) != "unchanged target" {
		t.Fatalf("guard did not hold original target: %q %v", data, err)
	}
}

func TestGuardRejectsRunningTargetThroughRenamedHardLink(t *testing.T) {
	root := t.TempDir()
	target := guardTestExecutable(t, root)
	alias := filepath.Join(t.TempDir(), "renamed-client.exe")
	if err := os.Link(target, alias); err != nil {
		t.Fatal(err)
	}
	startGuardTestExecutable(t, alias)
	if guard, err := Acquire(root); err == nil {
		guard.Close()
		t.Fatal("running target through renamed hard link admitted an update")
	}
}

func TestGuardExcludesUpdaterAndLaunchThroughHardLink(t *testing.T) {
	root := t.TempDir()
	target := guardTestExecutable(t, root)
	aliasRoot := t.TempDir()
	alias := filepath.Join(aliasRoot, "eqgame.exe")
	if err := os.Link(target, alias); err != nil {
		t.Fatal(err)
	}
	guard, err := Acquire(root)
	if err != nil {
		t.Fatal(err)
	}
	defer guard.Close()
	if second, err := Acquire(aliasRoot); err == nil {
		second.Close()
		t.Fatal("same target admitted a concurrent updater through a hard link")
	}
	blocked := exec.Command(alias, "-test.run=^TestProcessGuardHelper$")
	blocked.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	blocked.Env = append(os.Environ(), "NIGHTCAP_GUARD_HELPER=1")
	if err := blocked.Start(); err == nil {
		blocked.Process.Kill() // Only the owned temporary helper, never a real game.
		blocked.Wait()
		t.Fatal("target started through a hard link while its update guard was held")
	}
}
