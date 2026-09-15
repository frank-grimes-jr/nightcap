package installer

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"
	"testing"

	"nightcap/eq-launcher/internal/manifest"
)

type crashInput struct {
	Raw       []byte
	Signature manifest.Signature
	Trust     manifest.Trust
}

func TestCrashHelper(t *testing.T) {
	if os.Getenv("NIGHTCAP_INSTALL_CRASH") == "" {
		return
	}
	var in crashInput
	b, err := os.ReadFile(os.Getenv("NIGHTCAP_INSTALL_INPUT"))
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(b, &in); err != nil {
		t.Fatal(err)
	}
	root, err := os.OpenRoot(os.Getenv("NIGHTCAP_INSTALL_CLIENT"))
	if err != nil {
		t.Fatal(err)
	}
	defer root.Close()
	at := os.Getenv("NIGHTCAP_INSTALL_CRASH")
	if os.Getenv("NIGHTCAP_RECOVERY_CRASH") == "1" {
		if err := recoverWithFault(root, in.Trust, func(point string) {
			if point == at {
				os.Exit(73)
			}
		}); err != nil {
			t.Fatal(err)
		}
	} else {
		stage, err := os.OpenRoot(os.Getenv("NIGHTCAP_INSTALL_STAGE"))
		if err != nil {
			t.Fatal(err)
		}
		defer stage.Close()
		if _, err := installLocked(context.Background(), root, stage, in.Raw, in.Signature, in.Trust, func(point string) error {
			if point == at {
				os.Exit(73)
			}
			return nil
		}); err != nil {
			t.Fatal(err)
		}
	}
	t.Fatal("requested crash boundary was not reached")
}
func runCrash(t *testing.T, root, stage *os.Root, raw []byte, sig manifest.Signature, trust manifest.Trust, point string, recovering bool) {
	t.Helper()
	b, err := json.Marshal(crashInput{raw, sig, trust})
	if err != nil {
		t.Fatal(err)
	}
	input := filepath.Join(t.TempDir(), "input.json")
	if err = os.WriteFile(input, b, 0600); err != nil {
		t.Fatal(err)
	}
	helper := exec.Command(os.Args[0], "-test.run=^TestCrashHelper$")
	helper.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	helper.Env = append(os.Environ(), "NIGHTCAP_INSTALL_CRASH="+point, "NIGHTCAP_INSTALL_CLIENT="+root.Name(), "NIGHTCAP_INSTALL_STAGE="+stage.Name(), "NIGHTCAP_INSTALL_INPUT="+input)
	if recovering {
		helper.Env = append(helper.Env, "NIGHTCAP_RECOVERY_CRASH=1")
	}
	output, err := helper.CombinedOutput()
	var exit *exec.ExitError
	if !errors.As(err, &exit) || exit.ExitCode() != 73 {
		t.Fatalf("wrong helper termination: %v %s", err, output)
	}
}
func TestActualProcessExitRecovery(t *testing.T) {
	for _, point := range []string{"pending", "replace:0", "replace:1", "remove:2", "active"} {
		t.Run(point, func(t *testing.T) {
			root, stage, raw, sig, trust := fixture(t)
			runCrash(t, root, stage, raw, sig, trust, point, false)
			if err := recoverLocked(root, trust); err != nil {
				t.Fatal(err)
			}
			assertRestored(t, root)
		})
	}
}
func TestRecoveryCanRestartAfterProcessExit(t *testing.T) {
	root, stage, raw, sig, trust := fixture(t)
	runCrash(t, root, stage, raw, sig, trust, "active", false)
	runCrash(t, root, stage, raw, sig, trust, "restore:0", true)
	if err := recoverLocked(root, trust); err != nil {
		t.Fatal(err)
	}
	assertRestored(t, root)
}

func TestLockedUnchangedDestinationDoesNotBlockRollback(t *testing.T) {
	root, stage, raw, sig, trust := fixture(t)
	put(t, root.Name(), "uifiles/nightcap/window.xml", "old xml")
	wide, err := syscall.UTF16PtrFromString(filepath.Join(root.Name(), "uifiles/nightcap/window.xml"))
	if err != nil {
		t.Fatal(err)
	}
	handle, err := syscall.CreateFile(wide, syscall.GENERIC_READ, syscall.FILE_SHARE_READ|syscall.FILE_SHARE_WRITE, nil, syscall.OPEN_EXISTING, 0, 0)
	if err != nil {
		t.Fatal(err)
	}
	defer syscall.CloseHandle(handle)
	if _, err = installLocked(context.Background(), root, stage, raw, sig, trust, nil); err == nil {
		t.Fatal("locked file replacement succeeded")
	}
	assertBytes(t, root, "dinput8.dll", "old dll")
	assertBytes(t, root, "uifiles/nightcap/window.xml", "old xml")
	assertAbsent(t, root, ".nightcap/pending.json")
}

func TestInstallerRejectsJunctions(t *testing.T) {
	for _, component := range []string{"uifiles", ".nightcap"} {
		t.Run(component, func(t *testing.T) {
			root, stage, raw, sig, trust := fixture(t)
			outside := t.TempDir()
			put(t, outside, "sentinel", "untouched")
			alias := filepath.Join(root.Name(), component)
			if output, err := exec.Command("cmd", "/c", "mklink", "/J", alias, outside).CombinedOutput(); err != nil {
				t.Fatalf("junction setup: %v %s", err, output)
			}
			if _, err := installLocked(context.Background(), root, stage, raw, sig, trust, nil); err == nil {
				t.Fatal("installer followed junction")
			}
			assertBytes(t, root, "dinput8.dll", "old dll")
			entries, err := os.ReadDir(outside)
			if err != nil || len(entries) != 1 {
				t.Fatalf("outside directory mutated: %v %v", entries, err)
			}
			b, err := os.ReadFile(filepath.Join(outside, "sentinel"))
			if err != nil || string(b) != "untouched" {
				t.Fatalf("outside sentinel mutated: %q %v", b, err)
			}
		})
	}
}

func TestPublicInstallRequiresGuardAndSupportedExecutable(t *testing.T) {
	root, stage, raw, sig, trust := fixture(t)
	put(t, root.Name(), "eqgame.exe", "unsupported")
	b, err := encode(sig)
	if err != nil {
		t.Fatal(err)
	}
	if err = newBlob(stage, "manifest.json", raw); err != nil {
		t.Fatal(err)
	}
	if err = newBlob(stage, "signature.json", b); err != nil {
		t.Fatal(err)
	}
	if _, err = Install(context.Background(), root.Name(), stage.Name(), trust); err == nil {
		t.Fatal("unqualified client installed")
	}
	assertRestored(t, root)
	assertAbsent(t, root, ".nightcap")
}
