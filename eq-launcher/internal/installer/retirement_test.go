package installer

import (
	"context"
	"errors"
	"nightcap/eq-launcher/internal/manifest"
	"strings"
	"testing"
)

func TestPinnedRetirement(t *testing.T) {
	for _, mode := range []string{"original", "modified", "absent", "rollback"} {
		t.Run(mode, func(t *testing.T) {
			root, stage, raw, sig, trust := fixture(t)
			trust.RetiredSHA256 = map[string]string{"old.dll": manifest.Digest([]byte("retired bytes"))}
			if mode == "modified" {
				if err := root.WriteFile("old.dll", []byte("custom archive"), 0600); err != nil {
					t.Fatal(err)
				}
			}
			if mode == "absent" {
				if err := root.Remove("old.dll"); err != nil {
					t.Fatal(err)
				}
			}
			var fault func(string) error
			if mode == "rollback" {
				fault = func(step string) error {
					if step == "remove:2" {
						return errors.New("test failure")
					}
					return nil
				}
			}
			_, err := installLocked(context.Background(), root, stage, raw, sig, trust, fault)
			switch mode {
			case "modified":
				if err == nil {
					t.Fatal("accepted modified archive")
				}
				assertBytes(t, root, "old.dll", "custom archive")
				assertBytes(t, root, "dinput8.dll", "old dll")
				assertAbsent(t, root, ".nightcap/pending.json")
				assertAbsent(t, root, ".nightcap/active.json")
			case "rollback":
				if err == nil {
					t.Fatal("fault missing")
				}
				assertRestored(t, root)
			default:
				if err != nil {
					t.Fatal(err)
				}
				assertAbsent(t, root, "old.dll")
				assertBytes(t, root, "dinput8.dll", "new dll")
			}
		})
	}
}
func TestPinnedRetirementCannotChangeMidInstall(t *testing.T) {
	root, stage, raw, sig, trust := fixture(t)
	trust.RetiredSHA256 = map[string]string{"old.dll": manifest.Digest([]byte("retired bytes"))}
	attempted := false
	_, err := installLocked(context.Background(), root, stage, raw, sig, trust, func(step string) error {
		if step == "replace:0" {
			attempted = true
			if e := root.WriteFile("old.dll", []byte("custom archive"), 0600); e == nil {
				t.Fatal("retirement writable while pinned")
			}
			if e := root.Remove("old.dll"); e == nil {
				t.Fatal("retirement removable while pinned")
			}
		}
		return nil
	})
	if err != nil || !attempted {
		t.Fatalf("install: %v", err)
	}
	assertAbsent(t, root, "old.dll")
}
func TestPinnedRecoveryPreservesConflict(t *testing.T) {
	root, stage, raw, sig, trust := fixture(t)
	trust.RetiredSHA256 = map[string]string{"old.dll": manifest.Digest([]byte("retired bytes"))}
	_, err := installLocked(context.Background(), root, stage, raw, sig, trust, func(step string) error {
		if step == "remove:2" {
			return errInterrupted
		}
		return nil
	})
	if !errors.Is(err, errInterrupted) {
		t.Fatal(err)
	}
	if err = root.WriteFile("old.dll", []byte("custom archive"), 0600); err != nil {
		t.Fatal(err)
	}
	if err = recoverLocked(root, trust); err == nil {
		t.Fatal("overwrote conflict")
	}
	assertBytes(t, root, "old.dll", "custom archive")
	if _, err = root.Stat(".nightcap/pending.json"); err != nil {
		t.Fatal("lost pending recovery", err)
	}
}

func TestRetiredRestoreStagesBeforePublishing(t *testing.T) {
	root, _, _, _, _ := fixture(t)
	if err := root.Remove("old.dll"); err != nil {
		t.Fatal(err)
	}
	digest := manifest.Digest([]byte("retired bytes"))
	id := strings.Repeat("a", 32)
	if err := restoreRetired(root, "old.dll", strings.NewReader("partial"), 13, digest, id, 2, nil); err == nil {
		t.Fatal("accepted truncated restore")
	}
	assertAbsent(t, root, "old.dll")
	func() {
		defer func() {
			if recover() == nil {
				t.Fatal("no simulated crash")
			}
		}()
		_ = restoreRetired(root, "old.dll", strings.NewReader("retired bytes"), 13, digest, id, 2, func(string) { panic("crash") })
	}()
	assertAbsent(t, root, "old.dll")
	if err := restoreRetired(root, "old.dll", strings.NewReader("retired bytes"), 13, digest, id, 2, nil); err != nil {
		t.Fatal(err)
	}
	assertBytes(t, root, "old.dll", "retired bytes")
}
func TestRecoveryPreservesLateAppearingRetiredFile(t *testing.T) {
	root, stage, raw, sig, trust := fixture(t)
	if err := root.Remove("old.dll"); err != nil {
		t.Fatal(err)
	}
	trust.RetiredSHA256 = map[string]string{"old.dll": manifest.Digest([]byte("retired bytes"))}
	_, err := installLocked(context.Background(), root, stage, raw, sig, trust, func(step string) error {
		if step == "replace:0" {
			return errInterrupted
		}
		return nil
	})
	if !errors.Is(err, errInterrupted) {
		t.Fatal(err)
	}
	err = recoverWithFault(root, trust, func(step string) {
		if step == "restore:0" {
			if e := root.WriteFile("old.dll", []byte("custom"), 0600); e != nil {
				t.Fatal(e)
			}
		}
	})
	if err == nil {
		t.Fatal("lost late conflict")
	}
	assertBytes(t, root, "old.dll", "custom")
}
